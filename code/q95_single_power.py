#!/usr/bin/env python3
"""Power of the calibrated flag for a single-configuration extreme study.

The flag is now scoped to single-configuration studies, so the paper needs the
power for that subgroup, not only the false-positive rate. Uses the planted
all-parameter study from simulation_validation (one configuration per study)
and the 95th percentile of the other 59 studies in the same replicate.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from simulation_validation import simulate, audit  # noqa: E402

SEED = 42
REPS = int(os.environ.get("SP_REPS", 50))


def main():
    rng = np.random.default_rng(SEED)
    q95, gt2, planted, thr = [], [], [], []
    for _ in range(REPS):
        X, paper, pid = simulate(rng, planted=True)
        label = f"S{pid:02d}" if isinstance(pid, (int, np.integer)) else str(pid)
        _, coll = audit(X, paper, rng, draws=20)
        others = np.array([v for k, v in coll.items() if k != label])
        t = float(np.quantile(others, 0.95))
        p = float(coll[label])
        q95.append(p > t)
        gt2.append(p > 2.0)
        planted.append(p)
        thr.append(t)
    out = {
        "design": {"replicates": REPS, "studies": 60, "scenarios": 8,
                   "parameters": 30, "draws": 20, "seed": SEED,
                   "threshold": "q95 of the 59 non-planted ratios"},
        "planted": {"median": float(np.median(planted)),
                    "q025": float(np.quantile(planted, .025)),
                    "q975": float(np.quantile(planted, .975))},
        "threshold_median": float(np.median(thr)),
        "power_at_q95_pct": float(100 * np.mean(q95)),
        "power_at_2_pct": float(100 * np.mean(gt2)),
        "mc_se_pct": float(100 * np.sqrt(np.mean(q95) * (1 - np.mean(q95)) / REPS)),
    }
    with open(os.path.join(ROOT, "results", "post_audit",
                           "q95_single_power.json"), "w") as fh:
        json.dump(out, fh, indent=2); fh.write("\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
