# The model's equations against the published IFPRI standard model

This map takes each of the **48 equations** of the IFPRI standard CGE model, as published, to IFPRI's own GAMS code and to `pystdcge/cge.py`. It lets a reader check, equation by equation, that the Python code is the published model, or see exactly where and why it differs. The code line numbers are checked by `tests/test_docs.py`, so they cannot silently go out of date.

## Sources

| Source | Reference |
|---|---|
| **The book** | Lofgren, H., Harris, R. L. and Robinson, S. (2002). *A Standard Computable General Equilibrium (CGE) Model in GAMS*. Microcomputers in Policy Research 5, IFPRI. The 48 equations are summarised in the appendix table, printed pages 50-59, and derived in the main text, pages 18-40. |
| **IFPRI's code** | *Extended Standard Recursive Dynamic CGE Modeling System, Version 2.00* (July 2005; Thurlow's extension of the book's model), GAMS, GNU GPL v2; public copy `uw-windc/IFPRI_model`. Line numbers refer to `validation/ifpri/gams_ph/1DMODEL_PH.GMS` (only the data file name changed and a validation block appended, so the equation lines are IFPRI's). |
| **This package** | `pystdcge/cge.py`. Written from the book, not translated from the GAMS code. |

**Why some formulas look different but are the same.** The book writes production as a production function plus first-order conditions; the code writes the equivalent unit-cost function and the input demands derived from it (the dual form). Both give the same prices and quantities; test V2 shows they do numerically, against IFPRI's own program.

Status: **Same** = the published equation (possibly in the dual form); **Same (cond.)** = identical under the closures this package uses; **Not needed** = the book's term is zero in the Philippine SAM; **Simplified** = treated more simply by default (the book's form is available as an option where noted); **Special case** = a restricted version by default; **Option absent** = an alternative the book offers that is not built.

## Price block (book pp. 50-51)

| # | Book equation | GAMS | `cge.py` line | Status | Note |
|---|---|---|---|---|---|
| 1 | Import price PM = pwm(1+tm)EXR + Σ PQ·icm | PMDEF (1256) | 397 (+419 with `margins="split"`) | **Simplified** | By default trade margins are charged on the composite good (eq. 4); `margins="split"` applies the book's form (test V3) |
| 2 | Export price PE = pwe(1−te)EXR − Σ PQ·ice | PEDEF (1258) | 398 | **Simplified** | No export tax in the SAM (not needed); export margins as eq. 1 |
| 3 | Domestic demand price PDD = PDS + Σ PQ·icd | PDDDEF (1260) | 518; 539 with split margins | **Simplified** | As eq. 1 |
| 4 | Absorption PQ(1−tq)QQ = PDD·QD + PM·QM | PQDEF (1262) | 558 | **Same** | Sales tax defined on the pre-tax value (calibrated to the same SAM payments) |
| 5 | Marketed output value PX·QX = PDS·QD + PE·QE | PXDEF (1265) | 441 | **Same** | |
| 6 | Activity price PA = Σ PXAC·θ | PADEF (1267) | 442 | **Same** | One producer price per commodity (exact: one activity per commodity) |
| 7 | Intermediate input price PINTA = Σ PQ·ica | PINTADEF (1269) | 457 | **Same** | Inside eq. 8 |
| 8 | Activity revenue = costs: PA(1−ta)QA = PVA·QVA + PINTA·QINTA | PVADEF (1271) | 457 | **Same** | Zero profit; activity tax for the 2018 SAM (line 456) |
| 9 | Consumer price index CPI = Σ PQ·cwts | CPIDEF (1273) | 420, 586 | **Same** | CPI numeraire; in the Keynesian closure the exchange rate is fixed instead (a closure the book describes) |
| 10 | Producer price index DPI | DPIDEF (1275) | — | **Option absent** | Only needed if the DPI is the numeraire |

## Production and trade block (pp. 52-55)

| # | Book equation | GAMS | `cge.py` line | Status | Note |
|---|---|---|---|---|---|
| 11-12 | CES top nest (value added vs intermediates) | CESAGGPRD, CESAGGFOC | — | **Option absent** | Fixed proportions (eq. 13-14) for all activities; V2 ran IFPRI's model the same way |
| 13 | Leontief value added QVA = iva·QA | LEOAGGVA (1296) | 458 | **Same** | |
| 14 | Leontief intermediates QINTA = inta·QA | LEOAGGINT (1294) | 510 | **Same** | Combined with eq. 17 |
| 15 | CES value added | CESVAPRD (1301) | 452 | **Same** (dual) | Unit-cost form; αva is `tfp` |
| 16 | Factor demand (first-order condition) | CESVAFOC (1307) | 461 | **Same** (dual) | Activity-specific rental rates when capital is fixed by sector (line 447) |
| 17 | Intermediate demand QINT = ica·QINTA | INTDEM (1319) | 510 | **Same** | |
| 18 | Commodity production and allocation QXAC + Σ QHA = θ·QA | COMPRDFN (1321) | 425 | **Simplified** | By default home consumption is moved to market purchases; `home="separate"` applies eq. 18 and 34 (test V4) |
| 19-20 | Output aggregation across activities (CES) | OUTAGGFN, OUTAGGFOC | 425 (sum) | **Not needed** | No commodity has two producing activities in the 2023 SAM |
| 21 | CET between exports and domestic sales | CET (1330) | 427 | **Same** | |
| 22 | Export-domestic supply ratio | ESUPPLY (1333) | 429 | **Same** | |
| 23 | Only exported or only domestic: QX = QD + QE | CET2 (1336) | 435 | **Same** | |
| 24 | Armington composite supply | ARMINGTON (1339) | 522 (543 with split margins) | **Same** (dual) | |
| 25 | Import-domestic demand ratio | COSTMIN (1342) | 525 | **Same** | |
| 26 | Only imported or only domestic: QQ = QD + QM | ARMINGTON2 (1345) | 527 | **Same** | |
| 27 | Demand for trade and transport services | QTDEM (1348) | 513 (553 with split margins) | **Simplified** | As eq. 1 |

