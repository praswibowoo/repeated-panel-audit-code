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
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
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
    "water_only_check.json",
    "summary_excluded_check.json",
    "coverage_matrix_types.csv",
    "pcoa_summary.json",
    "pcoa_collapsed_summary.json",
    "coverage_3d_model.csv",
    "coverage_3d_models.csv",
    "p0_composition_percentile.csv",
    "presence_misclassification_summary.csv",
    "presence_misclassification_upper.csv",
    "presence_misclassification_direction.json",
    "common_evaluation_set.json",
    "weighted_matched_summary.json",
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
    "flagged_studies.csv",
    "balance_diagnostics.csv",
    "dimension_sweep.csv",
    "flagged_study_cis.csv",
    "two_level_delta.json",
    "balance_complete_partial.json",
    "cell_level_sample.csv",
    "cell_level_coded.csv",
    "cell_level_triage.csv",
    "duplicate_pair_audit_frame.csv",
    "duplicate_pair_source_review.csv",
    "duplicate_pair_source_review_summary.json",
    "prior_human_cell_corrections.csv",
    "prior_human_pair_evidence.csv",
    "prior_human_cell_corrections_status.csv",
    "duplicate_pair_adjudication_manifest.json",
    "HUMAN_ADJUDICATION_README.md",
    "duplicate_pair_human_adjudication_primary_blind.csv",
    "duplicate_pair_human_adjudication_primary_simple.csv",
    "duplicate_pair_human_adjudication_second_blind.csv",
    "duplicate_pair_human_adjudication_coordinator_key.csv",
    "duplicate_pair_human_adjudication_coder.xlsx",
    "duplicate_pair_human_adjudication_primary_only.xlsx",
    "duplicate_pair_human_adjudication_primary_simple.xlsx",
    "duplicate_pair_human_adjudication_second_only.xlsx",
    "duplicate_pair_human_adjudication_coordinator.xlsx",
    "duplicate_pair_human_adjudication_primary_completed_partial_2026-11-26.csv",
    "duplicate_pair_human_adjudication_partial_results_2026-11-26.csv",
    "duplicate_pair_human_adjudication_partial_summary_2026-11-26.json",
    "duplicate_pair_human_adjudication_partial_review_flags_2026-11-26.csv",
    "duplicate_pair_human_adjudication_partial_coordinator_notes_2026-11-26.md",
    "duplicate_pair_human_adjudication_primary_completed_2026-11-27.csv",
    "duplicate_pair_human_adjudication_results_2026-11-27.csv",
    "duplicate_pair_human_adjudication_summary_2026-11-27.json",
    "duplicate_pair_human_adjudication_processing_report_2026-11-27.csv",
    "duplicate_pair_human_adjudication_review_flags_2026-11-27.csv",
    "duplicate_pair_human_adjudication_coordinator_notes_2026-11-27.md",
    "duplicate_pair_coordinator_resolution_template_2026-11-27.csv",
]

