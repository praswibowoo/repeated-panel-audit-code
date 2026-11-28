#!/usr/bin/env python3
"""Render rounded fixed-evaluation values for manuscript checks."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXED = ROOT / "results" / "unit_revision_fixed" / "common_contrast.json"
PCOA = ROOT / "results" / "unit_revision_fixed" / "pcoa_contrast.json"
RMS = ROOT / "results" / "unit_revision_fixed" / "rms_sensitivity.json"
FIXED3D = ROOT / "results" / "unit_revision_fixed" / "fixed3d_contrast.json"
SIM = ROOT / "results" / "post_audit" / "simulation_fixed.json"


def pair(x: dict) -> str:
    return f"{x['median']:.2f} ({x['ci_lo']:.2f}--{x['ci_hi']:.2f})"


def parts(x: dict, prefix: str) -> dict[str, str]:
    if x.get("median") is None:
        return {prefix: "NA", prefix + "_LO": "NA", prefix + "_HI": "NA"}
    return {
        prefix: f"{x['median']:.2f}",
        prefix + "_LO": f"{x['ci_lo']:.2f}",
        prefix + "_HI": f"{x['ci_hi']:.2f}",
    }


def rep_parts(x: dict, prefix: str) -> dict[str, str]:
    return {
        prefix: f"{x['median']:.3f}",
        prefix + "_LO": f"{x['q025']:.3f}",
        prefix + "_HI": f"{x['q975']:.3f}",
    }


def main() -> None:
    d = json.loads(FIXED.read_text())
    vals: dict[str, str] = {}
    vals["PRIMARY_PAPERS"] = str(d["design"]["studies"])
    vals["PRIMARY_ROWS"] = str(d["design"]["rows"])
    vals["PRIMARY_CONFIGURATIONS"] = str(d["design"]["configurations"])
    vals["ACTIVE_PARAMETERS"] = str(d["design"]["n_active_parameters"])
    vals["SINGLE_CONFIG_N"] = str(d["subgroups"]["single"]["n"])
    vals["MULTI_CONFIG_BACKGROUND_N"] = str(d["subgroups"]["multi"]["n"])
    vals["BSTUDY_ELIGIBLE_N"] = str(d["availability"]["single_has_whole_study_donor"]["n"])
    vals["BBLOCK_ELIGIBLE_N"] = str(d["availability"]["single_has_exact_donor"]["n"])
    vals["ESTIMATOR"] = d["estimator"]["name"]
    vals.update(parts(d["designs"]["A"], "A_ALL"))
    vals.update(parts(d["designs"]["Bblock"], "BLOCK_ALL"))
    vals.update(parts(d["designs"]["C"], "C_ALL"))
    vals.update(parts(d["contrasts"]["ABblock"], "AB_ALL"))
    vals.update(parts(d["contrasts"]["ABstudy"], "ABSTUDY_ALL"))
    if "sensitivities" in d and "ABstudy_log" in d["sensitivities"]:
        vals.update(parts(d["sensitivities"]["ABstudy_log"], "ABSTUDY_LOG"))
    vals.update(parts(d["contrasts"]["AC"], "AC_ALL"))
    vals["AB_ALL_POS"] = f"{100*d['contrasts']['ABblock']['frac_positive']:.0f}"
    vals["AC_POS"] = f"{100*d['contrasts']['AC']['frac_positive']:.0f}"

    s = d["subgroups"]["single"]
    vals.update(parts(s["designs"]["A"], "A_SINGLE"))
    vals.update(parts(s["designs"]["C"], "C_SINGLE"))
    vals.update(parts(s["designs"]["Bblock"], "BLOCK_SINGLE"))
    vals.update(parts(s["designs"]["Bstudy"], "STUDY_SINGLE"))
    vals.update(parts(s["contrasts"]["ABblock"], "AB_SINGLE"))
    vals.update(parts(s["contrasts"]["ABstudy"], "ABSTUDY_SINGLE"))
    vals.update(parts(s["contrasts"]["AC"], "AC_SINGLE"))
    vals["AB_SINGLE_POS"] = f"{100*s['contrasts']['ABblock']['frac_positive']:.0f}"
    vals["ABSTUDY_SINGLE_POS"] = f"{100*s['contrasts']['ABstudy']['frac_positive']:.0f}"
    vals["AC_SINGLE_POS"] = f"{100*s['contrasts']['AC']['frac_positive']:.0f}"

    m = d["subgroups"]["multi"]
    vals.update(parts(m["designs"]["A"], "A_MULTI"))
    vals.update(parts(m["designs"]["Bblock"], "BLOCK_MULTI"))
    vals.update(parts(m["designs"]["C"], "C_MULTI"))
    vals.update(parts(m["contrasts"]["ABblock"], "AB_MULTI"))
    vals.update(parts(m["contrasts"]["AC"], "AC_MULTI"))

    if "availability" in d:
        vals["ALL_HAS_DONOR_N"] = str(d["availability"]["all_has_exact_donor"]["n"])
        vals["SINGLE_HAS_DONOR_N"] = str(d["availability"]["single_has_exact_donor"]["n"])
        vals["SINGLE_NO_DONOR_N"] = str(d["availability"]["single_no_exact_donor"]["n"])
        vals["SINGLE_STUDY_DONOR_N"] = str(d["availability"]["single_has_whole_study_donor"]["n"])
        vals["SINGLE_NO_STUDY_DONOR_N"] = str(d["availability"]["single_no_whole_study_donor"]["n"])
        vals.update(parts(d["availability"]["single_has_whole_study_donor"]["designs"]["A"], "A_SINGLE_STUDY_DONOR"))
        vals.update(parts(d["availability"]["single_has_whole_study_donor"]["contrasts"]["ABstudy"], "ABSTUDY_SINGLE_DONOR"))
        vals.update(parts(d["availability"]["all_has_exact_donor"]["designs"]["A"], "A_HAS_DONOR"))
        vals.update(parts(d["availability"]["single_has_exact_donor"]["designs"]["A"], "A_SINGLE_HAS_DONOR"))

    for label, stratum_key in (
        ("2_5", "2-5"), ("6_10", "6-10"), ("11_PLUS", ">=11")
    ):
        stratum = d["block_size_strata"][stratum_key]
        x = stratum["contrasts"]["ABstudy"]
        prefix = f"ABSTUDY_BLOCK_{label}"
        vals.update(parts(x, prefix))
        vals[prefix + "_N"] = str(x["n"])
        vals[prefix + "_SINGLE_TOTAL_N"] = str(stratum["n_single_configuration"])
        block = stratum["contrasts"]["ABblock"]
        vals.update(parts(block, f"ABBLOCK_BLOCK_{label}"))
        vals[f"ABBLOCK_BLOCK_{label}_N"] = str(block["n"])

    if PCOA.exists():
        p = json.loads(PCOA.read_text())
        vals.update(parts(p["designs"]["A"], "PCOA_A"))
        vals.update(parts(p["designs"]["Bblock"], "PCOA_B"))
        vals.update(parts(p["designs"]["Bstudy"], "PCOA_STUDY"))
        vals.update(parts(p["designs"]["C"], "PCOA_C"))
        vals.update(parts(p["contrasts"]["ABblock"], "PCOA_AB"))
        vals.update(parts(p["contrasts"]["ABstudy"], "PCOA_ABSTUDY"))
        vals.update(parts(p["contrasts"]["AC"], "PCOA_AC"))
        vals.update(parts(p["subgroups"]["single"]["contrasts"]["ABblock"], "PCOA_AB_SINGLE"))
        vals.update(parts(p["subgroups"]["single"]["contrasts"]["AC"], "PCOA_AC_SINGLE"))
        vals.update(parts(p["subgroups"]["multi"]["contrasts"]["ABblock"], "PCOA_AB_MULTI"))
        vals.update(parts(p["subgroups"]["multi"]["contrasts"]["AC"], "PCOA_AC_MULTI"))

    if RMS.exists():
        r = json.loads(RMS.read_text())
        vals.update(parts(r["designs"]["A"], "RMS_A"))
        vals.update(parts(r["designs"]["Bblock"], "RMS_B"))
        vals.update(parts(r["designs"]["Bstudy"], "RMS_STUDY"))
        vals.update(parts(r["designs"]["C"], "RMS_C"))
        vals.update(parts(r["contrasts"]["ABblock"], "RMS_AB"))
        vals.update(parts(r["contrasts"]["ABstudy"], "RMS_ABSTUDY"))
        vals.update(parts(r["contrasts"]["AC"], "RMS_AC"))
        vals.update(parts(r["subgroups"]["single"]["contrasts"]["ABblock"], "RMS_AB_SINGLE"))
        vals.update(parts(r["subgroups"]["multi"]["contrasts"]["ABblock"], "RMS_AB_MULTI"))

    if SIM.exists():
        sim = json.loads(SIM.read_text())
        vals.update(rep_parts(sim["H0_repeated"]["full_ratio"], "SIM_H0_A"))
        vals.update(rep_parts(sim["H0_repeated"]["whole_configuration_ratio"], "SIM_H0_B"))
        vals.update(rep_parts(sim["H0_repeated"]["collapsed_ratio"], "SIM_H0_C"))
        vals.update(rep_parts(sim["IID_rows"]["full_ratio"], "SIM_IID_A"))
        vals.update(rep_parts(sim["IID_rows"]["collapsed_ratio"], "SIM_IID_C"))
        vals.update(rep_parts(sim["H1_planted"]["full_ratio"], "SIM_H1_A"))
        vals.update(rep_parts(sim["H1_planted"]["collapsed_ratio"], "SIM_H1_C"))
        vals.update(rep_parts(sim["H1_planted"]["planted_collapsed_ratio"], "SIM_PLANTED"))

    if FIXED3D.exists():
        f3 = json.loads(FIXED3D.read_text())
        vals.update(parts(f3["designs"]["A"], "F3_A"))
        vals.update(parts(f3["designs"]["Bstudy"], "F3_STUDY"))
        vals.update(parts(f3["designs"]["Bblock"], "F3_BLOCK"))
        vals.update(parts(f3["contrasts"]["ABstudy"], "F3_ABSTUDY"))
        vals.update(parts(f3["contrasts"]["ABblock"], "F3_ABBLOCK"))
        vals.update(parts(f3["subgroups"]["single"]["contrasts"]["ABstudy"], "F3_ABSTUDY_SINGLE"))

    out = ROOT / "results" / "unit_revision_fixed" / "manuscript_values.json"
    out.write_text(json.dumps(vals, indent=2) + "\n")
    print(f"wrote {out}")
    for k in sorted(vals):
        print(f"{k}={vals[k]}")


if __name__ == "__main__":
    main()
