#!/usr/bin/env python3
"""Independent audit wrapper for the fixed-evaluation revision."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from check_fixed_revision import run_checks

ROOT = Path(__file__).resolve().parent.parent
EES = ROOT / "manuscript" / "ees"


def main() -> int:
    failures = run_checks()
    main_tex = (EES / "main.tex").read_text(encoding="utf-8")
    for retired in (
        "1.31 (1.20--1.59)", "1.13 (0.96--1.37)", "1.01 (0.89--1.17)",
        "0.20 (0.16--0.23)", "0.25 (0.20--0.33)",
    ):
        if retired in main_tex:
            failures.append(f"retired primary value in main text: {retired}")

    fig = ROOT / "figures" / "fig_paired_contrast.pdf"
    if not fig.exists():
        failures.append("missing primary figure")

    for log in ("main.log", "main_supplementary.log"):
        path = EES / log
        if path.exists():
            n = path.read_text(errors="ignore").count("Overfull \\hbox")
            if n:
                failures.append(f"{log}: {n} overfull hboxes")

    for pdf in ("main.pdf", "main_supplementary.pdf"):
        path = EES / pdf
        if not path.exists():
            failures.append(f"missing {pdf}")
            continue
        out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
        if not re.search(r"Pages:\s+\d+", out):
            failures.append(f"cannot read page count for {pdf}")

    print("[audit] fixed-evaluation revision")
    print(f"  failed checks: {len(failures)}")
    for failure in failures:
        print("  FAIL:", failure)
    if not failures:
        print("  PASS: fixed values, retired values, figure, and PDF layout")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
