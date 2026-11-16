#!/usr/bin/env python3
"""Multi-configuration stress test for the collapsed audit.

Three scenarios, 50 synthetic corpora each, 60 studies, 8 scenarios per study,
30 parameters:

  H0_coherent:          one study has three near-identical configurations and
                        no extreme configuration. This is a false-positive
                        control: the collapsed audit may flag coherence alone.
  H1_coherent_extreme:  one study has three near-identical configurations, all
                        extreme (all parameters present).
  H1_distinct_extreme:  one study has three distinct configurations, one of
                        which is extreme.

The audit is the same as simulation_validation.py: full row-level and
configuration-collapsed block/matched deletion, 30 matched draws.

Writes results/post_audit/multiconfig_h1.json.
Run: python3 code/multiconfig_h1.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from simulation_validation import audit, summarise  # noqa: E402

SEED = int(os.environ.get("SIM_SEED", 42))
S = 60
R = 8
P = 30
DRAWS = 30
REPS = int(os.environ.get("SIM_REPS", 50))
OUT = os.path.join(ROOT, "results", "post_audit", "multiconfig_h1.json")


def _flip(base: np.ndarray, rng: np.random.Generator, k: int) -> np.ndarray:
    out = base.copy()
    pos = rng.choice(P, size=k, replace=False)
    out[pos] = 1.0 - out[pos]
    return out


def simulate(rng: np.random.Generator, mode: str):
    """Return X, paper, planted_id."""
    X, paper = [], []
    planted_id = int(rng.integers(0, S))
    for s in range(S):
        label = f"S{s:02d}"
        base = (rng.random(P) < 0.30).astype(float)
        if base.sum() == 0:
            base[rng.integers(0, P)] = 1.0
        if s == planted_id:
            if mode == "H0_coherent":
                c = [base, _flip(base, rng, 1), _flip(base, rng, 2)]
            elif mode == "H1_coherent_extreme":
                ext = np.ones(P, dtype=float)
                c = [ext, _flip(ext, rng, 1), _flip(ext, rng, 1)]
            elif mode == "H1_distinct_extreme":
                c = [base, _flip(base, rng, 10), np.ones(P, dtype=float)]
            else:
                raise ValueError(mode)
            for r in range(R):
                X.append(c[r % 3])
                paper.append(label)
        else:
            for _ in range(R):
                X.append(base)
                paper.append(label)
    return np.asarray(X, float), np.asarray(paper, dtype=object), f"S{planted_id:02d}"


def main() -> None:
    rng = np.random.default_rng(SEED)
    out = {
        "design": {"studies": S, "scenarios_per_study": R, "parameters": P,
                   "matched_draws": DRAWS, "replicates": REPS, "seed": SEED},
    }
    for mode in ("H0_coherent", "H1_coherent_extreme", "H1_distinct_extreme"):
        planted, top1, top3, above2, rank_pct, max_other = [], [], [], [], [], []
        full_med, coll_med = [], []
        for _ in range(REPS):
            X, paper, pid = simulate(rng, mode)
            full, coll = audit(X, paper, rng, draws=DRAWS)
            full_med.append(float(np.median(list(full.values()))))
            coll_med.append(float(np.median(list(coll.values()))))
            planted.append(coll[pid])
            ranked = sorted(coll, key=coll.get, reverse=True)
            rank = ranked.index(pid) + 1
            top1.append(1.0 if rank == 1 else 0.0)
            top3.append(1.0 if rank <= 3 else 0.0)
            above2.append(1.0 if coll[pid] > 2.0 else 0.0)
            rank_pct.append(100.0 * (1.0 - (rank - 1) / (len(coll) - 1)))
            max_other.append(max(v for k, v in coll.items() if k != pid))
        out[mode] = {
            "full_ratio": summarise(full_med),
            "collapsed_ratio": summarise(coll_med),
            "planted_ratio": summarise(planted),
            "top1_pct": float(100.0 * np.mean(top1)),
            "top3_pct": float(100.0 * np.mean(top3)),
            "above2_pct": float(100.0 * np.mean(above2)),
            "rank_percentile_median": float(np.median(rank_pct)),
            "max_other_ratio": summarise(max_other),
        }
        print(mode, json.dumps(out[mode], indent=1))

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
