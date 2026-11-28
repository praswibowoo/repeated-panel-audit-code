#!/usr/bin/env python3
"""Primary figure for the fixed-evaluation whole-paper control audit."""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
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
    donors = np.array([d["meta"][p]["whole_study_donors"] for p in eligible], float)

    plt.rcParams.update({
        "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 10,
        "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "pdf.fonttype": 42,
    })
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.2), constrained_layout=True)

    ax = axes[0]
    donor_norm = Normalize(vmin=float(donors.min()), vmax=float(donors.max()))
    sc = ax.scatter(
        B, A, s=8 + 2.5 * rows, c=donors, cmap="viridis", norm=donor_norm,
        edgecolor="white", linewidth=0.3, alpha=0.9, zorder=3,
    )
    lo = max(min(A.min(), B.min()) * 0.8, 1e-3)
    hi = max(A.max(), B.max()) * 1.25
    ax.plot([lo, hi], [lo, hi], ls="--", lw=0.8, color="0.45", zorder=1)
    ax.axvline(np.median(B), ls=":", lw=0.8, color="0.25", zorder=2)
    ax.axhline(np.median(A), ls=":", lw=0.8, color="0.25", zorder=2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Whole-paper donor ratio $R_s^{\\mathrm{Bstudy}}$")
    ax.set_ylabel("Row-count ratio $R_s^{\\mathrm{A}}$")
    ax.set_title("(a) Full-fit paper-unit control")
    ax.text(0.03, 0.96, f"above 1:1 line: {100*np.mean(A>B):.0f}%",
            transform=ax.transAxes, va="top", ha="left", fontsize=8)
    cbar = fig.colorbar(sc, ax=ax, fraction=0.045, pad=0.02)
    cbar.set_label("Bstudy donor count", fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    ax = axes[1]
    strata = [
        ("2–5", (rows >= 2) & (rows <= 5), "#55a868"),
        ("6–10", (rows >= 6) & (rows <= 10), "#c44e52"),
        ("≥11", rows >= 11, "#8172b3"),
    ]
    rng = np.random.default_rng(20261128)
    for label, mask, color in strata:
        x = rows[mask] + rng.uniform(-0.12, 0.12, mask.sum())
        ax.scatter(x, D[mask], s=14, color=color, alpha=0.55,
                   edgecolor="none", label=label, zorder=3)
        med = float(np.median(D[mask]))
        ax.hlines(med, rows[mask].min() - 0.25, rows[mask].max() + 0.25,
                  color=color, lw=2.0, zorder=4)
    ax.axhline(0.0, ls="--", lw=0.8, color="0.35")
    ax.set_yscale("symlog", linthresh=0.5, linscale=1.0)
    ax.set_xlabel("Focal rows per paper $n_s$")
    ax.set_ylabel("Paired difference $D_s^{\\mathrm{ABstudy}}$")
    ax.set_title("(b) Continuous block-size view")
    ax.set_xticks(sorted(set(rows.astype(int))))
    ax.legend(title="Rows", frameon=False, loc="upper left", ncol=3)
    low, high = float(D.min()), float(D.max())
    pad = 0.08 * (high - low if high > low else 1.0)
    ax.set_ylim(low - pad, high + pad)

    fig.savefig(OUT, bbox_inches="tight", metadata={
        "Title": "Fixed-evaluation whole-paper donor contrast",
        "Subject": f"Primary corpus; {len(eligible)} eligible single-configuration papers; ratio of medians",
    })
    print("wrote", OUT)


if __name__ == "__main__":
    main()
