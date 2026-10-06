import tempfile
from pathlib import Path
import unittest
import pandas as pd
from training.label_pcaps import LabelIndex
from training.benchmark import clean_splits
from test_system import flow


class TrainingIntegrityTests(unittest.TestCase):
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
