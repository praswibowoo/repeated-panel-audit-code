#!/usr/bin/env python3
"""Apply the author-approved duplicate-pair cell corrections.

The approved log is the only input. The script validates every current value in
the curated matrix, all-paper matrix, full-extraction matrix, and canonical
stage-A presence layer before writing any file. It also refreshes matrix density
(`rho`) and records before/after hashes and configuration counts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STAGE = ROOT / "docs" / "extraction" / "stageA" / "matrix_presence_v2.csv"
MATRIX_FILES = [
    DATA / "coverage_matrix.csv",
    DATA / "coverage_matrix_all_paper.csv",
    DATA / "coverage_matrix_full_extraction.csv",
]
EXCLUDED = {"B175", "B111", "B095", "B182", "B239"}
PROVENANCE_NOTES = {
    ("B034", "Pom-rainy"): "pH examined in situ; presence set to Y",
    ("B065", "Group B - offshore / island edge (GX03,12,13)"): "NO2 examined at Group-B stations; presence set to Y",
    ("B069", "Station IV - nearshore coastal waters"): "pH examined in common four-station design; presence set to Y",
    ("B166", "Zone B - black mangrove (MB) piezometers"): "TSS explicitly analyzed; presence set to Y",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write_csv(df: pd.DataFrame, path: Path) -> None:
    newline = "\r\n" if b"\r\n" in path.read_bytes() else "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False, lineterminator=newline)
    tmp.replace(path)


def configuration_counts(frame: pd.DataFrame) -> tuple[int, dict[str, int]]:
    params = [c for c in frame.columns if c not in ("paper", "row", "rho")]
    patterns = frame[params].astype(int).astype(str).agg("".join, axis=1)
    per_paper = frame.assign(pattern=patterns).groupby("paper")["pattern"].nunique()
    return int(per_paper.sum()), {k: int(v) for k, v in per_paper.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corrections", type=Path,
        default=DATA / "duplicate_pair_approved_cell_corrections_2026-11-27.csv",
    )
    parser.add_argument("--date", default="2026-11-27")
    parser.add_argument("--dry-run", action="store_true", help="Validate all targets without writing files")
    args = parser.parse_args()

    corrections = pd.read_csv(args.corrections).fillna("")
    required = {"paper", "row", "parameter", "current_value", "new_value", "coordinator_approval"}
    if required - set(corrections.columns):
        raise ValueError(f"correction log missing columns: {sorted(required - set(corrections.columns))}")
    if not corrections.coordinator_approval.eq("approved").all():
        raise ValueError("all corrections must be approved before application")
    if corrections.duplicated(["paper", "row", "parameter"]).any():
        raise ValueError("duplicate cell corrections")

    curated = pd.read_csv(DATA / "coverage_matrix.csv")
    all_paper = pd.read_csv(DATA / "coverage_matrix_all_paper.csv")
    full = pd.read_csv(DATA / "coverage_matrix_full_extraction.csv")
    types = pd.read_csv(DATA / "coverage_matrix_types.csv")
    stage = pd.read_csv(STAGE)
    stage_original_batch_id = stage["batch_id"].copy()
    stage["batch_id"] = stage["batch_id"].ffill()
    stage_data = stage[stage.row_kind.eq("data")].copy()
    stage_data["paper_position"] = stage_data.groupby("batch_id").cumcount()

    before_counts = configuration_counts(curated)
    before_hashes = {str(path.relative_to(ROOT)): sha256(path) for path in MATRIX_FILES + [STAGE]}

    # Resolve and validate every target before mutating any frame.
    targets = []
    for corr in corrections.itertuples(index=False):
        paper = str(corr.paper)
        row = int(corr.row)
        parameter = str(corr.parameter)
        current = int(corr.current_value)
        new = int(corr.new_value)
        if current not in (0, 1) or new not in (0, 1) or current == new:
            raise ValueError(f"invalid binary correction: {paper} {row} {parameter} {current}->{new}")

        type_match = types[(types.paper == paper) & (types.row == row)]
        if len(type_match) != 1:
            raise ValueError(f"type-map lookup failed: {paper} {row}")
        scenario = str(type_match.iloc[0].scenario)
        stage_match = stage_data[(stage_data.batch_id == paper) & (stage_data.scenario == scenario)]
        if len(stage_match) != 1:
            raise ValueError(f"stage lookup failed: {paper} {scenario}")
        position = int(stage_match.iloc[0].paper_position)

        curated_match = curated[(curated.paper == paper) & (curated.row == row)]
        all_indices = all_paper.index[all_paper.paper == paper].tolist()
        full_indices = full.index[full.paper == paper].tolist()
        if len(curated_match) != 1 or position >= len(all_indices) or position >= len(full_indices):
            raise ValueError(f"matrix row lookup failed: {paper} {row} / position {position}")
        curated_idx = int(curated_match.index[0])
        all_idx = int(all_indices[position])
        full_idx = int(full_indices[position])
        stage_idx = int(stage_match.index[0])

        for label, frame, idx in (
            ("curated", curated, curated_idx),
            ("all_paper", all_paper, all_idx),
            ("full_extraction", full, full_idx),
            ("stageA", stage, stage_idx),
        ):
            if parameter not in frame.columns:
                raise ValueError(f"{label}: missing parameter {parameter}")
            raw_value = frame.loc[idx, parameter]
            if label == "stageA":
                token = "" if pd.isna(raw_value) else str(raw_value).strip().upper()
                if token not in {"", "NE", "Y"}:
                    raise ValueError(f"stageA: unexpected presence token {token!r}")
                observed = 1 if token == "Y" else 0
            else:
                observed = 0 if pd.isna(raw_value) else int(float(raw_value))
            if observed != current:
                raise ValueError(
                    f"{label}: current-value mismatch for {paper} {scenario} {parameter}: "
                    f"{observed} != {current}"
                )
        targets.append((corr, scenario, position, curated_idx, all_idx, full_idx, stage_idx, new))

    if args.dry_run:
        print(f"validated {len(targets)} approved cell corrections across {len(set(t[0].paper for t in targets))} papers")
        for corr, scenario, position, *_ in targets:
            print(f"{corr.paper} row {corr.row} ({scenario}): {corr.parameter} {corr.current_value}->{corr.new_value}")
        return 0

    # Apply only after all targets validate.
    for corr, scenario, position, curated_idx, all_idx, full_idx, stage_idx, new in targets:
        parameter = str(corr.parameter)
        curated.loc[curated_idx, parameter] = new
        all_paper.loc[all_idx, parameter] = new
        full.loc[full_idx, parameter] = new
        stage.loc[stage_idx, parameter] = "Y" if new == 1 else "NE"
        note_key = (str(corr.paper), scenario)
        if note_key in PROVENANCE_NOTES:
            marker = "[2026-11-27 author-approved review:"
            existing = str(stage.loc[stage_idx, "cause_effect_note"])
            if marker not in existing:
                stage.loc[stage_idx, "cause_effect_note"] = (
                    existing + " | " + marker + " " + PROVENANCE_NOTES[note_key] + "]"
                )

    for frame in (curated, all_paper, full):
        params = [c for c in frame.columns if c not in ("paper", "row", "rho")]
        frame["rho"] = (frame[params].sum(axis=1) / len(params)).round(6)

    # Preserve the curated = all-paper minus five papers invariant.
    params = [c for c in curated.columns if c not in ("paper", "row", "rho")]
    rebuilt = all_paper[~all_paper.paper.isin(EXCLUDED)].reset_index(drop=True)
    if list(rebuilt.paper) != list(curated.paper) or not (rebuilt[params].values == curated[params].values).all():
        raise ValueError("curated/all-paper invariant failed after correction")

    stage["batch_id"] = stage_original_batch_id
    atomic_write_csv(curated, DATA / "coverage_matrix.csv")
    atomic_write_csv(all_paper, DATA / "coverage_matrix_all_paper.csv")
    atomic_write_csv(full, DATA / "coverage_matrix_full_extraction.csv")
    atomic_write_csv(stage, STAGE)

    corrections["application_status"] = "applied"
    corrections["applied_date"] = args.date
    atomic_write_csv(corrections, args.corrections)

    after_counts = configuration_counts(curated)
    changed_papers = {
        paper: {"before": before_counts[1][paper], "after": after_counts[1][paper]}
        for paper in sorted(before_counts[1])
        if before_counts[1][paper] != after_counts[1][paper]
    }
    audit = {
        "approval_date": args.date,
        "approved_by": "user",
        "correction_file": str(args.corrections.relative_to(ROOT)),
        "cells_applied": len(targets),
        "papers_changed": len(changed_papers),
        "configuration_count_before": before_counts[0],
        "configuration_count_after": after_counts[0],
        "all_paper_configuration_count_after": int(all_paper.assign(
            pattern=all_paper[params].astype(int).astype(str).agg("".join, axis=1)
        ).groupby("paper")["pattern"].nunique().sum()),
        "full_extraction_configuration_count_after": int(full.assign(
            pattern=full[params].astype(int).astype(str).agg("".join, axis=1)
        ).groupby("paper")["pattern"].nunique().sum()),
        "configuration_counts_by_paper": changed_papers,
        "files_updated": [str(path.relative_to(ROOT)) for path in MATRIX_FILES + [STAGE]],
        "sha256_before": before_hashes,
        "sha256_after": {
            str(path.relative_to(ROOT)): sha256(path) for path in MATRIX_FILES + [STAGE]
        },
        "curated_all_paper_invariant": True,
        "rho_refreshed": True,
    }
    audit_path = DATA / f"duplicate_pair_cell_correction_application_audit_{args.date}.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    print(f"wrote {audit_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
