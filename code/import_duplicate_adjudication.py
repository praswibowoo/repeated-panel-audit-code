#!/usr/bin/env python3
"""Validate completed human duplicate-pair adjudication files.

This script never edits the coverage matrix. It writes a proposed human-filled
frame and a summary for coordinator review.
"""
from __future__ import annotations

import argparse
import json
import re
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


def read_completed(path: Path, expected_ids: set[str], label: str,
                   allow_partial: bool = False, allow_missing_metadata: bool = False) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "relation" in df.columns and "human_relation" not in df.columns:
        simple_required = {"pair_id", "relation", "evidence", "coder", "date"}
        missing_simple = simple_required - set(df.columns)
        if missing_simple:
            raise ValueError(f"{label}: simple sheet missing columns {sorted(missing_simple)}")
        df = df.rename(columns={
            "relation": "human_relation",
            "coder": "coder_name",
            "date": "coder_date",
        })
        df["source_page_table"] = df["evidence"]
        df["notes"] = df["evidence"]
        df["proposed_matrix_corrections"] = df.get("correction", "")
        df["confidence"] = "medium"
        df["parameters_only_a"] = ""
        df["parameters_only_b"] = ""
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
    missing_ids = expected_ids - got
    unexpected_ids = got - expected_ids
    if unexpected_ids or (missing_ids and not allow_partial):
        raise ValueError(
            f"{label}: pair assignment mismatch; missing={sorted(missing_ids)[:10]}, "
            f"unexpected={sorted(unexpected_ids)[:10]}"
        )
    if allow_partial:
        df = df[df.human_relation.notna() & df.human_relation.astype(str).str.strip().ne("")].copy()
    if not df.human_relation.isin(RELATIONS).all():
        raise ValueError(f"{label}: invalid human_relation")
    if not df.confidence.isin(CONFIDENCE).all():
        raise ValueError(f"{label}: invalid confidence")
    for col in ("source_page_table", "coder_name", "coder_date"):
        if allow_missing_metadata:
            continue
        if df[col].isna().any() or (df[col].astype(str).str.strip() == "").any():
            raise ValueError(f"{label}: blank {col}")
    for row in df.itertuples(index=False):
        if row.human_relation == "different" and not allow_missing_metadata:
            diffs = [getattr(row, c, "") for c in ("parameters_only_a", "parameters_only_b")]
            if not any(pd.notna(x) and str(x).strip() for x in diffs) and not str(row.notes).strip():
                raise ValueError(f"{label}: {row.pair_id} different without parameter-level evidence")
        if row.human_relation == "undecidable" and not allow_missing_metadata and not str(row.notes).strip():
            raise ValueError(f"{label}: {row.pair_id} undecidable without reason")
    return df


def looks_like_cell_correction(value) -> bool:
    if pd.isna(value) or not str(value).strip():
        return False
    text = str(value)
    return bool(re.search(r"(->|→)", text) and re.search(r"\d", text))


