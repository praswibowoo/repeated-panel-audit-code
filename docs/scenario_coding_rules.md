# Scenario-coding rules for the deletion-unit audit

## Eligible scenario

A scenario is a **source-defined, separately labeled sampling or reporting unit in the source paper**. Eligible labels include a named station, site, season, month, tidal cycle, depth, compartment, or experimental treatment when the source treats it as a distinct unit.

A scenario is not eligible when it is only an analyst-derived aggregation, re-slicing, pooled summary, or management grouping of the same underlying dataset without an independent source label.

Two eligible scenarios may have identical examined-parameter suites. They remain separate scenario rows and may form a repeated within-paper coverage configuration.

## Primary-corpus ambiguity rule

Papers with unresolved scenario identity are excluded from the eligibility-qualified primary corpus and retained only in the full-curated sensitivity corpus. The current exclusion set is B028, B057, B186, B221, and B222.

## Source-verified examples of genuine repeated rows

1. **B004 — SS-Jun-2010 versus SPS-Aug-2010.** The source identifies two rivers (Sungai Sibuti and Sungai Parit Scheme) sampled in June, August, and October 2010. Both scenarios report temperature, pH, dissolved oxygen, conductivity, turbidity, ammoniacal nitrogen, BOD, COD, and TSS. The distinct river-month labels are source-defined, not analyst-derived. Source text: `p1-family-diagnostic/docs/extraction/corpus_texts/B004.txt`, lines 17–22 and 74–103.

2. **B020 — St I versus St VI.** Table 2 reports the same seawater suite for each station: salinity, pH, dissolved oxygen, Fe, Mn, Zn, Cu, Pb, Cd, Ni, and V. Stations are separately labeled sampling units. Source text: `p1-family-diagnostic/docs/extraction/corpus_texts/B020.txt`, lines 440–454.

3. **B115 — pre-monsoon versus post-monsoon.** The source reports a seasonal monitoring series with temperature, pH, conductivity, dissolved oxygen, salinity, sulphate, phosphate, and nitrate. Seasons are separately labeled reporting periods. Source text: `p1-family-diagnostic/docs/extraction/corpus_texts/B115.txt`, lines 91–107 and 154–181.

## Coding procedure

- Record the source label verbatim where possible.
- Do not create scenario rows from pooled averages, derived indices, or management recommendations.
- If the source does not delimit a distinct scenario, code the row as ambiguous and exclude the paper from the primary corpus.
- Keep examined-absent records as `1`; keep not-reported records as `0`.
- Apply the duplicate-pair coding rule separately: `same` means identical examined-parameter suites; `different` means at least one parameter differs; `undecidable` means the source cannot support a decision.
