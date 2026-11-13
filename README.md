# p2-deletion-audit-code

GitHub remote: `repeated-panel-audit-code` (unchanged; the manuscript cites that URL).

Code and data for:

> **Repeated panels can inflate apparent study-block influence in pooled parameter-coverage ordinations.**
> Wibowo, P., Veesommai Sillberg, C., & Kiyoki, Y. (2026).
> *Environmental and Ecological Statistics*; manuscript prepared for submission.

This repository is the **check package** for the reported audit. It contains the coverage matrix, event tables, and audit summaries needed to reproduce the reported checks. The full analysis pipeline (composition, calibration, and 3-D checks) is in `ordination-stability-audit` (archived at submission). The manuscript source and submission package are available from the corresponding author.

## Contents

| Path | Purpose |
|---|---|
| `code/` | Audit scripts. See `code/README.md`. |
| `data/` | Coverage matrix, event tables, and audit JSONs. |
| `docs/extraction/` | Stage-A presence CSV (the stage-B value layer is restricted and not included). |
| `DATA_PROVENANCE.md` | Every reported quantity mapped to its file and script. |
| `results/post_audit/` | JSON summaries: 2×2 decomposition, density/PC2 check, synthetic validation, multi-configuration sensitivity, and all-paper audit. |

## Quick start

```bash
# Option 1: conda
conda env create -f environment.yml
conda activate p2-deletion-audit

# Option 2: pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 code/run_all.py --quick         # ~2 min: fast end-to-end check
python3 code/run_all.py                 # ~22 min: every analysis, then self-check
python3 code/run_all.py --list          # show the steps
```

`run_all.py` runs the analyses in order and finishes with `verify_package.py`.
Use `--only panel,pc2` (or any comma-separated subset) to run a few steps.

Individual steps are also runnable on their own:

```bash
python3 code/panel_decomposition.py
python3 code/pc2_density_check.py
python3 code/core_revision_checks.py
python3 code/all_paper_audit.py
python3 code/simulation_validation.py
python3 code/multiconfig_sensitivity.py
python3 code/verify_package.py
```

The scripts write to `results/post_audit/` (and `results/core_revision/`). The committed JSONs are the published outputs; rerunning them should reproduce the same values.

`simulation_validation.py` runs 100 synthetic corpora by default (about 6 minutes). For a quick check:

```bash
SIM_REPS=10 SIM_OUT=simulation_validation_quick.json python3 code/simulation_validation.py
# optional: core revision checks (coarsened control, exact-subset CIs)
python3 code/core_revision_checks.py
```

This writes the quick check to a separate file and does not overwrite the published 100-replicate summary.

## What each script does

| Script | Purpose |
|---|---|
| `panel_decomposition.py` | 2×2 decomposition of fit, evaluation set, and matched control; duplication quartiles; study-density-matched collapsed audit. |
| `pc2_density_check.py` | PC1/PC2/joint class flips under row-level and study-density-matched donors. |
| `simulation_validation.py` | Synthetic panel-structure validation: H0 repeated panels only; H1 planted study-level effect. |
| `multiconfig_sensitivity.py` | Within-study configuration-heterogeneity sensitivity (1% and 5% flips); wraps `simulation_validation.py` and merges both runs. |
| `all_paper_audit.py` | All-paper (730/122) coverage audit; reproduces the Table 4 ratio 1.34 (1.11–1.60). |
| `core_revision_checks.py` | Coarsened nearest-configuration control, exact-subset CIs, and same-size percentile checks. |
| `verify_package.py` | Fast self-check: file inventory, matrix agreement, and committed summary values. |
| `run_all.py` | One entry point: runs the analyses in order, then the self-check (`--quick`, `--only`, `--list`). |
| `common.py` | Shared helpers: PCA, Procrustes drift, paired ratio, bootstrap, unique mask, seed convention, loaders. |
| `code/legacy/revision_layers.py` | Provenance-only coverage/value builder; requires the restricted value layer and is not needed for the quick start. |

`code/legacy/` holds `clean_primary_audit.py`, `ees_post_audit_extra.py`, `ees_revision_checks.py`, and `revision_layers.py`; they require the archived pipeline (and, for two of them, the restricted value layer) and are not standalone. The event tables they produced are included in `data/`, so the published numbers can be checked without rerunning them.

## Data

- `data/coverage_matrix.csv` — 716 curated coverage rows × 44 parameters, with `paper`, `row`, and `rho`.
- `data/baseline_block.csv`, `data/baseline_matched.csv` — full row-level audit events.
- `data/collapsed_block.csv`, `data/collapsed_matched.csv` — unique-configuration audit events.
- `data/weighted_matched_block.csv`, `data/weighted_matched_matched.csv` — weighted control events.
- `data/core.json`, `data/extra.json`, `data/water.json`, `data/pcoa_summary.json`, `data/pcoa_collapsed_summary.json` — audit summaries.
- `data/core_checks.json` — coarsened nearest-configuration control and exact-subset CIs.
- `data/coverage_events.csv`, `data/composition_matched_control.csv` — full-pipeline inputs for `core_revision_checks.py`.
- `data/coverage_3d_model.csv` — three-component coverage block model (curated 3-D block factor 1.17).
- `docs/extraction/stageA/matrix_presence_v2.csv` — presence layer. The stage-B value layer is restricted and is **not** included in this repository.
- `data/coverage_matrix_all_paper.csv` (730 rows / 122 papers) and `data/coverage_matrix_full_extraction.csv` (764 / 122) — the all-paper and full-extraction coverage sets.
- `data/corpus_manifest.csv` — 138-paper manifest with data status and row counts.
- `data/composition_matched_summary.csv`, `composition_vs_density.csv`, `composition_exact_subset.csv`, `p0_composition_percentile.csv` — composition and percentile summaries.
- `data/presence_misclassification_summary.csv`, `preprocessing_block_factor.csv`, `coverage_volume_bins.csv`, `row_count_sensitivity.csv`, `review_findings.json` — sensitivity summaries.
- `data/calibration_*.csv`, `sim_calibration_*.csv` — SI calibration tables.

Coverage codes reported-present and examined-absent as 1, not-reported as 0. Standard/regulatory rows are excluded from the analysis sets.

## Historical release note

An early tag carried `docs/extraction/stageB/matrix_values_v2.csv`. On 2026-11-13 the repository was recreated without that file so the value layer stays restricted; existing clones should be re-cloned. Cite the current repository for the reported checks.

## Citation

If you use this code, cite the paper and this repository. A `CITATION.cff` is included.

## License

Code: MIT. Data: CC BY 4.0. Third-party source papers are not included. See `LICENSE`.

## Contact

Prasetyo Wibowo · pras@pens.ac.id
