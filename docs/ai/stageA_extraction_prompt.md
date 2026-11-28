# STAGE-A EXTRACTION AGENT PROMPT
# (read this + the listed text files + the template CSV — nothing else)

## TASK
For each paper in the chunk:
1. Read the text file (pdftotext -layout output).
2. Identify the scenario structure (sites/seasons/stations/standards).
3. For EACH scenario row, set the PRESENCE of each water-quality parameter:
   - `Y` = parameter reported in the paper (value may or may not be numeric; even "present" counts)
   - `NE` = measured but not detected / below detection limit
   - blank = NOT reported for this scenario (NR)
4. `verdict` = STRICT 11-class vocabulary ONLY (Optimal/Favorable/Stable/Mild stress/Stressful/Harmful/Degraded/Lethal / Mortality risk/Restoration target/Reference standard/Reference baseline/Natural stress (non-polluted)).
   - The paper's own classification phrasing (WQI classes, trophic state, "good/fair/polluted") goes to `cause_effect_note` prefixed "[paper-class: ...]".
   - If the paper states no class, leave verdict EMPTY (verdicts are derived uniformly at Stage-B from values via the rubric).
5. `scenario` = short label (e.g., "St1-monsoon", "SiteA", "WHO limit")
6. `scenario_type` = site / season / station / depth / standard / other
7. `source_table_ref` = page + table number where found
8. `batch_id` + `paper_doi` on the paper's FIRST row only

## KEY RULES
- ONE ROW = ONE SCENARIO (site × season, station, etc.)
- Default 5 rows per paper; INSERT more if needed (batch_id/paper_doi blank on added rows)
- Only fill cells with Y/NE/blank — do NOT extract numeric values (Stage-B does that)
- Apply criteria v2.0 rules (R-A system boundary / R-B water-column / R-C side-data / R-D codes)
- If a paper's WQ data is only in FIGURES (not tables), still mark Y and note "Fig X" in source_table_ref

## OUTPUT
Write back to the SAME template CSV (python csv module). Preserve header/order; only
decision columns change (scenario rows added/modified). All 5 default rows per paper
may need more — insert as needed.


## LESSON (D47, 2026-09-30)
Agents originally wrote paper-native classifications into `verdict` (533 rows, 150 unique strings). Fixed by normalization pass; vocabulary enforcement is now explicit. Always run text sanity: rescued PDFs may be cover/policy pages only (B171 case).
