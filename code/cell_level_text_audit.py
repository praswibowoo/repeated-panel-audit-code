#!/usr/bin/env python3
"""Text-assisted triage of the 351-cell coverage audit frame.

This is not human coding. It extracts a best evidence line for each sampled
cell from the source PDF and classifies:

  present cell + evidence line -> text_value=1 (high confidence)
  present cell + no evidence   -> REVIEW
  blank cell + no evidence     -> text_value=0 (high confidence)
  blank cell + evidence line   -> REVIEW

The REVIEW cells need a human decision (figure-only table, synonym miss,
author-name collision, or genuine under-marking).

Writes ``cell_level_triage.csv`` next to the frame.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import data_dir  # noqa: E402

PDF_DIR = Path(ROOT).parent.parent / "p1-family-diagnostic" / "data" / "raw" / "pdf"

ALIASES = {
    "Al": ["aluminum", "aluminium", "al"],
    "Alkalinity": ["alkalinity"],
    "As": ["arsenic", "as"],
    "BOD": ["bod", "biochemical oxygen demand"],
    "COD": ["cod", "chemical oxygen demand"],
    "Cd": ["cadmium", "cd"],
    "Chlorophyll-a": ["chlorophyll", "chl-a", "chl a"],
    "Cl-": ["chloride", "cl-", "cl "],
    "Co": ["cobalt", "co"],
    "Cr": ["chromium", "cr"],
    "Cu": ["copper", "cu"],
    "DO": ["dissolved oxygen", "d.o.", "do"],
    "DOC": ["doc", "dissolved organic carbon"],
    "E. coli": ["e. coli", "escherichia"],
    "EC": ["electrical conductivity", "conductivity", "ec"],
    "Fe": ["iron", "fe"],
    "Fecal Coliform": ["fecal coliform", "faecal coliform"],
    "H2S": ["h2s", "hydrogen sulfide", "sulfide"],
    "Hardness": ["hardness"],
    "Hg": ["mercury", "hg"],
    "Mn": ["manganese", "mn"],
    "NH3": ["ammonia", "nh3"],
    "NH4": ["ammonium", "nh4"],
    "NO2": ["nitrite", "no2"],
    "NO3": ["nitrate", "no3"],
    "Ni": ["nickel", "ni"],
    "ORP": ["orp", "redox"],
    "Oil & Grease": ["oil", "grease"],
    "PO4": ["phosphate", "po4", "orthophosphate"],
    "Pb": ["lead", "pb"],
    "SAR": ["sar", "sodium adsorption"],
    "Salinity": ["salinity", "sal", "psu", "ppt"],
    "Secchi": ["secchi", "transparency"],
    "Si": ["silicate", "silica", "sio2", "si"],
    "TDS": ["tds", "total dissolved solids"],
    "TN": ["total nitrogen", "tn"],
    "TOC": ["toc", "total organic carbon"],
    "TP": ["total phosphorus", "tp"],
    "TSS": ["tss", "total suspended solids", "suspended solids", "spm"],
    "Temperature": ["temperature", "temp"],
    "Total Coliform": ["total coliform"],
    "Turbidity": ["turbidity", "ntu"],
    "Zn": ["zinc", "zn"],
    "pH": ["ph"],
}

BAD_LINE = re.compile(
    r"university|department|faculty|institute|email|e-mail|doi|http|received|"
    r"accepted|corresponding|author|abstract|keyword|copyright|elsevier|springer",
    re.I,
)


def base_param(p: str) -> str:
    for key in ALIASES:
        if key.lower() in p.lower():
            return key
    return p


def alias_regex(alias: str) -> re.Pattern:
    # Token boundary; avoid "as" in "was", "ph" in "graph".
    return re.compile(r"(?<![A-Za-z])" + re.escape(alias) + r"(?![A-Za-z])", re.I)


def best_line(text: str, aliases: list[str]) -> tuple[str, float] | None:
    best = None
    best_score = 0.0
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 6 or BAD_LINE.search(line):
            continue
        for alias in aliases:
            if not alias_regex(alias).search(line):
                continue
            digits = len(re.findall(r"\d", line))
            if digits == 0:
                continue
            score = digits + (2.0 if re.search(r"\d+[.,]?\d*", line) else 0.0)
            if score > best_score:
                best_score = score
                best = line[:220]
    return (best, best_score) if best else None


def main() -> None:
    frame = pd.read_csv(os.path.join(data_dir(), "cell_level_sample.csv"))
    texts = {}
    for paper in sorted(frame.paper.unique()):
        path = PDF_DIR / f"{paper}.pdf"
        if not path.exists():
            texts[paper] = ""
            continue
        try:
            texts[paper] = subprocess.check_output(
                ["pdftotext", "-layout", str(path), "-"],
                stderr=subprocess.DEVNULL, timeout=30,
            ).decode("utf-8", "ignore")
        except Exception:
            texts[paper] = ""

    rows = []
    for _, r in frame.iterrows():
        b = base_param(r.parameter)
        ev = best_line(texts.get(r.paper, ""), ALIASES.get(b, [b.lower()]))
        if r.matrix_value == 1:
            text_value = 1 if ev else "REVIEW"
        else:
            text_value = "REVIEW" if ev else 0
        rows.append({
            "paper": r.paper,
            "row": r.row,
            "parameter": r.parameter,
            "matrix_value": int(r.matrix_value),
            "text_value": text_value,
            "evidence": ev[0] if ev else "",
            "confidence": "high" if text_value != "REVIEW" else "review",
        })

    out = pd.DataFrame(rows)
    path = os.path.join(data_dir(), "cell_level_triage.csv")
    out.to_csv(path, index=False)
    print(f"wrote {path}")
    print(out.text_value.value_counts(dropna=False).to_string())
    print(pd.crosstab(out.matrix_value, out.text_value))


if __name__ == "__main__":
    main()
