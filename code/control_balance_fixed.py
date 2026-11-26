#!/usr/bin/env python3
"""Balance summaries for the fixed-evaluation controls."""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import data_dir, load_curated, unique_mask  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "unit_revision_fixed", "control_balance.json")


def summarize_pool(df: pd.DataFrame, donor_col: str, focal_col: str) -> dict:
    pooled_sd = np.sqrt(
        (df[focal_col].var(ddof=1) + df[donor_col].var(ddof=1)) / 2
    )
    smd = float((df[donor_col].mean() - df[focal_col].mean()) / pooled_sd)
    gap = np.abs(df[donor_col] - df[focal_col])
    return {
        "n": int(len(df)),
        "focal_density_mean": float(df[focal_col].mean()),
        "donor_density_mean": float(df[donor_col].mean()),
        "density_standardized_mean_difference": smd,
        "density_gap_median_abs": float(gap.median()),
        "density_gap_q90_abs": float(gap.quantile(0.90)),
        "density_gap_frac_gt_0_05": float(np.mean(gap > 0.05)),
        "density_gap_frac_gt_0_10": float(np.mean(gap > 0.10)),
    }


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
    config_size = np.asarray(config_size)
    n_u = {p: int(np.sum(uni & (paper == p))) for p in papers}

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
        focal = [j for j in range(len(Xc)) if pc[j] == p]
        if len(focal) != 1:
            continue
        donors = [
            j for j in range(len(Xc))
            if pc[j] != p and config_size[j] == n_p
        ]
        if not donors:
            continue
        study_donors = [j for j in donors if n_u[pc[j]] == 1]
        focal_row = focal[0]
        rec = {
            "paper": p,
            "n_rows": n_p,
            "focal_density": float(rho[paper == p].mean()),
            "focal_water": float(water[paper == p].mean()),
            "focal_recurrence": len(pattern_papers[tuple(Xc[focal_row].astype(int))]) > 1,
            "bblock_donors": len(donors),
            "bblock_multi_donors": sum(n_u[pc[j]] > 1 for j in donors),
            "bstudy_donors": len(study_donors),
        }
        for label, pool in (("bblock", donors), ("bstudy", study_donors)):
            if not pool:
                rec[label + "_density_mean"] = np.nan
                rec[label + "_water_mean"] = np.nan
                rec[label + "_recurrence_mean"] = np.nan
                rec[label + "_hamming_mean"] = np.nan
                continue
            rec[label + "_density_mean"] = float(np.mean([rho[config_rows[j]].mean() for j in pool]))
            rec[label + "_water_mean"] = float(np.mean([water[config_rows[j]].mean() for j in pool]))
            rec[label + "_recurrence_mean"] = float(np.mean([
                len(pattern_papers[tuple(Xc[j].astype(int))]) > 1 for j in pool
            ]))
            rec[label + "_hamming_mean"] = float(np.mean([
                np.sum(Xc[j] != Xc[focal_row]) for j in pool
            ]))
        rows.append(rec)

    df = pd.DataFrame(rows)
    block = df.copy()
    study = df[df.bstudy_donors > 0].copy()
    fixed = json.load(open(os.path.join(ROOT, "results", "unit_revision_fixed", "common_contrast.json")))
    meta = fixed["meta"]
    block_missing = [p for p, m in meta.items() if m["n_configs"] == 1 and m["exact_block_donors"] == 0]
    study_missing = [p for p, m in meta.items() if m["n_configs"] == 1 and m["whole_study_donors"] == 0]

    out = {
        "bblock_single_eligible": {
            **summarize_pool(block, "bblock_density_mean", "focal_density"),
            "focal_recurrence_fraction": float(block.focal_recurrence.mean()),
            "donor_recurrence_fraction": float(block.bblock_recurrence_mean.mean()),
            "focal_water_fraction_mean": float(block.focal_water.mean()),
            "donor_water_fraction_mean": float(block.bblock_water_mean.mean()),
            "donor_hamming_mean": float(block.bblock_hamming_mean.mean()),
        },
        "bstudy_single_eligible": {
            **summarize_pool(study, "bstudy_density_mean", "focal_density"),
            "focal_recurrence_fraction": float(study.focal_recurrence.mean()),
            "donor_recurrence_fraction": float(study.bstudy_recurrence_mean.mean()),
            "focal_water_fraction_mean": float(study.focal_water.mean()),
            "donor_water_fraction_mean": float(study.bstudy_water_mean.mean()),
            "donor_hamming_mean": float(study.bstudy_hamming_mean.mean()),
        },
        "bblock_donor_composition": {
            "eligible": int(len(block)),
            "with_multi_configuration_donor": int(np.sum(block.bblock_multi_donors > 0)),
            "mean_multi_configuration_donor_fraction": float(np.mean(
                block.bblock_multi_donors / block.bblock_donors
            )),
            "with_whole_single_configuration_donor": int(np.sum(block.bstudy_donors > 0)),
            "without_whole_single_configuration_donor": [
                p for p in block.paper if int(block.loc[block.paper == p, "bstudy_donors"].iloc[0]) == 0
            ],
        },
        "bblock_missing_single": [
            {
                "paper": p,
                "rows": int(meta[p]["n_rows"]),
                "A": float(fixed["per_paper"]["A"][p]),
                "C": float(fixed["per_paper"]["C"][p]),
                "AC": float(fixed["per_paper"]["AC"][p]),
            }
            for p in sorted(block_missing, key=lambda q: -meta[q]["n_rows"])
        ],
        "bstudy_missing_single": [
            {
                "paper": p,
                "rows": int(meta[p]["n_rows"]),
                "bblock_donors": int(meta[p]["exact_block_donors"]),
                "A": float(fixed["per_paper"]["A"][p]),
                "Bblock": float(fixed["per_paper"]["Bblock"].get(p, 0.0)) if p in fixed["per_paper"]["Bblock"] else None,
                "C": float(fixed["per_paper"]["C"][p]),
                "AC": float(fixed["per_paper"]["AC"][p]),
            }
            for p in sorted(study_missing, key=lambda q: -meta[q]["n_rows"])
        ],
        "per_study_balance": df.astype(object).where(pd.notna(df), None).to_dict(orient="records"),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps({k: v for k, v in out.items() if k != "per_study_balance"}, indent=2))


if __name__ == "__main__":
    main()
