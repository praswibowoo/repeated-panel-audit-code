#!/usr/bin/env python3
"""Extract the Primary sheet from the simple adjudication workbook to CSV.

Uses only the Python standard library so the workbook can be processed without
an Excel reader dependency.
"""
from __future__ import annotations

import argparse
import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def extract(xlsx: Path, csv_path: Path) -> int:
    with zipfile.ZipFile(xlsx) as zf:
        shared = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))

        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        sheet_path = None
        for sheet in workbook.find("m:sheets", NS):
            if sheet.attrib["name"] == "Primary":
                rid = sheet.attrib[f"{{{REL_NS}}}id"]
                sheet_path = "xl/" + relmap[rid]
                break
        if sheet_path is None:
            raise ValueError("Primary sheet not found")

        root = ET.fromstring(zf.read(sheet_path))
        rows = []
        for row in root.findall(".//m:sheetData/m:row", NS):
            values = [""] * 8
            for cell in row.findall("m:c", NS):
                ref = cell.attrib.get("r", "A1")
                match = re.match(r"([A-Z]+)", ref)
                col_idx = 0
                for char in match.group(1):
                    col_idx = col_idx * 26 + ord(char) - 64
                if col_idx > 8:
                    continue
                cell_type = cell.attrib.get("t")
                value_node = cell.find("m:v", NS)
                if cell_type == "inlineStr":
                    value = "".join(
                        t.text or "" for t in cell.iter(f"{{{NS['m']}}}t")
                    )
                elif value_node is None:
                    value = ""
                elif cell_type == "s":
                    value = shared[int(value_node.text)]
                else:
                    value = value_node.text or ""
                values[col_idx - 1] = value
            if any(value != "" for value in values):
                rows.append(values)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)
    return max(0, len(rows) - 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    n = extract(args.xlsx, args.csv)
    print(f"wrote {args.csv}: {n} data rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
