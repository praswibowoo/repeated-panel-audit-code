#!/usr/bin/env python3
"""Within-study configuration-heterogeneity sensitivity.

Runs the synthetic panel-structure validation at 1% and 5% within-study
bit-flip rates and merges the two runs into the published summary.

Design is identical to ``simulation_validation.py``: 60 studies,
8 scenarios per study, 30 parameters, 30 matched draws, 100 replicates,
seed 42.  The flip rate is applied to every within-study row, so at 5%
a study's scenarios are similar but no longer identical.

Writes ``results/post_audit/multiconfig_sensitivity.json``.

Run: python3 code/multiconfig_sensitivity.py   (about 12 minutes)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "post_audit")
SCRIPT = os.path.join(ROOT, "code", "simulation_validation.py")
RATES = ("0.01", "0.05")

DESCRIPTION = (
    "Within-study configuration heterogeneity sensitivity for the synthetic "
    "panel-structure validation. Same design as simulation_validation.json "
    "(60 studies, 8 scenarios, 30 parameters, 30 matched draws, 100 replicates, "
    "seed 42), with within-study bit flips added to H0."
)


def run(rate: str) -> dict:
    """Run the simulation at one flip rate and return its summary."""
    name = f"_sim_flip{rate.replace('.', '')}.json"
    env = dict(os.environ, SIM_FLIP=rate, SIM_OUT=name)
    subprocess.run([sys.executable, SCRIPT], check=True, env=env, cwd=ROOT)
    path = os.path.join(OUT, name)
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    os.remove(path)
    return data


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    out = {"description": DESCRIPTION}
    for rate in RATES:
        data = run(rate)
        out[f"flip_{float(rate):.2f}"] = {
            "design": data["design"],
            "H0_repeated_panels_only": data["H0_repeated_panels_only"],
            "H1_planted_study": data["H1_planted_study"],
        }
    path = os.path.join(OUT, "multiconfig_sensitivity.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print("wrote", path)


if __name__ == "__main__":
    main()
