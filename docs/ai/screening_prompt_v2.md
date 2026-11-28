# FROZEN SCREENING CRITERIA v2.0 — R8c re-pilot + full screening (protocol v1.6)
# Supersedes v1.0 after boundary workshop (pilot round-2 FAIL: 54% raw / 68% collapsed)
# This file + the blind CSV are the ONLY permitted inputs.

## Task
For each row, decide from ONLY title, year, journal, abstract — write back:
- `decision` = INCLUDE | EXCLUDE | UNSURE   (uppercase)
- `reason_code` = R1|R2|R3|R4 when EXCLUDE, else empty
- `note` = optional ≤10 words
Never modify other columns. Never open other files.

## RULE SET v2.0 (four sharpened rules)

**R-A: System boundary (fixes Pattern 1).**
Eligible system = mangrove OR mangrove-linked waters: tidal creeks, backwaters,
estuaries, coastal lagoons, coastal ponds adjacent to mangrove.
NOT eligible: open coast without mangrove linkage, terrestrial/soil-primary studies,
freshwater-only ponds, laboratory/hatchery-only experiments with no field water body.

**R-B: Water column only (fixes Pattern 2).**
Qualifying data = WATER-COLUMN measurements (including water-column metals in µg/L,
dissolved nutrients, DO, pH, salinity, etc.).
NOT qualifying as primary: sediment-only, soil-only, plant/tissue/biota-only
measurements (e.g., metals in sediments or mangrove leaves). Such papers:
EXCLUDE with R1 if no water-column data at all.

**R-C: Side-data papers (fixes Pattern 1 continued).**
If a paper's MAIN topic is organisms, plankton, bacteriology, aquaculture trials, or
GIS/land-suitability, but it reports ≥1 water-column parameter with per-scenario
values — decision = INCLUDE (data extractability governs, not the paper's topic).

**R-D: Reason-code discipline (fixes mislabeling).**
- R1 = no water-column WQ data at all (incl. sediment/soil/plant-only papers, reviews,
  modeling-only, methods-only)
- R2 = water-column data exists but single aggregate value, no scenario split
- R3 = system boundary fail (open coast standalone, terrestrial, lab/hatchery-only)
- R4 = no reasonable path to full text
- Year floor (<2005): EXCLUDE with R1 + note "year<2005" — EXCEPT ecotoxicology
  (LC50/mortality/survival designs) which are eligible any year.

## Decision operational meaning
INCLUDE and UNSURE both mean **retrieve full text** (gate metric = operational
collapse: {INCLUDE,UNSURE} vs {EXCLUDE}); UNSURE still useful for uncertainty notes.
