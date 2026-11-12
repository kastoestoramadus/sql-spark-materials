# First-week checklist — SQL/Spark performance & cost review at a bank

Working copy for one engagement. Fill every line; if a line cannot be filled, write the blocker in "Open
questions" at the bottom and who owns it. Evidence pointers in brackets refer to `../report.md` sources.

## 0. Before day one (prepare at home, no bank data)

- [ ] Local toolchain verified on Windows + Docker WITHOUT WSL:
      - [ ] Docker Desktop runs with Hyper-V backend (needs all-users installation; ask the bank's admins
            whether that is installed — per-user installs default to WSL 2) [Docker docs, MS Hyper-V overview]
      - [ ] `docker pull apache/spark:<tag>` works and `docker run -it apache/spark /opt/spark/bin/spark-shell`
            starts [apache/spark Docker Hub]
      - [ ] Plan for running the Spark History Server and any Python tooling inside a container, not on the
            host (the shipped `sbin/start-history-server.sh` is a Unix shell script) [Spark monitoring docs]
- [ ] Blank copies of: findings table, savings estimate sheet, executive summary (this `templates/` dir).
- [ ] List of questions to send ahead (see `../report.md` section 6 "Questions to ask the bank").

## 1. Access (day 1)

- [ ] Spark Web UI reachable for at least the top queues/clusters; history server URL if apps are finished
- [ ] Event logs: is `spark.eventLog.enabled` on, and where is `spark.eventLog.dir`? Read access?
- [ ] Scheduler/cluster manager access: YARN ResourceManager REST (`/ws/v1/cluster/apps`) or
      Kubernetes/cloud console equivalents; queue definitions and policies
- [ ] Cost data: cloud billing export (e.g. AWS Cost and Usage Report in S3, Databricks system tables) or
      on-prem cost basis from finance; per-job tags present?
- [ ] Code: repository with the job definitions (SQL, Spark code, scheduler definitions like Airflow DAGs)
- [ ] Table metadata: catalog (Hive metastore / Unity Catalog / other), table sizes and partition counts
- [ ] The AI tools you are allowed to use with bank data, the approved endpoint, and the written policy

## 2. Platform facts (days 1–2)

- [ ] On-prem or cloud (or both)? Vendor and product names, Spark version, cluster manager
- [ ] Spark version ≥ 3.2? (AQE on by default since 3.2.0 — changes which tuning advice still applies)
- [ ] SQL dialect(s) in use: Spark SQL, Hive-flavoured, or RDBMS pushed down?
- [ ] Cluster sizing defaults, autoscaling on/off, queue/privileges model
- [ ] Who pays: central IT cost centre vs per-team chargeback? What currency does the bank count in
      (DBUs, instance-hours, memorySeconds, €/month)?

## 3. Governance facts (days 2–3)

- [ ] Change control: what is the change process for job code and configs (CAB/approver/tooling)?
- [ ] Are any of the pipelines feeding risk reports (BCBS 239-relevant risk data aggregation)? If yes,
      validation/evidence expectations rise
- [ ] Data classification rules for what may be pasted into AI tools; anonymisation requirements
- [ ] Model-risk contact if AI-assisted analysis outputs inform decisions (SR 11-7-style validation)

## 4. People (days 1–3)

- [ ] Named owners for the top 10 jobs/pipelines
- [ ] Platform team contact (clusters, queues, upgrades)
- [ ] Finance owner of the platform budget
- [ ] Risk/compliance contact for the AI-tool policy

## 5. First measurements (days 3–5)

- [ ] Top 10 expensive jobs list (from billing export or YARN `memorySeconds`/`vcoreSeconds` share)
- [ ] For each: runtime, frequency, cluster size, cost per run (see savings sheet), owner, business purpose
- [ ] One cheap candidate for a first quick win identified and agreed with its owner
- [ ] Baseline captured so any improvement can be proven: runtime, resource use, AND output checks
      (row counts/checksums before vs after) — [folklore, standard practice: verify results unchanged]

## 6. Process agreements (day 5)

- [ ] Agreed cadence: who sees what, when (weekly findings review, monthly savings tally)
- [ ] Agreed prioritisation rule (saving x confidence / (effort x risk)) recorded in the findings table
- [ ] Agreed definition of "savings realised" with finance (who signs the number)

## Open questions / blockers

| # | Question | Asked to | Date | Answer |
|---|----------|----------|------|--------|
|   |          |          |      |        |
