# Proposed coordinator resolution — source-review memo

Date: 2026-11-27
Scope: all 56 primary duplicate pairs
Status: **proposed only; no human approval and no matrix changes**

## Proposed relations

- `same`: 53
- `different`: 0
- `undecidable`: 3

The three unresolved pairs are:

- `B057_236_238` — row 238 is not delimited as an independent sampled scenario or parameter suite.
- `B186_615_617` — 20-cm and 60-cm are cultivation treatments, but water quality is reported only as one pond-wide range without depth-specific assignment.
- `B221_697_695` — no Cd-only water-chemistry panel is reported; chemistry is available only for control and combined Cd+PE-MP.

## Changes from the primary submission

19 primary labels would change:

### `different -> same` — 7

- `B034_177_181`
- `B034_183_181`
- `B036_184_187`
- `B090_344_342`
- `B107_396_395`
- `B190_633_636`
- `B200_654_652`

### `undecidable -> same` — 12

- `B031_160_157`
- `B050_211_212`
- `B076_283_282`
- `B083_302_301`
- `B097_366_368`
- `B102_376_377`
- `B125_440_443`
- `B166_579_580`
- `B169_592_594`
- `B191_642_641`
- `B222_700_701`
- `B222_702_699`

All 19 changed labels were independently rechecked without access to the matrix or prior labels. The blinded audit agreed with all 19 proposed relations.

## Cell-correction candidates

The proposal contains **42 unique binary-cell corrections**. Every candidate has `coordinator_approval = pending`.

After applying these corrections in memory:

- all 53 proposed `same` pairs become matrix-identical;
- the three `undecidable` pairs remain unresolved by design;
- no proposed `same` pair retains a nonzero Hamming distance.

The exact candidates are in:

`duplicate_pair_proposed_cell_corrections_2026-11-27.csv`

## Conflicts with prior accepted human corrections

Four proposed cell changes conflict with earlier accepted P1 human corrections and require explicit approval:

| Paper | Row | Parameter | Current | Proposed | Basis |
|---|---:|---|---:|---:|---|
| B034 | 181 | pH | 0 | 1 | Methods report in-situ pH measurement; Results report pH 7.6–8.8 in both lagoons. |
| B065 | 251 | NO2 (mg/L) | 0 | 1 | Nitrite was examined at Group-B stations GX03 and GX12. |
| B069 | 263 | pH | 0 | 1 | pH is explicitly examined in the common four-station design. |
| B166 | 580 | TSS (mg/L) | 0 | 1 | TSS is explicitly analyzed in the common MN/MB piezometer design. |

These proposals follow the coding rule that examined or examined-absent = `1`, while not reported = `0`. They must not be applied automatically.

## Unresolved cell-level ambiguity

`B200_654_652` is proposed `same` because both seasons belong to the same monitoring design. However, nitrate remains unresolved for rows 652 and 654: the abstract/introduction mention nitrate, while Methods/Results emphasize nitrite, phosphate, and silicate. No NO3 correction is proposed.

## Provisional configuration impact

If all 42 corrections are approved, the in-memory configuration count changes from **151 to 145** across 15 papers. Some papers lose duplicate configurations; others gain configurations because newly recognized parameters separate previously identical rows.

See:

`duplicate_pair_configuration_impact_proposed_2026-11-27.csv`

This is a provisional impact calculation only. No matrix, analysis output, manuscript value, or SI value has been changed.

## Files

- `duplicate_pair_coordinator_source_review_2026-11-27.csv` — 56 source-review rows.
- `duplicate_pair_coordinator_blind_audit_2026-11-27.csv` — 19 blinded rechecks of changed labels.
- `duplicate_pair_coordinator_resolution_proposed_2026-11-27.csv` — proposed resolutions with evidence and flags.
- `duplicate_pair_proposed_cell_corrections_2026-11-27.csv` — 42 pending cell corrections.
- `duplicate_pair_configuration_impact_proposed_2026-11-27.csv` — provisional configuration-count impact.

## Required approval sequence

1. Coordinator reviews the 19 changed labels and three unresolved pairs.
2. Coordinator explicitly approves or rejects the four prior-correction conflicts.
3. Coordinator marks each of the 42 cell corrections as approved or rejected.
4. Only approved corrections are applied to a controlled matrix copy.
5. Rerun duplicate-pair checks, fixed analyses, package verification, and manuscript/SI consistency checks if configuration counts change.

Until those steps are complete, the proposed resolution file must not be treated as final human adjudication.
