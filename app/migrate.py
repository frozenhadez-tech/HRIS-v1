"""Migrate HRPayroll_L98 from SQL Server → PostgreSQL (Neon or local).

Reads schema + data from the local SQL Server instance and recreates everything
in the Postgres target given by DATABASE_URL (or --target).

Usage:
  python migrate.py                      # migrate ALL tables (schema + data)
  python migrate.py --schema-only        # DDL only, no data
  python migrate.py --tables personnel payroll paytranh   # subset
  python migrate.py --limit 200          # cap rows/table (fast smoke test)
  python migrate.py --target "postgresql://..."           # override DATABASE_URL

Source (SQL Server) is fixed to localhost\\SQLEXPRESS / HRPayroll_L98 (Windows auth).
"""
from __future__ import annotations

import argparse
import os
import sys
import pyodbc
import psycopg

SRC = ("DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;"
       "DATABASE=HRPayroll_L98;Trusted_Connection=yes;")

# SQL Server type -> Postgres type
TYPEMAP = {
    "int": "integer", "bigint": "bigint", "smallint": "smallint", "tinyint": "smallint",
    "bit": "boolean", "decimal": "numeric", "numeric": "numeric", "money": "numeric(19,4)",
    "smallmoney": "numeric(10,4)", "float": "double precision", "real": "real",
    "datetime": "timestamp", "datetime2": "timestamp", "smalldatetime": "timestamp",
    "date": "date", "time": "time", "datetimeoffset": "timestamptz",
    "char": "varchar", "varchar": "varchar", "nchar": "varchar", "nvarchar": "varchar",
    "text": "text", "ntext": "text",
    "binary": "bytea", "varbinary": "bytea", "image": "bytea", "timestamp": "bytea",
    "uniqueidentifier": "text", "xml": "text",
}


def src_conn():
    return pyodbc.connect(SRC, autocommit=True)


def columns(cur, table):
    cur.execute("""
        SELECT c.name, ty.name AS typ, c.max_length, c.precision, c.scale, c.is_nullable
        FROM sys.columns c JOIN sys.types ty ON ty.user_type_id=c.user_type_id
        JOIN sys.tables t ON t.object_id=c.object_id
        WHERE t.name=? ORDER BY c.column_id""", table)
    cols = []
    for name, typ, maxlen, prec, scale, nullable in cur.fetchall():
        pg = TYPEMAP.get(typ, "text")
        if pg == "varchar":
            if maxlen == -1:
                pg = "text"                       # varchar(max)
            elif typ in ("nchar", "nvarchar"):
                pg = f"varchar({maxlen // 2})"     # unicode = 2 bytes/char
            else:
                pg = f"varchar({maxlen})"
        elif pg == "numeric" and prec:
            pg = f"numeric({prec},{scale})"
        cols.append({"name": name, "pg": pg, "nullable": bool(nullable)})
    return cols


def user_tables(cur):
    cur.execute("SELECT name FROM sys.tables WHERE is_ms_shipped=0 ORDER BY name")
    return [r[0] for r in cur.fetchall()]


def pk_columns(cur, table):
    cur.execute("""
        SELECT c.name FROM sys.indexes i
        JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id
        JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
        JOIN sys.tables t ON t.object_id=i.object_id
        WHERE t.name=? AND i.is_primary_key=1 ORDER BY ic.key_ordinal""", table)
    return [r[0] for r in cur.fetchall()]


def qi(name):  # quote identifier (lowercase, exact)
    return '"' + name.replace('"', '""') + '"'


def ddl(table, cols, pk):
    lines = [f"  {qi(c['name'])} {c['pg']}" + ("" if c["nullable"] else " NOT NULL") for c in cols]
    if pk:
        lines.append("  PRIMARY KEY (" + ", ".join(qi(c) for c in pk) + ")")
    return f"CREATE TABLE {qi(table)} (\n" + ",\n".join(lines) + "\n);"


def copy_data(scur, tcur, table, cols, limit):
    top = f"TOP {limit} " if limit else ""
    collist = ", ".join(qi(c["name"]) for c in cols)
    scur.execute(f"SELECT {top}{collist} FROM [{table}]")
    ph = ", ".join(qi(c["name"]) for c in cols)
    n = 0
    with tcur.copy(f"COPY {qi(table)} ({ph}) FROM STDIN") as cp:
        while True:
            batch = scur.fetchmany(2000)
            if not batch:
                break
            for row in batch:
                cp.write_row(tuple(row))
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema-only", action="store_true")
    ap.add_argument("--tables", nargs="*")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--target", default=os.environ.get("DATABASE_URL", ""))
    args = ap.parse_args()
    if not args.target:
        sys.exit("No target: set DATABASE_URL or pass --target")

    sc = src_conn(); scur = sc.cursor()
    tables = args.tables or user_tables(scur)
    print(f"Source: SQL Server · {len(tables)} tables · target: {args.target.split('@')[-1][:40]}…")

    with psycopg.connect(args.target, autocommit=False) as tc:
        tcur = tc.cursor()
        # 1) schema
        for t in tables:
            cols = columns(scur, t)
            pk = pk_columns(scur, t)
            tcur.execute(f"DROP TABLE IF EXISTS {qi(t)} CASCADE;")
            tcur.execute(ddl(t, cols, pk))
        tc.commit()
        print(f"Schema created ({len(tables)} tables).")
        if args.schema_only:
            return
        # 2) data
        total = 0
        for t in tables:
            cols = columns(scur, t)
            try:
                n = copy_data(scur, tcur, t, cols, args.limit)
                tc.commit()
                total += n
                print(f"  {t:<22} {n:>8,} rows")
            except Exception as e:
                tc.rollback()
                print(f"  {t:<22} ERROR: {str(e)[:100]}")
        print(f"DONE. {total:,} rows migrated.")


if __name__ == "__main__":
    main()
