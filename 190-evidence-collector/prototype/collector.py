"""Collector: manifests + run index + Spark event logs + catalog -> tagged records.

Definitions used by the queries:
- latest ATTEMPTED run of a workflow: the run record with the greatest start
  time over ALL attempts and rounds, regardless of outcome.
- latest SUCCESSFUL run: the same restricted to exit_code == 0.
- A run's plan evidence is used ONLY when the event-log app id equals the
  appinfo app id recorded by the runner; otherwise the join is REJECTED as
  ambiguous and the queries report 'conflicting-app-id'.
- The catalog is a CURRENT snapshot: it is never used as the schema a past run
  read; that comes from the event log ReadSchema or is 'unknown'.
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any  # boundary: parsed JSON/event-log lines

PROTO = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(PROTO, "repo")
RUNS = os.path.join(PROTO, "runs")
EVENTLOG = os.path.join(RUNS, "eventlog")
INDEX = os.path.join(RUNS, "index.jsonl")
CATALOG_DB = os.path.join(PROTO, "catalog", "catalog.db")
RECORDS = os.path.join(PROTO, "records", "records.jsonl")
EVIDENCE_DB = os.path.join(PROTO, "records", "evidence.db")
COLLECTOR_VERSION = "collector 0.1"
MANIFEST_PAGE_SIZE = 2  # small on purpose: exercises pagination on 3 manifests


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git(*args: str) -> str:
    out = subprocess.run(
        ["git", "-C", REPO, *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def record_id(body: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(body).encode()).hexdigest()[:16]


def make_record(
    kind: str,
    subject_id: str,
    version: dict[str, Any],
    source_endpoint: str,
    payload: dict[str, Any],
    completeness: tuple[str, list[str]] = ("complete", []),
    links: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = {
        "kind": kind,
        "subject": {"id": subject_id, "type": kind},
        "version": version,
        "source": {
            "system": "toy-platform",
            "endpoint": source_endpoint,
            "collected_at": now(),
            "collector_version": COLLECTOR_VERSION,
        },
        "payload": payload,
        "completeness": {"status": completeness[0], "reasons": completeness[1]},
        "links": links or {},
    }
    body["record_id"] = record_id(
        {k: v for k, v in body.items() if k != "record_id"}
    )
    return body


# ---------------------------------------------------------------- manifests


def load_manifests() -> tuple[list[dict[str, Any]], int]:
    """Paged listing, as a real API would force; returns manifests and page count."""
    index = json.loads(git("show", "HEAD:manifests/index.json"))
    pages = 0
    found: list[dict[str, Any]] = []
    for i in range(0, len(index), MANIFEST_PAGE_SIZE):
        pages += 1
        for rel in index[i : i + MANIFEST_PAGE_SIZE]:
            m = json.loads(git("show", f"HEAD:{rel}"))
            m["_rel"] = rel
            found.append(m)
    return found, pages


# ---------------------------------------------------------------- event logs

PATH_RE = re.compile(
    r"Location: InMemoryFileIndex(?: \(\d+ paths?\))? \[([^\]]+)\]"
)
READ_SCHEMA_RE = re.compile(r"ReadSchema: (struct<[^\n]*>)")
WRITE_PATH_RE = re.compile(r"InsertIntoHadoopFsRelationCommand (file:[^,]+)")


def parse_eventlog(path: str) -> dict[str, Any] | None:
    app: dict[str, Any] = {
        "file": os.path.basename(path),
        "app_id": None,
        "app_name": None,
        "user": None,
        "start_ts": None,
        "end_ts": None,
        "spark_version": None,
        "jobs": {},
        "num_tasks": 0,
        "sql": [],
        "parse_errors": 0,
    }
    sql_start: dict[int, dict[str, Any]] = {}
    with open(path) as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                app["parse_errors"] += 1
                continue
            ev = e.get("Event", "")
            if ev == "SparkListenerApplicationStart":
                app["app_id"] = e.get("App ID")
                app["app_name"] = e.get("App Name")
                app["user"] = e.get("User")
                app["start_ts"] = e.get("Timestamp")
            elif ev == "SparkListenerApplicationEnd":
                app["end_ts"] = e.get("Timestamp")
            elif ev == "SparkListenerLogStart":
                app["spark_version"] = e.get("Spark Version")
            elif ev == "SparkListenerJobEnd":
                jid = e.get("Job ID")
                res = e.get("Job Result", {}).get("Result")
                start = app["jobs"].get(jid, {}).get("start_ts")
                app["jobs"][jid] = {
                    "job_id": jid,
                    "result": res,
                    "duration_ms": (
                        e.get("Completion Time", 0) - start if start is not None else None
                    ),
                }
            elif ev == "SparkListenerJobStart":
                jid = e.get("Job ID")
                app["jobs"][jid] = {"job_id": jid, "start_ts": e.get("Submission Time")}
            elif ev == "SparkListenerTaskEnd":
                app["num_tasks"] += 1
            elif ev.endswith("SparkListenerSQLExecutionStart"):
                sql_start[e["executionId"]] = {
                    "execution_id": e["executionId"],
                    "description": (e.get("description") or "")[:200],
                    "physical_plan": e.get("physicalPlanDescription", ""),
                    "start_ts": e.get("time"),
                }
            elif ev.endswith("SparkListenerSQLExecutionEnd"):
                s = sql_start.pop(e["executionId"], None)
                if s is not None:
                    s["end_ts"] = e.get("time")
                    s["error"] = e.get("errorMessage")
                    app["sql"].append(s)
    app["sql"] += list(sql_start.values())  # started but never ended
    if app["app_id"] is None:
        return None
    return app


def normalise_plan(plan: str) -> str:
    t = plan.replace(os.path.join(PROTO, "warehouse"), "<WH>")
    t = re.sub(r"#\d+", "#", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def struct_to_fields(struct: str) -> list[tuple[str, str]]:
    inner = struct.strip()
    inner = inner[len("struct<") : -1] if inner.startswith("struct<") else inner
    if not inner:
        return []
    out = []
    # Spark nested structs/maps and decimal precision contain their own commas.
    parts: list[str] = []
    depth = 0
    quoted = False
    start = 0
    for i, char in enumerate(inner):
        if char == "`":
            quoted = not quoted
        elif not quoted:
            if char in "<([":
                depth += 1
            elif char in ">)]":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(inner[start:i])
                start = i + 1
        if depth < 0:
            raise ValueError("unbalanced Spark ReadSchema")
    if depth or quoted:
        raise ValueError("unbalanced Spark ReadSchema")
    parts.append(inner[start:])
    for part in parts:
        name, separator, typ = part.partition(":")
        if not separator or not name.strip() or not typ.strip():
            raise ValueError("invalid Spark ReadSchema field")
        out.append((name.strip(), typ.strip()))
    return out


def fields_hash(fields: list[tuple[str, str]]) -> str:
    joined = ";".join(f"{n}:{t}" for n, t in fields)
    return hashlib.sha256(joined.encode()).hexdigest()[:16]


def plan_reads_writes(plan: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Pair each scan Location with the nearest following ReadSchema (pruned!)."""
    reads: list[tuple[str, str]] = []
    locs = list(PATH_RE.finditer(plan))
    for i, m in enumerate(locs):
        end = locs[i + 1].start() if i + 1 < len(locs) else min(len(plan), m.end() + 3000)
        sm = READ_SCHEMA_RE.search(plan, m.end(), end)
        struct = sm.group(1) if sm else ""
        for p in m.group(1).split(","):
            p = p.strip().removeprefix("file:")
            if p:
                reads.append((p, struct))
    writes = [w.removeprefix("file:") for w in WRITE_PATH_RE.findall(plan)]
    return reads, writes


