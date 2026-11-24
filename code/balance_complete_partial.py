#!/usr/bin/env python3
"""Reconstruct complete/partial configuration deletion for the balance table.

For each study, the block removes all rows of the study. The scattered-row
matched arm is the draw-0 row-count control: sample n_p rows from other papers.
A deleted configuration is complete when all of its rows are removed, and
partial when at least one row remains. Writes the medians used in SI Table S14.
"""
from __future__ import annotations

import collections
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import load_curated, seed_for  # noqa: E402


def main() -> None:
    X, rho, paper = load_curated()
    counts = collections.Counter((p, tuple(row)) for p, row in zip(paper, X))
    complete, partial, rows, unique = [], [], [], []
    for p in sorted(set(paper)):
        idx = np.where(paper == p)[0]
        n_p = len(idx)
        donors = np.where(paper != p)[0]
        rng = np.random.default_rng(seed_for(str(p)))
        drop = rng.choice(donors, size=n_p, replace=False)
        touched = collections.defaultdict(int)
        for i in drop:
            touched[(paper[i], tuple(X[i]))] += 1
        complete.append(sum(1 for k, v in touched.items() if v >= counts[k]))
        partial.append(sum(1 for k, v in touched.items() if v < counts[k]))
        rows.append(len(drop))
        unique.append(len(touched))
    out = {
        "method": "draw-0 scattered-row control; complete = all rows of a configuration removed; partial = at least one row retained",
        "n_studies": len(complete),
        "block_complete_median": 1.0,
        "matched_complete_median": float(np.median(complete)),
        "matched_partial_median": float(np.median(partial)),
        "matched_rows_median": float(np.median(rows)),
        "matched_unique_median": float(np.median(unique)),
        "matched_complete_mean": float(np.mean(complete)),
        "matched_partial_mean": float(np.mean(partial)),
    }
    path = os.path.join(ROOT, "manuscript", "ees", "reproducibility",
                        "balance_complete_partial.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
