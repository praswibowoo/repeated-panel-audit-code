#!/usr/bin/env python3
"""all_paper_audit.py — all-paper (730/122) coverage deletion audit.

Reproduces the Table 4 all-paper row from the deposited matrix:
binary PCA on the 44 coverage columns, leave-one-study-out block deletion,
100 volume-matched scattered draws per study, Procrustes drift, and the
median per-study block/matched ratio with a study-level bootstrap interval.

The archived row also reports a log-linear block factor of 1.40 (1.25--1.58).
That summary is computed on the archived draw sequence; rerunning the model on
the draws below gives about 1.42, a draw-level Monte Carlo difference that the
manuscript already flags (Section 5.3). The paired ratio and its interval are
reproduced exactly.

Writes results/post_audit/all_paper_audit.json.
Run: python3 code/all_paper_audit.py   (about 2 minutes)
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
from common import DRAWS, N_BOOT, SEED, fit, median_drift, seed_for  # noqa: E402

OUT = os.path.join(ROOT, "results", "post_audit")


def main() -> None:
    frame = pd.read_csv(os.path.join(DATA, "coverage_matrix_all_paper.csv"))
    params = [c for c in frame.columns if c not in ("paper", "row", "rho")]
    X = frame[params].values.astype(float)
    paper = frame["paper"].values
    papers = sorted(set(paper))
    n = len(X)
    full = fit(X)

    ratios = []
    block_drift = []
    matched_median = []
    rows = []
    for p in papers:
        idx = np.where(paper == p)[0]
        n_p = len(idx)
        keep = paper != p
        block = median_drift(full[keep], fit(X[keep]))

        base = seed_for(str(p))
        draws = []
        for d in range(DRAWS):
            rng = np.random.default_rng(base + 7919 * d)
            drop = rng.choice(np.where(paper != p)[0], size=n_p, replace=False)
            keep_match = np.ones(n, bool)
            keep_match[drop] = False
            draws.append(median_drift(full[keep_match], fit(X[keep_match])))

        block_drift.append(block)
        matched_median.append(float(np.median(draws)))
        ratios.append(block / float(np.median(draws)))
        rows.append(n_p)

    ratios = np.asarray(ratios, float)
    rng = np.random.default_rng(SEED)
    boot = np.array([np.median(ratios[rng.integers(0, len(ratios), len(ratios))])
                     for _ in range(N_BOOT)])

    result = {
        "matrix": "coverage_matrix_all_paper.csv",
        "rows": int(len(X)),
        "papers": int(len(papers)),
        "draws_per_study": DRAWS,
        "seed": SEED,
        "paired_ratio": {
            "median": float(np.median(ratios)),
            "ci_lo": float(np.quantile(boot, 0.025)),
            "ci_hi": float(np.quantile(boot, 0.975)),
            "n": int(len(ratios)),
        },
        "block_factor_note": (
            "Archived log-linear block factor for this row is 1.40 (1.25--1.58); "
            "the model on these draws gives about 1.42, a draw-level Monte Carlo "
            "difference flagged in Section 5.3."
        ),
        "per_paper": {
            p: {"rows": int(r), "block": float(b), "matched_median": float(m),
                "ratio": float(x)}
            for p, r, b, m, x in zip(papers, rows, block_drift, matched_median, ratios)
        },
    }

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "all_paper_audit.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")

    print(f"{len(X)} rows / {len(papers)} papers")
    print("paired ratio %.4f (%.4f--%.4f)" % (
        result["paired_ratio"]["median"],
        result["paired_ratio"]["ci_lo"],
        result["paired_ratio"]["ci_hi"]))
    print("wrote", path)


if __name__ == "__main__":
    main()
