# The model

## 1. Idea

A CGE model is a social accounting matrix (SAM) brought to life. The SAM shows one year's flows; the model adds behaviour: industries choose inputs to minimise cost, households spend their income, buyers choose between imported and domestic goods, producers choose between exporting and selling at home. When something changes (a world price, a tax, spending), every price and quantity adjusts until all markets clear and every peso paid is a peso received. Unlike a fixed-price multiplier, the CGE lets prices move and respects limits on labour and capital, so it captures crowding out, substitution and trade responses.

## 2. Structure (`pystdcge/cge.py`)

The model follows the IFPRI standard CGE model (Lofgren, Harris and Robinson 2002). `docs/equations.md` maps all 48 published equations to the code.

| Block | Assumption | Parameters |
|---|---|---|
| Production | Value added and intermediate inputs in fixed proportions (Leontief); intermediates in fixed proportions | `ica`, `iva` |
| Value added | CES over low-, medium- and high-skill labour, land and capital | `sigma_va` |
| Outputs | Activities produce commodities in fixed shares (the SAM's make matrix) | `theta` |
| Exports | Output split between exports and domestic sales (CET); world prices given | `omega_t` |
| Imports | Armington CES composite of imported and domestic goods | `sigma_q` |
| Re-exports | Where exports exceed domestic output (electronics in the Philippine SAM), the excess passes through at world prices | `rex` |
| Margins | Trade and transport services per unit of the composite good (default), or charged separately on imports, exports and domestic sales as in the book (`margins="split"`) | `icq`, `sm`, `icx` |
| Taxes | Tariffs, sales taxes, a capital tax (2023 SAM) or activity tax (2018 SAM), direct taxes, at fixed rates | `tm`, `tq`, `tf`, `ta`, `tins`, `te` |
| Households (10) | Income from factors, enterprises, government and abroad; fixed tax and saving rates; Cobb-Douglas demand (default) or LES (`les=`); home consumption at market (default) or as own produce (`home="separate"`) | `mps`, `beta` |
| Government | Fixed real consumption and transfers; saving adjusts (or Cobb-Douglas value shares, `gov="cd"`) | `qg`, `trg_h` |
| Rest of world | Foreign savings fixed in foreign currency (except in the Keynesian closure) | `fsav` |

## 3. Calibration

All parameters come from the SAM, with benchmark prices set to 1 except composite prices, which carry taxes and margins. Shares and tax rates are read directly (e.g. tariff rate = tariff revenue / imports); CES and CET share and shift parameters are solved so that, at benchmark prices, the model reproduces every SAM flow (test C2: largest cell gap about 1e-7 ₱ bn). The only numbers not from the SAM are the elasticities (`docs/parameters.md`). The 2018 SAM, published in whole billions, is first balanced by weighted least squares that keeps empty cells empty and signs unchanged (`SAM.balance`).

## 4. Closures

A closure says which variables adjust to keep the model consistent; results can change sign across closures. Three are built in:

| Closure | Code | What adjusts | Typical use |
|---|---|---|---|
| Long run (investment-driven) | `CGE.from_sam()` | Wages and rents (full employment); household saving rates keep savings = investment; exchange rate | Structural questions, multi-year horizons |
| Savings-driven | `closure="savings"` | Investment adjusts to available savings | Capital-flow and saving questions |
| Short run (Keynesian) | `closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed"` | Employment of low- and medium-skill labour at fixed real wages; capital fixed by industry; exchange rate fixed (numeraire); foreign savings adjust | Spending shocks within a year |

Two lessons: an investment-driven closure with full employment lowers household saving rates when investment falls, which props up consumption; and a Keynesian closure anchored only on the nominal wage can let all other prices fall implausibly, so the built-in version anchors the exchange rate. Always ask whether results are plausible, not only whether the solver converged.

## 5. Running it

```python
from pystdcge.cge import CGE
m = CGE.from_sam(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
base = m.solve()
sim = m.solve({"qinv_scale": {"ccons": 0.9}})       # construction investment -10%
print(m.compare(base, sim))                          # GDP, consumption, trade, wages, employment, households
print(m.gdp(sim))                                    # nominal GDP by expenditure and income, real GDP
assert abs(sim["WALRAS"]) < 1e-6                     # the accounts must close
```

Shock keys (`CGE.make_shocks`): `qinv_scale`, `qg_scale`, `pwm_scale`, `pwe_scale`, `tm_scale`, `tq_scale`, `tfp_scale`, `qfs_scale`, `remit_scale`, `trg_scale`, `trg_h_scale`, `trg_h_add` (₱ bn of transfers), `tins_scale`, `ta_scale`, `ica_scale`, `sm_scale`, `fsav_scale`, `kscale`, `wbar`, `cpi`, `exr`. The 2023 SAM records only ₱103.7 bn of government transfers to households, far below actual cash-transfer programmes (most are booked elsewhere in the national accounts); model a transfer programme with `trg_h_add` in pesos.

## 6. The recursive-dynamic model (`pystdcge/dynamic.py`)

A sequence of static equilibria, 2023-2030, linked by capital accumulation; households and firms do not look ahead (the standard for policy CGE work: IFPRI's dynamic model, the World Bank's MAMS and MANAGE, PEP-1-t).

- **Capital:** K(t) = (1 − δ)K(t−1) + κ I(t−1). With `capital_allocation="putty-clay"`, installed capital stays in its industry and new capital is allocated by relative returns (Thurlow 2004, omega = 3).
- **Labour:** grows by skill (`psa_labour_growth()`, from the Labour Force Survey and population projections) or at a placeholder rate.
- **Productivity:** calibrated each year so that baseline real GDP follows the growth path; with `industry_targets=psa_industry_growth()`, each of PSA's 16 industries follows its own 2024-2025 growth.
- **Hybrid closure** (`hybrid=True`): years with a shock are solved with the short-run closure anchored to that year's baseline; the employment gap then closes by `gap_persistence` a year under the long-run closure.
- **Public capital** (`public_capital={...}`): changes in public construction investment change a public capital stock that scales productivity in every activity, (1 + dKG/KG)^phi.
- **Scenarios** keep the baseline productivity path and add shocks by year: `d.scenario({2025: {...}, 2026: {...}})`.

### Calibrating the dynamic baseline

`documented_baseline()` sets depreciation (5.02%, Penn World Table 11.0), the capital-output ratio (1.96 for rent-earning capital), labour growth by skill (PSA) and the government's growth path (DBCC: 4.0% in 2026, 5.5% in 2027-2030). The plain default keeps simple placeholder values (5% depreciation, 1.5% labour growth, a placeholder growth path) so that default results stay reproducible. Sources and grades: `docs/parameters.md`. A zero shock always reproduces the baseline exactly (tests Y1-Y5).

## 7. From time series to the CGE (`svar.py`, `macrolink.py`)

A structural VAR estimates how the economy responded to a shock on average; the CGE explains how given external changes spread through industries, prices and households. `macrolink` passes to the CGE only what the CGE treats as external: world oil prices, remittances, and capital inflows as foreign savings (or as investment in the short-run closure, where foreign savings adjust). The exchange rate, GDP and investment are CGE outcomes; `consistency()` compares them with the VAR's, so a gap shows what one model leaves out (expectations and financial channels in the CGE; sectoral detail and identification limits in the VAR).

## 8. Limits to state with every result

- One representative producer per industry; no firm-level detail; no informal/formal split.
- Recursive-dynamic, not intertemporal: no expectations, interest rates or financial sector (monetary policy questions need other tools).
- Elasticities: Philippine estimates exist only for Armington elasticities; CET values are assumptions (`docs/parameters.md`).
- The 2023 SAM's structure rests on the 2018 input-output table.
- The full 41-sector model has been compared with IFPRI's GAMS code only on a condensed 9-sector SAM, within the free GAMS licence's size limit.
