# decision.md — task 280 (retro-prep)

## 1. Question

What should the owner prepare BEFORE the first day at the bank, and which questions should be asked of the
bank first, so that days 1–5 produce a defensible top-10 expensive jobs list and a compliant working setup?

## 2. Evidence table (all fetched 2026-10-17; URLs and quotes also in ../report.md §7)

| # | Evidence | Source |
|---|----------|--------|
| D1 | After-the-fact analysis needs event logs: "To view the web UI after the fact, set spark.eventLog.enabled to true before starting the application." | https://spark.apache.org/docs/latest/monitoring.html |
| D2 | Top-jobs costing needs the platform's usage/cost source: AWS CUR "break down your costs ... by tags that you define yourself"; YARN REST exposes per-app "memorySeconds, vcoreSeconds"; Databricks bills per DBU with cluster-size DBU counts | docs.aws.amazon.com/cur/...; hadoop.apache.org ResourceManagerRest; azure.microsoft.com databricks pricing |
| D3 | Without WSL, Docker Desktop needs the Hyper-V backend, and "Hyper-V is only available with all-users installation" — an admin decision at the bank | https://docs.docker.com/desktop/setup/install/windows-install/ |
| D4 | A portable Spark exists: "docker run -it apache/spark /opt/spark/bin/spark-shell" | https://hub.docker.com/r/apache/spark |
| D5 | Tuning advice is version-gated: AQE "enabled by default since Apache Spark 3.2.0" | spark.apache.org sql-performance-tuning + sql-migration-guide (two pages) |
| D6 | AI-tool privacy depends on the bank's contract tier: Anthropic "may not train models on Customer Content from Services"; MS Foundry inputs/outputs "are NOT used ... to improve their models" but abuse monitoring applies by default | anthropic.com/legal/commercial-terms; learn.microsoft.com .../openai/data-privacy |
| D7 | Regulated expectations raise evidence needs: BCBS 239 P3 "Data should be aggregated on a largely automated basis so as to minimise the probability of errors"; SR 11-7 "effective challenge"; EU AI Act Art.26 logs "at least six months" | sources/bcbs239.pdf; sources/sr11-7.pdf; artificialintelligenceact.eu/article/26/ |
| D8 | Savings credibility needs finance agreement on the number; frameworks put allocation before optimisation (FinOps Inform→Optimize→Operate) | finops.org/framework/phases/ |

## 3. Options

A. Prepare tooling first (verify Docker/Hyper-V + Spark image at home; ask platform questions on day 1).
   Cost: ~1 day of home prep + a long question list. Benefit: nothing blocks days 2–5; questions arrive
   informed. Risk: some prep wasted if the bank's environment differs (e.g. no Docker rights).
B. Prepare a question-first pack (no local tooling; send questions ahead, build environment after answers).
   Cost: minimal. Benefit: zero wasted prep. Risk: day-1 latency while tools install under bank restrictions;
   admin tasks (all-users Docker install) can take days at a bank — the critical path.
C. Ask the bank to provide the analysis environment entirely (their VDI, their tooling).
   Cost: coordination. Benefit: maximal compliance. Risk: no offline preparation possible; velocity capped
   by environment availability and permissions.

## 4. Recommendation and confidence

Recommend A with B's question list sent ahead (they combine: the templates and question list travel before
the consultant, the toolchain is verified so no day-1 install happens). Confidence HIGH for the tooling half
(D3, D4 are directly sourced and testable at home), MEDIUM for the question ordering (rests on D1/D2/D6/D7
being the binding constraints, which is experience-based). What would change my mind: the bank answering
"we have no event logs and no billing export / no per-job cost source" — then day-1 work becomes
instrumentation-first and the top-10 list slips by weeks. How many cases does this rest on: the ordering is
generalisation from public documentation of 4 platform families (Spark, YARN, AWS, Azure/Databricks) plus
two vendor terms pages; no bank-specific case was available (correctly so — none exists yet).

## 5. What only the owner can decide / could not verify

- Owner-only: the actual engagement scope, rate/contract terms, and whether to accept the bank's AI-tool
  policy or negotiate (e.g. abuse-monitoring concessions are contract matters).
- Owner-only: whether BCBS 239/model-risk/s high-risk-AI classifications apply to the pipelines — bank
  answers, then the owner judges the evidence burden.
- Not verified: Databricks system-tables column detail (docs page moved, 404); OpenAI enterprise privacy
  (403); EBA/BoE AI-survey pages (404 during fetch); exact current DBU list prices; whether the bank's
  Windows fleet has Hyper-V-based Docker installed at all. All listed as questions for the bank (report §6).
