#!/usr/bin/env python3
"""supplementary_checks.py — tail, coherence, and provenance checks.

Adds the checks that the main audit's median-based summary does not expose:

1. within-paper configuration similarity (Hamming distribution);
2. one-configuration vs multi-configuration subgroup ratios;
3. the upper tail of the collapsed and density-matched ratios;
4. a per-study tail-decomposition table (full, collapsed, density, composition);
5. exact-subset descriptive means;
6. the block-percentile median and IQR;
7. the study-level block factor (curated and all-paper).

The point of the file is that every number in the manuscript's tail discussion
and in Table 4's study-level/3-D rows is backed by a deposited artifact.

Writes:
    results/post_audit/tail_audit.json
    results/post_audit/tail_decomposition.csv
    data/study_level_model.json

Run: python3 code/supplementary_checks.py   (about 2 min)
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import EXCLUDED, SEED, data_dir, load_curated  # noqa: E402

DATA = data_dir()
POST = os.path.join(ROOT, "results", "post_audit")
OUT_DATA = os.path.join(DATA, "study_level_model.json")


def _unique(rows):
    u = []
    for r in rows:
        if not any((r == q).all() for q in u):
            u.append(r)
    return u


def _ratio(block, matched):
    return (block / matched).dropna()


def _median_ci(values, n_boot=10000, seed=SEED):
    x = np.asarray(values, float)
    x = x[~np.isnan(x)]
    rng = np.random.default_rng(seed)
    boot = np.array([np.median(x[rng.integers(0, len(x), len(x))])
                     for _ in range(n_boot)])
    return {"median": float(np.median(x)),
            "ci_lo": float(np.quantile(boot, 0.025)),
            "ci_hi": float(np.quantile(boot, 0.975)),
            "n": int(len(x))}


def _two_level_bootstrap(block, matched_draws, n_boot=2000, seed=SEED):
    """Resample studies, then resample each study's matched draws.

    This captures both between-study and within-study (matched-draw) Monte Carlo
    variability, unlike the study-cluster bootstrap that resamples studies only.
    """
    papers = list(block.index)
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(n_boot):
        sel = rng.choice(papers, len(papers), replace=True)
        vals = []
        for p in sel:
            draws = matched_draws[p]
            med = np.median(rng.choice(draws, len(draws), replace=True))
            vals.append(block[p] / med)
        boot.append(np.median(vals))
    boot = np.asarray(boot, float)
    return {
        "median": float(np.median(boot)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n": int(len(papers)),
        "n_boot": int(n_boot),
    }


def _two_level_from_draws(draws_by_paper, n_boot=2000, seed=SEED):
    """Two-level bootstrap from per-paper draw arrays (no new PCA fits)."""
    papers = list(draws_by_paper)
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(n_boot):
        sel = rng.choice(papers, len(papers), replace=True)
        vals = []
        for p in sel:
            arr = np.asarray(draws_by_paper[p], float)
            vals.append(np.median(rng.choice(arr, len(arr), replace=True)))
        boot.append(np.median(vals))
    boot = np.asarray(boot, float)
    return {
        "median": float(np.median(boot)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n": int(len(papers)),
        "n_boot": int(n_boot),
    }


def _study_level_model(block, matched, rows):
    """Two-row-per-study log-linear model: log(d) ~ 1 + log(rows_c) + block."""
    df = []
    for p in block.index:
        if p not in matched.index:
            continue
        df.append((p, 1, np.log(block[p]), float(rows[p])))
        df.append((p, 0, np.log(matched[p]), float(rows[p])))
    df = pd.DataFrame(df, columns=["paper", "block", "logd", "n"])
    df["lc"] = np.log(df["n"]) - np.log(df["n"]).mean()
    X = np.column_stack([np.ones(len(df)), df["lc"], df["block"]])
    y = df["logd"].values
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    papers = df["paper"].unique()
    rng = np.random.default_rng(SEED)
    boot = []
    for _ in range(1000):
        sel = rng.choice(papers, len(papers), replace=True)
        d2 = pd.concat([df[df["paper"] == p] for p in sel])
        X2 = np.column_stack([np.ones(len(d2)), d2["lc"], d2["block"]])
        b2 = np.linalg.lstsq(X2, d2["logd"].values, rcond=None)[0]
        boot.append(np.exp(b2[2]))
    return {
        "median": float(np.exp(beta[2])),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n": int(len(papers)),
        "model": "log(d) ~ 1 + log(rows_c) + block; study-cluster bootstrap",
    }


def main() -> None:
    X, rho, paper = load_curated()
    n = len(X)
    papers = sorted(set(paper))
    cfg = defaultdict(list)
    for p, r in zip(paper, X):
        cfg[p].append(r)

    # ------------------------------------------------------------------
    # Panel structure and Hamming distribution
    # ------------------------------------------------------------------
    per_paper = {}
    hamming = Counter()
    pairs = 0
    for p in papers:
        u = _unique(cfg[p])
        rows = len(cfg[p])
        per_paper[p] = {
            "rows": rows,
            "unique": len(u),
            "duplicate_fraction": (rows - len(u)) / rows,
            "density": float(np.mean([q.mean() for q in cfg[p]])),
        }
        if len(u) > 1:
            for i in range(len(u)):
                for j in range(i + 1, len(u)):
                    h = int((u[i] != u[j]).sum())
                    hamming[h] += 1
                    pairs += 1
    hamming = dict(sorted(hamming.items()))
    n_multi = sum(1 for p in papers if per_paper[p]["unique"] > 1)

    # ------------------------------------------------------------------
    # Event tables
    # ------------------------------------------------------------------
    bb = pd.read_csv(os.path.join(DATA, "baseline_block.csv"))
    bm = pd.read_csv(os.path.join(DATA, "baseline_matched.csv"))
    cb = pd.read_csv(os.path.join(DATA, "collapsed_block.csv"))
    cm = pd.read_csv(os.path.join(DATA, "collapsed_matched.csv"))
    block_full = bb[bb.arm == "block"].set_index("paper")["med_drift"]
    match_full = bm[bm.arm == "matched"].groupby("paper")["med_drift"].median()
    block_coll = cb[cb.arm == "block"].set_index("paper")["med_drift"]
    match_coll = cm[cm.arm == "matched"].groupby("paper")["med_drift"].median()
    full_ratio = _ratio(block_full, match_full)
    coll_ratio = _ratio(block_coll, match_coll)

    dec = json.load(open(os.path.join(POST, "panel_decomposition.json"), encoding="utf-8"))
    dens = {p: float(v) for p, v in dec["density_matched_collapsed_per_paper"].items()}

    bm_draws = {p: g["med_drift"].values
                for p, g in bm[bm.arm == "matched"].groupby("paper")}
    cm_draws = {p: g["med_drift"].values
                for p, g in cm[cm.arm == "matched"].groupby("paper")}
    two_level = {
        "full": _two_level_bootstrap(block_full, bm_draws),
        "collapsed": _two_level_bootstrap(block_coll, cm_draws),
    }
    draw_path = os.path.join(POST, "panel_decomposition_draws.json")
    if os.path.exists(draw_path):
        pd_draws = json.load(open(draw_path, encoding="utf-8"))
        if "collapsed_unique" in pd_draws:
            two_level["common_evaluation"] = _two_level_from_draws(
                pd_draws["collapsed_unique"])
        if "density_matched" in pd_draws:
            two_level["density_matched"] = _two_level_from_draws(
                pd_draws["density_matched"])

    comp = pd.read_csv(os.path.join(DATA, "composition_matched_control.csv"))
    comp_match = (comp[comp.arm == "composition_matched"]
                  .groupby("paper")["med_drift"].median())
    comp_ratio = _ratio(block_full, comp_match)

    coh_path = os.path.join(POST, "coherence_control.json")
    coh = json.load(open(coh_path, encoding="utf-8")) if os.path.exists(coh_path) else {}

    # ------------------------------------------------------------------
    # Tail proportions
    # ------------------------------------------------------------------
    def tail(series):
        s = series.dropna()
        return {f">{t}": {"n": int((s > t).sum()),
                          "pct": float(100.0 * (s > t).mean())}
                for t in (1.5, 2.0, 3.0, 4.0)}

    # ------------------------------------------------------------------
    # One-config vs multi-config subgroup
    # ------------------------------------------------------------------
    one = [coll_ratio[p] for p in papers if per_paper[p]["unique"] == 1]
    multi = [coll_ratio[p] for p in papers if per_paper[p]["unique"] > 1]

    # ------------------------------------------------------------------
    # Exact-subset descriptive means
    # ------------------------------------------------------------------
    exact_papers = sorted(comp[comp.arm == "composition_matched"]
                          .groupby("paper")["exact_fraction"].mean()
                          .loc[lambda s: s > 0].index)
    def means(ps):
        return {
            "n": len(ps),
            "mean_rows": float(np.mean([per_paper[p]["rows"] for p in ps])),
            "mean_unique": float(np.mean([per_paper[p]["unique"] for p in ps])),
            "mean_duplicate_fraction": float(np.mean([per_paper[p]["duplicate_fraction"] for p in ps])),
            "mean_density": float(np.mean([per_paper[p]["density"] for p in ps])),
        }
    exact_means = means(exact_papers)
    other_means = means([p for p in papers if p not in set(exact_papers)])

    # ------------------------------------------------------------------
    # Block percentile (median, IQR)
    # ------------------------------------------------------------------
    pct = []
    for p in block_full.index:
        vals = bm[(bm.arm == "matched") & (bm.paper == p)]["med_drift"].values
        pct.append(100.0 * (np.sum(vals < block_full[p]) +
                            0.5 * np.sum(vals == block_full[p])) / len(vals))
    pct = np.asarray(pct)
    block_pct = {
        "median": float(np.median(pct)),
        "q25": float(np.quantile(pct, 0.25)),
        "q75": float(np.quantile(pct, 0.75)),
        "n": int(len(pct)),
    }

    # ------------------------------------------------------------------
    # Tail table
    # ------------------------------------------------------------------
    rows = []
    for p in coll_ratio.sort_values(ascending=False).head(12).index:
        u = _unique(cfg[p])
        ham = None
        if len(u) == 2:
            ham = int((u[0] != u[1]).sum())
        elif len(u) > 2:
            ham = min(int((a != b).sum()) for i, a in enumerate(u)
                      for b in u[i + 1:])
        coh_val = coh.get("per_paper", {}).get(p, {}).get("coherence_ratio", np.nan)
        rows.append({
            "paper": p,
            "full_ratio": float(full_ratio[p]),
            "collapsed_ratio": float(coll_ratio[p]),
            "density_matched_ratio": float(dens.get(p, np.nan)),
            "composition_ratio": float(comp_ratio.get(p, np.nan)),
            "coherence_ratio": float(coh_val) if not pd.isna(coh_val) else np.nan,
            "unique_configs": len(u),
            "min_hamming": ham,
        })
    tail_table = pd.DataFrame(rows)
    tail_table.to_csv(os.path.join(POST, "tail_decomposition.csv"), index=False)

    # ------------------------------------------------------------------
    # Study-level model (curated and all-paper)
    # ------------------------------------------------------------------
    study_level = _study_level_model(block_full, match_full,
                                     bb.set_index("paper")["n_rows_deleted"])
    ap = json.load(open(os.path.join(POST, "all_paper_audit.json"), encoding="utf-8"))
    pp = ap["per_paper"]
    ap_block = pd.Series({p: v["block"] for p, v in pp.items()})
    ap_match = pd.Series({p: v["matched_median"] for p, v in pp.items()})
    ap_rows = pd.Series({p: v["rows"] for p, v in pp.items()})
    study_level_all = _study_level_model(ap_block, ap_match, ap_rows)

    out = {
        "panel_structure": {
            "n_papers": len(papers),
            "n_rows": n,
            "n_unique_configs": int(sum(v["unique"] for v in per_paper.values())),
            "n_single_config_papers": int(sum(1 for v in per_paper.values() if v["unique"] == 1)),
            "n_multi_config_papers": n_multi,
        },
        "hamming": {
            "pairs": pairs,
            "distribution": {str(k): int(v) for k, v in hamming.items()},
            "pairs_le_3": int(sum(v for k, v in hamming.items() if k <= 3)),
            "pairs_le_2": int(sum(v for k, v in hamming.items() if k <= 2)),
        },
        "tail": {
            "full": tail(full_ratio),
            "collapsed": tail(coll_ratio),
            "density_matched": tail(pd.Series(dens)),
        },
        "subgroup": {
            "one_config": _median_ci(one),
            "multi_config": _median_ci(multi),
        },
        "exact_subset": {
            "papers": exact_papers,
            "exact": exact_means,
            "other": other_means,
        },
        "block_percentile": block_pct,
        "two_level_bootstrap": two_level,
        "study_level_model": {
            "curated": study_level,
            "all_paper": study_level_all,
        },
        "tail_table": rows,
        "coherence_control": coh,
    }

    with open(os.path.join(POST, "tail_audit.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    with open(OUT_DATA, "w", encoding="utf-8") as fh:
        json.dump(out["study_level_model"], fh, indent=2)
        fh.write("\n")

    print(json.dumps({k: v for k, v in out.items() if k != "tail_table"},
                     indent=2))
    print("\nwrote", os.path.join(POST, "tail_audit.json"))
    print("wrote", os.path.join(POST, "tail_decomposition.csv"))
    print("wrote", OUT_DATA)


if __name__ == "__main__":
    main()
