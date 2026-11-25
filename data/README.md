# Reproducibility deposit — key map

This folder holds matrices, audit frames, event tables, and sensitivity summaries used by the manuscript. The canonical SI map is `../SI_SOURCE_INDEX.md`.

## Primary data and audit frames

| File | Role |
|---|---|
| `coverage_matrix.csv` | Curated 716-row / 117-study binary coverage matrix. |
| `coverage_matrix_all_paper.csv` | 730-row / 122-study all-paper sensitivity. |
| `coverage_matrix_full_extraction.csv` | 764-row / 122-study full extraction. |
| `coverage_matrix_types.csv` | Water/non-water row map. |
| `corpus_manifest.csv` | 138-paper manifest and extraction status. |
| `cell_level_sample.csv`, `cell_level_coded.csv`, `cell_level_triage.csv` | Targeted 351-cell audit frame and coding. |
| `duplicate_pair_audit_frame.csv` | Frozen 100-pair duplicate-classification frame; human adjudication pending. |

## Fixed-evaluation outputs

These files are under `source/results/unit_revision_fixed/` in the release:

| File | Role |
|---|---|
| `common_contrast.json` | Primary PCA designs, contrasts, configuration strata, donor availability, and per-study draws. |
| `pcoa_contrast.json` | Fixed-set two-dimensional Jaccard PCoA sensitivity. |
| `rms_sensitivity.json` | Fixed-set PCA sensitivity using RMS event drift. |
| `control_balance.json` | Bblock balance and missing-donor studies. |
| `sensitivity_no_B208.json` | Fixed-set exclusion of B208. |
| `sensitivity_no_unsure_substitutes.json` | Fixed-set exclusion of 13 unsure records and two substitutes. |
| `manuscript_values.json` | Rounded values used by checks. |

## Synthetic and sensitivity outputs

| File | Role |
|---|---|
| `source/results/post_audit/simulation_fixed.json` | Fixed-set clustered, planted, and independent-row benchmarks. |
| `reproducibility/ca_sensitivity.json` | Legacy own-row correspondence-analysis sensitivity. |
| `reproducibility/water_only_check.json` | Legacy own-row water-only sensitivity. |
| `source/results/post_audit/dimension_sweep.json` | Legacy own-row 2–5 component sweep. |
| `source/results/post_audit/procrustes_holdout.json` | Legacy own-row held-out alignment sensitivity. |
| `source/results/post_audit/leave_flagged_out.json` | Legacy own-row leave-six-out sensitivity. |

Legacy event tables and archived analyses remain in the release for continuity but are not used for the manuscript's current claims.
