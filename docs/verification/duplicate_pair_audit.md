# Duplicate-pair audit — frame, protocol, and AI-assisted source review

**Status:** independent AI-assisted blinded source review complete; human source-text adjudication pending.

**Frame:** `data/duplicate_pair_audit_frame.csv`

**Source-review labels:** `data/duplicate_pair_source_review.csv`

**Generator:** `code/duplicate_pair_audit.py`

**Seed:** 20261125

## Purpose

The primary exposure in the manuscript is whether two scenario rows within one paper share the same binary coverage configuration. The existing 351-cell audit estimates targeted cell agreement but does not directly estimate duplicate-pair classification.

The frozen frame contained 100 records representing 83 unique unordered pairs from 48 papers:

- 38 unique matrix-identical pairs;
- 32 unique random-distinct pairs;
- 13 unique near-distinct pairs.

Repeated records in the original frame are retained for provenance but are not counted twice in the source-review summary.

## Human coding protocol

For each pair:

1. Open the source paper and identify both scenario rows using the deposited scenario metadata and source tables.
2. Code `human_relation` as:
   - `same`: the scenarios report/examine the same parameter suite under the manuscript coding rule;
   - `different`: at least one parameter differs between the scenarios;
   - `undecidable`: the paper does not support a decision.
3. Code `match` as `yes`, `no`, or `undecidable` relative to `matrix_hamming = 0` versus `matrix_hamming > 0`.
4. Record the page/table and any parameter-level discrepancy in `notes`.

Do not consult the matrix row vectors before completing source-text coding.

## Independent AI-assisted source review

A separate AI-assisted reviewer worked from the source texts/PDFs in the P1 corpus repository without access to the coverage matrix, parameter vectors, audit strata, or Hamming values. This was **not human adjudication**.

Results across 83 unique unordered pairs:

- `same`: 53;
- `different`: 27;
- `undecidable`: 3.

Comparison with the matrix after blinding was removed:

| Matrix class | Review same | Review different | Review undecidable |
|---|---:|---:|---:|
| Identical (n=38) | 37 | 0 | 1 |
| Distinct (n=45) | 16 | 27 | 2 |

Thus no matrix-identical pair was judged different, but 16 matrix-distinct pairs were judged to share the same examined-parameter suite. Those 16 pairs occurred only in multi-configuration studies. The matrix may therefore split some true repetitions; parameter-level correction requires human adjudication.

## Reporting after human adjudication

Report separately:

- sensitivity and specificity for duplicate classification;
- agreement for identical, random-distinct, and near-distinct strata;
- number of undecidable pairs;
- whether any corrected pair changes a paper's configuration count.

Until human adjudication is complete, the AI-assisted review is supporting evidence only, not a corpus-wide accuracy estimate. The reported primary estimates are not altered by the review labels.
