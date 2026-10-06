"""Generate an explicit offline fixture and replay it without transmitting attack packets."""
import argparse
from pathlib import Path
import os
from scapy.all import Ether, IP, TCP, wrpcap
from training.pcap import replay


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',default='http://127.0.0.1:5000')
    args=p.parse_args()
    target=Path('data/fixtures/scan-demo.pcap')
    target.parent.mkdir(parents=True,exist_ok=True)
    packets=[]
    for i in range(25):
        item=Ether(src='02:00:00:00:00:01',dst='02:00:00:00:00:02')/IP(src='192.0.2.10',dst='192.0.2.20')/TCP(sport=40000+i,dport=1000+i,flags='S')
        item.time=1700000000+i*.1
        packets.append(item)
    wrpcap(str(target),packets)
    if not os.getenv('IDS_TOKEN'):
        os.environ['IDS_TOKEN']=Path('data/local-token.txt').read_text().strip()
    replay(argparse.Namespace(input=target,url=args.url,model=None,database=Path('data/replay.db')))


if __name__=='__main__': main()
