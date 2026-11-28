#!/usr/bin/env python3
"""Fixed-evaluation Jaccard PCoA sensitivity for the primary coverage corpus.

Mirrors the primary PCA audit: a fixed nonfocal configuration evaluation set,
out-of-fit projection, ratio-of-medians estimator, exhaustive nested Bstudy and
Bblock donor pools, and two-level bootstrap. Multi-configuration studies remain
background only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass

import numpy as np
from scipy.linalg import eigh
from scipy.spatial.distance import cdist, pdist, squareform
from scipy.spatial import procrustes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import load_primary, seed_for, unique_mask  # noqa: E402
from unit_revision_fixed import (  # noqa: E402
    EXHAUSTIVE_KEYS,
    build_strata,
    describe,
    mean_pairwise_hamming,
    ratio_of_medians,
    study_bootstrap,
    subset_summary,
    two_level_bootstrap,
    two_level_contrast_bootstrap,
)


@dataclass
class JaccardPCoA:
    """Two-dimensional classical PCoA with out-of-sample projection."""

    X: np.ndarray
    dimensions: int = 2

    def __post_init__(self) -> None:
        self.X = np.asarray(self.X, float)
        n = len(self.X)
        if n <= self.dimensions:
            raise ValueError("PCoA requires more rows than dimensions")
        D = squareform(pdist(self.X, metric="jaccard"))
        D2 = D * D
        H = np.eye(n) - np.ones((n, n)) / n
        B = -0.5 * H @ D2 @ H
        B = (B + B.T) / 2
        vals, vecs = eigh(B, subset_by_index=[n - self.dimensions, n - 1])
        order = np.argsort(vals)[::-1]
        vals, vecs = vals[order], vecs[:, order]
        keep = vals > 1e-10
        if int(keep.sum()) < self.dimensions:
            raise ValueError("fewer than two positive Jaccard PCoA eigenvalues")
        self.eigenvalues = vals[keep][: self.dimensions]
        self.eigenvectors = vecs[:, keep][:, : self.dimensions]
        self.train_d2_row_mean = D2.mean(axis=1)
        self.train_d2_grand_mean = float(D2.mean())

    def transform(self, Xq: np.ndarray) -> np.ndarray:
        Xq = np.asarray(Xq, float)
        D2 = cdist(Xq, self.X, metric="jaccard") ** 2
        centered = (
            D2
            - D2.mean(axis=1, keepdims=True)
            - self.train_d2_row_mean[None, :]
            + self.train_d2_grand_mean
        )
        return -0.5 * (centered @ self.eigenvectors) / np.sqrt(self.eigenvalues)


def fit_pcoa(X: np.ndarray, dimensions: int = 2) -> JaccardPCoA:
    return JaccardPCoA(X, dimensions=dimensions)


def median_drift(ref: np.ndarray, red: np.ndarray) -> float:
    a, b, _ = procrustes(ref, red)
    return float(np.median(np.linalg.norm(a - b, axis=1)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if args.draws < 1:
        ap.error("--draws must be positive")

    loaded = load_primary(return_metadata=True)
    X, paper = loaded.X, loaded.paper
    papers = sorted(set(paper))
    n = len(X)
    uni = unique_mask(X, paper)
    Xc, pc = X[uni], paper[uni]
    nc = len(Xc)

    config_rows = []
    for j, p in enumerate(pc):
        config_rows.append(
            np.where((paper == p) & np.all(X == Xc[j], axis=1))[0]
        )
    config_size = np.array([len(rr) for rr in config_rows], int)
    n_u = {p: int(np.sum(uni & (paper == p))) for p in papers}
    coherence = {p: mean_pairwise_hamming(Xc[pc == p]) for p in papers}

    full = fit_pcoa(X)
    full_c = fit_pcoa(Xc)
    S_full = full.transform(X)
    S_full_c = full_c.transform(Xc)

    design_keys = ("A", "Bblock", "Bstudy", "C")
    contrast_keys = ("ABblock", "ABstudy", "AC", "ACsingle", "ACmulti")
    keys = design_keys + contrast_keys
    per_paper = {k: {} for k in keys}
    per_paper_draws = {k: {} for k in keys}
    per_paper_control_drifts = {k: {} for k in design_keys}
    per_paper_block_drift = {k: {} for k in design_keys}
    meta = {}

    for pi, p in enumerate(papers):
        n_p = int(np.sum(paper == p))
        nu = n_u[p]
        keep_block = paper != p
        keep_block_c = pc != p
        E = np.where(keep_block_c)[0]
        reps = np.array([config_rows[j][0] for j in E], int)
        ref = S_full[reps]
        ref_c = S_full_c[E]

        P_block = fit_pcoa(X[keep_block])
        d_block = median_drift(ref, P_block.transform(X[reps]))
        P_block_c = fit_pcoa(Xc[keep_block_c])
        d_block_c = median_drift(ref_c, P_block_c.transform(Xc[E]))

        donors = np.where(keep_block)[0]
        donors_c = np.where(keep_block_c)[0]
        exact_block = [int(j) for j in donors_c if config_size[j] == n_p]
        exact_study = [
            int(j) for j in exact_block if nu == 1 and n_u[pc[j]] == 1
        ]
        if not set(exact_study).issubset(exact_block):
            raise RuntimeError(f"Bstudy donor pool is not nested in Bblock for {p}")

        donor_drift = {}
        for j in exact_block:
            keep_R = np.ones(n, bool)
            keep_R[config_rows[j]] = False
            P_R = fit_pcoa(X[keep_R])
            donor_drift[j] = median_drift(ref, P_R.transform(X[reps]))
        block_control_drifts = [donor_drift[j] for j in exact_block]
        study_control_drifts = [donor_drift[j] for j in exact_study]
        r_block = ratio_of_medians(d_block, block_control_drifts)
        r_study = ratio_of_medians(d_block, study_control_drifts)

        draws = {k: [] for k in contrast_keys}
        control_drifts = {k: [] for k in ("A", "C")}
        base = seed_for(p)
        for _ in range(args.draws):
            rng = np.random.default_rng(base + 7919 * _)

            drop_A = rng.choice(donors, size=n_p, replace=False)
            keep_A = np.ones(n, bool)
            keep_A[drop_A] = False
            P_A = fit_pcoa(X[keep_A])
            d_A = median_drift(ref, P_A.transform(X[reps]))
            control_drifts["A"].append(d_A)

            drop_C = rng.choice(donors_c, size=nu, replace=False)
            keep_C = np.ones(nc, bool)
            keep_C[drop_C] = False
            P_C = fit_pcoa(Xc[keep_C])
            d_C = median_drift(ref_c, P_C.transform(Xc[E]))
            control_drifts["C"].append(d_C)

            rA = ratio_of_medians(d_block, [d_A])
            rC = ratio_of_medians(d_block_c, [d_C])
            if rA is None or rC is None:
                raise RuntimeError(f"zero control drift in {p}")
            draws["AC"].append(rA - rC)
            if nu == 1:
                draws["ACsingle"].append(rA - rC)
            else:
                draws["ACmulti"].append(rA - rC)
            if r_block is not None:
                draws["ABblock"].append(rA - r_block)
            if r_study is not None:
                draws["ABstudy"].append(rA - r_study)

        for key in design_keys:
            block_value = d_block_c if key == "C" else d_block
            drifts = control_drifts.get(key, [])
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
            per_paper_draws[key][p] = (
                [value] if key in EXHAUSTIVE_KEYS
                else [float(v) for v in (
                    control_drifts[key] if key == "A" else
                    [block_value / d for d in control_drifts[key]]
                )]
            )

        # A per-draw ratios are retained explicitly for the bootstrap fallback.
        per_paper_draws["A"][p] = [
            d_block / d for d in control_drifts["A"]
        ]
        per_paper_draws["C"][p] = [
            d_block_c / d for d in control_drifts["C"]
        ]

        contrast_pairs = {
            "ABblock": ("A", "Bblock"), "ABstudy": ("A", "Bstudy"),
            "AC": ("A", "C"), "ACsingle": ("A", "C"), "ACmulti": ("A", "C"),
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

        meta[p] = {
            "n_rows": n_p, "n_configs": nu, "coherence": coherence[p],
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
            print(f"pcoa {pi}/{len(papers)} {p}", flush=True)

    single = [p for p in papers if n_u[p] == 1]
    multi = [p for p in papers if n_u[p] > 1]
    designs = {}
    for key in design_keys:
        vals = [per_paper[key][p] for p in papers if p in per_paper[key]]
        summary = study_bootstrap(vals)
        summary.update(describe(vals))
        summary["two_level"] = two_level_bootstrap(
            per_paper_draws[key],
            control_drifts=per_paper_control_drifts[key],
            block_drifts=per_paper_block_drift[key],
            fixed_median=key in EXHAUSTIVE_KEYS,
        )
        summary["enumeration"] = "exhaustive" if key in EXHAUSTIVE_KEYS else "monte_carlo"
        designs[key] = summary

    contrast_specs = {
        "ABblock": ("A", "Bblock", single),
        "ABstudy": ("A", "Bstudy", single),
        "AC": ("A", "C", papers),
        "ACsingle": ("A", "C", single),
        "ACmulti": ("A", "C", multi),
    }
    contrasts = {}
    for key in contrast_keys:
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

    subgroups = {
        "single": {
            "role": "primary_focal_claims", "n": len(single),
            "designs": {k: subset_summary(per_paper, single, k) for k in design_keys},
            "contrasts": {
                k: subset_summary(per_paper, single, k)
                for k in ("ABblock", "ABstudy", "AC")
            },
        },
        "multi": {
            "role": "background_only", "n": len(multi),
            "designs": {k: subset_summary(per_paper, multi, k) for k in design_keys},
            "contrasts": {
                k: subset_summary(per_paper, multi, k)
                for k in ("ABblock", "AC")
            },
        },
    }
    strata, donor_distributions = build_strata(
        per_paper, meta, single, design_keys=design_keys
    )
    nested = {
        p: {
            "bstudy_donors": meta[p]["whole_study_donors"],
            "bblock_donors": meta[p]["exact_block_donors"],
            "bblock_only_donors": meta[p]["bblock_only_donor_count"],
            "bstudy_subset_of_bblock": meta[p]["bstudy_subset_of_bblock"],
        }
        for p in single if meta[p]["whole_study_donors"] > 0
    }

    out = {
        "estimator": {
            "name": "ratio_of_medians",
            "formula": "R_s^D = block_drift_s / median(control_drifts_s,D)",
            "block_drift": "median per-row Procrustes displacement",
            "monte_carlo_designs": ["A", "C"],
            "exhaustive_designs": list(EXHAUSTIVE_KEYS),
        },
        "design": {
            **loaded.metadata(),
            "method": "2-D classical PCoA of Jaccard distances",
            "studies": len(papers), "rows": n, "configurations": nc,
            "single_configuration_studies": len(single),
            "multi_configuration_studies_background": len(multi),
            "draws": args.draws, "primary_control": "Bstudy",
            "primary_focal_population": "single_configuration_studies_only",
            "multi_configuration_role": "background_only",
            "bstudy_enumeration": "all exact-size whole single-configuration donor studies",
            "bblock_enumeration": "all exact-size donor configurations",
            "evaluation": (
                "fixed set of all nonfocal within-study configurations; "
                "control-deleted configurations projected into reduced PCoA"
            ),
            "positive_eigenvalues_full": full.eigenvalues.tolist(),
            "positive_eigenvalues_collapsed": full_c.eigenvalues.tolist(),
        },
        "designs": designs, "contrasts": contrasts, "subgroups": subgroups,
        "block_size_strata": strata,
        "donor_pool_size_distributions": donor_distributions,
        "donor_pool_nesting": {
            "n_shared_bstudy_eligible": len(nested),
            "all_nested": all(v["bstudy_subset_of_bblock"] for v in nested.values()),
            "violations": [p for p, v in nested.items() if not v["bstudy_subset_of_bblock"]],
            "per_study": nested,
        },
        "per_paper": per_paper, "per_paper_draws": per_paper_draws,
        "per_paper_control_drifts": per_paper_control_drifts,
        "per_paper_block_drift": per_paper_block_drift, "meta": meta,
    }

    out_path = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results", "unit_revision_fixed", "pcoa_contrast.json",
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps({
        "design": out["design"], "designs": designs, "contrasts": contrasts,
        "subgroups": subgroups,
    }, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
