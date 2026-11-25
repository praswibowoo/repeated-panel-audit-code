#!/usr/bin/env python3
"""Fixed-evaluation synthetic benchmarks for the repeated-panel audit.

Unlike simulation_validation.py and simulation_iid_null.py, this script uses
the primary fixed evaluation set and projects control-deleted configurations
into each reduced PCA solution. It therefore validates the exact estimator used
in the revised main analysis.

Scenarios
---------
H0 repeated configurations:
    60 studies; each Bernoulli base pattern replicated eight times.
H1 planted study:
    H0 with one all-parameter study.
IID rows:
    Independent Bernoulli(0.30) rows assigned to study blocks.

Outputs are median per-study ratios across 100 synthetic corpora. Intervals
are 2.5--97.5% across corpora, not bootstrap confidence intervals.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import unique_mask  # noqa: E402
from unit_revision_fixed import fit_pca, median_drift  # noqa: E402

SEED = 20261125
S = 60
R = 8
P = 30
DRAWS = 30
REPS = 100
OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "results", "post_audit", "simulation_fixed.json",
)


def simulate(rng: np.random.Generator, kind: str):
    X, labels = [], []
    planted = None
    if kind == "planted":
        planted = int(rng.integers(0, S))
    for s in range(S):
        label = f"S{s:02d}"
        if kind == "iid":
            rows = (rng.random((R, P)) < 0.30).astype(float)
        else:
            if s == planted:
                base = np.ones(P, dtype=float)
            else:
                base = (rng.random(P) < 0.30).astype(float)
                if base.sum() == 0:
                    base[int(rng.integers(0, P))] = 1.0
            rows = np.repeat(base[None, :], R, axis=0)
        X.append(rows)
        labels.extend([label] * R)
    return np.vstack(X).astype(float), np.asarray(labels, dtype=object), planted


def audit(X: np.ndarray, paper: np.ndarray, rng: np.random.Generator):
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    Xc, pc = X[uni], paper[uni]
    n, nc = len(X), len(Xc)

    config_rows = []
    for j, p in enumerate(pc):
        config_rows.append(
            np.where((paper == p) & np.all(X == Xc[j], axis=1))[0]
        )

    full = fit_pca(X)
    full_c = fit_pca(Xc)
    S_full = full.transform(X)
    S_full_c = full_c.transform(Xc)

    A, C = {}, {}
    for p in papers:
        n_p = int(np.sum(paper == p))
        nu = int(np.sum(uni[paper == p]))
        keep_block = paper != p
        keep_block_c = pc != p
        E = np.where(keep_block_c)[0]
        reps = np.array([config_rows[j][0] for j in E], int)
        ref = S_full[reps]
        ref_c = S_full_c[E]

        P_block = fit_pca(X[keep_block])
        d_block = median_drift(ref, P_block.transform(X[reps]))
        P_block_c = fit_pca(Xc[keep_block_c])
        d_block_c = median_drift(ref_c, P_block_c.transform(Xc[E]))

        donors = np.where(keep_block)[0]
        donors_c = np.where(keep_block_c)[0]
        rA, rC = [], []
        for _ in range(DRAWS):
            drop_A = rng.choice(donors, size=n_p, replace=False)
            keep_A = np.ones(n, bool)
            keep_A[drop_A] = False
            P_A = fit_pca(X[keep_A])
            rA.append(d_block / median_drift(ref, P_A.transform(X[reps])))

            drop_C = rng.choice(donors_c, size=nu, replace=False)
            keep_C = np.ones(nc, bool)
            keep_C[drop_C] = False
            P_C = fit_pca(Xc[keep_C])
            rC.append(d_block_c / median_drift(ref_c, P_C.transform(Xc[E])))

        A[p] = float(np.median(rA))
        C[p] = float(np.median(rC))
    return A, C


def summarise(values) -> dict:
    x = np.asarray(values, float)
    return {
        "median": float(np.median(x)),
        "q025": float(np.quantile(x, 0.025)),
        "q975": float(np.quantile(x, 0.975)),
        "mean": float(np.mean(x)),
    }


def main() -> None:
    rng = np.random.default_rng(SEED)
    out = {
        "design": {
            "studies": S,
            "rows_per_study": R,
            "parameters": P,
            "draws": DRAWS,
            "replicates": REPS,
            "seed": SEED,
            "estimator": "fixed nonfocal configuration set with out-of-fit projection",
        },
        "H0_repeated": {},
        "H1_planted": {},
        "IID_rows": {},
    }
    h0_A, h0_C = [], []
    h1_A, h1_C, planted_C, planted_top1, planted_above2 = [], [], [], [], []
    iid_A, iid_C = [], []

    for rep in range(REPS):
        X, paper, _ = simulate(rng, "repeated")
        A, C = audit(X, paper, rng)
        h0_A.append(float(np.median(list(A.values()))))
        h0_C.append(float(np.median(list(C.values()))))

        X, paper, planted = simulate(rng, "planted")
        A, C = audit(X, paper, rng)
        h1_A.append(float(np.median(list(A.values()))))
        h1_C.append(float(np.median(list(C.values()))))
        pid = f"S{planted:02d}"
        planted_C.append(C[pid])
        rank = sorted(C, key=C.get, reverse=True).index(pid) + 1
        planted_top1.append(rank == 1)
        planted_above2.append(C[pid] > 2)

        X, paper, _ = simulate(rng, "iid")
        A, C = audit(X, paper, rng)
        iid_A.append(float(np.median(list(A.values()))))
        iid_C.append(float(np.median(list(C.values()))))

        if (rep + 1) % 10 == 0:
            print(f"fixed simulation {rep + 1}/{REPS}", flush=True)

    out["H0_repeated"] = {
        "full_ratio": summarise(h0_A),
        "collapsed_ratio": summarise(h0_C),
    }
    out["H1_planted"] = {
        "full_ratio": summarise(h1_A),
        "collapsed_ratio": summarise(h1_C),
        "planted_collapsed_ratio": summarise(planted_C),
        "planted_top1_pct": float(100 * np.mean(planted_top1)),
        "planted_above_2x_pct": float(100 * np.mean(planted_above2)),
    }
    out["IID_rows"] = {
        "full_ratio": summarise(iid_A),
        "collapsed_ratio": summarise(iid_C),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
