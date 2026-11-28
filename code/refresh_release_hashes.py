#!/usr/bin/env python3
"""Regenerate MANIFEST.json file hashes and SHA256SUMS for the release."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "MANIFEST.json"
SHA256SUMS = ROOT / "SHA256SUMS"
GENERATOR = "code/refresh_release_hashes.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    release_id = (ROOT / "RELEASE_ID.txt").read_text(encoding="utf-8").strip()
    release_date = "-".join(release_id.split("-")[1:])

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["release"] = release_id
    manifest["date"] = release_date

    listed = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    ).decode("utf-8").split("\0")
    rels = sorted({
        rel for rel in listed
        if rel and rel not in {"MANIFEST.json", "SHA256SUMS", ".DS_Store"}
    } | {GENERATOR})
    manifest["files"] = []
    for rel in rels:
        path = ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(path)
        manifest["files"].append({
            "path": rel,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    lines = [f"{sha256(ROOT / rel)}  {rel}" for rel in rels]
    SHA256SUMS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"updated {MANIFEST.name} and {SHA256SUMS.name} for {release_id}")


if __name__ == "__main__":
    main()
