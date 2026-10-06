"""Join canonical windows to verified CIC flow labels without feeding labels to extraction."""
import argparse
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


def prepare(raw, output):
    manifest = json.loads((raw/'download-manifest.json').read_text())
    required = [x['path'] for x in manifest['files'] if x['path'].startswith(('pcap/','traffic_labels/'))]
    if any(manifest['status'].get(x,{}).get('state') != 'verified' for x in required):
        raise ValueError('Full capture and label downloads must be verified before training extraction')
    output.mkdir(parents=True,exist_ok=False)
    report = dict(source_manifest_sha256=sha(raw/'download-manifest.json'), mirror_revision=manifest['revision'],
                  label_precision='inferred per file; minute-truncated labels use <=60 second uncertainty', files=[], status='extracting')
    seen_vectors = set()
    for split, days in [('train',['Monday','Tuesday','Wednesday']),('validation',['Thursday']),('test',['Friday'])]:
        with (output/f'{split}.jsonl').open('w',encoding='utf-8') as observations, (output/f'{split}-labels.csv').open('w',newline='',encoding='utf-8') as labels_out:
            writer=csv.DictWriter(labels_out,fieldnames=['event_id','label','family','label_source']); writer.writeheader()
            current_vectors=set()
            for day in days:
                pcap=next((raw/'pcap').glob(day+'*.pcap'))
                label_paths=list((raw/'traffic_labels').glob(day+'*.parquet'))
                index=LabelIndex(label_paths)
                counts=defaultdict(int)
                extraction_stats={}
                started=time.monotonic()
                capture_hash=manifest['status']['pcap/'+pcap.name]['sha256']
                for flow in read_pcap(pcap,'pcap:'+capture_hash[:16],extraction_stats):
                    counts['windows']+=1
                    label,reason=index.match(flow); counts[reason]+=1
                    if label:
                        vector=hashlib.sha256(json.dumps([flow[k] for k in FEATURES]).encode()).digest()
                        if vector in seen_vectors:
                            counts['cross_split_duplicate']+=1
                            continue
                        current_vectors.add(vector)
                        observations.write(json.dumps(flow,allow_nan=False)+'\n')
                        writer.writerow(dict(event_id=flow['event_id'],**label))
                        counts['written']+=1
                    if counts['windows']%100000 == 0:
                        print(day,dict(counts),flush=True)
                report['files'].append(dict(file=pcap.name,split=split,counts=dict(counts),extraction=extraction_stats,label_tolerance_seconds=index.tolerance,seconds=time.monotonic()-started))
                (output/'extraction-report.json').write_text(json.dumps(report,indent=2))
            seen_vectors.update(current_vectors)
    report['status']='complete'
    (output/'extraction-report.json').write_text(json.dumps(report,indent=2))
    for entry in report['files']:
        counts=entry['counts']
        if entry['extraction']['capacity_drops']:
            raise ValueError('Extractor capacity drops detected; adjust bounds and re-extract before training')
        if counts.get('matched',0)/max(1,counts['windows']) < .8:
            raise ValueError('Label alignment below 80%; inspect extraction-report.json before training')
    return output


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw',type=Path,default=Path('data/raw/cicids2017'))
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); prepare(a.raw,a.output)
