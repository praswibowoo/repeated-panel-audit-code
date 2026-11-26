# Primary adjudication processing — coordinator notes

Processed: 2026-11-27
Input: `duplicate_pair_human_adjudication_primary_simple.xlsx`
Submission rows: **56**
Completed relation labels: **55 / 56**
Pending relation label: **1**

## Relation counts

- `same`: 34
- `different`: 6
- `undecidable`: 15

Against the deposited matrix:

- match: 25
- mismatch: 15
- undecidable: 15

All 55 labels remain provisional primary-only labels. None are finalized.

## Blocking submission issues

### Missing relation and evidence

- `B200_654_652` — `Post-monsoon` vs `Pre-monsoon`: `relation`, `evidence`, and `correction` are blank.

Source check: B200 reports both seasons within the same water/phytoplankton monitoring programme (Results, pp. 491–493). The coder must still enter the relation and source evidence; no label was assigned automatically.

### Missing coder/date

- `B001_7_0` — `coder` and `date` are blank.

### Missing evidence among completed labels

- `B031_160_157`
- `B050_211_212`
- `B076_283_282`
- `B083_302_301`
- `B102_376_377`
- `B221_697_695`
- `B222_700_701`
- `B222_702_699`

For `undecidable` rows, state the specific source limitation. A blank evidence cell is not sufficient.

### Likely copied evidence

- `B063_243_244` — current evidence lists the B062 water-quality panel. B063 Tables 1–2 and 8–9 instead report THB, total coliforms, pH, TDS, EC, oil/grease, Ni, Cd, Cr, Co, Cu, Pb, Zn, Fe, and As. Replace the evidence and reconfirm the relation.

## Priority coordinator rechecks

### Prior human evidence conflicts

Primary coder marked `same`, but accepted P1 human corrections make the deposited matrix pair different:

- `B065_250_251` — NO2
- `B069_260_263` — pH
- `B069_263_262` — pH
- `B092_355_356` — Secchi vs brightness
- `B092_356_357` — Secchi vs brightness

Current evidence lists common parameters only. Resolve the specific disputed parameter before approval.

Also recheck `B166_579_580`: the primary label is `undecidable`, but the pair has an accepted prior human TSS correction for row 580.

### Matrix-identical pairs marked `different`

- `B036_184_187`
- `B107_396_395`
- `B190_633_636`

These would change configuration counts if confirmed. Current evidence/correction text does not identify an exact parameter-suite difference. Station/time aggregation alone does not establish `different`.

### Matrix-distinct pairs marked `same`

- `B065_250_251`
- `B069_260_263`
- `B069_263_262`
- `B080_298_299`
- `B080_300_299`
- `B092_355_356`
- `B092_356_357`
- `B153_536_537`
- `B153_537_538`
- `B153_537_539`
- `B153_538_536`
- `B153_539_538`

The processing report lists the exact matrix parameters that differ. Explain why each difference is not a real examined-parameter difference, or revise the relation.

### Matrix-distinct pairs marked `different`

- `B034_177_181` — pH
- `B034_183_181` — pH
- `B090_344_342` — NH4

These agree with the matrix class but disagree with the automated source review. Confirm the parameter-level difference from the source.

### Automated source-review disagreements

18 completed primary labels differ from the automated source-review label:

- `B031_160_157`
- `B034_177_181`
- `B034_183_181`
- `B036_184_187`
- `B050_211_212`
- `B076_283_282`
- `B083_302_301`
- `B090_344_342`
- `B097_366_368`
- `B102_376_377`
- `B107_396_395`
- `B125_440_443`
- `B166_579_580`
- `B169_592_594`
- `B190_633_636`
- `B191_642_641`
- `B222_700_701`
- `B222_702_699`

The automated label is not human evidence and does not override the primary coder.

## Correction entries that are notes, not matrix-cell corrections

These 16 entries do not specify `row; parameter; current value -> new value` and must not be applied as matrix corrections:

- `B031_160_157`
- `B034_177_181`
- `B034_183_181`
- `B036_184_187`
- `B050_211_212`
- `B090_344_342`
- `B097_366_368`
- `B107_396_395`
- `B125_440_443`
- `B144_520_513`
- `B153_536_537`
- `B153_537_538`
- `B153_537_539`
- `B153_538_536`
- `B153_539_538`
- `B169_592_594`

Move scenario/aggregation comments into `evidence`. Use `correction` only for an exact binary-cell change.

## Processing status

- `coordinator_review`: 25
- `incomplete_submission`: 9
- `incomplete_relation`: 1
- `provisional_no_flag`: 21

`provisional_no_flag` means no row-specific automated/manual flag was found; it does not mean approved.

## Saved outputs

- `duplicate_pair_human_adjudication_primary_completed_2026-11-27.csv`
- `duplicate_pair_human_adjudication_results_2026-11-27.csv`
- `duplicate_pair_human_adjudication_summary_2026-11-27.json`
- `duplicate_pair_human_adjudication_processing_report_2026-11-27.csv`
- `duplicate_pair_human_adjudication_review_flags_2026-11-27.csv`
- `duplicate_pair_coordinator_resolution_template_2026-11-27.csv`

## Status

No labels have been approved. No coverage-matrix cells, configuration counts, manuscript estimates, or SI values were changed. Final strict import is blocked until `B200_654_652`, `B001_7_0`, and the eight missing-evidence rows are completed.
