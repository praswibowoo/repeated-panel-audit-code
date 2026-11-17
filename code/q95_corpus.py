#!/usr/bin/env python3
"""Observed exceedance at the permutation-q95 threshold, by configuration count.

Uses the deposited collapsed event tables and the deposited label-permutation
null (tail_permutation.json). No new fits. Writes
results/post_audit/q95_corpus.json.
"""
from __future__ import annotations
import json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from common import data_dir  # noqa: E402

D = data_dir()
OUT = os.path.join(ROOT, "results", "post_audit", "q95_corpus.json")

def ratios():
    b = pd.read_csv(os.path.join(D, "collapsed_block.csv"))
    m = pd.read_csv(os.path.join(D, "collapsed_matched.csv"))
    bb = b[b.arm == "block"].set_index("paper")["med_drift"]
    mm = m[m.arm == "matched"].groupby("paper")["med_drift"].median()
    return (bb / mm).dropna()

def main():
    r = ratios()
    X = pd.read_csv(os.path.join(D, "coverage_matrix.csv"))
    params = [c for c in X.columns if c not in ("paper", "row", "rho")]
    cfg = X.groupby("paper")[params].apply(lambda d: d.drop_duplicates().shape[0])
    q = json.load(open(os.path.join(ROOT, "results", "post_audit", "tail_permutation.json")))
    q95 = {"single": q["groups"]["single"]["null"]["q95"],
           "multi": q["groups"]["multi"]["null"]["q95"]}
    out = {"q95_null": q95, "groups": {}}
    for name, mask in (("single", cfg == 1), ("multi", cfg > 1)):
        papers = list(cfg[mask].index)
        v = r.reindex(papers).dropna()
        out["groups"][name] = {
            "n": int(len(v)),
            "above2": int((v > 2).sum()),
            "above2_pct": float(100 * (v > 2).mean()),
            "above_q95": int((v > q95[name]).sum()),
            "above_q95_pct": float(100 * (v > q95[name]).mean()),
            "expected_q95": float(0.05 * len(v)),
            "median": float(v.median()),
            "q95_observed": float(v.quantile(0.95)),
        }
    out["all"] = {"n": int(len(r)), "above2": int((r > 2).sum()),
                  "above2_pct": float(100 * (r > 2).mean())}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2); fh.write("\n")
    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main()
