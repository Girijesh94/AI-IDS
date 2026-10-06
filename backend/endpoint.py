"""Windows Sysmon process event collection. Missing telemetry is reported explicitly."""
import hashlib
import threading
import time
import xml.etree.ElementTree as ET
from .command_rules import CMDDetector


class EndpointCollector:
    def __init__(self, runtime):
        self.runtime = runtime
        self.rules = CMDDetector()
        self.thread = None

    def analyze(self, command, event_id, timestamp=None, context=None, mode=None):
        if not isinstance(command, str) or not 1 <= len(command) <= 32768:
            raise ValueError('Command must contain 1-32768 characters')
        # Detection only: never execute supplied commands.
        result = self.rules.detect(command)
        # Lower-severity generic shell syntax is retained as evidence, not an incident.
        attack = bool(result['is_malicious'] and result['severity'] in {'high', 'critical'})
        result['score'] = result.pop('confidence', 0.0)
        result['confidence'] = None
        result['severity'] = result['severity'] if attack else 'low'
        event = dict(result, command=command, event_id=event_id,
                     timestamp=timestamp or time.time(), is_anomaly=attack,
                     is_malicious=attack, sensor_id='local-endpoint',
                     context=context or {}, detection_method='regex',
                     model_version='none', rule_version='command-regex-v1',
                     prediction_status='rules_only', mode=mode or self.runtime.settings.mode)
        if self.runtime.store.save(event, 'command', event['mode']):
            self.runtime.emit('cmd_detection', event)
            if attack:
                self.runtime.emit('alert', dict(event, type='cmd_detection'))
        return event

    def start(self):
        self.thread = threading.Thread(target=self._run, name='ids-sysmon', daemon=True)
        self.thread.start()

    def _run(self):
        import os
        if os.name != 'nt':
            self.runtime.status.update(endpoint='unavailable', endpoint_error='Sysmon requires Windows')
            return
        try:
            import win32evtlog as evt
            def next_events(handle, count):
                try:
                    return evt.EvtNext(handle, count)
                except Exception as exc:
                    if getattr(exc, 'winerror', None) == 259:
                        return []
                    raise
            channel = 'Microsoft-Windows-Sysmon/Operational'
            bookmark = self.runtime.store.state('sysmon_bookmark')
            if bookmark:
                query = evt.EvtQuery(channel, evt.EvtQueryChannelPath | evt.EvtQueryForwardDirection, '*[System[EventID=1]]')
                mark = evt.EvtCreateBookmark(bookmark)
                evt.EvtSeek(query, 1, mark, 0, evt.EvtSeekRelativeToBookmark)
            else:
                # First launch starts at the newest event; subsequent launches resume bookmarks.
                query = evt.EvtQuery(channel, evt.EvtQueryChannelPath | evt.EvtQueryReverseDirection, '*[System[EventID=1]]')
                latest = next_events(query, 1)
                mark = evt.EvtCreateBookmark(None)
                if latest:
                    evt.EvtUpdateBookmark(mark, latest[0])
                    self.runtime.store.state('sysmon_bookmark', evt.EvtRender(mark, evt.EvtRenderBookmark))
            self.runtime.status['endpoint'] = 'running'
            while not self.runtime.stop.wait(1):
                bookmark = self.runtime.store.state('sysmon_bookmark')
                query = evt.EvtQuery(channel, evt.EvtQueryChannelPath | evt.EvtQueryForwardDirection, '*[System[EventID=1]]')
                if bookmark:
                    mark = evt.EvtCreateBookmark(bookmark)
                    evt.EvtSeek(query, 1, mark, 0, evt.EvtSeekRelativeToBookmark)
                events = next_events(query, 128)
                for entry in events:
                    xml = evt.EvtRender(entry, evt.EvtRenderEventXml)
                    root = ET.fromstring(xml)
                    ns = {'e': 'http://schemas.microsoft.com/win/2004/08/events/event'}
                    values = {x.attrib['Name']: x.text or '' for x in root.findall('e:EventData/e:Data', ns)}
                    command = values.get('CommandLine', '')
                    if command and command != '-':
                        identity = 'sysmon:' + hashlib.sha256(xml.encode()).hexdigest()
                        self.analyze(command, identity, context={k: values.get(k) for k in
                            ['ProcessGuid', 'ParentProcessGuid', 'Image', 'ParentImage', 'User', 'UtcTime']}, mode='live')
                    evt.EvtUpdateBookmark(mark, entry)
                    self.runtime.store.state('sysmon_bookmark', evt.EvtRender(mark, evt.EvtRenderBookmark))
                self.runtime.status['endpoint_heartbeat'] = time.time()
        except Exception as exc:
            self.runtime.status.update(endpoint='unavailable', endpoint_error=str(exc))
            self._run_wmi()

    def _run_wmi(self):
        """Limited fallback: short-lived processes may disappear before WMI reads them."""
        sysmon_error=self.runtime.status.get('endpoint_error')
        initialized=False
        connection=watcher=process=None
        try:
            import pythoncom
            import wmi
            pythoncom.CoInitialize()
            initialized=True
            connection=wmi.WMI()
            watcher=connection.Win32_Process.watch_for('creation')
            self.runtime.status['endpoint']='limited_wmi'
            self.runtime.status['endpoint_error']=f'Sysmon unavailable ({sysmon_error}); WMI can miss short-lived processes'
            while not self.runtime.stop.is_set():
                self.runtime.status['endpoint_heartbeat']=time.time()
                try:
                    process=watcher(timeout_ms=1000)
                    command=getattr(process,'CommandLine',None)
                    if command:
                        identity='wmi:'+hashlib.sha256(f'{process.ProcessId}|{process.CreationDate}|{command}'.encode()).hexdigest()
                        self.analyze(command,identity,context={'pid':process.ProcessId,
                            'parent_pid':process.ParentProcessId,'source':'wmi_limited'},mode='live')
                except wmi.x_wmi_timed_out:
                    continue
        except Exception as exc:
            self.runtime.status.update(endpoint='unavailable',endpoint_error=str(exc))
        finally:
            if initialized:
                # Release COM proxies before uninitializing the apartment.
                watcher=connection=process=None
                import gc
                gc.collect()
                pythoncom.CoUninitialize()

