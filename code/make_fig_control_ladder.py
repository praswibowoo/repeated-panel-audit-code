#!/usr/bin/env python3
"""Control-ladder forest plot for the EES coverage audit.

Reads the deposited sharpening checks and draws the five control estimates
on one axis. Writes source/figures/fig_control_ladder.pdf.
"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "figures", "fig_control_ladder.pdf")


def find(name: str) -> str:
    for root in (
        os.path.join(ROOT, "data"),
        os.path.join(ROOT, "results", "post_audit"),
        os.path.join(ROOT, "manuscript", "ees", "reproducibility"),
    ):
        path = os.path.join(root, name)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(name)


s = json.load(open(find("sharpening_checks.json")))
p = json.load(open(find("panel_decomposition.json")))


def ci(d):
    return d["median"], d["ci_lo"], d["ci_hi"]


rows = [
    ("Row-count control, full fit", *ci(p["factorial"]["full_row"]), "#D55E00"),
    ("Volume-matched unique, full fit", *ci(s["volume_matched_unique"]["exact_volume_median"]), "#0072B2"),
    ("Unique-configuration, collapsed", *ci(p["factorial"]["collapsed_unique"]), "#0072B2"),
    ("Composition-prioritized, collapsed", *ci(s["composition_collapsed"]["median"]), "#009E73"),
    ("Exact-match subset", *ci(s["composition_collapsed"]["exact_subset"]), "#009E73"),
]

fig, ax = plt.subplots(figsize=(7.2, 3.4))
y = np.arange(len(rows))[::-1]
for yi, (label, med, lo, hi, color) in zip(y, rows):
    ax.errorbar(med, yi, xerr=[[med - lo], [hi - med]], fmt="o",
                color=color, ecolor=color, elinewidth=1.4, capsize=3,
                markersize=6)
    ax.text(hi + 0.015, yi, f"{med:.2f} ({lo:.2f}–{hi:.2f})",
            va="center", fontsize=8, color="#333333")

ax.axvline(1.0, color="#666666", linestyle="--", linewidth=1)
ax.set_yticks(y)
ax.set_yticklabels([r[0] for r in rows], fontsize=8.5)
ax.set_xlabel("Block / matched median drift ratio (95% CI)", fontsize=9)
ax.set_xlim(0.75, 1.65)
ax.set_ylim(-0.6, len(rows) - 0.4)
ax.tick_params(axis="x", labelsize=8)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
fig.tight_layout()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
