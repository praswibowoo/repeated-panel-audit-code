#!/usr/bin/env python3
"""Permutation null for the per-study collapsed ratio.

The per-study ratio is a block deletion divided by the median of 100 matched
deletions. It has a null distribution of its own: a study with no unusual
influence still produces a ratio away from 1 when the deleted set is small. The
null is estimated here by treating each matched draw as a pseudo-block at the
paper's own deletion count, so numerator and denominator are exchangeable sets
of the same size, and by stratifying on the number of unique configurations
(k = 1 vs k >= 2), because a block that removes several configurations is
coherent by construction even when the study has no influence.

Also reports a common-evaluation recomputation of the observed tail, which is
the estimator the Methods section describes; the deposited per-study ratios use
each arm's own retained rows.

Writes results/post_audit/tail_null.json only. Does not touch the deposited
event tables or tail_audit.json.
Run: python3 code/tail_null.py   (about 2 minutes)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import binom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DRAWS, data_dir, fit, common_ratio,  # noqa: E402
                    load_curated, seed_for, unique_mask)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = data_dir()
OUT = os.path.join(ROOT, "results", "post_audit")
THRESH = (1.5, 2.0, 3.0, 4.0)


def _num(v: float) -> str:
    """One decimal, unless the value is below 1 (then two, e.g. 0.15)."""
    return f"{v:.1f}" if v >= 1 else f"{v:.2f}"


def _summ(x, observed_n):
    """Null tail summary for one group and the binomial test against it."""
    x = np.asarray(x, float)
    n = int(observed_n)
    out = {"n": n, "q95": float(np.quantile(x, 0.95)),
           "q99": float(np.quantile(x, 0.99)),
           "median": float(np.median(x)), "thresholds": {}}
    for t in THRESH:
        p0 = float(np.mean(x > t))
        obs = None  # filled by caller
        out["thresholds"][f"{t:g}"] = {
            "null_pct": float(100.0 * p0),
            "expected": float(n * p0),
        }
    return out


def main() -> None:
    cov = pd.read_csv(os.path.join(DATA, "coverage_matrix.csv"))
    params = [c for c in cov.columns if c not in ("paper", "row", "rho")]
    k = (cov.groupby("paper")[params]
            .apply(lambda g: len(g.drop_duplicates())).to_dict())

    cb = pd.read_csv(os.path.join(DATA, "collapsed_block.csv"))
    cm = pd.read_csv(os.path.join(DATA, "collapsed_matched.csv"))
    block = cb[cb.arm == "block"].set_index("paper")["med_drift"]
    draws = {p: g["med_drift"].to_numpy(float)
             for p, g in cm[cm.arm == "matched"].groupby("paper")}
    observed = {p: block[p] / np.median(draws[p]) for p in draws if p in block}

    # Permutation null: each matched draw is a pseudo-block of the same size.
    rows = []
    for p, v in draws.items():
        for i in range(len(v)):
            rows.append((p, int(k[p]), v[i] / np.median(np.delete(v, i))))
    null = pd.DataFrame(rows, columns=["paper", "k", "r"])

    groups = {
        "single": [p for p in observed if k[p] == 1],
        "multi": [p for p in observed if k[p] > 1],
        "all": list(observed),
    }
    result = {
        "method": ("matched draw as pseudo-block at the paper's deletion count; "
                   "pooled within configuration-count group; 100 draws per paper"),
        "estimator": ("block arm median drift on its own retained rows, divided "
                      "by the median of 100 matched draws, each on its own "
                      "retained rows"),
        "groups": {},
    }
    for name, papers in groups.items():
        obs = np.array([observed[p] for p in papers], float)
        sel = (null.k == 1) if name == "single" else (
            (null.k > 1) if name == "multi" else np.ones(len(null), bool))
        pool = null.loc[sel, "r"].to_numpy(float)
        s = _summ(pool, len(obs))
        s["observed"] = {}
        for t in THRESH:
            m = int((obs > t).sum())
            p0 = float(np.mean(pool > t))
            s["observed"][f"{t:g}"] = {
                "n": m,
                "pct": float(100.0 * m / len(obs)),
                "p_binom": float(binom.sf(m - 1, len(obs), p0)),
            }
            s["thresholds"][f"{t:g}"]["observed"] = m
        s["above_null_q95"] = int((obs > s["q95"]).sum())
        result["groups"][name] = s

    # Common-evaluation sensitivity: the estimator the Methods text names.
    X, rho, paper = load_curated()
    m = unique_mask(X, paper)
    Xc, pc = X[m], paper[m]
    S_full = fit(Xc)
    common = {}
    for p in sorted(set(pc)):
        n_u = len(np.where(pc == p)[0])
        kb = pc != p
        rb = np.where(kb)[0]
        S_b = fit(Xc[kb])
        don = np.where(pc != p)[0]
        rng = np.random.default_rng(seed_for(p, 11))
        vals = []
        for _ in range(DRAWS):
            drop = rng.choice(don, size=n_u, replace=False)
            km = np.ones(len(Xc), bool)
            km[drop] = False
            rm = np.where(km)[0]
            vals.append(common_ratio(S_full, S_b, rb, fit(Xc[km]), rm, kb & km))
        common[p] = float(np.nanmedian(vals))
    r = np.array(list(common.values()), float)
    result["common_evaluation_sensitivity"] = {
        "estimator": "common evaluation set (rows retained in both arms)",
        "median": float(np.median(r)),
        "tail": {f"{t:g}": {"n": int((r > t).sum()),
                            "pct": float(100.0 * np.mean(r > t))}
                 for t in THRESH},
    }

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "tail_null.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)

    for name in ("single", "multi", "all"):
        g = result["groups"][name]
        print(f"{name:6} n={g['n']:3}  q95={g['q95']:.2f}  "
              + "  ".join(f">{t:g} {g['thresholds'][f'{t:g}']['null_pct']:.1f}%"
                          f" (obs {g['observed'][f'{t:g}']['n']}, "
                          f"exp {_num(g['thresholds'][f'{t:g}']['expected'])})"
                          for t in THRESH))
    print("common-evaluation sensitivity: median %.3f, >2 %d/117, >3 %d/117" % (
        result["common_evaluation_sensitivity"]["median"],
        result["common_evaluation_sensitivity"]["tail"]["2"]["n"],
        result["common_evaluation_sensitivity"]["tail"]["3"]["n"]))
    print("wrote", path)


if __name__ == "__main__":
    main()
