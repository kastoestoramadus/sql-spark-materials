"""Score reviewer findings against case keys.

Usage: python score.py <cases_dir> <submission_dir> [penalty]
  <cases_dir>    directory of NN-name/case.json + answer.md
  <submission_dir> directory with one NN.txt per case (the reviewer's findings)
  penalty        points subtracted per decoy/false claim found (default 1.0)

Scoring: each required finding counts 1.0 if any of its alternative phrasings
(case.json required_findings, split on ' | ' or ' or ') appears in the submission
(case-insensitive substring). Each non_defects decoy phrase found in the
submission counts as a false claim and subtracts the penalty. Limitations are
documented in README.md (paraphrase detection is substring-based on purpose:
an ungrounded paraphrase without the key term scores nothing).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def alts(line: str) -> list[str]:
    parts = line.replace(" or ", " | ").split(" | ")
    return [p.strip().lower() for p in parts if len(p.strip()) > 3]


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    cases_dir = Path(sys.argv[1])
    sub_dir = Path(sys.argv[2])
    penalty = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    rows: list[tuple[str, str, int, int, int, float]] = []
    for cdir in sorted(cases_dir.iterdir()):
        cj = cdir / "case.json"
        if not cj.exists():
            continue
        meta = json.loads(cj.read_text(encoding="utf-8"))
        n = meta["n"]
        sub_file = sub_dir / f"{n}.txt"
        text = sub_file.read_text(encoding="utf-8").lower() if sub_file.exists() else ""
        hit = sum(1 for f in meta.get("required_findings", []) if any(a in text for a in alts(f)))
        total = len(meta.get("required_findings", []))
        decoys = sum(1 for d in meta.get("non_defects", []) if any(a in text for a in alts(d)))
        score = round(hit - penalty * decoys, 2)
        rows.append((n, meta["difficulty"], hit, total, decoys, score))
    print("case\tfound\trequired\tdecoy_hits\tscore\tdifficulty")
    for n, diff, hit, total, dec, sc in rows:
        print(f"{n}\t{hit}\t{total}\t{dec}\t{sc}\t{diff}")
    if rows:
        found = sum(r[2] for r in rows)
        req = sum(r[3] for r in rows)
        dec = sum(r[4] for r in rows)
        tot = round(sum(r[5] for r in rows), 2)
        print(f"TOTAL\t{found}\t{req}\t{dec}\t{tot}\trecall={found / req:.0%} penalty={penalty}")
        for diff in ("easy", "medium", "hard"):
            sel = [r for r in rows if r[1] == diff]
            if sel:
                f = sum(r[2] for r in sel)
                t = sum(r[3] for r in sel)
                print(f"  {diff}: recall {f}/{t} = {f / t:.0%}, decoy hits {sum(r[4] for r in sel)}")


if __name__ == "__main__":
    main()
