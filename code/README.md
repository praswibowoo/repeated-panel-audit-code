# Code map

Run from the repository root (`p2-deletion-audit-code/`).

## One command

```bash
python3 code/run_all.py            # every analysis, then the self-check
python3 code/run_all.py --quick    # two simulation replicates, no multiconfig, 3-D, or tail
python3 code/run_all.py --list
```

`run_all.py` imports each module and calls its `main()`. `common.py` holds the
shared estimator pieces (PCA, drift, bootstrap, seed convention, loaders); the
analysis modules contain only their own design choices. The manuscript checks
(`check_ees.py`, `check_numbers.py`) exist only in the manuscript package, so
`run_all.py` skips them here and ends with `verify_package.py`.

`weighted_pca` is the legacy sqrt(w)-scaled score helper used by the legacy decomposition; `weighted_pca_unweighted` is used by the current factorial, so the weighted+unique cell is an exact row-level identity for the collapsed audit.

## Runnable

| Script | Purpose | Output |
|---|---|---|
| `code/build_matrix_types.py` | Descriptive matrix-type map from the stage-A scenario labels; asserts the 675/41 split. | `data/coverage_matrix_types.csv` |
| `code/water_only_check.py` | Water-only counts and the water-only full and collapsed audit. | `data/water_only_check.json` |
| `code/balance_diagnostics.py` | Balance of the block and matched arms for the four controls (Table S14). | `data/balance_diagnostics.csv` |
| `code/flagged_studies.py` | Descriptors for the six collapsed-audit flags (Table S15). | `data/flagged_studies.csv` |
| `code/multiconfig_h1.py` | Multi-configuration stress test: coherent H0, coherent-extreme, and distinct-extreme designs. | `results/post_audit/multiconfig_h1.json` |
| `code/perturbation_upper.py` | Extraction-error perturbation at 5–25%, including the two upper-bound rates. | `data/presence_misclassification_upper.csv` |
| `code/panel_decomposition.py` | Fit × control factorial (current) plus legacy decomposition, duplication quartiles, study-density-matched collapsed audit. Reads `data/coverage_matrix.csv` and `data/baseline_*.csv` / `data/collapsed_*.csv`. | `results/post_audit/panel_decomposition.json` |
| `code/pc2_density_check.py` | PC1/PC2/joint class flips under row-level and density-matched donors. | `results/post_audit/pc2_density_check.json` |
| `code/simulation_validation.py` | Synthetic panel-structure validation (H0 repeated panels; H1 planted study). | `results/post_audit/simulation_validation.json` |
| `code/multiconfig_sensitivity.py` | 1% and 5% within-study bit-flip sensitivity; runs the simulation twice and merges. | `results/post_audit/multiconfig_sensitivity.json` |
| `code/all_paper_audit.py` | All-paper 730/122 audit; Table 4 ratio 1.34 (1.11--1.60). | `results/post_audit/all_paper_audit.json` |
| `code/core_revision_checks.py` | Coarsened nearest-configuration control, exact-subset CIs, same-size percentile. | `results/core_revision/core_checks.json` |
| `code/supplementary_checks.py` | Hamming distribution, tail proportions, subgroup, exact-subset means, block-percentile IQR, study-level model, two-level bootstrap. | `results/post_audit/tail_audit.json`, `tail_decomposition.csv`, `data/study_level_model.json` |
| `code/tail_null.py` | Permutation null for the per-study collapsed ratio by configuration count, with the common-evaluation recomputation. | `results/post_audit/tail_null.json` |
| `code/table_checks.py` | Exact-subset block factor, top-25/Spearman differences, and row-level PC2 summary for Tables S3, S5, and S10. | `results/post_audit/table_checks.json` |
| `code/rebuild_events.py` | Regenerates the four primary event tables from `coverage_matrix.csv` and reports the difference; does not overwrite them. | `results/rebuild/` |
| `code/coherence_control.py` | Coherence-matched control for the 20 multi-configuration papers. | `results/post_audit/coherence_control.json` |
| `code/three_d_models.py` | Three-component block models for the curated, all-paper, and include-standard matrices. | `data/coverage_3d_models.csv`, `results/post_audit/three_d_models.json` |
| `code/verify_package.py` | Fast self-check: file inventory, matrix agreement, committed values. | console |
| `code/run_all.py` | Runs every step in order, then the self-check. | console |

```bash
python3 code/verify_package.py            # ~10 s
python3 code/build_matrix_types.py        # ~2 s
python3 code/water_only_check.py          # ~30 s
python3 code/balance_diagnostics.py       # ~5 s
python3 code/flagged_studies.py           # ~5 s
python3 code/panel_decomposition.py       # ~60 s
python3 code/pc2_density_check.py         # ~15 s
python3 code/core_revision_checks.py      # ~60 s
python3 code/simulation_validation.py     # ~6 min
python3 code/multiconfig_sensitivity.py   # ~12 min
python3 code/multiconfig_h1.py            # ~4 min
python3 code/perturbation_upper.py        # ~6 min
python3 code/supplementary_checks.py      # ~2 min
python3 code/all_paper_audit.py           # ~2 min
```

`core_revision_checks.py` reads `data/coverage_matrix.csv`, `data/coverage_events.csv`, and `data/composition_matched_control.csv` directly and does not require the restricted value layer.

## Provenance only

| Script | Why it is not standalone |
|---|---|
| `legacy/revision_layers.py` | Rebuilds coverage and value layers from `docs/extraction/stageA` and the restricted `stageB/matrix_values_v2.csv`; the value layer is not in this repository. |
| `legacy/clean_primary_audit.py` | Imports `ees_revision_checks`, which imports `experiment_H_volumematch` and `ees_rank_matched`; those are not in this repository. |
| `legacy/ees_post_audit_extra.py` | Imports `ees_post_audit`, which imports `experiment_H_volumematch`. |
| `legacy/ees_revision_checks.py` | Imports `experiment_H_volumematch` and `ees_rank_matched`. |

The event tables they produced are included in `data/`, so the published numbers can be checked without rerunning the legacy pipeline.

## Data paths

- `data/` — coverage matrix, event tables, and audit JSONs.
- `docs/extraction/stageA/matrix_presence_v2.csv` — presence layer. The stage-B value layer is restricted and is not included.
- `results/post_audit/` — current JSON summaries.

## Repositories

- Check package (this repository): `repeated-panel-audit-code`.
- Full analysis pipeline: `ordination-stability-audit`, archived at submission — composition, calibration, and 3-D checks.

