# Data provenance — manuscript map

**Manuscript:** *Deletion-unit choice in leave-one-study-out audits of repeated binary coverage rows*

**Release:** `v1.9.2-2026-11-28`

The manuscript has three main tables, one main figure, and SI Tables S1–S6. This file maps each item to the code and deposited outputs in this repository.

## Main manuscript

| Item | Content | Primary scripts / files |
|---|---|---|
| Table 1 | Corpus and matrix-defined configuration structure | `code/verify_package.py`, `data/coverage_matrix.csv`, `data/corpus_manifest.csv` |
| Table 2 | Primary whole-study control, secondary configuration-donor control, and protocol contrasts | `code/unit_revision_fixed.py`, `results/unit_revision_fixed/common_contrast.json` |
| Table 3 | Two-axis reporting protocol: fit weighting versus control benchmark | Derived from Table 2 and SI Tables S2–S5 |
| Fig. 1 | Full-fit A versus Bstudy for 92 eligible single-configuration studies, with block-size strata | `code/make_fig_paired_contrast.py`, `results/unit_revision_fixed/common_contrast.json` |

## Supplementary information

| SI item | Content | Primary scripts / files |
|---|---|---|
| S1 | Corpus construction, verification, and approved priority-pair adjudication | `docs/prisma_log.csv`, `docs/screening/`, `docs/verification/`, `data/duplicate_pair_audit_frame.csv` |
| S2 | Fixed designs, median-ratio contrasts, donor availability, and two-level sensitivity | `code/unit_revision_fixed.py`, `results/unit_revision_fixed/common_contrast.json` |
| S3 | Bstudy/Bblock balance, donor composition, density gaps, and H implementation status | `code/control_balance_fixed.py`, `code/unit_revision_fixed.py`, `results/unit_revision_fixed/control_balance.json`, `results/unit_revision_fixed/common_contrast.json` |
| S4 | Fixed-set synthetic benchmarks including Bblock | `code/simulation_fixed.py`, `results/post_audit/simulation_fixed.json` |
| S5 | Fixed 3-D PCA, PCoA/RMS, and labeled own-row sensitivities | `code/fixed3d_sensitivity.py`, `code/pcoa_fixed.py`, `code/rms_fixed_sensitivity.py`, `code/ca_sensitivity.py`, `code/water_only_check.py`, `code/dimension_sweep.py`, `code/procrustes_holdout.py`, `code/revision/hamming_audit.py` |
| S6 | Fixed corpus sensitivities | `results/unit_revision_fixed/sensitivity_no_B208.json`, `results/unit_revision_fixed/sensitivity_no_unsure_substitutes.json` |

## Core reported values

- Curated corpus: 117 papers, 716 rows, 145 matrix-defined within-study configurations, 131 distinct patterns; 571 repeated rows.
- Primary fixed PCA A−Bstudy, 92 single-configuration studies: 0.17 (0.07–0.37), 79% positive.
- Secondary fixed PCA A−Bblock, 93 single-configuration studies: 0.23 (0.14–0.33), 82% positive.
- Fixed PCA A−C, 117: 0.28 (0.19–0.39).
- Canonical A−B and A−C contrasts are differences of per-study median ratios. The log-ratio is a separate control-only sensitivity.
- Fixed 3-D PCA A−Bstudy, 92: 0.06 (0.02–0.18), 62% positive.
- Duplicate-pair adjudication: 56 priority pairs resolved (53 same, three undecidable); 42 approved cell corrections applied. The 27 nonprimary pairs remain without approved coordinator adjudication.

## Audit frames

- `data/cell_level_sample.csv`, `data/cell_level_coded.csv`, `data/cell_level_triage.csv`: targeted 351-cell audit.
- `data/duplicate_pair_audit_frame.csv`: frozen 100 records representing 83 unique unordered pairs; 56 priority pairs have author-approved coordinator resolutions.
- `data/duplicate_pair_source_review.csv`: independent AI-assisted blinded source-review labels; not human adjudication.
- `data/duplicate_pair_source_review_summary.json`: source-review counts and post-correction matrix comparison.
- `data/prior_human_cell_corrections.csv`: 13 historical P1 human corrections; four are superseded by the approved 2026-11-27 review.
- `data/prior_human_pair_evidence.csv`: prior correction mapping with post-correction values and resolution status.
- `data/duplicate_pair_human_adjudication_coder.xlsx`: blind primary/secondary coding workbook.
- `data/duplicate_pair_human_adjudication_coordinator.xlsx`: coordinator key and prior-evidence workbook.

The numeric water-quality value layer is restricted and is not included. All binary coverage matrices and code needed for the reported checks are present.
