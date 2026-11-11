# repeated-panel-audit-code

Code and data for:

> **Repeated panels inflate apparent study-block influence in a pooled coverage ordination.**
> Wibowo, P., Veesommai Sillberg, C., & Kiyoki, Y. (2026).
> *Environmental and Ecological Statistics*, in review.

This repository contains the code, coverage matrix, event tables, and audit summaries needed to reproduce the reported checks. The manuscript source and submission package are available from the corresponding author.

## Contents

| Path | Purpose |
|---|---|
| `code/` | Audit scripts. See `code/README.md`. |
| `data/` | Coverage matrix, event tables, and audit JSONs. |
| `docs/extraction/` | Source extraction CSVs required by `revision_layers.py`. |
| `results/post_audit/` | Current JSON summaries for the 2×2 decomposition, density/PC2 check, and synthetic validation. |

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 code/panel_decomposition.py
python3 code/pc2_density_check.py
python3 code/simulation_validation.py
```

The scripts write to `results/post_audit/`. The committed JSONs are the published outputs; rerunning them should reproduce the same values.

`simulation_validation.py` runs 100 synthetic corpora by default (about 6 minutes). For a quick check:

```bash
SIM_REPS=10 python3 code/simulation_validation.py
```

## What each script does

| Script | Purpose |
|---|---|
| `panel_decomposition.py` | 2×2 decomposition of fit, evaluation set, and matched control; duplication quartiles; study-density-matched collapsed audit. |
| `pc2_density_check.py` | PC1/PC2/joint class flips under row-level and study-density-matched donors. |
| `simulation_validation.py` | Synthetic panel-structure validation: H0 repeated panels only; H1 planted study-level effect. |
| `core_revision_checks.py` | Shared data loader and audit helpers. |
| `revision_layers.py` | Canonical coverage/value layers and source CSV loader. |

`clean_primary_audit.py`, `ees_post_audit_extra.py`, and `ees_revision_checks.py` are included for provenance but require the full legacy pipeline; they are not standalone. The event tables they produced are included in `data/`, so the published numbers can be checked without rerunning them.

## Data

- `data/coverage_matrix.csv` — 716 curated coverage rows × 44 parameters, with `paper`, `row`, and `rho`.
- `data/baseline_block.csv`, `data/baseline_matched.csv` — full row-level audit events.
- `data/collapsed_block.csv`, `data/collapsed_matched.csv` — unique-configuration audit events.
- `data/weighted_matched_block.csv`, `data/weighted_matched_matched.csv` — weighted control events.
- `data/core.json`, `data/extra.json`, `data/water.json`, `data/pcoa_summary.json`, `data/pcoa_collapsed_summary.json` — audit summaries.
- `docs/extraction/stageA/matrix_presence_v2.csv`, `docs/extraction/stageB/matrix_values_v2.csv` — source extraction CSVs.

Coverage codes reported-present and examined-absent as 1, not-reported as 0. Standard/regulatory rows are excluded from the analysis sets.

## License

Code: MIT. Data: CC BY 4.0. Third-party source papers are not included. See `LICENSE`.

## Contact

Prasetyo Wibowo · pras@pens.ac.id
