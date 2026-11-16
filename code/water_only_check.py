#!/usr/bin/env python3
"""Validate the deposited matrix-type map and the water-only audit.

Reads data/coverage_matrix.csv and data/coverage_matrix_types.csv, asserts the
water/non-water counts, and runs the full and panel-collapsed audits on the
water-only set with 100 matched draws.

Writes data/water_only_check.json.
Run: python3 code/water_only_check.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import (DRAWS, SEED, data_dir, fit, load_curated, median_ci,
                    median_drift, seed_for, unique_mask)  # noqa: E402

DATA = data_dir()
TYPES = os.path.join(DATA, "coverage_matrix_types.csv")
OUT = os.path.join(DATA, "water_only_check.json")


def block_factor(block, matched) -> float:
    """exp(beta_block) from log(d) ~ 1 + log(rows) + block + block x log(rows)."""
    df = pd.DataFrame(block + matched)
    y = np.log(df["med_drift"].to_numpy(float))
    lv = np.log(df["n_rows_deleted"].to_numpy(float))
    lv = lv - lv.mean()
    blk = (df["arm"] == "block").to_numpy(float)
    design = np.column_stack([np.ones(len(df)), lv, blk, blk * lv])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    return float(np.exp(beta[2]))


def block_factor_ci(block, matched, n_boot=1000):
    """Study-cluster bootstrap for the block factor."""
    by_b, by_m = defaultdict(list), defaultdict(list)
    for r in block:
        by_b[r["paper"]].append(r)
    for r in matched:
        by_m[r["paper"]].append(r)
    papers = sorted(by_b)
    rng = np.random.default_rng(SEED)
    vals = []
    for _ in range(n_boot):
        pick = rng.choice(papers, len(papers), replace=True)
        b = [r for p in pick for r in by_b[p]]
        m = [r for p in pick for r in by_m[p]]
        vals.append(block_factor(b, m))
    vals = np.asarray(vals, float)
    return {
        "median": float(np.median(vals)),
        "ci_lo": float(np.quantile(vals, 0.025)),
        "ci_hi": float(np.quantile(vals, 0.975)),
        "n": int(len(papers)),
        "n_boot": int(n_boot),
    }


def audit(X: np.ndarray, paper: np.ndarray):
    n = len(X)
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    Xc = X[uni]
    paper_c = paper[uni]
    S_full = fit(X)
    S_full_c = fit(Xc)
    full, coll = {}, {}
    fb, fm, cb, cm = [], [], [], []

    for p in papers:
        idx = np.where(paper == p)[0]
        n_p = len(idx)
        keep = paper != p
        block = median_drift(S_full[keep], fit(X[keep]))
        fb.append({"paper": p, "arm": "block",
                   "n_rows_deleted": n_p, "med_drift": block})
        donors = np.where(paper != p)[0]
        vals = []
        for dr in range(DRAWS):
            rng = np.random.default_rng(seed_for(p) + 7919 * dr)
            drop = rng.choice(donors, size=n_p, replace=False)
            keep2 = np.ones(n, bool)
            keep2[drop] = False
            v = median_drift(S_full[keep2], fit(X[keep2]))
            vals.append(v)
            fm.append({"paper": p, "arm": "matched",
                       "n_rows_deleted": n_p, "med_drift": v})
        full[p] = block / float(np.median(vals))

        keep_c = paper_c != p
        n_u = int(uni[idx].sum())
        block_c = median_drift(S_full_c[keep_c], fit(Xc[keep_c]))
        cb.append({"paper": p, "arm": "block",
                   "n_rows_deleted": n_u, "med_drift": block_c})
        donors_c = np.where(paper_c != p)[0]
        vals_c = []
        for dr in range(DRAWS):
            rng = np.random.default_rng(seed_for(p, 11) + 7919 * dr)
            drop_c = rng.choice(donors_c, size=n_u, replace=False)
            keep2_c = np.ones(len(Xc), bool)
            keep2_c[drop_c] = False
            v = median_drift(S_full_c[keep2_c], fit(Xc[keep2_c]))
            vals_c.append(v)
            cm.append({"paper": p, "arm": "matched",
                       "n_rows_deleted": n_u, "med_drift": v})
        coll[p] = block_c / float(np.median(vals_c))

    return (median_ci(list(full.values())), median_ci(list(coll.values())),
            block_factor_ci(fb, fm), block_factor_ci(cb, cm))


def main() -> None:
    X, rho, paper = load_curated()
    types = pd.read_csv(TYPES)
    frame = pd.read_csv(os.path.join(DATA, "coverage_matrix.csv"))[["paper", "row"]]
    frame = frame.merge(types[["paper", "row", "matrix_type", "water_only"]],
                        on=["paper", "row"], how="left")
    if frame["matrix_type"].isna().any():
        raise SystemExit("matrix type map does not cover every coverage row")
    keep = frame["water_only"].to_numpy(bool)
    Xw, paperw = X[keep], paper[keep]
    counts = types["matrix_type"].value_counts().to_dict()
    water_papers = types.loc[types["water_only"], "paper"].nunique()
    print("matrix types", counts)
    print("water rows", int(keep.sum()), "water-only papers", water_papers)
    if int(keep.sum()) != 675 or water_papers != 115:
        raise SystemExit("water-only count does not match the deposited map")
    full, coll, full_bf, coll_bf = audit(Xw, paperw)
    out = {
        "matrix_types": counts,
        "water_rows": int(keep.sum()),
        "water_only_papers": int(water_papers),
        "water_unique_configurations": int(unique_mask(Xw, paperw).sum()),
        "full": full,
        "collapsed": coll,
        "full_block_factor": full_bf,
        "collapsed_block_factor": coll_bf,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
