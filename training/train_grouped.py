"""Fit all available CIC families using session and feature component splits.

This is an in-dataset grouped evaluation, not an independent capture evaluation.
The strict Friday holdout result must remain visible as the generalization stress
check. Neither result authorizes production use without an independent live pilot.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from backend.schemas import FEATURES, SCHEMA, validate_flow
from training.benchmark import metrics, threshold_for, sha


def components(rows):
    parents = {}
    def find(key):
        parents.setdefault(key,key)
        root=key
        while parents[root]!=root: root=parents[root]
        while parents[key]!=key:
            previous=parents[key]; parents[key]=root; key=previous
        return root
    first={}
    connections={}
    has_endpoints={'sensor_id','src_ip','dst_ip','src_port','dst_port','proto'} <= set(rows.columns)
    if has_endpoints:
        for row in rows[['session_id','sensor_id','src_ip','dst_ip','src_port','dst_port','proto']].itertuples(index=False,name=None):
            session,sensor,src,dst,sport,dport,proto=row
            endpoints=tuple(sorted([(src,int(sport)),(dst,int(dport))]))
            connection=(sensor,endpoints,int(proto))
            if connection in connections:
                a,b=find(session),find(connections[connection])
                if a!=b: parents[max(a,b)]=min(a,b)
            else:
                connections[connection]=session;find(session)
    for session, vector in zip(rows.session_id, rows._vector):
        if vector in first:
            a,b=find(session),find(first[vector])
            if a!=b: parents[max(a,b)]=min(a,b)
        else:
            first[vector]=session; find(session)
    return [find(session) for session in rows.session_id]


def train(directory, output):
    if output.exists(): raise ValueError('Use a new model output directory')
    prepared=json.loads((directory/'extraction-report.json').read_text())
    if prepared['status']!='complete': raise ValueError('Preparation is incomplete')
    frames, sources=[],[]
    for day in ['Monday','Tuesday','Wednesday','Thursday','Friday']:
        folder=directory/'days'/day
        report=json.loads((folder/'report.json').read_text())
        if sha(folder/'observations.jsonl')!=report['data_sha256'] or sha(folder/'labels.csv')!=report['labels_sha256']:
            raise ValueError('Preparation checksum mismatch')
        observations=[]
        with (folder/'observations.jsonl').open(encoding='utf-8') as stream:
            for line in stream: observations.append(validate_flow(json.loads(line)))
        frame=pd.DataFrame(observations)
        labels=pd.read_csv(folder/'labels.csv')
        if not labels.label_source.eq('verified_benchmark').all(): raise ValueError('Independent labels required')
        frame=frame.merge(labels,on='event_id',how='left',validate='one_to_one')
        if not frame.label.isin([0,1]).all(): raise ValueError('Missing labels')
        frames.append(frame); sources.append(dict(day=day,**report))
    rows=pd.concat(frames,ignore_index=True)
    if rows.event_id.duplicated().any(): raise ValueError('Duplicate event IDs')
    rows['_vector']=[hashlib.sha256(np.asarray(values,dtype='<f8').tobytes()).hexdigest()
                     for values in rows[FEATURES].itertuples(index=False,name=None)]
    print('Building connected session/feature groups',len(rows),'windows',flush=True)
    rows['_group']=components(rows)
    # The split algorithm sees family labels only to stratify whole components.
    # Tuning and model fitting still never see test rows or test scores.
    splitter=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42)
    fold=np.empty(len(rows),dtype=np.int8)
    for index,(_,heldout) in enumerate(splitter.split(rows,rows.family,rows._group)): fold[heldout]=index
    data={name:rows.loc[mask].copy() for name,mask in [('train',fold<3),('validation',fold==3),('test',fold==4)]}
    manifests={}; seen_sessions=set(); seen_vectors=set(); seen_groups=set()
    for name,frame in data.items():
        sessions,vectors,groups=set(frame.session_id),set(frame._vector),set(frame._group)
        if sessions&seen_sessions or vectors&seen_vectors or groups&seen_groups: raise ValueError('Split contamination')
        if frame.label.nunique()!=2: raise ValueError('Each partition must contain both classes')
        seen_sessions.update(sessions);seen_vectors.update(vectors);seen_groups.update(groups)
        manifests[name]=dict(rows=len(frame),sessions=len(sessions),components=len(groups),
            families={str(k):int(v) for k,v in frame.family.value_counts().items()})
    model=RandomForestClassifier(n_estimators=200,max_depth=18,min_samples_leaf=3,
        class_weight='balanced_subsample',random_state=42,n_jobs=4)
    print('Training',manifests,flush=True)
    model.fit(data['train'][FEATURES].to_numpy(),data['train'].label)
    validation=data['validation']; validation_scores=model.predict_proba(validation[FEATURES].to_numpy())[:,1]
    threshold=threshold_for(validation.label,validation_scores,.001)
    test=data['test']; scores=model.predict_proba(test[FEATURES].to_numpy())[:,1]
    result=metrics(test.label,scores,threshold,test.family)
    output.mkdir(parents=True)
    joblib.dump(model,output/'model.joblib')
    manifest=dict(version=output.name,schema_version=SCHEMA,features=FEATURES,threshold=threshold,
        deployment_approved=False,purpose='candidate_pending_independent_live_pilot',
        model_sha256=sha(output/'model.joblib'),model_type='random_forest')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    test[['event_id','session_id','_group','label','family']].assign(score=scores).to_csv(output/'test-predictions.csv',index=False)
    rows[['event_id','session_id','_group','_vector']].assign(split=np.where(fold<3,'train',np.where(fold==3,'validation','test'))).to_csv(output/'split-manifest.csv',index=False)
    report=dict(manifest=manifest,inputs=manifests,sources=sources,
        split_policy='Three training folds, one validation fold, one untouched test fold; connected components of bidirectional capture/endpoint tuples, session segments and identical numeric feature vectors',
        evaluation_scope='in_dataset_grouped; captures shared across partitions',
        validation=metrics(validation.label,validation_scores,threshold,validation.family),test=result,
        release_gates={'independent_capture_test':False,'shadow_pilot':False,'soak_72_hours':False},
        limitations=['Five captures from one dated laboratory environment; no modern production generalization claim.',
            'Identical features can have conflicting labels; every connected session is kept in one partition.',
            'All-family model uses Friday labels for training; it cannot reuse the strict Friday holdout as its independent test.',
            'Rare family support and minute-level label uncertainty remain visible in counts.',
            'Threshold selected only on validation at a 0.1% benign false-positive budget; test FPR can differ.'])
    (output/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/prepared/canonical-v3'))
    parser.add_argument('--output',type=Path,default=Path('models/canonical-all-families-v2'))
    args=parser.parse_args();train(args.input,args.output)