def matrix_match(matrix_same: bool, relation: str) -> str:
    if relation == "undecidable":
        return "undecidable"
    return "yes" if (matrix_same and relation == "same") or ((not matrix_same) and relation == "different") else "no"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary", type=Path, required=True)
    ap.add_argument("--second", type=Path, default=None,
                    help="Optional independent second-coder file")
    ap.add_argument("--resolution", type=Path, default=None,
                    help="Optional coordinator resolution CSV")
    ap.add_argument("--allow-partial", action="store_true",
                    help="Accept a subset of the assigned primary pairs")
    ap.add_argument("--allow-missing-metadata", action="store_true",
                    help="Accept blank coder/date/evidence fields and flag them")
    ap.add_argument("--out-dir", type=Path, default=DATA)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(MANIFEST.read_text())
    primary_ids = set(manifest["primary_pair_ids"])
    second_ids = set(manifest["second_coder_pair_ids"])
    primary = read_completed(
        args.primary, primary_ids, "primary",
        allow_partial=args.allow_partial,
        allow_missing_metadata=args.allow_missing_metadata,
    )
    second = read_completed(
        args.second, second_ids, "second",
        allow_partial=args.allow_partial,
        allow_missing_metadata=args.allow_missing_metadata,
    ) if args.second else None

    key = pd.read_csv(COORDINATOR)
    p = primary.rename(columns={
        "human_relation": "primary_relation",
        "source_page_table": "primary_source", "confidence": "primary_confidence",
        "coder_name": "primary_coder", "coder_date": "primary_date",
        "notes": "primary_notes", "parameters_only_a": "primary_only_a",
        "parameters_only_b": "primary_only_b",
        "proposed_matrix_corrections": "primary_proposed_corrections",
    })
    if second is not None:
        s = second.rename(columns={
            "human_relation": "second_relation",
            "source_page_table": "second_source", "confidence": "second_confidence",
            "coder_name": "second_coder", "coder_date": "second_date",
            "notes": "second_notes", "parameters_only_a": "second_only_a",
            "parameters_only_b": "second_only_b",
            "proposed_matrix_corrections": "second_proposed_corrections",
        })
    else:
        s = pd.DataFrame(columns=["pair_id"])
    p = p[[
        "pair_id",
        "primary_relation", "primary_source", "primary_confidence",
        "primary_coder", "primary_date", "primary_notes", "primary_only_a",
        "primary_only_b", "primary_proposed_corrections",
    ]]
    if second is not None:
        s = s[[
            "pair_id",
            "second_relation", "second_source", "second_confidence",
            "second_coder", "second_date", "second_notes", "second_only_a",
            "second_only_b", "second_proposed_corrections",
        ]]
    results = key.merge(p, on="pair_id", how="left", validate="one_to_one").merge(
        s, on="pair_id", how="left", validate="one_to_one"
    )
    if second is None:
        for col in ("second_relation", "second_source", "second_confidence",
                    "second_coder", "second_date", "second_notes", "second_only_a",
                    "second_only_b", "second_proposed_corrections"):
            results[col] = pd.NA
    if args.resolution:
        resolution = pd.read_csv(args.resolution)
        req_res = {"pair_id", "resolved_relation", "resolution_notes", "resolver", "resolution_date"}
        if req_res - set(resolution.columns):
            raise ValueError(f"resolution file missing columns {sorted(req_res-set(resolution.columns))}")
        if resolution.pair_id.duplicated().any():
            raise ValueError("resolution file has duplicate pair_id values")
        if not set(resolution.pair_id).issubset(set(key.pair_id)):
            raise ValueError("resolution file contains unknown pair_id values")
        if not resolution.resolved_relation.isin(RELATIONS).all():
            raise ValueError("resolution file has invalid resolved_relation")
        resolution = resolution[["pair_id", "resolved_relation", "resolution_notes", "resolver", "resolution_date"]].rename(columns={"resolved_relation": "coordinator_relation"})
        results = results.merge(resolution, on="pair_id", how="left", validate="one_to_one")
    else:
        for col in ("coordinator_relation", "resolution_notes", "resolver", "resolution_date"):
            results[col] = pd.NA
    results["coder_agreement"] = (
        results.primary_relation.notna()
        & results.second_relation.notna()
        & results.primary_relation.eq(results.second_relation)
    )
    results["resolution_status"] = "not_adjudicated"
    both = results.primary_relation.notna() & results.second_relation.notna()
    results.loc[both & results.coder_agreement, "resolution_status"] = "resolved_agreement"
    results.loc[both & ~results.coder_agreement & results.coordinator_relation.notna(), "resolution_status"] = "resolved_coordinator"
    results.loc[both & ~results.coder_agreement & results.coordinator_relation.isna(), "resolution_status"] = "coordinator_resolution_required"
    results.loc[results.primary_relation.notna() & results.second_relation.isna() & results.coordinator_relation.notna(), "resolution_status"] = "resolved_coordinator"
    results.loc[results.primary_relation.notna() & results.second_relation.isna() & results.coordinator_relation.isna(), "resolution_status"] = "primary_only"
    results.loc[results.primary_relation.isna() & results.second_relation.notna(), "resolution_status"] = "second_qc_only"
    results["resolved_relation"] = results.primary_relation.where(results.coder_agreement)
    results.loc[results.resolution_status == "resolved_coordinator", "resolved_relation"] = results.loc[results.resolution_status == "resolved_coordinator", "coordinator_relation"]
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
    results["evidence_missing"] = results.primary_source.fillna("").astype(str).str.strip().eq("")
    results["coder_metadata_missing"] = (
        results.primary_coder.fillna("").astype(str).str.strip().eq("")
        | results.primary_date.fillna("").astype(str).str.strip().eq("")
    )
    results["correction_format_warning"] = results.primary_proposed_corrections.apply(
        lambda x: bool(pd.notna(x) and str(x).strip() and not looks_like_cell_correction(x))
    )
    results["prior_evidence_conflict"] = (
        results.primary_relation.eq("same")
        & results.prior_evidence_status.fillna("").str.contains("conflicts_with_ai_same")
    )
    results["matrix_disagreement"] = results.primary_match.eq("no")
    results["ai_disagreement"] = (
        results.primary_relation.notna()
        & results.primary_relation.ne(results.reviewer_relation)
    )

    results_path = args.out_dir / "duplicate_pair_human_adjudication_results.csv"
    results.to_csv(results_path, index=False)

    # Proposed frame: fill only resolved pairs; preserve all original records.
    frame = pd.read_csv(FRAME)
    resolved = results[results.resolution_status.isin(["resolved_agreement", "resolved_coordinator"])][
        ["pair_id", "resolved_relation", "resolved_match", "primary_source", "second_source",
         "primary_notes", "second_notes", "resolver", "resolution_date", "resolution_notes"]
    ].copy()
    if resolved.empty:
        resolved["notes"] = pd.Series(dtype=str)
    else:
        resolved["notes"] = resolved.apply(
            lambda r: " | ".join(str(x) for x in [
                f"primary source: {r.primary_source}", f"second source: {r.second_source}",
                f"primary note: {r.primary_notes}", f"second note: {r.second_notes}",
                f"coordinator: {r.resolver} {r.resolution_date}",
                f"coordinator note: {r.resolution_notes}",
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

    resolved_df = results[results.resolution_status.isin(["resolved_agreement", "resolved_coordinator"])]
    qc_df = results[results.resolution_status == "second_qc_only"]
    completed_df = results[results.primary_relation.notna()]
    summary = {
        "primary_rows": len(primary),
        "expected_primary_pairs": len(primary_ids),
        "pending_primary_pairs": len(primary_ids) - len(primary),
        "pending_primary_pair_ids": sorted(primary_ids - set(primary.pair_id)),
        "completed_relation_counts": {
            k: int(completed_df.primary_relation.eq(k).sum()) for k in sorted(RELATIONS)
        },
        "completed_matrix_match_counts": {
            k: int(completed_df.primary_match.eq(k).sum()) for k in sorted(MATCHES)
        },
        "completed_ai_agreement": int(completed_df.primary_relation.eq(completed_df.reviewer_relation).sum()),
        "evidence_missing": int(completed_df.evidence_missing.sum()),
        "coder_metadata_missing": int(completed_df.coder_metadata_missing.sum()),
        "correction_format_warnings": int(completed_df.correction_format_warning.sum()),
        "prior_evidence_conflicts": int(completed_df.prior_evidence_conflict.sum()),
        "matrix_disagreements": int(completed_df.matrix_disagreement.sum()),
        "ai_disagreements": int(completed_df.ai_disagreement.sum()),
        "second_rows": 0 if second is None else len(second),
        "resolved_agreement": int(results.resolution_status.eq("resolved_agreement").sum()),
        "resolved_coordinator": int(results.resolution_status.eq("resolved_coordinator").sum()),
        "coordinator_resolution_required": int(results.resolution_status.eq("coordinator_resolution_required").sum()),
        "primary_only": int(results.resolution_status.eq("primary_only").sum()),
        "second_coder_used": second is not None,
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
        "evidence_missing_pair_ids": completed_df.loc[completed_df.evidence_missing, "pair_id"].tolist(),
        "coder_metadata_missing_pair_ids": completed_df.loc[completed_df.coder_metadata_missing, "pair_id"].tolist(),
        "correction_format_warning_pair_ids": completed_df.loc[completed_df.correction_format_warning, "pair_id"].tolist(),
        "prior_evidence_conflict_pair_ids": completed_df.loc[completed_df.prior_evidence_conflict, "pair_id"].tolist(),
        "matrix_disagreement_pair_ids": completed_df.loc[completed_df.matrix_disagreement, "pair_id"].tolist(),
        "ai_disagreement_pair_ids": completed_df.loc[completed_df.ai_disagreement, "pair_id"].tolist(),
        "ready_for_strict_import": bool(
            not (primary_ids - set(primary.pair_id))
            and not completed_df.evidence_missing.any()
            and not completed_df.coder_metadata_missing.any()
        ),
        "coverage_matrix_modified": False,
        "configuration_impact": "pending parameter-level correction log",
    }
    (args.out_dir / "duplicate_pair_human_adjudication_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )

    resolution_template = args.out_dir / "duplicate_pair_coordinator_resolution_template.csv"
    if not resolution_template.exists():
        needs = results[results.resolution_status.isin(["primary_only", "coordinator_resolution_required"])]
        pd.DataFrame({
            "pair_id": needs.pair_id,
            "paper": needs.paper,
            "row_a": needs.row_a,
            "row_b": needs.row_b,
            "primary_relation": needs.primary_relation,
            "second_relation": needs.second_relation,
            "primary_evidence": needs.primary_source,
            "primary_correction": needs.primary_proposed_corrections,
            "matrix_hamming": needs.matrix_hamming,
            "ai_relation": needs.reviewer_relation,
            "prior_evidence_status": needs.prior_evidence_status,
            "issue": needs.resolution_status,
            "resolved_relation": "",
            "resolution_notes": "",
            "resolver": "",
            "resolution_date": "",
        }).to_csv(resolution_template, index=False)

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
    print(f"wrote {resolution_template}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
