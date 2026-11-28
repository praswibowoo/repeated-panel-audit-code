#!/usr/bin/env python3
"""Regenerate the PRISMA-style corpus provenance figure.

The figure is illustrative, not a systematic-review flow.  It mirror the
numbers in SI Table S1 and uses "human x automated" for the two-coder screen.
Writes ``figures/figS1_prisma_flow.pdf``.
"""
from __future__ import annotations

import os
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "figures", "figS1_prisma_flow.pdf")

MAIN_EDGE = "#1f2d3d"
SIDE_EDGE = "#b03a2e"
FINAL_EDGE = "#2e7d32"
PANEL = "#f4f5f6"
SIDE_FILL = "#fdecec"
FINAL_FILL = "#e8f5e9"


def box(ax, x, y, w, h, text, edge, fill="white", fontsize=7.6, bold=False):
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.006,rounding_size=0.012",
        linewidth=1.2, edgecolor=edge, facecolor=fill, zorder=2,
    )
    ax.add_patch(patch)
    ax.text(
        x, y, text, ha="center", va="center", fontsize=fontsize,
        color="#1a1a1a", zorder=3,
        fontweight="bold" if bold else "normal",
        linespacing=1.25,
    )
    return patch


def arrow(ax, x1, y1, x2, y2, color="#333333", lw=1.1):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9,
        linewidth=lw, color=color, shrinkA=2, shrinkB=2, zorder=1,
    ))


def main() -> None:
    fig, ax = plt.subplots(figsize=(9.2, 12.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Backing panel for the main flow.
    ax.add_patch(FancyBboxPatch(
        (0.18, 0.025), 0.47, 0.935,
        boxstyle="round,pad=0.0,rounding_size=0.01",
        linewidth=0, facecolor=PANEL, zorder=0,
    ))

    # Title.
    ax.text(
        0.5, 0.995,
        "Corpus provenance funnel — mangrove water-quality literature\n(OpenAlex search batch)",
        ha="center", va="top", fontsize=10.8, fontweight="bold", color="#111111",
        linespacing=1.2,
    )

    # Stage labels.
    for label, y in (("IDENTIFICATION", 0.86), ("SCREENING", 0.55), ("INCLUDED", 0.17)):
        ax.text(0.105, y, label, rotation=90, ha="center", va="center",
                fontsize=8.2, color="#555555", fontweight="bold")

    mx, mw, mh = 0.415, 0.38, 0.068
    sx, sw, sh = 0.805, 0.26, 0.072
    ys = [0.910, 0.795, 0.680, 0.565, 0.450, 0.320, 0.190, 0.070]

    # Main boxes.
    main_text = [
        "Records identified from databases\nOpenAlex Boolean queries · 10 families\n(Q1–Q9 + Q3b)\nn = 11,612",
        "Records after duplicate removal\nn = 8,931",
        "Records after eligibility filters\npeer-reviewed · mangrove-linked\nn = 6,093",
        "Pre-screen frame (term-scoring tiers)\nn = 375",
        "Records screened\nhuman × automated, blind · κ = 0.529\nn = 237",
        "Reports sought for retrieval\nn = 148: 134 include + 14 unsure",
        "Qualified corpus\nn = 135 qualified papers",
        "Studies in the synthesis — analyzed corpus\n122 papers; 119 full texts + 3 substitutes",
    ]
    for y, text in zip(ys, main_text):
        fill = FINAL_FILL if text.startswith("Studies in the synthesis") else "white"
        edge = FINAL_EDGE if text.startswith("Studies in the synthesis") else MAIN_EDGE
        box(ax, mx, y, mw, mh, text, edge, fill=fill, fontsize=7.6,
            bold=text.startswith("Studies in the synthesis"))

    # Vertical arrows.
    for i in range(len(ys) - 1):
        arrow(ax, mx, ys[i] - mh / 2, mx, ys[i + 1] + mh / 2)

    # Side boxes.
    side = [
        (ys[0], "Duplicate records removed\nn = 2,681"),
        (ys[1], "Records removed before screening\nn = 2,838; preprints/reviews →\nchaining file · non-mangrove ·\ntitle dupes"),
        (ys[2], "Records removed at pre-screen\nn = 5,718;\n37-param term scoring"),
        (ys[3], "Screening pilots consumed\n138 of 375 frame titles"),
        (ys[4], "Records excluded\nn = 89"),
        (ys[5] + 0.040, "Metadata validation\n117 DOI confirmed · 25 DOI-less\n6 manual checks · 3 year fixes"),
        (ys[5] - 0.040, "Records removed at intake (n = 13)\noff-topic 8 · not processed 5"),
        (ys[6], "Reports not retrieved (n = 16)\nILL-pending; 119/135 PDFs (88%)"),
    ]
    for y, text in side:
        box(ax, sx, y, sw, sh * 0.88, text, SIDE_EDGE, fill=SIDE_FILL, fontsize=6.8)
        arrow(ax, mx + mw / 2, y, sx - sw / 2, y, color=SIDE_EDGE, lw=1.0)

    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.04)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
