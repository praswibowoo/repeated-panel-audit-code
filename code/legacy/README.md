# Legacy pipeline scripts

These four scripts produced the summary tables that are deposited in `data/`.
They are **not runnable from this repository**: they import modules from the
full analysis pipeline (`ordination-stability-audit`) and, for
`revision_layers.py` and `clean_primary_audit.py`, require the restricted
value layer that is not part of this package.

They are kept for provenance only. The outputs they produced are committed, so
every reported number can be checked without rerunning them.

| Script | Requirement |
|---|---|
| `revision_layers.py` | `docs/extraction/stageA` and the restricted `stageB/matrix_values_v2.csv` |
| `clean_primary_audit.py` | `ees_revision_checks`, `ees_rank_matched`, `experiment_H_volumematch` |
| `ees_post_audit_extra.py` | `ees_post_audit`, `experiment_H_volumematch` |
| `ees_revision_checks.py` | `experiment_H_volumematch`, `ees_rank_matched` |
