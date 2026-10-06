import tempfile
from pathlib import Path
import unittest
import json
import hashlib
import pandas as pd
from training.label_pcaps import LabelIndex
from training.benchmark import clean_splits
from test_system import flow
from backend.detection import Detector
from backend.schemas import FEATURES, SCHEMA


class TrainingIntegrityTests(unittest.TestCase):
    def test_bundled_candidate_loads_in_shadow_with_pinned_dependencies(self):
        path=Path(__file__).resolve().parents[1]/'pretrained/canonical-all-families-v2'
        detector=Detector(path,shadow=True)
        self.assertIsNone(detector.error)
        self.assertIsNotNone(detector.model)
        self.assertEqual(detector.score(flow())['prediction_status'],'shadow')
        self.assertIsNone(Detector(path).model)

    def test_duplicate_vectors_connect_entire_sessions(self):
        from training.train_grouped import components
        frame=pd.DataFrame(dict(session_id=['a','a','b','b','c','d'],
                                _vector=['x','y','y','z','z','other']))
        groups=components(frame)
        self.assertEqual(len(set(groups[:5])),1)
        self.assertNotEqual(groups[0],groups[5])

    def test_capture_connections_keep_different_session_segments_together(self):
        from training.train_grouped import components
        frame=pd.DataFrame(dict(session_id=['segment-a','segment-b','other'],
            _vector=['x','y','z'],sensor_id=['capture']*3,src_ip=['192.0.2.1']*3,
            dst_ip=['192.0.2.2']*3,src_port=[1000,1000,1001],dst_port=[443]*3,proto=[6]*3))
        groups=components(frame)
        self.assertEqual(groups[0],groups[1])
        self.assertNotEqual(groups[0],groups[2])

    def test_unapproved_candidate_is_shadow_only_and_checksum_checked(self):
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            model=RandomForestClassifier(n_estimators=2,random_state=42)
            model.fit([[0]*len(FEATURES),[10000000]*len(FEATURES)],[1,0])
            joblib.dump(model,path/'model.joblib')
            manifest=dict(version='test',schema_version=SCHEMA,features=FEATURES,threshold=.01,
                deployment_approved=False,model_sha256=hashlib.sha256((path/'model.joblib').read_bytes()).hexdigest())
            (path/'manifest.json').write_text(json.dumps(manifest))
            self.assertIsNone(Detector(path).model)
            shadow=Detector(path,shadow=True)
            result=shadow.score(flow())
            self.assertEqual(result['prediction_status'],'shadow')
            self.assertTrue(result['model_results']['random_forest']['is_attack'])
            self.assertFalse(result['is_anomaly'])
            manifest['model_sha256']='invalid'
            (path/'manifest.json').write_text(json.dumps(manifest))
            self.assertIsNone(Detector(path,shadow=True).model)

    def test_day_checkpoint_reuses_only_intact_outputs(self):
        from training.label_pcaps import prepare_day
        from training.benchmark import sha
        from test_system import packet
        from scapy.all import wrpcap
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); raw=root/'raw'; output=root/'prepared'
            (raw/'pcap').mkdir(parents=True); (raw/'traffic_labels').mkdir()
            capture=raw/'pcap/Monday.pcap'; wrpcap(str(capture),[packet()])
            raw_flow=flow()
            labels=raw/'traffic_labels/Monday.parquet'
            pd.DataFrame([{'Source IP':raw_flow['src_ip'],'Destination IP':raw_flow['dst_ip'],
                'Source Port':raw_flow['src_port'],'Destination Port':raw_flow['dst_port'],
                'Protocol':6,'Timestamp':pd.Timestamp(1000,unit='s'),'Flow Duration':1000000,
                'Label':'BENIGN'}]).to_parquet(labels,index=False)
            manifest=dict(status={'pcap/Monday.pcap':{'sha256':sha(capture)},
                'traffic_labels/Monday.parquet':{'sha256':sha(labels)}})
            (raw/'download-manifest.json').write_text(json.dumps(manifest))
            first=prepare_day(raw,output,'Monday',1,manifest)
            self.assertEqual(first['counts']['written'],1)
            self.assertEqual(prepare_day(raw,output,'Monday',1,manifest),first)
            (output/'days/Monday/observations.jsonl').write_text('altered')
            with self.assertRaisesRegex(ValueError,'altered checkpoint'):
                prepare_day(raw,output,'Monday',1,manifest)

    def test_minute_precision_and_ambiguous_label_quarantine(self):
        raw=flow(t=1210)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'labels.parquet'
            row={'Source IP':raw['src_ip'],'Destination IP':raw['dst_ip'],
                 'Source Port':raw['src_port'],'Destination Port':raw['dst_port'],
                 'Protocol':6,'Timestamp':pd.Timestamp(1200,unit='s'),
                 'Flow Duration':100,'Label':'BENIGN'}
            pd.DataFrame([row]).to_parquet(path,index=False)
            idx=LabelIndex([path])
            self.assertEqual(idx.tolerance,60)
            self.assertEqual(idx.match(raw)[0]['label'],0)
            pd.DataFrame([row,dict(row,Label='PortScan')]).to_parquet(path,index=False)
            self.assertEqual(LabelIndex([path]).match(raw),(None,'ambiguous'))

    def test_training_validation_test_fingerprints_disjoint(self):
        parts={k:pd.DataFrame({'_group':g,'_label':[0,1,0]}) for k,g in
               [('train',['a','b','c']),('validation',['d','e','a']),('test',['f','g','d'])]}
        clean,audit=clean_splits(parts)
        self.assertEqual(len(clean['validation']),2)
        self.assertFalse(set(clean['test']['_group']) & set(clean['validation']['_group']))


if __name__=='__main__': unittest.main()
