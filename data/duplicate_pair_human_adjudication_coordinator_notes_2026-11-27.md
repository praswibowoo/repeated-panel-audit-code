# Primary adjudication processing — coordinator notes

Processed: 2026-11-27
Input: `duplicate_pair_human_adjudication_primary_simple.xlsx`
Submission rows: **56**
Completed relation labels: **56 / 56**
Strict structural import: **PASS**

## Relation counts

- `same`: 34
- `different`: 7
- `undecidable`: 15

Against the deposited matrix:

- match: 25
- mismatch: 16
- undecidable: 15

All 56 labels remain provisional primary-only labels. None are finalized.

## Submission completeness

- No blank `relation` cells.
- No blank `evidence` cells.
- No blank `coder` or `date` cells.
- Coder: `A` throughout.
- Date: `2026-11-27` throughout.

Structural completeness does not establish evidentiary adequacy. The issues below still require coordinator review.

## Priority coordinator rechecks

### Likely copied evidence

- `B063_243_244` — current evidence lists the B062 water-quality panel. B063 Tables 1–2 and 8–9 instead report THB, total coliforms, pH, TDS, EC, oil/grease, Ni, Cd, Cr, Co, Cu, Pb, Zn, Fe, and As. Replace the evidence and reconfirm the relation.

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
- `B200_654_652`

These would change configuration counts if confirmed. Current evidence/correction text does not identify an exact parameter-suite difference.

For `B200_654_652`, the source describes post- and pre-monsoon monitoring within the same programme, but `P.4-6` alone does not identify a differing parameter. The coder/coordinator must specify the exact difference or reconsider the label.

Station/time aggregation alone does not establish `different`.

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

### Matrix-distinct pairs marked `different` without a documented decisive parameter

- `B034_177_181` — deposited matrix difference: pH
- `B034_183_181` — deposited matrix difference: pH
- `B090_344_342` — deposited matrix difference: NH4

These agree with the matrix class but disagree with the automated source review. State the exact parameter-level difference and source location.

### Undecidable labels without a stated reason

The following 13 rows give a parameter list or table/figure pointer but do not explain why the source cannot support `same` or `different`:

- `B057_236_238`
- `B076_283_282`
- `B083_302_301`
- `B097_366_368`
- `B102_376_377`
- `B125_440_443`
- `B166_579_580`
- `B169_592_594`
- `B186_615_617`
- `B191_642_641`
- `B221_697_695`
- `B222_700_701`
- `B222_702_699`

Add the decisive source limitation to `evidence`. Notes such as `No Table`, `For phytoplankton`, and `have 12 sample` do not by themselves explain the uncertainty.

### Same labels with vague evidence

- `B208_669_670` — `Table 1-2`
- `B213_681_683` — `P3 Table 2`
- `B214_684_687` — `P.11 Table 3-4`

Add the examined parameter suite; a table reference alone does not document why the configurations are the same.

### Automated source-review disagreements

19 completed primary labels differ from the automated source-review label:

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
- `B200_654_652`
- `B222_700_701`
- `B222_702_699`

The automated label is not human evidence and does not override the primary coder.

## Correction entries that are notes, not matrix-cell corrections

These 17 entries do not specify `row; parameter; current value -> new value; reason` and must not be applied as matrix corrections:

- `B031_160_157`
- `B034_177_181`
- `B034_183_181`
- `B036_184_187`
- `B050_211_212`
- `B076_283_282`
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

- `coordinator_review`: 39
- `provisional_no_flag`: 17
- `incomplete_submission`: 0
- `incomplete_relation`: 0

`provisional_no_flag` means no row-specific automated/manual flag was found; it does not mean approved.

## Saved outputs

- `duplicate_pair_human_adjudication_primary_completed_2026-11-27.csv`
- `duplicate_pair_human_adjudication_results_2026-11-27.csv`
- `duplicate_pair_human_adjudication_summary_2026-11-27.json`
- `duplicate_pair_human_adjudication_processing_report_2026-11-27.csv`
- `duplicate_pair_human_adjudication_review_flags_2026-11-27.csv`
- `duplicate_pair_coordinator_resolution_template_2026-11-27.csv`

## Status

Strict structural import passes because all required fields are populated. Coordinator resolution is still required for all 56 primary-only labels. No coverage-matrix cells, configuration counts, manuscript estimates, or SI values were changed.
