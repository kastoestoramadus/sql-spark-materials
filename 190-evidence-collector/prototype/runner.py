"""Runner: executes a workflow script and appends a run record to runs/index.jsonl.

Run record fields are the runner's OWN observation (start/end/exit code), not
the collector's inference. `--crash` kills the child early to simulate an
attempt that leaves no artifacts (no appinfo, maybe no event log).
`shadow` runs an app WITHOUT recording it (omitted-workflow test).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any  # boundary: parsed JSON records

PROTO = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(PROTO, "repo")
VENV_PY = os.path.join(PROTO, "venv", "bin", "python")
RUNS = os.path.join(PROTO, "runs")
EVENTLOG = os.path.join(RUNS, "eventlog")
APPINFO = os.path.join(RUNS, "appinfo")
INDEX = os.path.join(RUNS, "index.jsonl")
COLLECTOR_VERSION = "runner 0.1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git(*args: str) -> str:
    out = subprocess.run(
        ["git", "-C", REPO, *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def definition_state(wf: str) -> dict[str, Any]:
    manifest_rel = f"manifests/{wf}.json"
    manifest = json.loads(git("show", f"HEAD:{manifest_rel}"))
    commit = git("rev-parse", "HEAD")
    h = hashlib.sha256()
    for rel in [manifest_rel, manifest["entry"], "wfbase.py"]:
        h.update(rel.encode())
        h.update(b"\0")
        h.update(git("show", f"HEAD:{rel}").encode())
        h.update(b"\0")
    return {"manifest": manifest, "commit": commit, "definition_hash": h.hexdigest()[:16]}


def child_env(run_id: str, attempt: int) -> dict[str, str]:
    env = {
        "PROTO_ROOT": PROTO,
        "RUN_ID": run_id,
        "ATTEMPT": str(attempt),
        "APP_NAME": run_id,
        "EVENTLOG_DIR": EVENTLOG,
        "APPINFO_DIR": APPINFO,
        "WAREHOUSE_DIR": os.path.join(PROTO, "warehouse"),
        "CATALOG_DB": os.path.join(PROTO, "catalog", "catalog.db"),
        "PYSPARK_PYTHON": VENV_PY,
        "PATH": os.environ.get("PATH", ""),
    }
    if "JAVA_HOME" in os.environ:
        env["JAVA_HOME"] = os.environ["JAVA_HOME"]
    return env


def execute(run_id: str, attempt: int, entry: str, crash: bool) -> dict[str, Any]:
    os.makedirs(APPINFO, exist_ok=True)
    cmd = [VENV_PY, os.path.join(REPO, entry)]
    start = now()
    if crash:
        p = subprocess.run(
            ["timeout", "-s", "KILL", "5", *cmd],
            env=child_env(run_id, attempt),
            capture_output=True,
            text=True,
        )
    else:
        p = subprocess.run(cmd, env=child_env(run_id, attempt), capture_output=True, text=True)
    end = now()
    appinfo_path = os.path.join(APPINFO, f"{run_id}.json")
    if not os.path.exists(appinfo_path):  # wfbase appends the attempt suffix
        appinfo_path = os.path.join(APPINFO, f"{run_id}--{attempt}.json")
    appinfo = None
    if os.path.exists(appinfo_path):
        with open(appinfo_path) as f:
            appinfo = json.load(f)
    return {
        "start": start,
        "end": end,
        "exit_code": p.returncode,
        "stdout_tail": p.stdout[-400:],
        "stderr_tail": p.stderr[-400:],
        "appinfo": appinfo,
    }


def record(wf: str, rnd: int, attempt: int, crash: bool) -> None:
    run_id = f"{wf}--r{rnd}--a{attempt}"
    d = definition_state(wf)
    res = execute(run_id, attempt, d["manifest"]["entry"], crash)
    rec = {
        "run_id": run_id,
        "workflow": wf,
        "round": rnd,
        "attempt": attempt,
        "code_commit": d["commit"],
        "definition_version": d["manifest"]["definition_version"],
        "definition_hash": d["definition_hash"],
        "collector_version": COLLECTOR_VERSION,
        "crash_simulated": crash,
        **res,
    }
    with open(INDEX, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(
        f"runner: {run_id} exit={res['exit_code']} app_id="
        f"{(res['appinfo'] or {}).get('app_id')}"
    )


def shadow(rnd: int) -> None:
    run_id = f"wf_shadow--r{rnd}--a1"
    res = execute(run_id, 1, "wf_shadow.py", False)
    print(f"shadow: {run_id} exit={res['exit_code']} (NOT recorded in index)")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("wf")
    p_run.add_argument("round", type=int)
    p_run.add_argument("attempt", type=int)
    p_run.add_argument("--crash", action="store_true")
    p_run.set_defaults(func=lambda a: record(a.wf, a.round, a.attempt, a.crash))
    p_sh = sub.add_parser("shadow")
    p_sh.add_argument("round", type=int)
    p_sh.set_defaults(func=lambda a: shadow(a.round))
    args = ap.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
