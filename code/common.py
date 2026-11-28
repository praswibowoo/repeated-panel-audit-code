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
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.spatial import procrustes
from sklearn.decomposition import PCA

SEED = 42
DRAWS = 100
N_BOOT = 10000
EXCLUDED = ("B175", "B111", "B095", "B182", "B239")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_CANDIDATES = (
    os.path.join(ROOT, "data"),
    os.path.join(ROOT, "manuscript", "ees", "reproducibility"),
)


def data_dir() -> str:
    """Return the directory holding the coverage matrices and event tables.

    The check package keeps them in ``data/``; the manuscript source package
    keeps them in ``manuscript/ees/reproducibility/``. One resolver keeps the
    two layouts on the same code path, so the scripts cannot drift.
    """
    for candidate in DATA_CANDIDATES:
        if os.path.isdir(candidate):
            return candidate
    return DATA_CANDIDATES[0]

COVERAGE_CANDIDATES = (
    os.path.join(ROOT, "data", "coverage_matrix.csv"),
    os.path.join(ROOT, "manuscript", "ees", "reproducibility", "coverage_matrix.csv"),
)
PRIMARY_COVERAGE = os.path.join(ROOT, "data", "coverage_matrix_primary.csv")


@dataclass(frozen=True)
class LoadedMatrix:
    """Coverage matrix plus active-parameter provenance."""

    X: np.ndarray
    rho: np.ndarray
    paper: np.ndarray
    parameters: tuple[str, ...]
    empty_parameters: tuple[str, ...]
    source: str
    corpus: str
    excluded_papers: tuple[str, ...]

    def metadata(self) -> dict:
        return {
            "corpus": self.corpus,
            "matrix_path": os.path.relpath(self.source, ROOT),
            "active_parameters": list(self.parameters),
            "n_active_parameters": len(self.parameters),
            "empty_parameters_dropped": list(self.empty_parameters),
            "loader_excluded_papers": list(self.excluded_papers),
            "rho_definition": "row mean over active (populated) parameter columns",
        }


def fit(X: np.ndarray, dims: int = 2) -> np.ndarray:
    """Binary PCA scores (centred, unscaled)."""
    return PCA(n_components=dims, random_state=SEED).fit_transform(X)


def weighted_pca(X: np.ndarray, w: np.ndarray, dims: int = 2) -> np.ndarray:
    """PCA scores of the weighted covariance (weights sum to one).

    Legacy: the returned scores carry the sqrt(w) row scaling, so a
    configuration with k duplicates is shrunk by 1/sqrt(k).  Use
    `weighted_pca_unweighted` for row-level drift comparisons.
    """
    w = np.asarray(w, float)
    w = w / w.sum()
    mu = (X * w[:, None]).sum(0)
    Xc = X - mu
    Xw = Xc * np.sqrt(w[:, None])
    U, S, _ = np.linalg.svd(Xw, full_matrices=False)
    return U[:, :dims] * S[:dims]


def weighted_pca_unweighted(X: np.ndarray, w: np.ndarray, dims: int = 2) -> np.ndarray:
    """Weighted components with unweighted row scores.

    The weighted covariance equals the collapsed covariance when weights are
    1/k within a paper-configuration.  Projecting the centred rows onto the
    weighted components (instead of returning U*S of X*sqrt(w)) removes the
    per-row sqrt(w) scaling, so the weighted fit is an exact row-level
    identity for the collapsed audit.
    """
    w = np.asarray(w, float)
    w = w / w.sum()
    mu = (X * w[:, None]).sum(0)
    Xc = X - mu
    Xw = Xc * np.sqrt(w[:, None])
    _, _, Vt = np.linalg.svd(Xw, full_matrices=False)
    return Xc @ Vt[:dims].T


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


def _load_matrix_data(
    path: str,
    corpus: str,
    excluded_papers: tuple[str, ...] = (),
) -> LoadedMatrix:
    frame = pd.read_csv(path)
    nominal = [c for c in frame.columns if c not in ("paper", "row", "rho")]
    values = frame[nominal].to_numpy(float)
    active_mask = np.any(values != 0, axis=0)
    parameters = tuple(c for c, keep in zip(nominal, active_mask) if keep)
    empty_parameters = tuple(c for c, keep in zip(nominal, active_mask) if not keep)
    if not parameters:
        raise ValueError(f"no populated parameter columns in {path}")
    X = frame[list(parameters)].to_numpy(float)
    rho = X.mean(axis=1)
    paper = frame["paper"].to_numpy()
    if excluded_papers:
        keep = ~np.isin(paper, excluded_papers)
        X, rho, paper = X[keep], rho[keep], paper[keep]
    return LoadedMatrix(
        X=X,
        rho=rho,
        paper=paper,
        parameters=parameters,
        empty_parameters=empty_parameters,
        source=os.path.abspath(path),
        corpus=corpus,
        excluded_papers=excluded_papers,
    )


def load_matrix(path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load X, recomputed rho, and paper after dropping all-zero parameters."""
    loaded = _load_matrix_data(path, corpus="custom")
    return loaded.X, loaded.rho, loaded.paper


def _validate_shape(loaded: LoadedMatrix, rows: int, papers: int, parameters: int) -> None:
    if loaded.X.shape != (rows, parameters):
        raise ValueError(
            f"expected {rows} x {parameters} populated {loaded.corpus} matrix, "
            f"found {loaded.X.shape}"
        )
    n_papers = len(set(loaded.paper))
    if n_papers != papers:
        raise ValueError(f"expected {papers} papers, found {n_papers}")


def load_curated(
    path: str | None = None,
    *,
    return_metadata: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | LoadedMatrix:
    """Load the full 716-row / 117-paper / 42-active-parameter sensitivity corpus."""
    if path is None:
        for candidate in COVERAGE_CANDIDATES:
            if os.path.exists(candidate):
                path = candidate
                break
    if path is None:
        raise FileNotFoundError(
            "coverage_matrix.csv not found; expected data/coverage_matrix.csv"
        )
    loaded = _load_matrix_data(path, corpus="full_curated", excluded_papers=EXCLUDED)
    _validate_shape(loaded, rows=716, papers=117, parameters=42)
    if return_metadata:
        return loaded
    return loaded.X, loaded.rho, loaded.paper


def load_primary(
    path: str | None = None,
    *,
    return_metadata: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | LoadedMatrix:
    """Load the 555-row / 87-paper / 42-active-parameter primary corpus."""
    path = path or PRIMARY_COVERAGE
    loaded = _load_matrix_data(path, corpus="primary")
    _validate_shape(loaded, rows=555, papers=87, parameters=42)
    if return_metadata:
        return loaded
    return loaded.X, loaded.rho, loaded.paper