## Institution block (pp. 55-57)

| # | Book equation | GAMS | `cge.py` line | Status | Note |
|---|---|---|---|---|---|
| 28 | Factor income YF = Σ WF·WFDIST·QF | YFDEF (1362) | 464 | **Same** | Plus factor income from abroad (a SAM cell) |
| 29 | Institutional factor incomes | YIFDEF (1364) | 467 | **Same** | |
| 30 | Income of households and enterprises | YIDEF (1367) | 471, 476 | **Same** | |
| 31 | Transfers between institutions | TRIIDEF (1371) | 476 | **Same (cond.)** | Enterprise-to-household transfers proportional to enterprise income: equal to the book with fixed enterprise tax and saving rates |
| 32 | Household consumption spending | EHDEF (1374) | 478 | **Same (cond.)** | Payments to government and abroad deducted before saving; identical at fixed rates |
| 33 | Household demand (LES) | HMDEM (1377) | 483 (Cobb-Douglas), 486 (LES) | **Special case** by default | Cobb-Douglas (LES without subsistence) by default; full LES with `les=` (test H1) |
| 34 | Home-produced goods demand | HADEM (1381) | — | **Simplified** | See eq. 18 |
| 35 | Investment demand QINV = IADJ·qinv | INVDEM (1386) | 509 | **Same** | |
| 36 | Government consumption QG = GADJ·qg | GOVDEM (1389) | 505 | **Same** | |
| 37 | Government revenue | YGDEF (1391) | 564 | **Same** for every tax in the SAM | |
| 38 | Government expenditure | EGDEF (1402) | 566 | **Same** | Plus government payments abroad |

## System constraints (pp. 57-59)

| # | Book equation | GAMS | `cge.py` line | Status | Note |
|---|---|---|---|---|---|
| 39 | Factor markets Σ QF = QFS | FACEQUIL (1408) | 575 | **Same** | Also unemployment at a fixed real wage (line 421) and capital fixed by sector (line 578), closures the book describes |
| 40 | Composite commodity markets | COMEQUIL (1410) | 572 | **Same** | |
| 41 | Current account (foreign currency) | CURACCBAL (1413) | 579 | **Same** | Re-exports on both sides of the account (a feature of the Philippine data) |
| 42 | Government balance YG = EG + GSAV | GOVBAL (1416) | 567 | **Same** | |
| 43 | Direct tax rates with adjustment | TINSDEF (1418) | 477 | **Option absent** (partial) | Rates can be shocked; the closure that adjusts them is not built |
| 44 | Saving rates with adjustment | MPSDEF (1421) | 479 | **Same** (partial) | Proportional adjustment (MPSADJ) used in the investment-driven closure |
| 45 | Savings-investment balance (with WALRAS) | SAVINVBAL (1427) | 584 | **Same** | WALRAS is zero in every solution (test C4) |
| 46-48 | "Balanced" closure (absorption shares) | TABSEQ, INVABEQ, GDABEQ | — | **Option absent** | |

## Tally

| Status | Equations | Count |
|---|---|---|
| As published (including dual forms; same under the package's closures) | 4-9, 13-17, 21-26, 28-32, 35-42, 44, 45 | 32 |
| Not needed with the Philippine SAM | 19, 20 | 2 |
| Simplified by default (trade margins; home consumption), book form available as an option | 1, 2, 3, 18, 27, 34 | 6 |
| Special case by default (Cobb-Douglas; full LES as an option) | 33 | 1 |
| Optional features not built | 10, 11, 12, 43, 46, 47, 48 | 7 |
| **Total** | | **48** |

## The numerical test behind the map

IFPRI's GAMS model and this package were solved on the same condensed Philippine SAM (9 sectors, 10 household groups) for four shocks under two closures (`validation/ifpri/`). With IFPRI's model set to the same choices (Leontief top nest, Cobb-Douglas household demand, home consumption at market), real GDP and consumption agree within 0.005 percentage points, and 96% of 232 compared results within 0.1 pp; the largest gaps (up to 0.51 pp) come from the margins treatment. With `margins="split"` the largest gap falls to 0.11 pp and GDP and consumption agree within 0.0006 pp; the remaining gaps are measurement conventions (the CPI weights and the units of imports), shown by re-expressing the solution in IFPRI's conventions (`validation/ifpri/matched_cpi_test.py`: 0.0009 pp and 0.0003 pp). Equations marked "Option absent" are not tested, and the full 41-sector model has not yet been compared with GAMS.

Note: Hosoe, Gasawa and Hashimoto's textbook "standard CGE model" is a different, smaller model; the package reproduces it too (test V5, `validation/hosoe/`).
