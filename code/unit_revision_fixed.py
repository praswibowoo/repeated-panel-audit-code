#!/usr/bin/env python3
"""Fixed-evaluation, configuration-stratified LOSO audit.

Primary evaluation is fixed within each focal study: every nonfocal
configuration is evaluated, independent of the random control. Coordinates for
configurations deleted by a control are obtained by projection through that
control's reduced PCA solution.

Designs
-------
A       row-count control, full row fit
B       legacy greedy exact-volume whole-configuration control, full row fit
Bblock  one uniformly sampled donor configuration with exactly the focal row
        volume, full row fit (available for 112/117 studies)
Bstudy  all exact-size whole single-configuration donor studies enumerated,
         full row fit (primary for 91/97 single-configuration studies)
C       pooled configuration-count control, collapsed fit
H       exploratory donor-study configuration control, collapsed
        fit (multi-configuration studies only; not coherence-balanced)

Primary contrasts
-----------------
AC       A minus C, all studies
ABstudy  A minus Bstudy, single-configuration studies with a whole-study donor
ABblock  A minus Bblock, single-configuration studies with an exact-size donor
ACmulti  A minus C, multi-configuration studies
CminusH  C minus H, multi-configuration studies

The legacy B design is retained only as an algorithmic sensitivity.
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

from common import N_BOOT, SEED, load_curated, seed_for, unique_mask  # noqa: E402
from unit_revision_common import exact_volume_indices  # noqa: E402


def fit_pca(X: np.ndarray, dims: int = 2) -> PCA:
    return PCA(n_components=dims, svd_solver="full", random_state=SEED).fit(X)


def median_drift(ref: np.ndarray, red: np.ndarray) -> float:
    a, b, _ = procrustes(ref, red)
    return float(np.median(np.linalg.norm(a - b, axis=1)))


def rms_drift(ref: np.ndarray, red: np.ndarray) -> float:
    """Root-mean-square Procrustes displacement over the evaluation set."""
    a, b, _ = procrustes(ref, red)
    return float(np.sqrt(np.mean(np.sum((a - b) ** 2, axis=1))))


def study_bootstrap(values, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    x = np.asarray(values, float)
    if not len(x):
        return {"n": 0, "median": None, "ci_lo": None, "ci_hi": None}
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        boot[i] = np.median(x[rng.integers(0, len(x), len(x))])
    return {
        "n": int(len(x)),
        "median": float(np.median(x)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n_boot": int(n_boot),
    }


def two_level_bootstrap(per_draw: dict, n_boot: int = 5000, seed: int = SEED) -> dict:
    """Resample studies and all D draws within each resampled study."""
    papers = sorted(per_draw)
    if not papers:
        return {"n": 0, "median": None, "ci_lo": None, "ci_hi": None}
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for b in range(n_boot):
        selected = rng.integers(0, len(papers), len(papers))
        vals = []
        for i in selected:
            arr = np.asarray(per_draw[papers[i]], float)
            vals.append(np.median(rng.choice(arr, len(arr), replace=True)))
        boot[b] = np.median(vals)
    return {
        "n": int(len(papers)),
        "median": float(np.median(boot)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n_boot": int(n_boot),
    }


def describe(values) -> dict:
    x = np.asarray(values, float)
    if not len(x):
        return {"n": 0, "median": None, "iqr_lo": None, "iqr_hi": None,
                "frac_positive": None}
    return {
        "n": int(len(x)),
        "median": float(np.median(x)),
        "iqr_lo": float(np.quantile(x, 0.25)),
        "iqr_hi": float(np.quantile(x, 0.75)),
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--dims", type=int, default=2)
    ap.add_argument(
        "--drift-summary", choices=("median", "rms"), default="median",
        help="Event-drift summary; median is primary and RMS is a sensitivity.",
    )
    ap.add_argument("--out", default=None)
    ap.add_argument(
        "--exclude", default="",
        help="Comma-separated paper IDs to exclude before recomputing configurations.",
    )
    args = ap.parse_args()
    drift_fn = median_drift if args.drift_summary == "median" else rms_drift

    excluded = [x.strip() for x in args.exclude.split(",") if x.strip()]
    X, rho, paper = load_curated()
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

    keys = ("A", "B", "Bblock", "Bstudy", "C", "H", "AB", "AC", "BC",
            "ABblock", "ABstudy", "ACsingle", "ACmulti", "CminusH")
    per_paper = {k: {} for k in keys}
    per_paper_draws = {k: {} for k in keys}
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

        # Fixed evaluation: all nonfocal configurations.
        E = np.where(keep_block_c)[0]
        reps = np.array([config_rows[j][0] for j in E], int)
        ref = S_full[reps]
        ref_c = S_full_c[E]

        P_block = fit_pca(X[keep_block], dims=args.dims)
        S_block = P_block.transform(X[reps])
        d_block = drift_fn(ref, S_block)

        P_block_c = fit_pca(Xc[keep_block_c], dims=args.dims)
        S_block_c = P_block_c.transform(Xc[E])
        d_block_c = drift_fn(ref_c, S_block_c)

        donors = np.where(keep_block)[0]
        donors_c = np.where(keep_block_c)[0]
        exact_block = [int(j) for j in donors_c if config_size[j] == n_p]
        exact_study = [
            int(j) for j in exact_block
            if nu == 1 and n_u[pc[j]] == 1
        ]

        if nu > 1:
            donor_papers = [q for q in papers if q != p and n_u[q] == nu]
            if not donor_papers:
                donor_papers = [q for q in papers if q != p and n_u[q] > nu]
            fallback = not donor_papers
            if fallback:
                donor_papers = [q for q in papers if q != p]
            donor_papers = sorted(
                donor_papers, key=lambda q: abs(coherence[q] - coherence[p])
            )[:5]
        else:
            donor_papers = []
            fallback = False

        # Enumerate every eligible whole-study donor. The donor pools are small
        # (median 12, maximum 18), so exhaustive enumeration removes Monte Carlo
        # error from the primary Bstudy control.
        study_control_drifts = []
        for j in exact_study:
            keep_study = np.ones(n, bool)
            keep_study[config_rows[j]] = False
            P_study = fit_pca(X[keep_study], dims=args.dims)
            study_control_drifts.append(
                drift_fn(ref, P_study.transform(X[reps]))
            )
        d_study = float(np.median(study_control_drifts)) if study_control_drifts else None
        r_study = d_block / d_study if d_study else None

        draws = {k: [] for k in keys}
        base = seed_for(p)
        for dr in range(args.draws):
            rng = np.random.default_rng(base + 7919 * dr)

            # A: scattered rows, full fit.
            drop_A = rng.choice(donors, size=n_p, replace=False)
            keep_A = np.ones(n, bool)
            keep_A[drop_A] = False
            P_A = fit_pca(X[keep_A], dims=args.dims)
            d_A = drift_fn(ref, P_A.transform(X[reps]))

            # B: legacy greedy exact-volume control.
            chosen_B = exact_volume_indices(donors_c, n_p, config_size, rng)
            drop_B = np.concatenate([config_rows[j] for j in chosen_B])
            keep_B = np.ones(n, bool)
            keep_B[drop_B] = False
            P_B = fit_pca(X[keep_B], dims=args.dims)
            d_B = drift_fn(ref, P_B.transform(X[reps]))
            greedy_counts.append(len(chosen_B))
            greedy_single_exact.append(
                int(len(chosen_B) == 1 and config_size[chosen_B[0]] == n_p)
            )
            greedy_exact += int(config_size[chosen_B].sum() == n_p)
            greedy_total += 1

            # C: pooled configuration control, collapsed fit.
            drop_C = rng.choice(donors_c, size=nu, replace=False)
            keep_C = np.ones(nc, bool)
            keep_C[drop_C] = False
            P_C = fit_pca(Xc[keep_C], dims=args.dims)
            d_C = drift_fn(ref_c, P_C.transform(Xc[E]))

            rA = d_block / d_A
            rB = d_block / d_B
            rC = d_block_c / d_C
            draws["A"].append(rA)
            draws["B"].append(rB)
            draws["C"].append(rC)
            draws["AB"].append(rA - rB)
            draws["AC"].append(rA - rC)
            draws["BC"].append(rB - rC)

            if nu == 1:
                draws["ACsingle"].append(rA - rC)

            # Bblock: one exact-size donor configuration.
            if exact_block:
                j = exact_block[int(rng.integers(0, len(exact_block)))]
                keep_R = np.ones(n, bool)
                keep_R[config_rows[j]] = False
                P_R = fit_pca(X[keep_R], dims=args.dims)
                d_R = drift_fn(ref, P_R.transform(X[reps]))
                rR = d_block / d_R
                draws["Bblock"].append(rR)
                draws["ABblock"].append(rA - rR)

            # Bstudy: exact enumeration of all eligible whole-study donors.
            if r_study is not None:
                draws["Bstudy"].append(r_study)
                draws["ABstudy"].append(rA - r_study)

            # H: exploratory donor-study configuration block.
            if nu > 1:
                if fallback:
                    drop_H = rng.choice(donors_c, size=nu, replace=False)
                else:
                    q = donor_papers[int(rng.integers(0, len(donor_papers)))]
                    q_rows = np.where(pc == q)[0]
                    if len(q_rows) > nu:
                        drop_H = rng.choice(q_rows, size=nu, replace=False)
                    else:
                        drop_H = q_rows
                keep_H = np.ones(nc, bool)
                keep_H[drop_H] = False
                P_H = fit_pca(Xc[keep_H], dims=args.dims)
                d_H = drift_fn(ref_c, P_H.transform(Xc[E]))
                rH = d_block_c / d_H
                draws["H"].append(rH)
                draws["ACmulti"].append(rA - rC)
                draws["CminusH"].append(rC - rH)

        for k in keys:
            if draws[k]:
                per_paper[k][p] = float(np.median(draws[k]))
                per_paper_draws[k][p] = [float(v) for v in draws[k]]

        meta[p] = {
            "n_rows": n_p,
            "n_configs": nu,
            "coherence": coherence[p],
            "exact_block_donors": len(exact_block),
            "whole_study_donors": len(exact_study),
            "bstudy_control_drift_median": d_study,
            "bstudy_donors_enumerated": len(study_control_drifts),
            "coherence_fallback": bool(fallback) if nu > 1 else False,
        }
        if pi % 10 == 0:
            print(f"{pi}/{len(papers)} {p} rows={n_p} configs={nu}", flush=True)

    single = [p for p in papers if n_u[p] == 1]
    multi = [p for p in papers if n_u[p] > 1]

    designs = {}
    for k in ("A", "B", "Bblock", "Bstudy", "C", "H"):
        vals = [per_paper[k][p] for p in papers if p in per_paper[k]]
        summary = study_bootstrap(vals)
        summary.update(describe(vals))
        two = two_level_bootstrap(per_paper_draws[k])
        summary["two_level"] = two
        designs[k] = summary

    contrasts = {}
    for k in ("AB", "AC", "BC", "ABblock", "ABstudy", "ACsingle", "ACmulti", "CminusH"):
        vals = [per_paper[k][p] for p in papers if p in per_paper[k]]
        summary = describe(vals)
        summary.update(study_bootstrap(vals))
        summary["two_level"] = two_level_bootstrap(per_paper_draws[k])
        contrasts[k] = summary

    subgroups = {
        "single": {
            "n": len(single),
            "designs": {
                k: subset_summary(per_paper, single, k)
                for k in ("A", "B", "Bblock", "Bstudy", "C")
            },
            "contrasts": {
                k: subset_summary(per_paper, single, k)
                for k in ("AB", "AC", "ABblock", "ABstudy")
            },
        },
        "multi": {
            "n": len(multi),
            "designs": {
                k: subset_summary(per_paper, multi, k)
                for k in ("A", "B", "Bblock", "C", "H")
            },
            "contrasts": {
                k: subset_summary(per_paper, multi, k)
                for k in ("AB", "ABblock", "AC", "BC", "CminusH")
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
            "n": len(all_has),
            "papers": all_has,
            "designs": {
                k: subset_summary(per_paper, all_has, k)
                for k in ("A", "B", "C")
            },
            "contrasts": {
                k: subset_summary(per_paper, all_has, k)
                for k in ("AB", "ABblock", "AC")
            },
        },
        "all_no_exact_donor": {
            "n": len(all_missing),
            "papers": all_missing,
        },
        "single_has_exact_donor": {
            "n": len(single_has),
            "papers": single_has,
            "designs": {
                k: subset_summary(per_paper, single_has, k)
                for k in ("A", "B", "Bblock", "C")
            },
            "contrasts": {
                k: subset_summary(per_paper, single_has, k)
                for k in ("AB", "AC", "ABblock")
            },
        },
        "single_has_whole_study_donor": {
            "n": len(single_study_has),
            "papers": single_study_has,
            "designs": {
                k: subset_summary(per_paper, single_study_has, k)
                for k in ("A", "Bstudy", "C")
            },
            "contrasts": {
                k: subset_summary(per_paper, single_study_has, k)
                for k in ("ABstudy", "AC")
            },
        },
        "single_no_whole_study_donor": {
            "n": len(single_study_missing),
            "papers": single_study_missing,
            "designs": {
                k: subset_summary(per_paper, single_study_missing, k)
                for k in ("A", "Bblock", "C")
            },
            "contrasts": {
                k: subset_summary(per_paper, single_study_missing, k)
                for k in ("ABblock", "AC")
            },
        },
        "single_no_exact_donor": {
            "n": len(single_missing),
            "papers": single_missing,
            "designs": {
                k: subset_summary(per_paper, single_missing, k)
                for k in ("A", "B", "C")
            },
            "contrasts": {
                k: subset_summary(per_paper, single_missing, k)
                for k in ("AB", "AC")
            },
        },
    }

    out = {
        "design": {
            "studies": len(papers),
            "rows": n,
            "configurations": nc,
            "draws": args.draws,
            "dimensions": args.dims,
            "drift_summary": args.drift_summary,
            "primary_control": "Bstudy",
            "bstudy_enumeration": "all exact-size whole single-configuration donor studies",
            "excluded": excluded,
            "evaluation": (
                "fixed set of all nonfocal within-study configurations; "
                "control-deleted configurations projected through reduced PCA"
            ),
        },
        "designs": designs,
        "contrasts": contrasts,
        "subgroups": subgroups,
        "availability": availability,
        "legacy_B_matching": {
            "exact_draws": greedy_exact,
            "total_draws": greedy_total,
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
        "meta": meta,
    }

    default_name = (
        "common_contrast.json" if args.dims == 2
        else f"fixed{args.dims}d_contrast.json"
    )
    out_path = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results", "unit_revision_fixed", default_name
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps({
        "designs": designs,
        "contrasts": contrasts,
        "subgroups": subgroups,
        "legacy_B_matching": out["legacy_B_matching"],
    }, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
