#!/usr/bin/env python3
"""Export flat block-stratum and donor-pool tables from fixed audit outputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
FIXED = ROOT / "results" / "unit_revision_fixed"
SOURCES = [
    ("primary_2d_pca", FIXED / "common_contrast.json"),
    ("primary_3d_pca", FIXED / "fixed3d_contrast.json"),
    ("primary_jaccard_pcoa", FIXED / "pcoa_contrast.json"),
    ("primary_rms", FIXED / "rms_sensitivity.json"),
    ("full_curated_2d_pca", FIXED / "sensitivity_full_curated.json"),
]


def fmt(x):
    return "" if x is None else x


def main() -> int:
    rows = []
    donor_rows = []
    for method, path in SOURCES:
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for label, stratum in data["block_size_strata"].items():
            ab = stratum["contrasts"]["ABstudy"]
            abb = stratum["contrasts"]["ABblock"]
            pool = data["donor_pool_size_distributions"][label]
            row = {
                "method": method,
                "corpus": data["design"]["corpus"],
                "stratum": label,
                "n_single_total": stratum["n_single_configuration"],
                "n_bstudy_eligible": stratum["n_bstudy_eligible"],
                "n_bblock_eligible": stratum["n_bblock_eligible"],
                "A_median": fmt(stratum["designs"]["A"]["median"]),
                "A_median_shared_bstudy_set": fmt(median([
                    data["per_paper"]["A"][paper]
                    for paper in data["per_paper"]["Bstudy"]
                    if paper in stratum["papers"]
                ])),
                "Bstudy_median": fmt(stratum["designs"]["Bstudy"]["median"]),
                "Bblock_median": fmt(stratum["designs"]["Bblock"]["median"]),
                "ABstudy_median": fmt(ab["median"]),
                "ABstudy_ci_lo": fmt(ab["ci_lo"]),
                "ABstudy_ci_hi": fmt(ab["ci_hi"]),
                "ABstudy_iqr_lo": fmt(ab["iqr_lo"]),
                "ABstudy_iqr_hi": fmt(ab["iqr_hi"]),
                "ABstudy_positive_fraction": fmt(ab["frac_positive"]),
                "ABblock_median": fmt(abb["median"]),
                "ABblock_ci_lo": fmt(abb["ci_lo"]),
                "ABblock_ci_hi": fmt(abb["ci_hi"]),
                "ABblock_positive_fraction": fmt(abb["frac_positive"]),
            }
            for design in ("Bstudy", "Bblock"):
                summary = pool[design]
                for key in ("min", "q1", "median", "q3", "max", "count_le_2", "count_le_5"):
                    row[f"{design}_pool_{key}"] = fmt(summary[key])
            rows.append(row)

        if method == "primary_2d_pca":
            for paper, meta in sorted(data["meta"].items()):
                donor_rows.append({
                    "paper": paper,
                    "n_rows": meta["n_rows"],
                    "n_configurations": meta["n_configs"],
                    "bstudy_donors": meta["whole_study_donors"],
                    "bblock_donors": meta["exact_block_donors"],
                    "bblock_only_donors": meta["bblock_only_donor_count"],
                    "bstudy_subset_of_bblock": meta["bstudy_subset_of_bblock"],
                })

    fields = list(rows[0]) if rows else []
    with (FIXED / "strata_sensitivity.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with (FIXED / "donor_pool_by_focal.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(donor_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(donor_rows)
    print(f"wrote {len(rows)} stratum rows and {len(donor_rows)} focal donor rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
