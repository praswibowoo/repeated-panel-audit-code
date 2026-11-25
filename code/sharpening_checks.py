#!/usr/bin/env python3
"""Sharpening checks for the EES coverage audit.

Three checks requested in the scope-sharpening pass:

1. Composition-prioritized *collapsed* control for all 117 studies.
   Donors are whole papers chosen by the distance between their mean unique
   coverage configuration and the focal paper's mean unique configuration.
   The matched arm removes the same number of unique configurations as the
   focal paper, with a per-donor cap of ceil(n_u / 2).

2. Volume-matched *unique-configuration* control for the full fit.
   The matched arm removes whole donor configurations until the total number
   of removed rows is as close as possible to the focal paper's row count.
   This is the missing volume-matched analogue of the full + unique cell.

3. Common-evaluation leverage model.
   The two-term log-ratio model is rerun on the common-evaluation
   per-paper ratios (factor factorial_per_paper), not the own-row ratios.

Writes manuscript/ees/reproducibility/sharpening_checks.json.

Run from the source root:
    python3 code/sharpening_checks.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import (  # noqa: E402
    DRAWS, N_BOOT, data_dir, fit, common_ratio, load_curated, median_ci,
    seed_for, unique_mask,
)

OUT = os.path.join(data_dir(), "sharpening_checks.json")


def find(name: str) -> str:
    """Resolve an input file in either the code package or the manuscript tree."""
    for root in (
        data_dir(),
        os.path.join(ROOT, "results", "post_audit"),
        os.path.join(ROOT, "manuscript", "ees", "reproducibility"),
    ):
        path = os.path.join(root, name)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(name)


def composition_collapsed(X, paper):
    """Collapsed audit with donors matched on mean coverage configuration."""
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    Xc = X[uni]
    paper_c = paper[uni]
    n_u = {p: int((paper_c == p).sum()) for p in papers}

    mean_cfg = {p: Xc[paper_c == p].mean(axis=0) for p in papers}
    # Pairwise Euclidean distance between mean coverage profiles.
    dist = {
        (p, q): float(np.linalg.norm(mean_cfg[p] - mean_cfg[q]))
        for p in papers for q in papers if p != q
    }

    S_full = fit(Xc)
    per_paper = {}
    match_hamming = []
    match_density = []
    for p in papers:
        keep_block = paper_c != p
        block_rows = np.where(keep_block)[0]
        S_block = fit(Xc[keep_block])
        k = n_u[p]

        # Pool of the ten compositionally nearest donor papers.
        donor_papers = sorted(
            [q for q in papers if q != p], key=lambda q: dist[(p, q)]
        )[:10]
        pool_rows = np.where(np.isin(paper_c, donor_papers))[0]
        if len(pool_rows) < k:
            donor_papers = [q for q in papers if q != p]
            pool_rows = np.where(np.isin(paper_c, donor_papers))[0]

        base = seed_for("compcoll" + p)
        ratios = []
        for dr in range(DRAWS):
            rng = np.random.default_rng(base + 7919 * dr)
            order = rng.permutation(pool_rows)
            cap = max(1, int(np.ceil(0.5 * k)))
            counts: Counter = Counter()
            chosen = []
            for j in order:
                s = paper_c[j]
                if counts[s] < cap:
                    chosen.append(int(j))
                    counts[s] += 1
                    if len(chosen) == k:
                        break
            if len(chosen) < k:
                used = set(chosen)
                for j in order:
                    if int(j) not in used:
                        chosen.append(int(j))
                        if len(chosen) == k:
                            break
            chosen = np.asarray(chosen, int)
            keep_match = np.ones(len(Xc), bool)
            keep_match[chosen] = False
            match_rows = np.where(keep_match)[0]
            S_match = fit(Xc[keep_match])
            common = keep_block & keep_match
            ratios.append(
                common_ratio(S_full, S_block, block_rows, S_match,
                             match_rows, common)
            )
            # Match quality: minimum Hamming from each focal configuration
            # to the selected donor configurations, and mean density gap.
            focal = Xc[paper_c == p]
            if len(chosen):
                H = (focal[:, None, :] != Xc[chosen][None, :, :]).sum(axis=2)
                match_hamming.append(float(np.mean(H.min(axis=1))))
                match_density.append(
                    float(abs(focal.mean() - Xc[chosen].mean()))
                )
        per_paper[p] = float(np.median(ratios))

    vals = np.asarray([per_paper[p] for p in papers], float)
    comp = pd.read_csv(find("composition_matched_control.csv"))
    exact = (comp[comp["arm"] == "composition_matched"]
             .groupby("paper")["exact_fraction"].mean())
    exact_papers = sorted(exact[exact > 0].index)

    def subset(ids):
        return median_ci(np.asarray([per_paper[p] for p in ids], float))

    return {
        "median": median_ci(vals),
        "exact_subset": subset(exact_papers),
        "non_exact_subset": subset([p for p in papers if p not in exact_papers]),
        "n_exact": len(exact_papers),
        "match_quality": {
            "mean_min_hamming": float(np.mean(match_hamming)),
            "median_min_hamming": float(np.median(match_hamming)),
            "mean_density_gap": float(np.mean(match_density)),
            "median_density_gap": float(np.median(match_density)),
        },
        "per_paper": per_paper,
    }


def _subset_sum_indices(donors_c, target, config_size):
    """Exact subset-sum fallback for donor pools without a one-row filler."""
    reachable = {0: None}
    for j in donors_c:
        s = int(config_size[j])
        if s > target:
            continue
        for prev in list(reachable):
            new = prev + s
            if new <= target and new not in reachable:
                reachable[new] = int(j)
        if target in reachable:
            break
    if target not in reachable:
        return None
    chosen = []
    cur = target
    while cur > 0:
        j = reachable[cur]
        if j is None:
            return None
        chosen.append(j)
        cur -= int(config_size[j])
    return chosen


def volume_matched_unique(X, paper):
    """Full fit, matched arm removes whole configurations with matched volume."""
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    uni_idx = np.where(uni)[0]
    Xc = X[uni]
    paper_c = paper[uni]
    n = len(X)

    # Full-matrix row indices for each unique configuration.
    config_rows = {}
    for j in range(len(Xc)):
        p = paper_c[j]
        same = np.where((paper == p) & np.all(X == Xc[j], axis=1))[0]
        config_rows[j] = same
    config_size = {j: len(v) for j, v in config_rows.items()}

    S_full = fit(X)
    per_paper = {}
    overshoot = []
    for p in papers:
        idx_p = np.where(paper == p)[0]
        n_p = len(idx_p)
        keep_block = paper != p
        block_rows = np.where(keep_block)[0]
        S_block = fit(X[keep_block])
        keep_block_c = paper_c != p
        n_u = int((paper_c == p).sum())

        donors_c = [j for j in range(len(Xc)) if paper_c[j] != p]
        base = seed_for("voluniq" + p)
        ratios = []
        gaps = []
        for dr in range(DRAWS):
            rng = np.random.default_rng(base + 7919 * dr)
            order = rng.permutation(donors_c)
            chosen = []
            total = 0
            for j in order:
                if total == n_p:
                    break
                gap = n_p - total
                if config_size[j] <= gap:
                    chosen.append(int(j))
                    total += config_size[j]
            if total != n_p:
                dp = _subset_sum_indices(donors_c, n_p, config_size)
                if dp is not None:
                    chosen = dp
                    total = n_p
            overshoot.append(total - n_p)
            gaps.append(total - n_p)

            drop_rows = np.concatenate([config_rows[j] for j in chosen])
            keep_match = np.ones(n, bool)
            keep_match[drop_rows] = False
            match_rows = np.where(keep_match)[0]
            S_match = fit(X[keep_match])

            keep_match_c = np.ones(len(Xc), bool)
            keep_match_c[chosen] = False
            common_c = keep_block_c & keep_match_c
            common_mask = np.zeros(n, bool)
            common_mask[uni_idx[common_c]] = True
            ratios.append(
                common_ratio(S_full, S_block, block_rows, S_match,
                             match_rows, common_mask)
            )
        exact_draws = [r for r, g in zip(ratios, gaps) if g == 0]
        per_paper[p] = {
            "all": float(np.median(ratios)),
            "exact_volume": (
                float(np.median(exact_draws)) if len(exact_draws) >= 10
                else None
            ),
            "n_exact_draws": int(len(exact_draws)),
        }

    vals = np.asarray([per_paper[p]["all"] for p in papers], float)
    exact_papers = [p for p in papers if per_paper[p]["exact_volume"] is not None]
    exact_vals = np.asarray(
        [per_paper[p]["exact_volume"] for p in exact_papers], float
    )
    return {
        "median": median_ci(vals),
        "exact_volume_median": (
            median_ci(exact_vals) if len(exact_vals) else None
        ),
        "n_exact_volume_papers": int(len(exact_papers)),
        "volume_gap": {
            "mean_rows": float(np.mean(overshoot)),
            "median_rows": float(np.median(overshoot)),
            "max_abs_rows": float(np.max(np.abs(overshoot))),
            "frac_exact": float(np.mean(np.asarray(overshoot) == 0)),
        },
        "per_paper": per_paper,
    }


def common_leverage():
    """Two-term log-ratio model on the common-evaluation per-paper ratios."""
    panel = json.load(open(find("panel_decomposition.json")))
    lev = pd.read_csv(find("leverage_per_paper.csv"))
    if "Unnamed: 0" in lev.columns:
        lev = lev.rename(columns={"Unnamed: 0": "paper"})
    fac = panel["factorial_per_paper"]
    papers = sorted(fac["full_row"])
    df = pd.DataFrame({
        "paper": papers,
        "full": [fac["full_row"][p] for p in papers],
        "coll": [fac["collapsed_unique"][p] for p in papers],
    })
    lev = lev.set_index("paper")
    df = df.set_index("paper").join(lev[["lev", "n_rows", "rho"]], how="left")
    assert df["lev"].notna().all(), df[df["lev"].isna()]

    out = {"n": int(len(df))}
    from scipy import stats

    out["spearman"] = {}
    for a in ("lev", "n_rows", "rho"):
        for b in ("full", "coll"):
            r, p = stats.spearmanr(df[a], df[b])
            out["spearman"][f"{a}_vs_{b}"] = {
                "rho": float(r), "p": float(p)
            }

    rng = np.random.default_rng(42)
    for name, ycol in (("full", "full"), ("coll", "coll")):
        y = np.log(df[ycol].to_numpy(float))
        Xd = np.column_stack([
            np.ones(len(df)),
            np.log(df["n_rows"].to_numpy(float)),
            df["lev"].to_numpy(float),
        ])
        beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
        resid = y - Xd @ beta
        boot = np.empty((N_BOOT, 3))
        for i in range(N_BOOT):
            idx = rng.integers(0, len(y), len(y))
            boot[i], *_ = np.linalg.lstsq(Xd[idx], y[idx], rcond=None)
        lo, hi = np.quantile(boot, [0.025, 0.975], axis=0)
        # Standardized coefficients: change in log ratio per SD of covariate.
        sd_rows = np.std(np.log(df["n_rows"].to_numpy(float)), ddof=1)
        sd_lev = np.std(df["lev"].to_numpy(float), ddof=1)
        out[name] = {
            "log_rows": float(beta[1]),
            "log_rows_ci": [float(lo[1]), float(hi[1])],
            "leverage": float(beta[2]),
            "leverage_ci": [float(lo[2]), float(hi[2])],
            "log_rows_per_sd": float(beta[1] * sd_rows),
            "leverage_per_sd": float(beta[2] * sd_lev),
            "r2": float(1 - resid.var() / y.var()),
            "sd_log_rows": float(sd_rows),
            "sd_leverage": float(sd_lev),
        }
    return out


def paired_difference(a: dict, b: dict) -> dict:
    """Median paired difference a - b with a percentile bootstrap CI."""
    idx = sorted(set(a) & set(b))
    d = np.asarray([a[p] - b[p] for p in idx], float)
    rng = np.random.default_rng(42)
    boot = np.empty(N_BOOT)
    for i in range(N_BOOT):
        boot[i] = np.median(d[rng.integers(0, len(d), len(d))])
    return {
        "median": float(np.median(d)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n": int(len(d)),
    }


def main():
    X, rho, paper = load_curated()
    comp = composition_collapsed(X, paper)
    vol = volume_matched_unique(X, paper)
    panel = json.load(open(find("panel_decomposition.json")))
    collapsed = panel["factorial_per_paper"]["collapsed_unique"]
    vol_exact = {
        p: v["exact_volume"] for p, v in vol["per_paper"].items()
        if v["exact_volume"] is not None
    }
    out = {
        "n_rows": int(len(X)),
        "n_papers": int(len(set(paper))),
        "composition_collapsed": comp,
        "volume_matched_unique": vol,
        "common_leverage": common_leverage(),
        "paired_differences": {
            "control_row_minus_volume_unique": paired_difference(
                panel["factorial_per_paper"]["full_row"], vol_exact
            ),
            "composition_collapsed_minus_collapsed": paired_difference(
                comp["per_paper"], collapsed
            ),
            "volume_matched_unique_exact_minus_collapsed": paired_difference(
                vol_exact, collapsed
            ),
        },
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps({
        "composition_collapsed": {
            k: v for k, v in out["composition_collapsed"].items()
            if k != "per_paper"
        },
        "volume_matched_unique": {
            k: v for k, v in out["volume_matched_unique"].items()
            if k != "per_paper"
        },
        "common_leverage": out["common_leverage"],
        "paired_differences": out["paired_differences"],
    }, indent=2))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
