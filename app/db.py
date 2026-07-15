"""Database access layer — PostgreSQL (Neon in production, local for dev).

The app targets PostgreSQL. Connection comes from the DATABASE_URL environment
variable (Neon pooled connection string in production). Queries use `?`
placeholders throughout the app; this layer translates them to psycopg's `%s`.
"""
from __future__ import annotations

import os
import re
import psycopg
from psycopg.rows import dict_row

try:  # load .env for local development (no-op in production if absent)
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def _dsn() -> str:
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Put your Neon (or local Postgres) connection "
            "string in app/.env or the environment. See .env.example."
        )
    return DATABASE_URL


def _new_conn():
    # autocommit so read-only requests don't hold a transaction open across queries
    return psycopg.connect(_dsn(), row_factory=dict_row, connect_timeout=15, autocommit=True)


def get_conn():
    """One connection per Flask request (reused across queries); a fresh one for scripts."""
    try:
        from flask import g, has_app_context
        if has_app_context():
            if "db_conn" not in g:
                g.db_conn = _new_conn()
            return g.db_conn
    except Exception:
        pass
    return _new_conn()


def close_conn(_exc=None):
    try:
        from flask import g, has_app_context
        if has_app_context():
            c = g.pop("db_conn", None)
            if c is not None:
                c.close()
    except Exception:
        pass


_TOP = re.compile(r"^(\s*SELECT\s+)(DISTINCT\s+)?TOP\s+(\d+)\s+", re.IGNORECASE)


def _pg(sql: str) -> str:
    # Translate the app's T-SQL idioms to PostgreSQL.
    # 1) leading `SELECT [DISTINCT] TOP N` -> strip and append `LIMIT N`
    m = _TOP.match(sql)
    if m:
        n = m.group(3)
        sql = _TOP.sub(lambda x: x.group(1) + (x.group(2) or ""), sql, count=1)
        sql = sql.rstrip().rstrip(";") + f" LIMIT {n}"
    # 2) `?` params -> psycopg `%s` (no literal `%`/`?` exist in our SQL)
    return sql.replace("?", "%s")


def q(sql: str, *params):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(_pg(sql), params)
        return cur.fetchall()  # list[dict]


def one(sql: str, *params):
    r = q(sql, *params)
    return r[0] if r else None


def execute(sql: str, *params):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(_pg(sql), params)
