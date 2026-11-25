# Cell-level coverage audit — frame and protocol

**Status:** frame drawn; source-text check complete.  
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

## Coding

For each row in `cell_level_sample.csv`:

1. Open the paper at the cited scenario/table.
2. Set `human_value` to 1 if the parameter is reported or examined-absent
   (Y/NE), 0 if not reported (NR), or `NA` if the paper does not allow a
   decision.
3. Set `match` to `yes`, `no`, or `undecidable`.
4. Record the page/table location or the reason in `notes`.

Do not consult the matrix value before coding the paper.

## Source-text check

- 231/256 present cells have a direct PDF line with a numeric alias.
- 70/95 blank cells have no parameter line.
- 50 cells required snippet review: 19 present cells confirmed, 6 undecidable;
  23 blank cells confirmed, 2 show reported values and are under-marked
  (B028 pH, B084 Cu).
- Of 345 adjudicable cells, 343 match (99.4%) and 2 are under-marked (0.6%);
  6 remain undecidable.

The 231 text-supported present cells were not page-checked one by one. Treat
99.4% as an upper bound, not a full page-level error rate.

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

The current manuscript should not claim a cell-level error rate until this
frame is coded. The claim-level Stage-A result and the clustered perturbation
remain the interim evidence.
