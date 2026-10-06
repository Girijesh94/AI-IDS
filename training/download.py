"""Resumable, checksum-verified acquisition of CICIDS2017 PCAPs and labels.

Public mirror used because the publisher's form currently fails. Provenance is
recorded, and mirror checksums verify transport integrity, not publisher authenticity.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import threading
import time
import urllib.request
from urllib.parse import quote

REPO = 'bvsam/cic-ids-2017'


def main(output, workers=3):
    def get_json(url):
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    existing_manifest=output/'download-manifest.json'
    if existing_manifest.exists():
        previous=json.loads(existing_manifest.read_text())
        if previous['repository'] != REPO:
            raise ValueError('Existing download manifest belongs to another repository')
        revision=previous['revision']
    else:
        revision = get_json(f'https://huggingface.co/api/datasets/{REPO}')['sha']
    entries = get_json(f'https://huggingface.co/api/datasets/{REPO}/tree/{revision}?recursive=true&limit=100')
    files = [e for e in entries if e['type'] == 'file' and (e['path'].startswith(('pcap/', 'traffic_labels/')) or e['path'] == 'README.md')]
    output.mkdir(parents=True, exist_ok=True)
    def saved_bytes(entry):
        target = output / entry['path']
        partial = target.with_suffix(target.suffix + '.part')
        return target.stat().st_size if target.exists() else partial.stat().st_size if partial.exists() else 0
    required = sum(max(0, e['size'] - saved_bytes(e)) for e in files)
    if shutil.disk_usage(output).free < required + 10 * 1024**3:
        raise RuntimeError('Insufficient disk space for dataset plus 10 GiB working margin')
    manifest = dict(repository=REPO, revision=revision, publisher='https://www.unb.ca/cic/datasets/ids-2017.html',
                    mirror=True, files=files, status={})
    lock = threading.Lock()
    def status(name, **values):
        with lock:
            manifest['status'][name] = values
            temp = output / 'download-manifest.tmp'
            temp.write_text(json.dumps(manifest, indent=2))
            temp.replace(output / 'download-manifest.json')
    def download(e):
        path = output / e['path']
        if not path.resolve().is_relative_to(output.resolve()):
            raise ValueError('Unsafe path in remote dataset metadata')
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(path.suffix + '.part')
        expected = e.get('lfs', {}).get('oid')
        if path.exists():
            with path.open('rb') as source:
                h = hashlib.file_digest(source, 'sha256').hexdigest()
            if path.stat().st_size == e['size'] and (not expected or h == expected):
                status(e['path'], state='verified', bytes=e['size'], sha256=h)
                return
            raise ValueError(f'Existing file fails integrity check: {path}')
        url = f'https://huggingface.co/datasets/{REPO}/resolve/{revision}/{quote(e["path"])}?download=true'
        for attempt in range(4):
            offset = partial.stat().st_size if partial.exists() else 0
            status(e['path'], state='downloading', bytes=offset, total=e['size'])
            try:
                if offset == e['size']:
                    with partial.open('rb') as source:
                        digest = hashlib.file_digest(source, 'sha256').hexdigest()
                    if expected and digest != expected:
                        raise ValueError('Completed partial fails checksum; preserve for inspection')
                    partial.replace(path)
                    status(e['path'], state='verified', bytes=offset, sha256=digest)
                    return
                req = urllib.request.Request(url, headers={'Range': f'bytes={offset}-'} if offset else {})
                with urllib.request.urlopen(req, timeout=60) as response:
                    if offset and response.status != 206:
                        raise RuntimeError('Server did not honor resume range')
                    if offset and not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
                        raise RuntimeError('Server returned a different resume offset')
                    next_update = time.monotonic()
                    with partial.open('ab' if offset else 'wb') as out:
                        while block := response.read(4 * 1024 * 1024):
                            if offset + len(block) > e['size']:
                                raise RuntimeError('Response exceeds expected dataset file size')
                            out.write(block); offset += len(block)
                            if time.monotonic() >= next_update:
                                status(e['path'], state='downloading', bytes=offset, total=e['size'])
                                print(f'{e["path"]}: {offset/1024**3:.2f}/{e["size"]/1024**3:.2f} GiB', flush=True)
                                next_update = time.monotonic() + 30
                if partial.stat().st_size != e['size']:
                    raise RuntimeError('Downloaded size mismatch')
                with partial.open('rb') as source:
                    digest = hashlib.file_digest(source, 'sha256').hexdigest()
                if expected and digest != expected:
                    raise ValueError('SHA256 mismatch; preserve partial for inspection')
                partial.replace(path)
                status(e['path'], state='verified', bytes=e['size'], sha256=digest)
                print(f'Verified {path.name}', flush=True)
                return
            except Exception as exc:
                status(e['path'], state='retry' if attempt < 3 else 'failed', bytes=offset, error=str(exc))
                if attempt == 3:
                    print(f'FAILED {e["path"]}: {exc}', flush=True)
                    return
                time.sleep(2)
    # Labels first, then captures; independent downloads share bounded concurrency.
    files.sort(key=lambda e: (e['path'].startswith('pcap/'), e['size']))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(download, files))
    failures = [k for k,v in manifest['status'].items() if v['state'] != 'verified']
    if failures:
        raise SystemExit('Incomplete downloads: ' + ', '.join(failures))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=Path('data/raw/cicids2017'))
    p.add_argument('--workers', type=int, default=3)
    a = p.parse_args()
    main(a.output, a.workers)
