#!/usr/bin/env python3
"""Independent permutation null for the collapsed audit.

Study labels are permuted across the 145 unique coverage configurations while
preserving each paper's number of unique configurations. For every permutation
the collapsed block/matched ratio is recomputed with 20 matched draws per
paper. The pooled per-paper ratios form the null distribution; the permutation
medians form the null for the corpus-wide median.

This replaces the internal matched-draw reference (control arm used as its own
reference) with a label permutation that is independent of the focal paper.

Writes ``tail_permutation.json`` next to the coverage matrix.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import data_dir, fit, median_drift, unique_mask, load_curated  # noqa: E402

PERMS = 100
DRAWS = 20
THRESH = (1.5, 2.0, 3.0, 4.0)
SEED = 20261116


def _tail(null_values: np.ndarray, observed: np.ndarray) -> dict:
    out = {}
    for t in THRESH:
        p = float((null_values > t).mean())
        out[f"{t:g}"] = {
            "null_pct": 100.0 * p,
            "expected": float(len(observed) * p),
            "observed": int((observed > t).sum()),
        }
    return out


def _summ(values: np.ndarray) -> dict:
    return {
        "median": float(np.median(values)),
        "q025": float(np.quantile(values, 0.025)),
        "q975": float(np.quantile(values, 0.975)),
        "q95": float(np.quantile(values, 0.95)),
        "n": int(len(values)),
    }


def main() -> None:
    X, rho, paper = load_curated()
    uni = unique_mask(X, paper)
    Xc = X[uni]
    paper_c = paper[uni]
    papers = sorted(set(paper))
    n_u = {p: int((paper_c == p).sum()) for p in papers}
    S_full = fit(Xc)

    rng = np.random.default_rng(SEED)
    rows = []
    perm_medians = []
    for perm in range(PERMS):
        perm_paper = rng.permutation(paper_c)
        ratios = []
        for p in papers:
            n = n_u[p]
            block_rows = np.where(perm_paper == p)[0]
            keep = np.ones(len(Xc), bool)
            keep[block_rows] = False
            block = median_drift(S_full[keep], fit(Xc[keep]))
            donors = np.where(perm_paper != p)[0]
            draws = []
            for _ in range(DRAWS):
                drop = rng.choice(donors, size=n, replace=False)
                km = np.ones(len(Xc), bool)
                km[drop] = False
                draws.append(median_drift(S_full[km], fit(Xc[km])))
            ratios.append(block / float(np.median(draws)))
        perm_medians.append(float(np.median(ratios)))
        for p, r in zip(papers, ratios):
            rows.append((perm, p, n_u[p], float(r)))

    null = pd.DataFrame(rows, columns=["perm", "paper", "n_unique", "ratio"])

    # Observed primary collapsed audit on its own retained rows.
    data = data_dir()
    rebuild_path = os.path.join(ROOT, "results", "rebuild", "collapsed_events_rebuilt.csv")
    if os.path.exists(rebuild_path):
        events = pd.read_csv(rebuild_path)
        cb = events[events.arm == "block"]
        cm = events[events.arm == "matched"]
    else:
        cb = pd.read_csv(os.path.join(data, "collapsed_block.csv"))
        cm = pd.read_csv(os.path.join(data, "collapsed_matched.csv"))
    block = cb[cb.arm == "block"].set_index("paper")["med_drift"]
    matched = cm[cm.arm == "matched"].groupby("paper")["med_drift"].median()
    observed = (block / matched).dropna()

    groups = {
        "single": null[null.n_unique == 1]["ratio"].to_numpy(),
        "multi": null[null.n_unique > 1]["ratio"].to_numpy(),
        "all": null["ratio"].to_numpy(),
    }
    obs_groups = {
        "single": observed[[p for p in observed.index if n_u[p] == 1]].to_numpy(),
        "multi": observed[[p for p in observed.index if n_u[p] > 1]].to_numpy(),
        "all": observed.to_numpy(),
    }

    out = {
        "method": (
            "study labels permuted across the 145 unique configurations, "
            "preserving each paper's configuration count; collapsed "
            "block/matched ratio with 20 matched draws per paper"
        ),
        "n_permutations": PERMS,
        "draws_per_paper": DRAWS,
        "seed": SEED,
        "observed": _summ(observed.to_numpy()),
        "permutation_medians": {
            **_summ(np.asarray(perm_medians, float)),
            "p_ge_observed_median": float(
                np.mean(np.asarray(perm_medians) >= np.median(observed))
            ),
        },
        "groups": {},
    }
    for name in ("single", "multi", "all"):
        vals = groups[name]
        obs = obs_groups[name]
        out["groups"][name] = {
            "n_observed": int(len(obs)),
            "n_null": int(len(vals)),
            "null": _summ(vals),
            "observed": _summ(obs),
            "tail": _tail(vals, obs),
        }

    path = os.path.join(data, "tail_permutation.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
