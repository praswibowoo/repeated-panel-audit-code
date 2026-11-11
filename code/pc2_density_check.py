#!/usr/bin/env python3
"""PC1/PC2/joint class flips under a study-density-matched collapsed control.

The manuscript's collapsed class comparison uses row-level matched draws from
the whole corpus.  PC2 is the density axis, so that control can induce a
density-composition artifact.  This script repeats the collapsed class audit
with donors drawn from the same study-density quartile.

Writes results/post_audit/pc2_density_check.json.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from core_revision_checks import load_curated  # noqa: E402
from panel_decomposition import fit, unique_mask, SEED, DRAWS  # noqa: E402

OUT = os.path.join(ROOT, "results", "post_audit")


def class_flips(ref, red_common):
    """PC1, PC2, and joint quartile-class flip percentages."""
    out = []
    for ax in (0, 1):
        a = ref[:, ax].copy()
        b = red_common[:, ax].copy()
        c = np.corrcoef(a, b)[0, 1]
        if np.isfinite(c) and c < 0:
            b = -b
        b = (b - b.mean()) / b.std() * a.std() + a.mean()
        cuts = np.quantile(a, [0.25, 0.50, 0.75])
        qa = np.searchsorted(cuts, a, side="right")
        qb = np.searchsorted(cuts, b, side="right")
        out.append((qa, qb))
    pc1 = 100.0 * float(np.mean(out[0][0] != out[0][1]))
    pc2 = 100.0 * float(np.mean(out[1][0] != out[1][1]))
    joint = 100.0 * float(np.mean((out[0][0] != out[0][1]) |
                                  (out[1][0] != out[1][1])))
    return pc1, pc2, joint


def median_ci(values, n_boot=10000, seed=SEED):
    x = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        boot[i] = np.median(x[rng.integers(0, len(x), len(x))])
    return {"median": float(np.median(x)),
            "ci_lo": float(np.quantile(boot, 0.025)),
            "ci_hi": float(np.quantile(boot, 0.975)),
            "n": int(len(x))}


def main():
    X, rho, paper = load_curated()
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    Xc = X[uni]
    paper_c = paper[uni]
    rho_s = {p: float(np.mean(rho[paper == p])) for p in papers}
    cuts = np.quantile([rho_s[p] for p in papers], [0.25, 0.50, 0.75])
    qbin = {p: int(np.searchsorted(cuts, rho_s[p], side="right")) for p in papers}

    S_full_c = fit(Xc)
    diffs = {k: {} for k in ("pc1", "pc2", "joint")}

    for p in papers:
        keep_block_c = paper_c != p
        block_rows_c = np.where(keep_block_c)[0]
        S_block_c = fit(Xc[keep_block_c])
        n_u = int(uni[paper == p].sum())

        pool_papers = [q for q in papers if q != p and qbin[q] == qbin[p]]
        if len(pool_papers) < 5:
            pool_papers = [q for q in papers if q != p
                           and abs(qbin[q] - qbin[p]) <= 1]
        pool_rows = np.where(np.isin(paper_c, pool_papers))[0]
        if len(pool_rows) < n_u:
            pool_rows = np.where(paper_c != p)[0]

        base = SEED + __import__("zlib").crc32(("pc2" + p).encode()) % 100000
        per_draw = {k: [] for k in diffs}
        for dr in range(DRAWS):
            rng = np.random.default_rng(base + 7919 * dr)
            order = rng.permutation(pool_rows)
            cap = max(1, int(np.ceil(0.5 * n_u)))
            counts = Counter()
            chosen = []
            for j in order:
                s = paper_c[j]
                if counts[s] < cap:
                    chosen.append(int(j))
                    counts[s] += 1
                    if len(chosen) == n_u:
                        break
            if len(chosen) < n_u:
                used = set(chosen)
                for j in order:
                    if int(j) not in used:
                        chosen.append(int(j))
                        if len(chosen) == n_u:
                            break
            drop_c = np.asarray(chosen, int)
            keep_match_c = np.ones(len(Xc), bool)
            keep_match_c[drop_c] = False
            match_rows_c = np.where(keep_match_c)[0]
            S_match_c = fit(Xc[keep_match_c])
            common_c = keep_block_c & keep_match_c
            cc_idx = np.where(common_c)[0]
            pb = np.searchsorted(block_rows_c, cc_idx)
            pm = np.searchsorted(match_rows_c, cc_idx)

            ref = S_full_c[cc_idx]
            fb = class_flips(ref, S_block_c[pb])
            fm = class_flips(ref, S_match_c[pm])
            for k, i in (("pc1", 0), ("pc2", 1), ("joint", 2)):
                per_draw[k].append(fb[i] - fm[i])

        for k in diffs:
            diffs[k][p] = float(np.median(per_draw[k]))

    out = {}
    for k, v in diffs.items():
        vals = np.asarray(list(v.values()), float)
        boots = []
        rng = np.random.default_rng(SEED)
        for _ in range(10000):
            boots.append(np.median(vals[rng.integers(0, len(vals), len(vals))]))
        out[k] = {
            "median_diff": float(np.median(vals)),
            "ci_lo": float(np.quantile(boots, 0.025)),
            "ci_hi": float(np.quantile(boots, 0.975)),
            "pct_positive": 100.0 * float(np.mean(vals > 0)),
            "pct_negative": 100.0 * float(np.mean(vals < 0)),
            "pct_zero": 100.0 * float(np.mean(vals == 0)),
            "wilcoxon_p": float(stats.wilcoxon(vals).pvalue),
            "n": int(len(vals)),
        }
    with open(os.path.join(OUT, "pc2_density_check.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
