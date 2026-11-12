"""SQLite-backed catalog standing in for a metastore (task allows Derby or SQLite catalog).

The catalog is the CURRENT truth only: it reflects what is on disk at collection
time. It must never be labelled historical truth for a past run; that lives in
the run's event log (ReadSchema) or it is unknown.
"""
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any  # boundary: sqlite3 rows are untyped at the edge


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def schema_hash(dtypes: list[tuple[str, str]]) -> str:
    joined = ";".join(f"{n}:{t.strip()}" for n, t in dtypes)
    return hashlib.sha256(joined.encode()).hexdigest()[:16]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(os.environ["CATALOG_DB"])
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tables ("
        " name TEXT PRIMARY KEY, path TEXT, dtypes TEXT, version INTEGER,"
        " schema_hash TEXT, updated_at TEXT)"
    )
    return conn


def register_table(name: str, path: str, dtypes: list[tuple[str, str]]) -> dict[str, Any]:
    """Insert or bump version when schema or path changed; idempotent otherwise."""
    conn = connect()
    try:
        row = conn.execute(
            "SELECT path, dtypes, version FROM tables WHERE name = ?", (name,)
        ).fetchone()
        dtypes_json = json.dumps(dtypes)
        if row is None:
            version = 1
        elif row[0] == path and row[1] == dtypes_json:
            return table_meta(name)  # type: ignore[return-value]
        else:
            version = int(row[2]) + 1
        conn.execute(
            "INSERT OR REPLACE INTO tables VALUES (?,?,?,?,?,?)",
            (name, path, dtypes_json, version, schema_hash(dtypes), _now()),
        )
        conn.commit()
        meta = table_meta(name)
        assert meta is not None
        return meta
    finally:
        conn.close()


def table_meta(name: str) -> dict[str, Any] | None:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT name, path, dtypes, version, schema_hash, updated_at"
            " FROM tables WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            return None
        return {
            "name": row[0],
            "path": row[1],
            "dtypes": json.loads(row[2]),
            "version": row[3],
            "schema_hash": row[4],
            "updated_at": row[5],
        }
    finally:
        conn.close()


def all_tables() -> list[dict[str, Any]]:
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT name FROM tables ORDER BY name"
        ).fetchall()
        metas = []
        for (name,) in rows:
            meta = table_meta(name)
            if meta is not None:
                metas.append(meta)
        return metas
    finally:
        conn.close()


def write_table(spark: Any, name: str, df: Any) -> dict[str, Any]:
    """Write parquet under the warehouse, then register the CURRENT schema."""
    path = os.path.join(os.environ["WAREHOUSE_DIR"], name)
    df.write.mode("overwrite").parquet(path)
    return register_table(name, path, df.dtypes)


def read_table(spark: Any, name: str) -> Any:
    meta = table_meta(name)
    if meta is None:
        raise KeyError(f"table {name} not in catalog")
    return spark.read.parquet(meta["path"])
