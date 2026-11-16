#!/usr/bin/env python3
"""Upper-bound extraction-error perturbation for the P2 coverage audit.

Recomputes the coverage-cell perturbation at the archived rates (5/1, 10/5,
11.1/0) and at the two upper-bound rates requested in the P0 pass:

    19% present -> NR   (the lower bound of the 17/17 independent re-audit)
    25% present -> NR   (the fresh-screen mappable mismatch rate, 6/24)

The audit is the same as the primary design: full row-level block vs
row-count matched deletion, and collapsed unique-configuration block vs
unique-configuration matched deletion, with 20 draws per study and 3
replicates per rate.

Writes data/presence_misclassification_upper.csv.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import (SEED, data_dir, fit, load_curated, median_drift, seed_for,
                    unique_mask)  # noqa: E402

OUT = os.path.join(data_dir(), "presence_misclassification_upper.csv")
DRAWS = 20
REPS = 3
RATES = ((0.05, 0.01), (0.10, 0.05), (0.111, 0.0), (0.19, 0.0), (0.25, 0.0))


def perturb(X: np.ndarray, drop: float, add: float, rng: np.random.Generator) -> np.ndarray:
    Xp = X.copy()
    present = Xp == 1
    absent = Xp == 0
    Xp[present & (rng.random(Xp.shape) < drop)] = 0.0
    Xp[absent & (rng.random(Xp.shape) < add)] = 1.0
    return Xp


def audit(X: np.ndarray, paper: np.ndarray):
    """Return full and collapsed block/matched event tables."""
    n = len(X)
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    Xc = X[uni]
    paper_c = paper[uni]
    S_full = fit(X)
    S_full_c = fit(Xc)

    block, matched, cblock, cmatched = [], [], [], []
    for p in papers:
        idx = np.where(paper == p)[0]
        n_p = len(idx)
        keep = paper != p
        block.append({
            "paper": p, "arm": "block", "n_rows_deleted": n_p,
            "med_drift": median_drift(S_full[keep], fit(X[keep])),
        })
        donors = np.where(paper != p)[0]
        for dr in range(DRAWS):
            rng = np.random.default_rng(seed_for(p) + 7919 * dr)
            drop = rng.choice(donors, size=n_p, replace=False)
            keep2 = np.ones(n, bool)
            keep2[drop] = False
            matched.append({
                "paper": p, "arm": "matched", "n_rows_deleted": n_p,
                "med_drift": median_drift(S_full[keep2], fit(X[keep2])),
            })

        keep_c = paper_c != p
        n_u = int(uni[idx].sum())
        cblock.append({
            "paper": p, "arm": "block", "n_rows_deleted": n_u,
            "med_drift": median_drift(S_full_c[keep_c], fit(Xc[keep_c])),
        })
        donors_c = np.where(paper_c != p)[0]
        for dr in range(DRAWS):
            rng = np.random.default_rng(seed_for(p, 11) + 7919 * dr)
            drop_c = rng.choice(donors_c, size=n_u, replace=False)
            keep2_c = np.ones(len(Xc), bool)
            keep2_c[drop_c] = False
            cmatched.append({
                "paper": p, "arm": "matched", "n_rows_deleted": n_u,
                "med_drift": median_drift(S_full_c[keep2_c], fit(Xc[keep2_c])),
            })

    return (pd.DataFrame(block), pd.DataFrame(matched),
            pd.DataFrame(cblock), pd.DataFrame(cmatched))


def block_factor(block: pd.DataFrame, matched: pd.DataFrame) -> float:
    """exp(beta_block) from log(d) ~ 1 + log(rows) + block + block x log(rows)."""
    df = pd.concat([block, matched], ignore_index=True)
    y = np.log(df["med_drift"].to_numpy(float))
    lv = np.log(df["n_rows_deleted"].to_numpy(float))
    lv = lv - lv.mean()
    blk = (df["arm"] == "block").to_numpy(float)
    design = np.column_stack([np.ones(len(df)), lv, blk, blk * lv])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    return float(np.exp(beta[2]))


def paired_median(block: pd.DataFrame, matched: pd.DataFrame) -> float:
    b = block.set_index("paper")["med_drift"]
    m = matched.groupby("paper")["med_drift"].median()
    return float(np.median(b / m))


def summarize(values) -> tuple[float, float, float]:
    x = np.asarray(values, float)
    return float(np.median(x)), float(np.min(x)), float(np.max(x))


def main() -> None:
    X, rho, paper = load_curated()
    rows = []
    for drop, add in RATES:
        bf, pr_full, pr_coll = [], [], []
        for rep in range(REPS):
            rng = np.random.default_rng(SEED + 1000 + rep)
            Xp = perturb(X, drop, add, rng)
            fb, fm, cb, cm = audit(Xp, paper)
            bf.append(block_factor(fb, fm))
            pr_full.append(paired_median(fb, fm))
            pr_coll.append(paired_median(cb, cm))
        bf_med, bf_min, bf_max = summarize(bf)
        pf_med, pf_min, pf_max = summarize(pr_full)
        pc_med, pc_min, pc_max = summarize(pr_coll)
        rows.append({
            "drop_rate": drop,
            "add_rate": add,
            "block_factor_median": bf_med,
            "block_factor_min": bf_min,
            "block_factor_max": bf_max,
            "paired_full_median": pf_med,
            "paired_full_min": pf_min,
            "paired_full_max": pf_max,
            "paired_collapsed_median": pc_med,
            "paired_collapsed_min": pc_min,
            "paired_collapsed_max": pc_max,
            "n": REPS,
        })
        print(f"drop={drop:.3f} add={add:.3f} "
              f"block={bf_med:.5f} ({bf_min:.5f}-{bf_max:.5f}) "
              f"full={pf_med:.5f} ({pf_min:.5f}-{pf_max:.5f}) "
              f"collapsed={pc_med:.5f} ({pc_min:.5f}-{pc_max:.5f})")

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
