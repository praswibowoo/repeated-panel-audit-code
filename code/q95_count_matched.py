#!/usr/bin/env python3
"""Count-matched null for a 3-configuration study.

The pooled q95 uses single-configuration studies to calibrate a
three-configuration study. This script builds the correct null: random
three-configuration pseudo-studies assembled from single-configuration studies.
It tests whether the 38% coherent-null flag rate is a count-calibration defect
or a coherence effect.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from multiconfig_h1 import simulate as sim_multi  # noqa: E402
from simulation_validation import simulate as sim_single, audit  # noqa: E402

SEED = 42
REPS = int(os.environ.get("CM_REPS", 200))
PSEUDO = int(os.environ.get("CM_PSEUDO", 100))


def pseudo_null(rng, reps=PSEUDO):
    vals = []
    for _ in range(reps):
        X, paper, _ = sim_single(rng, planted=False)
        papers = sorted(set(paper))
        chosen = rng.choice(papers, size=3, replace=False)
        rows = [int(np.where(paper == p)[0][0]) for p in chosen]
        keep = ~np.isin(paper, chosen)
        Xp = np.vstack([X[keep], X[rows]])
        pp = np.concatenate([paper[keep], np.array(["PSEUDO"] * 3)])
        _, coll = audit(Xp, pp, rng, draws=20)
        vals.append(float(coll["PSEUDO"]))
    return np.asarray(vals)


def main():
    rng = np.random.default_rng(SEED)
    planted = []
    for _ in range(REPS):
        X, paper, pid = sim_multi(rng, "H0_coherent")
        _, coll = audit(X, paper, rng, draws=20)
        planted.append(float(coll[pid]))
    planted = np.asarray(planted)
    null = pseudo_null(rng)
    q95 = float(np.quantile(null, 0.95))
    out = {
        "design": {"replicates": REPS, "pseudo_replicates": PSEUDO,
                   "studies": 60, "scenarios": 8, "parameters": 30, "seed": SEED},
        "planted": {"median": float(np.median(planted)),
                    "q025": float(np.quantile(planted, .025)),
                    "q975": float(np.quantile(planted, .975))},
        "count_matched_null": {"median": float(np.median(null)),
                               "q95": q95,
                               "q025": float(np.quantile(null, .025)),
                               "q975": float(np.quantile(null, .975)),
                               "n": int(len(null))},
        "fpr_at_count_matched_q95": float(100 * (planted > q95).mean()),
        "fpr_at_2": float(100 * (planted > 2.0).mean()),
    }
    with open(os.path.join(ROOT, "results", "post_audit",
                           "q95_count_matched.json"), "w") as fh:
        json.dump(out, fh, indent=2); fh.write("\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
