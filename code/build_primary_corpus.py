#!/usr/bin/env python3
"""Build the eligibility-qualified primary corpus for the deletion-unit audit.

The full 117-paper curated matrix is retained as the sensitivity corpus. The
primary corpus excludes papers with unresolved duplicate-pair adjudication,
decidable primary/coordinator disagreement, ambiguous scenario identity,
uncertain/substitute extraction status, or the B149 one-row boundary exception.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

AMBIGUOUS_SCENARIO = {"B028", "B057", "B186", "B221", "B222"}
ONE_ROW_BOUNDARY = {"B149"}
DECIDABLE = {"same", "different"}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def coder_concordance(rows: list[dict[str, str]]) -> dict[str, object]:
    paired = [
        (r["primary_relation"], r["coordinator_relation"])
        for r in rows
        if r.get("primary_relation") and r.get("coordinator_relation")
    ]
    categories = ["same", "different", "undecidable"]
    matrix = np.array([
        [sum(a == x and b == y for a, b in paired) for y in categories]
        for x in categories
    ], dtype=int)
    observed = float(np.trace(matrix) / matrix.sum())
    expected = float((matrix.sum(axis=1) * matrix.sum(axis=0)).sum() / matrix.sum() ** 2)
    kappa = (observed - expected) / (1.0 - expected)
    decidable_pairs = [(a, b) for a, b in paired if a in DECIDABLE and b in DECIDABLE]
    return {
        "n_pairs": len(paired),
        "raw_agreement": observed,
        "cohen_kappa": kappa,
        "confusion_matrix": {
            "rows_primary": categories,
            "columns_coordinator": categories,
            "counts": matrix.tolist(),
        },
        "n_both_decidable": len(decidable_pairs),
        "agreement_both_decidable": float(sum(a == b for a, b in decidable_pairs) / len(decidable_pairs)),
        "note": "Coordinator was not blinded; this is concordance, not independent inter-rater reliability.",
    }


def pair_trace(rows: list[dict[str, str]]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    unresolved: dict[str, list[str]] = defaultdict(list)
    disagreement: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        paper = row["paper"]
        pair_id = row["pair_id"]
        if row.get("resolution_status") == "not_adjudicated":
            unresolved[paper].append(pair_id)
        if (
            row.get("primary_relation") in DECIDABLE
            and row.get("coordinator_relation") in DECIDABLE
            and row.get("primary_relation") != row.get("coordinator_relation")
        ):
            disagreement[paper].append(pair_id)
    return dict(unresolved), dict(disagreement)


def main() -> int:
    matrix_fields, matrix_rows = read_csv(DATA / "coverage_matrix.csv")
    manifest_fields, manifest_rows = read_csv(DATA / "corpus_manifest.csv")
    _, adjudication = read_csv(DATA / "duplicate_pair_human_adjudication_results_approved_2026-11-27.csv")
    _, screening_rows = read_csv(ROOT / "docs" / "screening" / "batch1_final_decisions.csv")
    _, substitute_rows = read_csv(DATA / "substitute_intake_log.csv")

    screening = {r["batch_id"]: r for r in screening_rows}
    substitutes = {r["batch_id"]: r for r in substitute_rows}
    unresolved, disagreement = pair_trace(adjudication)

    all_papers = {r["paper"] for r in matrix_rows}
    unsure = {p for p in all_papers if screening.get(p, {}).get("decision") == "UNSURE"}
    substitute = {p for p in all_papers if p in substitutes}

    if len(unresolved) != 11 or sum(len(v) for v in unresolved.values()) != 27:
        raise ValueError("expected 27 unresolved pairs across 11 papers")
    if len(disagreement) != 6 or sum(len(v) for v in disagreement.values()) != 7:
        raise ValueError("expected seven decidable disagreements across six papers")
    if len(unsure) != 13:
        raise ValueError(f"expected 13 curated unsure papers, found {len(unsure)}")
    if substitute != {"B238", "B240"}:
        raise ValueError(f"expected two retained substitutes, found {sorted(substitute)}")

    reasons: dict[str, list[str]] = defaultdict(list)
    for label, papers in [
        ("unresolved_duplicate_pair", set(unresolved)),
        ("decidable_coder_disagreement", set(disagreement)),
        ("ambiguous_scenario_identity", AMBIGUOUS_SCENARIO),
        ("unsure", unsure),
        ("substitute", substitute),
        ("one_row_boundary", ONE_ROW_BOUNDARY),
    ]:
        for paper in sorted(papers):
            reasons[paper].append(label)

    unknown = sorted(set(reasons) - all_papers)
    if unknown:
        raise ValueError(f"exclusion IDs absent from curated matrix: {unknown}")
    excluded = set(reasons)
    primary_rows = [r for r in matrix_rows if r["paper"] not in excluded]
    primary_papers = {r["paper"] for r in primary_rows}

    parameter_fields = [c for c in matrix_fields if c not in {"paper", "row", "rho"}]
    populated = [c for c in parameter_fields if any(float(r[c]) > 0 for r in primary_rows)]
    if len(populated) != 42:
        raise ValueError(f"expected 42 populated primary parameters, found {len(populated)}")

    primary_out = []
    for row in primary_rows:
        item = dict(row)
        item["rho"] = f"{np.mean([float(row[c]) for c in populated]):.6f}"
        primary_out.append(item)
    write_csv(DATA / "coverage_matrix_primary.csv", matrix_fields, primary_out)

    configurations = {(r["paper"], tuple(r[c] for c in parameter_fields)) for r in primary_rows}
    config_counts = Counter(p for p, _ in configurations)
    row_counts = Counter(r["paper"] for r in primary_rows)

    audit_fields = manifest_fields + [
        "screening_decision", "screening_reason_code", "screening_adjudicated",
        "unsure_flag", "substitute_flag", "substitute_candidate_id",
        "curated_eligible", "primary_eligible", "primary_exclusion_reasons",
        "unresolved_pair_ids", "decidable_disagreement_pair_ids",
        "duplicate_adjudication_status", "scenario_ambiguity_flag",
        "one_row_boundary_flag", "primary_rows", "primary_configurations",
    ]
    manifest_audit = []
    for row in manifest_rows:
        paper = row.get("batch_id", "")
        screen = screening.get(paper, {})
        item = dict(row)
        item.update({
            "screening_decision": screen.get("decision", ""),
            "screening_reason_code": screen.get("reason_code", ""),
            "screening_adjudicated": screen.get("adjudicated", ""),
            "unsure_flag": screen.get("decision") == "UNSURE",
            "substitute_flag": paper in substitutes,
            "substitute_candidate_id": substitutes.get(paper, {}).get("cand_id", ""),
            "curated_eligible": paper in all_papers,
            "primary_eligible": paper in primary_papers,
            "primary_exclusion_reasons": ";".join(reasons.get(paper, [])),
            "unresolved_pair_ids": ";".join(unresolved.get(paper, [])),
            "decidable_disagreement_pair_ids": ";".join(disagreement.get(paper, [])),
            "duplicate_adjudication_status": (
                "unresolved_pairs_excluded" if paper in unresolved
                else "decidable_disagreement_excluded" if paper in disagreement
                else "priority_pairs_reviewed" if any(r["paper"] == paper for r in adjudication)
                else "no_priority_pair"
            ),
            "scenario_ambiguity_flag": paper in AMBIGUOUS_SCENARIO,
            "one_row_boundary_flag": paper in ONE_ROW_BOUNDARY,
            "primary_rows": row_counts.get(paper, 0),
            "primary_configurations": config_counts.get(paper, 0),
        })
        manifest_audit.append(item)
    write_csv(DATA / "corpus_manifest_audit.csv", audit_fields, manifest_audit)
    write_csv(
        DATA / "corpus_manifest_primary.csv",
        audit_fields,
        [r for r in manifest_audit if r["primary_eligible"]],
    )

    exclusion_rows = [
        {
            "paper": paper,
            "reasons": ";".join(reasons[paper]),
            "n_curated_rows": sum(r["paper"] == paper for r in matrix_rows),
            "n_primary_rows": row_counts.get(paper, 0),
            "n_primary_configurations": config_counts.get(paper, 0),
            "unresolved_pair_ids": ";".join(unresolved.get(paper, [])),
            "decidable_disagreement_pair_ids": ";".join(disagreement.get(paper, [])),
            "scenario_ambiguity_flag": paper in AMBIGUOUS_SCENARIO,
            "unsure_flag": paper in unsure,
            "substitute_flag": paper in substitute,
            "one_row_boundary_flag": paper in ONE_ROW_BOUNDARY,
        }
        for paper in sorted(excluded)
    ]
    write_csv(
        DATA / "primary_corpus_exclusions.csv",
        [
            "paper", "reasons", "n_curated_rows", "n_primary_rows",
            "n_primary_configurations", "unresolved_pair_ids",
            "decidable_disagreement_pair_ids", "scenario_ambiguity_flag",
            "unsure_flag", "substitute_flag", "one_row_boundary_flag",
        ],
        exclusion_rows,
    )

    summary = {
        "policy": {
            "primary": "eligibility-qualified single-configuration focal scope; multi-configuration papers retained as background",
            "full_curated": "sensitivity corpus",
            "exclude_unresolved_pairs": True,
            "exclude_decidable_coder_disagreements": True,
            "exclude_ambiguous_scenarios": True,
            "exclude_unsure": True,
            "exclude_substitutes": True,
            "exclude_one_row_boundary": True,
        },
        "full_curated": {
            "papers": len(all_papers),
            "rows": len(matrix_rows),
            "nominal_parameters": len(parameter_fields),
            "populated_parameters": sum(any(float(r[c]) > 0 for r in matrix_rows) for c in parameter_fields),
        },
        "primary": {
            "papers": len(primary_papers),
            "rows": len(primary_rows),
            "configurations": len(configurations),
            "single_configuration_papers": sum(v == 1 for v in config_counts.values()),
            "multi_configuration_papers": sum(v > 1 for v in config_counts.values()),
            "nominal_parameters": len(parameter_fields),
            "populated_parameters": len(populated),
            "empty_parameter_columns": [c for c in parameter_fields if c not in populated],
        },
        "excluded": {
            "n_papers": len(excluded),
            "by_reason": {
                "unresolved_duplicate_pair": len(unresolved),
                "decidable_coder_disagreement": len(disagreement),
                "ambiguous_scenario_identity": len(AMBIGUOUS_SCENARIO),
                "unsure": len(unsure),
                "substitute": len(substitute),
                "one_row_boundary": len(ONE_ROW_BOUNDARY),
            },
            "reason_counts_overlap": True,
            "papers": sorted(excluded),
        },
        "coder_concordance": coder_concordance(adjudication),
    }
    with (DATA / "primary_corpus_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
