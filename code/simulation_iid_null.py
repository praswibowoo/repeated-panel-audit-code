#!/usr/bin/env python3
"""IID-row null benchmark for the row-count LOSO control.

Unlike simulation_validation.py, rows are generated independently from a
common Bernoulli distribution and only then assigned to study blocks.  This is
the exchangeability null stated for the row-count control.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from simulation_validation import audit, summarise  # noqa: E402

SEED = int(os.environ.get("IID_SEED", 20261125))
S = int(os.environ.get("IID_S", 60))
R = int(os.environ.get("IID_R", 8))
P = int(os.environ.get("IID_P", 30))
DRAWS = int(os.environ.get("IID_DRAWS", 30))
REPS = int(os.environ.get("IID_REPS", 100))
OUT = os.path.join(ROOT, "results", "post_audit", "simulation_iid_null.json")


def simulate(rng):
    X = (rng.random((S * R, P)) < 0.30).astype(float)
    paper = np.repeat([f"S{s:02d}" for s in range(S)], R)
    return X, paper


def main() -> None:
    rng = np.random.default_rng(SEED)
    full, collapsed = [], []
    for rep in range(REPS):
        X, paper = simulate(rng)
        f, c = audit(X, paper, rng, draws=DRAWS)
        full.append(float(np.median(list(f.values()))))
        collapsed.append(float(np.median(list(c.values()))))
        if (rep + 1) % 10 == 0:
            print(f"replicate {rep + 1}/{REPS}", flush=True)
    out = {
        "design": {
            "studies": S, "rows_per_study": R, "parameters": P,
            "draws": DRAWS, "replicates": REPS, "seed": SEED,
            "generation": "IID Bernoulli(0.30) rows assigned to study blocks",
        },
        "row_count_ratio": summarise(full),
        "collapsed_ratio": summarise(collapsed),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
