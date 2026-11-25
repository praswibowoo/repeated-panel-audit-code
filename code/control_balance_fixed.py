#!/usr/bin/env python3
"""Balance summaries for the fixed-evaluation controls."""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import data_dir, load_curated, unique_mask  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "unit_revision_fixed", "control_balance.json")


def main() -> None:
    X, rho, paper = load_curated()
    papers = sorted(set(paper))
    uni = unique_mask(X, paper)
    Xc, pc = X[uni], paper[uni]

    config_rows = []
    config_size = []
    for j, p in enumerate(pc):
        rr = np.where((paper == p) & np.all(X == Xc[j], axis=1))[0]
        config_rows.append(rr)
        config_size.append(len(rr))

    cov = pd.read_csv(os.path.join(data_dir(), "coverage_matrix.csv"))[["paper", "row"]]
    types = pd.read_csv(os.path.join(data_dir(), "coverage_matrix_types.csv"))
    water = cov.merge(
        types[["paper", "row", "water_only"]], on=["paper", "row"], how="left"
    )["water_only"].to_numpy(bool)

    pattern_papers = {}
    for j in range(len(Xc)):
        pattern_papers.setdefault(tuple(Xc[j].astype(int)), set()).add(pc[j])

    rows = []
    for p in papers:
        n_p = int(np.sum(paper == p))
        donors = [j for j in range(len(Xc)) if pc[j] != p and config_size[j] == n_p]
        if not donors:
            continue
        focal = [j for j in range(len(Xc)) if pc[j] == p]
        donor_density, donor_water, donor_recurrence, donor_hamming = [], [], [], []
        for j in donors:
            rr = config_rows[j]
            donor_density.append(float(rho[rr].mean()))
            donor_water.append(float(water[rr].mean()))
            donor_recurrence.append(len(pattern_papers[tuple(Xc[j].astype(int))]) > 1)
            donor_hamming.append(float(np.sum(Xc[j] != Xc[focal[0]])))
        rows.append({
            "paper": p,
            "n_rows": n_p,
            "n_configs": len(focal),
            "focal_density": float(rho[paper == p].mean()),
            "donor_density_mean": float(np.mean(donor_density)),
            "donor_water_mean": float(np.mean(donor_water)),
            "focal_water": float(water[paper == p].mean()),
            "focal_recurrence": len(pattern_papers[tuple(Xc[focal[0]].astype(int))]) > 1,
            "donor_recurrence_mean": float(np.mean(donor_recurrence)),
            "donor_hamming_mean": float(np.mean(donor_hamming)),
        })

    df = pd.DataFrame(rows)
    single = df[df.n_configs == 1]
    pooled_sd = np.sqrt((single.focal_density.var(ddof=1) + single.donor_density_mean.var(ddof=1)) / 2)
    smd = float((single.donor_density_mean.mean() - single.focal_density.mean()) / pooled_sd)

    fixed = json.load(open(os.path.join(ROOT, "results", "unit_revision_fixed", "common_contrast.json")))
    meta = fixed["meta"]
    missing = [p for p, m in meta.items() if m["n_configs"] == 1 and m["exact_block_donors"] == 0]

    out = {
        "bblock_single_eligible": {
            "n": int(len(single)),
            "focal_density_mean": float(single.focal_density.mean()),
            "donor_density_mean": float(single.donor_density_mean.mean()),
            "density_standardized_mean_difference": smd,
            "focal_recurrence_fraction": float(single.focal_recurrence.mean()),
            "donor_recurrence_fraction": float(single.donor_recurrence_mean.mean()),
            "focal_water_fraction_mean": float(single.focal_water.mean()),
            "donor_water_fraction_mean": float(single.donor_water_mean.mean()),
            "donor_hamming_mean": float(single.donor_hamming_mean.mean()),
        },
        "bblock_missing_single": [
            {
                "paper": p,
                "rows": int(meta[p]["n_rows"]),
                "A": float(fixed["per_paper"]["A"][p]),
                "C": float(fixed["per_paper"]["C"][p]),
                "AC": float(fixed["per_paper"]["AC"][p]),
            }
            for p in sorted(missing, key=lambda q: -meta[q]["n_rows"])
        ],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps(out, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
