"""Transactional telemetry, incidents and independently reviewed labels."""
from contextlib import contextmanager
import hashlib
import json
import sqlite3
import time
from pathlib import Path


class Store:
    def __init__(self, path, retention_days=30):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        with self.connection() as c:
            c.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
                INSERT OR IGNORE INTO schema_version VALUES(1);
                CREATE TABLE IF NOT EXISTS events(
                    event_id TEXT PRIMARY KEY, kind TEXT NOT NULL, mode TEXT NOT NULL,
                    timestamp REAL NOT NULL, received REAL NOT NULL, attack INTEGER NOT NULL,
                    severity TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS events_time ON events(received DESC);
                CREATE INDEX IF NOT EXISTS events_kind ON events(kind, received DESC);
                CREATE TABLE IF NOT EXISTS incidents(
                    id INTEGER PRIMARY KEY, fingerprint TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'new',
                    first_seen REAL, last_seen REAL, count INTEGER NOT NULL DEFAULT 1,
                    severity TEXT, reason TEXT, last_event_id TEXT, mode TEXT);
                CREATE INDEX IF NOT EXISTS incident_key ON incidents(fingerprint,last_seen);
                CREATE TABLE IF NOT EXISTS labels(
                    event_id TEXT PRIMARY KEY REFERENCES events(event_id), label INTEGER NOT NULL,
                    analyst TEXT NOT NULL, note TEXT NOT NULL, reviewed_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS audit(
                    id INTEGER PRIMARY KEY, timestamp REAL, action TEXT, actor TEXT, detail TEXT);
                CREATE TABLE IF NOT EXISTS collector_state(key TEXT PRIMARY KEY, value TEXT);
                CREATE TABLE IF NOT EXISTS logs(
                    id INTEGER PRIMARY KEY, timestamp REAL, level TEXT, component TEXT, message TEXT);
            ''')

    @contextmanager
    def connection(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA busy_timeout=10000')
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def exists(self, event_id):
        with self.connection() as c:
            return c.execute('SELECT 1 FROM events WHERE event_id=?', (event_id,)).fetchone() is not None

    def save(self, event, kind, mode):
        now = time.time()
        with self.connection() as c:
            cursor = c.execute('INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?,?,?)',
                (event['event_id'], kind, mode, event['timestamp'], now,
                 int(event['is_anomaly']), event['severity'], json.dumps(event, allow_nan=False)))
            if cursor.rowcount == 0:
                return False
            if event['is_anomaly']:
                # Keep sensors, destinations, modes and detection reasons in separate incident groups.
                fingerprint = hashlib.sha256(json.dumps([kind, mode, event.get('sensor_id'),
                    event.get('src_ip'), event.get('dst_ip'), event.get('reason')], sort_keys=True).encode()).hexdigest()
                old = c.execute("SELECT id FROM incidents WHERE fingerprint=? AND last_seen>=? AND state IN ('new','investigating') ORDER BY id DESC LIMIT 1",
                                (fingerprint, now - 300)).fetchone()
                if old:
                    c.execute('UPDATE incidents SET count=count+1,last_seen=?,last_event_id=? WHERE id=?',
                              (now, event['event_id'], old['id']))
                else:
                    c.execute('INSERT INTO incidents(fingerprint,first_seen,last_seen,severity,reason,last_event_id,mode) VALUES(?,?,?,?,?,?,?)',
                              (fingerprint, now, now, event['severity'], event['reason'], event['event_id'], mode))
        return True

    def events(self, kind=None, alerts=False, limit=200):
        clauses, params = [], []
        if kind:
            clauses.append('kind=?'); params.append(kind)
        if alerts:
            clauses.append('attack=1')
        sql = 'SELECT payload,mode FROM events' + (' WHERE ' + ' AND '.join(clauses) if clauses else '')
        with self.connection() as c:
            rows = c.execute(sql + ' ORDER BY received DESC LIMIT ?', params + [limit]).fetchall()
        return [dict(json.loads(row['payload']), mode=row['mode']) for row in rows]

    def log(self, level, component, message):
        with self.connection() as c:
            c.execute('INSERT INTO logs(timestamp,level,component,message) VALUES(?,?,?,?)',
                      (time.time(), level, component, str(message)[:4000]))

    def state(self, key, value=None):
        with self.connection() as c:
            if value is not None:
                c.execute('INSERT INTO collector_state VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, value))
            row = c.execute('SELECT value FROM collector_state WHERE key=?', (key,)).fetchone()
            return row['value'] if row else None

    def cleanup(self):
        cutoff = time.time() - self.retention_days * 86400
        with self.connection() as c:
            # Reviewed events and incident evidence survive automatic retention.
            c.execute('DELETE FROM events WHERE received<? AND event_id NOT IN (SELECT event_id FROM labels) AND event_id NOT IN (SELECT last_event_id FROM incidents)', (cutoff,))
            c.execute('DELETE FROM logs WHERE timestamp<?', (cutoff,))

    def backup(self, destination):
        destination = Path(destination)
        if destination.resolve() == self.path.resolve() or destination.exists():
            raise ValueError('Backup destination must be a new file')
        destination.parent.mkdir(parents=True, exist_ok=True)
        target = sqlite3.connect(destination)
        try:
            with self.connection() as source:
                source.backup(target)
        finally:
            target.close()
