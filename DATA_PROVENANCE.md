# Data provenance — every reported quantity and its file

This package is self-contained for the reported 2-D results, the tail checks,
and the three 3-D models. Version: P2 v1.87 (scope-locked; leverage mechanism; CA sensitivity; flag scoped to single-configuration studies). A few archived full-pipeline values are noted where
the deposited re-run differs only by draw-level Monte Carlo; those rows say so.
Each row names the quantity as it appears in the manuscript, the file that
carries it, and whether this package recomputes it or only carries the summary.

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
| Post-correction re-audit: 25 papers, 30 claims (13 corrections + 17 sampled), 30/30 pass; 17 independent (95% CI 81--100) | `data/verification/stageA_postcorrection_summary.json`, `..._results.csv` | deposited row-level results (recovered from the P1 archive) |
| 44 parameters (42 populated; Al and SAR empty) | all three matrices | recomputed (`verify_package.py`) |
| Coverage cells 7,238 / 49 / 26,329; row density 0.20 (0.16–0.27) | `docs/extraction/stageA/matrix_presence_v2.csv` (764 data rows × 44 columns) | derived; the coverage matrix encodes Y and NE as 1 (7,287 ones), so the split is not recoverable from it |

## Primary audit (716/117)

| Quantity | File | Status |
|---|---|---|
| 1.37 (1.13–1.57), two-level; block factor 1.39 (1.23–1.56) | `tail_audit.json` (`two_level_bootstrap`), `core.json` (`model.block`), `baseline_block.csv`, `baseline_matched.csv` | recomputed (`supplementary_checks.py`); `core.json` gives the study-level 1.36 (1.12–1.59) |
| Fit × control factorial 1.27 / 1.23 / 1.43 / 0.97 / 0.97 | `results/post_audit/panel_decomposition.json` (`factorial`) | recomputed (`panel_decomposition.py`, unweighted row scores) |
| Factorial interaction 0.99 (0.68–1.28); 99.1% positive | `results/post_audit/panel_decomposition.json` (`factorial.interaction`) | recomputed (`panel_decomposition.py`) |
| Legacy decomposition 1.33 / 1.59 / 1.53 / 0.97 (legacy weighted scores) | `results/post_audit/panel_decomposition.json` (`decomposition`) | legacy; retained in SI S9, not current |
| 1.03 (0.89–1.19), two-level; 1.01 (0.89–1.15) | `tail_audit.json` (`two_level_bootstrap`), `core.json` (`model.block`), `collapsed_block.csv`, `collapsed_matched.csv` | recomputed (`supplementary_checks.py`); `extra.json` gives the study-level 1.04 (0.91–1.16) |
| 1.45 (1.27–1.66) legacy weighted scores; 1.53 (1.27–1.88) legacy | `weighted_matched_*.csv`, `panel_decomposition.json` (`decomposition`) | deposited summary/legacy; not current |
| Study-level refit 1.42 (1.25–1.59) | `study_level_model.json` (`curated`; re-run 1.416, 1.244–1.605), `tail_audit.json` | recomputed (`supplementary_checks.py`); archived CI 1.25–1.59 |
| Interaction 1.43 / 1.12 | `core.json` (`baseline.model`, `collapsed.model`) | derived |
| PC1/PC2/joint class changes 3.37/3.38, 2.10/1.41, 4.92/4.63 | baseline event tables | recomputed (`verify_package.py`) |
| Block percentile 76 (30–98); 29.1% / 6.0% | `p0_composition_percentile.csv` (median/tails); `tail_audit.json` (`block_percentile`, IQR) | recomputed (`supplementary_checks.py`) |
| B063 / B166 ratios and class changes | collapsed event tables | recomputed (`verify_package.py`) |
| Leverage vs full 0.69; vs collapsed 0.70; rows vs full 0.29; rows vs collapsed 0.01 | `results/post_audit/leverage_check.json`, `leverage_per_paper.csv` | recomputed (`leverage_check.py`) |
| Log models: full 0.32 log rows + 0.17 leverage (R² 0.55); collapsed −0.10 + 0.18 (R² 0.55) | `results/post_audit/leverage_check.json` | recomputed (`leverage_check.py`) |
| Corpus exceedance: 16/97 and 3/20 at >2; 2/97 and 3/20 at q95 | `results/post_audit/q95_corpus.json` | recomputed (`q95_corpus.py`) |
| Synthetic flag rates: H0 62%/38%; coherent-extreme 100%/82%; distinct-extreme 56%/36% | `results/post_audit/q95_calibration.json` | recomputed (`q95_calibration.py`) |
| CA sensitivity: full 1.26 (1.00–1.66); collapsed 1.15 (0.81–1.51); paired 0.18 (0.06–0.37) | `results/post_audit/ca_sensitivity.json` | recomputed (`ca_sensitivity.py`) |
| Count-matched null: median 1.06, q95 1.94; coherent null flagged 66% | `results/post_audit/q95_count_matched.json` | recomputed (`q95_count_matched.py`) |
| Single-configuration power: 80% at q95, 94% at >2 | `results/post_audit/q95_single_power.json` | recomputed (`q95_single_power.py`) |

