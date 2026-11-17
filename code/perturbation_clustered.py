#!/usr/bin/env python3
"""Study-clustered extraction-error perturbation.

The primary perturbation flips coverage cells independently. The observed
Stage-A errors were clustered by paper and parameter (for example, one paper's
TSS, another paper's Secchi plus PO4 plus salinity). This script selects 11.1%
of papers, flips all present cells for one to three parameters within each
selected paper to NR, and reruns the full and collapsed audits (20 draws per
study, 100 replicates). It reports the distribution of the block factor and
the paired ratios.

Writes ``presence_misclassification_clustered.json`` next to the coverage
matrix.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import data_dir, load_curated  # noqa: E402
from perturbation_upper import audit, block_factor, paired_median  # noqa: E402

REPS = 100
DRAWS = 20
RATE = 13 / 117  # 11.1% of papers
SEED = 20261116


def main() -> None:
    X, rho, paper = load_curated()
    papers = sorted(set(paper))
    n_sel = max(1, int(round(RATE * len(papers))))
    rng = np.random.default_rng(SEED)

    rows = []
    for rep in range(REPS):
        Xp = X.copy()
        selected = rng.choice(papers, size=n_sel, replace=False)
        for p in selected:
            idx = np.where(paper == p)[0]
            k = int(rng.integers(1, 4))  # one to three parameters
            cols = rng.choice(X.shape[1], size=k, replace=False)
            block = Xp[np.ix_(idx, cols)]
            block[block == 1] = 0.0
            Xp[np.ix_(idx, cols)] = block

        fb, fm, cb, cm = audit(Xp, paper)
        rows.append({
            "rep": rep,
            "papers_flipped": int(n_sel),
            "block_factor": block_factor(fb, fm),
            "full_ratio": paired_median(fb, fm),
            "collapsed_ratio": paired_median(cb, cm),
        })

    import pandas as pd

    df = pd.DataFrame(rows)
    out = {
        "method": (
            "11.1% of papers selected; one to three parameters per selected "
            "paper flipped from present to NR for all their rows; full and "
            "collapsed audits with 20 matched draws per study"
        ),
        "replicates": REPS,
        "papers_flipped": int(n_sel),
        "seed": SEED,
    }
    for col in ("block_factor", "full_ratio", "collapsed_ratio"):
        out[col] = {
            "median": float(df[col].median()),
            "q025": float(df[col].quantile(0.025)),
            "q975": float(df[col].quantile(0.975)),
            "min": float(df[col].min()),
            "max": float(df[col].max()),
        }

    path = os.path.join(data_dir(), "presence_misclassification_clustered.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
