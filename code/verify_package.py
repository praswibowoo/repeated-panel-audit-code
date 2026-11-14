#!/usr/bin/env python3
"""verify_package.py — self-check for the P2 check package.

Verifies that every deposited data file is present, that the three coverage
matrices agree with each other and with the manuscript's panel structure, and
that the committed summaries carry the values reported in the paper.

This is not a substitute for rerunning the analyses; it is the fast check a
reader can run before doing so.

Run: python3 code/verify_package.py
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import data_dir  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = data_dir()
POST = os.path.join(ROOT, "results", "post_audit")

FILES = [
    "coverage_matrix.csv",
    "coverage_matrix_all_paper.csv",
    "coverage_matrix_full_extraction.csv",
    "corpus_manifest.csv",
    "baseline_block.csv",
    "baseline_matched.csv",
    "collapsed_block.csv",
    "collapsed_matched.csv",
    "weighted_matched_block.csv",
    "weighted_matched_matched.csv",
    "composition_matched_control.csv",
    "core.json",
    "core_checks.json",
    "extra.json",
    "water.json",
    "pcoa_summary.json",
    "pcoa_collapsed_summary.json",
    "coverage_3d_model.csv",
    "coverage_3d_models.csv",
    "p0_composition_percentile.csv",
    "presence_misclassification_summary.csv",
    "preprocessing_block_factor.csv",
    "composition_matched_summary.csv",
    "composition_vs_density.csv",
    "composition_exact_subset.csv",
    "coverage_volume_bins.csv",
    "row_count_sensitivity.csv",
    "review_findings.json",
    "coverage_events.csv",
    "calibration_direction.csv",
    "calibration_size_direction.csv",
    "sim_calibration_summary.csv",
    "sim_calibration_extended_summary.csv",
    "study_level_model.json",
]

POST_FILES = [
    "all_paper_audit.json",
    "panel_decomposition.json",
    "panel_decomposition_draws.json",
    "pc2_density_check.json",
    "simulation_validation.json",
    "multiconfig_sensitivity.json",
    "tail_audit.json",
    "tail_decomposition.csv",
    "three_d_models.json",
    "coherence_control.json",
    "tail_null.json",
    "table_checks.json",
]

EXCLUDED = ("B175", "B111", "B095", "B182", "B239")

failures: list[str] = []


def check(name: str, got, want, tol=5e-3) -> None:
    ok = (abs(float(got) - float(want)) <= tol) if isinstance(want, (int, float)) else (got == want)
    if not ok:
        failures.append(f"{name}: got {got!r}, expected {want!r}")


def load_json(path: str) -> dict:
    with open(os.path.join(DATA, path), encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    missing = [f for f in FILES if not os.path.exists(os.path.join(DATA, f))]
    missing += [f"results/post_audit/{f}" for f in POST_FILES
                if not os.path.exists(os.path.join(POST, f))]
    if missing:
        print("MISSING:", ", ".join(missing))
        return 1

    params = lambda df: [c for c in df.columns if c not in ("paper", "row", "rho")]

    # --- corpus and panel structure -------------------------------------
    cur = pd.read_csv(os.path.join(DATA, "coverage_matrix.csv"))
    allp = pd.read_csv(os.path.join(DATA, "coverage_matrix_all_paper.csv"))
    full = pd.read_csv(os.path.join(DATA, "coverage_matrix_full_extraction.csv"))
    man = pd.read_csv(os.path.join(DATA, "corpus_manifest.csv"))

    check("curated rows", len(cur), 716)
    check("curated papers", cur.paper.nunique(), 117)
    check("all-paper rows", len(allp), 730)
    check("all-paper papers", allp.paper.nunique(), 122)
    check("full rows", len(full), 764)
    check("full papers", full.paper.nunique(), 122)
    check("manifest papers", len(man), 138)
    check("manifest data rows", int(man["data_rows"].sum()), 764)

    p = params(cur)
    check("coverage columns", len(p), 44)
    check("empty columns", sum(1 for c in p if cur[c].sum() == 0), 2)

    patterns = cur[p].astype(int).astype(str).agg("".join, axis=1)
    per_paper = cur.assign(pat=patterns).groupby("paper")["pat"].nunique()
    check("unique configurations", int(per_paper.sum()), 151)
    check("single-config papers", int((per_paper == 1).sum()), 97)
    check("duplicate rows", len(cur) - int(per_paper.sum()), 565)

    rebuilt = allp[~allp.paper.isin(EXCLUDED)].reset_index(drop=True)
    check("curated = all-paper minus five papers (papers)",
          list(rebuilt.paper) == list(cur.paper), True)
    check("curated = all-paper minus five papers (cells)",
          bool((rebuilt[p].values == cur[p].values).all()), True)

    # --- primary audit from the event tables ----------------------------
    bb = pd.read_csv(os.path.join(DATA, "baseline_block.csv"))
    bm = pd.read_csv(os.path.join(DATA, "baseline_matched.csv"))
    cb = pd.read_csv(os.path.join(DATA, "collapsed_block.csv"))
    cm = pd.read_csv(os.path.join(DATA, "collapsed_matched.csv"))

    def ratio(block, matched):
        b = block[block.arm == "block"].set_index("paper")["med_drift"]
        m = matched[matched.arm == "matched"].groupby("paper")["med_drift"].median()
        return (b / m).dropna()

    rf = ratio(bb, bm)
    rc = ratio(cb, cm)
    match_full = bm[bm.arm == "matched"].groupby("paper")["med_drift"].median()
    check("full paired ratio", rf.median(), 1.3628, 1e-3)
    check("collapsed paired ratio", rc.median(), 1.0390, 1e-3)
    check("ratio of per-study medians",
          bb[bb.arm == "block"]["med_drift"].median()
          / match_full.median(), 1.143, 5e-3)
    check("PC1 class change", bb[bb.arm == "block"]["pc1_flip"].median(), 3.37, 5e-3)
    check("PC2 class change", bb[bb.arm == "block"]["pc2_flip"].median(), 2.10, 5e-3)

    # --- committed summaries --------------------------------------------
    core = load_json("core.json")
    check("core full ratio", core["baseline"]["audit"]["baseline_ratio"]["median"], 1.3628, 1e-3)
    check("core block factor", core["baseline"]["model"]["block"]["factor"], 1.3868, 1e-3)
    check("core collapsed ratio", core["collapsed"]["audit"]["collapsed_ratio"]["median"], 1.0390, 1e-3)
    check("core collapsed block factor", core["collapsed"]["model"]["block"]["factor"], 1.0122, 1e-3)
    tn = json.load(open(os.path.join(POST, "tail_null.json"), encoding="utf-8"))
    check("tail-null single q95", tn["groups"]["single"]["q95"], 4.28, 6e-3)
    check("tail-null multi q95", tn["groups"]["multi"]["q95"], 2.71, 6e-3)
    check("tail-null single observed >2", tn["groups"]["single"]["observed"]["2"]["n"], 16, 0)
    check("tail-null multi observed >4", tn["groups"]["multi"]["observed"]["4"]["n"], 3, 0)
    tc = json.load(open(os.path.join(POST, "table_checks.json"), encoding="utf-8"))
    check("exact block factor", tc["exact_subset_block_factor"]["median"], 0.879, 2e-3)
    check("top-25 difference", tc["pc1_top25"]["median_diff"], -0.0056, 2e-3)
    check("pc2 row-level mean", tc["pc2_rowlevel_collapsed"]["mean"], 1.44, 1e-2)

    cc = load_json("core_checks.json")
    check("exact subset n", cc["exact"]["n"], 21)
    check("exact volume", cc["exact"]["volume_all"]["median"], 0.8056, 1e-3)
    check("coarsened control", cc["coarsened"]["all"]["median"], 1.1380, 1e-3)

    dec = json.load(open(os.path.join(POST, "panel_decomposition.json"), encoding="utf-8"))
    d = dec["decomposition"]
    check("decomposition full/all", d["full_all"]["median"], 1.36, 5e-3)
    check("decomposition full/unique", d["full_unique"]["median"], 1.3291, 1e-3)
    check("decomposition weighted/unique", d["weighted_unique"]["median"], 1.5863, 1e-3)
    check("decomposition collapsed", d["collapsed_unique"]["median"], 0.9714, 1e-3)
    check("density-matched", dec["density_matched_collapsed"]["median"], 0.9575, 1e-3)

    pc2 = json.load(open(os.path.join(POST, "pc2_density_check.json"), encoding="utf-8"))
    check("PC2 density-matched p", pc2["pc2"]["wilcoxon_p"], 0.0141, 1e-3)
    check("PC2 positive share", pc2["pc2"]["pct_positive"], 42.74, 5e-2)

    sim = json.load(open(os.path.join(POST, "simulation_validation.json"), encoding="utf-8"))
    check("H0 full", sim["H0_repeated_panels_only"]["full_ratio"]["median"], 1.5813, 1e-3)
    check("H0 collapsed", sim["H0_repeated_panels_only"]["collapsed_ratio"]["median"], 0.9955, 1e-3)
    check("H1 planted", sim["H1_planted_study"]["planted_collapsed_ratio"]["median"], 4.6591, 1e-3)
    check("H1 above 2", sim["H1_planted_study"]["planted_above_2x_pct"], 90.0)

    mc = json.load(open(os.path.join(POST, "multiconfig_sensitivity.json"), encoding="utf-8"))
    check("flip 1%", mc["flip_0.01"]["H0_repeated_panels_only"]["collapsed_ratio"]["median"], 0.9589, 1e-3)
    check("flip 5%", mc["flip_0.05"]["H0_repeated_panels_only"]["collapsed_ratio"]["median"], 1.3375, 1e-3)

    ap = json.load(open(os.path.join(POST, "all_paper_audit.json"), encoding="utf-8"))
    check("all-paper ratio", ap["paired_ratio"]["median"], 1.3428, 1e-3)
    check("all-paper CI low", ap["paired_ratio"]["ci_lo"], 1.1096, 5e-3)
    check("all-paper CI high", ap["paired_ratio"]["ci_hi"], 1.5957, 5e-3)

    water = load_json("water.json")
    check("water full", water["full"]["water_full_ratio"]["median"], 1.3820, 1e-3)
    check("water collapsed", water["collapsed"]["water_collapsed_ratio"]["median"], 1.0388, 1e-3)

    pcoa = load_json("pcoa_summary.json")
    pcoa_c = load_json("pcoa_collapsed_summary.json")
    check("PCoA full", pcoa["audit"]["pcoa_ratio"]["median"], 1.3874, 1e-3)
    check("PCoA collapsed", pcoa_c["audit"]["pcoa_ratio"]["median"], 0.9940, 1e-3)

    pct = pd.read_csv(os.path.join(DATA, "p0_composition_percentile.csv")).iloc[0]
    check("block percentile", float(pct["median_percentile"]), 76.0, 1e-6)
    check("above 95th", float(pct["above95_pct"]), 29.06, 5e-2)
    check("below 5th", float(pct["below5_pct"]), 5.98, 5e-2)

    # --- tail / coherence checks ---------------------------------------
    tail = json.load(open(os.path.join(POST, "tail_audit.json"), encoding="utf-8"))
    ps = tail["panel_structure"]
    check("tail papers", ps["n_papers"], 117)
    check("tail rows", ps["n_rows"], 716)
    check("tail unique configs", ps["n_unique_configs"], 151)
    check("tail single-config", ps["n_single_config_papers"], 97)
    check("tail multi-config", ps["n_multi_config_papers"], 20)

    ham = tail["hamming"]
    check("hamming pairs", ham["pairs"], 54)
    check("hamming one-bit", ham["distribution"]["1"], 16)
    check("hamming two-bit", ham["distribution"]["2"], 11)
    check("hamming three-bit", ham["distribution"]["3"], 5)
    check("hamming le 3", ham["pairs_le_3"], 32)

    check("collapsed >2", tail["tail"]["collapsed"][">2.0"]["n"], 19)
    check("two-level collapsed median", tail["two_level_bootstrap"]["collapsed"]["median"], 1.0340, 1e-3)
    draws = json.load(open(os.path.join(POST, "panel_decomposition_draws.json"), encoding="utf-8"))
    check("draws collapsed papers", len(draws["collapsed_unique"]), 117)
    check("draws density papers", len(draws["density_matched"]), 117)
    check("two-level common-evaluation median",
          tail["two_level_bootstrap"]["common_evaluation"]["median"], 0.9857, 1e-3)
    check("two-level density median",
          tail["two_level_bootstrap"]["density_matched"]["median"], 0.9604, 1e-3)
    check("density-matched >2", tail["tail"]["density_matched"][">2.0"]["n"], 14)
    check("multi-config median", tail["subgroup"]["multi_config"]["median"], 1.0973, 1e-3)
    check("one-config median", tail["subgroup"]["one_config"]["median"], 1.0265, 1e-3)
    check("exact mean rows", tail["exact_subset"]["exact"]["mean_rows"], 4.5238, 1e-3)
    check("other mean rows", tail["exact_subset"]["other"]["mean_rows"], 6.4688, 1e-3)
    check("exact mean duplicate fraction",
          tail["exact_subset"]["exact"]["mean_duplicate_fraction"], 0.5773, 1e-3)
    check("other mean duplicate fraction",
          tail["exact_subset"]["other"]["mean_duplicate_fraction"], 0.7384, 1e-3)
    check("block percentile q25", tail["block_percentile"]["q25"], 30.0, 0.5)
    check("block percentile q75", tail["block_percentile"]["q75"], 98.0, 0.5)
    check("study-level curated", tail["study_level_model"]["curated"]["median"],
          1.4160, 1e-3)
    check("study-level all-paper", tail["study_level_model"]["all_paper"]["median"],
          1.4209, 1e-3)

    coh = json.load(open(os.path.join(POST, "coherence_control.json"), encoding="utf-8"))
    check("coherence n", coh["n_papers"], 20)
    check("coherence median", coh["median"], 1.0103, 1e-3)
    check("coherence B063", coh["per_paper"]["B063"]["coherence_ratio"], 8.9499, 1e-3)
    check("coherence B166", coh["per_paper"]["B166"]["coherence_ratio"], 7.2859, 1e-3)
    check("coherence B201", coh["per_paper"]["B201"]["coherence_ratio"], 3.3990, 1e-3)

    three = pd.read_csv(os.path.join(DATA, "coverage_3d_models.csv"))
    check("3-D curated", float(three.loc[three.set == "curated", "block_at_mean_volume"].iloc[0]),
          1.1669, 1e-3)
    check("3-D all-paper", float(three.loc[three.set == "all_paper", "block_at_mean_volume"].iloc[0]),
          1.1866, 1e-3)
    check("3-D include-standard",
          float(three.loc[three.set == "include_standard", "block_at_mean_volume"].iloc[0]),
          1.0999, 1e-3)

    # The fresh core-revision output must agree with the deposited copy.
    fresh_path = os.path.join(ROOT, "results", "core_revision", "core_checks.json")
    if os.path.exists(fresh_path):
        fresh = json.load(open(fresh_path, encoding="utf-8"))
        check("fresh core exact n", fresh["exact"]["n"], cc["exact"]["n"])
        check("fresh core exact volume", fresh["exact"]["volume_all"]["median"],
              cc["exact"]["volume_all"]["median"], 1e-9)
        check("fresh core coarsened", fresh["coarsened"]["all"]["median"],
              cc["coarsened"]["all"]["median"], 1e-9)

    if failures:
        print("FAIL — %d mismatch(es):" % len(failures))
        for f in failures:
            print("  -", f)
        return 1

    print(f"PASS — {len(FILES) + len(POST_FILES)} files present; "
          "panel structure, event-table ratios, and all summaries match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
