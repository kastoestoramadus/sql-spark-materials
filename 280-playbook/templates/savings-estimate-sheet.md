# Savings estimate sheet — explicit assumptions

Every number in an executive summary traces back to this sheet. Rule: no saving is reported without (a) a
measured baseline, (b) a stated assumption list, (c) a confidence mark, and (d) who validated the number.

## A. Per-job cost model (fill one block per job)

```
Job: ________________  Owner: ____________  Review date: ________
Frequency: runs/month ______  (source: scheduler / event logs, date: ______)

CLOUD variant (e.g. Databricks on AWS/Azure, EMR):
  Unit price:  DBU rate ______ /instance-hour rate ______  (source: bank's contract or public list
               price + date; list prices are region-dependent and NOT the bank's price)
  Usage per run: ______ DBU-hours / instance-hours  (source: system tables / billing export, date)
  Cost per run  = unit price x usage per run
  Monthly cost  = cost per run x runs/month
  Annualised    = monthly x 12

ON-PREM variant (YARN/K8s cluster, cost allocation):
  Cluster monthly fully-loaded cost: ______  (source: finance — MUST come from the bank)
  Job's share = (job memorySeconds) / (cluster memorySeconds per month)  (source: YARN RM REST
                /ws/v1/cluster/apps fields: allocatedMB, memorySeconds, vcoreSeconds; date)
  Monthly cost = cluster cost x job share
```

## B. Expected saving per finding

```
Finding ID: F-___   Job: ____________
Baseline metric  : ______ (runtime per run / cost per run / both; measurement date + tool)
Expected metric  : ______ (from: measured A/B test / vendor claim marked as such / extrapolation —
                   write which, and for extrapolations the formula)
Runs affected    : ______ % of runs (full/partial)
Gross annual saving = (baseline - expected) x cost per run basis x runs/year x % affected
Deductions:
  - rerun/validation cost during rollout: ______
  - licences/prepurchases affected (e.g. DBU prepurchase tiers): ______
Net annual saving: ______
Confidence: HIGH (A/B measured on bank data) / MEDIUM (mechanism certain, size estimated) /
            LOW (vendor claim or analogy)
Assumptions (list each; strike none):
  1. Workload volume stays at ___ for the horizon
  2. Price basis: ___ (contract rate / list rate dated ___)
  3. Frequency change: none planned (or: known change ___)
  4. Result-neutrality: outputs verified identical by ___ (row counts/checksums) on ___
Validated by (finance/platform owner): ____________ Date: ______
```

## C. Assumptions register (one row per assumption across all findings)

| # | Assumption | Used by findings | Basis | If wrong, saving becomes | Owner |
|---|------------|------------------|-------|--------------------------|-------|
| A1 | e.g. "EMR billed per-second with 1-minute minimum" | F-003 | AWS pricing page, fetched 2026-10-17 | recalibrate | |
| A2 | | | | | |

## D. Honesty rules

- Vendor performance multipliers (e.g. Photon "DBU emission rate 2.9X vs non-Photon") are claims from the
  vendor's own pricing page: they change BOTH speed and DBU burn, so quote savings only after an A/B run.
- A saving the bank cannot see in its own bill is not a saving: agree with finance which report is truth.
- Capacity savings on a fixed on-prem cluster are only real if capacity is actually removed or redeployed;
  otherwise report "capacity freed", not "cost saved". [folklore, standard FinOps caution]
