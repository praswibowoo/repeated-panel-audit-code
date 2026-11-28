# Reproducibility deposit — key map

This folder holds matrices, audit frames, event tables, and sensitivity summaries used by the manuscript. The canonical SI map is `../SI_SOURCE_INDEX.md`.

The deposited legacy `baseline_*` and `collapsed_*` event tables remain archived. After the approved 2026-11-27 corrections, current-matrix event rebuilds are under `results/rebuild/`, and the fixed-evaluation outputs under `results/unit_revision_fixed/` are authoritative for the revised manuscript.

## Primary data and audit frames

| File | Role |
|---|---|
| `coverage_matrix.csv` | Curated 716-row / 117-study binary coverage matrix. |
| `coverage_matrix_all_paper.csv` | 730-row / 122-study all-paper sensitivity. |
| `coverage_matrix_full_extraction.csv` | 764-row / 122-study full extraction. |
| `coverage_matrix_types.csv` | Water/non-water row map. |
| `corpus_manifest.csv` | 138-paper manifest and extraction status. |
| `cell_level_sample.csv`, `cell_level_coded.csv`, `cell_level_triage.csv` | Targeted 351-cell audit frame and coding. |
| `duplicate_pair_audit_frame.csv` | Frozen 100-record / 83-unique-unordered-pair frame; 56 priority pairs have author-approved coordinator resolutions. |
| `duplicate_pair_source_review.csv` | Independent AI-assisted blinded source-review labels; not human adjudication. |
| `duplicate_pair_source_review_summary.json` | Source-review counts and post-correction matrix comparison. |
| `prior_human_cell_corrections.csv` | Thirteen historical P1 human-verified cell corrections; four are superseded by the approved 2026-11-27 review. |
| `prior_human_pair_evidence.csv` | Mapping of prior human corrections to affected pairs, with post-correction values and resolution status. |
| `duplicate_pair_adjudication_manifest.json` | Coordinator manifest: 56 primary pairs, 62 second-coder pairs, six QC pairs. |
| `HUMAN_ADJUDICATION_README.md` | Coder instructions, file map, partial-processing commands, and import workflow. |
| `duplicate_pair_human_adjudication_primary_completed_partial_2026-11-26.csv` | Extracted 31-row partial primary submission. |
| `duplicate_pair_human_adjudication_partial_results_2026-11-26.csv` | Provisional row-level processing results. |
| `duplicate_pair_human_adjudication_partial_summary_2026-11-26.json` | Partial-processing counts and quality flags. |
| `duplicate_pair_human_adjudication_partial_review_flags_2026-11-26.csv` | Completed rows requiring coordinator recheck. |
| `duplicate_pair_human_adjudication_partial_coordinator_notes_2026-11-26.md` | Human-readable coordinator review notes for the 31-row partial submission. |
| `duplicate_pair_human_adjudication_primary_completed_2026-11-27.csv` | Extracted 56-row primary submission; all relation labels completed. |
| `duplicate_pair_human_adjudication_results_2026-11-27.csv` | Provisional row-level processing results for the current submission. |
| `duplicate_pair_human_adjudication_summary_2026-11-27.json` | Current counts, disagreement lists, and strict-import readiness. |
| `duplicate_pair_human_adjudication_processing_report_2026-11-27.csv` | All 56 primary rows with status, matrix differences, flags, and required actions. |
| `duplicate_pair_human_adjudication_review_flags_2026-11-27.csv` | 39 rows requiring coordinator review. |
| `duplicate_pair_human_adjudication_coordinator_notes_2026-11-27.md` | Human-readable coordinator review notes for the current submission. |
| `duplicate_pair_coordinator_resolution_template_2026-11-27.csv` | Provisional primary-only coordinator resolution template. |
| `duplicate_pair_coordinator_source_review_2026-11-27.csv` | Proposed source-based relations for all 56 primary pairs; not human-approved. |
| `duplicate_pair_coordinator_blind_audit_2026-11-27.csv` | Blinded recheck of all 19 changed primary labels; all agree with proposals. |
| `duplicate_pair_coordinator_resolution_proposed_2026-11-27.csv` | Proposed coordinator resolutions with evidence, confidence, correction flags, and blind-audit results. |
| `duplicate_pair_proposed_cell_corrections_2026-11-27.csv` | 42 unique pending binary-cell corrections; none approved or applied. |
| `duplicate_pair_configuration_impact_proposed_2026-11-27.csv` | Provisional in-memory configuration impact: 151 to 145 across 15 papers if all corrections are approved. |
| `duplicate_pair_coordinator_review_memo_2026-11-27.md` | Review memo covering proposed relations, prior-correction conflicts, unresolved cells, and approval sequence. |
| `duplicate_pair_approved_cell_corrections_2026-11-27.csv` | User-approved 42-cell correction log; all cells applied. |
| `duplicate_pair_coordinator_resolution_approved_2026-11-27.csv` | User-approved resolutions: 53 same, 3 undecidable. |
| `duplicate_pair_cell_correction_application_audit_2026-11-27.json` | Application audit with before/after hashes and configuration counts. |
| `duplicate_pair_human_adjudication_results_approved_2026-11-27.csv` | Final approved row-level adjudication results. |
| `duplicate_pair_human_adjudication_summary_approved_2026-11-27.json` | Final approved counts and matrix agreement. |
| `duplicate_pair_audit_frame_human_approved_2026-11-27.csv` | Approved human-filled audit frame. |
| `duplicate_pair_coordinator_review_memo_approved_2026-11-27.md` | Approval/application memo, superseded prior corrections, residual issues, and downstream status. |
| `duplicate_pair_human_adjudication_primary_blind.csv` | Blind 56-pair primary coding sheet. |
| `duplicate_pair_human_adjudication_second_blind.csv` | Blind 62-pair independent second-coder sheet. |
| `duplicate_pair_human_adjudication_coder.xlsx` | Coder workbook with Instructions, Primary, and Second sheets; no matrix/AI labels. |
| `duplicate_pair_human_adjudication_primary_simple.csv` | Recommended eight-column primary coding CSV. |
| `duplicate_pair_human_adjudication_primary_simple.xlsx` | Eight-column primary workbook; completed user submission dated 2026-11-27. |
| `duplicate_pair_human_adjudication_primary_only.xlsx` | Full primary-only 56-pair coder workbook for advanced use. |
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
| `source/results/post_audit/hamming_collapse_review.json` | Post-correction own-row Hamming-collapse ratios and configuration counts. |
| `reproducibility/ca_sensitivity.json` | Legacy own-row correspondence-analysis sensitivity. |
| `reproducibility/water_only_check.json` | Legacy own-row water-only sensitivity. |
| `source/results/post_audit/dimension_sweep.json` | Legacy own-row 2–5 component sweep. |
| `source/results/post_audit/procrustes_holdout.json` | Legacy own-row held-out alignment sensitivity. |
| `source/results/post_audit/leave_flagged_out.json` | Legacy own-row leave-six-out sensitivity. |

Legacy event tables and archived analyses remain in the release for continuity but are not used for the manuscript's current claims.
