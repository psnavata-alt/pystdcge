# Validation against IFPRI's own model, with home consumption kept (0.3.1, 8 Oct 2026)

**Result: pystdcge's new home-consumption option reproduces IFPRI's standard CGE model.** Both models ran on the same condensed Philippine SAM with households' own produce kept as home consumption. Real GDP and consumption agree within **0.0006 percentage points**, home consumption within **0.0010 pp**, and **239 of 240** compared results within 0.1 pp (with IFPRI-style margins, `margins="split"`). Check **V4**.

## Why

The IFPRI 2023 Philippine SAM records ₱363.7 bn of home consumption: households consuming their own rice, fish, fruit and food. That is 1.8% of all household consumption, and 5.9% for the poorest rural quintile. pystdcge 0.2, the version behind every published result, treated it as if it were bought on the market (`SAM.move_home_consumption_to_market`). In the equation map this was one of the six "simplified" equations: book eq. 18 and 34 (Lofgren, Harris and Robinson 2002, pp. 53 and 57). The route-A validation (`../ifpri/`) therefore moved home consumption to the market for both models.

`CGE(home="separate")` now applies the book's treatment:
- own produce is valued at the producer price PX;
- it pays no trade margin or sales tax and does not compete with imports;
- marketed output = gross output − home use;
- households spend a fixed share of their budget on it (Cobb-Douglas, as for market goods);
- CPI weights cover market purchases only (IFPRI's `cwts`, `1DMODEL_PH.GMS` line 698).

The option is off by default, so published results do not change (check R0).

## What was run

- **Data:** the IFPRI 2023 SAM condensed to the same 9 sectors as in V2, **without** moving home consumption (20 activity → household cells: agriculture ₱239.4 bn, food ₱124.3 bn), with IFPRI's netting rules (`build_home_inputs.py` → `gams_ph/sam_netted_home.csv`).
- **IFPRI's model:** the same altered copy of IFPRI's code as in V2, run with GAMS 54.5 (demo licence; all solves status 1, optimal). IFPRI's own default data for home goods were used:
    - `LESELAS2 = 1` and Frisch −1, i.e. Cobb-Douglas;
    - `SHRHOME` from output shares, exact here because each activity makes one good.
- **The only change** to the model file is in the appended validation report: real GDP and consumption now include home consumption valued at base producer prices (`PXAC0·QHA`), and home consumption (`RHOME`) is reported separately. No IFPRI equation was changed.
- **Shocks and closures:** as in V2 (T1 chemicals import price +10%, T2 construction investment −10%, T3 remittances −10%, T4 farm productivity +5%; closures SAV and INV).

## Results (`out/comparison_home_composite.csv`, `out/comparison_home_split.csv`)

| pystdcge margins | GDP and consumption, largest gap | Home consumption, largest gap | Within 0.1 pp (of 240) | Largest gap |
|---|---|---|---|---|
| default (`composite`) | 0.0044 pp | 0.0068 pp | 230 | 0.509 pp (chemicals output, T1: margins, as in V2) |
| `split` (IFPRI-style) | **0.0006 pp** | **0.0010 pp** | **239** | 0.109 pp (real imports, T1: import units, as in V3) |

## Does it change aggregate results?

Hardly. `examples/home_consumption_sensitivity.py` compares the two treatments: for a construction-investment cut and world oil prices +20%, GDP, consumption and poverty are the same to the decimals shown. The option matters mainly for food-price shocks and the poorest rural households.

## Rerun

1. `py validation/ifpri_home/build_home_inputs.py`
2. In `validation/ifpri_home/gams_ph/`: `gams ph_data.gms`, then `gams 1DMODEL_PH.GMS` (writes `ifpri_results.csv`).
3. `py validation/ifpri_home/compare_home.py split` (or `composite`).

Check V4 reruns step 3 against the saved IFPRI results; GAMS is not needed for the check.
