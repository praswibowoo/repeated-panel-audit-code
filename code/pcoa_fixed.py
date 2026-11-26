#!/usr/bin/env python3
"""Fixed-evaluation Jaccard PCoA sensitivity for the coverage audit.

This script mirrors the primary fixed-evaluation PCA audit but replaces binary
covariance PCA with two-dimensional classical principal coordinates analysis
of Jaccard distances. Every design is evaluated on the same set of all
nonfocal within-study configurations. Configurations removed by a control are
projected into the reduced PCoA solution rather than omitted from evaluation.

Designs
-------
A       row-count control, full row fit
Bstudy  all exact-size whole single-configuration donor studies enumerated,
        full row fit
Bblock  one exact-size whole-configuration donor, full row fit
C       configuration-count control, collapsed fit

Primary outputs
---------------
A-Bstudy paired whole-study contrast for eligible single-configuration studies
A-Bblock paired configuration-donor contrast
A-C paired protocol contrast
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

from common import load_curated, seed_for, unique_mask  # noqa: E402
from unit_revision_fixed import (  # noqa: E402
    describe,
    mean_pairwise_hamming,
    study_bootstrap,
    two_level_bootstrap,
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
        lo = n - self.dimensions
        vals, vecs = eigh(B, subset_by_index=[lo, n - 1])
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


def subset_summary(per_paper: dict, papers: list[str], key: str) -> dict:
    vals = [per_paper[key][p] for p in papers if p in per_paper[key]]
    out = describe(vals)
    out.update(study_bootstrap(vals))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    X, _, paper = load_curated()
    papers = sorted(set(paper))
    n = len(X)
    uni = unique_mask(X, paper)
    Xc = X[uni]
    pc = paper[uni]
    nc = len(Xc)

    config_rows = []
    for j, p in enumerate(pc):
        config_rows.append(
            np.where((paper == p) & np.all(X == Xc[j], axis=1))[0]
        )
    config_size = np.array([len(v) for v in config_rows], int)
    n_u = {p: int(np.sum(uni & (paper == p))) for p in papers}
    coherence = {
        p: mean_pairwise_hamming(Xc[pc == p])
        for p in papers
    }

    full = fit_pcoa(X)
    full_c = fit_pcoa(Xc)
    S_full = full.transform(X)
    S_full_c = full_c.transform(Xc)

    keys = ("A", "Bblock", "Bstudy", "C", "ABblock", "ABstudy", "AC", "ACsingle", "ACmulti")
    per_paper = {k: {} for k in keys}
    per_paper_draws = {k: {} for k in keys}
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
            int(j) for j in exact_block
            if nu == 1 and n_u[pc[j]] == 1
        ]
        study_control_drifts = []
        for j in exact_study:
            keep_study = np.ones(n, bool)
            keep_study[config_rows[j]] = False
            P_study = fit_pcoa(X[keep_study])
            study_control_drifts.append(
                median_drift(ref, P_study.transform(X[reps]))
            )
        d_study = float(np.median(study_control_drifts)) if study_control_drifts else None
        r_study = d_block / d_study if d_study else None

        draws = {k: [] for k in keys}
        base = seed_for(p)
        for dr in range(args.draws):
            rng = np.random.default_rng(base + 7919 * dr)

            drop_A = rng.choice(donors, size=n_p, replace=False)
            keep_A = np.ones(n, bool)
            keep_A[drop_A] = False
            P_A = fit_pcoa(X[keep_A])
            d_A = median_drift(ref, P_A.transform(X[reps]))
            rA = d_block / d_A

            drop_C = rng.choice(donors_c, size=nu, replace=False)
            keep_C = np.ones(nc, bool)
            keep_C[drop_C] = False
            P_C = fit_pcoa(Xc[keep_C])
            d_C = median_drift(ref_c, P_C.transform(Xc[E]))
            rC = d_block_c / d_C

            draws["A"].append(rA)
            draws["C"].append(rC)
            draws["AC"].append(rA - rC)
            if nu == 1:
                draws["ACsingle"].append(rA - rC)
            else:
                draws["ACmulti"].append(rA - rC)

            if exact_block:
                j = exact_block[int(rng.integers(0, len(exact_block)))]
                keep_R = np.ones(n, bool)
                keep_R[config_rows[j]] = False
                P_R = fit_pcoa(X[keep_R])
                d_R = median_drift(ref, P_R.transform(X[reps]))
                rR = d_block / d_R
                draws["Bblock"].append(rR)
                draws["ABblock"].append(rA - rR)

            # Bstudy: exact enumeration of all eligible whole-study donors.
            if r_study is not None:
                draws["Bstudy"].append(r_study)
                draws["ABstudy"].append(rA - r_study)

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
        }
        if pi % 10 == 0:
            print(f"pcoa {pi}/{len(papers)} {p}", flush=True)

    single = [p for p in papers if n_u[p] == 1]
    multi = [p for p in papers if n_u[p] > 1]

    designs = {}
    for k in ("A", "Bblock", "Bstudy", "C"):
        vals = [per_paper[k][p] for p in papers if p in per_paper[k]]
        summary = study_bootstrap(vals)
        summary.update(describe(vals))
        summary["two_level"] = two_level_bootstrap(per_paper_draws[k])
        designs[k] = summary

    contrasts = {}
    for k in ("ABblock", "ABstudy", "AC", "ACsingle", "ACmulti"):
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
                for k in ("A", "Bblock", "Bstudy", "C")
            },
            "contrasts": {
                k: subset_summary(per_paper, single, k)
                for k in ("ABblock", "ABstudy", "AC")
            },
        },
        "multi": {
            "n": len(multi),
            "designs": {
                k: subset_summary(per_paper, multi, k)
                for k in ("A", "Bblock", "Bstudy", "C")
            },
            "contrasts": {
                k: subset_summary(per_paper, multi, k)
                for k in ("ABblock", "ABstudy", "AC")
            },
        },
    }

    out = {
        "design": {
            "method": "2-D classical PCoA of Jaccard distances",
            "studies": len(papers),
            "rows": n,
            "configurations": nc,
            "draws": args.draws,
            "primary_control": "Bstudy",
            "bstudy_enumeration": "all exact-size whole single-configuration donor studies",
            "evaluation": (
                "fixed set of all nonfocal within-study configurations; "
                "control-deleted configurations projected into reduced PCoA"
            ),
            "positive_eigenvalues_full": full.eigenvalues.tolist(),
            "positive_eigenvalues_collapsed": full_c.eigenvalues.tolist(),
        },
        "designs": designs,
        "contrasts": contrasts,
        "subgroups": subgroups,
        "per_paper": per_paper,
        "per_paper_draws": per_paper_draws,
        "meta": meta,
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
        "design": out["design"],
        "designs": designs,
        "contrasts": contrasts,
        "subgroups": subgroups,
    }, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
