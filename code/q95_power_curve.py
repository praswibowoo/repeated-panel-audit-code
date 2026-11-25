#!/usr/bin/env python3
"""Power curve for the calibrated single-configuration flag.

The effect size is the fraction of the 30 parameters examined by the planted
study. Levels are chosen from the corpus density distribution, not guessed:
0.20 (median), 0.30 (p90), 0.40 (p95), 0.50 (empirical edge), 1.00 (beyond the
corpus, kept as the extreme anchor). Writes q95_power_curve.json.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from common import load_curated, unique_mask  # noqa: E402
from simulation_validation import audit  # noqa: E402

SEED = 42
S, R, P, DRAWS = 60, 8, 30, 20
REPS = int(os.environ.get("PC_REPS", 200))
LEVELS = [float(x) for x in os.environ.get(
    "PC_LEVELS", "0.20,0.30,0.40,0.50,1.00").split(",")]


def sim_frac(rng, frac):
    X, paper = [], []
    pid = int(rng.integers(0, S))
    for s in range(S):
        label = f"S{s:02d}"
        if s == pid:
            k = max(1, int(round(frac * P)))
            base = np.zeros(P)
            base[rng.choice(P, size=k, replace=False)] = 1.0
        else:
            base = (rng.random(P) < 0.30).astype(float)
            if base.sum() == 0:
                base[rng.integers(0, P)] = 1.0
        for _ in range(R):
            X.append(base)
            paper.append(label)
    return np.asarray(X, float), np.asarray(paper, dtype=object), f"S{pid:02d}"


def main():
    X, rho, paper = load_curated()
    uni = unique_mask(X, paper)
    U = X[uni]
    mu = U.mean(0)
    lev = ((U - mu) ** 2).sum(1)
    out = {
        "design": {"studies": S, "scenarios": R, "parameters": P,
                   "draws": DRAWS, "replicates": REPS, "seed": SEED,
                   "levels": LEVELS},
        "corpus": {"density_p90": float(np.percentile(rho, 90)),
                   "density_p95": float(np.percentile(rho, 95)),
                   "density_p99": float(np.percentile(rho, 99)),
                   "leverage_p95": float(np.percentile(lev, 95)),
                   "leverage_p99": float(np.percentile(lev, 99))},
        "levels": {},
    }
    rng = np.random.default_rng(SEED)
    for f in LEVELS:
        powers, ratios, thrs, levq = [], [], [], []
        for _ in range(REPS):
            Xs, ps, pid = sim_frac(rng, f)
            _, coll = audit(Xs, ps, rng, draws=DRAWS)
            others = np.array([v for k, v in coll.items() if k != pid])
            t = float(np.quantile(others, 0.95))
            powers.append(coll[pid] > t)
            ratios.append(float(coll[pid]))
            thrs.append(t)
            u = unique_mask(Xs, ps)
            Uu, puu = Xs[u], ps[u]
            mu2 = Uu.mean(0)
            lv = ((Uu - mu2) ** 2).sum(1)
            base = lv[puu != pid]
            own = lv[puu == pid][0]
            levq.append(float(100 * (base < own).mean()))
        out["levels"][f"{int(round(f*100))}"] = {
            "planted_density": f,
            "planted_ratio_median": float(np.median(ratios)),
            "threshold_median": float(np.median(thrs)),
            "power_pct": float(100 * np.mean(powers)),
            "power_mc_se_pct": float(100 * np.sqrt(
                np.mean(powers) * (1 - np.mean(powers)) / REPS)),
            "leverage_percentile_vs_base": float(np.median(levq)),
        }
    with open(os.path.join(ROOT, "results", "post_audit",
                           "q95_power_curve.json"), "w") as fh:
        json.dump(out, fh, indent=2); fh.write("\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
