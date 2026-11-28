#!/usr/bin/env python3
"""Fixed-evaluation, configuration-stratified LOSO audit.

The eligibility-qualified primary corpus is the default. The full curated
117-paper matrix remains available with ``--matrix`` for sensitivity analyses.
Primary focal claims use single-configuration studies only; multi-configuration
studies are retained as background summaries.

Designs
-------
A       row-count control, full row fit (Monte Carlo)
B       legacy greedy exact-volume whole-configuration control (Monte Carlo)
Bblock  every exact-size donor configuration enumerated, full row fit
Bstudy  every exact-size whole single-configuration donor study enumerated,
        full row fit; nested within Bblock
C       pooled configuration-count control, collapsed fit (Monte Carlo)

Estimator
---------
For every design, R_s = block_drift_s / median(control_drifts_s). Block drift is
fixed within study. A/B/C resample control drifts in the two-level bootstrap;
exhaustive Bstudy/Bblock control-drift medians remain fixed within study
resamples. Design H is not part of the current analysis.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from scipy.spatial import procrustes
from sklearn.decomposition import PCA

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import N_BOOT, SEED, load_curated, load_primary, seed_for, unique_mask  # noqa: E402
from unit_revision_common import exact_volume_indices  # noqa: E402


DESIGN_KEYS = ("A", "B", "Bblock", "Bstudy", "C")
EXHAUSTIVE_KEYS = ("Bblock", "Bstudy")
CONTRAST_KEYS = ("AB", "AC", "BC", "ABblock", "ABstudy", "ACsingle", "ACmulti")
STRATA = (("2-5", 2, 5), ("6-10", 6, 10), (">=11", 11, 10**9))


def fit_pca(X: np.ndarray, dims: int = 2) -> PCA:
    return PCA(n_components=dims, svd_solver="full", random_state=SEED).fit(X)


def median_drift(ref: np.ndarray, red: np.ndarray) -> float:
    """Median per-row Procrustes displacement."""
    a, b, _ = procrustes(ref, red)
    return float(np.median(np.linalg.norm(a - b, axis=1)))


def rms_drift(ref: np.ndarray, red: np.ndarray) -> float:
    """Root-mean-square Procrustes displacement over the evaluation set."""
    a, b, _ = procrustes(ref, red)
    return float(np.sqrt(np.mean(np.sum((a - b) ** 2, axis=1))))


def ratio_of_medians(block_drift: float, control_drifts) -> float | None:
    values = np.asarray(control_drifts, float)
    if not len(values):
        return None
    denominator = float(np.median(values))
    if denominator <= 0:
        return None
    return float(block_drift / denominator)


def study_bootstrap(values, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Conditional study bootstrap of a median over per-study estimates."""
    x = np.asarray(values, float)
    if not len(x):
        return {"n": 0, "median": None, "ci_lo": None, "ci_hi": None}
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(x), size=(n_boot, len(x)))
    boot = np.median(x[indices], axis=1)
    return {
        "n": int(len(x)),
        "median": float(np.median(x)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n_boot": int(n_boot),
    }


def _resampled_ratio(rng, design, paper, ratios, control_drifts, block_drifts, fixed):
    if control_drifts is None or block_drifts is None:
        arr = np.asarray(ratios[paper], float)
        return float(np.median(rng.choice(arr, len(arr), replace=True)))
    arr = np.asarray(control_drifts[paper], float)
    if fixed:
        control_median = float(np.median(arr))
    else:
        control_median = float(np.median(rng.choice(arr, len(arr), replace=True)))
    return float(block_drifts[paper] / control_median)


def two_level_bootstrap(
    per_draw: dict,
    n_boot: int = 5000,
    seed: int = SEED,
    *,
    control_drifts: dict | None = None,
    block_drifts: dict | None = None,
    fixed_median: bool = False,
) -> dict:
    """Resample studies and control drifts, then recompute ratio of medians.

    ``per_draw`` retains the historical paper->ratio-draw mapping. When drift
    arrays are supplied, the bootstrap uses those arrays directly and recomputes
    block_drift / median(resampled control drifts).
    """
    papers = sorted(per_draw)
    if not papers:
        return {"n": 0, "median": None, "ci_lo": None, "ci_hi": None}
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for b in range(n_boot):
        selected = rng.integers(0, len(papers), len(papers))
        vals = [
            _resampled_ratio(
                rng, "", papers[i], per_draw, control_drifts, block_drifts,
                fixed_median,
            )
            for i in selected
        ]
        boot[b] = np.median(vals)
    return {
        "n": int(len(papers)),
        "median": float(np.median(boot)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n_boot": int(n_boot),
        "resamples_control_drifts": not fixed_median,
    }


def two_level_contrast_bootstrap(
    per_paper_draws: dict,
    papers: list[str],
    key_j: str,
    key_k: str,
    n_boot: int = 5000,
    seed: int = SEED,
    *,
    control_drifts: dict | None = None,
    block_drifts: dict | None = None,
    fixed_designs: tuple[str, ...] = EXHAUSTIVE_KEYS,
) -> dict:
    """Two-level bootstrap of paired per-study ratio differences."""
    papers = [
        p for p in papers
        if p in per_paper_draws.get(key_j, {})
        and p in per_paper_draws.get(key_k, {})
    ]
    if not papers:
        return {"n": 0, "median": None, "ci_lo": None, "ci_hi": None}
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for b in range(n_boot):
        selected = rng.integers(0, len(papers), len(papers))
        vals = []
        for i in selected:
            p = papers[i]
            rj = _resampled_ratio(
                rng, key_j, p, per_paper_draws[key_j],
                None if control_drifts is None else control_drifts[key_j],
                None if block_drifts is None else block_drifts[key_j],
                key_j in fixed_designs,
            )
            rk = _resampled_ratio(
                rng, key_k, p, per_paper_draws[key_k],
                None if control_drifts is None else control_drifts[key_k],
                None if block_drifts is None else block_drifts[key_k],
                key_k in fixed_designs,
            )
            vals.append(rj - rk)
        boot[b] = np.median(vals)
    return {
        "n": len(papers),
        "median": float(np.median(boot)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n_boot": int(n_boot),
        "fixed_design_medians": [k for k in (key_j, key_k) if k in fixed_designs],
    }


def describe(values) -> dict:
    x = np.asarray(values, float)
    if not len(x):
        return {
            "n": 0, "median": None, "iqr_lo": None, "iqr_hi": None,
            "min": None, "max": None, "frac_positive": None,
        }
    return {
        "n": int(len(x)),
        "median": float(np.median(x)),
        "iqr_lo": float(np.quantile(x, 0.25)),
        "iqr_hi": float(np.quantile(x, 0.75)),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "frac_positive": float(np.mean(x > 0)),
    }


def mean_pairwise_hamming(X: np.ndarray) -> float:
    if len(X) < 2:
        return 0.0
    vals = []
    for i in range(len(X)):
        for j in range(i + 1, len(X)):
            vals.append(int(np.sum(X[i] != X[j])))
    return float(np.mean(vals))


def subset_summary(per_paper: dict, papers: list[str], key: str) -> dict:
    vals = [per_paper[key][p] for p in papers if p in per_paper[key]]
    out = describe(vals)
    out.update(study_bootstrap(vals))
    return out


def pool_size_summary(sizes) -> dict:
    x = np.asarray(sizes, int)
    if not len(x):
        return {
            "n_eligible": 0, "min": None, "q1": None, "median": None,
            "q3": None, "max": None, "count_le_2": 0, "count_le_5": 0,
        }
    return {
        "n_eligible": int(len(x)),
        "min": int(np.min(x)),
        "q1": float(np.quantile(x, 0.25)),
        "median": float(np.quantile(x, 0.5)),
        "q3": float(np.quantile(x, 0.75)),
        "max": int(np.max(x)),
        "count_le_2": int(np.sum(x <= 2)),
        "count_le_5": int(np.sum(x <= 5)),
    }


def build_strata(per_paper, meta, single, design_keys=DESIGN_KEYS):
    strata = {}
    distributions = {}
    for label, lo, hi in STRATA:
        focal = [p for p in single if lo <= meta[p]["n_rows"] <= hi]
        bstudy = [p for p in focal if meta[p]["whole_study_donors"] > 0]
        bblock = [p for p in focal if meta[p]["exact_block_donors"] > 0]
        designs = {}
        for key in design_keys:
            eligible = bstudy if key == "Bstudy" else bblock if key == "Bblock" else focal
            designs[key] = subset_summary(per_paper, eligible, key)
        contrasts = {
            "ABstudy": subset_summary(per_paper, bstudy, "ABstudy"),
            "ABblock": subset_summary(per_paper, bblock, "ABblock"),
        }
        strata[label] = {
            "row_range": [lo, None if hi >= 10**9 else hi],
            "n_single_configuration": len(focal),
            "n_bstudy_eligible": len(bstudy),
            "n_bblock_eligible": len(bblock),
            "papers": focal,
            "designs": designs,
            "contrasts": contrasts,
        }
        distributions[label] = {
            "n_single_configuration": len(focal),
            "Bstudy": pool_size_summary([
                meta[p]["whole_study_donors"] for p in bstudy
            ]),
            "Bblock": pool_size_summary([
                meta[p]["exact_block_donors"] for p in bblock
            ]),
        }
    return strata, distributions


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--dims", type=int, default=2)
    ap.add_argument(
        "--matrix", default=None,
        help="Optional full-curated matrix path for sensitivity analysis.",
    )
    ap.add_argument(
        "--drift-summary", choices=("median", "rms"), default="median",
        help="Event-drift summary; both use the ratio-of-medians estimator.",
    )
    ap.add_argument("--out", default=None)
    ap.add_argument(
        "--exclude", default="",
        help="Comma-separated paper IDs to exclude before recomputing configurations.",
    )
    args = ap.parse_args()
    if args.draws < 1:
        ap.error("--draws must be positive")
    drift_fn = median_drift if args.drift_summary == "median" else rms_drift

    excluded = [x.strip() for x in args.exclude.split(",") if x.strip()]
    if args.out is None and (
        args.draws != 100 or args.dims != 2 or args.matrix is not None
        or args.drift_summary != "median" or excluded
    ):
        ap.error(
            "--out is required when matrix, draw count, dimensions, drift summary, "
            "or exclusions differ from the primary defaults"
        )
    loaded = (
        load_curated(args.matrix, return_metadata=True)
        if args.matrix is not None else load_primary(return_metadata=True)
    )
    X, rho, paper = loaded.X, loaded.rho, loaded.paper
    if excluded:
        missing = sorted(set(excluded) - set(paper))
        if missing:
            raise ValueError(f"unknown exclusion IDs: {missing}")
        keep = ~np.isin(paper, excluded)
        X, rho, paper = X[keep], rho[keep], paper[keep]
    papers = sorted(set(paper))
    n = len(X)
    uni = unique_mask(X, paper)
    Xc = X[uni]
    pc = paper[uni]
    nc = len(Xc)

    config_rows = []
    for j, p in enumerate(pc):
        config_rows.append(np.where((paper == p) & np.all(X == Xc[j], axis=1))[0])
    config_size = np.array([len(v) for v in config_rows], int)
    n_u = {p: int(np.sum(uni & (paper == p))) for p in papers}
    cfg = {p: Xc[pc == p] for p in papers}
    coherence = {p: mean_pairwise_hamming(cfg[p]) for p in papers}

    full = fit_pca(X, dims=args.dims)
    full_c = fit_pca(Xc, dims=args.dims)
    S_full = full.transform(X)
    S_full_c = full_c.transform(Xc)

    keys = DESIGN_KEYS + CONTRAST_KEYS + ("ABstudy_log",)
    per_paper = {k: {} for k in keys}
    per_paper_draws = {k: {} for k in keys if k != "ABstudy_log"}
    per_paper_control_drifts = {k: {} for k in DESIGN_KEYS}
    per_paper_block_drift = {k: {} for k in DESIGN_KEYS}
    meta = {}
    greedy_counts = []
    greedy_single_exact = []
    greedy_exact = 0
    greedy_total = 0

    for pi, p in enumerate(papers):
        n_p = int(np.sum(paper == p))
        nu = n_u[p]
        keep_block = paper != p
        keep_block_c = pc != p
        E = np.where(keep_block_c)[0]
        reps = np.array([config_rows[j][0] for j in E], int)
        ref = S_full[reps]
        ref_c = S_full_c[E]

        P_block = fit_pca(X[keep_block], dims=args.dims)
        d_block = drift_fn(ref, P_block.transform(X[reps]))
        P_block_c = fit_pca(Xc[keep_block_c], dims=args.dims)
        d_block_c = drift_fn(ref_c, P_block_c.transform(Xc[E]))

        donors = np.where(keep_block)[0]
        donors_c = np.where(keep_block_c)[0]
        exact_block = [int(j) for j in donors_c if config_size[j] == n_p]
        exact_study = [
            int(j) for j in exact_block if nu == 1 and n_u[pc[j]] == 1
        ]
        if not set(exact_study).issubset(exact_block):
            raise RuntimeError(f"Bstudy donor pool is not nested in Bblock for {p}")

        # One fit per exact-size donor configuration. Bstudy reuses the nested
        # subset, so both empirical control distributions are exhaustive.
        donor_drift = {}
        for j in exact_block:
            keep_R = np.ones(n, bool)
            keep_R[config_rows[j]] = False
            P_R = fit_pca(X[keep_R], dims=args.dims)
            donor_drift[j] = drift_fn(ref, P_R.transform(X[reps]))
        block_control_drifts = [donor_drift[j] for j in exact_block]
        study_control_drifts = [donor_drift[j] for j in exact_study]
        r_block = ratio_of_medians(d_block, block_control_drifts)
        r_study = ratio_of_medians(d_block, study_control_drifts)

        draws = {k: [] for k in DESIGN_KEYS + CONTRAST_KEYS}
        control_drifts = {k: [] for k in DESIGN_KEYS}
        base = seed_for(p)
        for dr in range(args.draws):
            rng = np.random.default_rng(base + 7919 * dr)

            drop_A = rng.choice(donors, size=n_p, replace=False)
            keep_A = np.ones(n, bool)
            keep_A[drop_A] = False
            P_A = fit_pca(X[keep_A], dims=args.dims)
            d_A = drift_fn(ref, P_A.transform(X[reps]))
            control_drifts["A"].append(d_A)

            chosen_B = exact_volume_indices(donors_c, n_p, config_size, rng)
            drop_B = np.concatenate([config_rows[j] for j in chosen_B])
            keep_B = np.ones(n, bool)
            keep_B[drop_B] = False
            P_B = fit_pca(X[keep_B], dims=args.dims)
            d_B = drift_fn(ref, P_B.transform(X[reps]))
            control_drifts["B"].append(d_B)
            greedy_counts.append(len(chosen_B))
            greedy_single_exact.append(
                int(len(chosen_B) == 1 and config_size[chosen_B[0]] == n_p)
            )
            greedy_exact += int(config_size[chosen_B].sum() == n_p)
            greedy_total += 1

            drop_C = rng.choice(donors_c, size=nu, replace=False)
            keep_C = np.ones(nc, bool)
            keep_C[drop_C] = False
            P_C = fit_pca(Xc[keep_C], dims=args.dims)
            d_C = drift_fn(ref_c, P_C.transform(Xc[E]))
            control_drifts["C"].append(d_C)

            rA = ratio_of_medians(d_block, [d_A])
            rB = ratio_of_medians(d_block, [d_B])
            rC = ratio_of_medians(d_block_c, [d_C])
            if rA is None or rB is None or rC is None:
                raise RuntimeError(f"zero control drift in {p}, draw {dr}")
            draws["A"].append(rA)
            draws["B"].append(rB)
            draws["C"].append(rC)
            draws["AB"].append(rA - rB)
            draws["AC"].append(rA - rC)
            draws["BC"].append(rB - rC)
            if nu == 1:
                draws["ACsingle"].append(rA - rC)
            else:
                draws["ACmulti"].append(rA - rC)
            if r_block is not None:
                draws["Bblock"].append(r_block)
                draws["ABblock"].append(rA - r_block)
            if r_study is not None:
                draws["Bstudy"].append(r_study)
                draws["ABstudy"].append(rA - r_study)

        for key in DESIGN_KEYS:
            block_value = d_block_c if key == "C" else d_block
            drifts = control_drifts[key]
            if key == "Bblock":
                drifts = block_control_drifts
            elif key == "Bstudy":
                drifts = study_control_drifts
            value = ratio_of_medians(block_value, drifts)
            if value is None:
                continue
            per_paper[key][p] = value
            per_paper_control_drifts[key][p] = [float(v) for v in drifts]
            per_paper_block_drift[key][p] = float(block_value)
            if key in EXHAUSTIVE_KEYS:
                per_paper_draws[key][p] = [value]
            else:
                per_paper_draws[key][p] = [float(v) for v in draws[key]]

        contrast_pairs = {
            "AB": ("A", "B"), "AC": ("A", "C"), "BC": ("B", "C"),
            "ABblock": ("A", "Bblock"), "ABstudy": ("A", "Bstudy"),
            "ACsingle": ("A", "C"), "ACmulti": ("A", "C"),
        }
        for key, (key_j, key_k) in contrast_pairs.items():
            if key in ("ABblock", "ABstudy") and nu != 1:
                continue
            if key == "ACsingle" and nu != 1:
                continue
            if key == "ACmulti" and nu <= 1:
                continue
            if p in per_paper[key_j] and p in per_paper[key_k]:
                per_paper[key][p] = per_paper[key_j][p] - per_paper[key_k][p]
                if draws[key]:
                    per_paper_draws[key][p] = [float(v) for v in draws[key]]
        if p in per_paper["A"] and p in per_paper["Bstudy"]:
            per_paper["ABstudy_log"][p] = float(
                np.log(per_paper["A"][p] / per_paper["Bstudy"][p])
            )

        meta[p] = {
            "n_rows": n_p,
            "n_configs": nu,
            "coherence": coherence[p],
            "exact_block_donors": len(exact_block),
            "whole_study_donors": len(exact_study),
            "bblock_donors_enumerated": len(block_control_drifts),
            "bstudy_donors_enumerated": len(study_control_drifts),
            "bblock_control_drift_median": (
                float(np.median(block_control_drifts)) if block_control_drifts else None
            ),
            "bstudy_control_drift_median": (
                float(np.median(study_control_drifts)) if study_control_drifts else None
            ),
            "bstudy_subset_of_bblock": set(exact_study).issubset(exact_block),
            "bblock_only_donor_count": len(set(exact_block) - set(exact_study)),
            "bblock_donor_config_rows": [int(config_rows[j][0]) for j in exact_block],
            "bstudy_donor_config_rows": [int(config_rows[j][0]) for j in exact_study],
        }
        if pi % 10 == 0:
            print(f"{pi}/{len(papers)} {p} rows={n_p} configs={nu}", flush=True)

    single = [p for p in papers if n_u[p] == 1]
    multi = [p for p in papers if n_u[p] > 1]

    designs = {}
    for key in DESIGN_KEYS:
        vals = [per_paper[key][p] for p in papers if p in per_paper[key]]
        summary = study_bootstrap(vals)
        summary.update(describe(vals))
        summary["two_level"] = two_level_bootstrap(
            per_paper_draws[key],
            control_drifts=per_paper_control_drifts[key],
            block_drifts=per_paper_block_drift[key],
            fixed_median=key in EXHAUSTIVE_KEYS,
        )
        summary["control_drift_median_across_studies"] = float(np.median([
            np.median(per_paper_control_drifts[key][p])
            for p in per_paper_control_drifts[key]
        ])) if per_paper_control_drifts[key] else None
        summary["enumeration"] = (
            "exhaustive" if key in EXHAUSTIVE_KEYS else "monte_carlo"
        )
        designs[key] = summary

    contrast_specs = {
        "AB": ("A", "B", papers), "AC": ("A", "C", papers),
        "BC": ("B", "C", papers), "ABblock": ("A", "Bblock", single),
        "ABstudy": ("A", "Bstudy", single),
        "ACsingle": ("A", "C", single), "ACmulti": ("A", "C", multi),
    }
    contrasts = {}
    for key in CONTRAST_KEYS:
        vals = [per_paper[key][p] for p in papers if p in per_paper[key]]
        summary = describe(vals)
        summary.update(study_bootstrap(vals))
        key_j, key_k, bootstrap_papers = contrast_specs[key]
        summary["two_level"] = two_level_contrast_bootstrap(
            per_paper_draws, bootstrap_papers, key_j, key_k,
            control_drifts=per_paper_control_drifts,
            block_drifts=per_paper_block_drift,
        )
        contrasts[key] = summary

    log_values = list(per_paper["ABstudy_log"].values())
    sensitivities = {
        "ABstudy_log": {**describe(log_values), **study_bootstrap(log_values)}
    }

    subgroups = {
        "single": {
            "role": "primary_focal_claims",
            "n": len(single),
            "designs": {
                k: subset_summary(per_paper, single, k) for k in DESIGN_KEYS
            },
            "contrasts": {
                k: subset_summary(per_paper, single, k)
                for k in ("AB", "AC", "ABblock", "ABstudy", "ABstudy_log")
            },
        },
        "multi": {
            "role": "background_only",
            "n": len(multi),
            "designs": {
                k: subset_summary(per_paper, multi, k) for k in DESIGN_KEYS
            },
            "contrasts": {
                k: subset_summary(per_paper, multi, k)
                for k in ("AB", "ABblock", "AC", "BC")
            },
        },
    }

    all_has = [p for p in papers if meta[p]["exact_block_donors"] > 0]
    all_missing = [p for p in papers if meta[p]["exact_block_donors"] == 0]
    single_has = [p for p in single if meta[p]["exact_block_donors"] > 0]
    single_missing = [p for p in single if meta[p]["exact_block_donors"] == 0]
    single_study_has = [p for p in single if meta[p]["whole_study_donors"] > 0]
    single_study_missing = [p for p in single if meta[p]["whole_study_donors"] == 0]
    availability = {
        "all_has_exact_donor": {
            "n": len(all_has), "papers": all_has,
            "designs": {k: subset_summary(per_paper, all_has, k) for k in ("A", "B", "C")},
            "contrasts": {k: subset_summary(per_paper, all_has, k) for k in ("AB", "ABblock", "AC")},
        },
        "all_no_exact_donor": {"n": len(all_missing), "papers": all_missing},
        "single_has_exact_donor": {
            "n": len(single_has), "papers": single_has,
            "designs": {k: subset_summary(per_paper, single_has, k) for k in ("A", "B", "Bblock", "C")},
            "contrasts": {k: subset_summary(per_paper, single_has, k) for k in ("AB", "AC", "ABblock")},
        },
        "single_has_whole_study_donor": {
            "n": len(single_study_has), "papers": single_study_has,
            "designs": {k: subset_summary(per_paper, single_study_has, k) for k in ("A", "Bstudy", "C")},
            "contrasts": {k: subset_summary(per_paper, single_study_has, k) for k in ("ABstudy", "ABstudy_log", "AC")},
        },
        "single_no_whole_study_donor": {
            "n": len(single_study_missing), "papers": single_study_missing,
            "designs": {k: subset_summary(per_paper, single_study_missing, k) for k in ("A", "Bblock", "C")},
            "contrasts": {k: subset_summary(per_paper, single_study_missing, k) for k in ("ABblock", "AC")},
        },
        "single_no_exact_donor": {
            "n": len(single_missing), "papers": single_missing,
            "designs": {k: subset_summary(per_paper, single_missing, k) for k in ("A", "B", "C")},
            "contrasts": {k: subset_summary(per_paper, single_missing, k) for k in ("AB", "AC")},
        },
    }

    strata, donor_distributions = build_strata(per_paper, meta, single)
    nested = {
        p: {
            "bstudy_donors": meta[p]["whole_study_donors"],
            "bblock_donors": meta[p]["exact_block_donors"],
            "bblock_only_donors": meta[p]["bblock_only_donor_count"],
            "bstudy_subset_of_bblock": meta[p]["bstudy_subset_of_bblock"],
        }
        for p in single_study_has
    }

    out = {
        "estimator": {
            "name": "ratio_of_medians",
            "formula": "R_s^D = block_drift_s / median(control_drifts_s,D)",
            "block_drift": args.drift_summary,
            "control_distribution": "one drift scalar per control fit",
            "monte_carlo_designs": ["A", "B", "C"],
            "exhaustive_designs": list(EXHAUSTIVE_KEYS),
            "two_level_bootstrap": (
                "resample studies and A/B/C control drifts; recompute median control "
                "drift and ratio; exhaustive Bstudy/Bblock medians fixed within study resamples"
            ),
        },
        "design": {
            **loaded.metadata(),
            "studies": len(papers), "rows": n, "configurations": nc,
            "single_configuration_studies": len(single),
            "multi_configuration_studies_background": len(multi),
            "draws": args.draws, "dimensions": args.dims,
            "drift_summary": args.drift_summary,
            "primary_control": "Bstudy",
            "primary_focal_population": "single_configuration_studies_only",
            "multi_configuration_role": "background_only",
            "bstudy_enumeration": "all exact-size whole single-configuration donor studies",
            "bblock_enumeration": "all exact-size donor configurations",
            "excluded": excluded,
            "evaluation": (
                "fixed set of all nonfocal within-study configurations; "
                "control-deleted configurations projected through reduced PCA"
            ),
        },
        "designs": designs,
        "contrasts": contrasts,
        "sensitivities": sensitivities,
        "subgroups": subgroups,
        "availability": availability,
        "block_size_strata": strata,
        "donor_pool_size_distributions": donor_distributions,
        "donor_pool_nesting": {
            "n_shared_bstudy_eligible": len(nested),
            "all_nested": all(v["bstudy_subset_of_bblock"] for v in nested.values()),
            "violations": [p for p, v in nested.items() if not v["bstudy_subset_of_bblock"]],
            "per_study": nested,
        },
        "legacy_B_matching": {
            "exact_draws": greedy_exact, "total_draws": greedy_total,
            "exact_fraction": greedy_exact / greedy_total,
            "donor_config_count_median": float(np.median(greedy_counts)),
            "donor_config_count_min": int(np.min(greedy_counts)),
            "donor_config_count_max": int(np.max(greedy_counts)),
            "studies_with_exact_size_donor_fraction": float(np.mean([
                m["exact_block_donors"] > 0 for m in meta.values()
            ])),
            "single_exact_size_draw_fraction": float(np.mean(greedy_single_exact)),
        },
        "per_paper": per_paper,
        "per_paper_draws": per_paper_draws,
        "per_paper_control_drifts": per_paper_control_drifts,
        "per_paper_block_drift": per_paper_block_drift,
        "meta": meta,
    }

    default_name = "common_contrast.json" if args.dims == 2 else f"fixed{args.dims}d_contrast.json"
    out_path = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results", "unit_revision_fixed", default_name,
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps({
        "design": out["design"], "designs": designs, "contrasts": contrasts,
        "block_size_strata": strata,
        "donor_pool_size_distributions": donor_distributions,
        "donor_pool_nesting": {
            k: v for k, v in out["donor_pool_nesting"].items() if k != "per_study"
        },
    }, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
