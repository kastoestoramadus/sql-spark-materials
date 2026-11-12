#!/usr/bin/env bash
# End-to-end prototype run: seed, round 1 (with failure + crash + shadow app),
# schema change + code change (git round2), round 2, collect, query.
set -uo pipefail
. /home/walidus/ai-based-projects/idle-coordinator/system/env.sh
PROTO="$(cd "$(dirname "$0")" && pwd)"
PY="$PROTO/venv/bin/python"
export PYSPARK_PYTHON="$PY"  # workers must match driver python (3.12)
cd "$PROTO"
rm -rf runs warehouse catalog records outputs
mkdir -p runs/eventlog runs/appinfo catalog warehouse

"$PY" seed.py || exit 1

echo "--- round 1 (commit round1, schemas v1)"
git -C repo checkout -q round1
"$PY" runner.py run wf_sales_daily 1 1
"$PY" runner.py run wf_risk_report 1 1 --crash     # attempt 1 dies, no artifacts
"$PY" runner.py run wf_risk_report 1 2             # retry succeeds
"$PY" runner.py run wf_gdpr_purge 1 1              # fails: buggy code, exit 1
"$PY" runner.py shadow 1                           # unmapped app, not indexed

echo "--- platform DDL + code change"
"$PY" change_schema.py
git -C repo checkout -q round2

echo "--- round 2 (commit round2, customers v2)"
"$PY" runner.py run wf_sales_daily 2 1
"$PY" runner.py run wf_risk_report 2 1
"$PY" runner.py run wf_gdpr_purge 2 1

echo "--- collect and query"
"$PY" collector.py collect
"$PY" collector.py query-a
"$PY" collector.py query-b wf_sales_daily--r1--a1
"$PY" collector.py query-c customers
