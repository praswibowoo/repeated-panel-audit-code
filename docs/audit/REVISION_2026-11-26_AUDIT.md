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
- Deposited an independent AI-assisted blinded source review of 83 unordered duplicate pairs; 37/38 matrix-identical pairs were reviewed same and one undecidable; 16/45 matrix-distinct pairs were reviewed same. Eight of those 16 conflict with prior P1 human-verified cell corrections already incorporated in the P2 matrix. All are treated as AI-flagged potential false-distinct pairs, not confirmed errors. Human pair-level adjudication remains pending.
- Clarified that three substitutes were added but only B238/B240 remained after B239 single-row curation.
- Removed revision-scar language and internal screener session identifiers.
- Added evidence-and-gap-map citations.
- Prepared blind human-adjudication workbooks: recommended eight-column primary sheet, full primary/secondary sheets, primary-only and second-only workbooks, and a coordinator key with prior P1 human evidence separated from AI labels.
- Added Excel date-serial conversion to the simple-workbook extractor and detailed pending/disagreement identifiers to the importer summary.
- Added a reproducible all-row adjudication-report builder with exact matrix differences, row-level flags, and required actions.
- Processed the completed 2026-11-27 primary submission: all 56 relation labels populated; 34 same, 7 different, 15 undecidable. Strict structural import passes. Produced all-row processing and coordinator-review reports without changing the matrix or manuscript estimates.
- Completed a proposed source-based coordinator review of all 56 pairs: 53 same, 3 undecidable, 19 changed primary labels independently rechecked, and 42 pending cell corrections. Four proposed cells conflict with prior accepted human corrections. Provisional in-memory configuration impact is 151 to 145 across 15 papers; no matrix or analysis output was changed.
- Updated code/data release to v1.8.0-2026-11-26.

## Verification

- Python compilation: pass.
- Frozen duplicate-pair frame: 100 records / 83 unique unordered pairs; AI-assisted review labels present.
- Exhaustive Bstudy output matches an independent enumeration script for all 91 eligible studies (maximum absolute difference 0).
- Source-review spot checks: B153 common station panel, B080 common station panel, and B186 undecidable depth-specific water quality supported the deposited labels.
- `verify_package.py`: PASS (106 files).
- Adjudication-package audit: PASS (recommended eight-column primary sheet, 56 primary / 62 second-coder assignments, six QC pairs, coder-workbook blinding, 56 source-PDF hyperlinks, source availability, and 10 mapped prior corrections confirmed zero in P2 matrix).
- Partial primary submission processed: 31/56 pairs; 19 same, 5 different, 7 undecidable; 15 matrix matches, 9 matrix disagreements, 7 undecidable. Five prior-human-evidence conflicts and eight non-correction notes flagged. No matrix or manuscript estimates changed.
- Current primary submission processed: 56/56 labels; 34 same, 7 different, 15 undecidable; 25 matrix matches, 16 matrix disagreements, 15 undecidable. No missing evidence or coder metadata. Seventeen non-correction notes, five prior-human-evidence conflicts, and 19 automated source-review disagreements flagged; 39 rows require coordinator review. Strict structural import passes. No matrix or manuscript estimates changed.
- Proposed coordinator review validated: 56 source-review rows, 19/19 blinded changed-label agreements, 42 unique pending cell corrections, and all 53 proposed same pairs matrix-identical after in-memory corrections. Four proposed cells conflict with prior accepted human corrections. No correction was approved or applied.
- Importer mock tests: PASS for simple primary CSV, two-coder agreement, primary-only provisional import, coordinator resolution, forced disagreement, and partial input with missing metadata.
- `SHA256SUMS`: all 260 manifested files verified.
- Numerical manuscript/SI consistency script: PASS.
- Figure parity between code and manuscript repositories: PASS.
- `make check`: clean; main 21 pages, SI 9 pages, title page 1 page; no undefined references/citations or overfull boxes in final logs.
- No unresolved placeholders or stale primary claims remain.
