# Code map

Release: `v1.7.0-2026-11-25`. Run scripts from the repository root.

## Primary analyses

| Script | Purpose | Output |
|---|---|---|
| `unit_revision_fixed.py` | Fixed-set PCA; A/Bblock/C/H, donor availability, paired contrasts, optional exclusions | `results/unit_revision_fixed/common_contrast.json` |
| `rms_fixed_sensitivity.py` | Fixed-set PCA with RMS event drift | `results/unit_revision_fixed/rms_sensitivity.json` |
| `control_balance_fixed.py` | Bblock balance and missing-donor summary | `results/unit_revision_fixed/control_balance.json` |
| `pcoa_fixed.py` | Fixed-set 2-D Jaccard PCoA with out-of-fit projection | `results/unit_revision_fixed/pcoa_contrast.json` |
| `simulation_fixed.py` | Fixed-set clustered, planted, and independent-row benchmarks | `results/post_audit/simulation_fixed.json` |
| `duplicate_pair_audit.py` | Verify frozen 100-pair duplicate-classification frame | `data/duplicate_pair_audit_frame.csv` |
| `make_fig_paired_contrast.py` | Main control-geometry figure | `figures/fig_paired_contrast.pdf` |
| `make_fig_prisma.py` | Corpus provenance figure | `figures/figS1_prisma_flow.pdf` |

## Corpus exclusions

```bash
python3 code/unit_revision_fixed.py --draws 100 --exclude B208 \
  --out results/unit_revision_fixed/sensitivity_no_B208.json

python3 code/unit_revision_fixed.py --draws 100 \
  --exclude B020,B025,B034,B038,B054,B069,B070,B071,B190,B208,B221,B222,B237,B238,B240 \
  --out results/unit_revision_fixed/sensitivity_no_unsure_substitutes.json
```

## Supporting and archived analyses

| Script | Purpose |
|---|---|
| `water_only_check.py` | Water-only own-row sensitivity |
| `ca_sensitivity.py` | Correspondence-analysis own-row sensitivity |
| `dimension_sweep.py` | Own-row 2–5 component sweep |
| `procrustes_holdout.py` | Own-row held-out alignment sensitivity |
| `revision/hamming_audit.py` | Near-duplicate Hamming sensitivity |
| `panel_decomposition.py` | Archived fit/control decomposition and density-matched audit |
| `simulation_validation.py` | Archived own-row synthetic benchmark |
| `simulation_iid_null.py` | Archived own-row independent-row benchmark |
| `balance_diagnostics.py` | Legacy block/control balance summary |
| `verify_package.py` | File inventory and numerical self-check |

Manuscript-specific LaTeX/package checks remain in the editable manuscript source tree and are not required to reproduce the analysis outputs in this repository.
