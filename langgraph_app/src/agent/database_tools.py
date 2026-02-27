"""
database_tools.py
=================
Routes all SQL execution through the DB API server (db_api_server.py) rather
than opening direct psycopg2 connections.  The public interface is unchanged so
graph.py continues to work without modification:

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [d[0] for d in cursor.description]
    cursor.close()

The returned "connection" and "cursor" objects are lightweight proxies that
forward every `.execute()` call to POST /api/database/query on the API server.
"""

import os
import threading
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────

DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST",     "localhost"),
    "port":     int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB",       "edward_local"),
    "user":     os.getenv("POSTGRES_USER",     "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "Test1234"),
    "schema":   os.getenv("POSTGRES_SCHEMA",   "olist_db"),
}

DB_API_URL = os.getenv("DB_API_URL", "http://localhost:8000")

# Thread-local storage keeps a *connection_id* per thread (mirrors the old
# per-thread psycopg2 connection behaviour).
thread_local = threading.local()


# ── Proxy cursor ──────────────────────────────────────────────────────────────

class _ApiCursor:
    """Minimal cursor-like object that delegates execution to the API server."""

    def __init__(self, connection_id: str, schema: str):
        self._connection_id = connection_id
        self._schema = schema
        self.description = None   # list of (name, ...) tuples after execute()
        self._rows: list = []

    # ------------------------------------------------------------------ core
    def execute(self, sql: str, params=None):
        """Send *sql* to POST /api/database/query and cache the results."""
        if params:
            # psycopg2-style %s substitution (for the rare non-LLM calls)
            import psycopg2.extensions as _ext
            sql = sql % tuple(
                _ext.adapt(p).getquoted().decode() if hasattr(_ext.adapt(p), "getquoted")
                else repr(p)
                for p in params
            )

        payload = {
            "sql":           sql,
            "connection_id": self._connection_id,
            "schema":        self._schema,
        }

        print(f" ! [db_api] POST {DB_API_URL}/api/database/query")
        resp = requests.post(
            f"{DB_API_URL}/api/database/query",
            json=payload,
            timeout=180,
        )

        if not resp.ok:
            detail = resp.json().get("detail", resp.text) if resp.content else resp.text
            raise Exception(f"DB API query failed ({resp.status_code}): {detail}")

        data = resp.json()
        columns = data.get("columns", [])

        # Build description compatible with DB-API 2.0 (7-tuple, rest None)
        self.description = [(col, None, None, None, None, None, None) for col in columns]
        self._rows = [tuple(row) for row in data.get("rows", [])]

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchmany(self, size=1):
        return self._rows[:size]

    def close(self):
        self.description = None
        self._rows = []

    # context-manager support
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# ── Proxy connection ──────────────────────────────────────────────────────────

class _ApiConnection:
    """Minimal connection-like object backed by a DB API server connection."""

    def __init__(self, connection_id: str, schema: str):
        self._connection_id = connection_id
        self._schema = schema
        self.autocommit = True   # matches the original get_db_connection() behaviour
        self.closed = False

    def cursor(self):
        return _ApiCursor(self._connection_id, self._schema)

    def close(self):
        try:
            requests.post(
                f"{DB_API_URL}/api/database/disconnect",
                params={"connection_id": self._connection_id},
                timeout=10,
            )
        except Exception:
            pass
        self.closed = True

    def rollback(self):
        pass  # read-only / autocommit – nothing to roll back

    def commit(self):
        pass

    # context-manager support
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# ── Public API ────────────────────────────────────────────────────────────────

def _ensure_api_connection() -> str:
    """Register (or reuse) a DB API server connection and return its id."""

    # Check whether the API server already has an active connection for our DB
    try:
        status = requests.get(f"{DB_API_URL}/api/database/status", timeout=10).json()
        expected_id = f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        for c in status.get("connections", []):
            if c.get("connection_id") == expected_id:
                print(f" ! [db_api] Reusing existing connection: {expected_id}")
                return expected_id
    except Exception:
        pass  # server not reachable yet – will fail below with a clear message

    # Create a new connection via the API
    payload = {
        "host":     DB_CONFIG["host"],
        "port":     DB_CONFIG["port"],
        "database": DB_CONFIG["database"],
        "username": DB_CONFIG["user"],
        "password": DB_CONFIG["password"],
    }
    print(f" ! [db_api] Registering connection to {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    resp = requests.post(
        f"{DB_API_URL}/api/database/connect",
        json=payload,
        timeout=15,
    )

    if not resp.ok:
        detail = resp.json().get("detail", resp.text) if resp.content else resp.text
        raise Exception(f"DB API connect failed ({resp.status_code}): {detail}")

    connection_id = resp.json().get("connection_id")
    print(f" ! [db_api] Connected successfully. connection_id={connection_id}")
    return connection_id


def get_db_connection() -> _ApiConnection:
    """Return a thread-local proxy connection that routes SQL to the API server.

    Drop-in replacement for the old psycopg2-based implementation.
    The returned object exposes .cursor(), .autocommit, .closed, etc.
    """
    # Re-use the same connection_id within this thread
    if not hasattr(thread_local, "api_conn") or thread_local.api_conn is None or thread_local.api_conn.closed:
        connection_id = _ensure_api_connection()
        thread_local.api_conn = _ApiConnection(connection_id, DB_CONFIG["schema"])

    return thread_local.api_conn


def connect_db(
    host: str = None,
    port: int = None,
    database: str = None,
    user: str = None,
    password: str = None,
    schema: str = None,
) -> _ApiConnection:
    """Connect with explicit parameters and return a proxy connection.

    Registers a new connection through the API server every time it is called.
    """
    payload = {
        "host":     host     or DB_CONFIG["host"],
        "port":     port     or DB_CONFIG["port"],
        "database": database or DB_CONFIG["database"],
        "username": user     or DB_CONFIG["user"],
        "password": password or DB_CONFIG["password"],
    }
    resp = requests.post(f"{DB_API_URL}/api/database/connect", json=payload, timeout=15)
    if not resp.ok:
        detail = resp.json().get("detail", resp.text) if resp.content else resp.text
        raise Exception(f"DB API connect failed ({resp.status_code}): {detail}")

    connection_id = resp.json().get("connection_id")
    schema_to_use = schema or DB_CONFIG["schema"]
    print(f" ! [db_api] Connected: {payload['database']}  connection_id={connection_id}")
    return _ApiConnection(connection_id, schema_to_use)
