# Eligibility-qualified primary corpus

## Definition

The primary corpus is the full 117-paper curated matrix after excluding papers with unresolved duplicate-pair adjudication, decidable blinded-primary/unblinded-coordinator disagreement, ambiguous scenario identity, unsure/substitute status, or the B149 one-row boundary exception.

The full curated matrix remains the sensitivity corpus. Multi-configuration papers remain in the primary background matrix, but the primary focal estimand is restricted to single-configuration paper blocks.

## Counts

| Quantity | Full curated | Primary |
|---|---:|---:|
| Papers | 117 | 87 |
| Scenario rows | 716 | 555 |
| Within-paper configurations | 145 | 93 |
| Single-configuration papers | 98 | 81 |
| Multi-configuration papers | 19 | 6 |
| Nominal parameter columns | 44 | 44 |
| Populated parameter columns | 42 | 42 |

Thirty papers are excluded from the full curated corpus. Reason counts overlap:

- 11 papers tied to 27 unresolved duplicate pairs.
- 6 papers with decidable primary/coordinator disagreements.
- 5 papers with ambiguous scenario identity.
- 15 unsure/substitute papers.
- B149 one-row boundary.

The exact list is in `data/primary_corpus_exclusions.csv`; machine-readable counts are in `data/primary_corpus_summary.json`.

## Coder concordance

The blinded primary coder and unblinded coordinator agreed on 37/56 priority pairs (66.1%; Cohen's κ = 0.17). Among 41 pairs where both gave a decidable same/different label, agreement was 82.9%; all seven disagreements were primary = different and coordinator = same. Only the primary coder was blinded, so these are concordance statistics, not independent inter-rater reliability. No completed human second-coder file is available.

Papers with decidable disagreements are excluded from the primary corpus.

## Correction impact

The 42 approved corrections changed the full-curated configuration count from 151 to 145 and changed single/multi status in 11 papers. Within current primary membership, 28 corrections across eight papers changed configurations from 96 to 93 and changed status in eight papers. Donor counts changed for 36 of 77 persistent primary single-configuration papers; B052 changed from one exact-size donor to zero. All current donor pools use the corrected matrix. Full and primary impacts are reported separately in `data/duplicate_pair_correction_impact_audit.json`.

## Scenario construct

An eligible scenario is a source-defined, separately labeled sampling or reporting unit in the source paper. Analyst-derived aggregates, re-slicings, pooled summaries, and management groupings do not qualify as separate scenarios. B028, B057, B186, B221, and B222 are excluded from the primary corpus for scenario-identity ambiguity.

B084 Cu is retained as 0 for the water-scenario rows: the source reports Cu in waterlogged-soil Table 2, not in the water table used for the B084 scenarios. The apparent cell-audit mismatch is annotated as scenario-inapplicable.

See `docs/scenario_coding_rules.md` for the rule and three source-verified repeated-row examples.

## Reproduction

```bash
python3 code/build_primary_corpus.py
```

The script reads the full curated matrix, approved duplicate-pair results, and corpus manifest, then writes the primary matrix, primary manifest, exclusion audit, and summary JSON.
