# Parameters and their sources

Every number the models assume beyond the SAM, where it comes from, and how good the source is.

**Grades.** **Gold**: official Philippine data, or a Philippine estimate in a peer-reviewed source. **Silver**: the standard value of an authoritative model or international dataset, not estimated for the Philippines. **Placeholder**: an assumption still to be replaced. Every source listed was opened before use.

The default model (`settings "default"`) uses the original simple values (elasticities 0.8 / 2.0 / 2.0, Cobb-Douglas demand, 5% depreciation, placeholder growth path) so that results stay reproducible; the sourced values below are used by the `"extended"` setting or by the named options.

## 1. Dynamic model: capital

| Parameter | Value | Grade | Source | For comparison |
|---|---|---|---|---|
| Depreciation rate of capital | **5.02%** (2023); 5.0-5.4% over 2010-2023 (`documented_baseline()`) | Gold (built on PSA national accounts) | Penn World Table 11.0, capital detail: capital consumption / previous-year net capital stock, current prices. PWT investment equals PSA gross fixed capital formation exactly, 2010-2023 | PWT `delta` 4.64% (stock-weighted); IMF ICSD Manual 2021, Table 1: 5.40% (private, middle income); MANAGE-WB default 4% |
| Capital stock / GDP | **2.42** (2023, current prices); about **1.96** excluding public capital (rent-earning capital) | Gold | PWT 11.0 net capital stock / PSA nominal GDP; public share about 19% (IMF ICSD 2019) | IMF ICSD total 2.08 (2019) |
| Investment mobility omega (putty-clay allocation) | **3.0**; 1 and 5 as sensitivity (stable for 0-5) | Silver | IFPRI Extended Standard Recursive Dynamic CGE v2.00, `beta1 = beta2 = 3.00`; rule from Thurlow (2004), TIPS WP 1-2004, eqs P-U, and Diao and Thurlow, eqs 22-23 | MANAGE-WB uses a vintage rule (disinvestment elasticity 0.7) |
| Public capital depreciation | **3.52%** | Silver | IMF ICSD 2021 Manual & FAQ, Table 1 (middle income) | |
| Public investment efficiency `e` | **0.77** | Gold | IMF Country Report 19/137, Philippines PIMA (2018), pp. 8, 25: efficiency gap "about 23 percent" | MANAGE-WB 0.75; IMF (2015) average gap 27% |
| Public capital stock / GDP `kg_gdp` | **0.296** (constant 2017 PPP) to **0.397** (current pesos), 2019, as a range | Gold | IMF Investment and Capital Stock Dataset (July 2025 release) | |
| Output elasticity of public capital phi | **0.083** (short run) to **0.122** (long run) | Silver (meta-analysis, mostly OECD) | Bom and Ligthart (2014), *Journal of Economic Surveys* 28(5): 889-916 | |

## 2. Dynamic model: growth path and labour

