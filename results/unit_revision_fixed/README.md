# Current fixed-evaluation audit outputs

Generated from `data/coverage_matrix_primary.csv` unless a file is explicitly
labeled full-curated. Primary focal claims use single-configuration studies
only; multi-configuration studies are background.

## Evaluation and estimator

For each focal study, every nonfocal matrix-defined within-study configuration
is evaluated. The set is fixed before control draws. Configurations deleted by
a control are projected into the reduced solution.

Every design uses `R_s = block_drift_s / median(control_drifts_s)`. Raw block
drifts and control-drift lists are deposited alongside per-study estimates.

## Designs

- **A:** full-fit row-count control; Monte Carlo.
- **Bstudy:** full-fit exact-size whole single-configuration donor studies; exhaustive and primary on eligible single-configuration foci.
- **Bblock:** full-fit exact-size donor configurations; exhaustive and nested around Bstudy.
- **C:** collapsed-fit configuration-count control; Monte Carlo.
- **B:** archived greedy exact-volume whole-configuration matcher; Monte Carlo provenance sensitivity.
- **H:** removed from current code and outputs.

## Files

- `common_contrast.json`: current 2-D primary audit, contrasts, strata, donor-pool size distributions, nested-pool diagnostics, per-study medians, block drifts, and control-drift lists.
- `fixed3d_contrast.json`: current fixed-set 3-D PCA sensitivity.
- `pcoa_contrast.json`: current fixed-set Jaccard PCoA sensitivity with exhaustive Bstudy/Bblock.
- `rms_sensitivity.json`: current fixed-set PCA sensitivity using RMS event drift.
- `control_balance.json`: current Bstudy/Bblock balance, donor composition, and missing-donor studies.
- `sensitivity_full_curated.json`: current estimator applied to the full 117-paper curated matrix.
- `manuscript_values.json`: rounded values rendered from current outputs.
- `strata_sensitivity.csv`: flat exploratory block-size results across all fixed sensitivities; includes both all-focal and shared-Bstudy-set A medians.
- `donor_pool_by_focal.csv`: per-focal Bstudy/Bblock pool sizes and nesting.
- `convergence_500.json`: separate 500-draw run used only for convergence checking.
- `convergence_100_vs_500.json` and `.csv`: comparison summary.
- `sensitivity_no_B208.json`, `sensitivity_no_unsure_substitutes.json`: legacy full-curated exclusion outputs; provenance only, not current primary results.

The 100-draw outputs remain canonical. The 500-draw run verifies stability and is
not substituted for the reported primary estimates.
