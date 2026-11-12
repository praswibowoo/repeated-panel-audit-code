# AI Screener Provenance — ROUND 2 (R8b/D23, protocol v1.5)

> **SEALED UNTIL SCREENER A RETURNS.** Do not open/relay before pilot_blind_A.csv completed.

| Field | Value |
|---|---|
| Role | Screener B, pilot ROUND 2 (50 titles, seed 43, round-1 excluded, D25/D26 amendments) |
| Agent sessions | main 47 rows: ses_f18cf9bf1ffeoHJB3fqpGir1Lx · supplement 3 rows: ses_f188a329effedZM4gLAdSBS0a2 |
| Agent | OpenCode subagent `general` (LLM: MiMo-V2.6-Flash via opencode-go) |
| Date | 2026-09-28 |
| Inputs permitted | ai_screening_prompt.md (criteria v1.0) + pilot_blind_B.csv only |
| Prompt hash | sha256:ca858b42bb628e47440943cd92a1e633e3f11a33c216fd01af7750f014f4a1aa |
| Output hash (final) | sha256:b86dfa06674c3f614876b83724cdacdf55beb0e5e475ca62f7506fc2bbfaeb32 |
| Integrity (final) | 50 rows; input cols byte-identical A==B; 0 illegal values; 0 blanks |
| D25 swap chain | 3 preprints dropped (P001/P013/P025) -> P051-P053 (leaked to chat) -> swapped -> **P054-P056 silent-screened (status-only report, no leak)** |
| Final distribution | {'INCLUDE': 37, 'EXCLUDE': 10, 'UNSURE': 3} |
| Notes | ecotoxicology year exemption applied; NO-DOI articles kept (D26); year-floor uses R1 + note (frozen criteria gap — adjudication item) |
| Gate | human–AI concordance >90% raw on n=50; disagreements → mandatory human adjudication |
| Human anchor | C. Sillberg blind 10% (5 rows) pending post-A |
| Disclosure | Methods limitation + Elsevier AI-use declaration at submission |
