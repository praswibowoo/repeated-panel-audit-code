#!/usr/bin/env python3
"""Run the primary fixed-evaluation ratio-of-medians PCA audit in 3-D."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unit_revision_fixed import main  # noqa: E402


def run() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "results", "unit_revision_fixed", "fixed3d_contrast.json")
    sys.argv = [
        sys.argv[0],
        "--draws", "100",
        "--dims", "3",
        "--out", out,
    ]
    return main()


if __name__ == "__main__":
    raise SystemExit(run())
