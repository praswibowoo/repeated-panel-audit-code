#!/usr/bin/env python3
"""Draw or verify a frozen duplicate-pair audit frame.

The manuscript's central exposure is whether two scenario rows within a paper
share one coverage configuration. This frame samples row pairs directly rather
than individual cells:

* 40 pairs coded as identical configurations by the matrix;
* 40 random pairs coded as distinct configurations;
* 20 nearest distinct pairs (Hamming distance <= 3 where available).

The frame is reproducible from coverage_matrix.csv. It contains 100 records
representing 83 unique unordered pairs. The 56 priority pairs now have
user-approved coordinator resolutions; the remaining 27 pairs are not part of
the primary-only adjudication. Independent AI-assisted source-review labels
remain stored alongside the frozen frame. Run without --force to verify the
frozen frame.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import data_dir  # noqa: E402

SEED = 20261125
N_DUPLICATE = 40
N_DISTINCT_RANDOM = 40
N_DISTINCT_NEAR = 20


def draw_frame() -> pd.DataFrame:
    frame = pd.read_csv(os.path.join(data_dir(), "coverage_matrix.csv"))
    params = [c for c in frame.columns if c not in ("paper", "row", "rho")]
    X = frame[params].to_numpy(int)
    paper = frame["paper"].to_numpy(object)
    rho = frame["rho"].to_numpy(float)
    rng = np.random.default_rng(SEED)

    duplicate_pairs = []
    distinct_random_pairs = []
    distinct_near_pairs = []

    for p in sorted(set(paper)):
        idx = np.where(paper == p)[0]
        if len(idx) < 2:
            continue
        patterns = {}
        for i in idx:
            patterns.setdefault(tuple(X[i]), []).append(int(i))
        groups = list(patterns.values())

        for group in groups:
            if len(group) < 2:
                continue
            for _ in range(min(2, len(group))):
                a, b = rng.choice(group, size=2, replace=False)
                duplicate_pairs.append((int(a), int(b), "matrix_identical"))

        for _ in range(max(2, len(groups) * 3)):
            a, b = rng.choice(idx, size=2, replace=False)
            if tuple(X[a]) != tuple(X[b]):
                distinct_random_pairs.append(
                    (int(a), int(b), "matrix_distinct_random")
                )

        near = []
        for gi in range(len(groups)):
            for gj in range(gi + 1, len(groups)):
                a = int(groups[gi][0])
                b = int(groups[gj][0])
                h = int(np.sum(X[a] != X[b]))
                near.append((h, a, b))
        for h, a, b in sorted(near)[:10]:
            distinct_near_pairs.append((int(a), int(b), "matrix_distinct_near"))

    def sample(pool: list, n: int) -> list:
        if len(pool) < n:
            raise RuntimeError(f"audit pool too small: {len(pool)} < {n}")
        chosen = rng.choice(len(pool), size=n, replace=False)
        return [pool[int(i)] for i in chosen]

    rows = []
    for a, b, stratum in (
        sample(duplicate_pairs, N_DUPLICATE)
        + sample(distinct_random_pairs, N_DISTINCT_RANDOM)
        + sample(distinct_near_pairs, N_DISTINCT_NEAR)
    ):
        rows.append({
            "paper": paper[a],
            "row_a": int(frame.loc[a, "row"]),
            "row_b": int(frame.loc[b, "row"]),
            "audit_stratum": stratum,
            "matrix_hamming": int(np.sum(X[a] != X[b])),
            "density_a": float(rho[a]),
            "density_b": float(rho[b]),
            "paper_configurations": int(len(patterns_for_paper(X, paper, a))),
            "paper_rows": int(np.sum(paper == paper[a])),
            "human_relation": "",
            "match": "",
            "notes": "",
        })
    return pd.DataFrame(rows)


def patterns_for_paper(X: np.ndarray, paper: np.ndarray, i: int) -> set:
    return {tuple(X[j]) for j in np.where(paper == paper[i])[0]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    path = os.path.join(data_dir(), "duplicate_pair_audit_frame.csv")
    if os.path.exists(path) and not args.force:
        old = pd.read_csv(path)
        old_ordered = old.assign(
            row_lo=old[["row_a", "row_b"]].min(axis=1),
            row_hi=old[["row_a", "row_b"]].max(axis=1),
        )
        unique = old_ordered.drop_duplicates(["paper", "row_lo", "row_hi"])
        if len(old) != 100 or len(unique) != 83 or old.paper.nunique() < 20:
            raise SystemExit("frozen duplicate-pair frame has unexpected structure")
        if old.reviewer_relation.isna().any():
            raise SystemExit("frozen duplicate-pair frame lacks AI-assisted source-review labels")
        resolved = old_ordered.dropna(subset=["human_relation"]).drop_duplicates(["paper", "row_lo", "row_hi"])
        if len(resolved) != 56 or not old["match"].notna().sum() == old.human_relation.notna().sum():
            raise SystemExit("approved human-adjudication fields have unexpected structure")
        if not resolved.human_relation.isin({"same", "different", "undecidable"}).all():
            raise SystemExit("approved human-adjudication fields contain invalid labels")
        if resolved.human_relation.value_counts().to_dict() != {"same": 53, "undecidable": 3}:
            raise SystemExit("approved human-adjudication counts changed unexpectedly")
        print(f"verified frozen duplicate-pair frame: {len(old)} records, {len(unique)} unique unordered pairs")
        print(f"approved primary resolutions: {len(resolved)} unique pairs")
        print(f"sha256={hashlib.sha256(open(path, 'rb').read()).hexdigest()}")
        return
    out = draw_frame()
    out.to_csv(path, index=False)
    print(f"wrote {path}: {len(out)} pairs from {out.paper.nunique()} papers")
    print(out.audit_stratum.value_counts().to_string())
    if args.force:
        print("WARNING: new frame; do not reuse historical coding.")


if __name__ == "__main__":
    main()
