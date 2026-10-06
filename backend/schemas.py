"""The only telemetry contract accepted by production inference."""
import ipaddress
import math

SCHEMA = 'flow-window-v1'
FEATURES = ['duration', 'src2dst_pkts', 'dst2src_pkts', 'src2dst_bytes',
            'dst2src_bytes', 'mean_pkt_size', 'min_pkt_size', 'max_pkt_size',
            'iat_mean', 'tcp_syn', 'tcp_rst', 'tcp_fin', 'proto']
COUNTS = ['pkt_count', 'byte_count', 'src2dst_pkts', 'dst2src_pkts',
          'src2dst_bytes', 'dst2src_bytes', 'tcp_syn', 'tcp_rst', 'tcp_fin']


def validate_flow(raw):
    if not isinstance(raw, dict) or raw.get('schema_version') != SCHEMA:
        raise ValueError(f'Expected schema_version={SCHEMA}')
    # Copy an allowlist: labels, scores, reasons, severity and predictions never enter inference.
    out = {'schema_version': SCHEMA}
    for key in ['event_id', 'session_id', 'sensor_id']:
        value = raw.get(key)
        if not isinstance(value, str) or not 1 <= len(value) <= 200:
            raise ValueError(f'Invalid {key}')
        out[key] = value
    for key in ['src_ip', 'dst_ip']:
        out[key] = str(ipaddress.ip_address(raw.get(key, '')))
    for key, maximum in [('src_port', 65535), ('dst_port', 65535), ('proto', 255)]:
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
            raise ValueError(f'Invalid {key}')
        out[key] = value
    for key in set(FEATURES + COUNTS + ['timestamp']):
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f'Invalid {key}')
        if key in COUNTS and (value != int(value) or value > 2**53):
            raise ValueError(f'Invalid count {key}')
        out[key] = value
    if not out['pkt_count'] or out['pkt_count'] != out['src2dst_pkts'] + out['dst2src_pkts']:
        raise ValueError('Packet totals disagree')
    if out['byte_count'] != out['src2dst_bytes'] + out['dst2src_bytes']:
        raise ValueError('Byte totals disagree')
    if abs(out['mean_pkt_size'] - out['byte_count'] / out['pkt_count']) > 1e-6:
        raise ValueError('Mean size disagrees with totals')
    if not out['min_pkt_size'] <= out['mean_pkt_size'] <= out['max_pkt_size']:
        raise ValueError('Invalid packet size range')
    if any(out[key] > out['pkt_count'] for key in ['tcp_syn', 'tcp_rst', 'tcp_fin']):
        raise ValueError('Invalid TCP flag counts')
    if out['duration'] > 5.000001:
        raise ValueError('Observation window exceeds five seconds')
    return out
