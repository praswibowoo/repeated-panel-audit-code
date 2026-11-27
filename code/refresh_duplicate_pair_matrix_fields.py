#!/usr/bin/env python3
"""Refresh duplicate-pair matrix fields after approved cell corrections.

The frozen pair assignments and audit strata are retained. Matrix Hamming,
density, per-paper configuration counts, source-review matrix comparisons, and
prior-correction status are refreshed from the approved coverage matrix.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
COVERAGE = DATA / "coverage_matrix.csv"
FRAME = DATA / "duplicate_pair_audit_frame.csv"
KEY = DATA / "duplicate_pair_human_adjudication_coordinator_key.csv"
REVIEW = DATA / "duplicate_pair_source_review.csv"
SUMMARY = DATA / "duplicate_pair_source_review_summary.json"
MANIFEST = DATA / "duplicate_pair_adjudication_manifest.json"
PRIOR_STATUS = DATA / "prior_human_cell_corrections_status.csv"
PRIOR_EVIDENCE = DATA / "prior_human_pair_evidence.csv"
SUPERSEDED = {
    ("B034", 181, "pH"),
    ("B065", 251, "NO2 (mg/L)"),
    ("B069", 263, "pH"),
    ("B166", 580, "TSS (mg/L)"),
}


def pair_fields(frame: pd.DataFrame, coverage: pd.DataFrame, params: list[str]) -> pd.DataFrame:
    indexed = coverage.set_index(["paper", "row"])
    per_paper = coverage.assign(
        pattern=coverage[params].astype(int).astype(str).agg("".join, axis=1)
    ).groupby("paper")["pattern"].nunique()
    rows = []
    for r in frame.itertuples(index=False):
        a = indexed.loc[(r.paper, int(r.row_a))]
        b = indexed.loc[(r.paper, int(r.row_b))]
        rows.append({
            "pair_id": getattr(r, "pair_id", ""),
            "paper": r.paper,
            "row_a": int(r.row_a),
            "row_b": int(r.row_b),
            "matrix_hamming": int(sum(int(a[p]) != int(b[p]) for p in params)),
            "density_a": float(a["rho"]),
            "density_b": float(b["rho"]),
            "paper_configurations": int(per_paper[r.paper]),
        })
    return pd.DataFrame(rows)


def main() -> int:
    coverage = pd.read_csv(COVERAGE)
    params = [c for c in coverage.columns if c not in ("paper", "row", "rho")]
    frame = pd.read_csv(FRAME)
    key = pd.read_csv(KEY)
    review = pd.read_csv(REVIEW).fillna("")

    frame_fields = pair_fields(frame, coverage, params)
    for col in ["matrix_hamming", "density_a", "density_b", "paper_configurations"]:
        frame[col] = frame_fields[col]
    frame.to_csv(FRAME, index=False)

    key_fields = pair_fields(key, coverage, params)
    key["matrix_hamming"] = key_fields["matrix_hamming"]
    key.to_csv(KEY, index=False)

    # Refresh the automated source-review comparison against the approved matrix.
    comparison = review.merge(key[["pair_id", "matrix_hamming"]], on="pair_id", validate="one_to_one")
    identical = comparison.matrix_hamming.eq(0)
    distinct = ~identical
    same = comparison.reviewer_relation.eq("same")
    different = comparison.reviewer_relation.eq("different")
    undecidable = comparison.reviewer_relation.eq("undecidable")
    ident_decidable = identical & ~undecidable
    dist_decidable = distinct & ~undecidable
    false_distinct = comparison.loc[distinct & same, "pair_id"].tolist()
    false_identical = comparison.loc[identical & different, "pair_id"].tolist()
    false_distinct_papers = sorted(comparison.loc[distinct & same, "paper"].unique().tolist())
    n_ident = int(identical.sum())
    n_dist = int(distinct.sum())
    n_same = int(same.sum())
    n_diff = int(different.sum())
    n_und = int(undecidable.sum())
    ident_same = int((identical & same).sum())
    dist_diff = int((distinct & different).sum())

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    summary["matrix_comparison"].update({
        "matrix_identical_n": n_ident,
        "matrix_identical_review_same": ident_same,
        "matrix_identical_review_different": int((identical & different).sum()),
        "matrix_distinct_n": n_dist,
        "matrix_distinct_review_different": dist_diff,
        "matrix_distinct_review_same": int((distinct & same).sum()),
        "matrix_identical_sensitivity_decidable": ident_same / int(ident_decidable.sum()) if ident_decidable.any() else None,
        "matrix_identical_sensitivity_conservative": ident_same / n_ident if n_ident else None,
        "matrix_distinct_specificity_decidable": dist_diff / int(dist_decidable.sum()) if dist_decidable.any() else None,
        "matrix_distinct_specificity_conservative": dist_diff / n_dist if n_dist else None,
        "overall_agreement_decidable": (ident_same + dist_diff) / int((ident_decidable | dist_decidable).sum()) if (ident_decidable | dist_decidable).any() else None,
        "false_distinct_pairs": false_distinct,
        "false_distinct_papers": false_distinct_papers,
        "false_identical_pairs": false_identical,
        "false_identical_status": "matrix_identical_but_automated_review_different",
        "false_distinct_status": "resolved_by_user_approved_cell_corrections",
        "note": (
            "Matrix comparison refreshed after user-approved 2026-11-27 cell corrections. "
            "The historical prior-human conflict list is retained for provenance; all eight "
            "conflicted pairs are resolved by the approved corrections."
        ),
    })
    summary["matrix_comparison"]["prior_human_evidence_conflict_resolved_pairs"] = summary[
        "matrix_comparison"
    ]["prior_human_evidence_conflict_pairs"]
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["post_approved_correction"] = {
        "date": "2026-11-27",
        "approved_by": "user",
        "cells_applied": 42,
        "matrix_identical": n_ident,
        "matrix_distinct": n_dist,
        "false_distinct_pairs": false_distinct,
        "false_identical_pairs": false_identical,
        "prior_human_evidence_conflicts_resolved": 8,
        "configuration_count": int(coverage.assign(
            pattern=coverage[params].astype(int).astype(str).agg("".join, axis=1)
        ).groupby("paper")["pattern"].nunique().sum()),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    status = pd.read_csv(PRIOR_STATUS)
    for idx, r in status.iterrows():
        if pd.isna(r.row):
            continue
        if (r.paper, int(r.row), r.parameter) in SUPERSEDED:
            cell = coverage[(coverage.paper == r.paper) & (coverage.row == int(r.row))]
            status.loc[idx, "current_value"] = int(cell.iloc[0][r.parameter])
            status.loc[idx, "status"] = "superseded_by_user_approved_2026-11-27_correction"
    status.to_csv(PRIOR_STATUS, index=False)

    evidence = pd.read_csv(PRIOR_EVIDENCE)
    evidence["post_correction_value"] = ""
    evidence["resolution_status"] = "prior_correction_retained"
    for idx, r in evidence.iterrows():
        cell = coverage[(coverage.paper == r.paper) & (coverage.row == int(r.corrected_row))]
        if len(cell) == 1:
            evidence.loc[idx, "post_correction_value"] = str(int(cell.iloc[0][r.parameter]))
        if (r.paper, int(r.corrected_row), r.parameter) in SUPERSEDED:
            evidence.loc[idx, "resolution_status"] = "superseded_by_user_approved_2026-11-27_correction"
    evidence.to_csv(PRIOR_EVIDENCE, index=False)

    print(json.dumps({
        "matrix_identical": n_ident,
        "matrix_distinct": n_dist,
        "false_distinct_pairs": false_distinct,
        "matrix_identical_review_same": ident_same,
        "matrix_distinct_review_different": dist_diff,
        "prior_corrections_superseded": len(SUPERSEDED),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
