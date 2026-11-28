# FROZEN SCREENING CRITERIA — R8b AI Screener (protocol v1.5, prompt v1.0)
# This file + pilot_blind_B.csv are the ONLY permitted inputs for screener B.

## Task
For each of the 50 rows (P001–P050) in `pilot_blind_B.csv`, decide using ONLY the
row's `title`, `year`, `journal`, `abstract` columns and the criteria below.

## Output (write back to the SAME file, same rows/columns)
- `decision` ∈ {INCLUDE, EXCLUDE, UNSURE}  (uppercase; never empty)
- `reason_code` = R1|R2|R3|R4 when decision=EXCLUDE, else empty
- `note` = optional short reason (≤10 words)
- Do NOT modify any other column. Do NOT sort/delete rows. Do NOT open any other
  file (especially pilot_key.csv, pilot_blind_A.csv, tier/flag data — blindness).

## Eligibility — INCLUDE if plausibly could contribute a row to a mangrove
water-quality matrix (screening is about plausibility, not certainty):
- I1 system: mangrove, or estuarine/coastal/lagoon waters linked to mangroves
- I2 measured numeric water-quality data (NOT modeling-only, NOT review/opinion,
  NOT pure microbiology/molecular ecology, NOT remote-sensing-method papers)
- I4 ≥2 scenarios (sites / seasons / stations / treatment levels / standards)
  OR a regulatory limit table
- Publication language with abstract in English; year ≥2005
  EXCEPTION: ecotoxicology (LC50/mortality/survival) papers may pre-date 2005.

## EXCLUDE with reason code:
- R1 no data — no measured numeric WQ values (review, editorial, modeling-only,
  non-WQ biology/microbiology, methods-only)
- R2 no per-scenario split — single aggregate value only, no site/season/stage/
  standard breakdown
- R3 wrong system — not mangrove/estuarine-connected (open ocean, river-only
  with no coastal connection, freshwater pond, terrestrial)
- R4 not accessible — no reasonable path to full text (no DOI and no locator)

## UNSURE — genuine doubt from thin/absent abstract or borderline criteria.
(UnSURE is treated as include-for-retrieval; use it freely — do not guess.)

## Known context (applies equally, hidden from other screener):
- Toxicology rows (LC50/mortality) are eligible regardless of year (era=classic).
- Regional-language papers with English abstracts are eligible.