| Parameter | Value | Grade | Source |
|---|---|---|---|
| Real GDP growth 2024-2025 | 5.7%, 4.4% | Gold | PSA national accounts |
| Real GDP growth 2026-2030 | 4.0% (2026), 5.5% (2027-2030): midpoints of the government's ranges (3.5-4.5%; 5.0-6.0%) | Gold | Development Budget Coordination Committee (DBCC), 193rd statement, 8 July 2026 |
| Labour growth by skill | 2024: low -7.65%, medium -4.08%, high +4.92%; 2025: -4.65%, -2.21%, +1.97%; 2026 (Jan-Jul): -4.19%, -4.50%, +3.58%; 2027-2030: total with the population aged 15+, skill shares continuing their 2023-2025 trend (`psa_labour_growth()`; test L1) | Gold (2024-2026); sourced projection (2027-2030) | PSA OpenSTAT 0141B3FEMP7 (LFS, employed by highest grade completed) and 0021A3BPOP1 (population projections). Low = no grade or elementary undergraduate; medium = elementary graduate or junior high undergraduate; high = junior high completed and above |
| Industry baseline | Each PSA industry's real GVA growth in 2024-2025 reproduced exactly; real GDP then 5.69% and 4.49% (PSA: 5.71%, 4.40%) | Gold (targets) | PSA OpenSTAT 0052B5BPRA1 (test Y5) |
| Job-gap persistence (hybrid closure) | 0.5 a year | **Placeholder** | To be estimated from labour-market evidence (unemployment and underemployment, wage rigidity, Okun's law) |

## 3. Static CGE: elasticities (`pystdcge/elasticities.py`; test E1)

**What exists.** Philippine econometric estimates exist only for Armington (import-domestic) elasticities: Kapuscinski and Warr (1999), 33 products. Other Philippine CGE models (APEX, PCGEM, MIMAP, Briones, PHILGEM) reuse those or assume values. For everything else the sets use GTAP's standard values, taken from the World Bank's MANAGE-WB template and weighted by Philippine trade and value added. No CET (export transformation) estimate exists for the Philippines; those values are assumptions.

| Set | Value added (by activity) | Armington (by commodity) | CET (by commodity) |
|---|---|---|---|
| `default` | 0.8 | 2.0 | 2.0 |
| `gtap` | GTAP 9 ESUBVA: crops and livestock 0.26; forestry, fishing, mining 0.20; food and beverages 1.12; manufacturing, utilities, most services 1.26; construction 1.40; trade, transport, hotels 1.68 | GTAP 9 ESUBD, Philippine import-weighted: 1.15 to 5.05 | equal to ESUBD (MANAGE-WB convention) |
| `ph` | as `gtap` | Kapuscinski and Warr (1999) where valid (13 commodities, e.g. corn 3.72, poultry 1.39, food 1.03, textiles 0.65, machinery 1.05); GTAP elsewhere | as `gtap` |
| `ph_pcgem_cet` | as `gtap` | as `ph` | PCGEM (Cororaton 2000, Table 3), assumed values 0.3-3.0 |

Rule for `ph`: Kapuscinski and Warr's preferred estimate (Table 4, column 7, error-correction model) where it is significant at 10%, positive, and the significant estimates cover at least half of the group's imports (their Table 1); otherwise GTAP. Grades: Kapuscinski and Warr gold but dated (1970s-80s data); GTAP silver; CET values are assumptions.

## 4. Household demand: Linear Expenditure System (`pystdcge/demand.py`; test H1)

- **Income elasticities:** Briones et al. (2023), PIDS DP 2023-23, Table 5 (AMPLE-CGE; food values from QAIDS estimates, non-food imputed by the authors) and Table 4 (other cereals); sub-groups weighted with PSA's 2018-based CPI weights; scaled per household group to satisfy Engel aggregation.
- **Frisch parameter:** fitted per household group so the LES own-price elasticities best match Briones's: -1.28 (poorest rural) to -1.15 (richest urban).
- **Benchmark:** USDA ERS, Muhammad, Seale, Meade and Regmi (2011), TB-1929 (144 countries): the implied Philippine Frisch parameter is -1.363; `les_usda2011()` builds the LES from these elasticities.

## 5. Oil and the petroleum-split SAM (`pystdcge/oil.py`; test S1)

The IFPRI SAM puts refined petroleum, chemicals, pharmaceuticals, and rubber and plastics in one account; crude oil is in mining. The split SAM separates refined petroleum (PSA 2018 sectors 107-108) using the cost structure, purchases, imports and exports of PSA's 2018 240-industry table; every other account of the IFPRI 2023 SAM is unchanged.

| Parameter | Value | Source |
|---|---|---|
| Petroleum share of "chemicals and petroleum" imports (combined SAM) | 0.512 | PSA 2018, 240-industry imports, sectors 107-108 / 107-118 |
| Crude share of mining imports (split SAM) | 0.677 | PSA 2018, sector 40 / 39-45 |
| Fertiliser share of chemical imports | 0.026 | PSA 2018, sector 110 / 109-118 |
| Input-output pass-through, world oil to refined-petroleum price | 0.634 = (s_m + (1-s_m)c) / (1-(1-s_m)o) | import share s_m 0.354 (2018 supply table, sector 107); crude c 0.269 and own use o 0.260 per peso of refinery output (80-industry table) |

## 6. Time series

The VAR tools estimate everything from the data supplied; the only fixed choices are the user's (lags, ordering, block, prior tightness). The Minnesota prior follows Banbura, Giannone and Reichlin (2010): overall tightness 0.2 by default, own first-lag prior mean 0 for growth rates (1 for levels), lag decay 1, a near-flat prior on the constant. In `macrolink`, the default FDI pass-through to investment is 1.0, with 0.81-0.90 from Bosworth and Collins (1999) as a sensitivity range.

## References

- Banbura, M., Giannone, D. and Reichlin, L. (2010). Large Bayesian vector auto regressions. *Journal of Applied Econometrics* 25(1): 71-92.
- Bom, P. R. D. and Ligthart, J. E. (2014). What have we learned from three decades of research on the productivity of public capital? *Journal of Economic Surveys* 28(5): 889-916.
- Bosworth, B. P. and Collins, S. M. (1999). Capital flows to developing economies: implications for saving and investment. *Brookings Papers on Economic Activity* 1999(1): 143-180.
- Briones, R. M. et al. (2023). Food affordability for Filipinos in 2030. PIDS Discussion Paper 2023-23.
- Cororaton, C. B. (2000). Philippine computable general equilibrium model (PCGEM). PIDS Discussion Paper 2000-33.
- Feenstra, R. C., Inklaar, R. and Timmer, M. P. (2015). The next generation of the Penn World Table. *American Economic Review* 105(10): 3150-3182.
- IMF (2019). Philippines: Technical Assistance Report, Public Investment Management Assessment. Country Report 19/137.
- IMF (2021). Investment and Capital Stock Dataset: Manual & FAQ.
- Kapuscinski, C. A. and Warr, P. G. (1999). Estimation of Armington elasticities: an application to the Philippines. *Economic Modelling* 16(2): 257-278.
- Muhammad, A., Seale, J. L., Meade, B. and Regmi, A. (2011). International evidence on food consumption patterns: an update using 2005 International Comparison Program data. USDA ERS Technical Bulletin 1929.
- Thurlow, J. (2004). A dynamic computable general equilibrium (CGE) model for South Africa: extending the static IFPRI model. TIPS Working Paper 1-2004.
