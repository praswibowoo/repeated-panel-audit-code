#!/usr/bin/env python3
"""Out-of-sample Procrustes sensitivity for the coverage audit.

The primary drift is an in-sample aligned residual: the Procrustes rotation and
scale are fitted on the same shared rows on which the drift is measured.  This
script refits the alignment on a random half of the shared rows and measures the
residual on the held-out half.  It repeats the split 10 times per deletion and
takes the median held-out drift, then repeats the block/matched ratio.

The design is deliberately the same as the primary audit: block deletion vs 100
scattered row-count-matched draws, on the full and panel-collapsed matrices.
Only the Procrustes fitting/evaluation split changes.

Writes results/post_audit/procrustes_holdout.json.

Run: python3 code/procrustes_holdout.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zlib

import numpy as np
import pandas as pd
from scipy.spatial import procrustes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import (DRAWS, SEED, data_dir, fit, load_curated,  # noqa: E402
                    median_ci, unique_mask)

OUT = os.path.join(ROOT, "results", "post_audit")
N_SPLITS = 10
MIN_HALF = 3


def _seed(p: str, dr: int, split: int) -> int:
    return (SEED + zlib.crc32(str(p).encode()) % 100000
            + 7919 * dr + 104729 * split)


def _holdout_drift(ref, red, rows, rng):
    """Median held-out drift after fitting Procrustes on half the rows.

    ``rows`` are absolute row indices in the full matrix.  The reduced fit
    ``red`` contains only those rows, in the same order, so absolute indices
    are mapped to positions with ``searchsorted``.
    """
    if len(rows) < 2 * MIN_HALF:
        return np.nan
    order = rng.permutation(len(rows))
    half = max(MIN_HALF, min(len(rows) - MIN_HALF, len(rows) // 2))
    fit_rows = rows[order[:half]]
    hold_rows = rows[order[half:]]
    fit_pos = np.searchsorted(rows, fit_rows)
    hold_pos = np.searchsorted(rows, hold_rows)
    ref_fit = ref[fit_rows]
    ref_mean = ref_fit.mean(0)
    norm1 = np.linalg.norm(ref_fit - ref_mean)
    a, b, _ = procrustes(ref_fit, red[fit_pos])
    # b is the aligned red[fit_pos] on the normalized ref scale.
    # Recover the affine map from red to b.
    X = np.column_stack([red[fit_pos], np.ones(len(fit_pos))])
    T, *_ = np.linalg.lstsq(X, b, rcond=None)
    Xh = np.column_stack([red[hold_pos], np.ones(len(hold_pos))])
    aligned = Xh @ T
    ref_hold = (ref[hold_rows] - ref_mean) / norm1
    return float(np.median(np.linalg.norm(ref_hold - aligned, axis=1)))


def _event_ratio(S_full, S_block, block_rows, S_match, match_rows,
                 n_split: int) -> float:
    """Block/matched ratio of median held-out drift, one event."""
    block_vals = []
    match_vals = []
    for sp in range(n_split):
        rng = np.random.default_rng(_seed("hold", 0, sp))
        block_vals.append(_holdout_drift(S_full, S_block, block_rows, rng))
        rng = np.random.default_rng(_seed("holdm", 0, sp))
        match_vals.append(_holdout_drift(S_full, S_match, match_rows, rng))
    block_vals = np.asarray(block_vals, float)
    match_vals = np.asarray(match_vals, float)
    block_vals = block_vals[np.isfinite(block_vals)]
    match_vals = match_vals[np.isfinite(match_vals)]
    if len(block_vals) == 0 or len(match_vals) == 0:
        return np.nan
    return float(np.median(block_vals) / np.median(match_vals))


def run_matrix(X, paper, label: str, draws: int, n_split: int):
    papers = sorted(set(paper))
    S_full = fit(X)
    out = {}
    for p in papers:
        mask = paper == p
        n_p = int(mask.sum())
        keep_block = ~mask
        block_rows = np.where(keep_block)[0]
        S_block = fit(X[keep_block])
        donors = np.where(~mask)[0]
        vals = []
        for dr in range(draws):
            rng = np.random.default_rng(
                SEED + zlib.crc32(str(p).encode()) % 100000 + 7919 * dr)
            drop = rng.choice(donors, size=n_p, replace=False)
            keep_match = np.ones(len(X), bool)
            keep_match[drop] = False
            match_rows = np.where(keep_match)[0]
            S_match = fit(X[keep_match])
            # Use the same split seeds for block and matched so the halves are
            # comparable; the shared row sets differ, as in the primary audit.
            block_vals = []
            match_vals = []
            for sp in range(n_split):
                rng_b = np.random.default_rng(_seed(p, dr, sp))
                block_vals.append(_holdout_drift(S_full, S_block, block_rows, rng_b))
                rng_m = np.random.default_rng(_seed(p + "m", dr, sp))
                match_vals.append(_holdout_drift(S_full, S_match, match_rows, rng_m))
            block_vals = np.asarray(block_vals, float)
            match_vals = np.asarray(match_vals, float)
            block_vals = block_vals[np.isfinite(block_vals)]
            match_vals = match_vals[np.isfinite(match_vals)]
            if len(block_vals) and len(match_vals):
                vals.append(float(np.median(block_vals) /
                                  np.median(match_vals)))
        out[p] = float(np.median(vals)) if vals else np.nan
    series = pd.Series(out).dropna()
    summary = median_ci(series.to_numpy(float))
    summary["n"] = int(series.size)
    summary["n_splits"] = int(n_split)
    summary["n_draws"] = int(draws)
    summary["label"] = label
    return summary, {p: float(v) for p, v in out.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="limit the number of papers for a quick test")
    ap.add_argument("--draws", type=int, default=50,
                    help="matched draws per study; 50 matches the manuscript, "
                         "100 is the primary-audit convention")
    ap.add_argument("--splits", type=int, default=N_SPLITS)
    args = ap.parse_args()

    X, rho, paper = load_curated()
    if args.limit:
        keep_papers = sorted(set(paper))[:args.limit]
        keep = np.isin(paper, keep_papers)
        X, paper = X[keep], paper[keep]

    full_sum, full_pp = run_matrix(X, paper, "full", args.draws, args.splits)

    uni = unique_mask(X, paper)
    coll_sum, coll_pp = run_matrix(X[uni], paper[uni], "collapsed",
                                   args.draws, args.splits)

    result = {
        "design": ("50/50 split of shared rows; Procrustes fitted on half A, "
                   "drift measured on half B; median over splits and draws; "
                   "block vs row-count-matched control"),
        "full": full_sum,
        "collapsed": coll_sum,
        "per_paper": {"full": full_pp, "collapsed": coll_pp},
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "procrustes_holdout.json"), "w",
              encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps({"full": full_sum, "collapsed": coll_sum}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
