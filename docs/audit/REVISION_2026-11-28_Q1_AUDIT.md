# Q1 revision audit — 2026-11-28

## Status

Release `v1.10.0-2026-11-28` prepared for commit, annotated tag, and push. No new DOI minted.

## Locked scientific decisions

- Primary focal scope: single-configuration paper blocks only; multi-configuration papers remain in the background matrix.
- Primary corpus excludes papers with unresolved duplicate pairs, decidable primary/coordinator disagreement, ambiguous scenario identity, unsure status, retained-substitute status, and the B149 one-row boundary.
- Full 117-paper curated corpus retained as sensitivity.
- Estimand harmonized to `R_s = block_drift_s / median(control_drifts_s)`.
- Bstudy and Bblock are exhaustive; Bstudy donors are nested within Bblock on the shared eligible set.
- Overall A−Bstudy remains primary; 2–5/6–10/≥11 strata are exploratory because cut points were not prespecified.
- B084 Cu remains 0 for water scenarios; soil-only Table 2 evidence is annotated as scenario-inapplicable.
- AI-use disclosure retained; bare model-identifier nondisclosure sentence removed; exact prompts deposited in `docs/ai/`.

## Corpus audit

| Quantity | Full curated | Primary |
|---|---:|---:|
| Papers | 117 | 87 |
| Rows | 716 | 555 |
| Configurations | 145 | 93 |
| Single-configuration papers | 98 | 81 |
| Multi-configuration papers | 19 | 6 |
| Populated parameters | 42 | 42 |

Thirty papers are excluded from the full curated corpus. Reason counts overlap: 11 unresolved-pair papers, six coder-disagreement papers, five ambiguous-scenario papers, 13 unsure papers, two retained substitutes, and B149.

The 42 approved cell corrections changed full-curated configuration counts in 15 papers (151 to 145 overall) and changed single/multi status in 11 papers. Within current primary membership, 28 corrections across eight papers changed configurations from 96 to 93 and status in eight papers. Donor counts changed for 36/77 persistent primary single-configuration papers; B052 changed from one donor to zero. All donor pools were recomputed from the corrected matrix.

Blinded-primary/unblinded-coordinator concordance: 37/56 (66.1%; Cohen's κ = 0.17). Among 41 pairs with two decidable labels, agreement was 82.9%; all seven disagreements were primary = different and coordinator = same. Only the primary coder was blinded, and no completed human second-coder file is available.

## Primary 2-D PCA results

| Quantity | n | Median | Conditional range |
|---|---:|---:|---:|
| A, all primary | 87 | 1.31 | 1.01–1.69 |
| Bstudy, eligible single | 74 | 1.02 | 0.82–1.17 |
| Bblock, eligible single | 74 | 1.08 | 0.81–1.32 |
| A−Bstudy | 74 | 0.12 | 0.05–0.29 |
| A−Bblock | 74 | 0.06 | −0.03–0.15 |
| A−C, all | 87 | 0.40 | 0.29–0.47 |

Block-size A−Bstudy medians:

| Rows | Eligible / total | 2-D | 3-D | RMS | PCoA | Full curated |
|---|---:|---:|---:|---:|---:|---:|
| 2–5 | 47 / 47 | −0.02 | 0.00 | 0.01 | 0.11 | 0.05 |
| 6–10 | 20 / 21 | 1.05 | 0.88 | 1.23 | 1.67 | 0.87 |
| ≥11 | 7 / 13 | 1.77 | 1.33 | 1.75 | 1.19 | 1.06 |

The block-size strata are exploratory. All 20 eligible 6–10-row papers have positive contrasts in every fixed sensitivity, but donor pools are small (median four, range 2–7). The ≥11-row result is donor-selected and uses pools of at most four donors.

## Convergence

| Contrast | 100 draws | 500 draws | Median absolute per-paper shift | Maximum shift |
|---|---:|---:|---:|---:|
| A−Bstudy | 0.116 | 0.133 | 0.032 | 0.372 |
| A−Bblock | 0.057 | 0.050 | 0.032 | 0.372 |
| A−C | 0.400 | 0.425 | 0.102 | 1.293 |

The first 100 control drifts match exactly. Exhaustive Bstudy/Bblock estimates are identical across draw counts.

## Checks passed

- `python3 code/build_primary_corpus.py`
- `python3 code/audit_correction_impact.py`
- Primary 2-D, 3-D, RMS, PCoA, balance, simulation, and full-curated runs.
- `python3 code/export_strata.py`
- `python3 code/compare_convergence.py`
- Per-paper ratio-of-medians identities and paired-contrast identities.
- Bstudy subset-of-Bblock checks for every eligible focal paper.
- Primary/full-curated stratum counts, including the B149 boundary outside full-curated strata.
- Shared-Bstudy-set A medians exported separately from all-focal A medians; ≥11-row shared A = 3.16.
- Primary-specific correction impact: 28 cells/eight papers, 96→93 configurations, 36/77 donor-count changes, B052 1→0 donors.
- Correction-impact Bblock counts enumerate every matching configuration and match canonical fixed-audit donor counts for full and primary corpora.
- Stored full-curated/all-paper/full-extraction `rho` values use the 42 populated columns and match loader-recomputed density.
- B084 Cu retained as 0 with soil-only Table 2 adjudication note.
- Cell-audit documentation distinguishes automated text triage from targeted human snippet review.
- Manifest/exclusion traceability: 27 unresolved pair IDs and seven disagreement pair IDs.
- `python3 code/refresh_release_hashes.py`
- `python3 code/verify_package.py` — PASS, 297 manifest files and 122 required analysis files.
- `shasum -a 256 -c SHA256SUMS` — PASS.
- `python3 -m compileall -q code` and `git diff --check` — PASS.
- Manuscript `make check` — PASS; no undefined references/citations, overfull boxes, duplicate destinations, or unresolved `??` in final PDFs.
- Main PDF 21 pages; SI 8 pages; title page 1 page; cover letter 1 page.
- Figure PDFs are byte-identical across the code and manuscript repositories.
- Cross-repository manuscript/data audit: 64/64 checks passed, including PDF text, donor counts/nesting, B084 adjudication, primary correction impact, and active-column `rho`.
- New-review corrections verified: Table S6 full-curated Bstudy n=92; human primary coder separated from AI-assisted review; Table 2 A−C rows split and Panel C widened; C_{-D} notation; natural-log definition; 100/500-draw rationale; exact-size rationale; non-water row composition; synthetic Bstudy/Bblock equivalence; symlog caption; SI terminology/spacing; SAR/Al all-zero markers; V/sulphate tracked-subset notes.
- Rendered Table 2 and SI Tables S1–S7 visually inspected after layout changes; no clipping or overfull boxes.
- Final wording/render pass: source-reported summary scenarios distinguished from analyst-derived pooled summaries; disagreement wording corrected to “were”; Table 2 shortstack left-aligned; Figure S1 now shows 119 retrieved PDFs +3 substitutes →122 analyzed and labels six Crossref-missing checks.

## Deliberately not added

- Option B whole-study control for multi-configuration papers.
- Additional replication-factor simulation sweep.
- Worked single-paper example.
- Git tag/push, pending author approval; no new DOI minted.

## Remaining scientific limitations

- The 27 unresolved pairs were excluded, not human-adjudicated.
- No completed human second-coder file is available; only the primary coder was blinded.
- The corpus remains a purposive methodological testbed, not a probability sample.
- The ≥11-row estimate is based on seven donor-eligible papers and should not be extrapolated to the excluded upper tail.
