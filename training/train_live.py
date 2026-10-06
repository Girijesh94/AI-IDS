"""Train a canonical candidate from explicit capture splits and reviewed labels.

Input directory contains train.jsonl, validation.jsonl and test.jsonl, with matching
*-labels.csv files: event_id,label,family,label_source. Every observation must have
one reviewed label. Keep unknown rows out of supervised datasets explicitly.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from backend.schemas import FEATURES, SCHEMA, validate_flow
from .benchmark import sha, metrics, threshold_for


def train(directory, output, session_sample_modulus=10):
    data, manifests, seen_sessions, seen_captures, seen_vectors = {}, {}, set(), set(), set()
    for split in ['train', 'validation', 'test']:
        path = directory / f'{split}.jsonl'
        labels_path = directory / f'{split}-labels.csv'
        observations = []
        rows_read = 0
        with path.open() as f:
            for line in f:
                if not line.strip():
                    continue
                observation = validate_flow(json.loads(line))
                rows_read += 1
                bucket = int(hashlib.sha256(observation['session_id'].encode()).hexdigest()[:8], 16)
                if bucket % session_sample_modulus == 0:
                    observations.append(observation)
        if not observations:
            raise ValueError(f'{split}: no selected sessions; reduce --session-sample-modulus')
        rows = pd.DataFrame(observations)
        event_ids = set(rows['event_id'])
        labels = pd.concat([chunk.loc[chunk['event_id'].isin(event_ids)]
                            for chunk in pd.read_csv(labels_path, chunksize=100000)], ignore_index=True)
        if not {'event_id', 'label', 'family', 'label_source'} <= set(labels.columns):
            raise ValueError('Labels require event_id,label,family,label_source')
        if not labels['label_source'].isin(['analyst', 'verified_lab', 'verified_benchmark']).all():
            raise ValueError('Only independently reviewed labels are accepted')
        rows = rows.merge(labels, on='event_id', validate='one_to_one', how='left')
        if not rows['label'].isin([0, 1]).all() or rows['label'].nunique() != 2:
            raise ValueError(f'{split}: independently labeled benign and attack observations required')
        sessions, captures = set(rows['session_id']), set(rows['sensor_id'])
        vectors = set(pd.util.hash_pandas_object(rows[FEATURES], index=False))
        if sessions & seen_sessions or captures & seen_captures or vectors & seen_vectors:
            raise ValueError(f'{split}: capture/session/feature duplicate overlap; rebuild independent partitions')
        seen_sessions.update(sessions); seen_captures.update(captures); seen_vectors.update(vectors)
        data[split] = rows
        manifests[split] = dict(data_sha256=sha(path), labels_sha256=sha(labels_path),
                               rows_read=rows_read, rows=len(rows), sessions=len(sessions), captures=len(captures),
                               session_sample_modulus=session_sample_modulus)
    model = RandomForestClassifier(n_estimators=200, max_depth=18, min_samples_leaf=3,
                                   class_weight='balanced_subsample', random_state=42, n_jobs=4)
    model.fit(data['train'][FEATURES].to_numpy(), data['train']['label'])
    val = data['validation']
    threshold = threshold_for(val['label'], model.predict_proba(val[FEATURES].to_numpy())[:, 1], .001)
    test = data['test']
    result = metrics(test['label'], model.predict_proba(test[FEATURES].to_numpy())[:, 1], threshold, test['family'])
    output.mkdir(parents=True, exist_ok=False)
    joblib.dump(model, output / 'model.joblib')
    manifest = dict(version=output.name, schema_version=SCHEMA, features=FEATURES,
                    threshold=threshold, deployment_approved=False, purpose='candidate_pending_shadow_pilot',
                    model_sha256=sha(output / 'model.joblib'), model_type='random_forest')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    (output / 'report.json').write_text(json.dumps(dict(manifest=manifest, inputs=manifests, test=result,
        release_gates={'independent_test': True, 'shadow_pilot': False, 'soak_72_hours': False},
        note='Candidate only. Complete live release gates before deployment approval.'), indent=2))
    print(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--session-sample-modulus', type=int, default=10,
                        help='Keep one in N complete sessions, independent of labels; 1 keeps all')
    args = parser.parse_args()
    if args.session_sample_modulus < 1:
        parser.error('Session sample modulus must be >=1')
    train(args.input, args.output, args.session_sample_modulus)
