#!/usr/bin/env python3
"""run_all.py — one command for the whole package.

Examples
--------
    python3 code/run_all.py                  # every analysis (~22 minutes)
    python3 code/run_all.py --quick          # fast check (~2 minutes)
    python3 code/run_all.py --only panel,pc2
    python3 code/run_all.py --list

Each analysis writes its summary under ``results/``.  The last step is the
package self-check, so a green run means the committed values were reproduced.

The long steps are the synthetic validation (~6 min), the multi-configuration
sensitivity (~12 min, which runs the synthetic validation twice), the coherence control (~1 min), the three-set
3-D models (~7 min), and the tail checks (~2 min).  ``--quick`` runs the
synthetic validation with two replicates and skips the multi-configuration,
coherence, 3-D, and tail steps, so it does not overwrite their published summaries.
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

STEPS: dict[str, tuple[str, str, str]] = {
    "panel": ("panel_decomposition", "2x2 decomposition and density control", "~60 s"),
    "pc2": ("pc2_density_check", "PC2 density-matched class check", "~15 s"),
    "core": ("core_revision_checks", "coarsened control and exact-subset CIs", "~60 s"),
    "allpaper": ("all_paper_audit", "all-paper 730/122 audit", "~2 min"),
    "simulation": ("simulation_validation", "synthetic panel-structure validation", "~6 min"),
    "multiconfig": ("multiconfig_sensitivity", "1% and 5% within-study flips", "~12 min"),
    "coherence": ("coherence_control", "coherence-matched control", "~1 min"),
    "threed": ("three_d_models", "three-component models for the three coverage sets", "~7 min"),
    "tail": ("supplementary_checks", "Hamming, tail, subgroup, and study-level checks", "~2 min"),
    "tailnull": ("tail_null", "permutation null for the per-study collapsed ratio", "~10 s"),
    "rebuild": ("rebuild_events", "regenerate the primary event tables from the matrix", "~20 s"),
    "verify": ("verify_package", "package self-check", "~10 s"),
}

ORDER = ["panel", "pc2", "core", "allpaper", "simulation", "multiconfig", "coherence", "threed", "tail", "tailnull", "rebuild", "verify"]


def run_step(name: str) -> None:
    module_name, title, estimate = STEPS[name]
    print(f"\n== {name}: {title} ({estimate}) ==", flush=True)
    started = time.time()
    module = importlib.import_module(module_name)
    result = module.main()
    if name == "verify" and result not in (None, 0):
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
        order = ["panel", "pc2", "core", "allpaper", "simulation", "verify"]
    else:
        order = list(ORDER)

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
