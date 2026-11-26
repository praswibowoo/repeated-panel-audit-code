# Partial primary adjudication — coordinator review notes

Processed: 2026-11-26
Input: `duplicate_pair_human_adjudication_primary_simple.xlsx`
Completed: **31 of 56** primary pairs. Remaining: **25**.

## Relation counts

- `same`: 19
- `different`: 5
- `undecidable`: 7

Against the deposited matrix:

- match: 15
- mismatch: 9
- undecidable: 7

## Priority rechecks

### Prior human evidence conflicts

Primary coder marked `same`, but prior P1 human-verified cell corrections make the matrix pair different:

- `B065_250_251`
- `B069_260_263`
- `B069_263_262`
- `B092_355_356`
- `B092_356_357`

Recheck the specific disputed parameter in each source paper. Current evidence lists only common parameters and does not resolve the conflict.

### Matrix-identical pairs marked `different`

These would change configuration counts if confirmed:

- `B036_184_187`
- `B107_396_395`

The current correction notes concern station/time aggregation, not an explicit parameter-suite difference. `relation` compares parameter suites, not spatial/temporal aggregation. Specify the exact differing parameter or reconsider the label.

### Matrix-distinct pairs marked `same`

Potential false-distinct pairs:

- `B065_250_251`
- `B069_260_263`
- `B069_263_262`
- `B080_298_299`
- `B080_300_299`
- `B092_355_356`
- `B092_356_357`

The B080 evidence should explain why the matrix differences do not represent real parameter-suite differences.

### Missing or inadequate evidence

Evidence is blank or not source-specific for:

- `B031_160_157`
- `B050_211_212`
- `B076_283_282`
- `B083_302_301`
- `B102_376_377`

### Likely copied evidence

`B063_243_244` uses the B062 parameter list. B063 Tables 1–2 and 8–9 instead concern pH, TDS, EC, oil/grease, metals and microbial panels. Replace the evidence text.

### Correction entries that are notes, not cell corrections

These entries do not specify `row; parameter; current -> new` and must not be applied as matrix corrections:

- `B031_160_157`
- `B034_177_181`
- `B034_183_181`
- `B036_184_187`
- `B050_211_212`
- `B090_344_342`
- `B097_366_368`
- `B107_396_395`

Move scenario/aggregation comments into `evidence`. Use `correction` only for an exact binary-cell change.

## Metadata

- `coder` and `date` are blank for all 31 completed rows.
- Fill both before final import.

## Status

No labels have been approved. No matrix cells or manuscript estimates were changed.
