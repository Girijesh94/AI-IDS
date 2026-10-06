"""Bounded local qualification, not a substitute for the 72-hour soak."""
import json
from pathlib import Path
import statistics
import tempfile
import time
import argparse
from backend.app import create_app
from backend.config import Settings
from backend.features import FlowExtractor
from scapy.all import IP,TCP


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path)
    parser.add_argument('--shadow',action='store_true')
    parser.add_argument('--output',type=Path,default=Path('artifacts/qualification.json'))
    args=parser.parse_args()
    samples=[]
    with tempfile.TemporaryDirectory() as tmp:
        app,socket=create_app(Settings(database=Path(tmp)/'load.db',token='qualification',model=args.model,model_shadow=args.shadow))
        runtime=app.extensions['ids_runtime']
        if args.model and runtime.detector.model is None: raise ValueError(runtime.detector.error)
        start=time.perf_counter()
        for i in range(1000):
            extractor=FlowExtractor('load-fixture')
            p=IP(src='192.0.2.1',dst='192.0.2.2')/TCP(sport=10000+i,dport=443,flags='A')
            p.time=1700000000+i*.01
            extractor.add(p); f=extractor.flush(final=True)[0]
            tick=time.perf_counter(); runtime.process(f,'replay'); samples.append(time.perf_counter()-tick)
        elapsed=time.perf_counter()-start
        c=app.test_client(); api=[]
        for _ in range(50):
            tick=time.perf_counter(); r=c.get('/api/network-flows?limit=200'); api.append(time.perf_counter()-tick)
            assert r.status_code==200
        result=dict(observations=1000,stored=len(runtime.store.events(limit=2000)),
            end_to_end_seconds=elapsed,windows_per_second=1000/elapsed,
            persistence_p95_ms=sorted(samples)[949]*1000,api_p95_ms=sorted(api)[47]*1000,
            tests='single producer, synthetic valid observations, temporary SQLite database',
            model_version=runtime.detector.manifest.get('version'),model_shadow=runtime.detector.shadow,
            soak_72_hours='not_performed',shadow_pilot='not_performed',packet_capture_driver='not_validated')
        assert result['stored']==1000
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
