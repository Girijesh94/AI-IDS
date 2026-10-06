import json
from pathlib import Path
import tempfile
import unittest
from scapy.all import IP, IPv6, TCP, UDP, ICMP, Ether, Dot1Q, Raw, wrpcap
from backend.features import FlowExtractor, read_pcap
from backend.schemas import validate_flow
from backend.config import Settings
from backend.app import create_app
from backend.detection import Detector
from backend.storage import Store
from training.benchmark import threshold_for
import numpy as np


def packet(t=1000, reverse=False, ipv6=False, port=80):
    a, b = ('2001:db8::1', '2001:db8::2') if ipv6 else ('192.0.2.1', '192.0.2.2')
    layer = IPv6 if ipv6 else IP
    p = Ether(src='02:00:00:00:00:01',dst='02:00:00:00:00:02')/layer(src=b if reverse else a, dst=a if reverse else b)/TCP(
        sport=port if reverse else 12345, dport=12345 if reverse else port, flags='SA' if reverse else 'S')
    p.time = t
    return p


def flow(port=80, t=1000):
    f = FlowExtractor()
    f.add(packet(t=t, port=port))
    return f.flush(final=True)[0]


class ExtractionTests(unittest.TestCase):
    def test_bidirectional_and_ipv6(self):
        for v6 in [False, True]:
            f=FlowExtractor(); f.add(packet(ipv6=v6)); f.add(packet(t=1000.5,reverse=True,ipv6=v6))
            rows=f.flush(final=True)
            self.assertEqual(len(rows),1)
            r=rows[0]
            self.assertEqual((r['src2dst_pkts'],r['dst2src_pkts']),(1,1))
            self.assertEqual(r['byte_count'],80 if not v6 else 120)
            self.assertEqual(r['duration'],.5)
            self.assertEqual(r['iat_mean'],.5)

    def test_disjoint_windows_and_no_idle_repeats(self):
        f=FlowExtractor(); f.add(packet())
        first=f.add(packet(t=1005.01))
        last=f.flush(final=True)
        self.assertEqual([r['pkt_count'] for r in first+last],[1,1])
        self.assertNotEqual(first[0]['event_id'],last[0]['event_id'])
        f=FlowExtractor(); f.add(packet())
        self.assertEqual(len(f.flush(1005)),1)
        self.assertEqual(f.flush(1006),[])

    def test_capacity_and_order(self):
        f=FlowExtractor(max_flows=1); f.add(packet()); f.add(packet(t=1001,port=81))
        f.add(packet(t=999))
        self.assertEqual(f.dropped,1); self.assertEqual(f.out_of_order,1)

    def test_repeated_reset_timestamp_has_unique_reproducible_ids(self):
        rows=[]
        for _ in range(2):
            extractor=FlowExtractor('fixture')
            p=packet(); p[TCP].flags='R'
            emitted=extractor.add(p)+extractor.add(p)
            self.assertNotEqual(emitted[0]['event_id'],emitted[1]['event_id'])
            rows.append(emitted)
        self.assertEqual(rows[0],rows[1])

    def test_parser_parity(self):
        packets=[packet(),packet(t=1001,reverse=True),packet(t=1006,port=81)]
        f=FlowExtractor('fixture'); expected=[]
        for p in packets: expected.extend(f.add(p))
        expected.extend(f.flush(final=True))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'fixture.pcap'; wrpcap(str(path),packets)
            self.assertEqual(list(read_pcap(path,'fixture')),expected)

    def test_fast_decoder_matches_reference_for_formats_and_timing(self):
        from scapy.utils import PcapWriter, PcapNgWriter
        packets = [packet(t=1000.123456), packet(t=1000.223456, reverse=True),
                   packet(t=1005.333333, ipv6=True),
                   Ether()/Dot1Q(vlan=7)/IP(src='192.0.2.3',dst='192.0.2.4')/UDP(sport=3,dport=4)/Raw(b'payload'),
                   Ether()/IP(src='192.0.2.5',dst='192.0.2.6')/ICMP(),
                   Ether()/IP(src='192.0.2.5',dst='192.0.2.6',flags='MF')/UDP(),
                   packet(t=1020.123456,port=90)]
        for i in [3,4,5]: packets[i].time=1006+i*.1
        with tempfile.TemporaryDirectory() as tmp:
            for name, writer_type, options in [('micro',PcapWriter,{}),('nano',PcapWriter,{'nano':True}),('ng',PcapNgWriter,{})]:
                path=Path(tmp)/name
                with writer_type(str(path),**options) as writer:
                    for p in packets: writer.write(p)
                fast_stats, reference_stats = {}, {}
                self.assertEqual(list(read_pcap(path,'fixture',fast_stats)),
                                 list(read_pcap(path,'fixture',reference_stats,fast=False)))
                self.assertEqual(fast_stats,reference_stats)

    def test_schema_rejects_invalid_counts_nan_and_missing(self):
        for change in [{'pkt_count':99},{'duration':float('nan')},{'mean_pkt_size':1},{'src_ip':'<script>'}]:
            with self.assertRaises(ValueError): validate_flow(dict(flow(),**change))
        raw=flow(); del raw['src2dst_bytes']
        with self.assertRaises(ValueError): validate_flow(raw)

    def test_labels_and_sender_scores_cannot_change_prediction(self):
        ordinary=flow()
        for label in [0,1,True,False,'attack']:
            injected=dict(ordinary,ground_truth=label,label=label,is_anomaly=True,score=1,severity='critical')
            self.assertEqual(validate_flow(injected),ordinary)
            self.assertEqual(Detector().score(ordinary),Detector().score(validate_flow(injected)))

    def test_scan_rule_and_benign_single_connection(self):
        d=Detector()
        for port in range(20): result=d.score(flow(port=port,t=1000+port))
        self.assertTrue(result['is_anomaly'])
        self.assertFalse(Detector().score(flow())['is_anomaly'])

    def test_threshold_budget(self):
        y=np.array([0,0,1,1]); scores=np.array([.1,.8,.7,.9])
        t=threshold_for(y,scores,0)
        self.assertEqual(t,.9)


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'soc.db'
        self.app,self.socket=create_app(Settings(database=self.path,token='test-token'))
        self.client=self.app.test_client()
        self.headers={'Authorization':'Bearer test-token'}

    def tearDown(self):
        self.app.extensions['ids_runtime'].close()
        self.temp.cleanup()

    def test_import_does_not_start_collectors(self):
        self.assertIsNone(self.app.extensions['ids_runtime'].worker)
        r=self.client.get('/api/health')
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json['model_ready'])
        self.assertEqual(r.json['network_runtime']['capture'],'disabled')

    def test_routes(self):
        for route in ['/', '/operations','/network-flows','/attack-tracker','/cmd-history','/system-logs',
            '/api/alerts','/api/network-flows','/api/stats','/api/benchmarks','/api/incidents',
            '/api/model-metrics','/api/system-logs','/api/logs-stats','/api/cmd-detections']:
            with self.subTest(route=route):
                response=self.client.get(route)
                self.assertEqual(response.status_code,200)
                response.close()

    def test_auth_origin_and_rebinding(self):
        self.assertEqual(self.client.post('/api/ingest',json=flow()).status_code,401)
        self.assertEqual(self.client.post('/api/ingest',json=flow(),headers=dict(self.headers,Origin='https://evil.example')).status_code,403)
        self.assertEqual(self.client.get('/api/health',headers={'Host':'evil.example'}).status_code,403)

    def test_committed_ack_and_idempotent_restart(self):
        raw=flow()
        r=self.client.post('/api/ingest',json=raw,headers=self.headers)
        self.assertEqual(r.json['status'],'stored')
        self.assertEqual(self.client.post('/api/ingest',json=raw,headers=self.headers).json['status'],'duplicate')
        a,s=create_app(Settings(database=self.path,token='test-token'))
        self.assertEqual(a.test_client().post('/api/ingest',json=raw,headers=self.headers).json['status'],'duplicate')
        self.assertEqual(self.client.get('/api/network-flows').json['count'],1)

    def test_malformed_api_input(self):
        for raw in [{},[],dict(flow(),timestamp=float('inf'))]:
            self.assertEqual(self.client.post('/api/ingest',json=raw,headers=self.headers).status_code,400)

    def test_incident_review_separate_from_prediction(self):
        for port in range(21):
            self.client.post('/api/ingest',json=flow(port=port,t=1000+port),headers=self.headers)
        incident=self.client.get('/api/incidents').json['incidents'][0]
        self.assertEqual(incident['count'],2)
        r=self.client.patch('/api/incidents/'+str(incident['id']),json={'state':'investigating'},headers=self.headers)
        self.assertEqual(r.status_code,200)
        event_id=incident['last_event_id']
        r=self.client.post('/api/labels',json=dict(event_id=event_id,label=0,analyst='tester',note='Reviewed fixture'),headers=self.headers)
        self.assertEqual(r.status_code,200)
        self.assertTrue(self.client.get('/api/alerts').json['alerts'][0]['is_anomaly'])

    def test_command_detection_does_not_execute(self):
        r=self.client.post('/api/test-cmd',json={'command':'powershell -enc JABhID0gMjAwMzs='},headers=self.headers)
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['is_anomaly'])
        self.assertIsNone(r.json['confidence'])
        self.assertEqual(r.json['mode'],'replay')

    def test_backup_restore(self):
        self.client.post('/api/ingest',json=flow(),headers=self.headers)
        backup=Path(self.temp.name)/'backup.db'
        self.app.extensions['ids_store'].backup(backup)
        self.assertEqual(len(Store(backup).events()),1)

    def test_csv_model_is_refused(self):
        path=Path(self.temp.name)/'wrong-model'; path.mkdir()
        (path/'manifest.json').write_text(json.dumps(dict(schema_version='cicids2017-csv-v1',deployment_approved=False)))
        detector=Detector(path)
        self.assertIsNone(detector.model)
        self.assertIn('not approved',detector.error)


if __name__ == '__main__': unittest.main()
