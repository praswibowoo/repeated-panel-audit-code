#!/usr/bin/env python3
"""Leverage proxy for the configuration-unit effect.

Prediction: a study's block/matched ratio should rise with the leverage of its
configurations (distance from the corpus centroid), and the collapsed ratio
should retain that leverage signal while losing the row-count signal.

Writes results/post_audit/leverage_check.json with bootstrap CIs.
"""
from __future__ import annotations
import json, os, sys
import numpy as np, pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from common import data_dir, fit, unique_mask  # noqa: E402

D = data_dir()
OUT = os.path.join(ROOT, "results", "post_audit", "leverage_check.json")

def main():
    X = pd.read_csv(os.path.join(D, "coverage_matrix.csv"))
    params = [c for c in X.columns if c not in ("paper", "row", "rho")]
    A = X[params].to_numpy(float)
    paper = X["paper"].to_numpy()
    uni = unique_mask(A, paper)
    U, pu = A[uni], paper[uni]
    mu = U.mean(0)
    lev = ((U - mu) ** 2).sum(1)          # squared distance from centroid

    b = pd.read_csv(os.path.join(D, "baseline_block.csv"))
    bm = pd.read_csv(os.path.join(D, "baseline_matched.csv"))
    c = pd.read_csv(os.path.join(D, "collapsed_block.csv"))
    cm = pd.read_csv(os.path.join(D, "collapsed_matched.csv"))
    def ratio(bl, ma):
        bb = bl[bl.arm == "block"].set_index("paper")["med_drift"]
        mm = ma[ma.arm == "matched"].groupby("paper")["med_drift"].median()
        return (bb / mm).dropna()
    rf, rc = ratio(b, bm), ratio(c, cm)

    rows = {}
    for p in sorted(set(pu)):
        m = pu == p
        own = lev[m].mean()
        other = lev[~m].mean()
        rows[p] = {"lev": float(own),
                   "lev_ratio": float(own / other),
                   "n_unique": int(m.sum()),
                   "n_rows": int((paper == p).sum()),
                   "rho": float(X.loc[X.paper == p, "rho"].mean()),
                   "full": float(rf.get(p, np.nan)),
                   "coll": float(rc.get(p, np.nan))}
    df = pd.DataFrame(rows).T.dropna()
    df["diff"] = df["full"] - df["coll"]
    out = {"n": int(len(df))}
    pairs = [("lev", "full"), ("lev", "coll"), ("lev", "diff"),
             ("lev_ratio", "full"), ("lev_ratio", "coll"),
             ("n_rows", "full"), ("n_rows", "coll"),
             ("rho", "full"), ("rho", "coll")]
    out["spearman"] = {}
    for a, bb in pairs:
        r, p = stats.spearmanr(df[a], df[bb])
        out["spearman"][f"{a}_vs_{bb}"] = {"rho": float(r), "p": float(p)}
    # log-linear check: does row count or leverage explain the full ratio?
    y = np.log(df["full"].to_numpy(float))
    Xd = np.column_stack([np.ones(len(df)),
                          np.log(df["n_rows"].to_numpy(float)),
                          df["lev"].to_numpy(float)])
    beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
    resid = y - Xd @ beta
    boot = np.random.default_rng(20261119)
    draws = np.empty((10000, 3))
    for i in range(len(draws)):
        idx = boot.integers(0, len(y), len(y))
        draws[i], *_ = np.linalg.lstsq(Xd[idx], y[idx], rcond=None)
    lo, hi = np.quantile(draws, [0.025, 0.975], axis=0)
    out["log_full_model"] = {"intercept": float(beta[0]),
                             "log_rows": float(beta[1]),
                             "leverage": float(beta[2]),
                             "r2": float(1 - resid.var() / y.var()),
                             "log_rows_ci": [float(lo[1]), float(hi[1])],
                             "leverage_ci": [float(lo[2]), float(hi[2])]}
    y2 = np.log(df["coll"].to_numpy(float))
    beta2, *_ = np.linalg.lstsq(Xd, y2, rcond=None)
    resid2 = y2 - Xd @ beta2
    draws = np.empty((10000, 3))
    for i in range(len(draws)):
        idx = boot.integers(0, len(y2), len(y2))
        draws[i], *_ = np.linalg.lstsq(Xd[idx], y2[idx], rcond=None)
    lo, hi = np.quantile(draws, [0.025, 0.975], axis=0)
    out["log_coll_model"] = {"intercept": float(beta2[0]),
                             "log_rows": float(beta2[1]),
                             "leverage": float(beta2[2]),
                             "r2": float(1 - resid2.var() / y2.var()),
                             "log_rows_ci": [float(lo[1]), float(hi[1])],
                             "leverage_ci": [float(lo[2]), float(hi[2])]}
    df.to_csv(os.path.join(ROOT, "results", "post_audit", "leverage_per_paper.csv"))
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2); fh.write("\n")
    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main()
