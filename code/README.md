# Code map

Run from the repository root (`p2-repeated-panel-audit-code/`).

## Runnable

| Script | Purpose | Output |
|---|---|---|
| `code/panel_decomposition.py` | 2×2 decomposition, duplication quartiles, study-density-matched collapsed audit. Reads `data/baseline_*.csv` and `data/collapsed_*.csv`. | `results/post_audit/panel_decomposition.json` |
| `code/pc2_density_check.py` | PC1/PC2/joint class flips under row-level and density-matched donors. | `results/post_audit/pc2_density_check.json` |
| `code/simulation_validation.py` | Synthetic panel-structure validation (H0 repeated panels; H1 planted study). | `results/post_audit/simulation_validation.json` |

```bash
python3 code/panel_decomposition.py
python3 code/pc2_density_check.py
python3 code/simulation_validation.py
```

`core_revision_checks.py` and `revision_layers.py` are dependencies imported by the scripts above; they are not intended to be run directly.

## Provenance only

| Script | Why it is not standalone |
|---|---|
| `clean_primary_audit.py` | Imports `ees_revision_checks`, which imports `experiment_H_volumematch` and `ees_rank_matched`; those are not in this repository. |
| `ees_post_audit_extra.py` | Imports `ees_post_audit`, which imports `experiment_H_volumematch`. |
| `ees_revision_checks.py` | Imports `experiment_H_volumematch` and `ees_rank_matched`. |

The event tables they produced are included in `data/`, so the published numbers can be checked without rerunning the legacy pipeline.

## Data paths

- `data/` — coverage matrix, event tables, and audit JSONs.
- `docs/extraction/stageA/matrix_presence_v2.csv` and `stageB/matrix_values_v2.csv` — source CSVs required by `revision_layers.py`.
- `results/post_audit/` — current JSON summaries.
