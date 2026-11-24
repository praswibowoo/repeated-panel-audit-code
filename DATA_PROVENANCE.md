# Data provenance — final manuscript map

Final manuscript version: 2026-11-24. The current manuscript uses **main Tables 1--4**, **Fig. 1**, and **SI Tables S1--S12**.

This file is the referee-facing provenance map. The earlier, long archival provenance log is preserved at `docs/archive/DATA_PROVENANCE_ARCHIVE.md`; where it differs from the current manuscript or SI, the manuscript/SI are authoritative.

## Manuscript items

| Item | Content | Primary scripts / files |
|---|---|---|
| Table 1 | Corpus and configuration structure | `code/verify_package.py`, `data/coverage_matrix.csv`, `data/corpus_manifest.csv` |
| Table 2 | Primary design set | `code/panel_decomposition.py`, `code/sharpening_checks.py`, `results/post_audit/panel_decomposition.json`, `data/sharpening_checks.json` |
| Table 3 | Sensitivity checks | `code/dimension_sweep.py`, `code/ca_sensitivity.py`, `code/water_only_check.py`, `code/leave_flagged_out.py`, `code/revision/hamming_audit.py` |
| Table 4 | Reporting protocol | Derived from Tables 2--3 and SI Table S11 |
| Fig. 1 | Paired design contrast | `code/make_fig_paired_delta.py`, `results/post_audit/panel_decomposition.json`, `data/sharpening_checks.json` |

## SI tables

| SI item | Content | Primary scripts / files |
|---|---|---|
| S1 | Corpus construction and verification | `docs/prisma_log.csv`, `docs/screening/`, `code/verify_package.py` |
| S2 | Misclassification and duplication diagnostics | `code/perturbation_upper.py`, `code/perturbation_clustered.py`, `data/row_count_sensitivity.csv`, `data/baseline_block.csv`, `data/baseline_matched.csv`, `data/p0_composition_percentile.csv` |
| S3 | Resampling-unit calibration | `data/sim_calibration_summary.csv`, `data/sim_calibration_extended_summary.csv` |
| S4 | Core audit and two-level inference | `code/panel_decomposition.py`, `code/two_level_delta.py`, `code/procrustes_holdout.py`, `data/core.json`, `results/post_audit/tail_audit.json`, `data/water_only_check.json`, PCoA summaries |
| S5 | Synthetic validation | `code/simulation_validation.py`, `code/multiconfig_sensitivity.py` |
| S6 | Within-study coherence, upper-tail studies, flagged intervals | `code/supplementary_checks.py`, `code/tail_permutation.py`, `results/post_audit/tail_decomposition.csv`, `code/flagged_studies.py`, `code/flagged_study_cis.py`, `code/leave_flagged_out.py` |
| S7 | Balance and density-matched controls | `code/balance_diagnostics.py`, `code/panel_decomposition.py` (density-matched), `data/balance_complete_partial.json` |
| S8 | Dimension sweep and 3-D block factors | `code/dimension_sweep.py`, `code/three_d_models.py`, `data/coverage_3d_models.csv` |
| S9 | Leverage diagnostics | `code/leverage_check.py`, `results/post_audit/leverage_per_paper.csv` |
| S10 | Flag calibration and power | `code/q95_corpus.py`, `code/q95_calibration.py`, `code/q95_count_matched.py`, `code/q95_power_curve.py` |
| S11 | Design set and paired contrasts | `code/sharpening_checks.py`, `code/panel_decomposition.py`, `code/ca_sensitivity.py`, `code/all_paper_audit.py`, `data/summary_excluded_check.json` |
| S12 | Near-duplicate collapse | `code/revision/hamming_audit.py` |

## Core reported values

- Curated corpus: 117 papers, 716 rows, 151 within-paper configurations, 136 distinct patterns, 565 repeated rows (78.9%).
- Primary common-evaluation contrast: row-count 1.27 (1.08--1.48), collapsed 0.97 (0.88--1.21), paired \(\Delta=0.17\) (0.10--0.24); two-level interval 0.07--0.24.
- Own-row sensitivity: 1.36 (1.12--1.59) and 1.04 (0.91--1.16).
- Volume-matched whole-configuration control: 1.17 (0.97--1.40), \(\Delta=0.01\) (\(-0.02\)--0.10); exact-volume success 68.4%.
- Direct row-count minus volume-matched contrast: 0.13 (0.10--0.17).
