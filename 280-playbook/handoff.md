# handoff.md — task 280

## Done

- All deliverables in /home/walidus/hocon-fmt-analysis-2026-10-11/work/idle/queue/results/280-sql-spark-consulting-playbook/:
  - report.md — playbook with 24-row evidence table (report §7), every claim URL + fetch date 2026-10-17 +
    verbatim quote; folklore labelled; on-prem and cloud covered.
  - decision.md — retro-prep format (question, evidence D1–D8, options A/B/C, recommendation + confidence).
  - templates/first-week-checklist.md, templates/findings-table.md, templates/savings-estimate-sheet.md,
    templates/executive-summary-onepage.md, templates/30-90-day-plan.md.
  - sources/ — local copies: bcbs239.pdf + bcbs239.txt, sr11-7.pdf + sr11-7.txt, nist800-128.pdf + .txt,
    sr11-7.htm (Fed 404-page artefact, ignorable).
- No repository writes, no git worktree (task is pure research/writing), no venv needed (no Python tooling
  installed anywhere — task's Python rule did not trigger).

## Not done

- OpenAI enterprise-privacy quotes: openai.com/enterprise-privacy returned 403 (WebFetch and webReader).
  Alternative checked: learn.microsoft.com Foundry/Azure-OpenAI data-privacy page (fetched, quoted) — covers
  the OpenAI models only as sold via Azure. Direct OpenAI terms unverified.
- EBA / Bank of England "AI in financial services" survey pages: probed URL variants, all 404/302→404 in
  this fetch window; Bing/DDG/Mojeek search blocked by captcha, Internet Archive "Temporarily Offline".
  EU regulatory grounding therefore rests on the AI Act pages + SR 11-7 + BCBS 239 + NIST.
- Databricks billable-usage system-tables documentation: current docs layout 404s the historical URLs
  (301 → /aws/en/admin/system-tables/billable-usage → 404). Covered mechanism via the Azure pricing page;
  column-level detail unverified.
- Exact DBU list prices: Azure pricing page renders "$-" until a region is selected; only structural quotes
  extracted (DBU counts, Photon 2.9X, 37% pre-purchase).
- async-profiler / other Linux-only profilers' Windows compatibility: NOT checked (no fetch); flagged in
  report §3.1 as "verify before recommending" rather than asserted.
- Apache Atlas: site returned only the page title; cited title-only (report E24 labels it).
- report.md End timestamp: set from `date` at finish (see Verification); if the orchestrator reopens the
  task, trust commands.log times.

## Proposals needing a decision

None risky was done. One low-risk proposal for the owner (not executed): before day one, run at home
`docker pull apache/spark` and start a local history server in a container to rehearse; if the bank lacks a
Hyper-V-backed all-users Docker install, propose to the bank's admins (their decision, likely a ticket):
"Docker Desktop all-users installation with Hyper-V backend for the consultant's workstation" — risk: admin
approval latency; recommendation: raise it in the first call, it is the likeliest day-1 blocker.

## Ready-made texts

- templates/executive-summary-onepage.md doubles as the client-facing summary skeleton.
- Question list for the bank's first call: report.md §6 (items 1–10) can be pasted verbatim into an email.

## Verification

- Research-depth falsification (logged in progress.md):
  1. AQE default since 3.2.0 — attempted falsification via migration guide: HELD ("In Spark 3.2,
     spark.sql.adaptive.enabled is enabled by default.").
  2. Docker without WSL possible on Hyper-V backend — second source (Microsoft Learn Hyper-V overview)
     HELD, with the all-users-install caveat now documented (this nuance WEAKENED the simple claim).
  3. BCBS 239 quotes — second source is the same publisher (BIS landing page + PDF): labelled, not
     independently falsified.
  4. SR 11-7 framing — cross-checked against NIST AI RMF page (different authority, voluntary framework):
     complementary, HELD as framing, not as an EU obligation.
  5. FinOps phases — second page same publisher: labelled; AWS Well-Architected pillar used as the
     different-publisher sanity check for the cost-practice claims.
- Files checked present: report.md, decision.md, templates/ (5 files), sources/ (7 files), progress.md,
  checkpoint.md, commands.log, finished (created last).
- Commands longer than 60 s or failing: in commands.log (BIS redirect, Fed 404s, captchas, 403s, 12.7 MB
  Azure pricing fetch).

## Unverified

- Not searched (search engines blocked this run: DDG/Bing poor, Mojeek captcha, Archive offline): EBA
  follow-up reports on BCBS 239 implementation; BoE/FCA AI survey; OpenAI help-center data-controls FAQ;
  Google Cloud / BigQuery cost models (only AWS+Azure covered); Databricks' current docs sitemap; Polish
  KNF guidance on AI usage (may exist; not attempted in Polish sources); ITIL change-management primary
  source (NIST SP 800-128 used instead).
- Vendor claims (Photon 2.9X, 37% pre-purchase savings, Kryo "10x") are quoted as vendor/self-reported
  claims, not verified measurements.
- No prompt-injection attempts were found in fetched content.
