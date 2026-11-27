# Approved duplicate-pair correction application

Approval date: 2026-11-27
Approved by: user
Scope: all 42 proposed cell corrections

## Applied changes

- 42 binary cells updated across 15 papers.
- Updated files:
  - `data/coverage_matrix.csv`
  - `data/coverage_matrix_all_paper.csv`
  - `data/coverage_matrix_full_extraction.csv`
  - `docs/extraction/stageA/matrix_presence_v2.csv`
- Matrix density (`rho`) refreshed in all three matrices.
- Curated/all-paper invariant verified.
- Curated configuration count changed from **151 to 145**.
- Single-configuration papers changed from 97 to 98.

## Approved pair resolutions

- 56 unique priority pairs resolved.
- `same`: 53
- `different`: 0
- `undecidable`: 3
- All 53 `same` pairs are matrix-identical after correction.
- The audit frame now contains 61 resolved records representing those 56 unique pairs.

## Prior corrections

Four prior accepted human corrections were explicitly superseded by the user-approved review:

- B034 row 181 pH: `0 -> 1`
- B065 row 251 NO2: `0 -> 1`
- B069 row 263 pH: `0 -> 1`
- B166 row 580 TSS: `0 -> 1`

Their status is recorded in `prior_human_cell_corrections_status.csv` and `prior_human_pair_evidence.csv`.

## Residual issues

- `B200_654_652`: relation resolved `same`; nitrate presence remains unresolved between 0 and 1 because the source abstract/introduction and Methods/Results differ.
- `B222_702_700`: approved DO/temperature corrections make this QC pair matrix-identical, while the earlier automated source review labeled it `different`. The pair is outside the 56-pair primary resolution set and remains flagged as a residual matrix/review disagreement.

## Post-correction primary estimate

The fixed 2-D PCA rerun gives A$-$Bstudy = **0.17 (0.07--0.37)** across 92 eligible single-configuration studies, with 79\% positive. The single-configuration A$-$Bblock contrast is **0.20 (0.13--0.29)** across 93 studies. Fixed 3-D A$-$Bstudy is **0.06 (0.02--0.18)**; RMS A$-$Bstudy is **0.28 (0.19--0.51)**; Jaccard PCoA A$-$Bstudy is **0.27 (0.18--0.39)**.

## Downstream status

The full matrix-dependent analysis suite and manuscript/SI numerical refresh are complete. `verify_package.py` passes, the final LaTeX build is clean, and release `v1.9.0-2026-11-27` is prepared for tagging and push.
