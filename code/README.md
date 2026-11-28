# Code map

Release: `v1.9.2-2026-11-28`. Run scripts from the repository root.

## Primary analyses

| Script | Purpose | Output |
|---|---|---|
| `unit_revision_fixed.py` | Fixed-set PCA; A/exhaustive Bstudy/Bblock/C/H, donor availability, median-ratio contrasts, optional exclusions/dimensions | `results/unit_revision_fixed/common_contrast.json` |
| `fixed3d_sensitivity.py` | Fixed-set 3-D PCA sensitivity | `results/unit_revision_fixed/fixed3d_contrast.json` |
| `rms_fixed_sensitivity.py` | Fixed-set PCA with RMS event drift | `results/unit_revision_fixed/rms_sensitivity.json` |
| `control_balance_fixed.py` | Bstudy/Bblock balance, donor composition, and missing-donor summary | `results/unit_revision_fixed/control_balance.json` |
| `pcoa_fixed.py` | Fixed-set 2-D Jaccard PCoA with out-of-fit projection | `results/unit_revision_fixed/pcoa_contrast.json` |
| `simulation_fixed.py` | Fixed-set clustered, planted, and independent-row benchmarks | `results/post_audit/simulation_fixed.json` |
| `render_fixed_values.py` | Render rounded manuscript values from deposited JSONs | `results/unit_revision_fixed/manuscript_values.json` |
| `duplicate_pair_audit.py` | Verify frozen 100-record / 83-unique-unordered-pair frame | `data/duplicate_pair_audit_frame.csv` |
| `prepare_duplicate_adjudication.py` | Generate recommended eight-column primary sheet, full coder workbooks, and coordinator key | `data/duplicate_pair_human_adjudication_*.csv/xlsx` |
| `extract_simple_adjudication_xlsx.py` | Extract the Primary sheet from the simple workbook to CSV without Excel dependencies; converts Excel date serials | `primary_completed.csv` |
| `import_duplicate_adjudication.py` | Validate human labels and write provisional results, strict-import readiness, pending IDs, and disagreement flags; supports partial/simple input; never edits matrix | `data/duplicate_pair_human_adjudication_results.csv` |
| `build_adjudication_processing_report.py` | Build all-row and flagged coordinator reports with exact matrix differences and required actions; never assigns labels | `data/duplicate_pair_human_adjudication_processing_report_YYYY-MM-DD.csv` |
| `apply_approved_duplicate_pair_corrections.py` | Validate and apply author-approved cell corrections to curated/all-paper/full-extraction/stage-A layers; refresh rho and write audit | `data/duplicate_pair_cell_correction_application_audit_YYYY-MM-DD.json` |
| `refresh_duplicate_pair_matrix_fields.py` | Refresh pair Hamming/density/configuration fields and source-review matrix comparison after approved corrections | updated frame/key/summary/manifest |
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
| `balance_diagnostics.py` | Archived own-row balance summary |
| `verify_package.py` | File inventory and numerical self-check |
| `refresh_release_hashes.py` | Regenerate `MANIFEST.json` and `SHA256SUMS` for the current release |

Manuscript-specific LaTeX/package checks remain in the editable manuscript source tree and are not required to reproduce the analysis outputs in this repository.
