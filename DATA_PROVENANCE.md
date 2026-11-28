# Data provenance — manuscript map

**Manuscript:** *Row-count versus whole-study controls for repeated single-configuration blocks in binary coverage audits*

**Release:** `v1.10.0-2026-11-28`.

This file maps manuscript items to current code and deposited outputs. Legacy files are identified explicitly and are not current primary evidence.

## Main manuscript

| Item | Content | Primary scripts / files |
|---|---|---|
| Table 1 | Eligibility-qualified primary corpus and full-curated sensitivity corpus | `code/build_primary_corpus.py`, `data/coverage_matrix_primary.csv`, `data/primary_corpus_summary.json`, `data/coverage_matrix.csv` |
| Table 2 | Block-size-conditional A−Bstudy contrast; secondary A−Bblock and A−C contrasts; sensitivity medians | `code/unit_revision_fixed.py`, `results/unit_revision_fixed/common_contrast.json`, `results/unit_revision_fixed/strata_sensitivity.csv` |
| Table 3 | Three-factor framework: fit weighting × deletion unit × donor-sampling distribution | Current Table 2 and SI Tables S2–S5 |
| Fig. 1 | A versus exhaustive Bstudy on 74 eligible papers; continuous block-size view and donor-count encoding | `code/make_fig_paired_contrast.py`, `results/unit_revision_fixed/common_contrast.json` |

## Supplementary information

| SI item | Content | Primary scripts / files |
|---|---|---|
| Figure S1 | Provenance through the 87-paper primary corpus | `code/make_fig_prisma.py`, `data/primary_corpus_summary.json` |
| Table S1 | Eligibility, exclusions, verification, and coder concordance | `code/build_primary_corpus.py`, `data/corpus_manifest_audit.csv`, `data/primary_corpus_exclusions.csv`, `data/primary_corpus_summary.json` |
| Table S2 | Fixed designs, ratio-of-medians contrasts, donor availability, pool sizes, and two-level sensitivity | `code/unit_revision_fixed.py`, `results/unit_revision_fixed/common_contrast.json` |
| Table S3 | Bstudy/Bblock balance and donor composition | `code/control_balance_fixed.py`, `results/unit_revision_fixed/control_balance.json` |
| Table S4 | Fixed-set synthetic benchmarks | `code/simulation_fixed.py`, `results/post_audit/simulation_fixed.json` |
| Table S5 | Fixed 3-D PCA, PCoA, and RMS sensitivities | `code/fixed3d_sensitivity.py`, `code/pcoa_fixed.py`, `code/rms_fixed_sensitivity.py` |
| Table S6 | Full-curated corpus sensitivity and 100-versus-500 draw convergence | `results/unit_revision_fixed/sensitivity_full_curated.json`, `results/unit_revision_fixed/convergence_100_vs_500.json` |
| Table S7 | Parameter dictionary and scenario-coding rules | `data/parameter_dictionary.csv`, `docs/scenario_coding_rules.md`, `docs/primary_corpus.md` |

## Current corpus and estimator facts

- Primary corpus: 87 papers, 555 rows, 93 configurations; 81 single-configuration focal papers and six background multi-configuration papers.
- Full-curated sensitivity corpus: 117 papers, 716 rows, 145 configurations.
- Both loaders drop all-zero `SAR` and `Al (µg/L)` columns, retain 42 active parameters, and recompute `rho` over active columns.
- Estimator: `R_s = block_drift_s / median(control_drifts_s)`.
- A and C use 100 Monte Carlo draws. Bstudy and Bblock enumerate complete donor pools.
- On the shared 74-paper primary set, every Bstudy donor pool is nested within Bblock.
- Two-level bootstrap resamples papers and A/C control drifts; exhaustive Bstudy/Bblock medians remain fixed within paper resamples.
- Primary focal claims use single-configuration papers only. Multi-configuration papers are background. Design H is removed.
- Overall A−Bstudy is primary; 2–5/6–10/≥11 row strata are exploratory because cut points were not prespecified.
- Primary exclusions: unresolved duplicate pairs, decidable primary/coordinator disagreements, ambiguous scenario identity, unsure papers, retained substitutes, and B149.
- Blinded-primary/unblinded-coordinator concordance is 37/56 (66.1%; κ = 0.17). No completed human second-coder file is available.

## Current numerical source of truth

- `results/unit_revision_fixed/common_contrast.json`: primary 2-D estimates, strata, donor-pool distributions, nesting, per-paper ratios, block drifts, and control drifts.
- `results/unit_revision_fixed/fixed3d_contrast.json`, `pcoa_contrast.json`, `rms_sensitivity.json`: fixed sensitivities.
- `results/unit_revision_fixed/sensitivity_full_curated.json`: full-curated sensitivity.
- `results/unit_revision_fixed/convergence_500.json` and `convergence_100_vs_500.json`: draw-convergence check.
- `results/unit_revision_fixed/strata_sensitivity.csv` and `donor_pool_by_focal.csv`: flat audit exports.
- `results/unit_revision_fixed/manuscript_values.json`: rounded renderings only.

## Legacy provenance

- `results/unit_revision/`: archived own-row/common-evaluation audit.
- `results/unit_revision_fixed/sensitivity_no_B208.json` and `sensitivity_no_unsure_substitutes.json`: historical full-curated exclusion runs.
- `results/post_audit/simulation_validation.json`, `simulation_iid_null.json`, and own-row sensitivity summaries: historical methods and corpora.
- `docs/archive/DATA_PROVENANCE_ARCHIVE.md`: archived manuscript map.

## Audit frames

- `data/cell_level_sample.csv`, `cell_level_coded.csv`, `cell_level_triage.csv`: 351-cell automated text-triage and targeted snippet-review audit; not 351 independent human page checks.
- `data/duplicate_pair_audit_frame.csv`: frozen 100 records representing 83 unique pairs; 56 priority pairs have coordinator dispositions.
- `data/duplicate_pair_source_review.csv`: AI-assisted blinded source-review labels; not human adjudication.
- `data/duplicate_pair_human_adjudication_results_approved_2026-11-27.csv`: primary and coordinator labels used for concordance and exclusions.
- `data/duplicate_pair_correction_impact_audit.json`: full-curated and primary-specific configuration, status, and donor-count impact of the 42 approved corrections.
- `data/corpus_manifest_audit.csv`: paper-level screening, substitution, eligibility, exclusion reasons, and pair IDs.
- `docs/ai/`: exact screening and extraction prompts used by the AI-assisted workflow.

The numeric water-quality value layer is restricted and was not analyzed here. All binary matrices and code needed for the reported checks are present.
