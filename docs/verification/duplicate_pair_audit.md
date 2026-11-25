# Duplicate-pair audit — frame and protocol

**Status:** frame drawn; human source-text adjudication pending.  
**Frame:** `manuscript/ees/reproducibility/duplicate_pair_audit_frame.csv`  
**Generator:** `code/duplicate_pair_audit.py`  
**Seed:** 20261125

## Purpose

The primary exposure in the manuscript is whether two scenario rows within one paper share the same binary coverage configuration. The existing 351-cell audit estimates targeted cell agreement but does not directly estimate duplicate-pair classification.

This frame samples pairs of rows, not individual cells:

- 40 pairs coded as identical configurations by the deposited matrix;
- 40 random pairs coded as distinct configurations;
- 20 nearest distinct pairs, emphasizing Hamming distance <= 3 where available.

The frame contains 100 pairs from 48 papers.

## Human coding

For each pair:

1. Open the source paper and identify both scenario rows using the deposited scenario metadata and source tables.
2. Code `human_relation` as:
   - `same`: the scenarios report/examine the same parameter suite under the manuscript coding rule;
   - `different`: at least one parameter differs between the scenarios;
   - `undecidable`: the paper does not support a decision.
3. Code `match` as `yes`, `no`, or `undecidable` relative to `matrix_hamming = 0` versus `matrix_hamming > 0`.
4. Record the page/table and any parameter-level discrepancy in `notes`.

Do not consult the matrix row vectors before completing source-text coding.

## Reporting after adjudication

Report separately:

- sensitivity and specificity for duplicate classification;
- agreement for identical, random-distinct, and near-distinct strata;
- number of undecidable pairs;
- whether any corrected pair changes a paper's configuration count.

Until adjudication is complete, this frame is a deposited validation resource, not evidence of corpus-wide duplicate-classification accuracy.
