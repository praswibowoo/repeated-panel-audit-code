# Release preparation — v1.10.0-2026-11-28

Status: release candidate prepared; commit, annotated tag, and push are authorized for `v1.10.0-2026-11-28`.

## Verification before tagging

```bash
python3 code/build_primary_corpus.py
python3 code/unit_revision_fixed.py --draws 100
python3 code/fixed3d_sensitivity.py
python3 code/pcoa_fixed.py --draws 100
python3 code/rms_fixed_sensitivity.py
python3 code/control_balance_fixed.py
python3 code/render_fixed_values.py
python3 code/make_fig_paired_contrast.py
python3 code/make_fig_prisma.py
python3 code/export_strata.py
python3 code/compare_convergence.py
python3 code/refresh_release_hashes.py
python3 code/verify_package.py
shasum -a 256 -c SHA256SUMS
```

The 500-draw run is optional for routine reproduction and is deposited as
`results/unit_revision_fixed/convergence_500.json`.

## Author-approved release actions

Only after the working tree and audit are approved:

```bash
git add .
git commit -m "Release v1.10.0-2026-11-28: eligibility-qualified primary corpus and exhaustive nested controls"
git tag -a v1.10.0-2026-11-28 -m "Eligibility-qualified deletion-unit audit"
git push origin HEAD
git push origin v1.10.0-2026-11-28
```

Then verify the raw GitHub URLs for `code/unit_revision_fixed.py`,
`data/coverage_matrix_primary.csv`, and
`results/unit_revision_fixed/common_contrast.json`.

## Manuscript package

Upload `main.pdf`, `main_supplementary.pdf`, `cover_letter.pdf`, corresponding
LaTeX sources, figures, and style files. The manuscript links to the immutable
`v1.10.0-2026-11-28` code-release tag.
