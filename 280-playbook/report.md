Executed by: glm-5.3; effort: unknown, form default; ZCode idle subagent
Coordinator/run: coordinator model id: account:zai-offpeak-idle-plan/GLM-5.3; task 280-sql-spark-consulting-playbook; attempt 1; worker 2 of batch 5
Start: 2026-10-17T19:36:50+02:00  End: <filled below>

# Playbook: first 30/90 days of performance and cost consulting on SQL/Spark at a bank

Assumptions taken (conservative reading, unknowns flagged): (1) platform may be on-prem OR cloud — both are
covered and every "how to find the expensive jobs" recipe has an on-prem and a cloud variant; (2) the SQL
dialect is Spark SQL, possibly Hive-flavoured — no RDBMS-specific advice is given beyond "ask first";
(3) the bank's Windows machines run Docker WITHOUT WSL, so Docker Desktop runs on the Hyper-V backend —
this has an install-mode implication the owner must ask the bank's admins about (section 3.1); (4) no bank
data exists yet: every number in the templates is a placeholder to be filled from the bank's own systems.
All web sources were fetched 2026-10-17 (UTC+2). Quotes are verbatim from the fetched pages/PDFs.

---

## 1. How performance and cost reviews of data platforms are organised

### 1.1 What to measure first (Spark-specific, in this order)

