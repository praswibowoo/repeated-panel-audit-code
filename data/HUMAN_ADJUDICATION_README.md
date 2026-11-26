# Human duplicate-pair adjudication package

## Files to send coders

- `duplicate_pair_human_adjudication_coder.xlsx`
  - `Primary` sheet: 56 priority pairs.
  - `Second` sheet: 62 pairs for independent second coding.
- Or use the blind CSVs:
  - `duplicate_pair_human_adjudication_primary_blind.csv`
  - `duplicate_pair_human_adjudication_second_blind.csv`

Coder files contain no matrix class, Hamming distance, AI relation, or priority reason.

## Coordinator-only files

- `duplicate_pair_human_adjudication_coordinator.xlsx`
- `duplicate_pair_human_adjudication_coordinator_key.csv`
- `prior_human_pair_evidence.csv`
- `prior_human_cell_corrections.csv`
- `duplicate_pair_adjudication_manifest.json`

Do not send coordinator files to coders before independent coding is complete.

## Coding rule

For each pair, work from the source paper:

- `same`: identical examined-parameter suite.
- `different`: at least one parameter differs.
- `undecidable`: source cannot support a decision.

Examined or examined-absent = `1`; not reported = `0`. Normalize parameter names to the manuscript's 44-parameter schema.

Record page/table/figure locators and parameter-level differences. The coordinator computes `human_match` against the matrix after blinding is removed. Do not edit the coverage matrix directly.

## Priority design

- Primary: all 38 matrix-identical pairs + all 16 matrix-distinct/AI-same pairs + all 3 AI-undecidable pairs, with one overlap counted once = 56 pairs.
- Second coder: same 56 + 6 deterministic agreed-distinct QC pairs = 62 pairs.
- Prior P1 human cell corrections affect 13 pairs; 8 conflict with AI `same` labels. These corrections are evidence only, not pair-level human labels.

## Import completed files

```bash
python3 code/import_duplicate_adjudication.py \
  --primary <completed_primary.csv> \
  --second <completed_second.csv>
```

The importer validates assignments and required fields, compares coders, and writes:

- `duplicate_pair_human_adjudication_results.csv`
- `duplicate_pair_human_adjudication_summary.json`
- `duplicate_pair_audit_frame_human_filled.csv`
- correction and configuration-impact templates

It never edits `coverage_matrix.csv`.
