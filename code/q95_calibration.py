#!/usr/bin/env python3
"""Operating characteristics of the per-study screen at a fixed vs calibrated threshold.

For each synthetic mode, the threshold is the 95th percentile of the 59
non-planted ratios in the same replicate (what a practitioner can compute
without a permutation null). Reports:
  - planted flag rate at ratio > 2 and at ratio > corpus q95,
  - corpus-wide flag rate per replicate (share of all 60 studies flagged).
Writes results/post_audit/q95_calibration.json.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from multiconfig_h1 import simulate  # noqa: E402
from simulation_validation import audit  # noqa: E402

REPS = int(os.environ.get("Q95_REPS", 50))
SEED = 42
OUT = os.path.join(ROOT, "results", "post_audit", "q95_calibration.json")

def run(mode, rng, reps=REPS):
    gt2, gq, wide2, wideq, pr = [], [], [], [], []
    for _ in range(reps):
        X, paper, pid = simulate(rng, mode)
        full, coll = audit(X, paper, rng, draws=30)
        others = np.array([v for k, v in coll.items() if k != pid])
        thr = float(np.quantile(others, 0.95))
        p = float(coll[pid])
        gt2.append(p > 2.0); gq.append(p > thr); pr.append(p)
        vals = np.array(list(coll.values()))
        wide2.append(float((vals > 2.0).mean()))
        wideq.append(float((vals > thr).mean()))
    return {"reps": reps,
            "planted_gt2_pct": float(100 * np.mean(gt2)),
            "planted_q95_pct": float(100 * np.mean(gq)),
            "corpus_gt2_pct": float(100 * np.mean(wide2)),
            "corpus_q95_pct": float(100 * np.mean(wideq)),
            "planted_median": float(np.median(pr)),
            "planted_q025": float(np.quantile(pr, .025)),
            "planted_q975": float(np.quantile(pr, .975))}

def main():
    out = {"design": {"studies": 60, "scenarios": 8, "parameters": 30,
                      "draws": 30, "reps": REPS, "seed": SEED,
                      "threshold": "q95 of the 59 non-planted ratios"}}
    rng = np.random.default_rng(SEED)
    for mode in ("H0_coherent", "H1_coherent_extreme", "H1_distinct_extreme"):
        out[mode] = run(mode, rng)
        print(mode, json.dumps(out[mode]))
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2); fh.write("\n")
    print("wrote", OUT)

if __name__ == "__main__":
    main()
