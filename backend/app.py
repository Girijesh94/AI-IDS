"""Local IDS/SOC API. Importing this module starts no collectors or servers."""
import hmac
import json
import sqlite3
import time
import uuid
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO
from .config import ROOT, Settings
from .storage import Store
from .runtime import Runtime
from .endpoint import EndpointCollector


def create_app(settings=None):
    settings = settings or Settings.from_env()
    settings.validate()
    app = Flask(__name__, static_folder=str(ROOT / 'frontend'), static_url_path='/static')
    app.config.update(MAX_CONTENT_LENGTH=1024 * 1024, JSON_SORT_KEYS=False)
    socket = SocketIO(app, async_mode='threading', cors_allowed_origins=None)
    store = Store(settings.database, settings.retention_days)
    runtime = Runtime(settings, store, socket.emit)
    endpoint = EndpointCollector(runtime)
    app.extensions.update(ids_runtime=runtime, ids_store=store, ids_endpoint=endpoint)

    @app.before_request
    def protect():
        if request.host.split(':')[0] not in {'localhost', '127.0.0.1', '[', '::1'}:
            return jsonify(error='Local host required'), 403
        if request.method in {'POST', 'PATCH', 'DELETE', 'PUT'}:
            if not settings.token:
                return jsonify(error='Set IDS_TOKEN to enable write operations'), 503
            supplied = request.headers.get('Authorization', '')
            if not hmac.compare_digest(supplied, 'Bearer ' + settings.token):
                return jsonify(error='Authentication required'), 401
            origin = request.headers.get('Origin')
            if origin and origin != request.host_url.rstrip('/'):
                return jsonify(error='Cross-origin write rejected'), 403

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(ValueError)
    def invalid(exc):
        return jsonify(error=str(exc)), 400

    @app.errorhandler(sqlite3.Error)
    def storage_error(exc):
        app.logger.error('Storage error: %s', exc)
        return jsonify(error='Database operation failed; check server logs'), 503

    def limit(default=200):
        return max(1, min(1000, int(request.args.get('limit', default))))

    def body():
        value = request.get_json()
        if not isinstance(value, dict):
            raise ValueError('JSON object required')
        return value

    @app.get('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.get('/<page>')
    def pages(page):
        name = {'history': 'cmd_history.html', 'cmd-history': 'cmd_history.html',
                'system-logs': 'system_logs.html', 'attack-tracker': 'operations.html',
                'network-flows': 'network_flows.html', 'operations': 'operations.html'}.get(page)
        if name is None and page in {'index.html', 'cmd_history.html', 'system_logs.html', 'network_flows.html', 'attack_tracker.html'}:
            name = 'operations.html' if page == 'attack_tracker.html' else page
        if not name:
            return jsonify(error='Not found'), 404
        return send_from_directory(app.static_folder, name)

    @app.get('/api/health')
    def health():
        with store.connection() as c:
            c.execute('SELECT 1').fetchone()
        degraded = bool(runtime.detector.error or runtime.status['processing_errors'] or
                        runtime.status['capture'] == 'failed' or
                        (settings.mode == 'live' and runtime.status['capture'] != 'running') or
                        (settings.mode == 'live' and runtime.status['endpoint'] in {'unavailable','limited_wmi'}))
        return jsonify(status='degraded' if degraded else 'ready', mode=settings.mode,
            ml_mode='model+rules' if runtime.detector.model is not None else 'rules_only',
            database='ready', network_runtime=dict(runtime.status, iface=settings.interface,
                udp_flows_received=runtime.status['flows_received']),
            model_ready=runtime.detector.model is not None, model_error=runtime.detector.error,
            model_version=runtime.detector.manifest.get('version'),
            system_monitor_active=runtime.status['endpoint'] in {'running','limited_wmi'},
            ai_trainer_available=False, detector={'method': 'regex', 'ai_model': False},
            write_enabled=bool(settings.token), timestamp=time.time())

    @app.get('/api/network-status')
    def network_status():
        capture = runtime.extractor
        return jsonify(**runtime.status, queue_depth=runtime.queue.qsize(),
                       packet_count=capture.packets if capture else 0,
                       capacity_drops=capture.dropped if capture else 0,
                       unsupported_packets=capture.unsupported if capture else 0,
                       out_of_order_packets=capture.out_of_order if capture else 0,
                       active_flows=len(capture.flows) if capture else 0)

    @app.post('/api/ingest')
    def ingest():
        data = body()
        result = runtime.process(data, settings.mode)
        return jsonify(status='stored' if result else 'duplicate', event_id=data.get('event_id')), 200

    @app.get('/api/network-flows')
    def network_flows():
        rows = store.events('network', limit=limit())
        return jsonify(flows=rows, count=len(rows))

    @app.get('/api/alerts')
    def alerts():
        rows = store.events(alerts=True, limit=limit())
        return jsonify(alerts=rows, count=len(rows))

    @app.get('/api/cmd-detections')
    def commands():
        rows = store.events('command', limit=limit())
        if request.args.get('severity'):
            rows = [r for r in rows if r['severity'] == request.args['severity']]
        return jsonify(detections=rows, count=len(rows))

    @app.post('/api/test-cmd')
    def test_command():
        data = body()
        return jsonify(endpoint.analyze(data.get('command'), 'test:' + str(uuid.uuid4()), mode='replay'))

    @app.get('/api/stats')
    def stats():
        with store.connection() as c:
            row = dict(c.execute("SELECT COUNT(*) total_flows, COALESCE(SUM(attack),0) total_alerts, COALESCE(SUM(attack=1 AND severity='critical'),0) critical_count, COALESCE(SUM(attack=1 AND severity='high'),0) high_count, COALESCE(SUM(kind='command'),0) cmd_detections FROM events").fetchone())
            row['incidents'] = c.execute('SELECT COUNT(*) FROM incidents').fetchone()[0]
        return jsonify(row)

    @app.get('/api/model-metrics')
    def model_metrics():
        models = {}
        for name in ['isolation_forest', 'random_forest', 'gnn']:
            models[name] = dict(status='ready' if name == 'random_forest' and runtime.detector.model is not None else 'not_ready',
                                tpr=None, fpr=None, confidence=None, consistency=None, unique_rate=None, samples=0)
        return jsonify(models=models, samples_total=0, samples_attacks=0, samples_benign=0,
                       window=None, scope='live_unlabeled', note='Use benchmark reports for held-out evaluation')

    @app.get('/api/model-comparisons')
    def comparisons():
        rows = store.events('network', limit=limit())
        return jsonify(comparisons=rows, count=len(rows))

    @app.get('/api/benchmarks')
    def benchmarks():
        reports = []
        for path in sorted((ROOT / 'artifacts' / 'benchmarks').glob('*/report.json')):
            try:
                reports.append(json.loads(path.read_text(encoding='utf-8')))
            except (ValueError, OSError):
                continue
        return jsonify(reports=reports, live_compatible=False)

    @app.get('/api/data-progress')
    def data_progress():
        output = {'downloads': [], 'pipeline': {'stage': 'not_started'}}
        manifest = ROOT / 'data/raw/cicids2017/download-manifest.json'
        pipeline = ROOT / 'artifacts/pipeline-status.json'
        try:
            if manifest.exists():
                data = json.loads(manifest.read_text())
                for entry in data['files']:
                    state = data['status'].get(entry['path'], {'state': 'queued', 'bytes': 0})
                    output['downloads'].append(dict(path=entry['path'], size=entry['size'], **state))
            if pipeline.exists():
                output['pipeline'] = json.loads(pipeline.read_text())
        except (OSError, ValueError):
            output['pipeline'] = {'stage': 'status_temporarily_unavailable'}
        return jsonify(output)

    @app.get('/api/incidents')
    def incidents():
        with store.connection() as c:
            rows = [dict(x) for x in c.execute('SELECT * FROM incidents ORDER BY last_seen DESC LIMIT ?', (limit(),))]
        return jsonify(incidents=rows)

    @app.patch('/api/incidents/<int:incident_id>')
    def update_incident(incident_id):
        data = body()
        state = data.get('state')
        if state not in {'new', 'investigating', 'resolved', 'false_positive'}:
            raise ValueError('Invalid incident state')
        actor = str(data.get('analyst', 'local-operator'))[:100]
        with store.connection() as c:
            result = c.execute('UPDATE incidents SET state=? WHERE id=?', (state, incident_id))
            if not result.rowcount:
                return jsonify(error='Incident not found'), 404
            c.execute('INSERT INTO audit(timestamp,action,actor,detail) VALUES(?,?,?,?)',
                      (time.time(), 'incident_state', actor, json.dumps({'id': incident_id, 'state': state})))
        return jsonify(status='updated')

    @app.post('/api/labels')
    def label():
        data = body()
        if type(data.get('label')) is not int or data['label'] not in [0, 1]:
            raise ValueError('Label must be integer 0 or 1')
        actor, note = str(data.get('analyst', '')).strip(), str(data.get('note', '')).strip()
        if not actor or not note or len(actor) > 100 or len(note) > 4000:
            raise ValueError('Analyst and review note required')
        with store.connection() as c:
            if not c.execute('SELECT 1 FROM events WHERE event_id=?', (data.get('event_id'),)).fetchone():
                return jsonify(error='Event not found'), 404
            c.execute('INSERT INTO labels VALUES(?,?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET label=excluded.label,analyst=excluded.analyst,note=excluded.note,reviewed_at=excluded.reviewed_at',
                      (data['event_id'], data['label'], actor, note, time.time()))
            c.execute('INSERT INTO audit(timestamp,action,actor,detail) VALUES(?,?,?,?)',
                      (time.time(), 'label', actor, json.dumps(data)))
        return jsonify(status='reviewed')

    @app.get('/api/system-logs')
    def logs():
        with store.connection() as c:
            rows = [dict(x) for x in c.execute('SELECT * FROM logs ORDER BY id DESC LIMIT ?', (limit(),))]
        return jsonify(logs=rows, count=len(rows))

    @app.get('/api/logs-stats')
    def log_stats():
        with store.connection() as c:
            levels = dict(c.execute('SELECT level,COUNT(*) FROM logs GROUP BY level').fetchall())
        return jsonify(total=sum(levels.values()), by_level=levels)

    return app, socket
