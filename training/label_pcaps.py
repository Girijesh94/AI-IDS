"""Join canonical windows to verified CIC flow labels without feeding labels to extraction."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import os
import shutil
from bisect import bisect_right
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import time
import pandas as pd
from backend.features import read_pcap
from backend.schemas import FEATURES
from .benchmark import sha


def key(a, b, ap, bp, proto):
    endpoints = sorted([(str(a), int(ap)), (str(b), int(bp))])
    return tuple(endpoints) + (int(proto),)


class LabelIndex:
    def __init__(self, paths):
        records = defaultdict(list)
        cols = ['Source IP', 'Destination IP', 'Source Port', 'Destination Port',
                'Protocol', 'Timestamp', 'Flow Duration', 'Label']
        self.rows = 0
        self.tolerance = 1.0
        for path in paths:
            frame = pd.read_parquet(path, columns=cols)
            stamps = pd.to_datetime(frame['Timestamp'], utc=True).dt.as_unit('ns')
            starts = stamps.astype('int64') / 1e9
            # Some CIC labels omit seconds. Do not pretend these timestamps are precise.
            if len(starts) and ((starts % 60) == 0).all():
                self.tolerance = 60.0
            for values, start in zip(frame.itertuples(index=False, name=None), starts):
                a,b,ap,bp,proto,stamp,duration,label = values
                if pd.isna(start) or pd.isna(duration) or duration < 0:
                    continue
                records[key(a,b,ap,bp,proto)].append((float(start), float(start)+float(duration)/1e6, str(label)))
                self.rows += 1
        self.records = {}
        for k, values in records.items():
            values.sort()
            maximum, prefixes = float('-inf'), []
            for row in values:
                maximum = max(maximum, row[1]); prefixes.append(maximum)
            self.records[k] = ([r[0] for r in values], values, prefixes)

    def match(self, flow):
        entry = self.records.get(key(flow['src_ip'],flow['dst_ip'],flow['src_port'],flow['dst_port'],flow['proto']))
        if entry is None:
            return None, 'unmatched_tuple'
        starts, rows, prefixes = entry
        end, start = flow['timestamp'], flow['timestamp']-flow['duration']
        labels = set()
        # Truncated timestamps can precede the actual start by up to their precision.
        i = bisect_right(starts, start+1)-1
        while i >= 0 and prefixes[i] >= end-self.tolerance:
            s,e,label = rows[i]
            if s <= start+1 and e >= end-self.tolerance:
                labels.add(label)
            i -= 1
        if len(labels) != 1:
            return None, 'ambiguous' if labels else 'unmatched_time'
        label = next(iter(labels))
        return dict(label=0 if label == 'BENIGN' else 1, family=label, label_source='verified_benchmark'), 'matched'


DAYS = [('train', 'Monday'), ('train', 'Tuesday'), ('train', 'Wednesday'),
        ('validation', 'Thursday'), ('test', 'Friday')]
PREPARATION_VERSION = 'canonical-resumable-v3'


def prepare_day(raw, output, day, modulus, manifest):
    """Commit a day atomically. A restart reuses only checksum-verified results."""
    folder = output / 'days' / day
    report_path = folder / 'report.json'
    pcap = next((raw / 'pcap').glob(day + '*.pcap'))
    capture_hash = manifest['status']['pcap/' + pcap.name]['sha256']
    expected = dict(version=PREPARATION_VERSION, capture_sha256=capture_hash,
                    session_sample_modulus=modulus,
                    source_manifest_sha256=sha(raw / 'download-manifest.json'),
                    extractor_sha256=sha(Path(__file__).parents[1] / 'backend/features.py'))
    if report_path.exists():
        saved = json.loads(report_path.read_text())
        if (all(saved.get(k) == v for k, v in expected.items()) and
                saved['data_sha256'] == sha(folder / 'observations.jsonl') and
                saved['labels_sha256'] == sha(folder / 'labels.csv')):
            print(day, 'reusing verified checkpoint', flush=True)
            return saved
        raise ValueError(f'{day}: incompatible or altered checkpoint; use a new output directory')
    label_paths = sorted((raw / 'traffic_labels').glob(day + '*.parquet'))
    if sha(pcap) != capture_hash:
        raise ValueError(f'{day}: capture checksum no longer matches download manifest')
    for path in label_paths:
        if sha(path) != manifest['status']['traffic_labels/' + path.name]['sha256']:
            raise ValueError(f'{day}: label checksum mismatch')
    index = LabelIndex(label_paths)
    folder.mkdir(parents=True, exist_ok=True)
    counts, extraction_stats = defaultdict(int), {}
    started = time.monotonic()
    data_part, labels_part = folder / 'observations.partial', folder / 'labels.partial'
    with data_part.open('w', encoding='utf-8') as observations, labels_part.open('w', newline='', encoding='utf-8') as labels_out:
        writer = csv.DictWriter(labels_out, fieldnames=['event_id', 'label', 'family', 'label_source'])
        writer.writeheader()
        for flow in read_pcap(pcap, 'pcap:' + capture_hash[:16], extraction_stats):
            counts['windows'] += 1
            label, reason = index.match(flow)
            counts[reason] += 1
            # Same deterministic complete-session sampling used by the trainer,
            # moved before writing to bound disk and RAM; labels never select rows.
            bucket = int(hashlib.sha256(flow['session_id'].encode()).hexdigest()[:8], 16)
            if bucket % modulus == 0 and label:
                observations.write(json.dumps(flow, allow_nan=False) + '\n')
                writer.writerow(dict(event_id=flow['event_id'], **label))
                counts['written'] += 1
            if counts['windows'] % 100000 == 0:
                progress = dict(day=day, counts=dict(counts), elapsed_seconds=time.monotonic()-started)
                (folder / 'progress.json').write_text(json.dumps(progress))
                print(day, dict(counts), flush=True)
    if extraction_stats['capacity_drops']:
        raise ValueError(f'{day}: extractor capacity drops; do not train')
    if counts.get('matched', 0) / max(1, counts['windows']) < .8:
        raise ValueError(f'{day}: label alignment below 80%; do not train')
    data_part.replace(folder / 'observations.jsonl')
    labels_part.replace(folder / 'labels.csv')
    report = dict(expected, file=pcap.name, counts=dict(counts), extraction=extraction_stats,
                  label_tolerance_seconds=index.tolerance, seconds=time.monotonic()-started,
                  data_sha256=sha(folder / 'observations.jsonl'), labels_sha256=sha(folder / 'labels.csv'))
    pending = folder / 'report.tmp'
    pending.write_text(json.dumps(report, indent=2))
    pending.replace(report_path)
    return report


def prepare(raw, output, workers=3, session_sample_modulus=10):
    raw, output = Path(raw), Path(output)
    if session_sample_modulus < 1 or workers < 1:
        raise ValueError('Workers and session sample modulus must be positive')
    manifest = json.loads((raw / 'download-manifest.json').read_text())
    required = [x['path'] for x in manifest['files'] if x['path'].startswith(('pcap/', 'traffic_labels/'))]
    if any(manifest['status'].get(x, {}).get('state') != 'verified' for x in required):
        raise ValueError('Full capture and label downloads must be verified before extraction')
    output.mkdir(parents=True, exist_ok=True)
    report = dict(source_manifest_sha256=sha(raw / 'download-manifest.json'), mirror_revision=manifest['revision'],
                  preparation_version=PREPARATION_VERSION, session_sample_modulus=session_sample_modulus,
                  label_precision='inferred per file; minute-truncated labels use <=60 second uncertainty',
                  files=[], status='extracting')
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(prepare_day, raw, output, day, session_sample_modulus, manifest) for _, day in DAYS]
        for (split, day), future in zip(DAYS, futures):
            entry = dict(future.result(), split=split)
            report['files'].append(entry)
            (output / 'extraction-report.json').write_text(json.dumps(report, indent=2))
    seen_vectors = set()
    for split in ['train', 'validation', 'test']:
        current_vectors = set()
        removed = 0
        with (output / f'{split}.jsonl.partial').open('w', encoding='utf-8') as observations, (output / f'{split}-labels.csv.partial').open('w', newline='', encoding='utf-8') as labels_out:
            writer = csv.DictWriter(labels_out, fieldnames=['event_id', 'label', 'family', 'label_source'])
            writer.writeheader()
            for day_split, day in DAYS:
                if day_split != split:
                    continue
                folder = output / 'days' / day
                with (folder / 'observations.jsonl').open(encoding='utf-8') as source, (folder / 'labels.csv').open(newline='', encoding='utf-8') as label_source:
                    reader = csv.DictReader(label_source)
                    for line, label in zip(source, reader, strict=True):
                        flow = json.loads(line)
                        if flow['event_id'] != label['event_id']:
                            raise ValueError('Checkpoint observation/label order mismatch')
                        vector = hashlib.sha256(json.dumps([flow[k] for k in FEATURES]).encode()).digest()
                        if vector in seen_vectors:
                            removed += 1
                            continue
                        current_vectors.add(vector)
                        observations.write(line)
                        writer.writerow(label)
        seen_vectors.update(current_vectors)
        (output / f'{split}.jsonl.partial').replace(output / f'{split}.jsonl')
        (output / f'{split}-labels.csv.partial').replace(output / f'{split}-labels.csv')
        report.setdefault('cross_split_duplicates_removed', {})[split] = removed
    report['status'] = 'complete'
    pending = output / 'extraction-report.tmp'
    pending.write_text(json.dumps(report, indent=2))
    pending.replace(output / 'extraction-report.json')
    return output


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw',type=Path,default=Path('data/raw/cicids2017'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--workers',type=int,default=3)
    p.add_argument('--session-sample-modulus',type=int,default=10)
    a=p.parse_args(); prepare(a.raw,a.output,a.workers,a.session_sample_modulus)
