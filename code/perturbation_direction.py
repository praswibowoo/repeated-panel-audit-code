#!/usr/bin/env python3
"""Direction-resolved extraction-error perturbation.

The initial extraction audit found false positives (recorded present, actually
absent).  ``perturbation_upper.py`` and ``perturbation_clustered.py`` flip
present cells to NR, the opposite direction.  This script adds the observed
direction:

* unclustered 11.1% NR -> present (three replicates, 20 draws per study);
* cell-level 0.6% NR -> present (two errors in 345 decidable cells);
* study-clustered 11.1% NR -> present (13 papers, one to three parameters,
  100 replicates), the analogue of ``perturbation_clustered.py``.

It writes ``presence_misclassification_direction.json`` next to the coverage
matrix.  The values are the ones reported in the main text and Table S3.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import SEED, data_dir, load_curated  # noqa: E402
from perturbation_upper import audit, block_factor, paired_median, perturb, summarize  # noqa: E402

DRAWS = 20
SEED_CLUSTER = 20261116
RATE_CLAIM = 13 / 117
REPS_UNCLUSTERED = 3
REPS_CLUSTERED = 100


def unclustered(X, paper, add, reps):
    bf, full, coll = [], [], []
    for rep in range(reps):
        rng = np.random.default_rng(SEED + 1000 + rep)
        Xp = perturb(X, 0.0, add, rng)
        fb, fm, cb, cm = audit(Xp, paper)
        bf.append(block_factor(fb, fm))
        full.append(paired_median(fb, fm))
        coll.append(paired_median(cb, cm))
    return bf, full, coll


def clustered(X, paper, reps):
    papers = sorted(set(paper))
    n_sel = max(1, int(round(RATE_CLAIM * len(papers))))
    rng = np.random.default_rng(SEED_CLUSTER)
    bf, full, coll = [], [], []
    for _ in range(reps):
        Xp = X.copy()
        selected = rng.choice(papers, size=n_sel, replace=False)
        for p in selected:
            idx = np.where(paper == p)[0]
            k = int(rng.integers(1, 4))
            cols = rng.choice(X.shape[1], size=k, replace=False)
            block = Xp[np.ix_(idx, cols)]
            block[block == 0] = 1.0
            Xp[np.ix_(idx, cols)] = block
        fb, fm, cb, cm = audit(Xp, paper)
        bf.append(block_factor(fb, fm))
        full.append(paired_median(fb, fm))
        coll.append(paired_median(cb, cm))
    return bf, full, coll


def summarize_triplet(values):
    med, lo, hi = summarize(values)
    x = np.asarray(values, float)
    return {
        "median": med,
        "q025": float(np.quantile(x, 0.025)),
        "q975": float(np.quantile(x, 0.975)),
        "min": lo,
        "max": hi,
    }


def main() -> None:
    X, rho, paper = load_curated()
    out = {
        "method": (
            "NR -> present perturbations, the direction of the initial "
            "extraction errors. Unclustered rows use three replicates and "
            "20 draws per study; the clustered row selects 13 papers and "
            "flips one to three parameters for all their rows (100 replicates)."
        ),
        "n_rows": int(len(X)),
        "n_papers": int(len(set(paper))),
        "seed": SEED,
        "seed_cluster": SEED_CLUSTER,
        "draws_per_study": DRAWS,
    }

    bf, full, coll = unclustered(X, paper, 0.111, REPS_UNCLUSTERED)
    out["unclustered_11_1"] = {
        "replicates": REPS_UNCLUSTERED,
        "block_factor": summarize_triplet(bf),
        "full_ratio": summarize_triplet(full),
        "collapsed_ratio": summarize_triplet(coll),
    }

    bf, full, coll = unclustered(X, paper, 0.006, REPS_UNCLUSTERED)
    out["cell_level_0_6"] = {
        "replicates": REPS_UNCLUSTERED,
        "block_factor": summarize_triplet(bf),
        "full_ratio": summarize_triplet(full),
        "collapsed_ratio": summarize_triplet(coll),
    }

    bf, full, coll = clustered(X, paper, REPS_CLUSTERED)
    out["clustered_11_1"] = {
        "replicates": REPS_CLUSTERED,
        "papers_flipped": int(max(1, round(RATE_CLAIM * len(set(paper))))),
        "block_factor": summarize_triplet(bf),
        "full_ratio": summarize_triplet(full),
        "collapsed_ratio": summarize_triplet(coll),
    }

    path = os.path.join(data_dir(), "presence_misclassification_direction.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
