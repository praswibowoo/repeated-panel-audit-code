#!/usr/bin/env python3
"""Pilot: where does the single-configuration flag gain power?

Computes (a) the corpus row-density and configuration-leverage distributions,
and (b) a short power curve for a planted single-configuration study that
examines a fraction f of the 30 parameters. Used only to choose the effect-size
levels for the final table; not a manuscript deposit.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from common import load_curated, unique_mask  # noqa: E402
from simulation_validation import audit  # noqa: E402

SEED = 42
S, R, P, DRAWS, REPS = 60, 8, 30, 20, 10
FRACS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


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


def pct(x, q):
    return float(np.percentile(np.asarray(x, float), q))


def main():
    X, rho, paper = load_curated()
    uni = unique_mask(X, paper)
    U, pu = X[uni], paper[uni]
    mu = U.mean(0)
    lev = ((U - mu) ** 2).sum(1)
    out = {
        "corpus": {
            "row_density": {q: pct(rho, q) for q in (5, 25, 50, 75, 90, 95, 99)},
            "config_leverage": {q: pct(lev, q) for q in (5, 25, 50, 75, 90, 95, 99)},
            "n_rows": int(len(X)), "n_unique": int(len(lev)),
        },
        "pilot": {},
    }
    rng = np.random.default_rng(SEED)
    for f in FRACS:
        ratios, powers, thrs, levq = [], [], [], []
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
        out["pilot"][f"{int(f*100):d}"] = {
            "planted_ratio_median": float(np.median(ratios)),
            "threshold_median": float(np.median(thrs)),
            "power_pct": float(100 * np.mean(powers)),
            "leverage_percentile_vs_base": float(np.median(levq)),
        }
    print(json.dumps(out, indent=1))
    with open(os.path.join(ROOT, "results", "post_audit",
                           "power_levels_pilot.json"), "w") as fh:
        json.dump(out, fh, indent=2); fh.write("\n")


if __name__ == "__main__":
    main()
