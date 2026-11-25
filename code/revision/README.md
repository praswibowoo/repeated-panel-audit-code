# Revision recomputations

These scripts reproduce the new checks added in the 2026-11-22 revision.

| Script | Purpose | Output used in |
|---|---|---|
| `hamming_audit.py` | Own-row collapsed audit at within-paper Hamming thresholds 0, 1, 2, 3. Connected-components merge, medoid representative. | SI Table S23 |
| `dim_audit.py`, `dim3_variants.py` | Own-row full/collapsed ratios at 2–5 dimensions, 100 matched draws; 3-D alignment/seed variants. | Cross-check of SI Table S16; the 3-D full value is implementation-sensitive (1.09–1.21) and the row is omitted from the main text. |
| `exact_subgroup_check.py` | Exact-subgroup paired difference with and without the 7-paper shared-pattern cluster. | Main text Section 4.2; SI Table S22 note |

## Validation

- The block-drift implementation reproduces the deposited event table exactly for B001: `0.0005917790066305032`.
- The own-row aggregate reproduces the archived full/collapsed medians: 1.3628 / 1.0390 from `baseline_block.csv`, `baseline_matched.csv`, `collapsed_block.csv`, `collapsed_matched.csv`.
- The Hamming t=0 baseline gives 1.02 (0.90–1.17), 0.02 below the archived 1.04; the difference is the matched-draw seed. The t>0 values are 0.98 / 0.96 / 0.96.
- The dimension recomputation matches 2-D closely (1.366/1.023 vs 1.363/1.039). The 3-D value is implementation-sensitive: row-normalized alignment with seed 7 gives 1.090 (the archived value), while unnormalized alignment gives 1.138--1.207 across seeds 42/7/123 and no-centering gives 1.206--1.238. The archived 1.09 is therefore recoverable, but the value is not stable across reasonable implementations. The main text omits the 3-D row; SI Table S16 keeps it as an audit trail.

## Reproduce

```bash
cd manuscript/ees
python3 reproducibility/revision/hamming_audit.py
python3 reproducibility/revision/dim_audit.py
python3 reproducibility/revision/exact_subgroup_check.py
```
