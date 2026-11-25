#!/usr/bin/env python3
"""Secondary summaries for the unit-of-deletion revision.

All inputs are existing draws or deposited diagnostics.  No new simulation.

Computes:
  * two-level (study + draw) bootstrap intervals for A-B, B-C, A-C;
  * leverage/rows/density correlations against the new A and C ratios;
  * two-term log-linear models of log(A) and log(C);
  * threshold counts for the descriptive-flag caution.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import N_BOOT, data_dir  # noqa: E402

COMMON = os.path.join(ROOT, "results", "unit_revision", "common_contrast.json")
OUT = os.path.join(ROOT, "results", "unit_revision", "secondary.json")


def two_level_bootstrap(per_draw, n_boot=2000, seed=42):
    """Resample studies and all stored draws within each resampled study."""
    papers = sorted(per_draw)
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, len(papers), len(papers))
        vals = []
        for i in idx:
            arr = np.asarray(per_draw[papers[i]], float)
            vals.append(np.median(rng.choice(arr, len(arr), replace=True)))
        boot[b] = np.median(vals)
    return {
        "median": float(np.median(boot)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n_boot": n_boot,
    }


def ols_boot(y, X, n_boot=N_BOOT, seed=42):
    """OLS coefficients with percentile bootstrap intervals."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n, k = X.shape
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    rng = np.random.default_rng(seed)
    boot = np.empty((n_boot, k))
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        boot[b] = np.linalg.lstsq(X[idx], y[idx], rcond=None)[0]
    return {
        "coef": [float(x) for x in beta],
        "ci_lo": [float(x) for x in np.quantile(boot, 0.025, axis=0)],
        "ci_hi": [float(x) for x in np.quantile(boot, 0.975, axis=0)],
        "r2": float(1 - np.sum((y - X @ beta) ** 2) / np.sum((y - y.mean()) ** 2)),
    }


def main():
    d = json.load(open(COMMON))
    papers = sorted(d["per_paper"]["A"])
    A = np.array([d["per_paper"]["A"][p] for p in papers])
    C = np.array([d["per_paper"]["C"][p] for p in papers])
    n_p = np.array([d["meta"][p]["n_p"] for p in papers], float)
    n_u = np.array([d["meta"][p]["n_u"] for p in papers], float)

    lev = pd.read_csv(os.path.join(data_dir(), "leverage_per_paper.csv"))
    if "Unnamed: 0" in lev.columns:
        lev = lev.rename(columns={"Unnamed: 0": "paper"})
    lev = lev.set_index("paper").reindex(papers)
    if lev["lev"].isna().any():
        raise RuntimeError("leverage table does not cover all papers")
    leverage = lev["lev"].to_numpy(float)
    rho = lev["rho"].to_numpy(float)

    out = {
        "n_papers": len(papers),
        "two_level": {
            k: two_level_bootstrap(d["per_paper_draws"][k])
            for k in ("AB", "BC", "AC")
        },
        "correlations": {},
        "models": {},
        "flags": {},
    }

    pairs = {
        "leverage_vs_A": (leverage, A),
        "leverage_vs_C": (leverage, C),
        "rows_vs_A": (n_p, A),
        "rows_vs_C": (n_p, C),
        "density_vs_A": (rho, A),
        "density_vs_C": (rho, C),
        "density_vs_leverage": (rho, leverage),
    }
    for name, (x, y) in pairs.items():
        out["correlations"][name] = {
            "spearman": float(stats.spearmanr(x, y).statistic),
            "pearson": float(stats.pearsonr(x, y).statistic),
        }

    for name, y in (("A", A), ("C", C)):
        X = np.column_stack([np.ones_like(n_p), np.log(n_p), leverage])
        fit = ols_boot(np.log(y), X)
        out["models"][name] = {
            "log_rows_coef": fit["coef"][1],
            "log_rows_ci": [fit["ci_lo"][1], fit["ci_hi"][1]],
            "leverage_coef": fit["coef"][2],
            "leverage_ci": [fit["ci_lo"][2], fit["ci_hi"][2]],
            "r2": fit["r2"],
        }

    for name, vals in (("A", A), ("C", C)):
        out["flags"][name] = {
            "above_2": int(np.sum(vals > 2)),
            "above_2_single": int(np.sum((vals > 2) & (n_u == 1))),
            "above_2_multi": int(np.sum((vals > 2) & (n_u > 1))),
            "above_4": int(np.sum(vals > 4)),
        }

    # Per-study contrast summaries for the main text.
    for k in ("AB", "BC", "AC"):
        x = np.array([d["per_paper"][k][p] for p in papers])
        out.setdefault("contrast_descriptives", {})[k] = {
            "median": float(np.median(x)),
            "iqr": [float(np.quantile(x, 0.25)), float(np.quantile(x, 0.75))],
            "frac_positive": float(np.mean(x > 0)),
            "n": int(len(x)),
        }

    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
