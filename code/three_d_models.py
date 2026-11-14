#!/usr/bin/env python3
"""three_d_models.py — three-component coverage block models.

Fits the same log-linear block model used in the main audit, but with a
three-component PCA, for the curated, all-paper, and include-standard matrices.
The point estimates reproduce the archived 3-D rows; the bootstrap intervals
are draw-level Monte Carlo.

Writes data/coverage_3d_models.csv and results/post_audit/three_d_models.json.

Run: python3 code/three_d_models.py   (about 6--8 min)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import (DRAWS, SEED, data_dir, fit, median_drift,  # noqa: E402
                    seed_for)

DATA = data_dir()
POST = os.path.join(ROOT, "results", "post_audit")

SETS = [
    ("curated", "coverage_matrix.csv", "archived 1.17 (1.00--1.37)"),
    ("all_paper", "coverage_matrix_all_paper.csv", "archived 1.19 (1.01--1.40)"),
    ("include_standard", "coverage_matrix_full_extraction.csv", "archived 1.10 (0.91--1.33)"),
]


def run_one(path: str) -> dict:
    frame = pd.read_csv(path)
    params = [c for c in frame.columns if c not in ("paper", "row", "rho")]
    X = frame[params].values.astype(float)
    paper = frame["paper"].values
    papers = sorted(set(paper))
    n = len(X)
    full = fit(X, 3)

    events = []
    for p in papers:
        idx = np.where(paper == p)[0]
        n_p = len(idx)
        keep = paper != p
        block = median_drift(full[keep], fit(X[keep], 3))
        base = seed_for(str(p))
        draws = []
        for d in range(DRAWS):
            rng = np.random.default_rng(base + 7919 * d)
            drop = rng.choice(np.where(paper != p)[0], size=n_p, replace=False)
            km = np.ones(n, bool)
            km[drop] = False
            draws.append(median_drift(full[km], fit(X[km], 3)))
        events.append((p, 1, np.log(block), n_p))
        for v in draws:
            events.append((p, 0, np.log(v), n_p))

    df = pd.DataFrame(events, columns=["paper", "block", "logd", "n"])
    df["lc"] = np.log(df["n"]) - np.log(df["n"]).mean()
    df["bx"] = df["block"] * df["lc"]
    Xd = np.column_stack([np.ones(len(df)), df["lc"], df["block"], df["bx"]])
    beta = np.linalg.lstsq(Xd, df["logd"].values, rcond=None)[0]

    rng = np.random.default_rng(SEED)
    boot = []
    for _ in range(1000):
        sel = rng.choice(papers, len(papers), replace=True)
        d2 = pd.concat([df[df["paper"] == p] for p in sel])
        X2 = np.column_stack([np.ones(len(d2)), d2["lc"], d2["block"], d2["bx"]])
        b2 = np.linalg.lstsq(X2, d2["logd"].values, rcond=None)[0]
        boot.append(np.exp(b2[2]))

    return {
        "n_rows": int(n),
        "n_papers": int(len(papers)),
        "block_at_mean_volume": float(np.exp(beta[2])),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
    }


def main() -> None:
    rows = []
    out = {}
    for name, file, note in SETS:
        res = run_one(os.path.join(DATA, file))
        res["set"] = name
        res["note"] = note
        rows.append(res)
        out[name] = res
        print(name, res["block_at_mean_volume"],
              f"({res['ci_lo']:.4f}--{res['ci_hi']:.4f})", flush=True)

    df = pd.DataFrame(rows)[
        ["set", "n_rows", "n_papers", "block_at_mean_volume", "ci_lo", "ci_hi", "note"]
    ]
    df.to_csv(os.path.join(DATA, "coverage_3d_models.csv"), index=False)
    with open(os.path.join(POST, "three_d_models.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print("wrote", os.path.join(DATA, "coverage_3d_models.csv"))


if __name__ == "__main__":
    main()
