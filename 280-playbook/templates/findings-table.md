# Findings table — SQL/Spark performance & cost review

One row per finding. Every row must carry evidence (a command output, event-log/UI reference, or billing
line) — never a bare assertion. Copy the header row for each new review cycle.

| Field | How to fill |
|-------|-------------|
| ID | F-001, F-002 … stable across the engagement |
| Job / pipeline | Name plus where it is defined (repo path, scheduler entry) |
| Observation | What was measured, in plain words (e.g. "stage 7 re-reads 800 GB from object storage each run") |
| Evidence | Pointer: event log + stage id, UI screenshot ref, EXPLAIN output, billing line, command + date |
| Impact est. | Annual cost or time at stake, from the savings sheet; mark LOW/MED/HIGH confidence |
| Proposed change | The concrete change (config, SQL rewrite, layout change, scheduling) |
| Effort | S / M / L (person-days: <1 / 1–5 / >5) — practitioner scale [folklore] |
| Risk | C (results could change), P (performance regression elsewhere), O (operational, e.g. rerun needed); plus who must approve |
| Priority | saving x confidence / (effort x risk); anything with risk=C needs before/after result comparison |
| Owner / status | Named person; open / proposed / in change control / done / measured |

## Findings

| ID | Job / pipeline | Observation | Evidence | Impact est. | Proposed change | Effort | Risk | Priority | Owner / status |
|----|----------------|-------------|----------|-------------|-----------------|--------|------|----------|----------------|
| F-001 | | | | | | | | | |
| F-002 | | | | | | | | | |

## Suggested observation checklist (what to look at, in order)

1. Skew and shuffle: stage-level shuffle read/write and spill in the Spark UI (Jobs → Stage detail;
   "Shuffle spill (disk) is the size of the serialized form of the data on disk") [Spark web UI docs]
2. Join strategy and AQE behaviour: is AQE on (default since 3.2.0)? broadcast thresholds, skew join
   splitting active? [Spark SQL performance tuning docs]
3. Task count vs cores: "2-3 tasks per CPU core" recommendation; tiny-task stages [Spark tuning docs]
4. Input prunability: files/partitions read vs used; missing partition filters in SQL predicates
5. Caching misuse: Storage tab — cached but rarely reused, or spills
6. Executor health: GC time share, heap histogram (Executors tab) [Spark web UI docs]
7. Frequency vs value: nightly 3-hour job that 5 people read once a week → scheduling/SLA question
8. Cost attribution: DBUs or instance-hours per job where the platform exposes it; YARN memorySeconds
   share on-prem [YARN REST, AWS CUR, Azure Databricks pricing docs]
