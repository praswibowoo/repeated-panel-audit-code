#!/usr/bin/env python3
"""Primary figure for the fixed-evaluation whole-study control audit.

(a) Per-study row-count ratio versus exact-size whole single-configuration
donor-study ratio for the 92 eligible single-configuration focal studies.
(b) Paired A-Bstudy differences overall and by focal row-count stratum, with
all study points shown.
"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON = os.path.join(ROOT, "results", "unit_revision_fixed", "common_contrast.json")
OUT = os.path.join(ROOT, "figures", "fig_paired_contrast.pdf")


def main() -> None:
    d = json.load(open(COMMON, encoding="utf-8"))
    eligible = sorted(d["per_paper"]["Bstudy"])

    A = np.array([d["per_paper"]["A"][p] for p in eligible])
    B = np.array([d["per_paper"]["Bstudy"][p] for p in eligible])
    D = np.array([d["per_paper"]["ABstudy"][p] for p in eligible])
    rows = np.array([d["meta"][p]["n_rows"] for p in eligible], float)

    plt.rcParams.update({
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "pdf.fonttype": 42,
    })
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.0), constrained_layout=True)

    ax = axes[0]
    row_norm = Normalize(vmin=float(rows.min()), vmax=float(rows.max()))
    sc = ax.scatter(
        B, A, s=8 + 3 * rows, c=rows,
        cmap="viridis", norm=row_norm, edgecolor="white", linewidth=0.3,
        alpha=0.9, zorder=3,
    )
    lim = [0, max(A.max(), B.max()) * 1.04]
    ax.plot(lim, lim, ls="--", lw=0.8, color="0.45", zorder=1)
    ax.axvline(np.median(B), ls=":", lw=0.8, color="0.25", zorder=2)
    ax.axhline(np.median(A), ls=":", lw=0.8, color="0.25", zorder=2)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Whole-study donor ratio $R_s^{\\mathrm{Bstudy}}$")
    ax.set_ylabel("Row-count ratio $R_s^{\\mathrm{A}}$")
    ax.set_title("(a) Full-fit study-unit control")
    ax.text(
        0.03, 0.96, f"above 1:1 line: {100 * np.mean(A > B):.0f}%",
        transform=ax.transAxes, va="top", ha="left", fontsize=8,
    )
    cbar = fig.colorbar(sc, ax=ax, fraction=0.045, pad=0.02)
    cbar.set_label("Rows per study", fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    ax = axes[1]
    groups = [
        np.ones(len(eligible), dtype=bool),
        (rows >= 2) & (rows <= 5),
        (rows >= 6) & (rows <= 10),
        rows >= 11,
    ]
    data = [D[mask] for mask in groups]
    labels = [
        f"All\n(n={len(eligible)})",
        f"2--5 rows\n(n={len(data[1])})",
        f"6--10 rows\n(n={len(data[2])})",
        f"$\\geq$11 rows\n(n={len(data[3])})",
    ]
    colors = ["#4c72b0", "#55a868", "#c44e52", "#8172b3"]
    rng = np.random.default_rng(20261126)
    bp = ax.boxplot(
        data, tick_labels=labels, patch_artist=True, widths=0.6,
        showfliers=False, medianprops={"color": "black", "lw": 1},
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
    for i, values in enumerate(data, start=1):
        jitter = rng.uniform(-0.12, 0.12, len(values))
        ax.scatter(
            i + jitter, values, s=10, color=colors[i - 1],
            alpha=0.45, edgecolor="none", zorder=3,
        )
    ax.axhline(0.0, ls="--", lw=0.8, color="0.35")
    ax.set_ylabel("Paired difference $D_s^{\\mathrm{ABstudy}}$")
    ax.set_title("(b) Row count minus whole-study donor")
    low = min(float(x.min()) for x in data)
    high = max(float(x.max()) for x in data)
    pad = 0.08 * (high - low if high > low else 1.0)
    ax.set_ylim(low - pad, high + pad)

    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
