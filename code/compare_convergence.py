#!/usr/bin/env python3
"""Compare 100- and 500-draw fixed-evaluation outputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIXED = ROOT / "results" / "unit_revision_fixed"
BASE = FIXED / "common_contrast.json"
EXTENDED = FIXED / "convergence_500.json"


def main() -> int:
    base = json.loads(BASE.read_text())
    extended = json.loads(EXTENDED.read_text())
    rows = []
    for design in ("A", "B", "C", "Bstudy", "Bblock"):
        papers = sorted(set(base["per_paper"][design]) & set(extended["per_paper"][design]))
        delta = np.array([
            extended["per_paper"][design][p] - base["per_paper"][design][p]
            for p in papers
        ])
        rows.append({
            "quantity": design,
            "n": len(papers),
            "median_absolute_shift": float(np.median(np.abs(delta))),
            "max_absolute_shift": float(np.max(np.abs(delta))),
            "median_signed_shift": float(np.median(delta)),
            "base_aggregate_median": base["designs"][design]["median"],
            "extended_aggregate_median": extended["designs"][design]["median"],
        })
    for contrast in ("ABstudy", "ABblock", "AC"):
        papers = sorted(set(base["per_paper"][contrast]) & set(extended["per_paper"][contrast]))
        delta = np.array([
            extended["per_paper"][contrast][p] - base["per_paper"][contrast][p]
            for p in papers
        ])
        rows.append({
            "quantity": contrast,
            "n": len(papers),
            "median_absolute_shift": float(np.median(np.abs(delta))),
            "max_absolute_shift": float(np.max(np.abs(delta))),
            "median_signed_shift": float(np.median(delta)),
            "base_aggregate_median": base["contrasts"][contrast]["median"],
            "extended_aggregate_median": extended["contrasts"][contrast]["median"],
        })

    prefix_checks = {}
    for design in ("A", "B", "C"):
        papers = sorted(base["per_paper_control_drifts"][design])
        exact = all(
            np.allclose(
                base["per_paper_control_drifts"][design][p],
                extended["per_paper_control_drifts"][design][p][:100],
                rtol=0,
                atol=0,
            )
            for p in papers
        )
        prefix_checks[design] = exact

    out = {
        "base_draws": 100,
        "extended_draws": 500,
        "prefix_100_draws_exact": prefix_checks,
        "exhaustive_designs_identical": {
            design: all(
                base["per_paper"][design][p] == extended["per_paper"][design][p]
                for p in base["per_paper"][design]
            )
            for design in ("Bstudy", "Bblock")
        },
        "shifts": rows,
    }
    with (FIXED / "convergence_100_vs_500.json").open("w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    with (FIXED / "convergence_100_vs_500.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
