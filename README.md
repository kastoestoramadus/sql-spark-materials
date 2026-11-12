# SQL/Spark advisory research materials (October 2026)

A self-contained mirror of one research thread: reading Spark SQL plans, performance
and cost levers, an AI-reviewer design, local tooling (Windows + Docker), a benchmark
of 40 flawed SQL/Spark programs, and a 30/90-day consulting playbook.

**This repository is temporary.** It was published only so the materials can be opened
from a restricted machine without logging in, and it will be deleted after a few weeks.

## What is where

| Directory | Contents |
|---|---|
| `overview/` | The thread overview page (`overview.html`, open it in a browser), a findings digest with source quotes, a task inventory, and a version-ageing table (which claims went stale) |
| `190-evidence-collector/` | Prototype of a Spark evidence collector: what event logs can prove about schema provenance, plus a comparison with OpenLineage |
| `210-performance-and-cost/` | A 44-row catalogue of antipatterns and levers (symptom / detection / fix / measured effect) and the 15 example scripts behind the measurements |
| `220-ai-reviewer/` | Design of an AI reviewer for SQL: 26 failure modes, a reading experiment, four draft agent skills (`drafts/`), the compact-plan script and experiment artifacts |
| `230-tools-windows-docker/` | Tool survey for local Windows+Docker work (`tools.tsv`), Dockerfiles (untested — Docker was down at the time) and a synthetic Spark job |
| `260-pitfalls-benchmark/` | 35 reproduced correctness pitfalls (`pitfalls.tsv`), a 40-case benchmark with hidden keys and decoys, and `score.py` |
| `280-playbook/` | A 30/90-day consulting playbook with five ready templates (`templates/`) |

## Provenance and caveats

- Produced 17–19 October 2026 by AI agents from the owner's research pipeline;
  reviewed in November 2026. Reports quote their own sources with file:line where possible.
- Version claims in the reports were current for Spark 4.2.0; check `overview/aged.tsv`
  before reusing anything version-specific (Spark 4.3.0 shipped 2026-10-30).
- Known gaps, honestly recorded: the benchmark was never scored by a real model;
  Docker never started, so the Dockerfiles are untested; Databricks DBU prices were
  never verified. Details in `overview/overview.html` (section "Luki").
- No licence: all rights reserved by the repository owner.
