#!/usr/bin/env python3
"""Primary figure for the fixed-evaluation control-geometry audit.

(a) Per-study row-count ratio versus full-fit whole-configuration donor ratio
    for studies with an exact-size donor.
(b) Distribution of the paired A-Bblock difference by configuration stratum.
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
    eligible = sorted(d["per_paper"]["Bblock"])
    single = [p for p in eligible if d["meta"][p]["n_configs"] == 1]
    multi = [p for p in eligible if d["meta"][p]["n_configs"] > 1]

    A = np.array([d["per_paper"]["A"][p] for p in eligible])
    B = np.array([d["per_paper"]["Bblock"][p] for p in eligible])
    rows = np.array([d["meta"][p]["n_rows"] for p in eligible], float)
    is_single = np.array([d["meta"][p]["n_configs"] == 1 for p in eligible])

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
    for mask, marker, label in [
        (is_single, "o", "Single configuration (n=92)"),
        (~is_single, "s", "Multiple configurations (n=20)"),
    ]:
        sc = ax.scatter(
            B[mask], A[mask], s=8 + 3 * rows[mask], c=rows[mask],
            cmap="viridis", norm=row_norm, marker=marker, edgecolor="white", linewidth=0.3,
            alpha=0.9, zorder=3, label=label,
        )
    lim = [0, max(A.max(), B.max()) * 1.04]
    ax.plot(lim, lim, ls="--", lw=0.8, color="0.45", zorder=1)
    ax.axvline(np.median(B), ls=":", lw=0.8, color="0.25", zorder=2)
    ax.axhline(np.median(A), ls=":", lw=0.8, color="0.25", zorder=2)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Whole-configuration donor ratio $R_s^{\\mathrm{Bblock}}$")
    ax.set_ylabel("Row-count ratio $R_s^{\\mathrm{A}}$")
    ax.set_title("(a) Full-fit control geometry")
    frac_above = np.mean(A > B)
    ax.text(
        0.03, 0.96, f"above 1:1 line: {100 * frac_above:.0f}%",
        transform=ax.transAxes, va="top", ha="left", fontsize=8,
    )
    ax.legend(loc="lower right", frameon=False, fontsize=7)
    cbar = fig.colorbar(sc, ax=ax, fraction=0.045, pad=0.02)
    cbar.set_label("Rows per study", fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    ax = axes[1]
    groups = [eligible, single, multi]
    data = [
        np.array([d["per_paper"]["ABblock"][p] for p in ps])
        for ps in groups
    ]
    labels = ["All\n(n=112)", "Single\n(n=92)", "Multiple\n(n=20)"]
    colors = ["#4c72b0", "#55a868", "#c44e52"]
    bp = ax.boxplot(
        data, tick_labels=labels, patch_artist=True, widths=0.6,
        showfliers=False, medianprops={"color": "black", "lw": 1},
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)
    ax.axhline(0.0, ls="--", lw=0.8, color="0.35")
    ax.set_ylabel("Paired difference $D_s^{\\mathrm{ABblock}}$")
    ax.set_title("(b) Row count minus whole configuration")
    low = min(float(x.min()) for x in data)
    high = max(float(x.max()) for x in data)
    pad = 0.08 * (high - low if high > low else 1.0)
    ax.set_ylim(low - pad, high + pad)

    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
