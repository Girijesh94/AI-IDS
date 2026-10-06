"""Deterministic inference; no evaluation label or sender score is consulted."""
from collections import OrderedDict, deque
import hashlib
import json
import math
from pathlib import Path
from .schemas import SCHEMA, FEATURES


class Detector:
    def __init__(self, artifact=None):
        self.model = None
        self.manifest = {}
        self.error = None
        self.history = OrderedDict()
        if artifact:
            try:
                import joblib
                artifact = Path(artifact)
                self.manifest = json.loads((artifact / 'manifest.json').read_text())
                if (self.manifest.get('schema_version') != SCHEMA or
                    self.manifest.get('features') != FEATURES or
                    self.manifest.get('deployment_approved') is not True):
                    raise ValueError('Model is not approved for the live feature contract')
                threshold=float(self.manifest['threshold'])
                if not math.isfinite(threshold) or not 0 <= threshold <= 1:
                    raise ValueError('Invalid model decision threshold')
                model_file = artifact / 'model.joblib'
                if hashlib.sha256(model_file.read_bytes()).hexdigest() != self.manifest['model_sha256']:
                    raise ValueError('Model checksum mismatch')
                # Only load locally trained/approved artifacts. Pickle is not a safe interchange format.
                self.model = joblib.load(model_file)
                if list(self.model.classes_) != [0, 1]:
                    raise ValueError('Expected a binary benign/attack classifier')
                if self.model.n_features_in_ != len(FEATURES):
                    raise ValueError('Model feature dimension mismatch')
            except Exception as exc:
                self.error = str(exc)
                self.model = None

    def score(self, flow):
        reasons, score = [], 0.0
        now = flow['timestamp']
        key = (flow['sensor_id'], flow['src_ip'])
        history = self.history.setdefault(key, deque(maxlen=4096))
        self.history.move_to_end(key)
        while history and now - history[0][0] > 60:
            history.popleft()
        # Count TCP connection attempts, not every window of established transfers.
        if flow['proto'] == 6 and flow['tcp_syn'] and not flow['dst2src_pkts']:
            history.append((now, flow['dst_ip'], flow['dst_port']))
        if len(self.history) > 10000:
            self.history.popitem(last=False)
        ports = {x[2] for x in history if x[1] == flow['dst_ip']}
        hosts = {x[1] for x in history if x[2] == flow['dst_port']}
        if len(ports) >= 20 or len(hosts) >= 20:
            score = 0.8
            reasons.append('scan_rule: >=20 distinct unanswered TCP targets in 60 seconds')
        model_results = {}
        if self.model is not None:
            probability = float(self.model.predict_proba([[flow[k] for k in FEATURES]])[0, 1])
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError('Model returned an invalid score')
            threshold = float(self.manifest['threshold'])
            prediction = probability >= threshold
            model_results['random_forest'] = dict(score=probability, is_attack=prediction,
                                                  reason=f'Classifier threshold {threshold:.4f}')
            if prediction:
                reasons.append('flow_classifier: suspicious traffic pattern')
                score = max(score, probability)
        attack = bool(reasons)
        return dict(score=score, is_anomaly=attack, severity='high' if attack else 'low',
                    reason='; '.join(reasons) or 'No detector triggered; this is not proof of benign activity',
                    model_results=model_results, model_version=self.manifest.get('version', 'none'),
                    rule_version='scan-v1', prediction_status='scored' if self.model is not None else 'rules_only')
