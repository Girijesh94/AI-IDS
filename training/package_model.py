"""Package a locally trained candidate without approving it or copying raw data."""
import argparse
import json
from pathlib import Path
import joblib
from backend.schemas import SCHEMA, FEATURES
from training.benchmark import sha


def package(source, output):
    manifest=json.loads((source/'manifest.json').read_text())
    report=json.loads((source/'report.json').read_text())
    if manifest['schema_version']!=SCHEMA or manifest['features']!=FEATURES:
        raise ValueError('Incompatible feature contract')
    if sha(source/'model.joblib')!=manifest['model_sha256']:
        raise ValueError('Source model checksum mismatch')
    if manifest['deployment_approved']:
        raise ValueError('This packager is for unapproved candidates only')
    if output.exists(): raise ValueError('Destination exists; choose a new directory')
    model=joblib.load(source/'model.joblib')
    if list(model.classes_)!=[0,1] or model.n_features_in_!=len(FEATURES):
        raise ValueError('Unexpected estimator shape or classes')
    output.mkdir(parents=True)
    joblib.dump(model,output/'model.joblib',compress=3)
    manifest['model_sha256']=sha(output/'model.joblib')
    manifest['packaging']='joblib compression level 3; identical estimator'
    report['manifest']=manifest
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    test=report['test']
    lines=['# Traffic candidate model card','',f"Version: `{manifest['version']}`. **Unapproved; shadow evaluation only.**",'',
        '## Artifact and intended use','',
        'A 200-tree random forest using thirteen `flow-window-v1` numeric features from the shared live/replay state machine. Fit with the pinned dependencies. Compressed joblib artifact: load only a trusted copy with the matching manifest checksum. The package contains no raw traffic or local process data.','',
        '## Data and partitioning','',
        'Five CICIDS2017 captures and independent flow labels from the pinned public mirror revision recorded in the full report. Capture and label hashes were rechecked. Minute-level uncertainty is reported; ambiguous/unmatched joins are excluded. A deterministic one-in-ten complete-session sample was selected without labels.','',
        'All segments with the same bidirectional capture/endpoint tuple are connected. Shared feature vectors also connect their entire sessions. Three stratified folds train the model, one chooses the threshold under a 0.1% validation false-positive budget, and the untouched fifth fold evaluates it. Each connected component belongs to one partition. Captures are shared across partitions: this is an in-dataset test, not independent-network accuracy.','',
        '## Held-out results','',f"{test['samples']:,} windows: precision {test['precision']:.4%}, attack recall {test['recall']:.4%}, benign false-positive rate {test['fpr']:.4%}. Threshold {manifest['threshold']:.8f}. Scores are classifier outputs, not calibrated confidence.",'',
        '| Family | Test windows | Flagged | Recall / flag rate |','| --- | ---: | ---: | ---: |']
    for family,row in test['families'].items():
        lines.append(f"| {family.replace(chr(150),'–')} | {row['samples']:,} | {row['flagged']:,} | {row['flag_rate']:.2%} |")
    lines+=['','## Limits and release requirements','']+report.get('limitations',[])+['',
        'The separate strict Friday candidate detected only 35.4% of attacks. That retained report is a generalization stress result, not an independent test of this all-family model, which trains with Friday labels.','',
        'Weak or tiny family samples cannot establish reliable coverage. Production requires independent reviewed live accuracy, supported-family scope, full Windows collectors, a 72-hour soak, recovery evidence and independent approval. The manifest remains deployment_approved=false.','',
        '[CICIDS2017 publisher](https://www.unb.ca/cic/datasets/ids-2017.html) · [Mirror](https://huggingface.co/datasets/bvsam/cic-ids-2017) · [Full report](report.json)']
    (output/'MODEL_CARD.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Packaged candidate',output,'bytes',(output/'model.joblib').stat().st_size)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();package(args.input,args.output)
