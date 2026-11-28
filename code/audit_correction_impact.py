#!/usr/bin/env python3
"""Quantify how approved cell corrections changed configuration and donor status.

Reports both the full curated matrix and the current eligibility-qualified
primary matrix. The full-matrix result must not be used to imply stability of
primary-corpus donor availability.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def configuration_meta(frame: pd.DataFrame, parameters: list[str]):
    by_paper: dict[str, list[tuple[int, ...]]] = defaultdict(list)
    for _, row in frame.iterrows():
        by_paper[row["paper"]].append(tuple(int(row[c]) for c in parameters))
    meta = {
        paper: {
            "n_rows": len(rows),
            "n_configurations": len(set(rows)),
            "configuration_sizes": Counter(rows),
        }
        for paper, rows in by_paper.items()
    }
    eligibility = {}
    for paper, item in meta.items():
        if item["n_configurations"] != 1:
            continue
        n_rows = item["n_rows"]
        bstudy = sum(
            other != paper and candidate["n_configurations"] == 1
            and candidate["n_rows"] == n_rows
            for other, candidate in meta.items()
        )
        bblock = sum(
            sum(1 for size in candidate["configuration_sizes"].values() if size == n_rows)
            for other, candidate in meta.items()
            if other != paper
        )
        eligibility[paper] = {
            "n_rows": n_rows,
            "bstudy_donors": int(bstudy),
            "bblock_donors": int(bblock),
        }
    return meta, eligibility


def reverse_corrections(current: pd.DataFrame, corrections: pd.DataFrame):
    """Return the pre-correction matrix and verify every correction key."""
    before = current.copy()
    parameters = [c for c in current.columns if c not in {"paper", "row", "rho"}]
    index = {(row.paper, int(row.row)): i for i, row in current.iterrows()}
    for _, row in corrections.iterrows():
        key = (row.paper, int(row.row))
        if key not in index:
            raise ValueError(f"correction absent from matrix: {key}")
        i = index[key]
        if row.parameter not in parameters:
            raise ValueError(f"unknown parameter: {row.parameter}")
        if before.loc[i, row.parameter] != row.new_value:
            raise ValueError(
                f"correction does not match current matrix: "
                f"{row.paper} {row.row} {row.parameter}"
            )
        before.loc[i, row.parameter] = row.current_value
    return before


def build_impact(before: pd.DataFrame, current: pd.DataFrame, corrections: pd.DataFrame):
    parameters = [c for c in current.columns if c not in {"paper", "row", "rho"}]
    meta_before, elig_before = configuration_meta(before, parameters)
    meta_after, elig_after = configuration_meta(current, parameters)

    status_changes = []
    for paper in sorted(set(meta_before) | set(meta_after)):
        before_single = meta_before[paper]["n_configurations"] == 1
        after_single = meta_after[paper]["n_configurations"] == 1
        if before_single != after_single:
            status_changes.append({
                "paper": paper,
                "before": "single" if before_single else "multi",
                "after": "single" if after_single else "multi",
            })

    persistent_single = sorted(set(elig_before) & set(elig_after))
    donor_count_changes: dict[str, list[dict]] = {
        "bstudy_donors": [],
        "bblock_donors": [],
    }
    availability_changes = []
    papers_with_any_change = set()
    for paper in persistent_single:
        for key in donor_count_changes:
            before_n = elig_before[paper][key]
            after_n = elig_after[paper][key]
            if before_n != after_n:
                donor_count_changes[key].append({
                    "paper": paper,
                    "before": before_n,
                    "after": after_n,
                })
                papers_with_any_change.add(paper)
            if (before_n > 0) != (after_n > 0):
                availability_changes.append({
                    "paper": paper,
                    "donor_type": key,
                    "before": before_n,
                    "after": after_n,
                })

    return {
        "cells_applied": len(corrections),
        "papers_changed": int(corrections.paper.nunique()),
        "configurations_before": sum(v["n_configurations"] for v in meta_before.values()),
        "configurations_after": sum(v["n_configurations"] for v in meta_after.values()),
        "single_configuration_papers_before": len(elig_before),
        "single_configuration_papers_after": len(elig_after),
        "single_multi_status_changes": status_changes,
        "persistent_single_configuration_papers": len(persistent_single),
        "donor_count_changes": donor_count_changes,
        "papers_with_any_donor_count_change": len(papers_with_any_change),
        "papers_with_any_donor_count_change_ids": sorted(papers_with_any_change),
        "availability_changes_among_papers_single_before_and_after": availability_changes,
    }


def validate_current_donors(eligibility: dict, result_path: Path) -> None:
    """Check donor counts against the canonical fixed-audit output."""
    fixed = json.loads(result_path.read_text(encoding="utf-8"))
    for paper, item in eligibility.items():
        meta = fixed["meta"][paper]
        expected = {
            "bstudy_donors": meta["whole_study_donors"],
            "bblock_donors": meta["exact_block_donors"],
        }
        for key, want in expected.items():
            if item[key] != want:
                raise ValueError(
                    f"{result_path.name}: {paper} {key} mismatch: "
                    f"{item[key]} != {want}"
                )


def main() -> int:
    full_current = pd.read_csv(DATA / "coverage_matrix.csv")
    primary_current = pd.read_csv(DATA / "coverage_matrix_primary.csv")
    corrections = pd.read_csv(
        DATA / "duplicate_pair_approved_cell_corrections_2026-11-27.csv"
    )

    full_before = reverse_corrections(full_current, corrections)
    primary_corrections = corrections[
        corrections.paper.isin(primary_current.paper.unique())
    ].copy()
    primary_before = reverse_corrections(primary_current, primary_corrections)

    out = build_impact(full_before, full_current, corrections)
    out["primary_impact"] = build_impact(
        primary_before, primary_current, primary_corrections
    )

    full_params = [c for c in full_current.columns if c not in {"paper", "row", "rho"}]
    primary_params = [c for c in primary_current.columns if c not in {"paper", "row", "rho"}]
    _, full_eligibility = configuration_meta(full_current, full_params)
    _, primary_eligibility = configuration_meta(primary_current, primary_params)
    fixed_dir = ROOT / "results" / "unit_revision_fixed"
    validate_current_donors(full_eligibility, fixed_dir / "sensitivity_full_curated.json")
    validate_current_donors(primary_eligibility, fixed_dir / "common_contrast.json")

    out["note"] = (
        "Full-curated and primary-corpus impacts are reported separately. "
        "All current donor pools use the corrected matrices."
    )

    with (DATA / "duplicate_pair_correction_impact_audit.json").open(
        "w", encoding="utf-8"
    ) as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
