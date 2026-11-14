#!/usr/bin/env python3
"""core_revision_checks.py — revision checks for the EES coverage audit.

Adds the checks requested in review:

1. exact-match subset under a density-only control;
2. exact-match subset under a capped volume control;
3. volume-matched ratio evaluated on a common evaluation set;
4. study-level (same-size) block percentile;
5. PC1/PC2 association with row density.

Reads the frozen curated coverage layer and the deposited event tables.
Writes results/core_revision/core_checks.json.

Run: python3 code/core_revision_checks.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import (  # noqa: E402
    SEED, DRAWS, N_BOOT, EXCLUDED, data_dir, fit, drift, median_ci, seed_for,
    load_curated,
)

EXCLUDE = EXCLUDED
DATA = data_dir()
RESULTS = DATA if os.path.exists(os.path.join(DATA, "coverage_events.csv")) else os.path.join(ROOT, "results", "wp3_clean")
OUT = os.path.join(ROOT, "results", "core_revision")
os.makedirs(OUT, exist_ok=True)


def capped_draw(donors, n, cap, paper, rng):
    """Random donor rows with at most ``cap`` rows from any donor study."""
    order = rng.permutation(donors)
    counts: Counter = Counter()
    chosen = []
    for j in order:
        s = paper[j]
        if counts[s] < cap:
            chosen.append(int(j))
            counts[s] += 1
            if len(chosen) == n:
                break
    if len(chosen) < n:
        # Relax the cap only if the cap is infeasible (should not happen here).
        used = set(chosen)
        for j in order:
            if int(j) not in used:
                chosen.append(int(j))
                if len(chosen) == n:
                    break
    assert len(chosen) == n
    return np.asarray(chosen, int)


def coarsened_draw(idx_p, donor_rows, H, rho, paper, cap, rng):
    """Greedy nearest-configuration donor rows, with a per-study cap.

    H is the pairwise Hamming distance between 44-bit coverage configurations.
    Exact matches are preferred; near matches are next; density difference is
    a tie-breaker.  Returns the chosen donor rows and the focal rows in the
    same order so match quality can be summarized.
    """
    used = np.zeros(len(rho), bool)
    counts: Counter = Counter()
    focal = []
    chosen = []
    for i in rng.permutation(idx_p):
        candidates = donor_rows[~used[donor_rows]]
        if len(candidates) == 0:
            raise RuntimeError("no donor rows left")
        cost = (H[i, candidates].astype(float)
                + 1e-3 * np.abs(rho[i] - rho[candidates])
                + rng.random(len(candidates)) * 1e-6)
        over = np.asarray([counts[paper[j]] >= cap for j in candidates])
        cost[over] = np.inf
        if not np.isfinite(cost).any():
            # Relax the cap only if it is infeasible.
            cost = (H[i, candidates].astype(float)
                    + 1e-3 * np.abs(rho[i] - rho[candidates])
                    + rng.random(len(candidates)) * 1e-6)
        j = int(candidates[int(np.argmin(cost))])
        focal.append(int(i))
        chosen.append(j)
        used[j] = True
        counts[paper[j]] += 1
    return np.asarray(chosen, int), np.asarray(focal, int)


def paired_stats(a, b):
    """Median paired difference a - b, bootstrap CI, and Wilcoxon p."""
    idx = sorted(set(a.index) & set(b.index))
    d = (a.loc[idx] - b.loc[idx]).to_numpy(float)
    rng = np.random.default_rng(SEED)
    boot = np.empty(N_BOOT)
    for i in range(N_BOOT):
        boot[i] = np.median(d[rng.integers(0, len(d), len(d))])
    return {
        "median_diff": float(np.median(d)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "wilcoxon_p": float(stats.wilcoxon(d).pvalue),
        "n": int(len(d)),
    }


def same_size_permutation(block, sizes, n_perm=10000):
    """Permute block drift within same-size groups; calibrate tail counts."""
    groups = {}
    for p in block.index:
        groups.setdefault(int(sizes.loc[p]), []).append(p)
    groups = {k: sorted(v) for k, v in groups.items() if len(v) > 1}

    def pct_map(values_by_paper):
        out = {}
        for members in groups.values():
            vals = np.asarray([values_by_paper[p] for p in members], float)
            for i, p in enumerate(members):
                peers = np.delete(vals, i)
                out[p] = 100.0 * (np.sum(peers < vals[i]) +
                                  0.5 * np.sum(peers == vals[i])) / len(peers)
        return out

    observed = pct_map(block["med_drift"].to_dict())
    obs_above = int(sum(v > 95 for v in observed.values()))
    obs_below = int(sum(v < 5 for v in observed.values()))

    rng = np.random.default_rng(SEED)
    null_above = np.empty(n_perm, int)
    null_below = np.empty(n_perm, int)
    for b in range(n_perm):
        permuted = {}
        for members in groups.values():
            vals = block.loc[members, "med_drift"].to_numpy(float)
            vals = rng.permutation(vals)
            for p, v in zip(members, vals):
                permuted[p] = float(v)
        pm = pct_map(permuted)
        null_above[b] = int(sum(v > 95 for v in pm.values()))
        null_below[b] = int(sum(v < 5 for v in pm.values()))

    return {
        "n_studies": int(len(observed)),
        "observed_above95": obs_above,
        "observed_below5": obs_below,
        "null_above95_median": float(np.median(null_above)),
        "null_above95_q975": float(np.quantile(null_above, 0.975)),
        "p_upper": float((1 + np.sum(null_above >= obs_above)) / (n_perm + 1)),
        "null_below5_median": float(np.median(null_below)),
        "null_below5_q975": float(np.quantile(null_below, 0.975)),
        "p_lower": float((1 + np.sum(null_below >= obs_below)) / (n_perm + 1)),
    }


def main():
    X, rho, paper = load_curated()
    n = len(X)
    uniq = sorted(set(paper))
    S_full = fit(X)

    events = pd.read_csv(os.path.join(RESULTS, "coverage_events.csv"))
    block = events[events["arm"] == "block"].set_index("paper")
    matched = events[events["arm"] == "matched"].groupby("paper")["med_drift"].median()
    assert len(block) == 117
    sizes = block["n_rows_deleted"].astype(int)
    H = (X[:, None, :] != X[None, :, :]).sum(axis=2)

    # Existing per-study ratios (volume, uncapped, all retained rows).
    volume_all = (block["med_drift"] / matched.reindex(block.index)).dropna()

    # Composition and density controls (existing).
    comp = pd.read_csv(os.path.join(RESULTS, "composition_matched_control.csv"))
    comp_med = (comp[comp["arm"] == "composition_matched"]
                .groupby("paper")["med_drift"].median())
    dens_med = (comp[comp["arm"] == "density_only"]
                .groupby("paper")["med_drift"].median())
    comp_ratio = (block["med_drift"] / comp_med.reindex(block.index)).dropna()
    dens_ratio = (block["med_drift"] / dens_med.reindex(block.index)).dropna()

    # Exact-match subset, as used in the manuscript.
    exact = (comp[comp["arm"] == "composition_matched"]
             .groupby("paper")["exact_fraction"].mean())
    exact_papers = sorted(exact[exact > 0].index)
    assert len(exact_papers) == 21

    volume_common = {}
    volume_capped = {}
    volume_all_check = {}

    for p in uniq:
        idx = np.where(paper == p)[0]
        n_p = len(idx)
        keep_block = np.ones(n, bool)
        keep_block[idx] = False
        block_keep_idx = np.where(keep_block)[0]
        S_block = fit(X[keep_block])
        block_drift = drift(S_full[keep_block], S_block)

        donors = np.where(paper != p)[0]
        cap = max(1, int(np.ceil(0.5 * n_p)))

        common_ratios = []
        match_meds = []
        for dr in range(DRAWS):
            rng = np.random.default_rng(seed_for(p) + 7919 * dr)
            drop = rng.choice(donors, size=n_p, replace=False)
            keep_match = np.ones(n, bool)
            keep_match[drop] = False
            S_match = fit(X[keep_match])
            match_drift = drift(S_full[keep_match], S_match)
            match_meds.append(float(np.median(match_drift)))

            # Common evaluation set: rows retained in both fits.  The block
            # drift on this set varies with the donor draw, so the per-draw
            # ratio is summarized by its median across draws.
            common = np.where(keep_block & keep_match)[0]
            pos_b = np.searchsorted(block_keep_idx, common)
            match_keep_idx = np.where(keep_match)[0]
            pos_m = np.searchsorted(match_keep_idx, common)
            common_ratios.append(float(np.median(block_drift[pos_b]) /
                                       np.median(match_drift[pos_m])))

        cap_meds = []
        for dr in range(DRAWS):
            rng_cap = np.random.default_rng(seed_for(p) + 100000 + 7919 * dr)
            drop = capped_draw(donors, n_p, cap, paper, rng_cap)
            keep_match = np.ones(n, bool)
            keep_match[drop] = False
            S_match = fit(X[keep_match])
            match_drift = drift(S_full[keep_match], S_match)
            cap_meds.append(float(np.median(match_drift)))

        block_med = float(np.median(block_drift))
        volume_all_check[p] = block_med / float(np.median(match_meds))
        volume_common[p] = float(np.median(common_ratios))
        volume_capped[p] = block_med / float(np.median(cap_meds))

    volume_all_check = pd.Series(volume_all_check).reindex(block.index)
    volume_common = pd.Series(volume_common).reindex(block.index)
    volume_capped = pd.Series(volume_capped).reindex(block.index)

    # Coarsened composition control: nearest 44-bit configuration, with cap.
    coarsened = {}
    coarsened_hamming = []
    coarsened_drho = []
    for p in uniq:
        idx = np.where(paper == p)[0]
        n_p = len(idx)
        keep_block = np.ones(n, bool)
        keep_block[idx] = False
        S_block = fit(X[keep_block])
        block_med = float(np.median(drift(S_full[keep_block], S_block)))
        donors = np.where(paper != p)[0]
        cap = max(1, int(np.ceil(0.5 * n_p)))
        vals = []
        for dr in range(DRAWS):
            rng = np.random.default_rng(seed_for(p) + 300000 + 7919 * dr)
            drop, focal = coarsened_draw(idx, donors, H, rho, paper, cap, rng)
            coarsened_hamming.extend(H[focal, drop].astype(float).tolist())
            coarsened_drho.extend(np.abs(rho[focal] - rho[drop]).tolist())
            keep_match = np.ones(n, bool)
            keep_match[drop] = False
            S_match = fit(X[keep_match])
            vals.append(block_med / float(np.median(
                drift(S_full[keep_match], S_match))))
        coarsened[p] = float(np.median(vals))
    coarsened = pd.Series(coarsened).reindex(block.index)

    # Confirm the recomputed uncapped all-row ratio matches the deposited table.
    match_diff = float(np.max(np.abs(volume_all_check - volume_all)))
    assert match_diff < 1e-9, match_diff

    # Study-level same-size percentile.
    sizes = block["n_rows_deleted"].astype(int)
    same_pct = {}
    for p in uniq:
        n_p = int(sizes.loc[p])
        peers = [q for q in uniq if q != p and int(sizes.loc[q]) == n_p]
        if not peers:
            same_pct[p] = np.nan
            continue
        vals = block.loc[peers, "med_drift"].to_numpy(float)
        own = float(block.loc[p, "med_drift"])
        same_pct[p] = float((np.sum(vals < own) + 0.5 * np.sum(vals == own)) /
                            len(vals) * 100.0)
    same_pct = pd.Series(same_pct)
    same_perm = same_size_permutation(block, sizes)

    # PC1/PC2 association with row density.
    S = PCA(n_components=2, random_state=SEED).fit_transform(X)
    pc = {
        "pc1_vs_rho": float(stats.spearmanr(S[:, 0], rho).statistic),
        "pc1_p": float(stats.spearmanr(S[:, 0], rho).pvalue),
        "pc2_vs_rho": float(stats.spearmanr(S[:, 1], rho).statistic),
        "pc2_p": float(stats.spearmanr(S[:, 1], rho).pvalue),
        "explained": [float(v) for v in
                      PCA(n_components=2, random_state=SEED).fit(X).explained_variance_ratio_],
    }

    def subset_summary(series):
        return median_ci(series.loc[exact_papers].to_numpy(float))

    out = {
        "n_rows": n,
        "n_papers": len(uniq),
        "volume_all": median_ci(volume_all.to_numpy(float)),
        "volume_common": median_ci(volume_common.to_numpy(float)),
        "volume_capped": median_ci(volume_capped.to_numpy(float)),
        "composition_all": median_ci(comp_ratio.to_numpy(float)),
        "density_all": median_ci(dens_ratio.to_numpy(float)),
        "exact": {
            "n": len(exact_papers),
            "volume_all": subset_summary(volume_all),
            "volume_common": subset_summary(volume_common),
            "volume_capped": subset_summary(volume_capped),
            "composition": subset_summary(comp_ratio),
            "density": subset_summary(dens_ratio),
            "volume_common_vs_all_median_diff": float(
                np.median(volume_common.loc[exact_papers] -
                          volume_all.loc[exact_papers])),
            "capped_vs_volume_median_diff": float(
                np.median(volume_capped.loc[exact_papers] -
                          volume_all.loc[exact_papers])),
            "capped_vs_composition_wilcoxon_p": float(
                stats.wilcoxon(volume_capped.loc[exact_papers],
                               comp_ratio.loc[exact_papers]).pvalue),
            "capped_vs_density_wilcoxon_p": float(
                stats.wilcoxon(volume_capped.loc[exact_papers],
                               dens_ratio.loc[exact_papers]).pvalue),
            "composition_vs_density_wilcoxon_p": float(
                stats.wilcoxon(comp_ratio.loc[exact_papers],
                               dens_ratio.loc[exact_papers]).pvalue),
        },
        "coarsened": {
            "all": median_ci(coarsened.to_numpy(float)),
            "exact": subset_summary(coarsened),
            "non_exact": median_ci(coarsened.drop(exact_papers).to_numpy(float)),
            "vs_volume": paired_stats(coarsened, volume_all),
            "vs_composition": paired_stats(coarsened, comp_ratio),
            "vs_density": paired_stats(coarsened, dens_ratio),
            "exact_vs_composition": paired_stats(
                coarsened.loc[exact_papers], comp_ratio.loc[exact_papers]),
            "exact_vs_density": paired_stats(
                coarsened.loc[exact_papers], dens_ratio.loc[exact_papers]),
            "match_quality": {
                "n": int(len(coarsened_hamming)),
                "hamming_mean": float(np.mean(coarsened_hamming)),
                "hamming_median": float(np.median(coarsened_hamming)),
                "pct_exact": float(np.mean(np.asarray(coarsened_hamming) == 0) * 100),
                "pct_le2": float(np.mean(np.asarray(coarsened_hamming) <= 2) * 100),
                "pct_le4": float(np.mean(np.asarray(coarsened_hamming) <= 4) * 100),
                "pct_gt8": float(np.mean(np.asarray(coarsened_hamming) > 8) * 100),
                "abs_rho_mean": float(np.mean(coarsened_drho)),
                "abs_rho_median": float(np.median(coarsened_drho)),
            },
        },
        "same_size_percentile": {
            "n": int(same_pct.notna().sum()),
            "median": float(same_pct.median()),
            "above95": int((same_pct > 95).sum()),
            "above95_pct": float((same_pct > 95).sum() /
                                 same_pct.notna().sum() * 100),
            "below5": int((same_pct < 5).sum()),
            "below5_pct": float((same_pct < 5).sum() /
                                same_pct.notna().sum() * 100),
            "permutation": same_perm,
        },
        "pc": pc,
    }

    with open(os.path.join(OUT, "core_checks.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
