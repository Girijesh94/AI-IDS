"""Common bounded bidirectional extraction for packet replay and live capture.

Bytes count the IP packet (including IP headers); durations are seconds.
Five-second disjoint observation windows, ten-second idle timeout, sixty-second
session segmentation. The first packet establishes orientation. No payloads retained.
"""
import hashlib
from .schemas import SCHEMA, validate_flow


class FlowExtractor:
    def __init__(self, sensor_id='local', max_flows=20000):
        self.sensor_id = sensor_id
        self.max_flows = max_flows
        self.flows = {}
        self.dropped = 0
        self.unsupported = 0
        self.packets = 0
        self.out_of_order = 0
        self.last_time = 0.0
        self.next_sweep = 0.0

    def _record(self, state):
        f = state['window']
        if not f['pkt_count']:
            return None
        f = dict(f)
        f['duration'] = state['last'] - state['window_start']
        f['timestamp'] = state['last']
        f['mean_pkt_size'] = f['byte_count'] / f['pkt_count']
        f['iat_mean'] = f.pop('iat_sum') / max(1, f['pkt_count'] - 1)
        f['event_id'] = f"{state['session_id']}:{state['index']}"
        return validate_flow(f)

    def _window(self, state, now):
        state['window_start'] = now
        state['window'] = dict(schema_version=SCHEMA, session_id=state['session_id'],
                               sensor_id=self.sensor_id, src_ip=state['src'][0],
                               src_port=state['src'][1], dst_ip=state['dst'][0],
                               dst_port=state['dst'][1], proto=state['proto'],
                               pkt_count=0, byte_count=0, src2dst_pkts=0, dst2src_pkts=0,
                               src2dst_bytes=0, dst2src_bytes=0, min_pkt_size=float('inf'),
                               max_pkt_size=0, iat_sum=0, tcp_syn=0, tcp_rst=0, tcp_fin=0)

    def flush(self, now=None, final=False):
        emitted = []
        now = self.last_time if now is None else max(now, self.last_time)
        for key, state in list(self.flows.items()):
            expired = final or now - state['last'] >= 10 or now - state['first'] >= 60
            if expired or now - state['window_start'] >= 5:
                value = self._record(state)
                if value:
                    emitted.append(value)
                if expired:
                    del self.flows[key]
                else:
                    state['index'] += 1
                    self._window(state, now)
        return emitted

    def add(self, packet):
        from scapy.layers.inet import IP, TCP, UDP, ICMP
        from scapy.layers.inet6 import IPv6
        self.packets += 1
        now = float(packet.time)
        if now < self.last_time:
            self.out_of_order += 1
            return []
        self.last_time = now
        # Expire the whole map at most four times a second, not on every packet.
        emitted = []
        if now >= self.next_sweep:
            emitted = self.flush(now)
            self.next_sweep = now + 0.25
        ip = packet.getlayer(IP) or packet.getlayer(IPv6)
        if ip is None:
            self.unsupported += 1
            return emitted
        # Fragmented packets cannot reliably be assigned transport ports without reassembly.
        if isinstance(ip, IP) and (ip.frag or int(ip.flags) & 1):
            self.unsupported += 1
            return emitted
        if packet.haslayer('IPv6ExtHdrFragment'):
            self.unsupported += 1
            return emitted
        transport = packet.getlayer(TCP) or packet.getlayer(UDP)
        proto = 6 if packet.haslayer(TCP) else 17 if packet.haslayer(UDP) else int(getattr(ip, 'proto', getattr(ip, 'nh', 0)))
        if proto not in (1, 6, 17, 58):
            self.unsupported += 1
            return emitted
        a = (ip.src, int(transport.sport) if transport else 0)
        b = (ip.dst, int(transport.dport) if transport else 0)
        key = (min(a, b), max(a, b), proto)
        state = self.flows.get(key)
        if state and (now - state['first'] >= 60 or now - state['last'] >= 10):
            value = self._record(state)
            if value:
                emitted.append(value)
            del self.flows[key]
        elif state and now - state['window_start'] >= 5:
            value = self._record(state)
            if value:
                emitted.append(value)
            state['index'] += 1
            self._window(state, now)
        if key not in self.flows:
            if len(self.flows) >= self.max_flows:
                self.dropped += 1
                return emitted
            identity = hashlib.sha256(f'{self.sensor_id}|{key}|{now:.9f}'.encode()).hexdigest()[:32]
            state = dict(src=a, dst=b, proto=proto, first=now, last=now,
                         session_id=identity, index=0)
            self._window(state, now)
            self.flows[key] = state
        state = self.flows[key]
        f = state['window']
        # An empty window starts with its first observed packet, not the timer tick.
        if f['pkt_count'] == 0:
            state['window_start'] = now
        else:
            f['iat_sum'] += now - state['last']
        size = len(bytes(ip))
        direction = 'src2dst' if a == state['src'] else 'dst2src'
        f[direction + '_pkts'] += 1
        f[direction + '_bytes'] += size
        f['pkt_count'] += 1
        f['byte_count'] += size
        f['min_pkt_size'] = min(f['min_pkt_size'], size)
        f['max_pkt_size'] = max(f['max_pkt_size'], size)
        if proto == 6:
            flags = int(packet[TCP].flags)
            for field, mask in [('tcp_syn', 2), ('tcp_rst', 4), ('tcp_fin', 1)]:
                f[field] += bool(flags & mask)
        state['last'] = now
        if proto == 6 and int(packet[TCP].flags) & 4:
            emitted.append(self._record(state))
            del self.flows[key]
        return emitted


def read_pcap(path, sensor_id='replay', stats=None):
    from scapy.utils import PcapReader
    extractor = FlowExtractor(sensor_id)
    try:
        with PcapReader(str(path)) as packets:
            for packet in packets:
                yield from extractor.add(packet)
        yield from extractor.flush(final=True)
    finally:
        if stats is not None:
            stats.update(packets=extractor.packets, capacity_drops=extractor.dropped,
                         unsupported_packets=extractor.unsupported, out_of_order_packets=extractor.out_of_order)
