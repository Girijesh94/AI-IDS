"""Report release evidence without approving a model or inventing live labels."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sqlite3
import numpy as np
from training.benchmark import metrics, sha


def build(model, database, soak):
    manifest=json.loads((model/'manifest.json').read_text())
    offline=json.loads((model/'report.json').read_text())
    version=manifest['version']
    if sha(model/'model.joblib') != manifest['model_sha256']:
        raise ValueError('Model checksum mismatch')
    groups=defaultdict(list)
    connection=sqlite3.connect(f'file:{database.resolve().as_posix()}?mode=ro',uri=True)
    try:
        for payload,label in connection.execute("SELECT e.payload,l.label FROM events e LEFT JOIN labels l ON e.event_id=l.event_id WHERE e.kind='network' AND e.mode='live'"):
            event=json.loads(payload)
            result=event.get('model_results',{}).get('random_forest',{})
            if event.get('model_version')==version and result.get('shadow'):
                groups[event['session_id']].append((label,result['score']))
    finally: connection.close()
    # A session is eligible only if every observed window was independently reviewed.
    reviewed=[rows for rows in groups.values() if all(label in (0,1) for label,_ in rows)]
    truth=np.array([max(label for label,_ in rows) for rows in reviewed],dtype=int)
    scores=np.array([max(score for _,score in rows) for rows in reviewed],dtype=float)
    pilot=metrics(truth,scores,manifest['threshold']) if len(truth) else None
    soak_report=json.loads(soak.read_text()) if soak.exists() else {}
    test=offline['test']
    families={name:row for name,row in test['families'].items() if name!='BENIGN'}
    gates=dict(
        held_out_recall=test['recall'] is not None and test['recall']>=.8,
        held_out_fpr=test['fpr'] is not None and test['fpr']<=.001,
        supported_families=bool(families) and all(row['samples']>=100 and row['flag_rate']>=.8 for row in families.values()),
        reviewed_live_support=pilot is not None and pilot['benign']>=3000 and pilot['attacks']>=100,
        reviewed_live_accuracy=pilot is not None and pilot['recall'] is not None and pilot['recall']>=.8 and pilot['fpr']<=.001,
        soak_72_hours=soak_report.get('status')=='passed' and soak_report.get('soak_72_hours') is True and soak_report.get('model_version')==version and soak_report.get('scope')=='network_and_sysmon')
    return dict(version=version,model_sha256=manifest['model_sha256'],gates=gates,
        ready_for_independent_review=all(gates.values()),deployment_approved=manifest['deployment_approved'],
        held_out=test,live_reviewed_sessions=pilot,unreviewed_or_partial_sessions=len(groups)-len(reviewed),
        note='Thresholds are minimum project targets, not proof of universal accuracy. Live review selection and scenario coverage must be audited by the reviewer; this report never promotes the model.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,default=Path('pretrained/canonical-all-families-v2'))
    parser.add_argument('--database',type=Path,default=Path('data/live.db'))
    parser.add_argument('--soak',type=Path,default=Path('artifacts/shadow-soak.json'))
    parser.add_argument('--output',type=Path,default=Path('artifacts/release-report.json'))
    args=parser.parse_args()
    report=build(args.model,args.database,args.soak)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
