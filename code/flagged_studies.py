#!/usr/bin/env python3
"""Describe the studies flagged by the collapsed audit.

Writes data/flagged_studies.csv for the SI descriptor table.
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

from common import data_dir  # noqa: E402

DATA = data_dir()
POST = os.path.join(ROOT, "results", "post_audit")
OUT = os.path.join(DATA, "flagged_studies.csv")
PAPERS = ["B063", "B166", "B201", "B102", "B213", "B208"]


def main() -> None:
    cov = pd.read_csv(os.path.join(DATA, "coverage_matrix.csv"))
    types = pd.read_csv(os.path.join(DATA, "coverage_matrix_types.csv"))
    manifest = pd.read_csv(os.path.join(DATA, "corpus_manifest.csv"))
    tail = pd.read_csv(os.path.join(POST, "tail_decomposition.csv"))
    coh = json.load(open(os.path.join(POST, "coherence_control.json"), encoding="utf-8"))

    params = [c for c in cov.columns if c not in ("paper", "row", "rho")]
    rows = []
    for p in PAPERS:
        g = cov[cov.paper == p]
        if g.empty:
            continue
        unique = g[params].drop_duplicates().shape[0]
        mt = types[types.paper == p]["matrix_type"].value_counts().to_dict()
        man = manifest[manifest.batch_id == p]
        t = tail[tail.paper == p]
        c = coh["per_paper"].get(p, {})
        rows.append({
            "paper": p,
            "rows": len(g),
            "unique_configs": int(unique),
            "density": round(float(g["rho"].mean()), 3),
            "matrix_types": "; ".join(f"{k} {v}" for k, v in mt.items()),
            "year": int(man.iloc[0]["year"]) if not man.empty and pd.notna(man.iloc[0]["year"]) else "",
            "journal": man.iloc[0]["journal"] if not man.empty else "",
            "title": man.iloc[0]["title"] if not man.empty else "",
            "doi": man.iloc[0]["doi"] if not man.empty else "",
            "full_ratio": round(float(t.iloc[0]["full_ratio"]), 2) if not t.empty else "",
            "collapsed_ratio": round(float(t.iloc[0]["collapsed_ratio"]), 2) if not t.empty else "",
            "density_ratio": round(float(t.iloc[0]["density_matched_ratio"]), 2) if not t.empty else "",
            "composition_ratio": round(float(t.iloc[0]["composition_ratio"]), 2) if not t.empty else "",
            "coherence_ratio": round(float(c["coherence_ratio"]), 2) if c else "",
            "min_hamming": int(t.iloc[0]["min_hamming"]) if not t.empty and pd.notna(t.iloc[0]["min_hamming"]) else "",
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
