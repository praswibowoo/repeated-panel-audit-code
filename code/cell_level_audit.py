#!/usr/bin/env python3
"""Draw a stratified cell-level audit frame.

The Stage-A audit checked 117 claims, not a random sample of cells. This script
draws five cells per paper (three present if available, two blank) from the
curated coverage matrix and writes a CSV that a human coder fills against the
PDF. It does not code the cells.

Columns:
  paper, row, parameter, matrix_value, human_value, match, notes

Run from the source root:
    python3 code/cell_level_audit.py
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import data_dir  # noqa: E402

PER_PAPER = 3
SEED = 20261116


def main() -> None:
    frame = pd.read_csv(os.path.join(data_dir(), "coverage_matrix.csv"))
    params = [c for c in frame.columns if c not in ("paper", "row", "rho")]
    rng = np.random.default_rng(SEED)
    rows = []
    for paper, group in frame.groupby("paper", sort=True):
        idx = group.index.to_numpy()
        present = group.index[group[params].sum(axis=1) > 0].to_numpy()
        blank = group.index[group[params].sum(axis=1) == 0].to_numpy()
        chosen = []
        # Two present cells, spread across the paper's rows where possible.
        for j in rng.permutation(present)[:2]:
            cols = np.where(frame.loc[j, params].to_numpy(float) == 1)[0]
            if len(cols):
                chosen.append((j, params[int(rng.choice(cols))]))
        # One blank cell.
        for j in rng.permutation(blank)[:1]:
            cols = np.where(frame.loc[j, params].to_numpy(float) == 0)[0]
            if len(cols):
                chosen.append((j, params[int(rng.choice(cols))]))
        # Fill to PER_PAPER from any remaining cells.
        if len(chosen) < PER_PAPER:
            seen = {(int(j), c) for j, c in chosen}
            for j in rng.permutation(idx):
                for c in rng.permutation(params):
                    key = (int(j), c)
                    if key not in seen:
                        chosen.append(key)
                        seen.add(key)
                        if len(chosen) >= PER_PAPER:
                            break
                if len(chosen) >= PER_PAPER:
                    break
        for j, c in chosen[:PER_PAPER]:
            rows.append({
                "paper": paper,
                "row": int(frame.loc[j, "row"]),
                "parameter": c,
                "matrix_value": int(frame.loc[j, c]),
                "human_value": "",
                "match": "",
                "notes": "",
            })

    out = pd.DataFrame(rows)
    path = os.path.join(data_dir(), "cell_level_sample.csv")
    out.to_csv(path, index=False)
    print(f"wrote {path}: {len(out)} cells, {out.paper.nunique()} papers")


if __name__ == "__main__":
    main()
