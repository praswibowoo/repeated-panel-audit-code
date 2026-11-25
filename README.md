# p2-deletion-audit-code

Code, data, and result archive for:

> **Control-unit mismatch in leave-one-study-out audits of repeated binary coverage rows**
>
> Wibowo, P., Veesommai Sillberg, C., & Kiyoki, Y. (2026).
>
> *Environmental and Ecological Statistics*.

Release: `v1.7.0-2026-11-25`.

## Contents

| Path | Purpose |
|---|---|
| `code/` | Analysis and figure-generation scripts |
| `data/` | Curated/all-paper/full-extraction coverage matrices, event tables, audit frames, and sensitivity summaries |
| `results/unit_revision_fixed/` | Primary fixed-set PCA, RMS, PCoA, balance, and corpus-exclusion outputs |
| `results/post_audit/` | Synthetic benchmarks and labeled legacy/own-row sensitivities |
| `docs/` | Corpus provenance, screening, verification, and revision audit |
| `figures/` | Generated main and SI figure PDFs |
| `DATA_PROVENANCE.md` | Manuscript-to-source map |

The numeric water-quality value layer is restricted and is not included. All binary coverage matrices and code needed for the reported checks are present.

## Quick start

```bash
conda env create -f environment.yml
conda activate p2-deletion-audit

python3 code/unit_revision_fixed.py --draws 100
python3 code/rms_fixed_sensitivity.py
python3 code/pcoa_fixed.py --draws 100
python3 code/simulation_fixed.py
python3 code/make_fig_paired_contrast.py
python3 code/duplicate_pair_audit.py
python3 code/verify_package.py
```

Use `python3 code/run_all.py --list` to inspect all available analyses. Manuscript-specific LaTeX checks are not part of this standalone repository.

## Primary outputs

| File | Role |
|---|---|
| `results/unit_revision_fixed/common_contrast.json` | Primary fixed-set covariance-PCA audit |
| `results/unit_revision_fixed/rms_sensitivity.json` | Fixed-set RMS event-drift sensitivity |
| `results/unit_revision_fixed/pcoa_contrast.json` | Fixed-set two-dimensional Jaccard PCoA |
| `results/unit_revision_fixed/control_balance.json` | Bblock balance and missing-donor studies |
| `results/unit_revision_fixed/sensitivity_no_B208.json` | Fixed exclusion of B208 |
| `results/unit_revision_fixed/sensitivity_no_unsure_substitutes.json` | Fixed exclusion of 13 unsure records and two substitutes |
| `results/post_audit/simulation_fixed.json` | Fixed-set clustered, planted, and independent-row benchmarks |
| `data/duplicate_pair_audit_frame.csv` | Frozen 100-pair duplicate-classification frame; human adjudication pending |

## Interpretation

- A−Bblock is the primary full-fit control-geometry contrast.
- A−C is a secondary protocol contrast that changes fit weighting and control geometry.
- Bblock is unit-matched only for single-configuration studies.
- Five single-configuration studies lack an exact-size donor and are reported separately.
- H is an exploratory donor-study control, not a validated coherence match.
- Configuration collapse is recommended only for a configuration-weighted target.
- Per-study ratios are descriptive, not calibrated outlier scores.

## Manuscript map

The final manuscript has three main tables, one main figure, and SI Tables S1–S6. See `DATA_PROVENANCE.md` for the exact file/script mapping.