POST_FILES = [
    "all_paper_audit.json",
    "panel_decomposition.json",
    "panel_decomposition_draws.json",
    "pc2_density_check.json",
    "simulation_validation.json",
    "simulation_fixed.json",
    "simulation_iid_null.json",
    "multiconfig_sensitivity.json",
    "multiconfig_h1.json",
    "tail_audit.json",
    "tail_decomposition.csv",
    "three_d_models.json",
    "coherence_control.json",
    "tail_null.json",
    "table_checks.json",
    "pc2_density_check.json",
    "procrustes_holdout.json",
    "dimension_sweep.json",
    "leave_flagged_out.json",
    "flagged_study_cis.json",
    "tail_global_test.json",
    "tail_global_null.npz",
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
    fixed_dir = os.path.join(ROOT, "results", "unit_revision_fixed")
    fixed_path = os.path.join(fixed_dir, "common_contrast.json")
    for name in (
        "common_contrast.json",
        "fixed3d_contrast.json",
        "control_balance.json",
        "pcoa_contrast.json",
        "rms_sensitivity.json",
        "manuscript_values.json",
        "sensitivity_no_B208.json",
        "sensitivity_no_unsure_substitutes.json",
    ):
        if not os.path.exists(os.path.join(fixed_dir, name)):
            missing.append(f"results/unit_revision_fixed/{name}")
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
    ver = os.path.join(DATA, "verification")
    if not os.path.isdir(ver):
        ver = os.path.join(ROOT, "docs", "verification")
    pc = json.load(open(os.path.join(ver, "stageA_postcorrection_summary.json"), encoding="utf-8"))
    check("re-audit papers", pc["papers"], 25, 0)
    check("re-audit claims", pc["claims"], 30, 0)
    check("re-audit passed", pc["passed"], 30, 0)

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

    water = load_json("water_only_check.json")
    check("water full", water["full"]["median"], 1.4127, 1e-3)
    check("water collapsed", water["collapsed"]["median"], 0.9268, 1e-3)

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

    pc2 = json.load(open(os.path.join(POST, "pc2_density_check.json"), encoding="utf-8"))
    check("PC2 density mean", pc2["pc2"]["mean_diff"], 0.9857, 1e-3)
    check("PC2 density mean CI lo", pc2["pc2"]["mean_ci_lo"], 0.4207, 1e-3)
    check("PC2 density mean CI hi", pc2["pc2"]["mean_ci_hi"], 1.6489, 1e-3)

    ho = json.load(open(os.path.join(POST, "procrustes_holdout.json"), encoding="utf-8"))
    check("held-out full", ho["full"]["median"], 1.3279, 1e-3)
    check("held-out collapsed", ho["collapsed"]["median"], 1.0367, 1e-3)

    ds = json.load(open(os.path.join(POST, "dimension_sweep.json"), encoding="utf-8"))
    check("dimension 2-D full", ds["full"]["2"]["median"], 1.363, 1e-3)
    check("dimension 3-D full", ds["full"]["3"]["median"], 1.090, 1e-3)
    check("dimension 4-D full", ds["full"]["4"]["median"], 1.310, 1e-3)
    check("dimension 5-D full", ds["full"]["5"]["median"], 1.279, 1e-3)
    check("dimension 2-D collapsed", ds["collapsed"]["2"]["median"], 1.039, 1e-3)

    leave = json.load(open(os.path.join(POST, "leave_flagged_out.json"), encoding="utf-8"))
    check("leave-six-out full", leave["full"]["median"], 1.3121, 1e-3)
    check("leave-six-out collapsed", leave["collapsed"]["median"], 1.0715, 1e-3)

    fcis = json.load(open(os.path.join(POST, "flagged_study_cis.json"), encoding="utf-8"))
    check("flagged B063 collapsed", fcis["rows"][0]["collapsed_ratio"], 6.566, 1e-3)
    check("flagged B102 collapsed", fcis["rows"][-1]["collapsed_ratio"], 4.144, 1e-3)

    tg = json.load(open(os.path.join(POST, "tail_global_test.json"), encoding="utf-8"))
    check("tail global permutations", tg["n_permutations"], 200)
    tn = np.load(os.path.join(POST, "tail_global_null.npz"))
    check("tail null shape", tn["null"].shape, (200, 117))

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

    # Fixed-evaluation primary audit.
    fixed = json.load(open(fixed_path, encoding="utf-8"))
    check("fixed A", fixed["designs"]["A"]["median"], 1.3291, 1e-3)
    check("fixed C", fixed["designs"]["C"]["median"], 0.9819, 1e-3)
    check("fixed AC", fixed["contrasts"]["AC"]["median"], 0.2926, 1e-3)
    check("fixed ABblock", fixed["contrasts"]["ABblock"]["median"], 0.2637, 1e-3)
    check("fixed ABstudy", fixed["contrasts"]["ABstudy"]["median"], 0.3523, 2e-3)
    check("fixed Bstudy", fixed["designs"]["Bstudy"]["median"], 0.9405, 2e-3)
    check("fixed Bstudy donor enumeration", all(
        m["bstudy_donors_enumerated"] == m["whole_study_donors"]
        for m in fixed["meta"].values()
    ), True)
    check("fixed Bstudy draw invariance", all(
        len(set(values)) == 1
        for values in fixed["per_paper_draws"]["Bstudy"].values()
    ), True)
    check("fixed single ABstudy", fixed["subgroups"]["single"]["contrasts"]["ABstudy"]["median"], 0.3523, 2e-3)
    check("fixed single A", fixed["subgroups"]["single"]["designs"]["A"]["median"], 1.3657, 1e-3)
    check("fixed single C", fixed["subgroups"]["single"]["designs"]["C"]["median"], 0.9607, 1e-3)
    check("fixed single Bblock", fixed["subgroups"]["single"]["designs"]["Bblock"]["median"], 0.9744, 1e-3)
    check("fixed multi H", fixed["subgroups"]["multi"]["designs"]["H"]["median"], 0.9477, 1e-3)
    check("legacy B max donor configs", fixed["legacy_B_matching"]["donor_config_count_max"], 12)
    if "availability" in fixed:
        check("single exact donors", fixed["availability"]["single_has_exact_donor"]["n"], 92)
        check("single missing donors", fixed["availability"]["single_no_exact_donor"]["n"], 5)
        check("single whole-study donors", fixed["availability"]["single_has_whole_study_donor"]["n"], 91)
        check("single missing whole-study donors", fixed["availability"]["single_no_whole_study_donor"]["n"], 6)
    pcoa = json.load(open(os.path.join(fixed_dir, "pcoa_contrast.json"), encoding="utf-8"))
    check("fixed PCoA A", pcoa["designs"]["A"]["median"], 1.3362, 1e-3)
    check("fixed PCoA Bstudy", pcoa["designs"]["Bstudy"]["median"], 0.9813, 1e-3)
    check("fixed PCoA ABstudy", pcoa["contrasts"]["ABstudy"]["median"], 0.3863, 2e-3)
    check("fixed PCoA ABblock", pcoa["contrasts"]["ABblock"]["median"], 0.2946, 1e-3)
    rms = json.load(open(os.path.join(fixed_dir, "rms_sensitivity.json"), encoding="utf-8"))
    check("fixed RMS ABblock", rms["contrasts"]["ABblock"]["median"], 0.2930, 1e-3)
    check("fixed RMS single ABblock", rms["subgroups"]["single"]["contrasts"]["ABblock"]["median"], 0.3229, 1e-3)
    check("fixed RMS ABstudy", rms["contrasts"]["ABstudy"]["median"], 0.4707, 2e-3)
    check("fixed RMS single ABstudy", rms["subgroups"]["single"]["contrasts"]["ABstudy"]["median"], 0.4707, 2e-3)
    f3 = json.load(open(os.path.join(fixed_dir, "fixed3d_contrast.json"), encoding="utf-8"))
    check("fixed 3-D ABstudy", f3["contrasts"]["ABstudy"]["median"], 0.1425, 2e-3)
    check("fixed 3-D Bstudy", f3["designs"]["Bstudy"]["median"], 0.9940, 2e-3)
    check("fixed 3-D single ABstudy", f3["subgroups"]["single"]["contrasts"]["ABstudy"]["median"], 0.1425, 2e-3)
    sim_fixed = json.load(open(os.path.join(POST, "simulation_fixed.json"), encoding="utf-8"))
    check("fixed synthetic corpora", sim_fixed["design"]["replicates"], 100)
    check("fixed synthetic H0 full", sim_fixed["H0_repeated"]["full_ratio"]["median"], 1.5565, 1e-3)
    check("fixed synthetic H0 Bblock", sim_fixed["H0_repeated"]["whole_configuration_ratio"]["median"], 0.9930, 1e-3)
    check("fixed synthetic IID full", sim_fixed["IID_rows"]["full_ratio"]["median"], 0.9894, 1e-3)
    ex1 = json.load(open(os.path.join(fixed_dir, "sensitivity_no_B208.json"), encoding="utf-8"))
    ex2 = json.load(open(os.path.join(fixed_dir, "sensitivity_no_unsure_substitutes.json"), encoding="utf-8"))
    check("no-B208 ABstudy", ex1["contrasts"]["ABstudy"]["median"], 0.3578, 2e-3)
    check("no-unsure ABstudy", ex2["contrasts"]["ABstudy"]["median"], 0.1509, 2e-3)
    iid = json.load(open(os.path.join(POST, "simulation_iid_null.json"), encoding="utf-8"))
    check("IID row-count median", iid["row_count_ratio"]["median"], 1.0008, 1e-3)

    dup = load_json("duplicate_pair_source_review_summary.json")
    dup_frame = pd.read_csv(os.path.join(DATA, "duplicate_pair_audit_frame.csv"))
    check("duplicate human fields blank", bool(dup_frame.human_relation.isna().all() and dup_frame["match"].isna().all()), True)
    check("duplicate source-review pairs", dup["total_pairs"], 83, 0)
    check("duplicate source-review same", dup["counts_by_relation"]["same"], 53, 0)
    check("duplicate source-review false-distinct", len(dup["matrix_comparison"]["false_distinct_pairs"]), 16, 0)
    check("duplicate prior-human conflicts", len(dup["matrix_comparison"]["prior_human_evidence_conflict_pairs"]), 8, 0)
    adjud = json.load(open(os.path.join(DATA, "duplicate_pair_adjudication_manifest.json"), encoding="utf-8"))
    check("adjudication all pairs", adjud["counts"]["all_pairs"], 83, 0)
    check("adjudication primary pairs", adjud["counts"]["primary_required"], 56, 0)
    check("adjudication second-coder pairs", adjud["counts"]["second_coder_required"], 62, 0)
    check("adjudication prior-human conflicts", adjud["counts"]["prior_evidence_conflicts_with_ai_same"], 8, 0)
    partial = json.load(open(os.path.join(DATA, "duplicate_pair_human_adjudication_partial_summary_2026-11-26.json"), encoding="utf-8"))
    check("partial primary completed", partial["primary_rows"], 31, 0)
    check("partial primary pending", partial["pending_primary_pairs"], 25, 0)
    check("partial prior-human conflicts", partial["prior_evidence_conflicts"], 5, 0)
    current = json.load(open(os.path.join(DATA, "duplicate_pair_human_adjudication_summary_2026-11-27.json"), encoding="utf-8"))
    check("current primary completed", current["primary_rows"], 56, 0)
    check("current primary pending", current["pending_primary_pairs"], 0, 0)
    check("current pending pair", current["pending_primary_pair_ids"], [])
    check("current completed same", current["completed_relation_counts"]["same"], 34, 0)
    check("current completed different", current["completed_relation_counts"]["different"], 7, 0)
    check("current completed undecidable", current["completed_relation_counts"]["undecidable"], 15, 0)
    check("current evidence missing", current["evidence_missing"], 0, 0)
    check("current metadata missing", current["coder_metadata_missing"], 0, 0)
    check("current correction warnings", current["correction_format_warnings"], 17, 0)
    check("current matrix disagreements", current["matrix_disagreements"], 16, 0)
    check("current AI disagreements", current["ai_disagreements"], 19, 0)
    check("current strict import ready", current["ready_for_strict_import"], True)
    submission = pd.read_csv(os.path.join(DATA, "duplicate_pair_human_adjudication_primary_completed_2026-11-27.csv")).fillna("")
    check("current submission rows", len(submission), 56, 0)
    check("current submission blank relations", submission.loc[submission.relation.eq(""), "pair_id"].tolist(), [])
    check("current submission coder", sorted(submission.coder.unique()), ["A"])
    check("current submission date", sorted(submission.date.unique()), ["2026-11-27"])
    processing = pd.read_csv(os.path.join(DATA, "duplicate_pair_human_adjudication_processing_report_2026-11-27.csv")).fillna("")
    check("current processing rows", len(processing), 56, 0)
    check("current processing finalized", bool(processing.finalized.astype(str).str.lower().eq("true").any()), False)
    check("current processing incomplete relation", int(processing.processing_status.eq("incomplete_relation").sum()), 0, 0)
    check("current processing incomplete submission", int(processing.processing_status.eq("incomplete_submission").sum()), 0, 0)
    check("current processing coordinator review", int(processing.processing_status.eq("coordinator_review").sum()), 39, 0)
    check("current processing provisional no flag", int(processing.processing_status.eq("provisional_no_flag").sum()), 17, 0)
    for blind_name in ("duplicate_pair_human_adjudication_primary_blind.csv",
                       "duplicate_pair_human_adjudication_second_blind.csv"):
        blind = pd.read_csv(os.path.join(DATA, blind_name))
        forbidden = {"audit_stratum", "matrix_hamming", "reviewer_relation", "priority_tier", "priority_reason"}
        check(f"{blind_name} blind columns", bool(forbidden.isdisjoint(blind.columns)), True)
    simple = pd.read_csv(os.path.join(DATA, "duplicate_pair_human_adjudication_primary_simple.csv"))
    check("simple primary columns", list(simple.columns) == [
        "pair_id", "scenario_a", "scenario_b", "relation", "evidence", "correction", "coder", "date"
    ], True)
    check("simple primary rows", len(simple), 56, 0)
    for coder_name, expected_sheets in (
        ("duplicate_pair_human_adjudication_coder.xlsx", {"Instructions", "Primary", "Second"}),
        ("duplicate_pair_human_adjudication_primary_only.xlsx", {"Instructions", "Primary"}),
        ("duplicate_pair_human_adjudication_primary_simple.xlsx", {"Instructions", "Primary"}),
        ("duplicate_pair_human_adjudication_second_only.xlsx", {"Instructions", "Second"}),
    ):
        coder_book = os.path.join(DATA, coder_name)
        with zipfile.ZipFile(coder_book) as zf:
            payload = b" ".join(zf.read(name) for name in zf.namelist() if name.endswith(".xml"))
            workbook_xml = ET.fromstring(zf.read("xl/workbook.xml"))
            sheet_names = {node.attrib["name"] for node in workbook_xml.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet")}
            check(f"{coder_name} sheets", sheet_names == expected_sheets, True)
        for token in (b"matrix_identical", b"matrix_distinct", b"reviewer_relation", b"priority_tier", b"conflicts_with_ai_same"):
            check(f"{coder_name} excludes {token.decode()}", token not in payload, True)

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
