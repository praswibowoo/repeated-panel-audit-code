#!/usr/bin/env python3
"""Unified three-arm common-evaluation audit for the unit-of-deletion revision.

Designs, all evaluated on one common configuration set E_{s,d}:

  A  row-count control, full fit          (n_s scattered donor rows)
  B  volume-matched whole-configuration control, full fit (exact n_s rows)
  C  unique-configuration control, collapsed fit (n_{u,s} donor configurations)

The block arm is the focal study's full row block (A, B) or its collapsed
configuration block (C).  Every arm is evaluated on the configurations retained
in all four reduced fits (block, A, B, C), using one retained row per
configuration.  This makes A - C = (A - B) + (B - C) exact per study.

Outputs results/unit_revision/common_contrast.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    DRAWS, N_BOOT, drift, fit, load_curated, seed_for, unique_mask,
)


def subset_sum_indices(donors_c, target, config_size):
    """Exact subset-sum fallback for donor pools without a one-row filler.

    Bitset-style dynamic program over the small integer targets in this corpus.
    Returns a list of donor configuration indices summing to ``target``, or
    ``None`` if no exact combination exists.
    """
    reachable = {0: None}
    for j in donors_c:
        s = int(config_size[j])
        if s > target:
            continue
        snapshot = list(reachable.items())
        for prev, _ in snapshot:
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
        chosen.append(int(j))
        cur -= int(config_size[j])
    return chosen


def exact_volume_indices(donors_c, target, config_size, rng):
    """Gap-aware random-order greedy that always reaches exactly ``target``.

    A one-row donor configuration is always available in this corpus, so the
    greedy fills any residual gap.  The old random-order accumulator accepted
    a first configuration larger than the target, which is why it failed 31.6%
    of draws.  This version never accepts a configuration larger than the
    remaining gap.
    """
    order = rng.permutation(donors_c)
    chosen = []
    total = 0
    for j in order:
        if total == target:
            break
        gap = target - total
        if config_size[j] <= gap:
            chosen.append(int(j))
            total += int(config_size[j])
    if total != target:
        # Deterministic fill with unused one-row configurations.  This branch
        # should not trigger; it is a guard against pathological donor pools.
        chosen_set = set(chosen)
        for j in donors_c:
            if total == target:
                break
            if int(j) in chosen_set:
                continue
            if config_size[j] == 1:
                chosen.append(int(j))
                chosen_set.add(int(j))
                total += 1
    if total != target:
        dp = subset_sum_indices(donors_c, target, config_size)
        if dp is not None:
            return dp
        raise RuntimeError(f"exact volume match failed: target={target}, total={total}")
    return chosen


def median_ci(values, n_boot=N_BOOT, seed=42):
    x = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        boot[i] = np.median(x[rng.integers(0, len(x), len(x))])
    return {
        "median": float(np.median(x)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n": int(len(x)),
    }


def describe(values):
    x = np.asarray(values, float)
    q = np.quantile(x, [0.25, 0.5, 0.75])
    return {
        "median": float(q[1]),
        "iqr_lo": float(q[0]),
        "iqr_hi": float(q[2]),
        "mean": float(np.mean(x)),
        "sd": float(np.std(x, ddof=1)),
        "frac_positive": float(np.mean(x > 0)),
        "frac_above_0p1": float(np.mean(x > 0.1)),
        "frac_below_minus_0p1": float(np.mean(x < -0.1)),
        "n": int(len(x)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=DRAWS)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    X, rho, paper = load_curated()
    papers = sorted(set(paper))
    n = len(X)
    uni = unique_mask(X, paper)
    uni_idx = np.where(uni)[0]
    Xc = X[uni]
    pc = paper[uni]
    n_c = len(Xc)

    config_rows = []
    for j in range(n_c):
        p = pc[j]
        config_rows.append(
            np.where((paper == p) & np.all(X == Xc[j], axis=1))[0]
        )
    config_size = np.array([len(v) for v in config_rows], int)

    S_full = fit(X)
    S_full_c = fit(Xc)

    per_paper = {
        k: {} for k in ("A", "B", "C", "AB", "BC", "AC", "nE", "gap")
    }
    per_paper_draws = {k: {} for k in ("A", "B", "C", "AB", "BC", "AC")}
    meta = {}
    exact_draws = 0
    total_draws = 0
    gaps = []

    for pi, p in enumerate(papers):
        idx_p = np.where(paper == p)[0]
        n_p = int(len(idx_p))
        n_u = int(uni[idx_p].sum())
        keep_block = paper != p
        block_rows = np.where(keep_block)[0]
        keep_block_c = pc != p
        block_rows_c = np.where(keep_block_c)[0]
        donors = np.where(paper != p)[0]
        donors_c = np.where(pc != p)[0]
        S_block = fit(X[keep_block])
        S_block_c = fit(Xc[keep_block_c])

        draws = {k: [] for k in ("A", "B", "C", "AB", "BC", "AC", "nE", "gap")}
        base = seed_for(str(p))
        for dr in range(args.draws):
            rng = np.random.default_rng(base + 7919 * dr)

            # A: row-count control, full fit.
            drop_A = rng.choice(donors, size=n_p, replace=False)
            keep_A = np.ones(n, bool)
            keep_A[drop_A] = False
            match_rows_A = np.where(keep_A)[0]
            S_A = fit(X[keep_A])

            # B: exact volume-matched whole-configuration control, full fit.
            chosen_B = exact_volume_indices(donors_c, n_p, config_size, rng)
            drop_rows_B = np.concatenate([config_rows[j] for j in chosen_B])
            keep_B = np.ones(n, bool)
            keep_B[drop_rows_B] = False
            match_rows_B = np.where(keep_B)[0]
            S_B = fit(X[keep_B])
            gap = int(config_size[chosen_B].sum() - n_p)
            gaps.append(gap)
            exact_draws += int(gap == 0)
            total_draws += 1

            # C: unique-configuration control, collapsed fit.
            drop_C = rng.choice(donors_c, size=n_u, replace=False)
            keep_C_c = np.ones(n_c, bool)
            keep_C_c[drop_C] = False
            match_rows_C_c = np.where(keep_C_c)[0]
            S_C = fit(Xc[keep_C_c])

            # Common configuration set: retained in block, A, B, and C.
            retained_A = np.array(
                [np.any(keep_A[config_rows[j]]) for j in range(n_c)], bool
            )
            in_B = np.zeros(n_c, bool)
            in_B[chosen_B] = True
            in_C = np.zeros(n_c, bool)
            in_C[drop_C] = True
            common_c = keep_block_c & retained_A & (~in_B) & (~in_C)
            E = np.where(common_c)[0]
            if len(E) < 3:
                continue

            # One row per configuration that is retained in both A and B.
            rows = []
            for j in E:
                rr = config_rows[j]
                rr = rr[keep_A[rr] & keep_B[rr]]
                if len(rr) == 0:
                    break
                rows.append(int(rr[0]))
            if len(rows) != len(E):
                continue
            rows = np.asarray(rows, int)

            pos_block = np.searchsorted(block_rows, rows)
            pos_A = np.searchsorted(match_rows_A, rows)
            pos_B = np.searchsorted(match_rows_B, rows)
            pos_block_c = np.searchsorted(block_rows_c, E)
            pos_C = np.searchsorted(match_rows_C_c, E)

            dB_full = float(np.median(drift(S_full[rows], S_block[pos_block])))
            dA = float(np.median(drift(S_full[rows], S_A[pos_A])))
            dB_vol = float(np.median(drift(S_full[rows], S_B[pos_B])))
            dB_coll = float(np.median(drift(S_full_c[E], S_block_c[pos_block_c])))
            dC = float(np.median(drift(S_full_c[E], S_C[pos_C])))

            R_A = dB_full / dA
            R_B = dB_full / dB_vol
            R_C = dB_coll / dC
            draws["A"].append(R_A)
            draws["B"].append(R_B)
            draws["C"].append(R_C)
            draws["AB"].append(R_A - R_B)
            draws["BC"].append(R_B - R_C)
            draws["AC"].append(R_A - R_C)
            draws["nE"].append(len(E))
            draws["gap"].append(gap)

        for k, v in draws.items():
            if not v:
                raise RuntimeError(f"no draws for {p}")
            per_paper[k][p] = float(np.median(v))
        for k in per_paper_draws:
            per_paper_draws[k][p] = [float(x) for x in draws[k]]
        meta[p] = {"n_p": n_p, "n_u": n_u}

        if pi % 10 == 0:
            print(f"{pi}/{len(papers)} {p} n_p={n_p} n_u={n_u}", flush=True)

    designs = {k: median_ci(list(per_paper[k].values())) for k in ("A", "B", "C")}
    contrasts = {k: describe(list(per_paper[k].values())) for k in ("AB", "BC", "AC")}
    contrasts_ci = {k: median_ci(list(per_paper[k].values())) for k in ("AB", "BC", "AC")}
    for k in contrasts:
        contrasts[k].update(
            {"ci_lo": contrasts_ci[k]["ci_lo"], "ci_hi": contrasts_ci[k]["ci_hi"]}
        )

    A = np.array([per_paper["A"][p] for p in papers])
    B = np.array([per_paper["B"][p] for p in papers])
    C = np.array([per_paper["C"][p] for p in papers])
    nE = np.array([per_paper["nE"][p] for p in papers])

    def overlap(x, y, k):
        return int(len(set(np.argsort(-x)[:k]) & set(np.argsort(-y)[:k])))

    out = {
        "n_papers": len(papers),
        "n_rows": int(n),
        "n_configs": int(n_c),
        "n_draws": args.draws,
        "designs": designs,
        "contrasts": contrasts,
        "matching": {
            "exact_draws": int(exact_draws),
            "total_draws": int(total_draws),
            "frac_exact": float(exact_draws / total_draws),
            "gap_max": int(np.max(gaps)) if gaps else None,
            "gap_mean": float(np.mean(gaps)) if gaps else None,
        },
        "common_set": {
            "median_nE": float(np.median(nE)),
            "min_nE": int(np.min(nE)),
            "max_nE": int(np.max(nE)),
        },
        "correlations": {
            "A_vs_C_spearman": float(stats.spearmanr(A, C).statistic),
            "A_vs_C_pearson": float(stats.pearsonr(A, C).statistic),
            "A_vs_B_spearman": float(stats.spearmanr(A, B).statistic),
            "B_vs_C_spearman": float(stats.spearmanr(B, C).statistic),
        },
        "overlap": {
            "A_C_top10": overlap(A, C, 10),
            "A_C_top20": overlap(A, C, 20),
            "A_B_top10": overlap(A, B, 10),
        },
        "per_paper": per_paper,
        "per_paper_draws": per_paper_draws,
        "meta": meta,
    }

    out_path = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results",
        "unit_revision",
        "common_contrast.json",
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(json.dumps({k: out[k] for k in ("designs", "contrasts", "matching", "common_set", "correlations", "overlap")}, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
