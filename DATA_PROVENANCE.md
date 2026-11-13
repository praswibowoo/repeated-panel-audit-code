# Data provenance — every reported quantity and its file

This package is self-contained for the reported results. Each row names the
quantity as it appears in the manuscript, the file that carries it, and
whether this package recomputes it or only carries the summary.

Status codes:
- **recomputed** — a script in `code/` regenerates the value from `data/`.
- **summary** — the archived pipeline produced it; the summary file is
  deposited, the generating stage is not (stated in the manuscript's
  limitations).
- **derived** — the value follows from a deposited matrix by a documented rule.

## Corpus and panel structure

| Quantity | File | Status |
|---|---|---|
| 138 papers, 122 with data, 16 not retrieved | `corpus_manifest.csv` | derived |
| 867 presence rows | `docs/extraction/stageA/matrix_presence_v2.csv` (`row_kind`) | derived |
| 764 data rows; 730 all-paper rows | `coverage_matrix_full_extraction.csv`, `coverage_matrix_all_paper.csv` | derived (rule in `reproducibility` README of the manuscript source) |
| 716 / 117 curated; 151 within-paper unique; 565 duplicate rows | `coverage_matrix.csv` | recomputed (`verify_package.py`) |
| 44 parameters (42 populated; Al and SAR empty) | all three matrices | recomputed (`verify_package.py`) |
| Coverage cells 7,238 / 49 / 26,329; row density 0.20 (0.16–0.27) | `coverage_matrix_full_extraction.csv` | derived |

## Primary audit (716/117)

| Quantity | File | Status |
|---|---|---|
| 1.36 (1.12–1.59); block factor 1.39 (1.23–1.56) | `baseline_block.csv`, `baseline_matched.csv`, `core.json` | recomputed (`verify_package.py`) |
| 1.33 / 1.59 / 0.97 decomposition | `results/post_audit/panel_decomposition.json` | recomputed (`panel_decomposition.py`) |
| 1.04 (0.91–1.16); 1.01 (0.89–1.15) | `collapsed_block.csv`, `collapsed_matched.csv`, `extra.json` | recomputed (`verify_package.py`) |
| 1.45 (1.27–1.66); 1.53 (1.27–1.88) | `weighted_matched_*.csv`, `panel_decomposition.json` | recomputed |
| Study-level refit 1.42 (1.25–1.59); interaction 1.43 / 1.12 | `core.json` (`baseline.model`) | derived |
| PC1/PC2/joint class changes 3.37/3.38, 2.10/1.41, 4.92/4.63 | baseline event tables | recomputed (`verify_package.py`) |
| Block percentile 76 (30–98); 29.1% / 6.0% | `p0_composition_percentile.csv` | summary |
| B063 / B166 ratios and class changes | collapsed event tables | recomputed (`verify_package.py`) |

## Robustness and sensitivity

| Quantity | File | Status |
|---|---|---|
| Density-matched 0.96 (0.85–1.04); quartiles | `panel_decomposition.json` (`density_quartile_bin`, per-paper ratios) | recomputed (`panel_decomposition.py`) |
| PC2 1.44 pp; 49.6/26.5; 23.9% ties; p = 4.4e-6; density-matched 42.7/33.3; p = 0.014 | collapsed event tables; `results/post_audit/pc2_density_check.json` | recomputed (`pc2_density_check.py`) |
| Composition 1.14 / 1.26 / 1.34; exact 0.81 / 1.00 / 1.27; 96 without match 1.20 | `core_checks.json`, `composition_*.csv` | recomputed (`core_revision_checks.py`) |
| Water-only 1.38 / 1.04 | `water.json` | summary |
| PCoA 1.39 / 0.99 | `pcoa_summary.json`, `pcoa_collapsed_summary.json` | summary |
| 3-D 1.17 (curated) | `coverage_3d_model.csv` | summary |
| All-paper 1.34 (1.11–1.60) | `coverage_matrix_all_paper.csv`; `results/post_audit/all_paper_audit.json` | recomputed (`all_paper_audit.py`); block factor 1.40 archived vs ≈1.42 on a fresh draw, a Monte Carlo difference |
| Include-standard 1.10 | `coverage_matrix_full_extraction.csv` | derived (same caveat) |
| Over-marking perturbation 1.30–1.33 and 1.09–1.16 | `presence_misclassification_summary.csv`, `extra.json` | summary |
| 11.1% over-marking rate | `presence_misclassification_summary.csv` | derived |

## Synthetic validation and calibration

| Quantity | File | Status |
|---|---|---|
| H0 1.58 / 0.995; H1 4.66; 90% above 2; percentile 98.3 | `results/post_audit/simulation_validation.json` | recomputed (`simulation_validation.py`) |
| 1% / 5% flips: 0.96 / 1.34; 33% / 0% | `results/post_audit/multiconfig_sensitivity.json` | recomputed (`multiconfig_sensitivity.py`) |
| Calibration panels (SI) | `calibration_*.csv`, `sim_calibration_*.csv` | summary |
| Exact-subset baseline | `review_findings.json` | summary |

## Reproducing

```
python3 code/verify_package.py          # check every deposited value (~10 s)
python3 code/panel_decomposition.py     # ~60 s
python3 code/pc2_density_check.py       # ~15 s
python3 code/core_revision_checks.py    # ~60 s
python3 code/simulation_validation.py   # ~6 min
python3 code/multiconfig_sensitivity.py # ~12 min
```

The scripts write to `results/post_audit/` (and `results/core_revision/` for
the core checks). The committed JSONs are the published outputs.
