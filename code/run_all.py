#!/usr/bin/env python3
"""run_all.py — one command for the whole package.

Examples
--------
    python3 code/run_all.py                  # every analysis (~45 minutes)
    python3 code/run_all.py --quick          # fast check (~2 minutes)
    python3 code/run_all.py --only panel,pc2
    python3 code/run_all.py --list

Each analysis writes its summary under ``results/`` or the deposited reproducibility
folder. The last two steps run the manuscript and number checks and the package
self-check, so a green run means the committed values were reproduced.

The long steps are the synthetic validation (~6 min), the multi-configuration
sensitivity (~12 min, which runs the synthetic validation twice), the
multi-configuration stress test (~4 min), the upper-bound perturbation (~6 min),
the coherence control (~1 min), the three-set 3-D models (~7 min), and the tail
checks (~2 min).  ``--quick`` runs the synthetic validation with two replicates
and skips the multi-configuration, perturbation, coherence, 3-D, and tail steps,
so it does not overwrite their published summaries.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

STEPS: dict[str, tuple[str, str, str]] = {
    "types": ("build_matrix_types", "matrix-type map for the coverage rows", "~2 s"),
    "water": ("water_only_check", "water-only counts and audit", "~30 s"),
    "panel": ("panel_decomposition", "2x2 decomposition and density control", "~4 min"),
    "pc2": ("pc2_density_check", "PC2 density-matched class check", "~15 s"),
    "core": ("core_revision_checks", "coarsened control and exact-subset CIs", "~60 s"),
    "allpaper": ("all_paper_audit", "all-paper 730/122 audit", "~2 min"),
    "simulation": ("simulation_validation", "synthetic panel-structure validation", "~6 min"),
    "multiconfig": ("multiconfig_sensitivity", "1% and 5% within-study flips", "~12 min"),
    "mch1": ("multiconfig_h1", "multi-configuration stress test", "~8 min"),
    "perturb": ("perturbation_upper", "upper-bound extraction perturbation", "~2 min"),
    "pertclust": ("perturbation_clustered", "study-clustered extraction perturbation", "~5 min"),
    "coherence": ("coherence_control", "nearest-Hamming donor control", "~1 min"),
    "threed": ("three_d_models", "three-component models for the three coverage sets", "~7 min"),
    "tail": ("supplementary_checks", "Hamming, tail, subgroup, and study-level checks", "~2 min"),
    "balance": ("balance_diagnostics", "balance diagnostics for Table S14", "~5 s"),
    "flagged": ("flagged_studies", "flagged-study descriptors for Table S15", "~5 s"),
    "tailperm": ("tail_permutation", "independent label permutation null for the collapsed ratio", "~3 min"),
    "tailglobal": ("tail_global_test", "global permutation Cramér--von Mises test (LOO)", "~8 min"),
    "q95corpus": ("q95_corpus", "corpus exceedance at the permutation q95", "~5 s"),
    "leverage": ("leverage_check", "leverage correlations and log models", "~10 s"),
    "q95cal": ("q95_calibration", "synthetic flag rates at >2 and q95", "~6 min"),
    "holdout": ("procrustes_holdout", "held-out Procrustes sensitivity", "~1 min"),
    "dimsweep": ("dimension_sweep", "2--5 component sweep", "~1 min"),
    "leave": ("leave_flagged_out", "leave-six-out venue sensitivity", "~15 s"),
    "flagcis": ("flagged_study_cis", "matched-draw CIs for flagged studies", "~5 s"),
    "table": ("table_checks", "table-level summaries for S3, S5, and S10", "~10 s"),
    "rebuild": ("rebuild_events", "regenerate the primary event tables from the matrix", "~20 s"),
    "check": ("check_ees", "manuscript and number checks", "~5 s"),
    "verify": ("verify_package", "package self-check", "~10 s"),
}

ORDER = ["types", "water", "panel", "pc2", "core", "allpaper", "simulation",
         "multiconfig", "mch1", "perturb", "pertclust", "coherence", "threed",
         "tail", "balance", "flagged", "tailperm", "tailglobal", "q95corpus", "leverage", "q95cal", "holdout",
         "dimsweep", "leave", "flagcis", "table", "rebuild", "check", "verify"]


def run_step(name: str) -> None:
    module_name, title, estimate = STEPS[name]
    print(f"\n== {name}: {title} ({estimate}) ==", flush=True)
    started = time.time()
    module = importlib.import_module(module_name)
    saved_argv = sys.argv
    try:
        sys.argv = [saved_argv[0]]  # keep child parsers from seeing run_all flags
        result = module.main()
    finally:
        sys.argv = saved_argv
    if name == "check" and result not in (None, 0):
        raise SystemExit(result)
    print(f"-- {name} done in {time.time() - started:.1f}s", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the P2 reproducibility package.")
    parser.add_argument("--only", help="comma-separated step names (see --list)")
    parser.add_argument("--quick", action="store_true",
                        help="two simulation replicates; skips the multi-configuration, coherence, 3-D, and tail steps")
    parser.add_argument("--list", action="store_true", help="show steps and exit")
    args = parser.parse_args()

    if args.list:
        for name in ORDER:
            _, title, estimate = STEPS[name]
            print(f"{name:12s} {estimate:8s} {title}")
        return 0

    if args.only:
        selected = [s.strip() for s in args.only.split(",") if s.strip()]
        unknown = [s for s in selected if s not in STEPS]
        if unknown:
            parser.error(f"unknown step(s): {', '.join(unknown)}")
        # keep the canonical order regardless of how the user listed them
        order = [s for s in ORDER if s in selected]
    elif args.quick:
        order = ["types", "panel", "pc2", "core", "allpaper", "simulation", "check", "verify"]
    else:
        order = list(ORDER)

    # The manuscript checks (check_ees/check_numbers) live only in the
    # manuscript package, not in the standalone check repository.
    missing = [s for s in order if importlib.util.find_spec(STEPS[s][0]) is None]
    if missing:
        print(f"skipping unavailable step(s): {', '.join(missing)}", flush=True)
        order = [s for s in order if s not in missing]

    if args.quick:
        if "multiconfig" in order:
            parser.error("--quick and multiconfig cannot be combined: the "
                         "multi-configuration step would overwrite the published summary")
        os.environ["SIM_REPS"] = "2"
        os.environ["SIM_OUT"] = "simulation_validation_quick.json"

    started = time.time()
    for name in order:
        run_step(name)
    print(f"\nall done in {time.time() - started:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
