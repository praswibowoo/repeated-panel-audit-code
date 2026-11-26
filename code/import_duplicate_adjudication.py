#!/usr/bin/env python3
"""Validate completed human duplicate-pair adjudication files.

This script never edits the coverage matrix. It writes a proposed human-filled
frame and a summary for coordinator review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MANIFEST = DATA / "duplicate_pair_adjudication_manifest.json"
COORDINATOR = DATA / "duplicate_pair_human_adjudication_coordinator_key.csv"
FRAME = DATA / "duplicate_pair_audit_frame.csv"

RELATIONS = {"same", "different", "undecidable"}
MATCHES = {"yes", "no", "undecidable"}
CONFIDENCE = {"high", "medium", "low"}


def read_completed(path: Path, expected_ids: set[str], label: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {
        "pair_id", "human_relation", "source_page_table",
        "confidence", "coder_name", "coder_date", "notes",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{label}: missing columns {sorted(missing)}")
    if df.pair_id.duplicated().any():
        raise ValueError(f"{label}: duplicate pair_id values")
    got = set(df.pair_id)
    if got != expected_ids:
        raise ValueError(
            f"{label}: pair assignment mismatch; missing={sorted(expected_ids-got)[:10]}, "
            f"unexpected={sorted(got-expected_ids)[:10]}"
        )
    if not df.human_relation.isin(RELATIONS).all():
        raise ValueError(f"{label}: invalid human_relation")
    if not df.confidence.isin(CONFIDENCE).all():
        raise ValueError(f"{label}: invalid confidence")
    for col in ("source_page_table", "coder_name", "coder_date"):
        if df[col].isna().any() or (df[col].astype(str).str.strip() == "").any():
            raise ValueError(f"{label}: blank {col}")
    for row in df.itertuples(index=False):
        if row.human_relation == "different":
            diffs = [getattr(row, c, "") for c in ("parameters_only_a", "parameters_only_b")]
            if not any(pd.notna(x) and str(x).strip() for x in diffs) and not str(row.notes).strip():
                raise ValueError(f"{label}: {row.pair_id} different without parameter-level evidence")
        if row.human_relation == "undecidable" and not str(row.notes).strip():
            raise ValueError(f"{label}: {row.pair_id} undecidable without reason")
    return df


def matrix_match(matrix_same: bool, relation: str) -> str:
    if relation == "undecidable":
        return "undecidable"
    return "yes" if (matrix_same and relation == "same") or ((not matrix_same) and relation == "different") else "no"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary", type=Path, required=True)
    ap.add_argument("--second", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, default=DATA)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(MANIFEST.read_text())
    primary_ids = set(manifest["primary_pair_ids"])
    second_ids = set(manifest["second_coder_pair_ids"])
    primary = read_completed(args.primary, primary_ids, "primary")
    second = read_completed(args.second, second_ids, "second")

    key = pd.read_csv(COORDINATOR)
    p = primary.rename(columns={
        "human_relation": "primary_relation",
        "source_page_table": "primary_source", "confidence": "primary_confidence",
        "coder_name": "primary_coder", "coder_date": "primary_date",
        "notes": "primary_notes", "parameters_only_a": "primary_only_a",
        "parameters_only_b": "primary_only_b",
        "proposed_matrix_corrections": "primary_proposed_corrections",
    })
    s = second.rename(columns={
        "human_relation": "second_relation",
        "source_page_table": "second_source", "confidence": "second_confidence",
        "coder_name": "second_coder", "coder_date": "second_date",
        "notes": "second_notes", "parameters_only_a": "second_only_a",
        "parameters_only_b": "second_only_b",
        "proposed_matrix_corrections": "second_proposed_corrections",
    })
    p = p[[
        "pair_id", "paper", "row_a", "row_b", "scenario_a", "scenario_b",
        "primary_relation", "primary_source", "primary_confidence",
        "primary_coder", "primary_date", "primary_notes", "primary_only_a",
        "primary_only_b", "primary_proposed_corrections",
    ]]
    s = s[[
        "pair_id", "paper", "row_a", "row_b", "scenario_a", "scenario_b",
        "second_relation", "second_source", "second_confidence",
        "second_coder", "second_date", "second_notes", "second_only_a",
        "second_only_b", "second_proposed_corrections",
    ]]
    results = key.merge(p, on="pair_id", how="left", validate="one_to_one").merge(
        s, on="pair_id", how="left", validate="one_to_one"
    )
    results["coder_agreement"] = (
        results.primary_relation.notna()
        & results.second_relation.notna()
        & results.primary_relation.eq(results.second_relation)
    )
    results["resolution_status"] = "not_adjudicated"
    both = results.primary_relation.notna() & results.second_relation.notna()
    results.loc[both & results.coder_agreement, "resolution_status"] = "resolved_agreement"
    results.loc[both & ~results.coder_agreement, "resolution_status"] = "coordinator_resolution_required"
    results.loc[results.primary_relation.notna() & results.second_relation.isna(), "resolution_status"] = "primary_only"
    results.loc[results.primary_relation.isna() & results.second_relation.notna(), "resolution_status"] = "second_qc_only"
    results["resolved_relation"] = results.primary_relation.where(results.coder_agreement)
    results["matrix_same"] = results.matrix_hamming.eq(0)
    results["primary_match"] = [
        matrix_match(ms, rel) if pd.notna(rel) else ""
        for ms, rel in zip(results.matrix_same, results.primary_relation)
    ]
    results["second_match"] = [
        matrix_match(ms, rel) if pd.notna(rel) else ""
        for ms, rel in zip(results.matrix_same, results.second_relation)
    ]
    results["resolved_match"] = [
        matrix_match(ms, rel) if pd.notna(rel) else ""
        for ms, rel in zip(results.matrix_same, results.resolved_relation)
    ]
    results["ai_agrees_with_resolved"] = [
        (rel == ai) if pd.notna(rel) else None
        for rel, ai in zip(results.resolved_relation, results.reviewer_relation)
    ]

    results_path = args.out_dir / "duplicate_pair_human_adjudication_results.csv"
    results.to_csv(results_path, index=False)

    # Proposed frame: fill only resolved pairs; preserve all original records.
    frame = pd.read_csv(FRAME)
    resolved = results[results.resolution_status == "resolved_agreement"][
        ["pair_id", "resolved_relation", "resolved_match", "primary_source", "second_source",
         "primary_notes", "second_notes"]
    ].copy()
    resolved["notes"] = resolved.apply(
        lambda r: " | ".join(str(x) for x in [
            f"primary source: {r.primary_source}", f"second source: {r.second_source}",
            f"primary note: {r.primary_notes}", f"second note: {r.second_notes}",
        ] if pd.notna(x) and str(x) != "nan"), axis=1
    )
    proposed = frame.drop(columns=["human_relation", "match", "notes"]).merge(
        resolved[["pair_id", "resolved_relation", "resolved_match", "notes"]],
        on="pair_id", how="left", validate="many_to_one",
    ).rename(columns={
        "resolved_relation": "human_relation", "resolved_match": "match",
    })
    proposed = proposed[frame.columns]
    proposed.to_csv(args.out_dir / "duplicate_pair_audit_frame_human_filled.csv", index=False)

    resolved_df = results[results.resolution_status == "resolved_agreement"]
    qc_df = results[results.resolution_status == "second_qc_only"]
    summary = {
        "primary_rows": len(primary),
        "second_rows": len(second),
        "resolved_agreement": len(resolved_df),
        "coordinator_resolution_required": int(results.resolution_status.eq("coordinator_resolution_required").sum()),
        "second_qc_only": len(qc_df),
        "not_adjudicated": int(results.resolution_status.eq("not_adjudicated").sum()),
        "resolved_relation_counts": {
            k: int(resolved_df.resolved_relation.eq(k).sum()) for k in sorted(RELATIONS)
        },
        "matrix_identical_resolved": int((resolved_df.matrix_hamming == 0).sum()),
        "matrix_distinct_resolved": int((resolved_df.matrix_hamming > 0).sum()),
        "matrix_match_counts": {
            k: int(resolved_df.resolved_match.eq(k).sum()) for k in sorted(MATCHES)
        },
        "ai_agreement_resolved": int(resolved_df.ai_agrees_with_resolved.fillna(False).sum()),
        "prior_evidence_conflicts_resolved": int((
            resolved_df.prior_evidence_status.fillna("").str.contains("conflicts_with_ai_same")
        ).sum()),
        "qc_second_matrix_match": int(qc_df.second_match.eq("yes").sum()),
        "qc_second_ai_agreement": int(qc_df.second_relation.eq(qc_df.reviewer_relation).sum()),
        "qc_second_relation_counts": {
            k: int(qc_df.second_relation.eq(k).sum()) for k in sorted(RELATIONS)
        },
        "coverage_matrix_modified": False,
        "configuration_impact": "pending parameter-level correction log",
    }
    (args.out_dir / "duplicate_pair_human_adjudication_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )

    correction_template = args.out_dir / "duplicate_pair_proposed_cell_corrections.csv"
    if not correction_template.exists():
        pd.DataFrame(columns=[
            "pair_id", "paper", "row", "parameter", "current_value", "new_value",
            "source_page_table", "reason", "primary_coder", "second_coder", "coordinator_approval",
        ]).to_csv(correction_template, index=False)
    impact_template = args.out_dir / "duplicate_pair_configuration_impact.csv"
    if not impact_template.exists():
        pd.DataFrame(columns=[
            "paper", "configuration_count_before", "configuration_count_after",
            "changed_pair_ids", "correction_file", "rerun_required", "notes",
        ]).to_csv(impact_template, index=False)

    print(json.dumps(summary, indent=2))
    print(f"wrote {results_path}")
    print(f"wrote {args.out_dir / 'duplicate_pair_audit_frame_human_filled.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
