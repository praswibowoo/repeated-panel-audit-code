#!/usr/bin/env python3
"""coherence_control.py — a coherence-matched deletion control.

The configuration-count-matched control removes the same *number* of unique
configurations as the block arm, but the donors can come from several papers.
The coherence-matched control removes a single donor paper's configuration set
(or a subset of one donor paper) chosen to be close in within-paper Hamming
distance to the focal paper. It therefore matches the *coherence* of the
deleted set, not only its count.

Applied to the 20 multi-configuration papers; one-configuration papers have no
within-paper coherence to match.

Writes results/post_audit/coherence_control.json.

Run: python3 code/coherence_control.py   (about 1 min)
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import DRAWS, fit, median_drift, seed_for, unique_mask, load_curated  # noqa: E402

POST = os.path.join(ROOT, "results", "post_audit")


def _mean_pairwise_hamming(rows: np.ndarray) -> float:
    if len(rows) < 2:
        return 0.0
    vals = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            vals.append(int((rows[i] != rows[j]).sum()))
    return float(np.mean(vals))


def main() -> None:
    X, rho, paper = load_curated()
    uni = unique_mask(X, paper)
    Xc = X[uni]
    paper_c = paper[uni]
    papers = sorted(set(paper))
    cfg = defaultdict(list)
    for p, r in zip(paper, X):
        cfg[p].append(r)
    unique = {}
    for p in papers:
        u = []
        for r in cfg[p]:
            if not any((r == q).all() for q in u):
                u.append(r)
        unique[p] = np.asarray(u)
    n_u = {p: len(unique[p]) for p in papers}
    h = {p: _mean_pairwise_hamming(unique[p]) for p in papers}
    multi = [p for p in papers if n_u[p] > 1]

    S_full_c = fit(Xc)
    per_paper = {}
    for p in multi:
        keep_p = paper_c != p
        block = median_drift(S_full_c[keep_p], fit(Xc[keep_p]))
        donors = [q for q in papers if q != p and n_u[q] == n_u[p]]
        if not donors:
            donors = [q for q in papers if q != p and n_u[q] > n_u[p]]
        fallback = not donors
        if fallback:
            donors = [q for q in papers if q != p]
        # nearest five donors by within-paper Hamming distance
        donors = sorted(donors, key=lambda q: abs(h[q] - h[p]))[:5]
        base = seed_for("coh" + p)
        ratios = []
        for d in range(DRAWS):
            rng = np.random.default_rng(base + 7919 * d)
            q = donors[int(rng.integers(0, len(donors)))]
            q_rows = np.where(paper_c == q)[0]
            if fallback:
                # no donor with >= n_u configurations: use the pooled control
                pool = np.where(paper_c != p)[0]
                drop = rng.choice(pool, size=n_u[p], replace=False)
            elif len(q_rows) > n_u[p]:
                drop = rng.choice(q_rows, size=n_u[p], replace=False)
            else:
                drop = q_rows
            keep_m = np.ones(len(Xc), bool)
            keep_m[drop] = False
            matched = median_drift(S_full_c[keep_m], fit(Xc[keep_m]))
            ratios.append(block / matched)
        per_paper[p] = {
            "n_unique": n_u[p],
            "mean_hamming": h[p],
            "coherence_ratio": float(np.median(ratios)),
            "fallback": fallback,
        }

    vals = np.asarray([per_paper[p]["coherence_ratio"] for p in multi], float)
    out = {
        "n_papers": len(multi),
        "median": float(np.median(vals)),
        "q25": float(np.quantile(vals, 0.25)),
        "q75": float(np.quantile(vals, 0.75)),
        "per_paper": per_paper,
    }
    os.makedirs(POST, exist_ok=True)
    with open(os.path.join(POST, "coherence_control.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps({k: v for k, v in out.items() if k != "per_paper"}, indent=2))
    for p in sorted(per_paper, key=lambda p: -per_paper[p]["coherence_ratio"])[:8]:
        print(p, per_paper[p])


if __name__ == "__main__":
    main()
