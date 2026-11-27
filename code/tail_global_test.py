#!/usr/bin/env python3
"""Global permutation Cramér--von Mises test for the collapsed ratio.

The paper reports tail counts at 1.5/2/3/4.  This script replaces those
threshold-by-threshold statements with one distributional test:

  * permute study labels across the 145 unique configurations, preserving each
    paper's configuration count;
  * recompute the collapsed block/matched ratio with 20 draws per paper;
  * compare the observed 117-ratio distribution with the pooled permutation
    null using a two-sample Cramér--von Mises statistic;
  * calibrate the statistic by the permutation distribution with leave-one-out
    (LOO) reference pools, so a permutation is never compared with a null that
    contains itself.

The same test is reported for the single-configuration and multi-configuration
subgroups, because the paper reports those tails separately.

Writes results/post_audit/tail_global_test.json and
results/post_audit/tail_global_null.npz.

Run: python3 code/tail_global_test.py   (about 8 min at 200 permutations)
     python3 code/tail_global_test.py --perms 1000   (30--60 min)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import data_dir, fit, load_curated, median_drift, unique_mask  # noqa: E402

PERMS = 200
DRAWS = 20
SEED = 20261116
OUT = os.path.join(ROOT, "results", "post_audit")


def cvm(x: np.ndarray, y: np.ndarray) -> float:
    """Two-sample Cramér--von Mises statistic (equal-weight version)."""
    x = np.sort(np.asarray(x, float))
    y = np.sort(np.asarray(y, float))
    z = np.sort(np.concatenate([x, y]))
    fx = np.searchsorted(x, z, side="right") / len(x)
    fy = np.searchsorted(y, z, side="right") / len(y)
    return float(np.mean((fx - fy) ** 2))


def permute_once(Xc, paper_c, papers, n_u, S_full, rng):
    """One label permutation; returns 117 ratios in ``papers`` order."""
    perm_paper = rng.permutation(paper_c)
    ratios = []
    for p in papers:
        n = n_u[p]
        block_rows = np.where(perm_paper == p)[0]
        keep = np.ones(len(Xc), bool)
        keep[block_rows] = False
        block = median_drift(S_full[keep], fit(Xc[keep]))
        donors = np.where(perm_paper != p)[0]
        draws = []
        for _ in range(DRAWS):
            drop = rng.choice(donors, size=n, replace=False)
            km = np.ones(len(Xc), bool)
            km[drop] = False
            draws.append(median_drift(S_full[km], fit(Xc[km])))
        ratios.append(block / float(np.median(draws)))
    return np.asarray(ratios, float)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perms", type=int, default=PERMS)
    args = ap.parse_args()
    perms = args.perms

    X, rho, paper = load_curated()
    uni = unique_mask(X, paper)
    Xc = X[uni]
    paper_c = paper[uni]
    papers = sorted(set(paper))
    n_u = {p: int((paper_c == p).sum()) for p in papers}
    S_full = fit(Xc)

    data = data_dir()
    rebuild_path = os.path.join(ROOT, "results", "rebuild", "collapsed_events_rebuilt.csv")
    if os.path.exists(rebuild_path):
        events = pd.read_csv(rebuild_path)
        cb = events[events.arm == "block"]
        cm = events[events.arm == "matched"]
    else:
        cb = pd.read_csv(os.path.join(data, "collapsed_block.csv"))
        cm = pd.read_csv(os.path.join(data, "collapsed_matched.csv"))
    block = cb[cb.arm == "block"].set_index("paper")["med_drift"]
    matched = cm[cm.arm == "matched"].groupby("paper")["med_drift"].median()
    observed = (block / matched).dropna()
    obs_all = observed.to_numpy(float)
    obs_single = observed[[p for p in observed.index if n_u[p] == 1]].to_numpy(float)
    obs_multi = observed[[p for p in observed.index if n_u[p] > 1]].to_numpy(float)

    rng = np.random.default_rng(SEED)
    null_by_perm = []
    for i in range(perms):
        null_by_perm.append(permute_once(Xc, paper_c, papers, n_u, S_full, rng))
        if (i + 1) % 50 == 0:
            print(f"permutation {i + 1}/{perms}", flush=True)

    null = np.vstack(null_by_perm)
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(
        os.path.join(OUT, "tail_global_null.npz"),
        null=null,
        papers=np.array(papers),
        n_unique=np.array([n_u[p] for p in papers]),
    )

    groups = {
        "all": (obs_all, list(range(len(papers)))),
        "single": (obs_single,
                   [j for j, p in enumerate(papers) if n_u[p] == 1]),
        "multi": (obs_multi,
                  [j for j, p in enumerate(papers) if n_u[p] > 1]),
    }

    out = {
        "method": (
            "study labels permuted across the 145 unique configurations, "
            "preserving each paper's configuration count; collapsed "
            "block/matched ratio with 20 matched draws per paper; "
            "two-sample Cramér--von Mises statistic; leave-one-out "
            "calibration of the permutation null"
        ),
        "n_permutations": perms,
        "draws_per_paper": DRAWS,
        "seed": SEED,
        "groups": {},
    }
    for name, (obs, idx) in groups.items():
        sub = null[:, idx]
        pooled = sub.ravel()
        t_obs = cvm(obs, pooled)
        # Self-inclusive calibration, retained as a diagnostic.
        t_self = np.asarray([cvm(sub[i], pooled) for i in range(perms)])
        # Leave-one-out calibration: each permutation is compared with a null
        # that excludes that permutation.
        t_loo = np.asarray([
            cvm(sub[i], np.delete(sub, i, axis=0).ravel())
            for i in range(perms)
        ])
        p_self = float((1 + np.sum(t_self >= t_obs)) / (1 + perms))
        p_loo = float((1 + np.sum(t_loo >= t_obs)) / (1 + perms))
        out["groups"][name] = {
            "n_observed": int(len(obs)),
            "n_null": int(len(pooled)),
            "cvm": float(t_obs),
            "p_permutation": p_loo,
            "p_permutation_loo": p_loo,
            "p_permutation_self": p_self,
            "null_cvm_median": float(np.median(t_loo)),
            "null_cvm_median_self": float(np.median(t_self)),
            "null_cvm_q95": float(np.quantile(t_loo, 0.95)),
        }
        print(name, out["groups"][name], flush=True)

    with open(os.path.join(OUT, "tail_global_test.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("wrote", os.path.join(OUT, "tail_global_test.json"))


if __name__ == "__main__":
    main()
