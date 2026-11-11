#!/usr/bin/env python3
"""Synthetic validation of the panel-collapse audit.

Two scenarios, each with 100 independent synthetic corpora:

H0 (repeated panels only): every study draws its base coverage configuration
from the same distribution; scenarios within a study share the base
configuration with occasional bit flips.  The full row-level audit should
inflate the block/matched ratio; the configuration-collapsed audit should be
near unity.

H1 (planted study effect): one randomly chosen study has an extreme coverage
configuration (all parameters examined).  The full and collapsed audits should
both detect it, and the collapsed audit should rank the planted study first.

The audit reuses the estimators in panel_decomposition.py: binary PCA,
Procrustes drift, common evaluation, row-count control, and
unique-configuration control.

Writes results/post_audit/simulation_validation.json.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from panel_decomposition import fit, unique_mask, common_ratio  # noqa: E402

SEED = int(os.environ.get("SIM_SEED", 42))
S = int(os.environ.get("SIM_S", 60))       # studies per synthetic corpus
R = int(os.environ.get("SIM_R", 8))        # scenarios per study
P = int(os.environ.get("SIM_P", 30))       # parameters
DRAWS = int(os.environ.get("SIM_DRAWS", 30))  # matched draws per study
REPS = int(os.environ.get("SIM_REPS", 100))   # synthetic corpora per scenario
FLIP = float(os.environ.get("SIM_FLIP", 0.0))  # within-study bit flips
OUT = os.path.join(ROOT, "results", "post_audit")


def simulate(rng, planted=False):
    """Return X, paper, planted_id (or None)."""
    X, paper = [], []
    planted_id = None
    if planted:
        planted_id = int(rng.integers(0, S))
    for s in range(S):
        label = f"S{s:02d}"
        if planted and s == planted_id:
            base = np.ones(P, dtype=float)
        else:
            # Study-specific sparse coverage; mean about 0.3.
            base = (rng.random(P) < 0.30).astype(float)
            if base.sum() == 0:
                base[rng.integers(0, P)] = 1.0
        for _ in range(R):
            row = base.copy()
            if FLIP > 0:
                flip = rng.random(P) < FLIP
                row[flip] = 1.0 - row[flip]
            X.append(row)
            paper.append(label)
    return np.asarray(X, float), np.asarray(paper, dtype=object), planted_id


def audit(X, paper, rng, draws=DRAWS):
    """Return per-study full and collapsed block/matched ratios."""
    n = len(X)
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    Xc = X[uni]
    paper_c = paper[uni]
    S_full = fit(X)
    S_full_c = fit(Xc)

    full = {}
    coll = {}
    for p in papers:
        idx_p = np.where(paper == p)[0]
        n_p = len(idx_p)
        keep_block = paper != p
        block_rows = np.where(keep_block)[0]
        S_block = fit(X[keep_block])

        keep_block_c = paper_c != p
        block_rows_c = np.where(keep_block_c)[0]
        S_block_c = fit(Xc[keep_block_c])
        n_u = int(uni[idx_p].sum())

        donors = np.where(paper != p)[0]
        donors_c = np.where(paper_c != p)[0]

        rf, rc = [], []
        for _ in range(draws):
            drop = rng.choice(donors, size=n_p, replace=False)
            keep_match = np.ones(n, bool)
            keep_match[drop] = False
            match_rows = np.where(keep_match)[0]
            S_match = fit(X[keep_match])
            common = keep_block & keep_match
            rf.append(common_ratio(S_full, S_block, block_rows,
                                   S_match, match_rows, common))

            drop_c = rng.choice(donors_c, size=n_u, replace=False)
            keep_match_c = np.ones(len(Xc), bool)
            keep_match_c[drop_c] = False
            match_rows_c = np.where(keep_match_c)[0]
            S_match_c = fit(Xc[keep_match_c])
            common_c = keep_block_c & keep_match_c
            rc.append(common_ratio(S_full_c, S_block_c, block_rows_c,
                                   S_match_c, match_rows_c, common_c))
        full[p] = float(np.median(rf))
        coll[p] = float(np.median(rc))
    return full, coll


def summarise(values):
    x = np.asarray(values, float)
    return {
        "median": float(np.median(x)),
        "q025": float(np.quantile(x, 0.025)),
        "q975": float(np.quantile(x, 0.975)),
        "mean": float(np.mean(x)),
    }


def main():
    rng = np.random.default_rng(SEED)

    h0_full, h0_coll = [], []
    h1_full, h1_coll, h1_planted, h1_top = [], [], [], []
    h1_top3, h1_rank_pct, h1_above2 = [], [], []

    for rep in range(REPS):
        # H0: repeated panels only.
        X, paper, _ = simulate(rng, planted=False)
        f, c = audit(X, paper, rng)
        h0_full.append(np.median(list(f.values())))
        h0_coll.append(np.median(list(c.values())))

        # H1: one planted extreme study.
        X, paper, planted = simulate(rng, planted=True)
        f, c = audit(X, paper, rng)
        h1_full.append(np.median(list(f.values())))
        h1_coll.append(np.median(list(c.values())))
        pid = f"S{planted:02d}"
        h1_planted.append(c[pid])
        ranked = sorted(c, key=c.get, reverse=True)
        rank = ranked.index(pid) + 1
        h1_top.append(1.0 if rank == 1 else 0.0)
        h1_top3.append(1.0 if rank <= 3 else 0.0)
        h1_rank_pct.append(100.0 * (1.0 - (rank - 1) / (len(c) - 1)))
        h1_above2.append(1.0 if c[pid] > 2.0 else 0.0)

        if (rep + 1) % 10 == 0:
            print(f"  replicate {rep + 1}/{REPS}", flush=True)

    out = {
        "design": {
            "studies": S, "scenarios_per_study": R, "parameters": P,
            "within_study_flip_rate": FLIP,
            "matched_draws": DRAWS, "replicates": REPS, "seed": SEED,
        },
        "H0_repeated_panels_only": {
            "full_ratio": summarise(h0_full),
            "collapsed_ratio": summarise(h0_coll),
            "pct_collapsed_within_0.95_1.05": float(
                100.0 * np.mean((np.asarray(h0_coll) >= 0.95) &
                                (np.asarray(h0_coll) <= 1.05))),
        },
        "H1_planted_study": {
            "full_ratio": summarise(h1_full),
            "collapsed_ratio": summarise(h1_coll),
            "planted_collapsed_ratio": summarise(h1_planted),
            "planted_top1_pct": float(100.0 * np.mean(h1_top)),
            "planted_top3_pct": float(100.0 * np.mean(h1_top3)),
            "planted_rank_percentile_median": float(np.median(h1_rank_pct)),
            "planted_above_2x_pct": float(100.0 * np.mean(h1_above2)),
        },
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "simulation_validation.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
