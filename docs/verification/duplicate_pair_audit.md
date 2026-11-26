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

Thus no matrix-identical pair was judged different by the AI-assisted review, but 16 matrix-distinct pairs were judged to share the same examined-parameter suite. Eight of those 16 conflict with prior P1 human-verified cell corrections already incorporated in the P2 matrix. They are therefore AI-flagged potential false-distinct pairs, not confirmed matrix errors. Pair-level human adjudication remains pending.

## Prepared human-adjudication package

Run:

```bash
python3 code/prepare_duplicate_adjudication.py
```

The package separates blind coder files from coordinator evidence:

- Primary coder: 56 pairs = all 38 matrix-identical pairs + all 16 matrix-distinct/AI-same pairs + all 3 AI-undecidable pairs, with one overlap counted once. Send only `duplicate_pair_human_adjudication_primary_only.xlsx` or the primary blind CSV.
- Independent second coder, if used: the same 56 pairs + 6 randomly selected agreed-distinct QC pairs = 62 pairs. Send only `duplicate_pair_human_adjudication_second_only.xlsx` or the second blind CSV.
- Combined coder workbook: `data/duplicate_pair_human_adjudication_coder.xlsx`; no matrix class, Hamming distance, AI relation, or priority reason is shown.
- Coordinator workbook/key: `data/duplicate_pair_human_adjudication_coordinator.xlsx` and `duplicate_pair_human_adjudication_coordinator_key.csv`.
- Prior P1 human corrections: `data/prior_human_cell_corrections.csv`; pair-level evidence map: `data/prior_human_pair_evidence.csv`.

Prior human cell corrections affect 13 pairs: 8 conflict with an AI `same` label and 5 are consistent with an AI `different` label. They are evidence only and do not replace pair-level human labels.

After coding, validate and import with:

For a primary-only workflow:

```bash
python3 code/import_duplicate_adjudication.py \
  --primary <completed_primary.csv>
```

Review the generated coordinator resolution template, then rerun with `--resolution <completed_resolution.csv>`.

If an independent second coder is used:

```bash
python3 code/import_duplicate_adjudication.py \
  --primary <completed_primary.csv> \
  --second <completed_second.csv>
```

The importer never edits the coverage matrix. It writes a proposed human-filled frame, a results table, and a summary. Matrix corrections require a separate approved long-form correction log.

## Reporting after human adjudication

Report separately:

- sensitivity and specificity for duplicate classification;
- agreement for identical, random-distinct, and near-distinct strata;
- number of undecidable pairs;
- whether any corrected pair changes a paper's configuration count.

Until human adjudication is complete, the AI-assisted review is supporting evidence only, not a corpus-wide accuracy estimate. The reported primary estimates are not altered by the review labels.
