#!/usr/bin/env python3
"""Panel decomposition and study-density-matched collapsed control.

Adds the two checks needed to interpret the full-versus-collapsed contrast:

1. 2x2 decomposition of fit (full/weighted) and evaluation set (all rows /
   unique configurations), on a common evaluation set per draw.
2. Study-density-stratified donor control on the collapsed matrix.

The evaluation set is the set of rows retained in both the block and matched
fits (common evaluation).  The unique-row variant restricts that set to the
first occurrence of each within-paper coverage configuration.

Writes results/post_audit/panel_decomposition.json.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import (  # noqa: E402
    DRAWS, fit, weighted_pca, row_weights, median_ci,
    unique_mask, common_ratio, load_curated, seed_for,
)

OUT = os.path.join(ROOT, "results", "post_audit")
DATA = OUT
if not os.path.exists(os.path.join(DATA, "baseline_block.csv")):
    DATA = os.path.join(ROOT, "data")


def run_decomposition(X, rho, paper):
    n = len(X)
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    assert uni.sum() == 151, uni.sum()

    S_full = fit(X)
    w = row_weights(X, paper)
    S_full_w = weighted_pca(X, w)

    Xc = X[uni]
    paper_c = paper[uni]
    S_full_c = fit(Xc)

    out = {k: {} for k in ("full_all", "full_unique",
                            "weighted_all", "weighted_unique",
                            "collapsed_unique")}

    for p in papers:
        idx_p = np.where(paper == p)[0]
        n_p = len(idx_p)
        keep_block = paper != p
        block_rows = np.where(keep_block)[0]
        S_block = fit(X[keep_block])
        S_block_w = weighted_pca(X[keep_block], w[keep_block])

        keep_block_c = paper_c != p
        block_rows_c = np.where(keep_block_c)[0]
        S_block_c = fit(Xc[keep_block_c])
        n_u = int(uni[idx_p].sum())

        donors = np.where(paper != p)[0]
        donors_c = np.where(paper_c != p)[0]
        base = seed_for(str(p))

        ratios = {k: [] for k in out}
        for dr in range(DRAWS):
            rng = np.random.default_rng(base + 7919 * dr)

            drop = rng.choice(donors, size=n_p, replace=False)
            keep_match = np.ones(n, bool)
            keep_match[drop] = False
            match_rows = np.where(keep_match)[0]
            S_match = fit(X[keep_match])
            S_match_w = weighted_pca(X[keep_match], w[keep_match])

            common = keep_block & keep_match
            common_u = common & uni

            ratios["full_all"].append(
                common_ratio(S_full, S_block, block_rows,
                             S_match, match_rows, common))
            ratios["full_unique"].append(
                common_ratio(S_full, S_block, block_rows,
                             S_match, match_rows, common_u))
            ratios["weighted_all"].append(
                common_ratio(S_full_w, S_block_w, block_rows,
                             S_match_w, match_rows, common))
            ratios["weighted_unique"].append(
                common_ratio(S_full_w, S_block_w, block_rows,
                             S_match_w, match_rows, common_u))

            # Collapsed fit: draw the same number of unique rows as the
            # focal paper contributes.  The evaluation set is the unique
            # rows retained in both fits.
            drop_c = rng.choice(donors_c, size=n_u, replace=False)
            keep_match_c = np.ones(len(Xc), bool)
            keep_match_c[drop_c] = False
            match_rows_c = np.where(keep_match_c)[0]
            S_match_c = fit(Xc[keep_match_c])
            common_c = keep_block_c & keep_match_c
            ratios["collapsed_unique"].append(
                common_ratio(S_full_c, S_block_c, block_rows_c,
                             S_match_c, match_rows_c, common_c))

        for k in out:
            out[k][p] = float(np.median(ratios[k]))

    return {k: median_ci(list(v.values())) for k, v in out.items()}, out


def density_matched_collapsed(X, rho, paper):
    """Collapsed audit with donors drawn from same study-density quartile."""
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    Xc = X[uni]
    paper_c = paper[uni]
    rho_s = {p: float(np.mean(rho[paper == p])) for p in papers}
    cuts = np.quantile([rho_s[p] for p in papers], [0.25, 0.50, 0.75])
    qbin = {p: int(np.searchsorted(cuts, rho_s[p], side="right")) for p in papers}

    S_full_c = fit(Xc)
    out = {}
    for p in papers:
        keep_block_c = paper_c != p
        block_rows_c = np.where(keep_block_c)[0]
        S_block_c = fit(Xc[keep_block_c])
        n_u = int(uni[paper == p].sum())

        pool_papers = [q for q in papers if q != p and qbin[q] == qbin[p]]
        if len(pool_papers) < 5:
            # widen to the two nearest quartiles
            pool_papers = [q for q in papers if q != p
                           and abs(qbin[q] - qbin[p]) <= 1]
        pool_rows = np.where(np.isin(paper_c, pool_papers))[0]
        if len(pool_rows) < n_u:
            pool_rows = np.where(paper_c != p)[0]

        base = seed_for("dens" + p)
        ratios = []
        for dr in range(DRAWS):
            rng = np.random.default_rng(base + 7919 * dr)
            order = rng.permutation(pool_rows)
            cap = max(1, int(np.ceil(0.5 * n_u)))
            counts = Counter()
            chosen = []
            for j in order:
                s = paper_c[j]
                if counts[s] < cap:
                    chosen.append(int(j))
                    counts[s] += 1
                    if len(chosen) == n_u:
                        break
            if len(chosen) < n_u:
                used = set(chosen)
                for j in order:
                    if int(j) not in used:
                        chosen.append(int(j))
                        if len(chosen) == n_u:
                            break
            drop_c = np.asarray(chosen, int)
            keep_match_c = np.ones(len(Xc), bool)
            keep_match_c[drop_c] = False
            match_rows_c = np.where(keep_match_c)[0]
            S_match_c = fit(Xc[keep_match_c])
            common_c = keep_block_c & keep_match_c
            ratios.append(common_ratio(S_full_c, S_block_c, block_rows_c,
                                       S_match_c, match_rows_c, common_c))
        out[p] = float(np.median(ratios))
    return median_ci(list(out.values())), out, qbin


def main():
    X, rho, paper = load_curated()
    print("loaded", X.shape, len(set(paper)), "unique", unique_mask(X, paper).sum())

    dec, per_paper = run_decomposition(X, rho, paper)
    dens, dens_per_paper, qbin = density_matched_collapsed(X, rho, paper)

    # Duplication quartiles from the deposited event tables.
    import pandas as pd
    cm = pd.DataFrame({"paper": paper, "rho": rho})
    cm["key"] = [tuple(row.astype(int)) for row in X]
    g = cm.groupby("paper")
    rows = g.size().rename("rows")
    uniq = g["key"].nunique().rename("uniq")
    dup = (rows - uniq).rename("dup")
    dupfrac = (dup / rows).rename("dupfrac")
    rho_s = g["rho"].mean().rename("rho_s")
    df = pd.concat([rows, uniq, dup, dupfrac, rho_s], axis=1)

    b = pd.read_csv(os.path.join(DATA, "baseline_block.csv")).set_index("paper")["med_drift"]
    m = (pd.read_csv(os.path.join(DATA, "baseline_matched.csv"))
         .groupby("paper")["med_drift"].median())
    cb = pd.read_csv(os.path.join(DATA, "collapsed_block.csv")).set_index("paper")["med_drift"]
    cmat = (pd.read_csv(os.path.join(DATA, "collapsed_matched.csv"))
            .groupby("paper")["med_drift"].median())
    df["full_ratio"] = b / m
    df["collapsed_ratio"] = cb / cmat

    df["dup_q"] = pd.qcut(df["dup"], 4, labels=False, duplicates="drop")
    dupq = (df.groupby("dup_q")
            .agg(n=("full_ratio", "size"),
                 full=("full_ratio", "median"),
                 collapsed=("collapsed_ratio", "median"),
                 rows=("rows", "median"),
                 rho=("rho_s", "median"))
            .reset_index()
            .to_dict(orient="records"))

    df["rho_q"] = pd.qcut(df["rho_s"], 4, labels=False, duplicates="drop")
    rhoq = (df.groupby("rho_q")
            .agg(n=("full_ratio", "size"),
                 full=("full_ratio", "median"),
                 collapsed=("collapsed_ratio", "median"))
            .reset_index()
            .to_dict(orient="records"))

    result = {
        "n_rows": int(len(X)),
        "n_papers": int(len(set(paper))),
        "n_unique": int(unique_mask(X, paper).sum()),
        "decomposition": dec,
        "decomposition_per_paper": {k: {p: float(v) for p, v in d.items()}
                                    for k, d in per_paper.items()},
        "density_matched_collapsed": dens,
        "density_matched_collapsed_per_paper": {p: float(v) for p, v in dens_per_paper.items()},
        "density_quartile_bin": {p: int(v) for p, v in qbin.items()},
        "duplication_quartiles": dupq,
        "density_quartiles": rhoq,
        "correlations": {
            "full_vs_dup": float(stats.spearmanr(df["dup"], df["full_ratio"]).statistic),
            "full_vs_dupfrac": float(stats.spearmanr(df["dupfrac"], df["full_ratio"]).statistic),
            "full_vs_rows": float(stats.spearmanr(df["rows"], df["full_ratio"]).statistic),
            "full_vs_rho": float(stats.spearmanr(df["rho_s"], df["full_ratio"]).statistic),
            "collapsed_vs_dup": float(stats.spearmanr(df["dup"], df["collapsed_ratio"]).statistic),
            "collapsed_vs_rows": float(stats.spearmanr(df["rows"], df["collapsed_ratio"]).statistic),
            "collapsed_vs_rho": float(stats.spearmanr(df["rho_s"], df["collapsed_ratio"]).statistic),
        },
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "panel_decomposition.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("decomposition_per_paper",
                                   "density_matched_collapsed_per_paper",
                                   "density_quartile_bin")}, indent=2))


if __name__ == "__main__":
    main()
