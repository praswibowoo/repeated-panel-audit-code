# Retrospective Blind Anchor — Agreement Report (D79)

| metric | value |
|---|---|
| N | 24 |
| **Operational agreement (GATE)**: 20/24 | **83.3%** (κ=0.647) |
| Strict 3-class agreement (secondary) | 19/24 = 79.2% (κ=0.618) |
| Gate (>90% operational): formal N=24 → REVIEW · **criteria-layer (venue rows excluded, n=22): 20/22 = 90.9% (κ=0.804) → >90%** | companion: original human–AI batch-1 agreement 78.5% (D30) |

## Operational disagreements (adjudicate)
| code | original | domain lead | orig reason | new reason | ADJUDICATED |
|---|---|---|---|---|---|
| A11 | UNSURE | EXCLUDE |  | R1 | **UPHOLD ORIGINAL** (anchor R1 overruled — abstract carries WQ params) |
| A13 | EXCLUDE | INCLUDE | R1 |  | **UPHOLD EXCLUDE** (venue D42 — policy layer) |
| A16 | EXCLUDE | UNSURE | R3 |  | **UPHOLD EXCLUDE R3** (inland freshwater boundary) |
| A17 | EXCLUDE | INCLUDE | R1 |  | **UPHOLD EXCLUDE** (venue D42 — policy layer) |

## Strict-only differences (informational)
| code | original | domain lead |
|---|---|---|
| A23 | UNSURE | INCLUDE |

## Layer note (venue rows)
A13/B010 and A17/B029 carry post-screening predatory-publisher drops (policy layer, D42; notes in `batch1_final_decisions.csv`). The domain lead screened **content-only per criteria v2.0** (as instructed), so these are policy-layer, not criteria-layer, differences. Criteria-layer operational agreement: **20/22 = 90.9% (κ=0.804)**.

## Adjudication recommendations (DS review 2026-10-02 — pending PI/domain confirmation)
| code | item | recommendation | rationale |
|---|---|---|---|
| A11 | B190 Cassiopea distribution, Xel-Há | **Uphold original (UNSURE → retrieved); overrule anchor R1** | Abstract reports salinity / temperature / DO / pH / nutrients — R1 ("no water-column WQ data at all") inapplicable; paper already extracted, contributes F3-nutrient rows |
| A13 | B010 Nyong estuary WQ | **Uphold EXCLUDE (venue D42)** | Content-eligible; excluded by venue policy only — record as policy-layer |
| A16 | B204 Poonthura backwater | **Uphold EXCLUDE R3** | Prior 51-row workshop rationale: inland freshwater system ("code fix R3"); "mangrove" mention incidental |
| A17 | B029 Awat-Awat mangrove WQ | **Uphold EXCLUDE (venue D42)** | Same as A13 |
| A23 | B020 Al-Budhai metals | No action | Operational agreement (UNSURE↔INCLUDE) |

**Impact: zero corpus mutations required** (B190 stays; A13/A17 remain venue-excluded and are already covered by the D43 venue-audit sensitivity layer; A16 stays out). All four operational cases resolve to definite outcomes.

## Adjudication outcomes (2026-10-02 · PI-confirmed)
| code | final decision | note |
|---|---|---|
| A11 | **UNSURE → retrieved (original upheld)** | Anchor R1 overruled on evidence; B190 remains in corpus |
| A13 | **EXCLUDE (venue D42)** | Policy layer; content-eligibility noted for sensitivity (D43) |
| A16 | **EXCLUDE R3** | Inland freshwater boundary; workshop rationale stands |
| A17 | **EXCLUDE (venue D42)** | Policy layer; content-eligibility noted (D43) |

**Post-adjudication: all four cases resolved; corpus state unchanged (zero mutations). Gate metric (pre-adjudication, criteria layer): 20/22 = 90.9% operational (κ=0.804) — PASS.** Screening reliability evidence set complete: batch-1 human–AI 78.5% (D30) + 51-row adjudication (D30–D31) + domain-lead anchor 20/22 (D80–D81).

## Provenance
- Returned file SHA-256: `e7607521614d969aa3240bc282a498ce51150815da463da4dfa8ee5b21756730`
- Content columns verified byte-identical to shipped blind (no tampering); all 24 decisions complete; every EXCLUDE carries a reason code.
- Minor process note: the requested in-file blindness confirmation (note "blind" in A01) is absent — blinding relied on the written instruction.

_Generated 2026-10-02 by code/retro_anchor_agreement.py._
