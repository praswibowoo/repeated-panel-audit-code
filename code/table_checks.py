#!/usr/bin/env python3
"""Table-level checks that were previously computed in the archived pipeline.

Produces the three summaries that back Table S3 (exact-subset volume block
factor), Table S5 (top-25% overlap and PC1 Spearman differences), and Table S13
(row-level PC2 mean difference and sign shares). Every value here is computed
from the deposited event tables; nothing is hard-coded.

Writes results/post_audit/table_checks.json.
Run: python3 code/table_checks.py   (about 10 s)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import data_dir  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = data_dir()
OUT = os.path.join(ROOT, "results", "post_audit")
SEED = 42
N_BOOT = 10000


def _events(block_path, matched_path):
    bb = pd.read_csv(os.path.join(DATA, block_path))
    bm = pd.read_csv(os.path.join(DATA, matched_path))
    return (bb[bb.arm == "block"].set_index("paper"),
            bm[bm.arm == "matched"])


def exact_block_factor(block, matched, exact_papers):
    rows = []
    for p in exact_papers:
        rows.append((1.0, np.log(block.loc[p, "n_rows_deleted"]),
                     np.log(block.loc[p, "med_drift"])))
        sub = matched[matched.paper == p]
        for _, r in sub.iterrows():
            rows.append((0.0, np.log(r["n_rows_deleted"]), np.log(r["med_drift"])))
    d = pd.DataFrame(rows, columns=["block", "logrows", "logd"])
    d["lc"] = d["logrows"] - d["logrows"].mean()

    def fit(frame):
        X = np.column_stack([np.ones(len(frame)), frame["lc"], frame["block"]])
        beta, *_ = np.linalg.lstsq(X, frame["logd"].values, rcond=None)
        return float(np.exp(beta[2]))

    point = fit(d)
    rng = np.random.default_rng(SEED)
    boot = []
    for _ in range(2000):
        sel = rng.choice(exact_papers, len(exact_papers), replace=True)
        rows2 = []
        for p in sel:
            rows2.append((1.0, np.log(block.loc[p, "n_rows_deleted"]),
                          np.log(block.loc[p, "med_drift"])))
            sub = matched[matched.paper == p]
            for _, r in sub.iterrows():
                rows2.append((0.0, np.log(r["n_rows_deleted"]),
                              np.log(r["med_drift"])))
        d2 = pd.DataFrame(rows2, columns=["block", "logrows", "logd"])
        d2["lc"] = d2["logrows"] - d2["logrows"].mean()
        boot.append(fit(d2))
    return {"median": point,
            "ci_lo": float(np.quantile(boot, 0.025)),
            "ci_hi": float(np.quantile(boot, 0.975)),
            "n": len(exact_papers),
            "n_boot": 2000}


def paired_median_ci(block, matched, column):
    diff = (block[column] - matched.groupby("paper")[column].median()).dropna()
    rng = np.random.default_rng(SEED)
    boot = [np.median(rng.choice(diff.values, len(diff), replace=True))
            for _ in range(N_BOOT)]
    return {"median_diff": float(np.median(diff)),
            "ci_lo": float(np.quantile(boot, 0.025)),
            "ci_hi": float(np.quantile(boot, 0.975)),
            "n": int(len(diff))}


def pc2_rowlevel(block, matched):
    diff = (block["pc2_flip"] - matched.groupby("paper")["pc2_flip"].median()).dropna()
    return {"mean": float(diff.mean()),
            "median": float(diff.median()),
            "pct_positive": float(100.0 * (diff > 0).mean()),
            "pct_negative": float(100.0 * (diff < 0).mean()),
            "pct_tied": float(100.0 * (diff == 0).mean()),
            "wilcoxon_p": float(stats.wilcoxon(diff).pvalue),
            "n": int(len(diff))}


def main() -> None:
    comp = pd.read_csv(os.path.join(DATA, "composition_matched_control.csv"))
    exact_papers = sorted(
        comp[comp.arm == "composition_matched"]
        .groupby("paper")["exact_fraction"].mean().loc[lambda s: s > 0].index)

    block_f, matched_f = _events("baseline_block.csv", "baseline_matched.csv")
    block_c, matched_c = _events("collapsed_block.csv", "collapsed_matched.csv")

    out = {
        "exact_subset_block_factor": exact_block_factor(block_f, matched_f, exact_papers),
        "pc1_top25": paired_median_ci(block_f, matched_f, "pc1_top25"),
        "pc1_spearman": paired_median_ci(block_f, matched_f, "pc1_spearman"),
        "pc2_rowlevel_collapsed": pc2_rowlevel(block_c, matched_c),
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "table_checks.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    exact = out["exact_subset_block_factor"]
    print("exact block factor %.4f (%.3f--%.3f)"
          % (exact["median"], exact["ci_lo"], exact["ci_hi"]))
    for k in ("pc1_top25", "pc1_spearman"):
        v = out[k]
        print(f"{k}: {v['median_diff']:.6f} ({v['ci_lo']:.6f} to {v['ci_hi']:.6f})")
    v = out["pc2_rowlevel_collapsed"]
    print("pc2 row-level: mean %.2f, pos %.1f, neg %.1f, tied %.1f, p %.3g"
          % (v["mean"], v["pct_positive"], v["pct_negative"], v["pct_tied"],
             v["wilcoxon_p"]))
    print("wrote", os.path.join(OUT, "table_checks.json"))


if __name__ == "__main__":
    main()
