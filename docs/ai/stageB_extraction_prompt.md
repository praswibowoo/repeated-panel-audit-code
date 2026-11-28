# STAGE-B VALUE EXTRACTION AGENT PROMPT
# (read ONLY: your STB{n}_inputs.txt + STB{n}_template.csv + the listed corpus texts)

## TASK
For each row in your chunk's inputs file, extract the NUMERIC VALUE for each listed
(row x param) cell from the paper's text file `docs/extraction/corpus_texts/<batch_id>.txt`.
Fill the corresponding cell in `STB{n}_template.csv` (ONE template row per cell — do not
add, remove, or reorder rows; never touch other files).

## FILL RULES (per template row)
- `value_as_published` = VERBATIM text of the published cell (e.g. `7.2`, `23-28`, `7.2±0.3`,
  `<0.001`, `0.5 mg/L`). This is the audit anchor — never paraphrase.
- `value` = parsed numeric (mean for ranges/±sd). `value_max` = upper bound ONLY for ranges.
- `censored` = `lt` for `<x` / `ND` / `BDL` / `not detected` / `-`; `gt` for `>x`; else blank.
  For lt: leave `value` blank, keep `value_as_published`; values_available handled downstream.
- `sd_or_note` = `±sd`, `n=...`, or other qualifier from the cell.
- `unit_published` = unit AS PRINTED (e.g., `mg/L`, `ppm`, `µS/cm`, `%sat`). DO NOT convert
  units — conversion happens later in `code/stageB_merge.py` via `harmonize_units.py`.
- `extraction_confidence` = high / medium / low
- `notes` = source location (`Table 3`, `Fig 2`) + any caveat. Special notes:
  - `figure-only` if the value is readable only from a figure/graph, not text/table
  - `not found` if the parameter is genuinely absent after a careful search → leave
    value/value_max blank, confidence low

## KEY RULES
- One scenario row in Stage-A = one row here. Use the scenario's OWN row of values
  (site x season x station as labeled) — do not cross rows.
- If a table reports a range across stations vs a single scenario row, use the row's value
  if separable; otherwise use range with `value_max` + note.
- `%sat` for DO: record as published + note `DO-%sat` (no conversion; flagged separately).
- MPN vs CFU for coliforms: record `unit_published` exactly (`MPN/100mL` / `CFU/100mL`).
- Do NOT read paper prose for verdicts — Stage-B extracts VALUES only.
- Silent-agent protocol: report STATUS only (done/blocker), never counts/decisions in chat.

## OUTPUT
Write back to `STB{n}_template.csv` (python csv module, UTF-8). Preserve header/order.
Every listed cell must be filled (value or censored or not-found note).
