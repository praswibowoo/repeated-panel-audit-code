# Code map

Run from the repository root (`p2-deletion-audit-code/`).

## Runnable

| Script | Purpose | Output |
|---|---|---|
| `code/panel_decomposition.py` | 2×2 decomposition, duplication quartiles, study-density-matched collapsed audit. Reads `data/coverage_matrix.csv` and `data/baseline_*.csv` / `data/collapsed_*.csv`. | `results/post_audit/panel_decomposition.json` |
| `code/pc2_density_check.py` | PC1/PC2/joint class flips under row-level and density-matched donors. | `results/post_audit/pc2_density_check.json` |
| `code/simulation_validation.py` | Synthetic panel-structure validation (H0 repeated panels; H1 planted study). | `results/post_audit/simulation_validation.json` |

```bash
python3 code/panel_decomposition.py
python3 code/pc2_density_check.py
python3 code/simulation_validation.py
```

`core_revision_checks.py` is both the shared coverage loader and a runnable check for the coarsened nearest-configuration control and exact-subset CIs. It reads `data/coverage_matrix.csv`, `data/coverage_events.csv`, and `data/composition_matched_control.csv` directly and does not require the restricted value layer.

## Provenance only

| Script | Why it is not standalone |
|---|---|
| `revision_layers.py` | Rebuilds coverage and value layers from `docs/extraction/stageA` and the restricted `stageB/matrix_values_v2.csv`; the value layer is not in this repository. |
| `clean_primary_audit.py` | Imports `ees_revision_checks`, which imports `experiment_H_volumematch` and `ees_rank_matched`; those are not in this repository. |
| `ees_post_audit_extra.py` | Imports `ees_post_audit`, which imports `experiment_H_volumematch`. |
| `ees_revision_checks.py` | Imports `experiment_H_volumematch` and `ees_rank_matched`. |

The event tables they produced are included in `data/`, so the published numbers can be checked without rerunning the legacy pipeline.

## Data paths

- `data/` — coverage matrix, event tables, and audit JSONs.
- `docs/extraction/stageA/matrix_presence_v2.csv` — presence layer. The stage-B value layer is restricted and is not included.
- `results/post_audit/` — current JSON summaries.

## Repositories

- Check package (this repository): `repeated-panel-audit-code`.
- Full analysis pipeline: `ordination-stability-audit`, archived at submission — composition, calibration, and 3-D checks.

