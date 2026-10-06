"""Common bounded bidirectional extraction for packet replay and live capture.

Bytes count the IP packet (including IP headers); durations are seconds.
Five-second disjoint observation windows, ten-second idle timeout, sixty-second
session segmentation. The first packet establishes orientation. No payloads retained.
"""
import hashlib
import socket
import struct
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
        self.session_sequence = 0

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
        now = float(packet.time)
        ip = packet.getlayer(IP) or packet.getlayer(IPv6)
        values = None
        if ip is not None and not (isinstance(ip, IP) and (ip.frag or int(ip.flags) & 1)) and not packet.haslayer('IPv6ExtHdrFragment'):
            transport = packet.getlayer(TCP) or packet.getlayer(UDP)
            proto = 6 if packet.haslayer(TCP) else 17 if packet.haslayer(UDP) else int(getattr(ip, 'proto', getattr(ip, 'nh', 0)))
            if proto in (1, 6, 17, 58):
                values = (ip.src, ip.dst, int(transport.sport) if transport else 0,
                          int(transport.dport) if transport else 0, proto, len(bytes(ip)),
                          int(packet[TCP].flags) if packet.haslayer(TCP) else 0)
        return self.add_values(now, values)

    def add_values(self, now, values):
        """Shared state machine for decoded live packets and fast PCAP headers."""
        self.packets += 1
        if now < self.last_time:
            self.out_of_order += 1
            return []
        self.last_time = now
        # Expire the whole map at most four times a second, not on every packet.
        emitted = []
        if now >= self.next_sweep:
            emitted = self.flush(now)
            self.next_sweep = now + 0.25
        if values is None:
            self.unsupported += 1
            return emitted
        src, dst, sport, dport, proto, size, flags = values
        a, b = (src, sport), (dst, dport)
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
            # Captures can contain successive RST packets at the exact same time.
            # Include deterministic creation order so those sessions cannot collide.
            self.session_sequence += 1
            identity = hashlib.sha256(f'{self.sensor_id}|{key}|{now:.9f}|{self.session_sequence}'.encode()).hexdigest()[:32]
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
        direction = 'src2dst' if a == state['src'] else 'dst2src'
        f[direction + '_pkts'] += 1
        f[direction + '_bytes'] += size
        f['pkt_count'] += 1
        f['byte_count'] += size
        f['min_pkt_size'] = min(f['min_pkt_size'], size)
        f['max_pkt_size'] = max(f['max_pkt_size'], size)
        if proto == 6:
            for field, mask in [('tcp_syn', 2), ('tcp_rst', 4), ('tcp_fin', 1)]:
                f[field] += bool(flags & mask)
        state['last'] = now
        if proto == 6 and flags & 4:
            emitted.append(self._record(state))
            del self.flows[key]
        return emitted


def read_pcap(path, sensor_id='replay', stats=None, fast=True):
    """Decode Ethernet IPv4 headers directly; use Scapy for other formats.

    Both paths feed the same extraction state machine. No payload is decoded or
    retained by the fast path. PCAPNG and nanosecond PCAP preserve timestamp precision.
    """
    from scapy.utils import RawPcapReader
    if fast:
        with RawPcapReader(str(path)) as reader:
            compatible = not hasattr(reader, 'linktype') or reader.linktype == 1
        if compatible:
            yield from _read_fast(path, sensor_id, stats)
            return
    yield from _read_reference(path, sensor_id, stats)


def _read_reference(path, sensor_id='replay', stats=None):
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


def _read_fast(path, sensor_id, stats):
    from scapy.utils import RawPcapReader
    from scapy.layers.l2 import Ether
    from scapy.config import conf
    extractor = FlowExtractor(sensor_id)
    try:
        with RawPcapReader(str(path)) as packets:
            for raw, meta in packets:
                if hasattr(meta, 'tshigh'):
                    if meta.tshigh is None:
                        raise ValueError('PCAPNG packet has no observation timestamp')
                    now = ((meta.tshigh << 32) + meta.tslow) / meta.tsresol
                    linktype = meta.linktype
                else:
                    scale = 1000000000 if packets.nano else 1000000
                    now = (meta.sec * scale + meta.usec) / scale
                    linktype = packets.linktype
                if linktype != 1:
                    packet = conf.l2types.num2layer[linktype](raw)
                    packet.time = now
                    yield from extractor.add(packet)
                    continue
                offset = 14
                kind = int.from_bytes(raw[12:14], 'big')
                while kind in (0x8100, 0x88a8) and len(raw) >= offset + 4:
                    kind = int.from_bytes(raw[offset+2:offset+4], 'big')
                    offset += 4
                if kind != 0x0800 or len(raw) < offset + 20:
                    packet = Ether(raw)
                    packet.time = now
                    yield from extractor.add(packet)
                    continue
                header = (raw[offset] & 15) * 4
                proto = raw[offset+9]
                fragment = int.from_bytes(raw[offset+6:offset+8], 'big') & 0x3fff
                transport = offset + header
                if fragment:
                    yield from extractor.add_values(now, None)
                    continue
                if header < 20 or proto not in (6, 17) or len(raw) < transport + (20 if proto == 6 else 8):
                    packet = Ether(raw)
                    packet.time = now
                    yield from extractor.add(packet)
                    continue
                sport, dport = struct.unpack_from('!HH', raw, transport) if proto in (6, 17) else (0, 0)
                values = (socket.inet_ntoa(raw[offset+12:offset+16]),
                          socket.inet_ntoa(raw[offset+16:offset+20]), sport, dport,
                          proto, len(raw)-offset, raw[transport+13] if proto == 6 else 0)
                yield from extractor.add_values(now, values)
        yield from extractor.flush(final=True)
    finally:
        if stats is not None:
            stats.update(packets=extractor.packets, capacity_drops=extractor.dropped,
                         unsupported_packets=extractor.unsupported, out_of_order_packets=extractor.out_of_order)
