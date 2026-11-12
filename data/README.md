# Data

Derived tables and audit summaries for the repeated-panel coverage audit.

## Coverage matrix

`coverage_matrix.csv` — 716 curated coverage rows from 117 papers.

- `paper` — paper identifier.
- `row` — within-paper row index.
- `rho` — row coverage density (fraction of the 44 parameters examined).
- 44 parameter columns — 1 = reported present or examined absent; 0 = not reported.

Standard/regulatory rows are excluded. The full extraction has 764 data rows; the analysis sets exclude 34 standard rows and apply the curation rule described in the manuscript.

## Event tables

| File | Contents |
|---|---|
| `baseline_block.csv` | Full row-level block-deletion events. |
| `baseline_matched.csv` | Full row-level matched scattered draws. |
| `collapsed_block.csv` | Unique-configuration block-deletion events. |
| `collapsed_matched.csv` | Unique-configuration matched draws. |
| `weighted_matched_block.csv` | Weighted-fit block-deletion events. |
| `weighted_matched_matched.csv` | Weighted-fit matched draws. |
| `coverage_events.csv` | Row-level coverage audit events from the full pipeline (used by `core_revision_checks.py`). |
| `composition_matched_control.csv` | Composition-matched control events from the full pipeline (used by `core_revision_checks.py`). |
| `coverage_3d_model.csv` | Three-component coverage block model (curated 3-D block factor 1.17). |
| `core_checks.json` | Coarsened nearest-configuration control, exact-subset CIs, and same-size percentile checks. |

Each event table includes the paper identifier, arm, draw, number of rows deleted, median Procrustes drift, and the PC1/PC2/joint class-flip metrics where available.

## Audit summaries

| File | Contents |
|---|---|
| `core.json` | Main full/collapsed audit, block model, composition checks. |
| `extra.json` | Paired full-minus-collapsed difference, weighted control, MDE, perturbation. |
| `water.json` | Water-only audit. |
| `pcoa_summary.json` | Full-set Jaccard PCoA audit. |
| `pcoa_collapsed_summary.json` | Collapsed Jaccard PCoA audit. |

The current 2×2, density/PC2, synthetic-validation, and multi-configuration sensitivity summaries are in `results/post_audit/`.

## Source extraction

`docs/extraction/stageA/matrix_presence_v2.csv` is the presence layer. The stage-B value layer (`matrix_values_v2.csv`) is **not** included in this repository; it remains restricted in the Zenodo data record. The coverage matrix is included in full, so the reported coverage audit can be rerun without the value layer.

Historical release note: An earlier public release included `docs/extraction/stageB/matrix_values_v2.csv`; the current package does not.
