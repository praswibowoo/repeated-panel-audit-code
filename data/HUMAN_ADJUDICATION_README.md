# Human duplicate-pair adjudication package

## Primary-only workflow

Send the primary coder **only**:

- `duplicate_pair_human_adjudication_primary_simple.xlsx`

Or, if Excel is not needed:

- `duplicate_pair_human_adjudication_primary_simple.csv`

The simple primary file has eight columns:

| Column | Fill? | Purpose |
|---|---|---|
| `pair_id` | No | Click to open source PDF in Excel |
| `scenario_a` | No | First scenario |
| `scenario_b` | No | Second scenario |
| `relation` | Yes | `same`, `different`, or `undecidable` |
| `evidence` | Yes | Page/table/figure plus parameter differences or reason |
| `correction` | If needed | Exact proposed matrix correction; otherwise blank |
| `coder` | Yes | Coder name |
| `date` | Yes | `YYYY-MM-DD` |

The primary file contains 56 priority pairs and no matrix class, Hamming distance, AI relation, priority reason, or answer key.

Current submission status (2026-11-27): all 56 rows have `relation`, `evidence`, `coder`, and `date` populated. Strict structural import passes. Coordinator review remains required for 39 flagged rows; see `duplicate_pair_human_adjudication_coordinator_notes_2026-11-27.md`.

A proposed source-based coordinator package is also available: 53 `same`, 3 `undecidable`, 19 changed primary labels independently rechecked, and 42 pending cell corrections. It is not human-approved. Start with `duplicate_pair_coordinator_review_memo_2026-11-27.md`.

Do not send the coordinator workbook/key, AI source-review files, or prior-evidence files before coding is complete.

## Optional independent second coder

If a second coder is used later, send only:

- `duplicate_pair_human_adjudication_second_only.xlsx`
- or `duplicate_pair_human_adjudication_second_blind.csv`

The second file contains 62 pairs: the 56 priority pairs plus 6 QC pairs.

## Coding rule

For each pair, work from the source paper:

- `same`: identical examined-parameter suite.
- `different`: at least one parameter differs.
- `undecidable`: source cannot support a decision.

Examined or examined-absent = `1`; not reported = `0`. Normalize parameter names to the manuscript's 44-parameter schema.

Fill only:

- `relation`
- `evidence`
- `correction` — optional
- `coder`
- `date`

Do not fill `human_match`; the coordinator computes it after unblinding. Do not edit the coverage matrix directly.

## Process a partially completed workbook

Extract the `Primary` sheet:

```bash
python3 code/extract_simple_adjudication_xlsx.py \
  duplicate_pair_human_adjudication_primary_simple.xlsx \
  primary_completed.csv
```

Process a partial file without rejecting missing rows or blank coder/date/evidence fields:

```bash
python3 code/import_duplicate_adjudication.py \
  --primary primary_completed.csv \
  --allow-partial \
  --allow-missing-metadata
```

This produces provisional results and flags missing evidence, metadata, correction-format problems, matrix disagreements, AI disagreements, and prior-human-evidence conflicts. No labels are finalized and the coverage matrix is never edited. Excel numeric date serials are converted to `YYYY-MM-DD` during extraction.

Build the all-row processing report and flagged-row subset:

```bash
python3 code/build_adjudication_processing_report.py \
  --primary primary_completed.csv \
  --results duplicate_pair_human_adjudication_results.csv \
  --date YYYY-MM-DD
```

## Import completed primary-only results

Save the completed `Primary` sheet as CSV UTF-8, then run:

```bash
python3 code/import_duplicate_adjudication.py \
  --primary <completed_primary.csv>
```

The importer writes:

- `duplicate_pair_human_adjudication_results.csv`
- `duplicate_pair_human_adjudication_summary.json`
- `duplicate_pair_audit_frame_human_filled.csv`
- `duplicate_pair_coordinator_resolution_template.csv`
- correction and configuration-impact templates

Primary-only labels are **provisional** until coordinator review. Fill the resolution template, then rerun:

```bash
python3 code/import_duplicate_adjudication.py \
  --primary <completed_primary.csv> \
  --resolution <completed_resolution.csv>
```

The importer never edits `coverage_matrix.csv`.

## Import with an optional second coder

```bash
python3 code/import_duplicate_adjudication.py \
  --primary <completed_primary.csv> \
  --second <completed_second.csv>
```

Coder disagreements are flagged for coordinator resolution.
