# Zenodo metadata update — P2 v1.63

**Record:** `10.5281/zenodo.23973301` (concept DOI `10.5281/zenodo.23552334`)
**Status:** **applied and verified 2026-11-14.** The live description reports **511** documented blanks and carries no "Related publications", "Analysis code", or "Intended uses" section.
**Scope:** this record deposits the corpus **data** only. The manuscript PDF and the code package are not part of it. The code link belongs in the manuscript, not in the record.
**Unchanged:** title, restricted access, CC BY 4.0, deposited files.

## Live description (as verified)

> Derived research data from a purposively sampled corpus of 138 peer-reviewed studies of mangrove and closely coupled estuarine water-quality conditions. This is a general corpus release designed for reuse across multiple publications, not a supplement to a single paper.
>
> The bundle contains:
> - a 44-parameter presence layer (one row per study condition, with reporting flags and per-paper verdicts);
> - a harmonized value layer in canonical units (2,705 records across 3,216 Stage-B extraction cells, with 511 documented blanks: 2,705 = 2,658 numeric + 7 censored + 40 text/flag, and 3,216 − 2,705 = 511; no article text is redistributed);
> - per-row membership in the seven frozen parameter families;
> - the frozen family, unit and verdict rule documents;
> - machine-readable verdict-derivation and unit-conversion logs;
> - criterion-by-criterion tier verdicts for the seven frozen families;
> - a 138-paper corpus manifest with DOIs;
> - a 100-cell extraction verification trace;
> - SHA-256 checksums for every file.

The description ends with the file list. Nothing follows it.

## Notes

- **Version label.** The record page shows **Version v2** (published 2026-11-05); the API returns no version string. Use "v2" in prose.
- **Blank-count arithmetic.** 2,705 = 2,658 numeric + 7 censored + 40 text/flag; 3,216 − 2,705 = 511. The earlier 551 came from 3,216 − 2,658 − 7, which double-counted the 40 text/flag records.
- **Entities.** The stored description uses `&minus;` for the subtraction sign. It renders as "−" in the Zenodo viewer; check the preview if the record is re-edited.
- **Author name:** family name **Veesommai Sillberg**, given name **Chalisa** (matches `CITATION.cff` and the manuscript).

## Checklist

- [x] Description replaced (no "Related publications", "Analysis code", or "Intended uses").
- [x] Description reads **511**, not 551.
- [x] Deposited files unchanged.
- [x] Access setting unchanged (restricted).
