#!/usr/bin/env python3
"""Correspondence-analysis sensitivity for the full and collapsed audits.

Repeats the deletion audit with CA row coordinates instead of binary-PCA
scores. CA is the natural ordination for a presence/absence matrix; it removes
the "unscaled PCA" objection. Writes results/post_audit/ca_sensitivity.json.
"""
from __future__ import annotations
import json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from common import (data_dir, drift, median_drift, unique_mask,  # noqa: E402
                    common_ratio, median_ci, load_curated, SEED)


def fit_ca(X, dims=2):
    """CA row coordinates (first `dims` axes) for a nonnegative matrix."""
    X = np.asarray(X, float)
    keep = X.sum(0) > 0
    X = X[:, keep]
    P = X / X.sum()
    r = P.sum(1)
    c = P.sum(0)
    r = np.where(r <= 0, 1e-12, r)
    S = (P - np.outer(r, c)) / np.sqrt(np.outer(r, c))
    U, s, _ = np.linalg.svd(S, full_matrices=False)
    return (U[:, :dims] * s[:dims]) / np.sqrt(r)[:, None]


def ca_inertia(X, dims=2):
    """Percent of total inertia on the first `dims` CA axes."""
    X = np.asarray(X, float)
    keep = X.sum(0) > 0
    X = X[:, keep]
    P = X / X.sum()
    r = P.sum(1)
    c = P.sum(0)
    r = np.where(r <= 0, 1e-12, r)
    S = (P - np.outer(r, c)) / np.sqrt(np.outer(r, c))
    s = np.linalg.svd(S, compute_uv=False)
    return float(100 * (s[:dims] ** 2).sum() / (s ** 2).sum())


def audit(X, paper, rng, draws=100, fit_fn=fit_ca):
    n = len(X)
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    Xc, pc = X[uni], paper[uni]
    S_full = fit_fn(X)
    S_full_c = fit_fn(Xc)
    full, coll = {}, {}
    for p in papers:
        keep_block = paper != p
        block_rows = np.where(keep_block)[0]
        S_block = fit_fn(X[keep_block])
        keep_block_c = pc != p
        block_rows_c = np.where(keep_block_c)[0]
        S_block_c = fit_fn(Xc[keep_block_c])
        n_u = int(uni[paper == p].sum())
        donors = np.where(paper != p)[0]
        donors_c = np.where(pc != p)[0]
        rf, rc = [], []
        for _ in range(draws):
            drop = rng.choice(donors, size=int((paper == p).sum()), replace=False)
            keep_match = np.ones(n, bool); keep_match[drop] = False
            match_rows = np.where(keep_match)[0]
            S_match = fit_fn(X[keep_match])
            rf.append(common_ratio(S_full, S_block, block_rows, S_match,
                                   match_rows, keep_block & keep_match))
            drop_c = rng.choice(donors_c, size=n_u, replace=False)
            keep_match_c = np.ones(len(Xc), bool); keep_match_c[drop_c] = False
            match_rows_c = np.where(keep_match_c)[0]
            S_match_c = fit_fn(Xc[keep_match_c])
            rc.append(common_ratio(S_full_c, S_block_c, block_rows_c, S_match_c,
                                   match_rows_c, keep_block_c & keep_match_c))
        full[p] = float(np.median(rf))
        coll[p] = float(np.median(rc))
    return full, coll


def main():
    X, rho, paper = load_curated()
    rng = np.random.default_rng(SEED)
    full, coll = audit(X, paper, rng, draws=100)
    rf = pd.Series(full)
    rc = pd.Series(coll)
    diff = (rf - rc).dropna()
    out = {
        "method": "correspondence analysis, 2 axes, 100 matched draws per study",
        "full": median_ci(rf.to_numpy()),
        "collapsed": median_ci(rc.to_numpy()),
        "paired_difference": median_ci(diff.to_numpy()),
        "pct_below_one": float(100 * (rc < 1).mean()),
        "n": int(len(rf)),
        "inertia_2d_pct": ca_inertia(X),
    }
    os.makedirs(os.path.join(ROOT, "results", "post_audit"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "post_audit",
                           "ca_sensitivity.json"), "w") as fh:
        json.dump(out, fh, indent=2); fh.write("\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
