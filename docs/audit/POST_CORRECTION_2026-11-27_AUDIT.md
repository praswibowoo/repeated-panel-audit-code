# Post-correction audit — 2026-11-27

Status: historical audit for release `v1.9.0-2026-11-27`; superseded by `v1.9.1-2026-11-28`. Secondary contrasts below use the earlier draw-level estimator.

## Approved correction application

- The corresponding author approved all 42 proposed binary-cell corrections.
- Applied to:
  - `data/coverage_matrix.csv`
  - `data/coverage_matrix_all_paper.csv`
  - `data/coverage_matrix_full_extraction.csv`
  - `docs/extraction/stageA/matrix_presence_v2.csv`
- Matrix density (`rho`) refreshed.
- Curated/all-paper invariant verified.
- Curated configurations: **151 -> 145**.
- Curated distinct patterns: **136 -> 131**.
- Single-configuration papers: **97 -> 98**.
- Non-first curated rows: **565 -> 571**.
- All-paper configurations: **150**.
- Full-extraction configurations: **167**.

## Approved duplicate-pair resolution

- 56 unique priority pairs resolved.
- `same`: 53.
- `different`: 0.
- `undecidable`: 3.
- All 53 `same` pairs are matrix-identical after correction.
- Residual nonprimary disagreement: `B222_702_700` is matrix-identical but was labeled `different` by the earlier automated review.
- `B200_654_652` nitrate presence remains unresolved; pair relation is `same`.

## Primary fixed 2-D PCA after correction

- Curated matrix: 117 papers, 716 rows, 145 configurations.
- Single-configuration studies: 98.
- Whole-study donor available for 92 single-configuration studies.
- A median: **1.35 (1.12--1.59)**.
- Bstudy median: **1.05 (0.82--1.17)**.
- A$-$Bstudy: **0.17 (0.07--0.37)**, **79% positive**.
- Configuration donor available for 93 single-configuration studies.
- A$-$Bblock, single: **0.20 (0.13--0.29)**, **85% positive**.
- A$-$C, all: **0.24 (0.14--0.40)**.
- A$-$C, single: **0.31 (0.20--0.43)**.
- A$-$C, multiple: **0.10 ($-$0.11--0.24)**.
- Fixed 3-D A$-$Bstudy: **0.06 (0.02--0.18)**, 62\% positive.
- Fixed RMS A$-$Bstudy: **0.28 (0.19--0.51)**, 83\% positive.
- Fixed Jaccard PCoA A$-$Bstudy: **0.27 (0.18--0.39)**, 85\% positive.
- Excluding B208: A$-$Bstudy **0.12 (0.09--0.37)**, $n=92$.
- Larger unsure/substitute exclusion: A$-$Bstudy **0.09 ($-$0.01--0.17)**, $n=79$.

## Verification completed

- Correction dry-run validated all 42 current values before application.
- Curated/all-paper/full-extraction/stage-A values agree for every corrected cell.
- Approved resolution/matrix agreement: 53 yes, 3 undecidable, 0 no.
- Frozen duplicate-pair frame: 100 records / 83 unique pairs / 56 approved unique resolutions.
- Coordinator workbook and prior-correction statuses refreshed.
- Primary figure regenerated and copied to the manuscript source tree.
- Final LaTeX build: clean (main 21 pages, SI 9 pages, title page 1 page).
- Current-matrix panel decomposition, core checks, rebuilt-event tail checks, permutation nulls, PCoA, RMS, 3-D, exclusions, synthetic, perturbation, coherence, three-set, and own-row sensitivity outputs refreshed.
- `verify_package.py`: PASS (114 files).
- Manuscript/value/matrix/figure consistency check: PASS for the then-current v1.9.0 package. A later audit found documentation and secondary-estimator drift corrected in v1.9.1.

## Release status

- Release: `v1.9.0-2026-11-27`.
- Manifest and checksums regenerated locally.
- Code and manuscript changes committed locally.
- Annotated tags and branch pushes authorized.
