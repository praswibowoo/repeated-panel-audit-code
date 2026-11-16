#!/usr/bin/env python3
"""Balance diagnostics for the block and matched deletion arms.

For each control (volume, study-density, coarsened composition, coherence) and
arm (block, matched), report the median deleted rows, unique configurations,
row density, water fraction, within-set mean Hamming distance, and the number
of donor papers.  A representative draw (draw 0) is used per study, with the
same seed convention as the main analyses.

Writes data/balance_diagnostics.csv.
"""
from __future__ import annotations

import os
import sys
from collections import Counter

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import data_dir, fit, load_curated, seed_for, unique_mask  # noqa: E402
from core_revision_checks import coarsened_draw  # noqa: E402

DATA = data_dir()
OUT = os.path.join(DATA, "balance_diagnostics.csv")


def mean_hamming(rows: np.ndarray) -> float:
    if len(rows) < 2:
        return 0.0
    vals = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            vals.append(int((rows[i] != rows[j]).sum()))
    return float(np.mean(vals))


def stats_for(rows: np.ndarray, Xsrc: np.ndarray, rhosrc: np.ndarray,
              watersrc: np.ndarray, papersrc: np.ndarray) -> dict:
    rows = np.asarray(rows, int)
    if len(rows) == 0:
        return {"rows": 0, "unique": 0, "density": np.nan,
                "water": np.nan, "hamming": np.nan, "donors": 0}
    uniq = np.unique(Xsrc[rows].astype(int), axis=0)
    return {
        "rows": int(len(rows)),
        "unique": int(len(uniq)),
        "density": float(np.mean(rhosrc[rows])),
        "water": float(np.mean(watersrc[rows])),
        "hamming": mean_hamming(uniq),
        "donors": int(len(set(papersrc[rows]))),
    }


def main() -> None:
    X, rho, paper = load_curated()
    cov = pd.read_csv(os.path.join(DATA, "coverage_matrix.csv"))[["paper", "row"]]
    types = pd.read_csv(os.path.join(DATA, "coverage_matrix_types.csv"))
    frame = cov.merge(types[["paper", "row", "water_only"]], on=["paper", "row"], how="left")
    water = frame["water_only"].to_numpy(bool)
    if len(water) != len(X):
        raise SystemExit("matrix-type map does not align with the coverage matrix")
    H = (X[:, None, :] != X[None, :, :]).sum(axis=2)
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    uni_idx = np.where(uni)[0]
    Xc = X[uni]
    rho_c = rho[uni]
    water_c = water[uni]
    paper_c = paper[uni]
    n_u = {p: int(uni[paper == p].sum()) for p in papers}
    rho_s = {p: float(np.mean(rho[paper == p])) for p in papers}
    cuts = np.quantile([rho_s[p] for p in papers], [0.25, 0.50, 0.75])
    qbin = {p: int(np.searchsorted(cuts, rho_s[p], side="right")) for p in papers}

    # Coherence metadata: within-paper mean Hamming of unique configurations.
    cfg = {p: X[uni & (paper == p)] for p in papers}
    h = {p: mean_hamming(cfg[p]) for p in papers}
    multi = [p for p in papers if n_u[p] > 1]

    controls = ("volume", "density", "composition", "coherence")
    rows = []
    for control in controls:
        block_stats, match_stats = [], []
        study_list = multi if control == "coherence" else papers
        for p in study_list:
            idx = np.where(paper == p)[0]
            n_p = len(idx)
            n = n_u[p]
            focal_unique_c = np.where(paper_c == p)[0]
            if control in ("volume", "composition"):
                block_stats.append(stats_for(idx, X, rho, water, paper))
            else:
                block_stats.append(stats_for(focal_unique_c, Xc, rho_c, water_c, paper_c))

            if control == "volume":
                donors = np.where(paper != p)[0]
                rng = np.random.default_rng(seed_for(p))
                drop = rng.choice(donors, size=n_p, replace=False)
                match_stats.append(stats_for(drop, X, rho, water, paper))

            elif control == "density":
                pool_papers = [q for q in papers if q != p and qbin[q] == qbin[p]]
                if len(pool_papers) < 5:
                    pool_papers = [q for q in papers if q != p
                                   and abs(qbin[q] - qbin[p]) <= 1]
                pool_rows = np.where(np.isin(paper_c, pool_papers))[0]
                if len(pool_rows) < n:
                    pool_rows = np.where(paper_c != p)[0]
                rng = np.random.default_rng(seed_for("dens" + p))
                order = rng.permutation(pool_rows)
                cap = max(1, int(np.ceil(0.5 * n)))
                counts = Counter()
                chosen = []
                for j in order:
                    s = paper_c[j]
                    if counts[s] < cap:
                        chosen.append(int(j))
                        counts[s] += 1
                        if len(chosen) == n:
                            break
                match_stats.append(stats_for(np.asarray(chosen), Xc, rho_c, water_c, paper_c))

            elif control == "composition":
                donors = np.where(paper != p)[0]
                cap = max(1, int(np.ceil(0.5 * n_p)))
                rng = np.random.default_rng(seed_for(p) + 300000)
                chosen, _ = coarsened_draw(idx, donors, H, rho, paper, cap, rng)
                match_stats.append(stats_for(chosen, X, rho, water, paper))

            elif control == "coherence":
                if p not in multi:
                    # One-configuration papers use the pooled control.
                    donors = [q for q in papers if q != p]
                else:
                    donors = [q for q in papers if q != p and n_u[q] == n_u[p]]
                    if not donors:
                        donors = [q for q in papers if q != p and n_u[q] > n_u[p]]
                    if not donors:
                        donors = [q for q in papers if q != p]
                    donors = sorted(donors, key=lambda q: abs(h[q] - h[p]))[:5]
                rng = np.random.default_rng(seed_for("coh" + p))
                q = donors[int(rng.integers(0, len(donors)))]
                q_rows = np.where(paper_c == q)[0]
                if len(q_rows) > n:
                    drop = rng.choice(q_rows, size=n, replace=False)
                else:
                    drop = q_rows
                match_stats.append(stats_for(drop, Xc, rho_c, water_c, paper_c))

        def agg(values, key):
            x = np.asarray([v[key] for v in values], float)
            return float(np.nanmedian(x))

        def mean(values, key):
            x = np.asarray([v[key] for v in values], float)
            return float(np.nanmean(x))

        for arm, vals in (("block", block_stats), ("matched", match_stats)):
            rows.append({
                "control": control,
                "arm": arm,
                "n_studies": len(study_list),
                "rows": agg(vals, "rows"),
                "unique": agg(vals, "unique"),
                "density": agg(vals, "density"),
                "water_fraction": mean(vals, "water"),
                "mean_hamming": agg(vals, "hamming"),
                "donor_papers": mean(vals, "donors"),
            })

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(out.round(3).to_string(index=False))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
