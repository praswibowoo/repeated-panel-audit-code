# Upload instructions — v1.9.0-2026-11-27

## 1. Code/data repository

Repository: https://github.com/praswibowoo/repeated-panel-audit-code

Release branch: `revision/q1-scope`

```bash
cd p2-deletion-audit-code
python3 code/verify_package.py
shasum -a 256 -c SHA256SUMS
git status
git add .
git commit -m "Release v1.9.0-2026-11-27: approved duplicate-pair corrections and analysis rerun"
git push origin HEAD
git tag -a v1.9.0-2026-11-27 -m "Approved duplicate-pair corrections and full analysis rerun"
git push origin v1.9.0-2026-11-27
```

Verify:

```bash
curl -I https://raw.githubusercontent.com/praswibowoo/repeated-panel-audit-code/v1.9.0-2026-11-27/code/unit_revision_fixed.py
curl -I https://raw.githubusercontent.com/praswibowoo/repeated-panel-audit-code/v1.9.0-2026-11-27/results/unit_revision_fixed/common_contrast.json
curl -I https://raw.githubusercontent.com/praswibowoo/repeated-panel-audit-code/v1.9.0-2026-11-27/data/coverage_matrix.csv
```

## 2. Manuscript repository

Repository: https://github.com/praswibowoo/repeated-panel-audit

Release branch: `revision/q1-scope`

```bash
cd p2-deletion-audit
git add source/figures/fig_paired_contrast.pdf source/manuscript/ees
git commit -m "Release v1.9.0-2026-11-27: revised manuscript and SI"
git push origin HEAD
git tag -a v1.9.0-2026-11-27 -m "Revised manuscript and SI for approved matrix corrections"
git push origin v1.9.0-2026-11-27
```

Build check:

```bash
cd source/manuscript/ees
make check
```

## 3. Submission files

Upload `main.pdf`, `main_supplementary.pdf`, the corresponding LaTeX sources, required figures/style files, and `cover_letter.pdf` through the journal submission system.

## 4. Archival DOI

A Zenodo software DOI is recommended after the GitHub tags are verified. The existing corpus DOI remains separate:

https://doi.org/10.5281/zenodo.23973301