## Robustness and sensitivity

| Quantity | File | Status |
|---|---|---|
| Density-matched 0.96 (0.87–1.07; two-level); density-matched quartiles | `panel_decomposition.json` (`density_matched_collapsed`, `density_matched_collapsed_per_paper`), `tail_audit.json` (`density_matched`) | recomputed (`panel_decomposition.py`); row-level quartiles 0.93/0.67/0.78/1.73 from `collapsed_block.csv`/`collapsed_matched.csv` |
| PC2 1.44 pp; 49.6/26.5; 23.9% ties; p = 4.4e-6; density-matched 42.7/33.3; p = 0.014 | collapsed event tables; `results/post_audit/pc2_density_check.json` | recomputed (`pc2_density_check.py`) |
| Composition 1.14 / 1.26 / 1.34; exact 0.81 / 1.00 / 1.27; 96 without match 1.20 | `core_checks.json`, `composition_*.csv` | recomputed (`core_revision_checks.py`) |
| Matrix-type map: water 675, non-water 41 (summary 20, bioassay 7, sediment 5, experimental 4, soil 3, biota 2); 115 water-only papers | `coverage_matrix_types.csv` | derived (`build_matrix_types.py`) |
| Water-only 1.41 / 0.93; 675 rows / 115 papers / 134 unique configurations | `water_only_check.json` | recomputed (`water_only_check.py`) |
| PCoA 1.39 / 0.99 | `pcoa_summary.json`, `pcoa_collapsed_summary.json` | summary |
| 3-D 1.17 curated / 1.19 all-paper / 1.10 include-standard | `coverage_3d_models.csv` (all three); `coverage_3d_model.csv` (archived curated); `results/post_audit/three_d_models.json` | recomputed (`three_d_models.py`); point estimates match; packaged CIs differ in the last digit |
| All-paper 1.34 (1.11–1.60) | `coverage_matrix_all_paper.csv`; `results/post_audit/all_paper_audit.json` | recomputed (`all_paper_audit.py`) |
| All-paper block factor 1.42 (1.26–1.60) | `study_level_model.json` (`all_paper`, 1.421, 1.262–1.599); `all_paper_audit.json` note | recomputed (`supplementary_checks.py`); archived 1.40 (1.25–1.58) noted in `all_paper_audit.json` |
| Over-marking perturbation 1.31–1.34 and 1.07–1.09; 19–25% rows 1.20–1.28 and 1.05–1.11 | `presence_misclassification_upper.csv` | recomputed (`perturbation_upper.py`) |
| 11.1% over-marking rate | `presence_misclassification_summary.csv` | derived |
| Balance: volume block 1 unique / Hamming 0 vs matched 5 / 9.6; density 0.205 vs 0.205; coherence Hamming 3.0 vs 1.3 | `balance_diagnostics.csv` | recomputed (`balance_diagnostics.py`) |
| Flagged-study descriptors B063/B166/B201/B102/B213/B208 | `flagged_studies.csv` | derived (`flagged_studies.py`) |

## Synthetic validation and calibration

