# Upload instructions — v1.8.0-2026-11-26

## 1. Code/data repository

The standalone repository is `p2-deletion-audit-code/`, mapped to:

https://github.com/praswibowoo/repeated-panel-audit-code

It contains all analysis code, binary coverage matrices, audit frames, independent AI-assisted source-review labels, result JSONs, generated figures, and provenance documentation. The default `main` branch has diverged from the release branch, so the annotated tag is the canonical citation target; no force-push is used.

```bash
cd p2-deletion-audit-code
python3 code/verify_package.py
git status
git add .
git commit -m "Release v1.8.0-2026-11-26: whole-study control and fixed-set 3-D audit"
git push origin HEAD
git tag -a v1.8.0-2026-11-26 -m "Whole-study control and fixed-set 3-D audit"
git push origin v1.8.0-2026-11-26
```

Verify:

```bash
curl -I https://raw.githubusercontent.com/praswibowoo/repeated-panel-audit-code/v1.8.0-2026-11-26/code/unit_revision_fixed.py
curl -I https://raw.githubusercontent.com/praswibowoo/repeated-panel-audit-code/v1.8.0-2026-11-26/results/unit_revision_fixed/common_contrast.json
curl -I https://raw.githubusercontent.com/praswibowoo/repeated-panel-audit-code/v1.8.0-2026-11-26/results/unit_revision_fixed/fixed3d_contrast.json
curl -I https://raw.githubusercontent.com/praswibowoo/repeated-panel-audit-code/v1.8.0-2026-11-26/data/duplicate_pair_source_review.csv
```

## 2. Manuscript submission files

The canonical manuscript files are in `p2-deletion-audit/source/manuscript/ees/`, with figures in `p2-deletion-audit/source/figures/`.

```bash
cd p2-deletion-audit/source/manuscript/ees
make
make check
```

Upload `main.pdf`, `main_supplementary.pdf`, the corresponding LaTeX sources, required figures/style files, and `cover_letter.pdf` through the journal submission system.

## 3. Archival DOI

A Zenodo software DOI is recommended after the GitHub tag is verified. The existing corpus DOI remains separate:

https://doi.org/10.5281/zenodo.23973301
