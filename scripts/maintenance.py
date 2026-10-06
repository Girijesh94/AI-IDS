"""Database backup and retention CLI."""
import argparse
from pathlib import Path
from backend.storage import Store

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['backup', 'cleanup'])
    p.add_argument('--database', type=Path, default=Path('data/soc.db'))
    p.add_argument('--destination', type=Path)
    args = p.parse_args()
    store = Store(args.database)
    if args.action == 'backup':
        if args.destination is None:
            p.error('--destination is required')
        store.backup(args.destination)
    else:
        store.cleanup()
