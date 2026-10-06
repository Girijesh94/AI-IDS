import queue
import threading
import time
import copy
from .detection import Detector
from .schemas import validate_flow


class Runtime:
    def __init__(self, settings, store, emit=lambda *args: None):
        self.settings, self.store, self.emit = settings, store, emit
        self.detector = Detector(settings.model)
        self.lock = threading.RLock()
        self.queue = queue.Queue(settings.queue_size)
        self.stop = threading.Event()
        self.worker = None
        self.sniffer = None
        self.extractor = None
        self.capture_lock = threading.Lock()
        self.status = dict(mode=settings.mode, capture='disabled', capture_error=None,
                           interface=settings.interface, flows_received=0, duplicates=0,
                           queue_drops=0, processing_errors=0, last_event=0,
                           collector_heartbeat=0, endpoint='disabled', endpoint_error=None)

    def process(self, raw, mode=None):
        flow = validate_flow(raw)
        mode = mode or self.settings.mode
        if mode not in {'live', 'replay'}:
            raise ValueError('Invalid event mode')
        with self.lock:
            if self.store.exists(flow['event_id']):
                self.status['duplicates'] += 1
                return None
            # Roll back contextual state on failed persistence so retry semantics stay honest.
            history_key=(flow['sensor_id'],flow['src_ip'])
            previous=copy.copy(self.detector.history.get(history_key))
            try:
                event = dict(flow, **self.detector.score(flow), mode=mode, features=flow)
                saved=self.store.save(event, 'network', mode)
                if not saved:
                    if previous is None:
                        self.detector.history.pop(history_key,None)
                    else:
                        self.detector.history[history_key]=previous
                    self.status['duplicates']+=1
                    return None
            except Exception:
                if previous is None:
                    self.detector.history.pop(history_key,None)
                else:
                    self.detector.history[history_key]=previous
                raise
            self.status['flows_received'] += 1
            self.status['last_event'] = time.time()
        self.emit('network_flow', event)
        if event['is_anomaly']:
            self.emit('alert', event)
        return event

    def submit(self, flow):
        try:
            self.queue.put_nowait(flow)
            return True
        except queue.Full:
            self.status['queue_drops'] += 1
            return False

    def _work(self):
        while not self.stop.is_set() or not self.queue.empty():
            try:
                flow = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self.process(flow)
            except Exception as exc:
                self.status['processing_errors'] += 1
                try:
                    self.store.log('ERROR', 'INFERENCE', exc)
                except Exception:
                    pass
            finally:
                self.queue.task_done()

    def start(self):
        if self.worker:
            return
        self.worker = threading.Thread(target=self._work, name='ids-inference', daemon=True)
        self.worker.start()
        if self.settings.mode == 'live':
            self.start_capture()
        threading.Thread(target=self._maintenance, name='ids-maintenance', daemon=True).start()

    def _maintenance(self):
        next_cleanup = 0
        while not self.stop.wait(1):
            if self.extractor and self.status['capture'] == 'running':
                if not self.sniffer.running:
                    self.status['capture'] = 'failed'
                    self.status['capture_error'] = str(getattr(self.sniffer, 'exception', 'Capture stopped'))
                else:
                    with self.capture_lock:
                        for flow in self.extractor.flush(time.time()):
                            self.submit(flow)
                    self.status['collector_heartbeat'] = time.time()
            if time.time() >= next_cleanup:
                try:
                    self.store.cleanup()
                except Exception as exc:
                    self.status['storage_error'] = str(exc)
                next_cleanup = time.time() + 3600

    def start_capture(self):
        try:
            from scapy.all import AsyncSniffer
            from .features import FlowExtractor
            self.extractor = FlowExtractor('local-live')
            def callback(packet):
                with self.capture_lock:
                    for flow in self.extractor.add(packet):
                        self.submit(flow)
            def started():
                self.status['capture'] = 'running'
                self.status['collector_heartbeat'] = time.time()
            self.status['capture'] = 'starting'
            self.sniffer = AsyncSniffer(iface=self.settings.interface, store=False, prn=callback,
                filter='(ip or ip6) and not (tcp port 5000)', started_callback=started)
            self.sniffer.start()
            # Startup errors occur in the Scapy thread; surface them rather than claim readiness.
            threading.Thread(target=self._check_capture, daemon=True).start()
        except Exception as exc:
            self.status.update(capture='failed', capture_error=str(exc))

    def _check_capture(self):
        if self.stop.wait(2):
            return
        if self.status['capture'] == 'starting':
            self.status.update(capture='failed', capture_error=str(getattr(self.sniffer, 'exception', 'Capture driver did not start')))

    def close(self):
        if self.sniffer and self.sniffer.running:
            try:
                self.sniffer.stop()
            except Exception:
                pass
        if self.extractor:
            with self.capture_lock:
                for flow in self.extractor.flush(final=True):
                    self.submit(flow)
        self.stop.set()
        if self.worker:
            self.worker.join(timeout=10)
