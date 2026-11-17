#!/usr/bin/env python3
"""Dimension sweep for the coverage audit.

Runs the full and panel-collapsed block/matched ratio with 2, 3, 4, and 5
principal components.  The primary audit uses 2-D; the 3-D row is the existing
conditional check; 4-D and 5-D test whether the full-matrix contrast is
dimension-specific.

This is a sensitivity, so it uses 20 matched draws per study and 500 bootstrap
replicates.  The point estimate is the median per-study ratio.

Writes results/post_audit/dimension_sweep.json and
manuscript/ees/reproducibility/dimension_sweep.csv.

Run: python3 code/dimension_sweep.py   (about 2--3 min)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import (SEED, data_dir, fit, load_curated, median_ci,  # noqa: E402
                    median_drift, seed_for, unique_mask)

DIMS = (2, 3, 4, 5)
DRAWS = 100
OUT = os.path.join(ROOT, "results", "post_audit")
DATA = data_dir()


def run_matrix(X, paper, dims: int):
    papers = sorted(set(paper))
    full = fit(X, dims)
    vals = []
    for p in papers:
        mask = paper == p
        n_p = int(mask.sum())
        keep = ~mask
        block = median_drift(full[keep], fit(X[keep], dims))
        donors = np.where(~mask)[0]
        draws = []
        for d in range(DRAWS):
            rng = np.random.default_rng(seed_for(str(p)) + 7919 * d)
            drop = rng.choice(donors, size=n_p, replace=False)
            km = np.ones(len(X), bool)
            km[drop] = False
            draws.append(median_drift(full[km], fit(X[km], dims)))
        vals.append(block / float(np.median(draws)))
    return median_ci(vals, n_boot=500), vals


def main() -> None:
    X, rho, paper = load_curated()
    uni = unique_mask(X, paper)
    rows = []
    out = {"dims": list(DIMS), "draws": DRAWS, "full": {}, "collapsed": {}}
    for dims in DIMS:
        full_sum, _ = run_matrix(X, paper, dims)
        coll_sum, _ = run_matrix(X[uni], paper[uni], dims)
        out["full"][str(dims)] = full_sum
        out["collapsed"][str(dims)] = coll_sum
        rows.append({"dims": dims, "matrix": "full", **full_sum})
        rows.append({"dims": dims, "matrix": "collapsed", **coll_sum})
        print(f"{dims}-D full {full_sum['median']:.3f} "
              f"({full_sum['ci_lo']:.3f}--{full_sum['ci_hi']:.3f}); "
              f"collapsed {coll_sum['median']:.3f} "
              f"({coll_sum['ci_lo']:.3f}--{coll_sum['ci_hi']:.3f})",
              flush=True)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "dimension_sweep.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    pd.DataFrame(rows).to_csv(
        os.path.join(DATA, "dimension_sweep.csv"), index=False)
    print("wrote", os.path.join(DATA, "dimension_sweep.csv"))


if __name__ == "__main__":
    main()
