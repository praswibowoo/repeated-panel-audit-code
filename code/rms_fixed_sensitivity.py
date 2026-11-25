#!/usr/bin/env python3
"""Run the fixed-evaluation PCA audit with RMS event drift."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unit_revision_fixed import main  # noqa: E402


def run() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "results", "unit_revision_fixed", "rms_sensitivity.json")
    sys.argv = [
        sys.argv[0],
        "--draws", "100",
        "--drift-summary", "rms",
        "--out", out,
    ]
    return main()


if __name__ == "__main__":
    raise SystemExit(run())
