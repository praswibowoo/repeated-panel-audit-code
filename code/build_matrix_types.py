#!/usr/bin/env python3
"""Build the curated coverage-matrix type map.

The stage-A presence file carries the scenario label but not a matrix-type
column.  The coverage matrix rows align one-to-one, in order, with the stage-A
`row_kind == "data"` rows (standard rows and the five excluded studies removed).
This script assigns a descriptive matrix type from the scenario label and
writes:

    data/coverage_matrix_types.csv

Columns: paper, row, matrix_type, water_only, scenario, scenario_type,
stage_row_kind.

The water/non-water split is exact: 675 water rows and 41 non-water rows across
115 water-only papers. The eight-way labels are descriptive; the presence layer
has no strandline-only row, so the legacy 5/5/20 split for
strandline/summary/biota cannot be reconstructed from the deposited data.

Run: python3 code/build_matrix_types.py
"""
from __future__ import annotations

import os
import re
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import EXCLUDED, data_dir  # noqa: E402

STAGE = os.path.join(ROOT, "docs", "extraction", "stageA", "matrix_presence_v2.csv")
COVERAGE = os.path.join(data_dir(), "coverage_matrix.csv")
OUT = os.path.join(data_dir(), "coverage_matrix_types.csv")


def classify(scenario: str) -> str:
    """Descriptive matrix type from the scenario label."""
    s = str(scenario).lower()
    if re.search(r"bioassay|lc50", s):
        return "bioassay"
    if re.search(r"\bsoil\b", s):
        return "soil"
    if re.search(r"sediment", s):
        return "sediment"
    if re.search(r"tank|mesocosm|exposure media", s):
        return "experimental"
    if re.search(r"oyster|pb-treated fish", s):
        return "biota"
    if re.search(r"strandline|wrack|litter|debris", s):
        return "strandline"
    if re.search(r"summary|review|compilation|baseline|overall|pooled|"
                 r"study-wide|all sites|all stations|whole", s):
        return "summary"
    return "water"


def main() -> None:
    stage = pd.read_csv(STAGE)
    stage["batch_id"] = stage["batch_id"].ffill()
    data = stage[(stage["row_kind"] == "data") &
                 (stage["scenario_type"] != "standard") &
                 (~stage["batch_id"].isin(EXCLUDED))].copy()
    data["matrix_type"] = data["scenario"].map(classify)
    data["water_only"] = data["matrix_type"].eq("water")

    cov = pd.read_csv(COVERAGE)[["paper", "row"]].sort_values(["paper", "row"])
    rows = []
    for paper, group in cov.groupby("paper", sort=False):
        sg = data[data["batch_id"] == paper]
        if len(sg) != len(group):
            raise SystemExit(f"{paper}: stage rows {len(sg)} != coverage rows {len(group)}")
        sg = sg.reset_index(drop=True)
        for pos, (_, r) in enumerate(group.iterrows()):
            rows.append({
                "paper": paper,
                "row": int(r["row"]),
                "matrix_type": sg.loc[pos, "matrix_type"],
                "water_only": bool(sg.loc[pos, "water_only"]),
                "scenario": sg.loc[pos, "scenario"],
                "scenario_type": sg.loc[pos, "scenario_type"],
                "stage_row_kind": sg.loc[pos, "row_kind"],
            })

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    counts = out["matrix_type"].value_counts().to_dict()
    water_papers = out.loc[out["water_only"], "paper"].nunique()
    print("rows", len(out), "papers", out["paper"].nunique())
    print("matrix types", counts)
    print("water rows", int(out["water_only"].sum()), "water-only papers", water_papers)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
