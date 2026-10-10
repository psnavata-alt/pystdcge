# Cross-check: pystdcge against Hosoe et al.'s standard CGE model, as ported to Python by humans

**Run on 8 October 2026.** The options this comparison needs are in the package's own engine (`pystdcge/cge.py`: `gov="cd"`, `inv="value_shares"`, and the exact Cobb-Douglas case), off by default; test V5 reruns the comparison.

## What was compared

| | Reference | pystdcge |
|---|---|---|
| Model | Hosoe, Gasawa and Hashimoto's **standard CGE model** ("A Standard CGE Model in Ch. 6", GAMS Model Library `stdcge.gms`, SEQ=276; Hosoe et al., *Textbook of Computable General Equilibrium Modelling*, 2010, List 6.1, p. 106) | pystdcge's static CGE engine (`pystdcge/cge.py`; first run on a copy of live 0.3.0, rerun on live 0.3.1) with the options below |
| Code | **pycge** (Juan Fung, U.S. National Institute of Standards and Technology, and Charles Burtwistle), "Pyomo port of stdcge.gms from GAMS Model Library", July 2017: human-written, years before AI coding tools. Source: github.com/juanfung/pycge | Python, written with AI assistance |
| Solver | Ipopt 3.14.20 (COIN-OR's official Windows build, open source) through Pyomo 6.10.1 | SciPy `optimize.root` |
| Data | The 10-account SAM of `stdcge.gms` (2 goods, 2 factors, 1 household, government, investment, rest of world). pycge's data files are identical to the GAMS file, cell for cell | The same SAM in pystdcge's account names (built in `compare_hosoe.py`; rows equal columns exactly) |
| Experiment | **Abolish import tariffs**: the textbook's own simulation (`stdcge.gms` line 310) | The same (`tm_scale` = 0) |

**pycge is checked against the GAMS file first:** all 24 equations, the objective and the calibration formulas match `stdcge.gms` line by line, with Armington and transformation elasticities of 2. `stdcge.gms` (not redistributed here) was downloaded on 8 Oct 2026 from https://www.gams.com/latest/gamslib_ml/stdcge.276, SHA-256 `180e7140…fdc255`.

**One solver detail.** GAMS's solvers accept the one redundant equation that Walras' law creates; Ipopt does not ("too few degrees of freedom"). The run therefore sets aside the balance-of-payments equation and checks afterwards that it still holds: residual 6e-14 at the base and 1.5e-12 after the shock. This does not change the model.

## Making pystdcge follow Hosoe's rules

Three apparent differences turned out to be the same economics written differently, so they needed nothing:
- household saving (a share of gross income in Hosoe; a share of after-tax income in pystdcge, identical with a flat tax);
- the production tax (Hosoe's tax on output equals pystdcge's activity tax);
- capital income (Hosoe pays it straight to the household; here it passes through pystdcge's "enterprise" account unchanged).

Four things differed, so `engine_copy/pystdcge/cge.py` adds them, **all off by default**:

| Hosoe's rule | pystdcge default | Added (opt-in) |
|---|---|---|
| Government spends fixed **value shares** of revenue net of a fixed-rate saving | Fixed **real** consumption; saving adjusts | `gov="cd"` (one extra unknown, the spending level, and one equation) |
| Investment = fixed **value shares** of total savings | Fixed real proportions | `inv="value_shares"` |
| Cobb-Douglas value added (elasticity exactly 1) | Refused (the CES formula divides by zero) | `sigma_va=1.0` uses the closed-form Cobb-Douglas limit |
| No trade margins | Margin mix computed as 0/0 | Guard: no margins gives a zero margin mix |

**With the options off, the copy is the live pystdcge:** on the 2023 Philippine SAM, in all three closures, for a construction-investment cut and a three-part shock, every variable is identical: difference **exactly 0.0** (`check_defaults_output.txt`).

## Results (`compare_hosoe_output.txt`, `hosoe_comparison.csv`)

- **pystdcge reproduces Hosoe's SAM** at the base (largest gap 1.4e-14).
- **After abolishing tariffs, all 42 compared results agree to machine precision:**
    - output, consumption, government and investment demand, exports, imports, composite and domestic goods, value added, factor use;
    - the prices of goods, factors and foreign exchange, relative to the wage (Hosoe's numeraire);
    - taxes, savings and utility.
- Largest level gap **7.0e-13**; largest percentage-change gap **5.3e-12 points**.
- Welfare (Hicksian equivalent variation, Hosoe's List 8.2): **1.145 in both**.
- The one level difference is units, not a disagreement. Hosoe's producer price `pz` is per unit of output net of tax (base 1); pystdcge's is per unit of gross output (base 73/78 = 0.9359). Their percentage changes agree to 6e-13.
- **The new Cobb-Douglas branch is itself checked:** pystdcge's unmodified CES code at elasticities 0.9999 and 1.0001 lands within 1.1e-6 of the same answer from both sides.

Selected results (percentage change after abolishing tariffs; pycge = pystdcge in every row):

| | Bread (BRD) | Milk (MLK) |
|---|---|---|
| Output | +2.169 | −1.380 |
| Household consumption | +1.961 | +2.510 |
| Government consumption | −6.850 | −6.349 |
| Exports | +17.929 | +12.458 |
| Imports | −1.082 | +18.848 |

Exchange rate (relative to the wage): +6.282%. Government saving: −8.597%.

## What this shows, and what it does not

- **Shows:** pystdcge's core building blocks give exactly the same numbers as an independent, human-written implementation of a published textbook model:
    - production with an output tax;
    - export supply (CET) and import demand (Armington) with tariffs;
    - household income, tax, saving and spending;
    - government revenue;
    - the balance of payments and factor markets;
    - the numeraire and the solver.
- **Does not show:** the IFPRI-specific features that Hosoe's teaching model lacks (several households, trade margins, home consumption, LES demand); those are covered by the IFPRI check (V2, V3, V4). It does not show that the model's elasticities or closures are right for the Philippines, and it does not replace an outside human reviewer (verification Phase 5).
- **Two of the four options are new code** (`gov="cd"`, `inv="value_shares"`): they are tested here against pycge and, since 0.3.1, are in pystdcge's engine (off by default; check R0 shows the published results are unchanged).
- **GAMS itself was not run** (licence question). pycge's equations were checked against the GAMS file by reading it. The textbook's printed tables were not compared: only Palgrave's 26-page preview is on file, not the book.

## How to rerun

1. Download pycge (github.com/juanfung/pycge) into a folder `dl_pycge/`. Download Ipopt's official Windows build (github.com/coin-or/Ipopt/releases, `Ipopt-3.14.20-win64-msvs2022-md.zip`) and unzip it into `dl_ipopt/ipopt/`, both under one working folder W. Install Pyomo and dill (`py -m pip install --user pyomo dill`).
2. `py -P run_pycge.py W`: solves pycge's `stdcge` (base and no tariffs) and writes `W/hosoe/pycge_results.json` (the run of 8 Oct is kept here).
3. `py -P compare_hosoe.py`: builds the SAM, runs pystdcge's own engine and prints the comparison (it reads `pycge_results.json` from its own folder).
4. `py -P check_defaults.py "<this folder>\engine_copy\pystdcge"`: proves the morning copy equals pystdcge 0.3.0 with the options off (for the engine itself, check R0 does this).

Downloaded code (pycge) is unzipped into its own folder and run with `py -P`.
