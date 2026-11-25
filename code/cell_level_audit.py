#!/usr/bin/env python3
"""Draw or verify the frozen stratified cell-level audit frame.

The audited frame contains three cells per paper: two reported-present cells
and one blank cell, where available.  The curated matrix has no all-zero rows,
so a blank cell is sampled from zero entries within otherwise populated rows.

The deposited frame is frozen.  Running this script without --force verifies
that the frame is present and has the intended structure; it does not overwrite
the audited sample.  --force regenerates a valid new frame but will not recreate
the exact historical frame used for the published audit.

Columns:
  paper, row, parameter, matrix_value, human_value, match, notes
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import data_dir  # noqa: E402

PER_PAPER = 3
SEED = 20261116


def draw_frame() -> pd.DataFrame:
    frame = pd.read_csv(os.path.join(data_dir(), "coverage_matrix.csv"))
    params = [c for c in frame.columns if c not in ("paper", "row", "rho")]
    rng = np.random.default_rng(SEED)
    rows = []
    for paper, group in frame.groupby("paper", sort=True):
        idx = group.index.to_numpy()
        present_rows = idx
        chosen = []
        # Two reported-present cells, spread across rows.
        for j in rng.permutation(present_rows)[:2]:
            cols = np.where(frame.loc[j, params].to_numpy(float) == 1)[0]
            if len(cols):
                chosen.append((int(j), params[int(rng.choice(cols))]))
        # One blank cell from zero entries in any row of this paper.
        zero_cells = [
            (int(j), c)
            for j in idx
            for c in params
            if frame.loc[j, c] == 0
        ]
        if zero_cells:
            j, c = zero_cells[int(rng.integers(0, len(zero_cells)))]
            if (j, c) not in chosen:
                chosen.append((j, c))
        # Fill if a paper lacks enough present or blank cells.
        if len(chosen) < PER_PAPER:
            seen = set(chosen)
            candidates = [
                (int(j), c)
                for j in idx
                for c in params
                if (int(j), c) not in seen
            ]
            rng.shuffle(candidates)
            chosen.extend(candidates[:PER_PAPER - len(chosen)])
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
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="overwrite the frozen audited frame with a new draw")
    args = ap.parse_args()
    path = os.path.join(data_dir(), "cell_level_sample.csv")
    if os.path.exists(path) and not args.force:
        old = pd.read_csv(path)
        value_counts = old["matrix_value"].value_counts().to_dict()
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if len(old) != 351 or old["paper"].nunique() != 117:
            raise SystemExit("frozen cell-level frame has unexpected dimensions")
        if value_counts.get(1) != 256 or value_counts.get(0) != 95:
            raise SystemExit(f"frozen cell-level frame has unexpected values: {value_counts}")
        print(f"verified frozen frame: {len(old)} cells, {old.paper.nunique()} papers")
        print(f"sha256={sha}")
        return
    out = draw_frame()
    out.to_csv(path, index=False)
    print(f"wrote {path}: {len(out)} cells, {out.paper.nunique()} papers")
    if args.force:
        print("WARNING: regenerated frame differs from the historical audited frame; "
              "the existing human coding must not be reused without re-audit.")


if __name__ == "__main__":
    main()
