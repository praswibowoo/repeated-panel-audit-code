#!/usr/bin/env python3
"""Leave-six-out sensitivity for the venue-quality check.

The six studies flagged by the three-arm collapsed audit are B063, B201, B102,
B166, B012, and B208.  This script removes all six and reruns the full and
panel-collapsed block/matched audit with 100 draws per study.  It tests
whether the headline contrast depends on the flagged studies.

The five D42 predatory-publisher removals (B010, B029, B135, B183, B189) are
already absent from the curated matrix; this sensitivity addresses the six
studies that remain and are flagged by the audit, not the D42 policy layer.

Writes results/post_audit/leave_flagged_out.json.

Run: python3 code/leave_flagged_out.py   (about 2 min)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import (DRAWS, data_dir, fit, load_curated, median_ci,  # noqa: E402
                    median_drift, seed_for, unique_mask)

FLAGGED = ("B063", "B201", "B102", "B166", "B012", "B208")
OUT = os.path.join(ROOT, "results", "post_audit")


def run_matrix(X, paper, label: str):
    papers = sorted(set(paper))
    full = fit(X)
    vals = []
    for p in papers:
        mask = paper == p
        n_p = int(mask.sum())
        keep = ~mask
        block = median_drift(full[keep], fit(X[keep]))
        donors = np.where(~mask)[0]
        draws = []
        for d in range(DRAWS):
            rng = np.random.default_rng(seed_for(str(p)) + 7919 * d)
            drop = rng.choice(donors, size=n_p, replace=False)
            km = np.ones(len(X), bool)
            km[drop] = False
            draws.append(median_drift(full[km], fit(X[km])))
        vals.append(block / float(np.median(draws)))
    summary = median_ci(vals)
    summary["label"] = label
    summary["n_papers"] = len(papers)
    return summary


def main() -> None:
    X, rho, paper = load_curated()
    keep = ~np.isin(paper, FLAGGED)
    X, paper = X[keep], paper[keep]
    uni = unique_mask(X, paper)

    full = run_matrix(X, paper, "full")
    coll = run_matrix(X[uni], paper[uni], "collapsed")
    out = {
        "excluded": list(FLAGGED),
        "n_papers": int(len(set(paper))),
        "n_rows": int(len(X)),
        "n_unique": int(uni.sum()),
        "full": full,
        "collapsed": coll,
    }
    with open(os.path.join(OUT, "leave_flagged_out.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
