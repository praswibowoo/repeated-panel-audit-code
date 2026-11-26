# Data provenance — manuscript map

**Manuscript:** *Control-unit dependence in leave-one-study-out audits of repeated binary coverage rows*

**Release:** `v1.8.0-2026-11-26`

The manuscript has three main tables, one main figure, and SI Tables S1–S6. This file maps each item to the code and deposited outputs in this repository.

## Main manuscript

| Item | Content | Primary scripts / files |
|---|---|---|
| Table 1 | Corpus and matrix-defined configuration structure | `code/verify_package.py`, `data/coverage_matrix.csv`, `data/corpus_manifest.csv` |
| Table 2 | Primary whole-study control, secondary configuration-donor control, and protocol contrasts | `code/unit_revision_fixed.py`, `results/unit_revision_fixed/common_contrast.json` |
| Table 3 | Two-axis reporting protocol: fit weighting versus control benchmark | Derived from Table 2 and SI Tables S2–S5 |
| Fig. 1 | Full-fit A versus Bstudy for 91 eligible single-configuration studies, with block-size strata | `code/make_fig_paired_contrast.py`, `results/unit_revision_fixed/common_contrast.json` |

## Supplementary information

| SI item | Content | Primary scripts / files |
|---|---|---|
| S1 | Corpus construction, verification, and provisional duplicate classification | `docs/prisma_log.csv`, `docs/screening/`, `docs/verification/`, `data/duplicate_pair_source_review.csv` |
| S2 | Fixed designs, paired contrasts, donor availability, and two-level sensitivity | `code/unit_revision_fixed.py`, `results/unit_revision_fixed/common_contrast.json` |
| S3 | Bstudy/Bblock balance, donor composition, and per-study density gaps | `code/control_balance_fixed.py`, `results/unit_revision_fixed/control_balance.json` |
| S4 | Fixed-set synthetic benchmarks including Bblock | `code/simulation_fixed.py`, `results/post_audit/simulation_fixed.json` |
| S5 | Fixed 3-D PCA, PCoA/RMS, and labeled own-row sensitivities | `code/fixed3d_sensitivity.py`, `code/pcoa_fixed.py`, `code/rms_fixed_sensitivity.py`, `code/ca_sensitivity.py`, `code/water_only_check.py`, `code/dimension_sweep.py`, `code/procrustes_holdout.py`, `code/revision/hamming_audit.py` |
| S6 | Fixed corpus sensitivities | `results/unit_revision_fixed/sensitivity_no_B208.json`, `results/unit_revision_fixed/sensitivity_no_unsure_substitutes.json` |

## Core reported values

- Curated corpus: 117 papers, 716 rows, 151 matrix-defined within-study configurations, 136 distinct patterns; 565 repeated rows.
- Primary fixed PCA A−Bstudy, 91 single-configuration studies: 0.35 (0.23–0.48), 89% positive.
- Secondary fixed PCA A−Bblock, 92 single-configuration studies: 0.27 (0.22–0.36), 89% positive.
- Fixed PCA A−C, 117: 0.29 (0.19–0.35).
- Fixed 3-D PCA A−Bstudy, 91: 0.14 (0.09–0.32), 73% positive.
- Duplicate-pair source review: 83 unique unordered pairs; 37/38 matrix-identical pairs reviewed same, one undecidable; 16/45 matrix-distinct pairs reviewed same. Human adjudication pending.

## Audit frames

- `data/cell_level_sample.csv`, `data/cell_level_coded.csv`, `data/cell_level_triage.csv`: targeted 351-cell audit.
- `data/duplicate_pair_audit_frame.csv`: frozen 100 records representing 83 unique unordered pairs; human adjudication pending.
- `data/duplicate_pair_source_review.csv`: independent AI-assisted blinded source-review labels; not human adjudication.
- `data/duplicate_pair_source_review_summary.json`: source-review counts and comparison with matrix classes.

The numeric water-quality value layer is restricted and is not included. All binary coverage matrices and code needed for the reported checks are present.
