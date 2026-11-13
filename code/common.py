#!/usr/bin/env python3
"""Shared estimator pieces for the repeated-panel coverage audit.

Every script in this package uses the same binary PCA, Procrustes drift,
paired-ratio, bootstrap, and seed convention. They live here once so the
analysis scripts only contain their own design decisions.

Conventions
-----------
SEED, DRAWS, N_BOOT : global defaults used by every script.
seed_for(paper, salt) : per-paper deterministic seed, `SEED + salt + crc32`.
drift(ref, red) : per-row Procrustes displacement between two score matrices.
median_drift(...) : the scalar used in the block/matched ratio.
"""
from __future__ import annotations

import os
import zlib
from collections import Counter

import numpy as np
import pandas as pd
from scipy.spatial import procrustes
from sklearn.decomposition import PCA

SEED = 42
DRAWS = 100
N_BOOT = 10000
EXCLUDED = ("B175", "B111", "B095", "B182", "B239")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERAGE_CANDIDATES = (
    os.path.join(ROOT, "data", "coverage_matrix.csv"),
    os.path.join(ROOT, "manuscript", "ees", "reproducibility", "coverage_matrix.csv"),
)


def fit(X: np.ndarray, dims: int = 2) -> np.ndarray:
    """Binary PCA scores (centred, unscaled)."""
    return PCA(n_components=dims, random_state=SEED).fit_transform(X)


def weighted_pca(X: np.ndarray, w: np.ndarray, dims: int = 2) -> np.ndarray:
    """PCA scores of the weighted covariance (weights sum to one)."""
    w = np.asarray(w, float)
    w = w / w.sum()
    mu = (X * w[:, None]).sum(0)
    Xc = X - mu
    Xw = Xc * np.sqrt(w[:, None])
    U, S, _ = np.linalg.svd(Xw, full_matrices=False)
    return U[:, :dims] * S[:dims]


def row_weights(X: np.ndarray, paper: np.ndarray) -> np.ndarray:
    """1 / (number of rows sharing a paper-configuration), for the weighted fit."""
    counts: Counter = Counter()
    for p, row in zip(paper, X):
        counts[(p, tuple(row.astype(int)))] += 1
    return np.asarray([1.0 / counts[(p, tuple(row.astype(int)))]
                       for p, row in zip(paper, X)], float)


def drift(ref: np.ndarray, red: np.ndarray) -> np.ndarray:
    """Per-row Procrustes displacement after best rotation and scale."""
    a, b, _ = procrustes(ref, red)
    return np.linalg.norm(b - a, axis=1)


def median_drift(ref: np.ndarray, red: np.ndarray) -> float:
    """Median row displacement (the scalar used in the paired ratio)."""
    return float(np.median(drift(ref, red)))


def median_ci(values, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Median with a percentile bootstrap interval."""
    x = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        boot[i] = np.median(x[rng.integers(0, len(x), len(x))])
    return {
        "median": float(np.median(x)),
        "ci_lo": float(np.quantile(boot, 0.025)),
        "ci_hi": float(np.quantile(boot, 0.975)),
        "n": int(len(x)),
    }


def unique_mask(X: np.ndarray, paper: np.ndarray) -> np.ndarray:
    """True on the first occurrence of each within-paper configuration."""
    mask = np.zeros(len(X), bool)
    for p in sorted(set(paper)):
        seen = set()
        for i in np.where(paper == p)[0]:
            key = tuple(X[i].astype(int))
            if key not in seen:
                mask[i] = True
                seen.add(key)
    return mask


def common_ratio(S_ref, S_block, block_rows, S_match, match_rows, keep_mask) -> float:
    """Median block/matched drift ratio on rows retained in both fits."""
    idx = np.where(keep_mask)[0]
    if len(idx) < 3:
        return np.nan
    pb = np.searchsorted(block_rows, idx)
    pm = np.searchsorted(match_rows, idx)
    db = drift(S_ref[idx], S_block[pb])
    dm = drift(S_ref[idx], S_match[pm])
    return float(np.median(db) / np.median(dm))


def seed_for(paper_id: str, salt: int = 0) -> int:
    """Deterministic per-paper seed used by every draw loop."""
    return SEED + salt + zlib.crc32(paper_id.encode()) % 100000


def load_matrix(path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load a coverage matrix as X, rho, paper."""
    frame = pd.read_csv(path)
    params = [c for c in frame.columns if c not in ("paper", "row", "rho")]
    X = frame[params].to_numpy(float)
    rho = X.mean(axis=1)
    paper = frame["paper"].to_numpy()
    return X, rho, paper


def load_curated(path: str | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load the 716-row / 117-paper curated matrix."""
    if path is None:
        for candidate in COVERAGE_CANDIDATES:
            if os.path.exists(candidate):
                path = candidate
                break
    if path is None:
        raise FileNotFoundError(
            "coverage_matrix.csv not found; expected data/coverage_matrix.csv"
        )
    X, rho, paper = load_matrix(path)
    keep = ~np.isin(paper, EXCLUDED)
    X, rho, paper = X[keep], rho[keep], paper[keep]
    if X.shape != (716, 44):
        raise ValueError(f"expected 716 x 44 curated matrix, found {X.shape}")
    if len(set(paper)) != 117:
        raise ValueError(f"expected 117 papers, found {len(set(paper))}")
    return X, rho, paper
