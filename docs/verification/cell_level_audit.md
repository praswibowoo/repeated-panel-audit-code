# Cell-level coverage audit — frame and protocol

**Status:** frame drawn; automated source-text triage and targeted snippet review complete.
**Frame:** `source/manuscript/ees/reproducibility/cell_level_sample.csv`  
**Triage:** `cell_level_triage.csv`; coded pass: `cell_level_coded.csv`  
**Drawer / triage:** `source/code/cell_level_audit.py`, `source/code/cell_level_text_audit.py`  
**Date:** 2026-11-16

## Why this exists

The Stage-A audit checked 117 claims (39 papers × 3), not a random sample of
coverage cells. The paper therefore reports a claim-level residual rate, not a
cell-level error rate. This frame supplies a cell-level audit.

## Design

- 351 cells: three per paper for all 117 curated papers.
- 256 cells with matrix value 1 (present / NE) and 95 with matrix value 0
  (blank / NR).
- Two present cells and one blank cell per paper where available; remaining
  cells fill from the paper's rows.
- Seed 20261116; reproducible from `coverage_matrix.csv`.

## Coding and triage semantics

The intended manual protocol for each sampled cell was:

1. Open the paper at the cited scenario/table.
2. Set `human_value` to 1 if the parameter is reported or examined-absent
   (Y/NE), 0 if not reported (NR), or `NA` if the paper does not allow a
   decision.
3. Set `match` to `yes`, `no`, or `undecidable`.
4. Record the page/table location or reason in `notes`.

The deposited pass combined automatic whole-paper text triage with targeted
snippet review. Of 351 rows, 301 were automatic high-confidence triage and 50
were snippet-review cases. The historical `coding=manual_snippet` label does
not mean that all 351 cells were manually page-checked. Automatic rows carry
`human_value=0` as a placeholder, not as a human rejection.

## Source-text triage results

- 231/256 present cells had a whole-paper PDF line with a numeric alias.
- 70/95 blank cells had no parameter line in that text search.
- 50 cells required snippet review: 19 present cells confirmed, 6 undecidable;
  23 blank cells confirmed, and 2 apparent under-marked cells were flagged
  (B028 pH, B084 Cu).
- Of 345 decidable triage results, 343 matched (99.4%) and 2 were flagged
  (0.6%); 6 remained undecidable.

B084 Cu is a scenario-inapplicable text match: Cu occurs in waterlogged-soil
Table 2, whereas the B084 matrix rows are water scenarios from Table 1. The
matrix value Cu=0 is retained, and the mismatch is annotated in
`cell_level_coded.csv`. B028 pH remains an under-marked cell, but B028 is
outside the primary corpus.

The 231 text-supported present cells were not page-checked individually. Treat
99.4% as automated text-triage agreement plus targeted review, not as an
independent human page-level error rate.

## Gate

- Target: ≥95% cell agreement (≥334/351).
- If agreement is 90–95%, correct the disagreeing cells, re-audit a fresh 100-cell
  sample, and report both.
- If agreement is <90%, stop and re-extract the affected parameter families
  before using the coverage matrix for the audit.

## Reporting

Report:

- cell-level agreement with an exact 95% CI;
- agreement by matrix value (present vs blank), because over-marking and
  under-marking have different effects;
- agreement by parameter family, where the family map is available;
- the number of undecidable cells.

The manuscript reports this as automated text-triage agreement plus targeted
review, not as a cell-level error rate. The claim-level Stage-A result and the
clustered perturbation remain separate evidence.
