"""CSV-only research benchmarks. Artifacts are explicitly rejected by live inference.

python -m training.benchmark --dataset cicids2017 --input <directory>
python -m training.benchmark --dataset unsw-nb15 --input <directory>
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, average_precision_score, precision_recall_curve

ROOT = Path(__file__).resolve().parents[1]
CIC_FEATURES = ['Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
    'Total Length of Fwd Packets', 'Total Length of Bwd Packets', 'Fwd Packet Length Max',
    'Fwd Packet Length Min', 'Fwd Packet Length Mean', 'Fwd Packet Length Std',
    'Bwd Packet Length Max', 'Bwd Packet Length Min', 'Bwd Packet Length Mean',
    'Bwd Packet Length Std', 'Flow IAT Mean', 'Flow IAT Std', 'Flow IAT Max',
    'Flow IAT Min', 'FIN Flag Count', 'SYN Flag Count', 'RST Flag Count',
    'PSH Flag Count', 'ACK Flag Count', 'URG Flag Count']
UNSW_FEATURES = ['dur', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate', 'sttl', 'dttl',
    'sload', 'dload', 'sloss', 'dloss', 'sinpkt', 'dinpkt', 'sjit', 'djit',
    'swin', 'dwin', 'tcprtt', 'synack', 'ackdat', 'smean', 'dmean']


def sha(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load_file(path, features, dataset, cap, seed):
    rng = np.random.default_rng(seed)
    retained = pd.DataFrame()
    audit = dict(path=str(path.resolve()), sha256=sha(path), rows_read=0, invalid=0)
    offset = 0
    for chunk in pd.read_csv(path, chunksize=50000, encoding='cp1252', low_memory=False):
        chunk.columns = chunk.columns.str.strip()
        missing = set(features) - set(chunk.columns)
        if missing:
            raise ValueError(f'{path.name}: missing features {sorted(missing)}')
        x = chunk[features].apply(pd.to_numeric, errors='coerce')
        family = (chunk['Label'] if dataset == 'cicids2017' else chunk['attack_cat']).astype(str).str.strip()
        y = family.ne('BENIGN').astype(int) if dataset == 'cicids2017' else pd.to_numeric(chunk['label'], errors='coerce')
        valid = np.isfinite(x).all(axis=1) & x.ge(0).all(axis=1) & y.isin([0, 1])
        audit['rows_read'] += len(chunk)
        audit['invalid'] += int((~valid).sum())
        x['_label'], x['_family'] = y, family
        x['_source'] = path.name
        x['_row'] = np.arange(offset, offset + len(chunk))
        x['_priority'] = rng.random(len(chunk))
        offset += len(chunk)
        retained = pd.concat([retained, x.loc[valid]], ignore_index=True)
        if cap and len(retained) > cap:
            retained = retained.nsmallest(cap, '_priority')
    retained = retained.drop(columns='_priority')
    # Coarse numeric fingerprints group exact and near-identical feature vectors.
    numeric = retained[features].to_numpy(dtype=float)
    exponent = np.floor(np.log10(np.maximum(np.abs(numeric), 1e-12)))
    quantum = np.power(10.0, exponent - 2)
    rounded = np.round(numeric / quantum) * quantum
    retained['_group'] = pd.util.hash_pandas_object(pd.DataFrame(rounded, columns=features), index=False).astype(str).to_numpy()
    audit['sampled'] = len(retained)
    return retained, audit


def threshold_for(y, scores, max_fpr):
    y, scores = np.asarray(y), np.asarray(scores)
    # Evaluate every score boundary, including a reject-all boundary.
    order = np.argsort(-scores, kind='stable')
    sorted_scores, truth = scores[order], y[order]
    ends = np.r_[np.flatnonzero(np.diff(sorted_scores)), len(y)-1]
    tp = np.cumsum(truth)[ends]
    fp = np.cumsum(1-truth)[ends]
    fpr = fp / max(1, (y == 0).sum())
    precision = tp / np.maximum(1, tp + fp)
    recall = tp / max(1, y.sum())
    f1 = 2 * precision * recall / np.maximum(1e-15, precision + recall)
    eligible = np.flatnonzero(fpr <= max_fpr)
    if not len(eligible):
        return float(np.nextafter(scores.max(), np.inf))
    best = eligible[np.argmax(f1[eligible])]
    return float(sorted_scores[ends[best]])


def metrics(y, scores, threshold, family=None):
    y = np.asarray(y, dtype=int)
    prediction = scores >= threshold
    tn, fp, fn, tp = map(int, confusion_matrix(y, prediction, labels=[0, 1]).ravel())
    precision = tp / (tp+fp) if tp+fp else 0.0
    recall = tp / (tp+fn) if tp+fn else None
    result = dict(samples=len(y), attacks=int(y.sum()), benign=int((y == 0).sum()),
        tp=tp, fp=fp, tn=tn, fn=fn, precision=precision, recall=recall,
        fpr=fp/(fp+tn) if fp+tn else None,
        f1=2*precision*(recall or 0)/(precision+(recall or 0)) if precision+(recall or 0) else 0,
        average_precision=float(average_precision_score(y, scores)) if y.sum() else None,
        threshold=float(threshold))
    if family is not None:
        result['families'] = {}
        for name in sorted(set(family)):
            mask = np.asarray(family) == name
            result['families'][name] = dict(samples=int(mask.sum()), flagged=int(prediction[mask].sum()),
                flag_rate=float(prediction[mask].mean()))
    return result


def clean_splits(parts):
    # Test remains independent of training and tuning even without session IDs.
    seen = set()
    result, audit = {}, {}
    for name in ['train', 'validation', 'test']:
        data = parts[name]
        before = len(data)
        data = data.loc[~data['_group'].isin(seen)].drop_duplicates('_group').copy()
        seen.update(data['_group'])
        result[name] = data
        audit[name] = dict(removed_duplicate_or_overlapping=before-len(data), rows=len(data))
        if data['_label'].nunique() < 2:
            raise ValueError(f'{name} must contain both benign and attack samples after cleaning')
    return result, audit


def run(args):
    started = time.time()
    dataset = args.dataset
    features = CIC_FEATURES if dataset == 'cicids2017' else UNSW_FEATURES
    audits = []
    if dataset == 'cicids2017':
        buckets = {k: [] for k in ['train', 'validation', 'test']}
        for path in sorted(args.input.glob('*.csv')):
            name = path.name.lower()
            split = 'train' if any(day in name for day in ['monday', 'tuesday', 'wednesday']) else 'validation' if 'thursday' in name else 'test' if 'friday' in name else None
            if split:
                data, audit = load_file(path, features, dataset, args.max_per_file, args.seed)
                audit['split'] = split
                buckets[split].append(data)
                audits.append(audit)
        if any(not v for v in buckets.values()):
            raise ValueError('Need Monday-Wednesday training, Thursday validation and Friday test CSVs')
        parts = {k: pd.concat(v, ignore_index=True) for k, v in buckets.items()}
        split_policy = 'Monday-Wednesday train; Thursday validation; Friday locked test; family distribution shift is intentional'
    else:
        train, audit = load_file(args.input / 'UNSW_NB15_training-set.csv', features, dataset, args.max_per_file, args.seed)
        audits.append(audit)
        test, audit = load_file(args.input / 'UNSW_NB15_testing-set.csv', features, dataset, args.max_per_file, args.seed)
        audits.append(audit)
        # Whole numeric fingerprint groups share a partition; no label-based splitting.
        val = train['_group'].map(lambda x: int(x) % 5 == 0)
        parts = dict(train=train.loc[~val], validation=train.loc[val], test=test)
        split_policy = 'Supplied CSV filename partitions; training fingerprint groups hashed 80/20 for validation; source sessions unavailable'
    parts, cleaning = clean_splits(parts)
    out = args.output or ROOT / 'artifacts' / 'benchmarks' / (dataset + '-' + time.strftime('%Y%m%d-%H%M%S'))
    out.mkdir(parents=True, exist_ok=False)
    for name, data in parts.items():
        data[['_source', '_row', '_group', '_family', '_label']].to_csv(out / f'{name}-manifest.csv.gz', index=False)
    train, val, test = (parts[k] for k in ['train', 'validation', 'test'])
    x, y = train[features].to_numpy(dtype=float), train['_label'].to_numpy(dtype=int)
    xv, yv = val[features].to_numpy(dtype=float), val['_label'].to_numpy(dtype=int)
    candidates = {
        'logistic_regression': make_pipeline(StandardScaler(), LogisticRegression(max_iter=600, class_weight='balanced', random_state=args.seed)),
        'random_forest': RandomForestClassifier(n_estimators=200, max_depth=18, min_samples_leaf=3,
            class_weight='balanced_subsample', random_state=args.seed, n_jobs=4),
    }
    validation = {}
    for name, model in candidates.items():
        print(f'Training {dataset} {name}: {len(train)} rows', flush=True)
        model.fit(x, y)
        scores = model.predict_proba(xv)[:, 1]
        threshold = threshold_for(yv, scores, args.max_fpr)
        validation[name] = metrics(yv, scores, threshold)
    chosen = max(validation, key=lambda k: validation[k]['f1'])
    selected = candidates[chosen]
    threshold = validation[chosen]['threshold']
    # Anomaly baseline is evaluated independently; it does not override the selected classifier.
    iso = make_pipeline(StandardScaler(), IsolationForest(n_estimators=150, contamination='auto', random_state=args.seed, n_jobs=4))
    iso.fit(x[y == 0])
    iso_val = -iso.score_samples(xv)
    iso_threshold = threshold_for(yv, iso_val, args.max_fpr)
    validation['isolation_forest'] = metrics(yv, iso_val, iso_threshold)
    xt, yt = test[features].to_numpy(dtype=float), test['_label'].to_numpy(dtype=int)
    before = time.perf_counter()
    test_scores = selected.predict_proba(xt)[:, 1]
    elapsed = time.perf_counter()-before
    result = metrics(yt, test_scores, threshold, test['_family'].to_numpy())
    joblib.dump(selected, out / 'model.joblib')
    manifest = dict(version=out.name, dataset=dataset, schema_version=dataset + '-csv-v1',
        deployment_approved=False, purpose='offline_benchmark_only', features=features,
        model_type=chosen, threshold=threshold, model_sha256=sha(out / 'model.joblib'), seed=args.seed)
    report = dict(**manifest, split_policy=split_policy, data_sources=audits, cleaning=cleaning,
        validation=validation, test=result, isolation_forest_test=metrics(yt, -iso.score_samples(xt), iso_threshold),
        baseline_all_benign=metrics(yt, np.zeros(len(yt)), 1.0),
        test_batch_seconds=elapsed, training_seconds=time.time()-started,
        max_validation_fpr=args.max_fpr, cap_per_file=args.max_per_file,
        limitations=['CSV semantics differ from live flow-window-v1; never deploy this artifact live',
            'No packet/session identifiers in selected CSVs; fingerprint grouping cannot prove session independence',
            'Feature-vector deduplication changes prevalence; inspect per-family support',
            'Historical controlled traffic; no claims about current real-world or zero-day detection',
            'Confidence intervals over independent sessions unavailable because session IDs are absent'],
        environment=dict(python=platform.python_version(), dependencies={p: importlib.metadata.version(p) for p in ['scikit-learn', 'numpy', 'pandas', 'joblib']}))
    try:
        report['git_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    except Exception:
        report['git_commit'] = None
    report['training_code_sha256'] = sha(Path(__file__))
    if dataset == 'unsw-nb15' and [a['rows_read'] for a in audits] != [175341, 82332]:
        report['limitations'].append('Supplied filename partition sizes differ from publisher train=175341/test=82332; this is not a standard published-split benchmark')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (out / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    pd.DataFrame(dict(source=test['_source'], row=test['_row'], group=test['_group'],
        family=test['_family'], truth=yt, score=test_scores, prediction=(test_scores >= threshold).astype(int))).to_csv(out / 'test-predictions.csv.gz', index=False)
    print(json.dumps({'output': str(out), 'model': chosen, 'test': result}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=['cicids2017', 'unsw-nb15'], required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--max-per-file', type=int, default=60000, help='Uniform reservoir cap; 0 keeps all rows')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max-fpr', type=float, default=0.001)
    args = parser.parse_args()
    if args.max_per_file < 0 or not 0 <= args.max_fpr <= 1:
        parser.error('Invalid row cap or false-positive budget')
    run(args)
