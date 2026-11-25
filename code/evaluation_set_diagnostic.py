#!/usr/bin/env python3
"""Diagnostic for the draw-dependent common evaluation set.

The primary collapsed audit evaluates both arms on the unique configurations
retained by the block and matched fits in each draw.  This script records the
size of that set and checks whether the per-study ratio is associated with it.

20 draws per study (2,340 draws) are used.  Writes
``common_evaluation_set.json`` next to the coverage matrix.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import (DRAWS, data_dir, fit, load_curated, common_ratio,  # noqa: E402
                    seed_for, unique_mask)


def main() -> None:
    X, rho, paper = load_curated()
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    Xc = X[uni]
    paper_c = paper[uni]
    S_full_c = fit(Xc)

    rows = []
    for p in papers:
        idx_p = np.where(paper == p)[0]
        n_u = int(uni[idx_p].sum())
        keep_block_c = paper_c != p
        block_rows_c = np.where(keep_block_c)[0]
        S_block_c = fit(Xc[keep_block_c])
        donors_c = np.where(paper_c != p)[0]
        base = seed_for(str(p))
        for dr in range(20):
            rng = np.random.default_rng(base + 7919 * dr)
            drop_c = rng.choice(donors_c, size=n_u, replace=False)
            keep_match_c = np.ones(len(Xc), bool)
            keep_match_c[drop_c] = False
            match_rows_c = np.where(keep_match_c)[0]
            S_match_c = fit(Xc[keep_match_c])
            common_c = keep_block_c & keep_match_c
            ratio = common_ratio(S_full_c, S_block_c, block_rows_c,
                                 S_match_c, match_rows_c, common_c)
            rows.append((p, dr, int(common_c.sum()), float(ratio)))

    df = pd.DataFrame(rows, columns=["paper", "draw", "n_common", "ratio"])
    rho_s = stats.spearmanr(df["n_common"], df["ratio"])
    per_paper = df.groupby("paper").agg(n=("n_common", "median"), r=("ratio", "median"))
    rho_p = stats.spearmanr(per_paper["n"], per_paper["r"])
    out = {
        "method": (
            "collapsed block/matched audit, 20 draws per study; common "
            "evaluation set is the unique configurations retained by both arms"
        ),
        "n_draws": int(len(df)),
        "n_configurations": int(uni.sum()),
        "n_common": {
            "median": float(df["n_common"].median()),
            "q25": float(df["n_common"].quantile(0.25)),
            "q75": float(df["n_common"].quantile(0.75)),
            "min": int(df["n_common"].min()),
            "max": int(df["n_common"].max()),
            "share_at_149": float((df["n_common"] == 149).mean()),
        },
        "spearman_draw": {"rho": float(rho_s.statistic), "p": float(rho_s.pvalue)},
        "spearman_paper": {"rho": float(rho_p.statistic), "p": float(rho_p.pvalue)},
    }
    path = os.path.join(data_dir(), "common_evaluation_set.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
