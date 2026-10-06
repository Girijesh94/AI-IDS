"""Backward-compatible launcher for the modular IDS application."""
import sys
import os
import secrets
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app import create_app
from waitress import serve


def main():
    # A local token is created once, never embedded in HTML or printed to logs.
    if not os.getenv('IDS_TOKEN'):
        token_file = Path(__file__).resolve().parents[1] / 'data' / 'local-token.txt'
        token_file.parent.mkdir(parents=True, exist_ok=True)
        if not token_file.exists():
            token_file.write_text(secrets.token_urlsafe(32), encoding='utf-8')
        os.environ['IDS_TOKEN'] = token_file.read_text(encoding='utf-8').strip()
    app, socket = create_app()
    runtime = app.extensions['ids_runtime']
    runtime.start()
    if runtime.settings.mode == 'live':
        app.extensions['ids_endpoint'].start()
    runtime.store.log('INFO', 'SERVER', f'Started in {runtime.settings.mode} mode; localhost:5000')
    try:
        # Socket.IO clients use HTTP polling; no unsupported WebSocket upgrade.
        serve(app, host='127.0.0.1', port=5000, threads=8)
    finally:
        runtime.close()


if __name__ == '__main__':
    main()
