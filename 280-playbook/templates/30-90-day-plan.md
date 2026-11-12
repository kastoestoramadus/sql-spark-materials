# First 30 / 90 days — engagement plan (template)

The 30/90 split and the ordering below are practitioner convention [folklore, not sourced]; each step's
content is anchored to the evidence in `../report.md`. Adjust to what the bank's change calendar allows.

## Days 1–30: see, measure, agree

Goal: a defensible top-10 expensive jobs list, one agreed quick win, and written ground rules.

1. Access + platform facts + governance facts (first-week checklist sections 1–4).
2. Build the top-10 expensive jobs list:
   - cloud: billing export / system tables per-job DBUs or instance-hours (AWS CUR is tag-breakdown
     capable; Databricks bills by DBU) 
   - on-prem: YARN REST `/ws/v1/cluster/apps` → memorySeconds/vcoreSeconds share of cluster cost
3. For each of the top 10, record: owner, frequency, business purpose, runtime, cost/run (savings sheet A).
4. First findings pass with the observation checklist (findings table), prioritised by
   saving x confidence / (effort x risk).
5. Pick ONE quick win that is config-only and result-neutral; get it into the change pipeline.
6. Agree the working agreement: cadence, review board, definition of realised savings with finance,
   AI-tool usage rules within the bank's policy.

Exit criteria: top-10 list accepted by platform owner; quick win in change control; savings definition
signed by finance; findings table has >= 10 evidenced rows.

## Days 31–90: fix, prove, embed

1. Land the quick win; measure before/after (runtime, resource, output checks); record realised saving.
2. Roll the next findings through the bank's change control; keep result-neutrality evidence per change.
3. Where AI assistants analyse bank data, apply the privacy guardrails from report.md section 4:
   approved endpoints only, minimal/synthesised samples, no personal or trade data in prompts unless the
   bank's policy explicitly allows it; keep the analysis trail auditable (inputs, outputs, decisions).
4. Leave-behinds so the work continues without you:
   - top-N dashboard or query (billing/system tables or YARN REST) refreshed on a schedule
   - this findings table + savings sheet kept live by a named owner
   - a one-page "how we run reviews" for the platform team (adapted from report.md section 2)
   - optional: lineage coverage proposal if regulators' expectations apply (OpenLineage/Atlas evaluation)
5. 90-day report: executive summary + realised vs estimated savings + next-quarter backlog.

Exit criteria: >= 2 measured savings realised and signed; dashboard live; backlog handed over; final
executive summary delivered.
