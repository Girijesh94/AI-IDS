"""Record real live collector health over an uninterrupted shadow session.

This measures collection stability, not accuracy. Independent analyst labels are
required separately; polling success never substitutes for observed packets.
"""
import argparse
import json
from pathlib import Path
import time
from urllib.request import urlopen


def snapshot(url):
    with urlopen(url + '/api/health', timeout=10) as response:
        health = json.load(response)
    with urlopen(url + '/api/network-status', timeout=10) as response:
        network = json.load(response)
    return health, network


def assess(health, network, model_version, require_sysmon=False):
    failures = []
    if health.get('mode') != 'live': failures.append('not live')
    if not health.get('model_shadow') or not health.get('model_ready'): failures.append('shadow model unavailable')
    if health.get('model_version') != model_version: failures.append('model changed')
    if network.get('capture') != 'running': failures.append('capture unavailable')
    if require_sysmon and network.get('endpoint') != 'running': failures.append('Sysmon unavailable or degraded')
    for name in ['queue_drops', 'processing_errors', 'capacity_drops']:
        if network.get(name, 0): failures.append(name)
    now = time.time()
    for name in ['collector_heartbeat'] + (['endpoint_heartbeat'] if require_sysmon else []):
        if now - network.get(name, 0) > 15: failures.append(name + ' stale')
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:5000')
    parser.add_argument('--hours', type=float, default=72)
    parser.add_argument('--require-sysmon', action='store_true', help='Also require the Sysmon process collector')
    parser.add_argument('--output', type=Path, default=Path('artifacts/shadow-soak.json'))
    args = parser.parse_args()
    if args.url != 'http://127.0.0.1:5000' or args.hours <= 0:
        parser.error('Use the local server and a positive duration')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    health, network = snapshot(args.url)
    model_version = health.get('model_version')
    started, wall_started = time.monotonic(), time.time()
    initial_packets, initial_flows = network['packet_count'], network['flows_received']
    previous_packets = initial_packets
    run_id = network.get('run_id')
    last_poll = time.monotonic()
    report = dict(status='running', model_version=model_version, started=wall_started,
                  required_seconds=args.hours*3600, samples=0, failures=[],
                  scope='network_and_sysmon' if args.require_sysmon else 'network_shadow_model',
                  note='Collector stability only; independent labeled accuracy remains a separate gate')
    with args.output.with_suffix('.jsonl').open('a', encoding='utf-8') as journal:
        while True:
            try:
                health, network = snapshot(args.url)
                failures = assess(health, network, model_version, args.require_sysmon)
                if time.monotonic() - last_poll > 20: failures.append('polling gap or computer suspended')
                if network.get('run_id') != run_id: failures.append('server restarted')
                if network['packet_count'] < previous_packets: failures.append('collector restarted')
                previous_packets = network['packet_count']
                observed_packets = network['packet_count'] - initial_packets
                observed_flows = network['flows_received'] - initial_flows
            except Exception as exc:
                failures, observed_packets, observed_flows = [str(exc)], 0, 0
            elapsed = time.monotonic() - started
            last_poll = time.monotonic()
            journal.write(json.dumps(dict(timestamp=time.time(), elapsed=elapsed,
                packets=observed_packets, flows=observed_flows, failures=failures))+'\n')
            journal.flush()
            report.update(elapsed_seconds=elapsed, updated=time.time(), samples=report['samples']+1,
                          observed_packets=observed_packets, observed_flows=observed_flows)
            if failures:
                report.update(status='failed', failures=failures)
            elif elapsed >= report['required_seconds']:
                report.update(status='passed' if observed_packets>0 and observed_flows>0 else 'failed',
                              soak_72_hours=elapsed>=72*3600 and observed_packets>0 and observed_flows>0)
                if report['status']=='failed': report['failures']=['No new telemetry observed']
            pending=args.output.with_suffix('.tmp')
            pending.write_text(json.dumps(report,indent=2)); pending.replace(args.output)
            if report['status'] != 'running':
                print(json.dumps(report,indent=2))
                return 0 if report['status']=='passed' else 1
            time.sleep(5)


if __name__=='__main__': raise SystemExit(main())
