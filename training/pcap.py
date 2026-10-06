"""Prepare canonical observations or replay PCAPs through the real application."""
import argparse
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path
from backend.features import read_pcap
from backend.config import Settings
from backend.runtime import Runtime
from backend.storage import Store
from .benchmark import sha


def prepare(args):
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    source_hash = sha(args.input)
    sensor = 'pcap:' + source_hash[:16]
    with args.output.open('x', encoding='utf-8') as out:
        for flow in read_pcap(args.input, sensor):
            out.write(json.dumps(flow, allow_nan=False) + '\n')
            count += 1
    args.output.with_suffix('.manifest.json').write_text(json.dumps(dict(
        input=str(args.input.resolve()), sha256=source_hash, schema_version='flow-window-v1',
        output_sha256=sha(args.output), observations=count, labels='not supplied'), indent=2))
    print(f'Prepared {count} observations: {args.output}')


def replay(args):
    count = 0
    if args.url:
        if args.url.rstrip('/') != 'http://127.0.0.1:5000':
            raise ValueError('Replay endpoint must be local http://127.0.0.1:5000')
        with urllib.request.urlopen(args.url.rstrip('/') + '/api/health', timeout=10) as response:
            if json.load(response)['mode'] != 'replay':
                raise ValueError('Start the server in replay mode to keep live telemetry separate')
    sensor = 'pcap:' + sha(args.input)[:16]
    runtime = None
    if not args.url:
        settings = Settings(database=args.database.resolve(), mode='replay', model=args.model)
        runtime = Runtime(settings, Store(settings.database))
    for flow in read_pcap(args.input, sensor):
        if runtime:
            runtime.process(flow, 'replay')
        else:
            if args.url.rstrip('/') != 'http://127.0.0.1:5000':
                raise ValueError('Replay endpoint must be local http://127.0.0.1:5000')
            data = json.dumps(flow).encode()
            req = urllib.request.Request(args.url.rstrip('/') + '/api/ingest', data=data,
                headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + os.getenv('IDS_TOKEN', '')})
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        response.read()
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(0.5)
        count += 1
    print(f'Replayed {count} windows; duplicate event IDs are idempotent')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('replay')
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--database', type=Path, default=Path('data/replay.db'))
    p.add_argument('--model', type=Path)
    p.add_argument('--url')
    args = parser.parse_args()
    (prepare if args.action == 'prepare' else replay)(args)