The primary measurement surface is the Spark Web UI (or event logs replayed in the history server). What it
shows, per the official docs (https://spark.apache.org/docs/latest/web-ui.html, fetched 2026-10-17):

- Jobs/Stages: "The Jobs tab displays a summary page of all jobs in the Spark application and a details page
  for each job." / "The Stages tab displays a summary page that shows the current state of all stages of all
  jobs in the Spark application"
- Executors: "Each row shows resource usage (memory, disk, cores), storage memory reserved for cached data,
  task counts, shuffle totals, and performance signals such as GC time."
- SQL: "The SQL tab lists all SQL and DataFrame queries submitted to the Spark application ... with plan
  visualization and per-operator metrics."
- Stage detail metrics that flag expensive stages: "Duration of tasks.", "GC time is the total JVM garbage
  collection time.", "Peak execution memory is the maximum memory used by the internal data structures
  created during shuffles, aggregations and joins.", "Shuffle spill (disk) is the size of the serialized form
  of the data on disk."

Why event logs matter: "this information is only available for the duration of the application by default.
To view the web UI after the fact, set spark.eventLog.enabled to true before starting the application." and
"It is still possible to construct the UI of an application through Spark's history server, provided that the
application's event logs exist." (https://spark.apache.org/docs/latest/monitoring.html, fetched 2026-10-17).
So the FIRST measurement question at the bank is: are event logs kept, where, for how long?

Classic tuning levers, from the official tuning guide (https://spark.apache.org/docs/latest/tuning.html,
fetched 2026-10-17): serialization ("Often, this will be the first thing you should tune to optimize a Spark
application." — Kryo "often as much as 10x" faster/more compact than Java serialization), parallelism
("In general, we recommend 2-3 tasks per CPU core in your cluster."), memory ("The simplest fix here is to
increase the level of parallelism, so that each task's input set is smaller."), and serialized caching
("For most programs, switching to Kryo serialization and persisting data in serialized form will solve most
common performance issues.").

Check the Spark version before advising any of this: Adaptive Query Execution "is enabled by default since
Apache Spark 3.2.0" (https://spark.apache.org/docs/latest/sql-performance-tuning.html, fetched 2026-10-17;
confirmed by the migration guide: "In Spark 3.2, spark.sql.adaptive.enabled is enabled by default.",
https://spark.apache.org/docs/latest/sql-migration-guide.html, fetched 2026-10-17). AQE already coalesces
post-shuffle partitions, converts sort-merge joins to broadcast/hash joins at runtime, and splits skewed
partitions (skew = partition > skewedPartitionFactor 5.0 x median AND > skewedPartitionThresholdInBytes
256MB, per the same page) — manual advice that predates 3.2 may be obsolete or harmful.

### 1.2 How to find the top ten expensive jobs

Cloud variant (Databricks-style): billing is per Databricks Unit (DBU) with per-cluster-size DBU counts and
list rates published on the vendor pricing pages (Azure Databricks page structure: "Cluster Size / DBU Count
/ DBU Price", "Photon Available as an option. DBU emission rate 2.9X vs non-Photon", "You can get up to 37%
savings over pay-as-you-go DBU prices when you pre-purchase",
https://azure.microsoft.com/en-us/pricing/details/databricks/, fetched 2026-10-17; exact list rates render
after region selection and were not extractable — and the bank's contract price, not the list price, is what
counts). On AWS, usage lands in the Cost and Usage Report: "AWS Cost and Usage Reports (AWS CUR) contains
the comprehensive set of cost and usage data available. You can ... break down your costs by the hour, day,
or month, by product or product resource, or by tags that you define yourself. AWS updates the report in
your bucket once a day" (https://docs.aws.amazon.com/cur/latest/userguide/what-is-cur.html, fetched
2026-10-17 — note the page's first sentence reads "most comprehensive set", quoted here exactly).
EMR specifically: "you pay a per-second rate for every second you use, with a one-minute minimum." and
"The Amazon EMR price is added to the Amazon EC2 price (the price for the underlying servers) and Amazon
Elastic Block Store" (https://aws.amazon.com/emr/pricing/, fetched 2026-10-17).

On-prem variant (YARN): the ResourceManager REST API exposes per-application resource usage:
`http://rm-http-address:port/ws/v1/cluster/apps` — "With the Applications API, you can obtain a collection
of resources, each of which represents an application.", each app carrying `allocatedMB`, `allocatedVCores`,
`memorySeconds`, `vcoreSeconds`, `queueUsagePercentage` (https://hadoop.apache.org/docs/stable/hadoop-yarn/hadoop-yarn-site/ResourceManagerRest.html,
fetched 2026-10-17). Top-10 by memorySeconds share of the cluster's monthly cost, cross-checked against
event-log runtimes and the scheduler's (Airflow etc.) job list. Kubernetes on-prem would use namespace/pod
metrics instead — ask the bank which cluster manager is in place.

Cross-check both variants with event logs so "expensive" means both money and wall-clock pain the owners
recognise.

### 1.3 Prioritising by saving versus effort and risk

Industry frameworks converge on: allocate first, then optimise from a documented option list, then operate
continuously. FinOps: "The FinOps journey consists of Inform, Optimize and Operate." with allocation a
capability of the Understand-Usage-and-Cost domain, and of the Optimize phase: "The goal in this phase is to
identify and document a list of options for the organization to optimize its technology state."
(https://www.finops.org/framework/ and https://www.finops.org/framework/phases/, fetched 2026-10-17; content
CC BY 4.0 — attribute the FinOps Foundation if reused; both pages are the same publisher, so framework
details are single-source-by-publisher, cross-checked only against AWS's pillar below.)
AWS Well-Architected cost-optimization pillar (pub. date 2024-06-27 on the page) defines the goal as:
"A cost-optimized workload fully utilizes all resources, achieves an outcome at the lowest possible price
point, and meets your functional requirements." with practices incl. "Expenditure and usage awareness",
"Cost effective resources", "Manage demand and supply resources", "Optimize over time"
(https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html, fetched
2026-10-17).

Working rule for this engagement (folklore, consistent with the above): priority = expected annual saving x
confidence / (effort x risk). Effort S/M/L in person-days; risk has three flavours — correctness (outputs
could change; requires before/after result verification), performance regression elsewhere, and operational
burden (reruns, change-control weight). Start with result-neutral config wins, then SQL rewrites with
checksummed outputs, then structural changes.

### 1.4 Questions that organise the review

Written into the first-week checklist (templates/first-week-checklist.md) and section 6 below.

## 2. Report and recommendation structure

Deliverables that worked as shapes (structure is folklore; the wording standard is sourced): findings table
with one evidenced row per finding (templates/findings-table.md), savings sheet with explicit assumptions
(templates/savings-estimate-sheet.md), one-page executive summary (templates/executive-summary-onepage.md).
Writing standard: "The Plain Writing Act of 2010 established the requirement that content for the public is
written for its specific audience." — write for the reader you have: engineers get stage ids, configs and
repro commands; managers get money, risk and decisions (https://digital.gov/guides/plain-language, fetched
2026-10-17, redirects from plainlanguage.gov/guidelines/).

## 3. Working in a regulated environment

### 3.1 Tooling on Windows with Docker, WITHOUT WSL

- Docker Desktop on Windows supports Hyper-V as a backend, but: "WSL 2 is the default and works for most
  users without administrator privileges", while "Hyper-V is only available with all-users installation" —
  i.e. WITHOUT WSL the bank's admins must have installed Docker Desktop all-users with the Hyper-V backend.
  ASK THE BANK which install mode exists; a per-user install without WSL would be the Docker VMM beta.
  (https://docs.docker.com/desktop/setup/install/windows-install/, fetched 2026-10-17.)
- Hyper-V itself is a type-1 hypervisor that "supports a wide range of operating systems for guest virtual
  machines, including many versions of Windows, Linux, and FreeBSD" and delivers "near-native performance
  and robust isolation for virtualized workloads" (https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/hyper-v-technology-overview,
  fetched 2026-10-17). Second source for the claim that Linux containers can run on Windows without WSL.
- Spark locally in Docker: the official image exists — `docker run -it apache/spark /opt/spark/bin/spark-shell`
  with current tags like `4.1.3-scala2.13-java17-python3-r-ubuntu` (10M+ pulls)
  (https://hub.docker.com/r/apache/spark, fetched 2026-10-17).
- Needs WSL or Linux (mark in any recommendation): running the shipped `./sbin/start-history-server.sh`
  (a Unix shell script) natively on Windows — run the history server in a container instead; anything that
  assumes a Linux host (async-profiler-style native profiling, perf tooling) — NOT verified here beyond the
  script example, flagged as "verify before recommending" in handoff.md.
- Python/Java experiments: containerised or in a folder inside the engagement workspace, never installed on
  the bank's host — matches the task rules and keeps the bank's change control clean.

### 3.2 Change control

Expect a formal gate before touching production jobs. Public concept anchor (US federal, analogous to bank
CABs): a "Configuration Control Board (CCB) ... a group typically consisting of two or more individuals that
have the collective responsibility and authority to review and approve changes to an information system",
with "Configuration Change Control — process for managing updates to the baseline configurations" (NIST SP
800-128, August 2011, https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-128.pdf,
fetched 2026-10-17; local copy sources/nist800-128.pdf). Ask the bank for ITS change process, approvers and
windows; propose changes, never apply them.

### 3.3 Data privacy when using AI tools

- GDPR Art. 32: controllers/processors must "implement appropriate technical and organisational measures to
  ensure a level of security appropriate to the risk", including "the pseudonymisation and encryption of
  personal data" and "a process for regularly testing, assessing and evaluating the effectiveness" of
  measures (https://gdpr-info.eu/art-32-gdpr/, fetched 2026-10-17; gdpr-info.eu is an unofficial mirror —
  the binding text is EUR-Lex; quote verified against the mirror only).
- Vendor terms (the two model families the bank uses):
  - Anthropic: "Anthropic may not train models on Customer Content from Services."; "Anthropic agrees that
    Customer (a) retains all rights to its Inputs, and (b) owns its Outputs."; "Customer Content is
    Customer's Confidential Information." (https://www.anthropic.com/legal/commercial-terms, fetched
    2026-10-17). Which Anthropic service tier the bank's access uses (consumer vs commercial/API) decides
    whether these terms apply — ASK THE BANK for the contract's data-processing terms, not the vendor page.
  - Microsoft (if models are Azure-hosted): "Your prompts (inputs) and completions (outputs), your
    embeddings, and your training data: ... are NOT used by providers of Models sold by Azure to improve
    their models or services."; "The models are stateless: no prompts or completions are stored in the
    model."; abuse monitoring with human review applies by default, modifiable "managed customers may apply
    to modify abuse monitoring"; for EEA deployments "the authorized Microsoft employees are located in the
    European Economic Area" (https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy,
    fetched 2026-10-17). OpenAI's enterprise-privacy page itself was blocked (403) — see handoff.
- Practical rule regardless of vendor: paste schemas, plans and synthetic samples, not personal or trade
  data; get the bank's written AI-tool policy and approved endpoint list before day one.

### 3.4 Lineage and audit expectations (BCBS 239 as publicly described)

BCBS 239 "Principles for effective risk data aggregation and risk reporting" (BCBS, January 2013;
PDF now at https://www.bis.org/publications/201301-guidelines-principles-effective-risk-data-aggregation-and-risk-reporting.pdf
after the old /publ/bcbs239.pdf URL 301-redirects, fetched 2026-10-17; local copy sources/bcbs239.pdf):
aimed "in particular, G-SIBs", after the crisis showed "banks' ability to take risk decisions in a timely
fashion was seriously impaired" (landing page, https://www.bis.org/publications/201301-guidelines-principles-effective-risk-data-aggregation-and-risk-reporting,
fetched 2026-10-17). Principles that touch a SQL/Spark review directly:
- Principle 3: "A bank should be able to generate accurate and reliable risk data ... Data should be
  aggregated on a largely automated basis so as to minimise the probability of errors.", "Controls
  surrounding risk data should be as robust as those applicable to accounting data.", and where manual
  processes/spreadsheets are used, "it should have effective mitigants in place (eg end-user computing
  policies and procedures)".
- Principle 1: risk data aggregation "should be subject to strong governance arrangements", be "Fully
  documented and subject to high standards of validation", with independent validation "using staff with
  specific IT, data and reporting expertise".
Implication: if the jobs under review feed risk reports, an "optimisation" that changes outputs or timing is
not just a perf change — document result-neutrality evidence and keep it auditable. Whether BCBS 239 (or the
bank's local implementation of it) applies to a given pipeline is something ONLY the bank can answer.
Lineage tooling to propose if asked: OpenLineage — "OpenLineage defines the metadata for running jobs and
their corresponding events", modelling "a generic model of dataset, job, and run entities", with Spark, Hive,
dbt, Airflow integrations (https://openlineage.io/docs/, fetched 2026-10-17); Apache Atlas is the
"Data Governance and Metadata framework for Hadoop" (title-only source, https://atlas.apache.org/, fetched
2026-10-17 — single, title-only source).

### 3.5 Model risk for AI-assisted analysis

- SR 11-7 "Supervisory Guidance on Model Risk Management" (Federal Reserve, 2011;
  https://www.federalreserve.gov/boarddocs/SRLetters/2011/SR1107.pdf, fetched 2026-10-17; local copy
  sources/sr11-7.pdf): "Model risk occurs primarily for two reasons: (1) a model may have fundamental errors
  and produce inaccurate outputs ... (2) a model may be used incorrectly or inappropriately or there may be
  a misunderstanding about its limitations and assumptions. Model risk increases with greater model
  complexity, higher uncertainty about inputs and assumptions, broader extent of use, and larger potential
  impact." and "managing model risk involves 'effective challenge' of models: critical analysis by
  objective, informed parties that can identify model limitations and produce appropriate changes."
  Structure: development/implementation/use, validation ("Validation involves a degree of independence from
  model development and use."), governance.
- EU AI Act (Reg. (EU) 2024/1689): if the bank's use of an AI system is high-risk, deployer duties include
  using systems per instructions, assigning "human oversight to natural persons who have the necessary
  competence, training and authority", ensuring input data "is relevant and sufficiently representative",
  and keeping logs "for a period appropriate to the intended purpose ... of at least six months"; high-risk
  obligations apply from 2 December 2027 (Annex III systems) / 2 August 2028 (Annex I)
  (https://artificialintelligenceact.eu/article/26/ and .../implementation-timeline/, fetched 2026-10-17;
  the explorer is a secondary source of the Regulation text).
- NIST AI RMF 1.0 (released January 26, 2023, per the page) is "intended for voluntary use and to improve
  the ability to incorporate trustworthiness considerations" (https://www.nist.gov/itl/ai-risk-management-framework,
  fetched 2026-10-17).
- Conservative stance for AI-assisted code/SQL analysis: the AI is an assistant, not a decision-maker;
  every recommendation is human-verified against the measured system; keep the trail (what was asked, what
  was proposed, what was adopted, who approved) so the analysis itself stays auditable. Whether the bank
  classifies this use as model-risk-relevant is a bank question (SR 11-7 is US guidance; EU banks typically
  have an internal model-risk policy the owner must ask for — not verified here, see handoff).

## 4. Presenting findings to engineers and managers

- One artefact per audience, same numbers everywhere: findings table (engineers), executive summary
  (managers), savings sheet (finance) — all cross-referenced, so a challenge on any number lands in one
  place. Wording standard: audience-first plain language (source in section 2).
- To engineers: lead with evidence (stage ids, event-log refs, before/after measurements), never with the
  conclusion; make each finding reproducible by them. [folklore]
- To managers: money, risk, decision needed, deadline; one page; TLDR first. [folklore; matches the
  owner's own PR conventions]
- When claims rest on vendor numbers, label them vendor claims and show the bank's own A/B measurement plan.

## 5. What to prepare before day one (summary; full decision analysis in decision.md)

Windows+Docker toolchain verified at home (apache/spark image, containerised history server, Hyper-V
question for admins), template pack printed, question list sent ahead, and NO bank data taken home.

## 6. Questions to ask the bank first (ordered)

1. On-prem or cloud (or mix)? Which product(s) — Databricks, EMR, Cloudera, homegrown YARN/K8s? Spark version?
2. Are event logs enabled and retained (where, how long)? History server available?
3. Where does per-job cost exist: system tables/billing export (cloud) or cluster cost + YARN queue usage
   (on-prem)? Who owns that data? Access for the consultant?
4. Docker Desktop install mode on our machines: all-users with Hyper-V (required to work without WSL)?
5. Which AI endpoints may touch bank data, under which policy; data classification of job metadata vs data?
6. Change process for job code and configs: approvers, windows, evidence required?
7. Do any target pipelines feed risk-data aggregation/risk reports (BCBS 239-relevant in the bank's own
   mapping)? Who is the model-risk/validation contact for AI-assisted analysis?
8. Who signs the "savings realised" number with finance?
9. SQL dialects in use (Spark SQL / Hive / RDBMS pushdown) and where the SQL lives (repo, scheduler)?
10. Frequency/scheduling source of truth (Airflow? Control-M?) for the top-10 attribution.

## 7. Evidence table (claim → source, all fetched 2026-10-17)

| # | Claim | Source (URL / local copy) | Kind |
|---|-------|---------------------------|------|
| E1 | Web UI tabs & stage metrics as first measurement | spark.apache.org/docs/latest/web-ui.html | official docs |
| E2 | Event logs / history server for after-the-fact analysis | spark.apache.org/docs/latest/monitoring.html | official docs |
| E3 | Tuning levers: Kryo, 2-3 tasks/core, parallelism, serialized caching | spark.apache.org/docs/latest/tuning.html | official docs |
| E4 | AQE default since 3.2.0; features & thresholds | spark.apache.org/docs/latest/sql-performance-tuning.html + sql-migration-guide.html | official docs x2 (held under second doc) |
| E5 | DBU-based billing, Photon 2.9X DBU emission, 37% pre-purchase | azure.microsoft.com/en-us/pricing/details/databricks/ | vendor pricing page |
| E6 | EMR per-second billing, 1-min minimum, added to EC2/EBS | aws.amazon.com/emr/pricing/ | vendor pricing page |
| E7 | CUR: comprehensive cost/usage data, tag breakdown, daily CSV to S3 | docs.aws.amazon.com/cur/latest/userguide/what-is-cur.html | official docs |
| E8 | YARN RM REST /ws/v1/cluster/apps with memorySeconds etc. | hadoop.apache.org/docs/stable/.../ResourceManagerRest.html | official docs |
| E9 | FinOps phases Inform/Optimize/Operate; Optimize = documented option list | finops.org/framework/ + /framework/phases/ (CC BY 4.0) | industry body |
| E10 | Cost-optimized workload definition; pillar practices | docs.aws.amazon.com wellarchitected cost-optimization-pillar | vendor framework |
| E11 | Docker Desktop: WSL2 default; Hyper-V only with all-users install | docs.docker.com/desktop/setup/install/windows-install/ | official docs |
| E12 | Hyper-V runs Linux guests, near-native, isolation | learn.microsoft.com hyper-v overview | official docs (2nd source for no-WSL) |
| E13 | Official apache/spark Docker image & usage | hub.docker.com/r/apache/spark | vendor/official repo |
| E14 | CCB definition, configuration change control | NIST SP 800-128 PDF (sources/nist800-128.pdf) | standards body |
| E15 | GDPR Art.32 measures incl. pseudonymisation, testing process | gdpr-info.eu/art-32-gdpr/ | unofficial mirror (label) |
| E16 | Anthropic: no training on API customer content; confidentiality | anthropic.com/legal/commercial-terms | vendor terms |
| E17 | MS Foundry/Azure OpenAI: inputs/outputs not used to improve models; abuse monitoring; EEA reviewers | learn.microsoft.com .../openai/data-privacy | official docs |
| E18 | BCBS 239 P1/P3 quotes; G-SIB focus; crisis motivation | bis.org publications/201301-...(.pdf) (sources/bcbs239.pdf + landing) | regulator (2 BIS docs, same publisher) |
| E19 | SR 11-7 model risk definition; effective challenge; validation independence | federalreserve.gov/boarddocs/SRLetters/2011/SR1107.pdf (sources/sr11-7.pdf) | regulator |
| E20 | EU AI Act Art.26 deployer duties; application dates 2027/2028 | artificialintelligenceact.eu/article/26/ + /implementation-timeline/ | secondary source of law text |
| E21 | NIST AI RMF voluntary trustworthiness framework | nist.gov/itl/ai-risk-management-framework | standards body |
| E22 | Plain-writing audience standard | digital.gov/guides/plain-language | official (US) |
| E23 | OpenLineage job/run/dataset model; Spark/dbt integrations | openlineage.io/docs/ | open standard docs |
| E24 | Apache Atlas governance framework (title only) | atlas.apache.org | official site (title-only) |

## 8. Could not verify / not claimed

- Exact current DBU list prices (page renders rates after region choice; and the bank's contract governs).
- Databricks billable-usage system-tables doc page (URL moved; page 404 in current docs layout) — the DBU
  mechanism is sourced from the Azure pricing page instead; column-level detail NOT verified.
- OpenAI enterprise privacy page (403). EBA/BoE "AI in banking" survey pages (404/302-to-404 during the
  fetch window). Internet Archive offline (PDF fallbacks unavailable). See handoff.md for the full list.
- Whether the specific bank's jobs fall under BCBS 239, its model-risk policy scope, or high-risk AI
  classification: bank-only questions, listed in section 6.
- Anything about the bank's actual environment (invented data is forbidden by the task).

End: 2026-10-17T19:49:25+02:00
