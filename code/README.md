# Code map

Working release: `v1.10.0-2026-11-28`; final tag pending. Run scripts from the repository root.

## Current primary analyses

The default corpus is the eligibility-qualified primary matrix: 87 papers,
555 rows, 93 within-study configurations, 81 single-configuration papers, and
42 populated parameters. Multi-configuration papers remain background only.
All current fixed audits use `R_s = block_drift_s / median(control_drifts_s)`.
A and C are Monte Carlo controls; Bstudy and Bblock are exhaustive. Design H is
removed from current code and outputs.

| Script | Purpose | Output |
|---|---|---|
| `build_primary_corpus.py` | Rebuild primary matrix, manifest, exclusions, and coder-concordance summary | `data/coverage_matrix_primary.csv`, `data/primary_corpus_summary.json` |
| `audit_correction_impact.py` | Reverse approved corrections and quantify full-curated and primary-specific configuration/status/donor impact | `data/duplicate_pair_correction_impact_audit.json` |
| `unit_revision_fixed.py` | Primary fixed-set PCA; A/B/C Monte Carlo, exhaustive Bstudy/Bblock, nested-pool diagnostics, strata, ratio-of-medians contrasts | `results/unit_revision_fixed/common_contrast.json` |
| `fixed3d_sensitivity.py` | Primary fixed-set 3-D PCA sensitivity | `results/unit_revision_fixed/fixed3d_contrast.json` |
| `rms_fixed_sensitivity.py` | Primary fixed-set PCA with RMS event drift | `results/unit_revision_fixed/rms_sensitivity.json` |
| `control_balance_fixed.py` | Primary Bstudy/Bblock balance, donor composition, and missing-donor summary | `results/unit_revision_fixed/control_balance.json` |
| `pcoa_fixed.py` | Primary fixed-set 2-D Jaccard PCoA with exhaustive Bstudy/Bblock | `results/unit_revision_fixed/pcoa_contrast.json` |
| `simulation_fixed.py` | Fixed-set synthetic benchmarks; Bblock sampled and explicitly labeled | `results/post_audit/simulation_fixed.json` |
| `render_fixed_values.py` | Render rounded values from current deposited JSONs | `results/unit_revision_fixed/manuscript_values.json` |
| `make_fig_paired_contrast.py` | Primary paired-contrast figure | `figures/fig_paired_contrast.pdf` |
| `make_fig_prisma.py` | Corpus provenance through the primary set | `figures/figS1_prisma_flow.pdf` |
| `export_strata.py` | Flat exploratory-stratum and donor-pool exports, including shared-Bstudy-set A medians | `results/unit_revision_fixed/strata_sensitivity.csv`, `donor_pool_by_focal.csv` |
| `compare_convergence.py` | Compare 100- and 500-draw outputs | `results/unit_revision_fixed/convergence_100_vs_500.json` |
| `verify_package.py` | File inventory, corpus/loader checks, and numerical self-check | console |

## Full-curated sensitivity

`data/coverage_matrix.csv` remains the full 117-paper / 716-row sensitivity
corpus. It is not the default primary corpus.

```bash
python3 code/unit_revision_fixed.py --draws 100 \
  --matrix data/coverage_matrix.csv \
  --out results/unit_revision_fixed/sensitivity_full_curated.json
```

## Current reproduction sequence

```bash
python3 code/build_primary_corpus.py
python3 code/audit_correction_impact.py
python3 code/unit_revision_fixed.py --draws 100
python3 code/fixed3d_sensitivity.py
python3 code/pcoa_fixed.py --draws 100
python3 code/rms_fixed_sensitivity.py
python3 code/control_balance_fixed.py
python3 code/render_fixed_values.py
python3 code/make_fig_paired_contrast.py
python3 code/export_strata.py
python3 code/verify_package.py
```

`python3 code/run_all.py --list` includes `primarycorpus`, `fixed`, and
`fixedfull` steps. The 500-draw convergence run is intentionally separate.

## Legacy provenance

The following remain deposited for provenance only and are not current primary
outputs: `results/unit_revision/`, `results/unit_revision_fixed/sensitivity_no_B208.json`,
`results/unit_revision_fixed/sensitivity_no_unsure_substitutes.json`, and own-row
scripts/results listed below. Legacy files may use the full curated corpus,
median-of-ratios, sampled Bblock, or Design H.

## Supporting and archived analyses

| Script | Purpose |
|---|---|
| `water_only_check.py` | Legacy water-only own-row sensitivity |
| `ca_sensitivity.py` | Legacy correspondence-analysis own-row sensitivity |
| `dimension_sweep.py` | Legacy own-row 2–5 component sweep |
| `procrustes_holdout.py` | Legacy own-row held-out alignment sensitivity |
| `revision/hamming_audit.py` | Legacy near-duplicate Hamming sensitivity |
| `panel_decomposition.py` | Archived fit/control decomposition and density-matched audit |
| `simulation_validation.py` | Archived own-row synthetic benchmark |
| `simulation_iid_null.py` | Archived own-row independent-row benchmark |
| `balance_diagnostics.py` | Archived own-row balance summary |
| `refresh_release_hashes.py` | Regenerate `MANIFEST.json` and `SHA256SUMS` for the current release |

Manuscript-specific LaTeX/package checks remain in the editable manuscript source tree and are not required to reproduce the analysis outputs in this repository.
