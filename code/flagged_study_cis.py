#!/usr/bin/env python3
"""Matched-draw bootstrap CIs for the six flagged studies.

The per-study ratio is block median drift divided by the median of 100 matched
draws.  The block drift is a single observed value, so the interval below is
conditional on the block: it bootstraps the 100 matched draws and reports the
2.5--97.5% range of block / median(bootstrap matched draw).

Writes results/post_audit/flagged_study_cis.json and
manuscript/ees/reproducibility/flagged_study_cis.csv.

Run: python3 code/flagged_study_cis.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import SEED, data_dir  # noqa: E402

FLAGGED = ("B063", "B166", "B201", "B213", "B208", "B102")
OUT = os.path.join(ROOT, "results", "post_audit")
DATA = data_dir()


def ratio_ci(block: float, matched: np.ndarray, n_boot: int = 10000):
    matched = np.asarray(matched, float)
    point = block / float(np.median(matched))
    rng = np.random.default_rng(SEED)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        boots[i] = block / float(
            np.median(rng.choice(matched, size=len(matched), replace=True)))
    return point, float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def load_arm(prefix: str):
    block = pd.read_csv(os.path.join(DATA, f"{prefix}_block.csv"))
    block = block[block.arm == "block"].set_index("paper")["med_drift"]
    matched = pd.read_csv(os.path.join(DATA, f"{prefix}_matched.csv"))
    matched = (matched[matched.arm == "matched"]
               .groupby("paper")["med_drift"].apply(np.asarray))
    return block, matched


def main() -> None:
    full_block, full_match = load_arm("baseline")
    coll_block, coll_match = load_arm("collapsed")
    rows = []
    for p in FLAGGED:
        fr, flo, fhi = ratio_ci(full_block[p], full_match[p])
        cr, clo, chi = ratio_ci(coll_block[p], coll_match[p])
        rows.append({
            "paper": p,
            "full_ratio": fr, "full_ci_lo": flo, "full_ci_hi": fhi,
            "collapsed_ratio": cr, "collapsed_ci_lo": clo, "collapsed_ci_hi": chi,
        })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA, "flagged_study_cis.csv"), index=False)
    with open(os.path.join(OUT, "flagged_study_cis.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"method": "matched-draw bootstrap, conditional on block drift",
                   "n_boot": 10000, "rows": rows}, fh, indent=2)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