| Quantity | File | Status |
|---|---|---|
| H0 1.58 / 0.995; H1 4.66; 90% above 2; percentile 98.3 | `results/post_audit/simulation_validation.json` | recomputed (`simulation_validation.py`) |
| 1% / 5% flips: 0.96 / 1.34; 33% / 0% | `results/post_audit/multiconfig_sensitivity.json` | recomputed (`multiconfig_sensitivity.py`) |
| Multi-configuration stress: coherent H0 2.33, 62% >2; coherent-extreme 5.23, 100%; distinct-extreme 2.32, 56% | `results/post_audit/multiconfig_h1.json` | recomputed (`multiconfig_h1.py`) |
| Calibration panels (SI) | `calibration_*.csv`, `sim_calibration_*.csv` | summary |
| Exact-subset baseline | `review_findings.json` | summary |
| Exact-subset descriptive means (4.52/6.47 rows; 0.58/0.74 duplicate fraction; 0.155/0.223 density) | `tail_audit.json` (`exact_subset`) | recomputed (`supplementary_checks.py`) |
| Hamming distribution (54 pairs; 16/11/5 at 1/2/3 bits; 32 ≤3) | `tail_audit.json` (`hamming`) | recomputed (`supplementary_checks.py`) |
| Tail proportions (collapsed 19/117 >2; density-matched 14/117 >2) | `tail_audit.json` (`tail`) | recomputed (`supplementary_checks.py`) |
| Matched-draw reference null by configuration count: k=1 q95 4.28, 16/97 above 2 vs 15.8 expected; k≥2 q95 2.71, 3/20 above 4 vs 0.15 expected | `results/post_audit/tail_null.json` | recomputed (`tail_null.py`) |
| Common-evaluation recomputation 21/117 above 2, 13/117 above 3 | `tail_null.json` (`common_evaluation_sensitivity`) | recomputed (`tail_null.py`) |
| Exact-subset block factor 0.88 (0.75--1.02); top-25 -0.006 and Spearman -0.00010 differences; PC2 row-level 1.44, 49.6/26.5/23.9 | `results/post_audit/table_checks.json` | recomputed (`table_checks.py`) |
| Per-study ratios reproduce exactly from the matrix (per-study \|diff\| = 0, corr 1.000) | `baseline_*.csv`, `collapsed_*.csv` | recomputed (`rebuild_events.py`) |
| Estimator: block arm median drift on its own retained rows over the median of 100 matched draws; common-evaluation variant reported separately | `common.py` (`median_drift`, `common_ratio`) | derived |
| Coherence-matched control (median 1.01; B063 8.95, B166 7.29, B201 3.40) | `coherence_control.json`; `tail_audit.json` (`coherence_control`) | recomputed (`coherence_control.py`) |
| Two-level bootstrap (full 1.37, 1.13–1.57; collapsed 1.03, 0.89–1.19) | `tail_audit.json` (`two_level_bootstrap`) | recomputed (`supplementary_checks.py`) |
| Top-12 tail decomposition (full/collapsed/density/composition/Hamming) | `tail_decomposition.csv` | recomputed (`supplementary_checks.py`) |

## Reproducing

```
python3 code/run_all.py                 # every analysis + self-check (~22 min)
python3 code/run_all.py --quick         # fast end-to-end check (~2 min)

python3 code/verify_package.py          # check every deposited value (~10 s)
python3 code/panel_decomposition.py     # ~60 s
python3 code/pc2_density_check.py       # ~15 s
python3 code/core_revision_checks.py    # ~60 s
python3 code/simulation_validation.py   # ~6 min
python3 code/multiconfig_sensitivity.py # ~12 min
python3 code/coherence_control.py        # ~1 min
python3 code/three_d_models.py           # ~7 min
python3 code/supplementary_checks.py    # ~2 min
python3 code/tail_null.py               # ~10 s
python3 code/rebuild_events.py          # ~20 s
```

The scripts write to `results/post_audit/` (and `results/core_revision/` for
the core checks; `results/rebuild/` for the event-table rebuild). The committed
JSONs are the published outputs. `rebuild_events.py` does not overwrite the
deposited event tables; it writes a rebuilt copy and reports the difference.
