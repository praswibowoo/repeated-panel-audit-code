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

## Import primary-only results

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
