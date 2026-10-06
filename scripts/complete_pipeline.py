"""Continue authorized data preparation after the active download finishes.

Writes progress to artifacts/pipeline-status.json. Does not deploy an unqualified
candidate or change system drivers. Safe to stop and inspect at any stage.
"""
import json
import os
from pathlib import Path
import time
import traceback
import argparse

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, default=ROOT/'data/prepared/canonical-v3')
    parser.add_argument('--model', type=Path, default=ROOT/'models/canonical-v3')
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    # OS-held lock is released after interruption; stale PID files are not locks.
    import msvcrt
    (ROOT/'artifacts').mkdir(exist_ok=True)
    lock = (ROOT/'artifacts/pipeline.lock').open('a+b')
    lock.seek(0)
    if not lock.read(1):
        lock.write(b'0'); lock.flush()
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        raise RuntimeError('A continuation process is already running')
    status_file=ROOT/'artifacts/pipeline-status.json'
    def update(stage,**details):
        status_file.parent.mkdir(parents=True,exist_ok=True)
        pending=status_file.with_suffix('.tmp')
        pending.write_text(json.dumps(dict(stage=stage,updated=time.time(),pid=os.getpid(),**details),indent=2))
        pending.replace(status_file)
        print(stage,details,flush=True)
    raw=ROOT/'data/raw/cicids2017'
    update('waiting_for_downloads')
    while True:
        path=raw/'download-manifest.json'
        if path.exists():
            try:
                manifest=json.loads(path.read_text())
                needed=[e['path'] for e in manifest['files'] if e['path'].startswith(('pcap/','traffic_labels/'))]
                states=manifest.get('status',{})
                if any(states.get(p,{}).get('state')=='failed' for p in needed):
                    update('download_failed',action='Resume with python -m training.download')
                    raise RuntimeError('Download failed; resume with python -m training.download')
                if needed and all(states.get(p,{}).get('state')=='verified' for p in needed): break
                update('waiting_for_downloads',verified=sum(states.get(p,{}).get('state')=='verified' for p in needed),total=len(needed))
            except (OSError,json.JSONDecodeError):
                pass
        time.sleep(30)
    features=args.prepared.resolve()
    output=args.model.resolve()
    try:
        # Load the validated implementation after downloads, not hours before it is needed.
        from training.label_pcaps import prepare
        from training.train_live import train
        update('extracting_and_joining_labels',output=str(features))
        prepare(raw,features,workers=args.workers)
        update('training_candidate',output=str(output))
        if output.exists():
            from training.benchmark import sha
            report=json.loads((output/'report.json').read_text())
            saved=report['manifest']
            if saved['model_sha256'] != sha(output/'model.joblib'):
                raise RuntimeError('Existing candidate checksum mismatch; preserve it for inspection')
            for split, entry in report['inputs'].items():
                if entry['data_sha256'] != sha(features/f'{split}.jsonl') or entry['labels_sha256'] != sha(features/f'{split}-labels.csv'):
                    raise RuntimeError('Existing candidate inputs differ; choose a new --model destination')
            print('Reusing verified candidate',output,flush=True)
        else:
            train(features,output)
        update('candidate_ready_for_review',output=str(output),
               remaining=['independent shadow pilot','72-hour soak','review release thresholds before promotion'])
    except Exception as exc:
        update('failed',error=str(exc),traceback=traceback.format_exc())
        raise


if __name__=='__main__': main()
