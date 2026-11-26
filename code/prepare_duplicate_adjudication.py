#!/usr/bin/env python3
"""Prepare blind primary/secondary duplicate-pair adjudication workbooks.

The visible coder sheets contain no matrix class, Hamming distance, AI label, or
priority reason. A separate coordinator key links the 83 unordered pairs to the
existing matrix/AI review and to prior P1 human cell corrections.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import xlsxwriter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCE_REVIEW = DATA / "duplicate_pair_source_review.csv"
FRAME = DATA / "duplicate_pair_audit_frame.csv"
COVERAGE = DATA / "coverage_matrix.csv"
TYPES = DATA / "coverage_matrix_types.csv"
MANIFEST_PAPERS = DATA / "corpus_manifest.csv"
PRIOR_CORRECTIONS = DATA / "prior_human_cell_corrections.csv"

SEED = 20261126
QC_FRACTION = 0.20

BLIND_COLUMNS = [
    "pair_id", "paper", "doi", "title", "row_a", "row_b",
    "scenario_a", "scenario_b", "source_pdf_local", "source_text_local",
    "human_relation", "parameters_only_a", "parameters_only_b",
    "proposed_matrix_corrections", "source_page_table", "confidence",
    "coder_name", "coder_date", "notes",
]


def unordered_key(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["row_lo"] = out[["row_a", "row_b"]].min(axis=1)
    out["row_hi"] = out[["row_a", "row_b"]].max(axis=1)
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def make_workbook(path: Path, sheets: dict[str, pd.DataFrame], instructions: list[str]) -> None:
    workbook = xlsxwriter.Workbook(path)
    workbook.set_properties({
        "title": "Duplicate-pair human adjudication",
        "subject": "Blind source-text verification for P2 deletion audit",
        "author": "P2 deletion-audit team",
        "comments": "Coder sheets exclude matrix and AI labels.",
    })
    header = workbook.add_format({
        "bold": True, "font_color": "white", "bg_color": "#1F4E78",
        "border": 1, "text_wrap": True, "valign": "top",
    })
    text = workbook.add_format({"text_wrap": True, "valign": "top"})
    date_fmt = workbook.add_format({"num_format": "yyyy-mm-dd", "valign": "top"})
    title_fmt = workbook.add_format({"bold": True, "font_size": 14})
    instruction_fmt = workbook.add_format({"text_wrap": True, "valign": "top", "font_size": 11})

    ws = workbook.add_worksheet("Instructions")
    ws.set_column("A:A", 110)
    ws.write("A1", "Duplicate-pair human adjudication", title_fmt)
    for i, line in enumerate(instructions, start=2):
        ws.write(i - 1, 0, line, instruction_fmt)
        ws.set_row(i - 1, 32)

    for sheet_name, df in sheets.items():
        ws = workbook.add_worksheet(sheet_name)
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(df), len(df.columns) - 1)
        ws.set_row(0, 34)
        for col_idx, col in enumerate(df.columns):
            ws.write(0, col_idx, col, header)
            width = 18
            if col in {"title", "scenario_a", "scenario_b", "notes", "evidence_notes",
                       "prior_human_note", "parameters_only_a", "parameters_only_b",
                       "proposed_matrix_corrections", "source_page_table", "priority_reason",
                       "prior_human_evidence", "matrix_only_a", "matrix_only_b"}:
                width = 42
            elif col in {"source_pdf_local", "source_text_local", "doi"}:
                width = 34
            ws.set_column(col_idx, col_idx, width, text)
        for r_idx, row in enumerate(df.itertuples(index=False, name=None), start=1):
            for c_idx, value in enumerate(row):
                if pd.isna(value):
                    continue
                fmt = date_fmt if df.columns[c_idx] == "coder_date" else text
                ws.write(r_idx, c_idx, value, fmt)
        if "human_relation" in df.columns:
            c = df.columns.get_loc("human_relation")
            ws.data_validation(1, c, max(1, len(df)), c, {
                "validate": "list", "source": ["same", "different", "undecidable"],
                "input_title": "Relation",
                "input_message": "same / different / undecidable",
            })
        if "confidence" in df.columns:
            c = df.columns.get_loc("confidence")
            ws.data_validation(1, c, max(1, len(df)), c, {
                "validate": "list", "source": ["high", "medium", "low"],
            })
    workbook.close()


def make_simple_workbook(path: Path, df: pd.DataFrame) -> None:
    workbook = xlsxwriter.Workbook(path)
    workbook.set_properties({
        "title": "Primary duplicate-pair adjudication — simple",
        "subject": "Eight-column blind source-text coding sheet",
        "author": "P2 deletion-audit team",
    })
    title = workbook.add_format({"bold": True, "font_size": 14})
    body = workbook.add_format({"text_wrap": True, "valign": "top", "font_size": 11})
    header = workbook.add_format({
        "bold": True, "font_color": "white", "bg_color": "#1F4E78",
        "border": 1, "text_wrap": True, "valign": "top",
    })
    locked = workbook.add_format({"bg_color": "#E7E6E6", "text_wrap": True, "valign": "top"})
    editable = workbook.add_format({"bg_color": "#FFF2CC", "text_wrap": True, "valign": "top"})
    link = workbook.add_format({"bg_color": "#E7E6E6", "font_color": "#0563C1", "underline": 1})
    date_fmt = workbook.add_format({"bg_color": "#FFF2CC", "num_format": "yyyy-mm-dd", "valign": "top"})

    ws = workbook.add_worksheet("Instructions")
    ws.set_column("A:A", 105)
    ws.write("A1", "Primary adjudication — simple 8-column sheet", title)
    lines = [
        "Click pair_id to open the source PDF in the sibling p1-family-diagnostic repository.",
        "Fill only the yellow columns: relation, evidence, correction, coder, date.",
        "relation: same = identical examined-parameter suite; different = at least one parameter differs; undecidable = source insufficient.",
        "evidence: give PDF page/table/figure plus the decisive parameter difference or reason.",
        "correction: optional. Format: row number; parameter; current value -> new value; reason. Leave blank if none.",
        "coder/date: fill once, then copy down. Save the Primary sheet as CSV UTF-8 when finished.",
    ]
    for i, line in enumerate(lines, start=2):
        ws.write(i - 1, 0, line, body)
        ws.set_row(i - 1, 30)

    ws = workbook.add_worksheet("Primary")
    ws.freeze_panes(1, 0)
    ws.autofilter(0, 0, len(df), len(df.columns) - 1)
    widths = [20, 34, 34, 16, 52, 42, 20, 14]
    for c, width in enumerate(widths):
        ws.set_column(c, c, width)
    for c, col in enumerate(df.columns):
        ws.write(0, c, col, header)
    ws.set_row(0, 30)
    for r_idx, row in enumerate(df.itertuples(index=False), start=1):
        for c_idx, col in enumerate(df.columns):
            value = row[c_idx]
            if col == "pair_id":
                paper = str(value).split("_", 1)[0]
                url = f"external:../../p1-family-diagnostic/data/raw/pdf/{paper}.pdf"
                ws.write_url(r_idx, c_idx, url, link, string=str(value))
            elif col in {"relation", "evidence", "correction", "coder"}:
                ws.write(r_idx, c_idx, "" if pd.isna(value) else value, editable)
            elif col == "date":
                ws.write_blank(r_idx, c_idx, None, date_fmt)
            else:
                ws.write(r_idx, c_idx, "" if pd.isna(value) else value, locked)
    ws.data_validation(1, 3, max(1, len(df)), 3, {
        "validate": "list", "source": ["same", "different", "undecidable"],
        "input_title": "Relation",
        "input_message": "same / different / undecidable",
    })
    workbook.close()


def main() -> None:
    review = unordered_key(pd.read_csv(SOURCE_REVIEW)).drop_duplicates(["paper", "row_lo", "row_hi"])
    frame = unordered_key(pd.read_csv(FRAME)).drop_duplicates(["paper", "row_lo", "row_hi"])
    coverage = pd.read_csv(COVERAGE)
    types = pd.read_csv(TYPES)
    papers = pd.read_csv(MANIFEST_PAPERS)
    prior = pd.read_csv(PRIOR_CORRECTIONS)

    if len(review) != 83:
        raise ValueError(f"expected 83 unordered source-review pairs, found {len(review)}")

    params = [c for c in coverage.columns if c not in ("paper", "row", "rho")]
    key_cols = ["pair_id", "paper", "row_a", "row_b", "scenario_a", "scenario_b"]
    coordinator = review[key_cols + ["row_lo", "row_hi"]].merge(
        frame[["paper", "row_lo", "row_hi", "audit_stratum", "matrix_hamming"]],
        on=["paper", "row_lo", "row_hi"], how="left", validate="one_to_one",
    ).merge(
        review[["pair_id", "reviewer_relation"]], on="pair_id", how="left", validate="one_to_one"
    )

    # Bibliographic metadata for source retrieval.
    coord_papers = papers.rename(columns={"batch_id": "paper"})
    coordinator = coordinator.merge(
        coord_papers[["paper", "doi", "title"]], on="paper", how="left", validate="many_to_one"
    )

    # Prior human cell corrections: map each correction to the curated row and
    # then to every reviewed pair containing that row.
    evidence_rows = []
    correction_status = []
    for corr in prior.itertuples(index=False):
        matched = types[(types.paper == corr.paper) & (types.scenario == corr.scenario)]
        if matched.empty:
            correction_status.append({
                "paper": corr.paper, "scenario": corr.scenario, "parameter": corr.parameter,
                "status": "scenario_not_in_curated_matrix",
            })
            continue
        for t in matched.itertuples(index=False):
            cell = coverage[(coverage.paper == corr.paper) & (coverage.row == t.row)]
            current_value = None if cell.empty else cell.iloc[0].get(corr.parameter)
            correction_status.append({
                "paper": corr.paper, "scenario": corr.scenario, "parameter": corr.parameter,
                "row": int(t.row), "current_value": current_value,
                "status": "applied_zero" if current_value == 0 else "not_zero",
            })
            pair_rows = coordinator[(coordinator.paper == corr.paper) &
                                    ((coordinator.row_a == t.row) | (coordinator.row_b == t.row))]
            for pair in pair_rows.itertuples(index=False):
                a = coverage[(coverage.paper == pair.paper) & (coverage.row == pair.row_a)].iloc[0]
                b = coverage[(coverage.paper == pair.paper) & (coverage.row == pair.row_b)].iloc[0]
                only_a = [p for p in params if a[p] == 1 and b[p] == 0]
                only_b = [p for p in params if b[p] == 1 and a[p] == 0]
                if pair.matrix_hamming > 0 and pair.reviewer_relation == "same":
                    evidence_status = "conflicts_with_ai_same"
                elif pair.matrix_hamming > 0 and pair.reviewer_relation == "different":
                    evidence_status = "consistent_with_ai_different"
                else:
                    evidence_status = "identical_pair_requires_confirmation"
                evidence_rows.append({
                    "pair_id": pair.pair_id,
                    "paper": pair.paper,
                    "corrected_row": int(t.row),
                    "parameter": corr.parameter,
                    "current_value": current_value,
                    "prior_human_note": corr.prior_human_note,
                    "matrix_only_a": "; ".join(only_a),
                    "matrix_only_b": "; ".join(only_b),
                    "ai_relation": pair.reviewer_relation,
                    "evidence_status": evidence_status,
                    "acceptance_record": corr.acceptance_record,
                })

    evidence = pd.DataFrame(evidence_rows).drop_duplicates(
        ["pair_id", "corrected_row", "parameter"]
    )
    evidence_by_pair = evidence.groupby("pair_id").agg(
        prior_human_evidence=("prior_human_note", lambda x: " | ".join(sorted(set(x)))),
        prior_evidence_status=("evidence_status", lambda x: "; ".join(sorted(set(x)))),
    ).reset_index()
    coordinator = coordinator.merge(evidence_by_pair, on="pair_id", how="left")
    coordinator["prior_human_evidence"] = coordinator["prior_human_evidence"].fillna("")
    coordinator["prior_evidence_status"] = coordinator["prior_evidence_status"].fillna("none")

    def priority(row: pd.Series) -> tuple[str, str]:
        if row.audit_stratum == "matrix_identical":
            return "P1_confirm_identical", "Confirm matrix-identical pair from source text"
        if row.reviewer_relation == "same":
            return "P2_resolve_disagreement", "Matrix-distinct but AI-reviewed same"
        if row.reviewer_relation == "undecidable":
            return "P3_resolve_undecidable", "AI review undecidable"
        return "QC_agreed_distinct", "Agreed-distinct quality-control sample"

    coordinator[["priority_tier", "priority_reason"]] = coordinator.apply(
        lambda r: pd.Series(priority(r)), axis=1
    )
    coordinator["undecidable_flag"] = coordinator.reviewer_relation.eq("undecidable")
    primary_ids = set(coordinator.loc[coordinator.priority_tier != "QC_agreed_distinct", "pair_id"])

    qc_pool = sorted(coordinator.loc[coordinator.priority_tier == "QC_agreed_distinct", "pair_id"])
    qc_n = math.ceil(QC_FRACTION * len(qc_pool))
    rng = np.random.default_rng(SEED)
    qc_ids = set(rng.choice(qc_pool, size=qc_n, replace=False).tolist())
    second_ids = primary_ids | qc_ids
    coordinator["primary_required"] = coordinator.pair_id.isin(primary_ids)
    coordinator["second_coder_required"] = coordinator.pair_id.isin(second_ids)

    # Visible coder sheets: no matrix class, Hamming, AI label, or priority reason.
    blind = coordinator[[
        "pair_id", "paper", "doi", "title", "row_a", "row_b", "scenario_a", "scenario_b"
    ]].copy()
    blind["source_pdf_local"] = blind.paper.map(lambda p: f"p1-family-diagnostic/data/raw/pdf/{p}.pdf")
    blind["source_text_local"] = blind.paper.map(lambda p: f"p1-family-diagnostic/docs/extraction/corpus_texts/{p}.txt")
    for col in BLIND_COLUMNS:
        if col not in blind.columns:
            blind[col] = ""
    blind = blind[BLIND_COLUMNS]
    primary = blind[blind.pair_id.isin(primary_ids)].sort_values("pair_id").reset_index(drop=True)
    second = blind[blind.pair_id.isin(second_ids)].sort_values("pair_id").reset_index(drop=True)

    write_csv(primary, DATA / "duplicate_pair_human_adjudication_primary_blind.csv")
    write_csv(second, DATA / "duplicate_pair_human_adjudication_second_blind.csv")
    simple = primary[["pair_id", "scenario_a", "scenario_b"]].copy()
    simple["relation"] = ""
    simple["evidence"] = ""
    simple["correction"] = ""
    simple["coder"] = ""
    simple["date"] = ""
    write_csv(simple, DATA / "duplicate_pair_human_adjudication_primary_simple.csv")
    write_csv(coordinator.sort_values("pair_id"), DATA / "duplicate_pair_human_adjudication_coordinator_key.csv")
    write_csv(evidence.sort_values(["pair_id", "corrected_row", "parameter"]),
              DATA / "prior_human_pair_evidence.csv")
    write_csv(pd.DataFrame(correction_status), DATA / "prior_human_cell_corrections_status.csv")

    instructions = [
        "Work only from the source paper/PDF and the scenario labels. Do not open the coordinator key or AI review before coding.",
        "Code human_relation as same when the examined-parameter suites are identical; different when at least one parameter differs; undecidable when the source cannot support a decision.",
        "Coding rule: examined or examined-absent = 1; not reported = 0. Normalize parameter names to the 44-column manuscript schema.",
        "For different pairs, list parameters_only_a and parameters_only_b and give a page/table/figure locator.",
        "For any proposed matrix correction, specify paper, row, parameter, new value, source locator, and reason. Do not silently edit the coverage matrix.",
        "Record coder_name and coder_date. The second coder should work independently and should not see the primary coder's labels.",
        "Return the completed CSV or workbook. The coordinator will resolve disagreements and update the audit documentation.",
    ]
    make_workbook(
        DATA / "duplicate_pair_human_adjudication_coder.xlsx",
        {"Primary": primary, "Second": second}, instructions,
    )
    make_workbook(
        DATA / "duplicate_pair_human_adjudication_primary_only.xlsx",
        {"Primary": primary}, instructions,
    )
    make_simple_workbook(
        DATA / "duplicate_pair_human_adjudication_primary_simple.xlsx",
        simple,
    )
    make_workbook(
        DATA / "duplicate_pair_human_adjudication_second_only.xlsx",
        {"Second": second}, instructions,
    )
    make_workbook(
        DATA / "duplicate_pair_human_adjudication_coordinator.xlsx",
        {
            "Coordinator_Key": coordinator.sort_values("pair_id"),
            "Prior_Evidence": evidence.sort_values(["pair_id", "corrected_row", "parameter"]),
            "Prior_Corrections": prior,
            "Correction_Status": pd.DataFrame(correction_status),
        },
        ["Coordinator only: this workbook contains matrix classes, AI labels, priority flags, and prior human evidence.",
         "Send coders only duplicate_pair_human_adjudication_coder.xlsx or the blind CSV files."],
    )

    generated = [
        DATA / "duplicate_pair_human_adjudication_primary_blind.csv",
        DATA / "duplicate_pair_human_adjudication_primary_simple.csv",
        DATA / "duplicate_pair_human_adjudication_second_blind.csv",
        DATA / "duplicate_pair_human_adjudication_coordinator_key.csv",
        DATA / "prior_human_pair_evidence.csv",
        DATA / "prior_human_cell_corrections_status.csv",
        DATA / "duplicate_pair_human_adjudication_coder.xlsx",
        DATA / "duplicate_pair_human_adjudication_primary_only.xlsx",
        DATA / "duplicate_pair_human_adjudication_primary_simple.xlsx",
        DATA / "duplicate_pair_human_adjudication_second_only.xlsx",
        DATA / "duplicate_pair_human_adjudication_coordinator.xlsx",
    ]
    manifest = {
        "preparation_date": "2026-11-26",
        "released": False,
        "primary_coder": "",
        "second_coder": "",
        "seed": SEED,
        "coding_rule": "same = identical examined-parameter suite; different = at least one parameter differs; undecidable = source insufficient",
        "counts": {
            "all_pairs": len(coordinator),
            "matrix_identical": int(coordinator.audit_stratum.eq("matrix_identical").sum()),
            "matrix_distinct": int(coordinator.audit_stratum.ne("matrix_identical").sum()),
            "ai_same": int(coordinator.reviewer_relation.eq("same").sum()),
            "ai_different": int(coordinator.reviewer_relation.eq("different").sum()),
            "ai_undecidable": int(coordinator.reviewer_relation.eq("undecidable").sum()),
            "primary_required": len(primary_ids),
            "second_coder_required": len(second_ids),
            "qc_agreed_distinct": qc_n,
            "prior_human_corrections": len(prior),
            "prior_evidence_pairs": int(evidence.pair_id.nunique()),
            "prior_evidence_conflicts_with_ai_same": int(evidence.evidence_status.eq("conflicts_with_ai_same").sum()),
            "prior_evidence_consistent_with_ai_different": int(evidence.evidence_status.eq("consistent_with_ai_different").sum()),
        },
        "primary_pair_ids": sorted(primary_ids),
        "second_coder_pair_ids": sorted(second_ids),
        "qc_pair_ids": sorted(qc_ids),
        "prior_evidence_conflict_pair_ids": sorted(
            evidence.loc[evidence.evidence_status == "conflicts_with_ai_same", "pair_id"].unique()
        ),
        "files": {str(p.relative_to(ROOT)): sha256(p) for p in generated},
        "notes": [
            "Coder files are blind: no matrix class, Hamming distance, AI relation, or priority reason is shown.",
            "For a primary-only workflow, send duplicate_pair_human_adjudication_primary_simple.xlsx or the simple primary CSV.",
            "The simple sheet has eight columns; pair_id links to the source PDF and yellow columns are the only fields to complete.",
            "Prior P1 human cell corrections are evidence only; they do not replace pair-level human labels.",
            "Eight AI-same/matrix-distinct pairs conflict with prior human cell corrections and require explicit pair adjudication.",
            "The primary assignment is the union of all matrix-identical pairs, all matrix-distinct/AI-same pairs, and all undecidable pairs.",
        ],
    }
    (DATA / "duplicate_pair_adjudication_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(json.dumps(manifest["counts"], indent=2))
    print(f"wrote adjudication package under {DATA}")


if __name__ == "__main__":
    main()
