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
| `duplicate_pair_audit_frame.csv` | Frozen 100-record / 83-unique-unordered-pair frame; human adjudication pending. |
| `duplicate_pair_source_review.csv` | Independent AI-assisted blinded source-review labels; not human adjudication. |
| `duplicate_pair_source_review_summary.json` | Source-review counts and matrix comparison. |
| `prior_human_cell_corrections.csv` | Thirteen P1 human-verified cell corrections, already incorporated in the P2 matrix. |
| `prior_human_pair_evidence.csv` | Mapping of prior human corrections to the 13 affected P2 pairs. |
| `duplicate_pair_adjudication_manifest.json` | Coordinator manifest: 56 primary pairs, 62 second-coder pairs, six QC pairs. |
| `HUMAN_ADJUDICATION_README.md` | Coder instructions, file map, and import command. |
| `duplicate_pair_human_adjudication_primary_blind.csv` | Blind 56-pair primary coding sheet. |
| `duplicate_pair_human_adjudication_second_blind.csv` | Blind 62-pair independent second-coder sheet. |
| `duplicate_pair_human_adjudication_coder.xlsx` | Coder workbook with Instructions, Primary, and Second sheets; no matrix/AI labels. |
| `duplicate_pair_human_adjudication_primary_only.xlsx` | Primary-only 56-pair coder workbook; recommended file to send the primary coder. |
| `duplicate_pair_human_adjudication_second_only.xlsx` | Optional 62-pair independent second-coder workbook. |
| `duplicate_pair_human_adjudication_coordinator_key.csv` | Coordinator-only key linking pairs to matrix class, AI labels, priority, and prior evidence. |
| `duplicate_pair_human_adjudication_coordinator.xlsx` | Coordinator workbook with key, prior evidence, corrections, and status. |

## Fixed-evaluation outputs

These files are under `source/results/unit_revision_fixed/` in the release:

| File | Role |
|---|---|
| `common_contrast.json` | Primary PCA designs, contrasts, configuration strata, donor availability, and per-study draws. |
| `pcoa_contrast.json` | Fixed-set two-dimensional Jaccard PCoA sensitivity. |
| `rms_sensitivity.json` | Fixed-set PCA sensitivity using RMS event drift. |
| `control_balance.json` | Bstudy/Bblock balance, donor composition, and missing-donor studies. |
| `sensitivity_no_B208.json` | Fixed-set exclusion of B208. |
| `sensitivity_no_unsure_substitutes.json` | Fixed-set exclusion of 13 unsure records and the two substitutes retained in the curated set. |
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
