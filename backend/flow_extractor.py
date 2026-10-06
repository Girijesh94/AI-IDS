"""Capture belongs to the application; standalone UDP capture has been retired."""
if __name__ == '__main__':
    raise SystemExit('Start capture with scripts/start.ps1 -Mode live. Offline extraction: python -m training.pcap --help')