def compare_read(
    current_dtypes: list[tuple[str, str]], read_fields: list[tuple[str, str]]
) -> str:
    """Column-level comparison: ReadSchema is PRUNED, so only columns the query
    actually touched are proven. Missing/changed column proves non-current."""
    if not read_fields:
        return "no-columns-read"
    cur = {n: t for n, t in current_dtypes}
    for n, t in read_fields:
        if n not in cur:
            return f"not-current (column {n} absent from current schema)"
        if cur[n] != t:
            return f"not-current (type of {n}: {t} vs {cur[n]})"
    if set(cur) == {n for n, _ in read_fields}:
        return "matches-current-columns"
    return "subset-of-current (pruned read)"


# ---------------------------------------------------------------- collect


def table_for_path(path: str, catalog: list[dict[str, Any]]) -> str | None:
    for meta in catalog:
        if path == str(meta["path"]) or path.startswith(str(meta["path"]) + "/"):
            return str(meta["name"])
    return None


def collect() -> None:
    os.makedirs(os.path.dirname(RECORDS), exist_ok=True)
    manifests, pages = load_manifests()
    manifest_by_wf = {m["workflow_id"]: m for m in manifests}
    runs = []
    with open(INDEX) as f:
        for line in f:
            runs.append(json.loads(line))

    apps = []
    for name in sorted(os.listdir(EVENTLOG)):
        p = os.path.join(EVENTLOG, name)
        if os.path.isfile(p):
            a = parse_eventlog(p)
            if a is not None:
                apps.append(a)
    app_by_name = {a["app_name"]: a for a in apps}
    app_by_id = {a["app_id"]: a for a in apps}

    catalog: list[dict[str, Any]] = []
    conn = sqlite3.connect(CATALOG_DB)
    for (name,) in conn.execute("SELECT name FROM tables ORDER BY name"):
        row = conn.execute(
            "SELECT path, dtypes, version, schema_hash, updated_at FROM tables"
            " WHERE name = ?",
            (name,),
        ).fetchone()
        catalog.append(
            {
                "name": name,
                "path": row[0],
                "dtypes": json.loads(row[1]),
                "version": row[2],
                "schema_hash": row[3],
                "updated_at": row[4],
            }
        )
    conn.close()

    records: list[dict[str, Any]] = []
    referenced_apps: set[str] = set()

    # workflow-definition records, one per (workflow, commit) actually run
    def_cache: dict[tuple[str, str], dict[str, Any]] = {}
    manifest_at: dict[tuple[str, str], dict[str, Any]] = {}
    for r in runs:
        key = (r["workflow"], r["code_commit"])
        if key in def_cache:
            continue
        m = json.loads(git("show", f"{r['code_commit']}:manifests/{r['workflow']}.json"))
        manifest_at[key] = m
        d = make_record(
            "workflow-definition",
            r["workflow"],
            {"code_commit": r["code_commit"], "definition_version": m["definition_version"]},
            f"git {r['code_commit']} manifests/{r['workflow']}.json",
            {"manifest": m, "definition_hash": r["definition_hash"]},
            links={"code_commit": r["code_commit"]},
        )
        def_cache[key] = d
        records.append(d)

    # run, plan and metrics records
    for r in runs:
        key = (r["workflow"], r["code_commit"])
        if key not in manifest_at:
            manifest_at[key] = json.loads(
                git("show", f"{r['code_commit']}:manifests/{r['workflow']}.json")
            )
        r["_reads_expected"] = manifest_at[key].get("reads", [])
        appinfo = r.get("appinfo")
        app = None
        reasons: list[str] = []
        status = "complete"
        if appinfo is None:
            status = "partial"
            reasons.append("no appinfo (killed before start?)")
        else:
            app = app_by_name.get(r["run_id"]) or app_by_id.get(appinfo["app_id"])
            if app is None:
                status = "partial"
                reasons.append("no event log found for app id " + appinfo["app_id"])
            elif app["app_id"] != appinfo["app_id"]:
                status = "conflicting"
                reasons.append(
                    f"app id mismatch: index={appinfo['app_id']} log={app['app_id']}"
                )
                app = None  # REJECT the join
        if app is not None and app["end_ts"] is None:
            status = "partial"
            reasons.append("event log has no ApplicationEnd")
        if app is not None:
            referenced_apps.add(app["app_id"])
        run_rec = make_record(
            "run",
            r["run_id"],
            {
                "code_commit": r["code_commit"],
                "definition_version": r["definition_version"],
                "definition_hash": r["definition_hash"],
                "attempt": r["attempt"],
            },
            "runs/index.jsonl + eventlog/" + (app["file"] if app else "?"),
            {
                "workflow": r["workflow"],
                "app_id": (appinfo or {}).get("app_id"),
                "app_name": r["run_id"],
                "start": r["start"],
                "end": r["end"],
                "exit_code": r["exit_code"],
                "spark_version": app["spark_version"] if app else None,
                "reads_expected": r.get("_reads_expected", []),
                "crash_simulated": r["crash_simulated"],
            },
            completeness=("conflicting" if status == "conflicting" else status, reasons),
            links={
                "workflow_definition": {
                    "workflow": r["workflow"],
                    "code_commit": r["code_commit"],
                    "definition_version": r["definition_version"],
                },
                "plans": [],
            },
        )
        records.append(run_rec)
        if app is None:
            continue
        failed_jobs = [j for j in app["jobs"].values() if j.get("result") != "JobSucceeded"]
        records.append(
            make_record(
                "metrics",
                r["run_id"],
                {"app_id": app["app_id"], "attempt": r["attempt"]},
                "eventlog/" + app["file"],
                {
                    "num_sql_executions": len(app["sql"]),
                    "num_jobs": len(app["jobs"]),
                    "failed_jobs": len(failed_jobs),
                    "num_tasks": app["num_tasks"],
                    "duration_ms": (app["end_ts"] or 0) - (app["start_ts"] or 0),
                },
                links={"run": r["run_id"]},
            )
        )
        for s in app["sql"]:
            plan = s["physical_plan"]
            reads, writes = plan_reads_writes(plan)
            read_tables: list[dict[str, Any]] = []
            for p, struct in reads:
                t = table_for_path(p, catalog)
                if t is None:
                    read_tables.append({"path": p, "table": None})
                    continue
                meta = next(m for m in catalog if m["name"] == t)
                fields = struct_to_fields(struct) if struct else []
                read_tables.append(
                    {
                        "path": p,
                        "table": t,
                        "read_columns": fields,
                        "read_columns_hash": fields_hash(fields) if fields else None,
                        "catalog_version_now": meta["version"],
                        "catalog_updated_at": meta["updated_at"],
                        "catalog_match": compare_read(meta["dtypes"], fields),
                    }
                )
            plan_rec = make_record(
                "plan",
                f"{r['run_id']}#exec{s['execution_id']}",
                {
                    "run_id": r["run_id"],
                    "execution_id": s["execution_id"],
                    "code_commit": r["code_commit"],
                    "definition_version": r["definition_version"],
                },
                "eventlog/" + app["file"],
                {
                    "app_id": app["app_id"],
                    "description": s["description"],
                    "plan_hash": hashlib.sha256(
                        normalise_plan(plan).encode()
                    ).hexdigest()[:16],
                    "plan_normalised_excerpt": normalise_plan(plan)[:300],
                    "read_tables": read_tables,
                    "write_paths": writes,
                    "duration_ms": (s.get("end_ts") or 0) - (s["start_ts"] or 0),
                    "error": s.get("error"),
                },
                links={
                    "run": r["run_id"],
                    "code_commit": r["code_commit"],
                    "table_schemas": [t.get("table") for t in read_tables if t.get("table")],
                },
            )
            records.append(plan_rec)
            run_rec["links"]["plans"].append(plan_rec["record_id"])

    # unmapped applications: event-log apps no run references
    for a in apps:
        if a["app_id"] not in referenced_apps:
            records.append(
                make_record(
                    "gap",
                    a["app_id"],
                    {"app_id": a["app_id"]},
                    "eventlog/" + a["file"],
                    {
                        "gap_type": "unmapped_application",
                        "app_name": a["app_name"],
                        "note": "app present in event logs, absent from manifests/run index",
                    },
                    completeness=("partial", ["no workflow mapping"]),
                )
            )

    # catalog snapshot: CURRENT only, never historical truth
    for meta in catalog:
        records.append(
            make_record(
                "table-schema",
                meta["name"],
                {"version": meta["version"], "schema_hash": meta["schema_hash"]},
                "catalog/catalog.db",
                {k: v for k, v in meta.items() if k != "name"},
                completeness=(
                    "current_snapshot_only",
                    [
                        "catalog holds the latest version only; schemas read by past"
                        " runs come from event logs or are unknown"
                    ],
                ),
            )
        )

    # Run plan links are populated after record creation: hash the final stored body.
    for rec in records:
        rec["record_id"] = record_id({k: v for k, v in rec.items() if k != "record_id"})

    with open(RECORDS, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    db = sqlite3.connect(EVIDENCE_DB)
    db.executescript(
        """
        DROP TABLE IF EXISTS records;
        CREATE TABLE records (
            record_id TEXT PRIMARY KEY, kind TEXT, subject TEXT,
            collected_at TEXT, json TEXT);
        DROP VIEW IF EXISTS v_latest_attempted;
        DROP VIEW IF EXISTS v_latest_successful;
        DROP VIEW IF EXISTS v_run_plan_hashes;
        CREATE VIEW v_latest_attempted AS
          SELECT json_extract(json,'$.payload.workflow') AS workflow,
                 subject AS run_id,
                 json_extract(json,'$.payload.start') AS started,
                 json_extract(json,'$.payload.exit_code') AS exit_code,
                 json_extract(json,'$.completeness.status') AS completeness
          FROM records WHERE kind='run'
          GROUP BY json_extract(json,'$.payload.workflow')
          HAVING started = MAX(json_extract(json,'$.payload.start'));
        CREATE VIEW v_latest_successful AS
          SELECT json_extract(json,'$.payload.workflow') AS workflow,
                 subject AS run_id,
                 json_extract(json,'$.payload.start') AS started
          FROM records WHERE kind='run'
            AND json_extract(json,'$.payload.exit_code') = 0
          GROUP BY json_extract(json,'$.payload.workflow')
          HAVING started = MAX(json_extract(json,'$.payload.start'));
        CREATE VIEW v_run_plan_hashes AS
          SELECT json_extract(json,'$.version.run_id') AS run_id,
                 json_extract(json,'$.payload.plan_hash') AS plan_hash,
                 json_extract(json,'$.version.code_commit') AS code_commit
          FROM records WHERE kind='plan';
        """
    )
    for rec in records:
        db.execute(
            "INSERT OR REPLACE INTO records VALUES (?,?,?,?,?)",
            (
                rec["record_id"],
                rec["kind"],
                rec["subject"]["id"],
                rec["source"]["collected_at"],
                json.dumps(rec),
            ),
        )
    db.commit()
    db.close()

    counts: dict[str, int] = {}
    for rec in records:
        counts[rec["kind"]] = counts.get(rec["kind"], 0) + 1
    print(
        f"collector: {len(records)} records ({counts}), manifests={len(manifests)}"
        f" in {pages} pages, apps={len(apps)}, runs={len(runs)}"
    )


# ---------------------------------------------------------------- queries


def load_db() -> sqlite3.Connection:
    return sqlite3.connect(EVIDENCE_DB)


def query_a() -> None:
    out = ["(a) latest run per workflow (attempted vs successful), with plan hash"]
    db = load_db()
    rows = db.execute(
        "SELECT json_extract(json,'$.payload.workflow') AS workflow,"
        " subject AS run_id, json_extract(json,'$.payload.start') AS started,"
        " json_extract(json,'$.payload.exit_code') AS exit_code,"
        " json_extract(json,'$.completeness.status') AS completeness,"
        " (SELECT group_concat(plan_hash) FROM v_run_plan_hashes p"
        "   WHERE p.run_id = r.subject) AS plans"
        " FROM records r WHERE kind='run'"
        " ORDER BY started"
    ).fetchall()
    latest_attempted: dict[str, tuple[Any, ...]] = {}
    latest_success: dict[str, tuple[Any, ...]] = {}
    for row in rows:
        wf = row[0]
        if wf is None:
            continue
        if wf not in latest_attempted or row[2] > latest_attempted[wf][2]:
            latest_attempted[wf] = row
        if row[3] == 0 and (wf not in latest_success or row[2] > latest_success[wf][2]):
            latest_success[wf] = row
    for wf in sorted(latest_attempted):
        la = latest_attempted[wf]
        ls = latest_success.get(wf)
        out.append(
            f"  {wf}: latest attempted {la[1]} exit={la[3]} completeness={la[4]}"
            f" plans=[{la[5]}]"
        )
        if ls is not None and ls[1] != la[1]:
            out.append(
                f"    latest SUCCESSFUL differs: {ls[1]} plans=[{ls[5]}]"
                " (latest attempted failed)"
            )
    db.close()
    write_out("query-a.txt", out)


def query_b(run_id: str) -> None:
    out = [f"(b) provenance join for run {run_id}"]
    db = load_db()
    row = db.execute(
        "SELECT json FROM records WHERE kind='run' AND subject=?", (run_id,)
    ).fetchone()
    if row is None:
        out.append("  run not found")
    else:
        run = json.loads(row[0])
        if run["completeness"]["status"] == "conflicting":
            out.append(
                "  REJECTED: ambiguous app-id join ("
                + "; ".join(run["completeness"]["reasons"]) + ")"
            )
        out.append(f"  code_commit       {run['version']['code_commit']}")
        out.append(
            f"  definition v{run['version']['definition_version']}"
            f" hash {run['version']['definition_hash']}"
        )
        plans = db.execute(
            "SELECT json FROM records WHERE kind='plan'"
            " AND json_extract(json,'$.version.run_id')=?",
            (run_id,),
        ).fetchall()
        for (pj,) in plans:
            p = json.loads(pj)
            out.append(
                f"  exec {p['version']['execution_id']} plan_hash"
                f" {p['payload']['plan_hash']}"
            )
            for t in p["payload"]["read_tables"]:
                if t.get("table"):
                    out.append(
                        f"    read {t['table']}: columns={dict(t['read_columns'])}"
                        f" -> {t['catalog_match']}"
                        f" (catalog now v{t['catalog_version_now']})"
                    )
    db.close()
    write_out("query-b.txt", out)


def query_c(table: str) -> None:
    out = [f"(c) runs that read an OLDER schema of {table} than the current one"]
    db = load_db()
    cur = db.execute(
        "SELECT json_extract(json,'$.version.version'),"
        " json_extract(json,'$.payload.updated_at') FROM records"
        " WHERE kind='table-schema' AND subject=?",
        (table,),
    ).fetchone()
    if cur is None:
        out.append(f"  {table} not in catalog")
        db.close()
        write_out("query-c.txt", out)
        return
    out.append(f"  current: v{cur[0]} (updated_at {cur[1]})")
    runs = db.execute(
        "SELECT json_extract(json,'$.payload.start'),"
        " json_extract(json,'$.payload.reads_expected'), subject FROM records"
        " WHERE kind='run' ORDER BY subject"
    ).fetchall()
    for start, reads_expected, run_id in runs:
        entries = db.execute(
            "SELECT json_extract(json,'$.payload.read_tables') FROM records"
            " WHERE kind='plan'"
            " AND json_extract(json,'$.version.run_id')=?",
            (run_id,),
        ).fetchall()
        table_entries = [
            t
            for (rts_json,) in entries
            for t in json.loads(rts_json)
            if t.get("table") == table
        ]
        expected = table in json.loads(reads_expected or "[]")
        if not table_entries:
            if expected:
                out.append(f"  {run_id}: UNKNOWN (no scan evidence for {table})")
            continue
        for t in table_entries:
            cm = t["catalog_match"]
            if cm.startswith("not-current"):
                verdict = "NOT CURRENT - definitely another schema version"
            elif cm == "matches-current-columns":
                verdict = "current"
            elif cm == "no-columns-read":
                verdict = "UNKNOWN (scan read no columns, e.g. count-only)"
            else:
                verdict = (
                    "POSSIBLY OLDER - pruned subset and run predates current version"
                    if (start or "") < (cur[1] or "")
                    else "subset-consistent (run after current version)"
                )
            out.append(f"  {run_id}: {verdict}")
    db.close()
    write_out("query-c.txt", out)


def write_out(name: str, lines: list[str]) -> None:
    outdir = os.path.join(PROTO, "outputs")
    os.makedirs(outdir, exist_ok=True)
    text = "\n".join(lines) + "\n"
    with open(os.path.join(outdir, name), "w") as f:
        f.write(text)
    print(text, end="")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("collect").set_defaults(func=lambda a: collect())
    sub.add_parser("query-a").set_defaults(func=lambda a: query_a())
    pb = sub.add_parser("query-b")
    pb.add_argument("run_id")
    pb.set_defaults(func=lambda a: query_b(a.run_id))
    pc = sub.add_parser("query-c")
    pc.add_argument("table")
    pc.set_defaults(func=lambda a: query_c(a.table))
    args = ap.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
