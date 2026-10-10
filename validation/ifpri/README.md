# Validation against IFPRI's own CGE model

**Result (2 Oct 2026, about 4:35 AM): pystdcge reproduces IFPRI's standard CGE model on the same Philippine data.** Real GDP and real household consumption agree within **0.005 percentage points** (largest gap 0.0043 pp), for four test shocks under two closures. Of all 232 comparisons (GDP, consumption, trade, exchange rate, 5 factor prices, 9 industry outputs, 10 household groups), **75% agree within 0.01 pp and 96% within 0.1 pp**. The largest gap (0.51 pp, chemicals output under the import-price shock) is in the one place the two models are built differently (trade margins), see below.

## What was compared

- **IFPRI's model:** IFPRI's own GAMS code, *Extended Standard Recursive Dynamic CGE, Version 2.00* (July 2005; Thurlow's extension of Lofgren, Harris and Robinson 2002), GNU GPL v2, from the GitHub copy `uw-windc/IFPRI_model` (download it to rerun step 2). Solved one period (static) with **GAMS 54.5.0, demo licence**, PATH solver (MCP). Model size 514 equations and 514 variables (demo limit 1,000).
- **Data:** the IFPRI 2023 Philippine SAM condensed to 9 sectors (agriculture; mining; food and beverages; chemicals and petroleum; other manufacturing; utilities; construction; trade and transport; other services) and all 10 household groups (`build_condensed_sam.py`), with home consumption moved to market and IFPRI's own netting rules applied (`build_ifpri_inputs.py` → `gams_ph/sam_netted.csv`). **Both models use this same SAM.**
- **Base replication:** IFPRI's model reproduces the SAM with **0 solver iterations** (largest equation error 3e-9); real GDP ₱26,160.6 bn = the SAM's GDP. pystdcge reproduces it to 3e-11.
- **Shocks:** T1 world import price of chemicals and petroleum +10%; T2 real construction investment −10%; T3 remittances to households −10%; T4 agricultural productivity +5%.
- **Closures:** SAV (saving rates fixed, investment adjusts) and INV (real investment fixed, household saving rates adjust; IFPRI's enterprise saving rate held fixed via `mps01('ent') = 0`, as in pystdcge). Both: CPI numeraire, flexible exchange rate, fixed foreign savings, fixed real government consumption and tax rates, full employment, mobile factors.

## Settings that make the two models comparable (IFPRI side, all in data or run settings; no IFPRI equation changed)

One trading region (rest of world); no factor nests; one government function; Leontief top-level technology; household demand LES with all expenditure elasticities 1 and Frisch −1, which is exactly Cobb-Douglas; elasticities 0.8 (value added), 2.0 (Armington), 2.0 (CET); factor quantities = SAM values. Altered IFPRI files are marked as such (GPL condition 2): `gams_ph/1MODEL_PH.DAT`, `gams_ph/1DMODEL_PH.GMS` (data file swapped, validation block appended at the end).

## Main results (percent change from base)

| Closure | Shock | Real GDP: IFPRI | Real GDP: pystdcge | Real consumption: IFPRI | pystdcge | Exchange rate: IFPRI | pystdcge |
|---|---|---|---|---|---|---|---|
| SAV | T1 import price chem. +10% | −0.1453 | −0.1476 | −1.0009 | −0.9995 | −0.5314 | −0.4830 |
| SAV | T2 construction inv. −10% | 0.0264 | 0.0264 | −0.0212 | −0.0211 | 0.0697 | 0.0688 |
| SAV | T3 remittances −10% | −0.0462 | −0.0463 | −0.6824 | −0.6820 | 0.2199 | 0.2164 |
| SAV | T4 agri productivity +5% | 0.4196 | 0.4163 | 0.5450 | 0.5455 | 0.5350 | 0.5178 |
| INV | T1 | −0.1473 | −0.1496 | −1.1257 | −1.1253 | −0.5237 | −0.4752 |
| INV | T2 | 0.0555 | 0.0557 | 1.9158 | 1.9160 | −0.0439 | −0.0431 |
| INV | T3 | −0.0486 | −0.0487 | −0.8324 | −0.8325 | 0.2278 | 0.2243 |
| INV | T4 | 0.4195 | 0.4161 | 0.5378 | 0.5335 | 0.5354 | 0.5185 |

Full table: `out/comparison_pystdcge_vs_ifpri.csv`.

## The remaining difference: trade margins (explanation to be confirmed)

The largest gaps are all under T1: chemicals output +5.52% (pystdcge) vs +5.01% (IFPRI), other manufacturing −4.09% vs −3.85%, imports −2.73% vs −2.56%. Likely cause: **IFPRI charges trade and transport margins separately on imports and on domestic sales**, so the margin is part of the import and domestic prices between which buyers choose, diluting the import-price rise and reducing substitution towards domestic chemicals. **pystdcge adds margins after that choice** (on the composite good). This is a known simplification (`docs/model.md`, pystdcge "simplified to fit the Philippine SAM"). To confirm: add IFPRI-style margins to pystdcge as an option, or rerun both with margins set aside, and check that the gap closes.

## How to rerun

1. `py validation/ifpri/build_condensed_sam.py` (condensed SAM, pystdcge test results)
2. `py validation/ifpri/build_ifpri_inputs.py` (IFPRI inputs), then in `validation/ifpri/gams_ph/`: `gams ph_data.gms` and `gams 1DMODEL_PH.GMS` (writes `ifpri_results.csv`)
3. `py validation/ifpri/compare.py` (comparison table)

Test **V2** in `tests/` reruns step 3 against the saved IFPRI results (no GAMS needed).

## Next

- Confirm the margin explanation (above).
- Further benchmarks: a Julia/MPSGE version at full 41-sector size, and the World Bank's MANAGE-WB model.
- A full-size IFPRI run (41 sectors) needs more than the demo licence (community licence is academic only; or a partner).

## Trade margins option (7 Oct 2026, verification Phase 3)

pystdcge 0.3 now has `CGE(margins="split")`. It applies IFPRI's treatment: the margin is part of the import price and the domestic demand price, before buyers choose between them. Run `py validation/ifpri/compare.py split`. Results (`out/comparison_pystdcge_vs_ifpri_split_margins.csv`, check V3):

| | Default (`composite`) | `split` (IFPRI-style) |
|---|---|---|
| Real GDP and consumption, largest gap | 0.0043 pp | **0.0006 pp** |
| Results within 0.01 pp / 0.1 pp (of 232) | 175 / 222 | **200 / 231** |
| Largest gap anywhere | 0.509 pp | **0.109 pp** |

**The margins explanation is confirmed:** the gap closes when pystdcge charges margins as IFPRI does. The small remainder appears to be measurement conventions, not model behaviour:
- **Nominal prices (exchange rate, factor prices):** under T1 all nominal prices differ by the same ~0.054 pp. IFPRI's CPI numeraire weights each good by its base composite price `PQ0`, which includes sales tax (lines 643, 711), so the index tilts towards heavily taxed goods. pystdcge's base prices are all 1. Real quantities are unaffected: sector outputs within 0.002 pp, household consumption within 0.003 pp.
- **Real imports (up to 0.11 pp):** IFPRI measures import quantities in purchaser-price units (`PM0 = PDD0`, lines 617-632), pystdcge at world prices, so the unweighted sum of imports weights sectors differently.

**Both explanations confirmed, 8 Oct 2026** (`matched_cpi_test.py`, `out/matched_cpi_test.csv`). No model was changed: a CGE is homogeneous in prices, so pystdcge's solution was re-expressed with IFPRI's CPI weights, and its import quantities in IFPRI's purchaser-price units (IFPRI's base prices recomputed from the same SAM with IFPRI's formulas). Largest gaps, with `margins="split"`:
- nominal results (exchange rate, 5 factor prices; 48 values): **0.0543 pp before, 0.0009 pp after**;
- real imports (8 values): **0.1089 pp before, 0.0003 pp after**.

So every remaining difference between the two programs is a measurement convention, not model behaviour. Sector outputs and household consumption already agreed within 0.003 pp.
