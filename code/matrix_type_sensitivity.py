#!/usr/bin/env python3
"""Sensitivity excluding the 20 summary rows.

Summary rows aggregate scenarios (study-wide mean, pooled station set) rather
than recording one site/station/season/depth.  This script removes them and
reruns the full and collapsed audits with 100 matched draws.

Writes ``summary_excluded_check.json`` next to the coverage matrix.
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import data_dir, load_curated  # noqa: E402
from water_only_check import audit  # noqa: E402


def main() -> None:
    X, rho, paper = load_curated()
    d = data_dir()
    types = pd.read_csv(os.path.join(d, "coverage_matrix_types.csv"))
    cm = pd.read_csv(os.path.join(d, "coverage_matrix.csv"))
    cm = cm[~cm["paper"].isin(["B175", "B111", "B095", "B182", "B239"])].reset_index(drop=True)
    key = cm[["paper", "row"]].merge(types[["paper", "row", "matrix_type"]],
                                     on=["paper", "row"], how="left")
    if key["matrix_type"].isna().any():
        raise ValueError("matrix-type map does not cover the curated matrix")
    mask = (key["matrix_type"] != "summary").to_numpy()
    full, coll, bf_full, bf_coll = audit(X[mask], paper[mask])
    out = {
        "method": "curated matrix minus 20 summary rows; 100 matched draws",
        "rows": int(mask.sum()),
        "papers": int(len(set(paper[mask]))),
        "summary_rows_removed": int((~mask).sum()),
        "full": full,
        "collapsed": coll,
        "block_factor_full": bf_full,
        "block_factor_collapsed": bf_coll,
    }
    path = os.path.join(d, "summary_excluded_check.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
