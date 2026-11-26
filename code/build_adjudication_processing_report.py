#!/usr/bin/env python3
"""Build all-row and flagged primary-adjudication processing reports.

The report combines the extracted simple submission with the coordinator key,
the deposited coverage matrix, and the importer's provisional results. It never
assigns a relation or edits the coverage matrix.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KEY = DATA / "duplicate_pair_human_adjudication_coordinator_key.csv"
MATRIX = DATA / "coverage_matrix.csv"

MANUAL_FLAGS = {
    "B034_177_181": (
        "different_basis_missing",
        "State the exact parameter difference and source location; the deposited "
        "matrix difference is pH.",
    ),
    "B034_183_181": (
        "different_basis_missing",
        "State the exact parameter difference and source location; the deposited "
        "matrix difference is pH.",
    ),
    "B057_236_238": (
        "undecidable_reason_missing",
        "State why the source cannot support same or different; a parameter list "
        "alone is not an undecidable rationale.",
    ),
    "B063_243_244": (
        "possible_copied_evidence",
        "Replace evidence with B063 Tables 1–2 and 8–9: THB, total coliforms, "
        "pH, TDS, EC, oil/grease, Ni, Cd, Cr, Co, Cu, Pb, Zn, Fe and As; then "
        "reconfirm the relation.",
    ),
    "B076_283_282": (
        "undecidable_reason_missing",
        "State why Table 1a cannot support same or different; a table pointer "
        "alone is not an undecidable rationale.",
    ),
    "B083_302_301": (
        "undecidable_reason_missing",
        "State why Table 1 cannot support same or different; a table pointer "
        "alone is not an undecidable rationale.",
    ),
    "B090_344_342": (
        "different_basis_missing",
        "State the exact parameter difference and source location; the deposited "
        "matrix difference is NH4.",
    ),
    "B097_366_368": (
        "undecidable_reason_missing",
        "State why the source cannot support same or different; the phytoplankton "
        "note belongs in evidence and does not explain the uncertainty.",
    ),
    "B102_376_377": (
        "undecidable_reason_missing",
        "State why Figure 1–4 cannot support same or different; a figure pointer "
        "alone is not an undecidable rationale.",
    ),
    "B125_440_443": (
        "undecidable_reason_missing",
        "State why the source cannot support same or different; move the No Table "
        "reason from correction to evidence if that is the decisive limitation.",
    ),
    "B166_579_580": (
        "undecidable_reason_missing; prior_human_evidence_unresolved",
        "State why the source cannot support same or different and resolve the "
        "accepted prior human TSS correction for row 580.",
    ),
    "B169_592_594": (
        "undecidable_reason_missing",
        "State why the source cannot support same or different; the 12-sample "
        "note belongs in evidence and does not explain the uncertainty.",
    ),
    "B186_615_617": (
        "undecidable_reason_missing",
        "State why Table 1 cannot support same or different; a parameter list "
        "alone is not an undecidable rationale.",
    ),
    "B191_642_641": (
        "undecidable_reason_missing",
        "State why the source cannot support same or different; the narrative "
        "describes conditions but not the decisive limitation.",
    ),
    "B200_654_652": (
        "different_basis_missing",
        "P.4–6 gives no decisive parameter difference. Identify the exact "
        "parameter or reconsider the different label.",
    ),
    "B208_669_670": (
        "evidence_too_vague",
        "Add the examined parameter suite; Table 1–2 alone does not document why "
        "the configurations are the same.",
    ),
    "B213_681_683": (
        "evidence_too_vague",
        "Add the examined parameter suite; P3 Table 2 alone does not document "
        "why the configurations are the same.",
    ),
    "B214_684_687": (
        "evidence_too_vague",
        "Add the examined parameter suite; P.11 Tables 3–4 alone do not document "
        "why the configurations are the same.",
    ),
    "B221_697_695": (
        "undecidable_reason_missing",
        "State why Table 1 cannot support same or different; a table pointer "
        "alone is not an undecidable rationale.",
    ),
    "B222_700_701": (
        "undecidable_reason_missing",
        "State why Table 1 cannot support same or different; a table pointer "
        "alone is not an undecidable rationale.",
    ),
    "B222_702_699": (
        "undecidable_reason_missing",
        "State why Table 1 cannot support same or different; a table pointer "
        "alone is not an undecidable rationale.",
    ),
}


def matrix_differences(row: dict, matrix: pd.DataFrame, parameters: list[str]) -> str:
    a = matrix[(matrix.paper == row["paper"]) & (matrix.row == row["row_a"])]
    b = matrix[(matrix.paper == row["paper"]) & (matrix.row == row["row_b"])]
    if a.empty or b.empty:
        return ""
    a = a.iloc[0]
    b = b.iloc[0]
    return "; ".join(
        f"{parameter}:{int(a[parameter])}->{int(b[parameter])}"
        for parameter in parameters
        if int(a[parameter]) != int(b[parameter])
    )


def build(primary_path: Path, results_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    primary = pd.read_csv(primary_path).fillna("")
    results = pd.read_csv(results_path).fillna("")
    key = pd.read_csv(KEY).fillna("")
    matrix = pd.read_csv(MATRIX)
    parameters = [c for c in matrix.columns if c not in ("paper", "row", "rho")]

    key_primary = key[key.primary_required.astype(str).str.lower().eq("true")]
    merged = primary.merge(
        key_primary[
            [
                "pair_id", "paper", "row_a", "row_b", "matrix_hamming",
                "reviewer_relation", "prior_human_evidence", "prior_evidence_status",
                "priority_tier",
            ]
        ],
        on="pair_id", how="left", validate="one_to_one",
    ).merge(
        results[
            [
                "pair_id", "primary_match", "evidence_missing",
                "coder_metadata_missing", "correction_format_warning",
                "prior_evidence_conflict", "matrix_disagreement", "ai_disagreement",
            ]
        ],
        on="pair_id", how="left", validate="one_to_one",
    )

    rows = []
    for row in merged.to_dict("records"):
        flags: list[str] = []
        actions: list[str] = []
        relation = str(row["relation"]).strip()
        evidence = str(row["evidence"]).strip()
        correction = str(row["correction"]).strip()
        hamming = int(row["matrix_hamming"])

        if not relation:
            flags.append("relation_missing")
            actions.append(
                "Enter same, different, or undecidable from the source; add "
                "page/table/figure evidence."
            )
        if relation and not evidence:
            flags.append("evidence_missing")
            actions.append(
                "Add source page/table/figure and parameter-level evidence or "
                "the reason the source is insufficient."
            )
        if relation and (
            not str(row["coder"]).strip() or not str(row["date"]).strip()
        ):
            flags.append("coder_or_date_missing")
            actions.append("Fill coder and date.")
        if correction and not (
            re.search(r"->|→", correction) and re.search(r"\d", correction)
        ):
            flags.append("correction_not_cell_level")
            actions.append(
                "Move narrative from correction to evidence; use correction only "
                "as row; parameter; current value -> new value."
            )
        if hamming == 0 and relation == "different":
            flags.append("matrix_identical_marked_different")
            actions.append(
                "Identify the exact parameter present in one examined-parameter "
                "suite and absent in the other; station/time pooling alone is not "
                "a parameter-suite difference."
            )
        if hamming > 0 and relation == "same":
            flags.append("matrix_distinct_marked_same")
            actions.append(
                "Explain why the current matrix differences are not true "
                "parameter-suite differences, or revise the relation."
            )
        if str(row["matrix_disagreement"]).lower() == "true":
            flags.append("matrix_disagreement")
        if str(row["ai_disagreement"]).lower() == "true":
            flags.append("ai_disagreement")
            actions.append(
                "Coordinator should verify the source; the automated source-review "
                "label is not human evidence."
            )
        if str(row["prior_evidence_conflict"]).lower() == "true":
            flags.append("prior_human_evidence_conflict")
            actions.append(
                f"Recheck the accepted prior human correction: "
                f"{row['prior_human_evidence']}"
            )
        if row["pair_id"] in MANUAL_FLAGS:
            flag, action = MANUAL_FLAGS[row["pair_id"]]
            flags.append(flag)
            actions.append(action)

        if relation and not flags:
            status = "provisional_no_flag"
        elif not relation:
            status = "incomplete_relation"
        elif (
            not evidence
            or not str(row["coder"]).strip()
            or not str(row["date"]).strip()
        ):
            status = "incomplete_submission"
        else:
            status = "coordinator_review"

        flags = list(dict.fromkeys(flags))
        actions = list(dict.fromkeys(actions))
        output = dict(row)
        output["matrix_differing_parameters"] = matrix_differences(
            row, matrix, parameters
        )
        output["processing_status"] = status
        output["review_flags"] = "; ".join(flags)
        output["required_action"] = (
            " ".join(actions)
            if actions
            else "No row-specific flag; retain as provisional primary-only label "
                 "pending coordinator resolution."
        )
        output["finalized"] = False
        rows.append(output)

    report = pd.DataFrame(rows)[
        [
            "pair_id", "paper", "scenario_a", "scenario_b", "relation",
            "evidence", "correction", "coder", "date", "matrix_hamming",
            "matrix_differing_parameters", "reviewer_relation",
            "prior_evidence_status", "prior_human_evidence", "primary_match",
            "processing_status", "review_flags", "required_action", "finalized",
        ]
    ]
    flagged = report[report.processing_status.ne("provisional_no_flag")].copy()
    return report, flagged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--date", required=True, help="YYYY-MM-DD output label")
    parser.add_argument("--out-dir", type=Path, default=DATA)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    report, flagged = build(args.primary, args.results)
    report_path = args.out_dir / (
        f"duplicate_pair_human_adjudication_processing_report_{args.date}.csv"
    )
    flagged_path = args.out_dir / (
        f"duplicate_pair_human_adjudication_review_flags_{args.date}.csv"
    )
    report.to_csv(report_path, index=False)
    flagged.to_csv(flagged_path, index=False)
    print(f"wrote {report_path}: {len(report)} rows")
    print(f"wrote {flagged_path}: {len(flagged)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
