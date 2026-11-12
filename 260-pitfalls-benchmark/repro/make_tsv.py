"""Build pitfalls.tsv from the registry + run outputs. No Spark session needed.

Run: ../venv/py4/bin/python make_tsv.py   (from repro/)
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from pitfalls_core import PITFALLS as A  # noqa: E402
from pitfalls_more import PITFALLS as B  # noqa: E402

# ids whose main detection is a parser-level lint (no data needed)
LINTABLE = {"001", "002", "007", "010", "011", "015", "016", "023", "031", "032", "033", "034"}

seen: set[str] = set()
rows: list[dict[str, str]] = []
for p in A + B:
    if p["id"] in seen:
        continue
    seen.add(p["id"])
    ev_file = HERE / "outputs" / f"{p['id']}-{p['slug']}.txt"
    ev = ""
    if ev_file.exists():
        wrong_lines = [l for l in ev_file.read_text(encoding="utf-8").splitlines() if "WRONG" in l]
        ev = (wrong_lines[0] if wrong_lines else ev_file.read_text(encoding="utf-8").splitlines()[-3])[:200]
    rows.append({
        "id": p["id"],
        "title": p["title"],
        "category": p["category"],
        "engines": p["engines"],
        "why": p["why"],
        "detect_static": p["detect_static"],
        "detect_test": p["detect_test"],
        "lint_only": "yes" if p["id"] in LINTABLE else "needs-data-or-stats",
        "source": p["source"],
        "evidence": f"repro/outputs/{p['id']}-{p['slug']}.txt :: {ev}",
    })

out = HERE.parent / "pitfalls.tsv"
cols = ["id", "title", "category", "engines", "why", "detect_static", "detect_test",
        "lint_only", "source", "evidence"]
with out.open("w", encoding="utf-8") as f:
    f.write("\t".join(cols) + "\n")
    for r in rows:
        f.write("\t".join(r[c].replace("\t", " ").replace("\n", " ") for c in cols) + "\n")
print(f"wrote {out} with {len(rows)} rows")
