# Upload instructions — v1.7.0-2026-11-25

## 1. Code/data repository

The standalone repository is `p2-deletion-audit-code/`, mapped to:

https://github.com/praswibowoo/repeated-panel-audit-code

It contains all analysis code, binary coverage matrices, audit frames, result JSONs, generated figures, and provenance documentation.

```bash
cd p2-deletion-audit-code
git status
git add .
git commit -m "Release v1.7.0-2026-11-25: target-dependent fixed-evaluation audit"
git push origin main
git tag -a v1.7.0-2026-11-25 -m "Target-dependent fixed-evaluation revision"
git push origin v1.7.0-2026-11-25
```

Verify:

```bash
curl -I https://raw.githubusercontent.com/praswibowoo/repeated-panel-audit-code/v1.7.0-2026-11-25/code/unit_revision_fixed.py
curl -I https://raw.githubusercontent.com/praswibowoo/repeated-panel-audit-code/v1.7.0-2026-11-25/results/unit_revision_fixed/common_contrast.json
curl -I https://raw.githubusercontent.com/praswibowoo/repeated-panel-audit-code/v1.7.0-2026-11-25/data/coverage_matrix.csv
```

## 2. Manuscript submission files

The canonical manuscript files are in `p2-deletion-audit/source/manuscript/ees/`, with figures in `p2-deletion-audit/source/figures/`.

```bash
cd p2-deletion-audit/source/manuscript/ees
make
make check
```

Upload `main.pdf`, `main_supplementary.pdf`, the corresponding LaTeX sources, required figures/style files, and `cover_letter.pdf` through the journal submission system. Do not copy the code/data repository into the manuscript submission.

## 3. Optional archival DOI

Archive the tagged code repository on Zenodo if a software DOI is desired. The existing corpus DOI remains separate:

https://doi.org/10.5281/zenodo.23973301
