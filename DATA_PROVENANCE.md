# Data provenance — final manuscript map

Manuscript: **Control-unit mismatch in leave-one-study-out audits of repeated binary coverage rows**

Release: `v1.7.0-2026-11-25`.

The manuscript has three main tables, one main figure, and SI Tables S1–S6. This file maps each item to the code and deposited outputs in this repository.

## Main manuscript

| Item | Content | Primary scripts / files |
|---|---|---|
| Table 1 | Corpus and configuration structure | `code/verify_package.py`, `data/coverage_matrix.csv`, `data/corpus_manifest.csv` |
| Table 2 | Fixed-set control-geometry and protocol contrasts | `code/unit_revision_fixed.py`, `results/unit_revision_fixed/common_contrast.json` |
| Table 3 | Target-dependent reporting protocol | Derived from Table 2 and SI Tables S2–S5; no separate analysis |
| Fig. 1 | Full-fit A versus Bblock control geometry | `code/make_fig_paired_contrast.py`, `results/unit_revision_fixed/common_contrast.json` |

## Supplementary information

| SI item | Content | Primary scripts / files |
|---|---|---|
| S1 | Corpus construction and verification | `docs/prisma_log.csv`, `docs/screening/`, `docs/verification/`, `data/corpus_manifest.csv` |
| S2 | Fixed designs, paired contrasts, and donor availability | `code/unit_revision_fixed.py`, `results/unit_revision_fixed/common_contrast.json` |
| S3 | Control-balance diagnostics | `code/control_balance_fixed.py`, `code/balance_diagnostics.py`, `results/unit_revision_fixed/control_balance.json` |
| S4 | Fixed-set synthetic benchmarks | `code/simulation_fixed.py`, `results/post_audit/simulation_fixed.json` |
| S5 | Fixed PCoA/RMS and labeled own-row sensitivities | `code/pcoa_fixed.py`, `code/rms_fixed_sensitivity.py`, `code/ca_sensitivity.py`, `code/water_only_check.py`, `code/dimension_sweep.py`, `code/procrustes_holdout.py`, `code/revision/hamming_audit.py` |
| S6 | Fixed corpus sensitivities | `code/unit_revision_fixed.py --exclude ...`, `results/unit_revision_fixed/sensitivity_no_B208.json`, `results/unit_revision_fixed/sensitivity_no_unsure_substitutes.json` |

## Core reported values

- Curated corpus: 117 papers, 716 rows, 151 within-study configurations, 136 distinct patterns, 565 repeated rows (78.9%).
- Fixed PCA A−Bblock, 112: 0.26 (0.22–0.32), 90% positive.
- Fixed PCA single A−Bblock, 92: 0.27 (0.22–0.36), 89% positive.
- Fixed PCA multi A−Bblock, 20: 0.23 (0.13–0.28), 95% positive.
- Fixed PCA A−C, 117: 0.29 (0.19–0.35).
- Fixed PCoA A−Bblock, 112: 0.29 (0.23–0.34), 96% positive.
- Fixed RMS A−Bblock, 112: 0.29 (0.23–0.38), 90% positive.
- Fixed synthetic repeated-configuration benchmark: A 1.557 (1.283–1.813), C 0.979 (0.909–1.089).
- Fixed synthetic independent-row benchmark: A 0.989 (0.887–1.086), C 0.981 (0.876–1.093).

## Audit frames

- `data/cell_level_sample.csv`, `data/cell_level_coded.csv`, `data/cell_level_triage.csv`: targeted 351-cell audit.
- `data/duplicate_pair_audit_frame.csv`: frozen 100-pair duplicate-classification frame; independent human adjudication pending.

The numeric water-quality value layer is restricted and not included. The binary coverage matrices are sufficient for the reported ordination analyses.
