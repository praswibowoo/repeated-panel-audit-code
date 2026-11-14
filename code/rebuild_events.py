#!/usr/bin/env python3
"""Regenerate the four primary event tables from the coverage matrix.

The deposited ``baseline_*.csv`` and ``collapsed_*.csv`` tables were produced by
the archived full pipeline. This script rebuilds them from
``coverage_matrix.csv`` with the same estimator and seed convention
(``SEED + crc32(paper) % 100000 + 7919 * draw``) and writes the result to
``results/rebuild/``. It does not overwrite the deposited tables. It then
compares the two, so a reader can see whether the deposited primary inputs are
reproducible from the matrix.

Run: python3 code/rebuild_events.py   (about 2 minutes)
"""
from __future__ import annotations

import os
import sys
import zlib

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DRAWS, SEED, data_dir, fit, median_drift,  # noqa: E402
                    unique_mask, load_curated)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = data_dir()
OUT = os.path.join(ROOT, "results", "rebuild")


def rebuild(X, paper, label):
    rows = []
    S_full = fit(X)
    papers = sorted(set(paper))
    for p in papers:
        mask = paper == p
        n_p = int(mask.sum())
        keep = ~mask
        rows.append({"paper": p, "arm": "block", "draw": -1,
                     "n_rows_deleted": n_p,
                     "med_drift": median_drift(S_full[keep], fit(X[keep]))})
        donors = np.where(~mask)[0]
        for dr in range(DRAWS):
            rng = np.random.default_rng(
                SEED + zlib.crc32(str(p).encode()) % 100000 + 7919 * dr)
            drop = rng.choice(donors, size=n_p, replace=False)
            keep2 = np.ones(len(X), bool)
            keep2[drop] = False
            rows.append({"paper": p, "arm": "matched", "draw": dr,
                         "n_rows_deleted": n_p,
                         "med_drift": median_drift(S_full[keep2], fit(X[keep2]))})
    return pd.DataFrame(rows).assign(layer=label)


def compare(name, new, old):
    b = new[new.arm == "block"].set_index("paper")["med_drift"]
    m = new[new.arm == "matched"].groupby("paper")["med_drift"].median()
    ratio = (b / m).dropna()
    ob = old[old.arm == "block"].set_index("paper")["med_drift"]
    om = old[old.arm == "matched"].groupby("paper")["med_drift"].median()
    oratio = (ob / om).dropna()
    common = ratio.index.intersection(oratio.index)
    d = np.abs(ratio[common] - oratio[common])
    print(f"{name}: rebuilt median {ratio.median():.4f}  deposited "
          f"{oratio.median():.4f}  | per-study |diff| median {d.median():.4f}, "
          f"max {d.max():.4f}, corr {np.corrcoef(ratio[common], oratio[common])[0, 1]:.6f}")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    X, rho, paper = load_curated()
    uni = unique_mask(X, paper)

    full = rebuild(X, paper, "full")
    coll = rebuild(X[uni], paper[uni], "collapsed")
    full.to_csv(os.path.join(OUT, "baseline_events_rebuilt.csv"), index=False)
    coll.to_csv(os.path.join(OUT, "collapsed_events_rebuilt.csv"), index=False)

    compare("full", full, pd.concat([pd.read_csv(os.path.join(DATA, "baseline_block.csv")),
                                     pd.read_csv(os.path.join(DATA, "baseline_matched.csv"))]))
    compare("collapsed", coll, pd.concat([pd.read_csv(os.path.join(DATA, "collapsed_block.csv")),
                                          pd.read_csv(os.path.join(DATA, "collapsed_matched.csv"))]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
