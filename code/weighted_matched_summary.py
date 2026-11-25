#!/usr/bin/env python3
"""Summary of the weight-matched control in the weighted fit.

Reads the deposited ``weighted_matched_block.csv`` and
``weighted_matched_matched.csv`` event tables, checks that the matched arm
removed the same total weight as the block, and writes
``weighted_matched_summary.json`` next to the coverage matrix.

The ratio is the median per-paper block/matched drift ratio; the interval is a
percentile bootstrap over papers (10,000 resamples).
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

N_BOOT = 10000


def bootstrap_median(x: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED) -> tuple[float, float, float]:
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        boot[i] = np.median(x[rng.integers(0, len(x), len(x))])
    return float(np.median(x)), float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def main() -> None:
    d = data_dir()
    block = pd.read_csv(os.path.join(d, "weighted_matched_block.csv"))
    matched = pd.read_csv(os.path.join(d, "weighted_matched_matched.csv"))

    b = block.set_index("paper")["med_drift"]
    m = matched.groupby("paper")["med_drift"].median()
    ratio = (b / m).dropna()
    med, lo, hi = bootstrap_median(ratio.to_numpy())

    bw = block.groupby("paper")["weight_deleted"].first()
    mw = matched.groupby("paper")["weight_deleted"].median()
    diff = (mw - bw).dropna()

    df = pd.concat([block, matched], ignore_index=True)
    y = np.log(df["med_drift"].to_numpy(float))
    lv = np.log(df["n_rows_deleted"].to_numpy(float))
    lv = lv - lv.mean()
    blk = (df["arm"] == "block").to_numpy(float)
    design = np.column_stack([np.ones(len(df)), lv, blk, blk * lv])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)

    out = {
        "method": (
            "weighted 1/k fit; matched arm removes donor rows until total "
            "weight equals the block; median per-paper block/matched drift "
            "ratio; percentile bootstrap over papers"
        ),
        "n_papers": int(len(ratio)),
        "ratio": {"median": med, "ci_lo": lo, "ci_hi": hi},
        "block_factor": float(np.exp(beta[2])),
        "weight_difference": {
            "mean": float(diff.mean()),
            "median": float(diff.median()),
            "max_abs": float(diff.abs().max()),
        },
    }
    path = os.path.join(d, "weighted_matched_summary.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
