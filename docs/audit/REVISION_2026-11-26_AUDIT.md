# Revision audit — 2026-11-26

Release: `v1.8.0-2026-11-26`.

## Implemented changes

- Added exhaustive whole-study donor control Bstudy for single-configuration focal studies.
- Replaced an initial sampled Bstudy implementation after draw-stream sensitivity showed material Monte Carlo variability; exhaustive enumeration is now the released primary estimator.
- Made Bstudy the primary study-unit-matched comparison; retained Bblock as a sampled configuration-donor sensitivity.
- Enumerated all eligible Bstudy donors to remove donor-draw Monte Carlo error from the primary control.
- Added fixed-set 3-D PCA sensitivity and reported attenuation explicitly.
- Added Bblock to the fixed-set clustered synthetic benchmark using an independent random-number stream so A/C draws remain comparable.
- Added two-level bootstrap values to SI Table S2.
- Separated fit weighting from control benchmark in Methods, Discussion, and Table 3.
- Replaced expectation-only perturbation argument with exact covariance decomposition plus fluctuation scaling.
- Reframed “artifact” as a control-dependent descriptive effect.
- Added block-size stratification and per-study donor-balance distributions.
- Reported all screening/claim-audit rounds, including gate failures and retrospective anchor results.
- Deposited an independent AI-assisted blinded source review of 83 unordered duplicate pairs; 37/38 matrix-identical pairs were reviewed same and one undecidable; 16/45 matrix-distinct pairs were reviewed same. All false-distinct pairs occurred in multi-configuration studies. Human adjudication remains pending and is explicitly disclosed.
- Clarified that three substitutes were added but only B238/B240 remained after B239 single-row curation.
- Removed revision-scar language and internal screener session identifiers.
- Added evidence-and-gap-map citations.
- Updated code/data release to v1.8.0-2026-11-26.

## Verification

- Python compilation: pass.
- Frozen duplicate-pair frame: 100 records / 83 unique unordered pairs; AI-assisted review labels present.
- Exhaustive Bstudy output matches an independent enumeration script for all 91 eligible studies (maximum absolute difference 0).
- Source-review spot checks: B153 common station panel, B080 common station panel, and B186 undecidable depth-specific water quality supported the deposited labels.
- `verify_package.py`: PASS (74 files).
- `SHA256SUMS`: all 223 manifested files verified.
- Numerical manuscript/SI consistency script: PASS.
- Figure parity between code and manuscript repositories: PASS.
- `make check`: clean; main 21 pages, SI 9 pages, title page 1 page; no undefined references/citations or overfull boxes in final logs.
- No unresolved placeholders or stale primary claims remain.
