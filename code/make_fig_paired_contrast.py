#!/usr/bin/env python3
"""Two-panel primary figure for the unit-of-deletion revision.

(a) Per-study row-count ratio A against the collapsed ratio C, with the 1:1
    line, point size by rows per study, and marginal medians.
(b) Distribution of the per-study A-B contrast, isolating the control unit at
    a fixed full fit.
"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON = os.path.join(ROOT, "results", "unit_revision", "common_contrast.json")
OUT = os.path.join(ROOT, "figures", "fig_paired_contrast.pdf")
os.makedirs(os.path.dirname(OUT), exist_ok=True)


def main():
    d = json.load(open(COMMON))
    papers = sorted(d["per_paper"]["A"])
    A = np.array([d["per_paper"]["A"][p] for p in papers])
    C = np.array([d["per_paper"]["C"][p] for p in papers])
    AB = np.array([d["per_paper"]["AB"][p] for p in papers])
    n_p = np.array([d["meta"][p]["n_p"] for p in papers], float)

    plt.rcParams.update({
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "pdf.fonttype": 42,
    })

    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.9), constrained_layout=True)

    ax = axes[0]
    scatter = ax.scatter(
        C, A, s=8 + 3 * n_p, c=n_p, cmap="viridis",
        edgecolor="white", linewidth=0.3, alpha=0.9, zorder=3,
    )
    lim = [0, max(A.max(), C.max()) * 1.04]
    ax.plot(lim, lim, ls="--", lw=0.8, color="0.45", zorder=1)
    ax.axvline(np.median(C), ls=":", lw=0.8, color="0.25", zorder=2)
    ax.axhline(np.median(A), ls=":", lw=0.8, color="0.25", zorder=2)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Collapsed ratio $R_s^{\\mathrm{C}}$")
    ax.set_ylabel("Row-count ratio $R_s^{\\mathrm{A}}$")
    ax.set_title("(a) Per-study ratios")
    frac_above = np.mean(A > C)
    ax.text(
        0.03, 0.96,
        f"above 1:1 line: {100*frac_above:.0f}%",
        transform=ax.transAxes, va="top", ha="left", fontsize=8,
    )
    cbar = fig.colorbar(scatter, ax=ax, fraction=0.045, pad=0.02)
    cbar.set_label("Rows per study", fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    ax = axes[1]
    bins = np.linspace(min(AB.min(), -0.2), AB.max(), 24)
    ax.hist(AB, bins=bins, color="0.55", edgecolor="white", linewidth=0.4)
    ax.axvline(0, color="0.2", lw=0.8)
    ax.axvline(np.median(AB), color="C3", lw=1.0, ls="-")
    ax.set_xlabel("$R_s^{\\mathrm{A}} - R_s^{\\mathrm{B}}$")
    ax.set_ylabel("Studies")
    ax.set_title("(b) Control-unit contrast")
    ax.text(
        0.97, 0.96,
        f"median {np.median(AB):.2f}\n{100*np.mean(AB>0):.0f}% positive",
        transform=ax.transAxes, va="top", ha="right", fontsize=8,
    )
    ax.set_xlim(bins[0], bins[-1])

    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
