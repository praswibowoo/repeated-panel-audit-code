# Revision audit — 2026-11-25 (historical)

> Superseded by `REVISION_2026-11-26_AUDIT.md`. Retained for provenance.

Release: `v1.7.0-2026-11-25`.

## Claim hierarchy implemented

- Primary: full-fit A−Bblock control-geometry contrast.
- Secondary: A−C protocol contrast; it changes both fit weighting and control geometry.
- Single-configuration studies with an exact-size donor provide the clean unit-matched comparison.
- Multi-configuration studies show a descriptive control effect but no clean configuration-count-and-coherence-matched block control.
- H is an exploratory donor-study control, not a validated coherence match.
- Configuration collapse is recommended only for a configuration-weighted target.

## Material findings corrected

- Removed the unsupported claim that the control effect is confined to single-configuration studies.
- Disclosed that Bblock is available for 92/97 single-configuration studies; the five excluded studies have a median A−C of 1.12.
- Reported multi-configuration A−Bblock (0.23; 19/20 positive in PCA; 20/20 positive in fixed PCoA).
- Relabeled H and reported achieved Hamming imbalance.
- Made the protocol table target-dependent.

## New analyses

- `pcoa_fixed.py`: fixed-set 2-D Jaccard PCoA with out-of-fit projection.
- `simulation_fixed.py`: fixed-set clustered, planted, and independent-row benchmarks.
- Fixed exclusions for B208 and for 13 unsure records plus two substitutes.
- `duplicate_pair_audit.py`: frozen 100-pair duplicate-classification frame; human adjudication pending.
- `control_balance_fixed.py`: Bblock density, recurrence, water, Hamming, and missing-donor summaries.

## Active fixed PCA results

- A−Bblock, 112: 0.26 (0.22–0.32), 90% positive.
- Single A−Bblock, 92: 0.27 (0.22–0.36), 89% positive.
- Multi A−Bblock, 20: 0.23 (0.13–0.28), 95% positive.
- A−C, 117: 0.29 (0.19–0.35).
- Multi A−C, 20: 0.12 (−0.01–0.29).

## Active fixed PCoA results

- A−Bblock, 112: 0.29 (0.23–0.34), 96% positive.
- Single A−Bblock, 92: 0.31 (0.24–0.41), 96% positive.
- Multi A−Bblock, 20: 0.23 (0.21–0.31), 100% positive.
- A−C, 117: 0.34 (0.20–0.45).
- Multi A−C, 20: 0.13 (−0.56–0.32).

## Fixed RMS sensitivity

- A−Bblock, 112: 0.29 (0.23–0.38), 90% positive.
- Single A−Bblock, 92: 0.32 (0.26–0.46), 89% positive.
- Multi A−Bblock, 20: 0.21 (0.12–0.30), 95% positive.
- A−C, 117: 0.30 (0.21–0.44).

The RMS sensitivity preserves the direction of the primary median-drift control-geometry result.

## Fixed synthetic results

- Repeated configurations: A 1.557 (1.283–1.813), C 0.979 (0.909–1.089).
- Independent rows: A 0.989 (0.887–1.086), C 0.981 (0.876–1.093).
- Planted collapsed ratio: 3.99 (1.39–11.09); above two in 90%; top-ranked in 47%.

## Checks

- Python compilation: pass.
- `check_ees.py`: pass.
- `check_numbers.py`: pass.
- `check_fixed_revision.py`: pass.
- `verify_package.py`: pass.
- Main and SI LaTeX builds: pass.
- Publication SI reduced to Figures S1–S2 and Tables S1–S6.

## Independent manuscript audit

A second reviewer checked the revised claim hierarchy, donor availability, H labeling, PCoA/synthetic values, SI references, and conclusion scope. Seven issues were returned; all were resolved in the final build:

- explicit fixed-set two-dimensional PCA/PCoA scope in the conclusion;
- unambiguous single-configuration wording for the 92-study unit-matched result;
- reduced-corpus evaluation wording in Table S6;
- aggregation labels in Table S3 Panel A;
- density-matched source added to the SI source index;
- PCA/PCoA expanded at first use;
- Spearman correlation specified for the per-study rank comparison.

## Surgical reviewer-response pass

- Main-text robustness section now contains only fixed-set PCoA, fixed RMS, and fixed corpus-exclusion results; own-row sensitivities remain in SI Table S5.
- Median event drift is explicitly justified as a robust event-level summary, with RMS reported separately.
- The covariance matrix is defined and the random-deletion expectation is stated exactly; the deterministic block perturbation is contrasted with the isotropic random-deletion expectation.
- The extraction-audit paragraph is condensed; granular metrics remain in SI Table S1.
- Multi-configuration matching is framed as combinatorial sparsity, while H remains exploratory.
- Table 1 includes the 14-row exclusion arithmetic; Figure 1 explains the 3–12 colorbar range; SI Figure S2 explains use of the full-extraction ordination.

## Surgical-audit corrections

A focused second audit returned six issues; all are resolved in the final build:

- archived matcher B results removed from the main text and retained only in Table S2;
- SI contents wording reconciled with the labeled legacy/own-row rows;
- the covariance expectation qualified as an all-row exchangeability null, not design A's nonfocal donor expectation;
- Figure 1 given a common 1–18 color scale including the one-row boundary study;
- synthetic interpretation narrowed to exact repetition without a planted outlier, without claiming separation from between-study pattern heterogeneity;
- regulatory-row exclusion wording limited to inferential ordinations, with Figure S2 identified as descriptive provenance.

## Subsection consolidation

The manuscript was reorganized from 17 to nine subsections:

- 2.1 Units and fixed evaluation;
- 2.2 Deletion designs and estimands;
- 2.3 Mechanism and synthetic benchmarks;
- 4.1 Control geometry and protocol contrast;
- 4.2 Mechanism and null benchmarks;
- 4.3 Robustness and scope of per-study ratios;
- 5.1 Principal finding and contribution;
- 5.2 Reporting protocol;
- 5.3 Limitations.

The Application section no longer uses subsections. Bold lead-ins distinguish the single- and multi-configuration strata within 4.1. A regex audit found no paired section references and no hardcoded main-section numbers in the SI.

## Repository split

- `p2-deletion-audit-code/` now contains the synchronized analysis code, binary matrices, audit frames, result JSONs, generated figures, provenance documentation, and its own manifest/checksums.
- `p2-deletion-audit/source/` is the canonical editable manuscript tree. The generated `release/2026-11-25/` duplicate was removed to keep the manuscript repository simple.
- The manuscript source was compiled successfully with pdflatex/bibtex; main and SI produced 20 and 8 pages without undefined references or overfull boxes.

## Remaining human tasks

1. Independently adjudicate the duplicate-pair audit frame. Until completed, the manuscript makes no corpus-wide duplicate-classification accuracy claim.
2. Publish the code/data repository using `RELEASE_UPLOAD.md`, then submit the manuscript files directly from `p2-deletion-audit/source/manuscript/ees/`.
3. Decide whether the extraction-model name/version can be disclosed; the manuscript currently states that the identifier is not disclosed.
