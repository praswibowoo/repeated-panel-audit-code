# p2-deletion-audit-code

Code, data, and result archive for:

> **Row-count versus whole-study controls for repeated single-configuration blocks in binary coverage audits**
>
> Wibowo, P., Veesommai Sillberg, C., & Kiyoki, Y. (2026).
>
> *Environmental and Ecological Statistics*.

Release: `v1.10.0-2026-11-28`. The default `main` branch is historical; use the release tag or `revision/q1-scope` for the current manuscript analysis.

## Current corpus and estimator

- **Primary corpus:** 87 eligibility-qualified papers, 555 rows, 93 matrix-defined configurations; 81 single-configuration papers and six background multi-configuration papers.
- **Active parameters:** 42 populated columns. All-zero `SAR` and `Al (µg/L)` columns are dropped by the loaders; `rho` is recomputed over active columns.
- **Sensitivity corpus:** `data/coverage_matrix.csv` remains the full curated 117-paper / 716-row matrix.
- **Estimator:** `R_s = block_drift_s / median(control_drifts_s)`.
- **Controls:** A and C remain Monte Carlo; Bstudy and Bblock enumerate every eligible donor. Bstudy is nested within Bblock.
- **Scope:** primary focal claims use single-configuration studies only. Multi-configuration studies are background. Design H is removed from current code and outputs.

## Contents

| Path | Purpose |
|---|---|
| `code/` | Current analysis and figure scripts; legacy scripts remain labeled |
| `data/` | Primary/full-curated matrices, manifests, exclusions, event tables, audit frames, and provenance |
| `results/unit_revision_fixed/` | Current primary fixed-set PCA, RMS, PCoA, balance, strata, and full-curated sensitivity |
| `results/post_audit/` | Current fixed simulation and labeled legacy/own-row sensitivities |
| `docs/` | Corpus provenance, screening, verification, and revision audit |
| `figures/` | Generated main and SI figure PDFs |
| `DATA_PROVENANCE.md` | Manuscript-to-source map |

The numeric water-quality value layer is restricted and is not included. All binary coverage matrices and code needed for the reported checks are present.

## Quick start

```bash
conda env create -f environment.yml
conda activate p2-deletion-audit

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

Full-curated sensitivity:

```bash
python3 code/unit_revision_fixed.py --draws 100 \
  --matrix data/coverage_matrix.csv \
  --out results/unit_revision_fixed/sensitivity_full_curated.json
```

Use `python3 code/run_all.py --list` to inspect all available analyses. The
500-draw convergence run is intentionally separate. Manuscript-specific LaTeX
checks are not part of this standalone repository.

## Primary outputs

| File | Role |
|---|---|
| `data/coverage_matrix_primary.csv` | Eligibility-qualified primary corpus |
| `data/primary_corpus_summary.json` | Counts, exclusion reasons, and coder concordance |
| `results/unit_revision_fixed/common_contrast.json` | Primary fixed-set PCA, ratio-of-medians contrasts, strata, nested donor diagnostics, and drift-level bootstrap inputs |
| `results/unit_revision_fixed/fixed3d_contrast.json` | Fixed-set 3-D PCA sensitivity |
| `results/unit_revision_fixed/rms_sensitivity.json` | Fixed-set RMS event-drift sensitivity |
| `results/unit_revision_fixed/pcoa_contrast.json` | Fixed-set two-dimensional Jaccard PCoA |
| `results/unit_revision_fixed/control_balance.json` | Bstudy/Bblock balance and missing-donor studies |
| `results/unit_revision_fixed/sensitivity_full_curated.json` | Full 117-paper curated sensitivity using the current estimator |
| `results/unit_revision_fixed/manuscript_values.json` | Rounded values rendered from current outputs |
| `results/unit_revision_fixed/strata_sensitivity.csv` | Flat block-size sensitivity export |
| `results/unit_revision_fixed/donor_pool_by_focal.csv` | Per-focal exhaustive donor-pool sizes |
| `results/unit_revision_fixed/convergence_100_vs_500.json` | Draw-convergence audit |
| `results/post_audit/simulation_fixed.json` | Fixed-set synthetic benchmarks; simulation Bblock sampling is explicitly labeled |
| `figures/fig_paired_contrast.pdf` | Primary paired-contrast figure |

## Interpretation

- Canonical contrasts are differences of per-study ratio-of-medians estimates. Conditional study-bootstrap ranges are preserved.
- A−Bstudy is the primary whole-study control contrast on eligible single-configuration studies; every eligible whole-study donor is enumerated.
- The 2–5, 6–10, and ≥11 row strata are exploratory descriptive summaries; their cut points were not prespecified.
- A−Bblock is the secondary configuration-donor contrast; every exact-size donor configuration is enumerated, including configurations embedded in multi-configuration studies.
- Two-level bootstrap resamples studies and A/B/C control drifts, then recomputes median control drift and the ratio. Exhaustive Bstudy/Bblock medians stay fixed within study resamples.
- A−C is a protocol contrast that changes fit weighting, control geometry, reference ordination, and normalization.
- Per-study ratios are descriptive, not calibrated outlier scores.

## Legacy provenance

`results/unit_revision/`, `results/unit_revision_fixed/sensitivity_no_B208.json`,
`results/unit_revision_fixed/sensitivity_no_unsure_substitutes.json`, and
own-row scripts/results are retained for provenance only. They are not current
primary outputs and may use the full curated corpus, median-of-ratios, sampled
Bblock, or Design H.

## Manuscript map

The final manuscript has three main tables, one main figure, Figure S1, and SI Tables S1–S7. See `DATA_PROVENANCE.md` for the exact file/script mapping and `docs/audit/REVISION_2026-11-28_Q1_AUDIT.md` for the completed revision audit.
