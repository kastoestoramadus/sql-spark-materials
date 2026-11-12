# Task 220 Part 3: skill set design for a SQL/Spark AI reviewer (bank engagement)

## Skill-format research summary (sources fetched 2026-10-18)

- Anthropic Agent Skills (https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills):
  "a skill is a directory that contains a SKILL.md file. This file must start with YAML frontmatter that contains
  some required metadata: name and description"; "the agent pre-loads the name and description of every installed
  skill"; progressive disclosure "provides just enough information ... without loading all of it into context";
  split big skills into referenced files.
- OpenAI/Codex skills (https://learn.chatgpt.com/docs/build-skills, redirect from developers.openai.com/codex/skills):
  "A skill is a directory with a SKILL.md file plus optional scripts and references"; "description: Explain exactly
  when this skill should and should not trigger"; the skill list "uses at most 2% of the model's context window,
  or 8,000 characters"; "Prefer instructions over scripts unless you need deterministic behavior or external
  tooling."
- Consequence applied here: same SKILL.md shape works for both ecosystems; descriptions name positive AND negative
  triggers; deterministic behavior (parsing, plan digesting, metric summaries) goes into scripts exactly because
  "you need deterministic behavior"; prose carries only the judgement layer.

## The proposed skill set (drafts in drafts/, DRAFT status)

| # | skill | deterministic part (script) | model-reasoning part | evidence it targets |
|---|---|---|---|---|
| 1 | sql-pitfall-lint | parse in pinned dialect, 8 pitfall checks | confirm intent per HIGH finding | fired q01/q02/q03/q04 (run 2026-10-18) |
| 2 | spark-plan-review | compact_plan.py digest + WARN + UNKNOWN lists | read plan, compare layers, quote evidence | 13/13 fixture checks; q01/q02/q07/q12 found via plan |
| 3 | spark-skew-check | eventlog_summary.py per-stage stats + SKEW flag | map flagged stage to join key, decide fix | stage 7 ratio 17.1 on planted skew |
| 4 | sql-review-report | report skeleton + redaction regex (draft) | wording, severity, uncertainty split | F15/F24 (unmeasured claims, leakage) |

Order of first build: 1 -> 2 -> 3 -> 4. Rationale: lint is the cheapest and gates everything (parse errors end
reviews cleanly); the plan digest carries the largest measured gain (plan-only findings q01/q07/q12); skew needs
logs the bank must export anyway; the report writer is convention, not detection.

## What runs deterministically vs what stays with the model

Deterministic (scripts): parsing + dialect pinning; pitfall pattern list; EXPLAIN capture and compaction with
explicit elision markers; event-log statistics; before/after metric diff; redaction. Model-only: intent
judgement (was INNER meant?), domain calls (does NULL case matter?), physical-design advice (needs sizes and
config), writing. Rule drawn from the experiment: whenever a textual artifact contains the fact (CartesianProduct,
Inner-conversion, SinglePartition, 200-partition Exchange), the script surfaces it and the model quotes it; when
the fact is not in any text (skew, data formats), the model must say "cannot know from these artifacts" instead
of guessing - q06 showed models tempted to advise broadcast without knowing the config.

## Testing on the series benchmark

The 12 cases in artifacts/ (10 defects + 2 controls, answer key separate) are the seed benchmark: every skill
change re-runs (a) lint over all 12 sql files - expected findings q01,q02,q03,q04 and silence on q07,q10;
(b) compact over all explain files - expected WARNs with the known noise (200-partition WARN fires without size
context); (c) eventlog_summary on artifacts/eventlog - expected SKEW on stage 7. A skill release that changes
these outputs needs a reason in its commit. Growing the set: every real review adds a case (query + defect +
which artifact revealed it), controls included - the false-positive rate (controls q09/q11 stayed clean) is part
of the score, not a footnote.

## Bank constraints honored

- Windows + Docker, no WSL: all scripts are pure-Python (sqlglot wheel) or pyspark (run in a container);
  nothing Linux-only, no bashisms; paths given as arguments.
- Models: Opus / Sonnet / GPT - skill bodies are model-agnostic instructions; no provider-specific features.
- On-prem or cloud: plan/event-log pipeline identical; only the export path for logs differs (marked in the
  skew skill).
- Privacy: query text and logs stay on the machine; redaction draft gates anything outbound (owner approves).

## Final skills are NOT written here

These are DRAFTS by task instruction; stronger models write and review the final versions.
