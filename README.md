# pystdcge

**An open-source Python implementation of the IFPRI standard computable general equilibrium (CGE) model, validated against IFPRI's own GAMS code, with SAM and input-output multipliers, a recursive-dynamic extension, structural VARs and a link from VAR results to CGE shocks. Calibrated to the Philippines (IFPRI 2023 and 2018 social accounting matrices).**

> Version 0.3.3. Licence: MIT (see `LICENSE`), except IFPRI's GAMS files in `validation/*/gams_ph/` (GNU GPL v2, see `validation/ifpri/gams_ph/NOTICE.md`).

## Why

The IFPRI standard CGE model (Lofgren, Harris and Robinson 2002) is the most widely used single-country CGE model in developing economies. It is distributed as GAMS code, and GAMS needs a commercial licence for models of realistic size. `pystdcge` writes the same model in Python with open-source solvers. It is **checked equation by equation against the published model** and **solution by solution against IFPRI's own GAMS code** on the same data, so researchers and government analysts without a GAMS licence can use, inspect and extend it.

## What it does

| Module | What it does |
|---|---|
| `sam` | Load, check, balance (least squares) and aggregate IFPRI-style social accounting matrices |
| `multiplier` | SAM multipliers and fixed-price input-output models (upper bounds for demand shocks) |
| `cge` | The static standard CGE model: CES value added, Leontief intermediates, Armington imports, CET exports, trade margins, taxes, ten household groups; closures: investment-driven, savings-driven, short-run Keynesian with unemployment |
| `demand` | Linear Expenditure System household demand from published elasticities (Briones et al. 2023; USDA ERS) |
| `elasticities` | Sourced elasticity sets (GTAP via the World Bank's MANAGE-WB; Kapuscinski and Warr 1999 for Philippine Armington elasticities) |
| `dynamic` | Recursive-dynamic extension to 2030: capital accumulation, capital tied to its industry ("putty-clay"), labour growth by skill from the Labour Force Survey, industry baselines from national accounts, a short-run/long-run hybrid closure, and a public-capital productivity channel |
| `oil` | World oil-price shocks with sourced import shares, on a SAM with refined petroleum split from chemicals |
| `iomodel` | Leontief quantity, cost-push price and job-equivalent models on PSA's 2018 input-output tables (downloaded by the user) |
| `microsim` | Links model results to household survey data for poverty counts (PSA FIES 2023, downloaded by the user) |
| `var`, `svar` | Newey-West regressions and local projections; structural VARs with block exogeneity, Cholesky and sign-restriction identification, bootstrap bands, historical decompositions, "channel shut off" counterfactuals and a Minnesota-prior Bayesian VAR |
| `macrolink` | Turns VAR results into CGE shocks (oil, remittances, FDI as foreign savings or investment) and compares the CGE's own outcomes with the VAR's |
| `settings` | Two named settings: `"default"` (the original model) and `"extended"` (every sourced extension) |

## Install

Python 3.11 or later.

```
git clone <repository URL>
cd pystdcge
python -m pip install -e .            # numpy, scipy, pandas, statsmodels, openpyxl
python -m pip install -e ".[test]"    # adds pytest
```

## Quick start

```python
from pystdcge.cge import CGE

m = CGE.from_sam()                                       # IFPRI 2023 Philippine SAM, long-run closure
base = m.solve()
sim = m.solve({"pwm_scale": {"cchem": 1.2}})             # world import price of chemicals and petroleum +20%
print(m.gdp(sim)["real"] / m.gdp(base)["real"] - 1)      # real GDP: -0.39%

short = CGE.from_sam(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
print(short.compare(short.solve(), short.solve({"qinv_scale": {"ccons": 0.9}})))  # construction investment -10%
```

More in `examples/`: a CGE shock under three closures, a dynamic investment programme to 2030, and a VAR estimated on simulated data whose results are passed to the CGE.

## Tests and validation

```
python -m pytest                 # all tests (about 10 minutes)
python -m pytest -m "not slow"   # the fast ones (under a minute)
```

| Test | What it shows |
|---|---|
| C1-C8 | Every equation holds at the SAM; the model reproduces the SAM; homogeneity; Walras' law; GDP identity; signs; multiplier bounds; the same on the 2018 SAM |
| **V2, V3** | **Reproduces IFPRI's own GAMS model** on a condensed Philippine SAM: real GDP and consumption within 0.005 pp (0.0006 pp with IFPRI-style margins); 99.6% of 232 compared results within 0.1 pp. The remaining gaps are measurement conventions, shown by test (`validation/ifpri/README.md`) |
| V4 | The same with home consumption kept (book equations 18 and 34) |
| **V5** | **Reproduces pycge**, a human-written Python port of Hosoe, Gasawa and Hashimoto's standard CGE model, to 1e-12 |
| V7 | The VAR code equals statsmodels to 1e-12; exact properties of block exogeneity, decompositions, counterfactuals, sign restrictions and the BVAR |
| Y1-Y5, L1 | Dynamic baselines hit their targets (DBCC growth path; PSA GVA by industry; LFS labour by skill) and a zero shock reproduces them |
| E1, H1, S1, S2 | Sourced elasticities, LES demand, the petroleum-split SAM and the named settings |
| R0 | Key default results equal the frozen reference (`tests/reference_results.json`) |
| D1, D2, M1 | Data checksums; SAM balance; SAM multipliers |
| I3, I4, P1 | Input-output identities and the poverty baseline (run once you have downloaded the PSA files) |

The equations, written next to the published model's numbering and the GAMS code, are in `docs/equations.md`.

## Data

`data/DATA_SOURCES.md` lists every file with its source, licence and checksum. Included: IFPRI's 2023 and 2018 Philippine SAMs (CC BY 4.0), PSA OpenSTAT series (CC BY), published elasticities. **Not included**, because their terms do not allow redistribution: PSA's input-output tables (`data/raw/io/README.md` explains how to download and convert them), PSA's FIES household survey (`data/raw/fies/README.md`) and the Labour Force Survey employment table (`data/raw/lfs/README.md`). The tests that need them are skipped until you add them.

*This data was provided by the International Food Policy Research Institute (IFPRI). IFPRI bears no responsibility for the analyses or interpretations of the data presented here.*

## Use of AI

The code, tests and documentation were written with an AI coding assistant (Claude Code, Anthropic; Claude Opus 5.5 model) working under the author's direction. The author specified the model and checks, reviewed the results and is responsible for the content. Because AI-written code needs checks that do not rely on the AI, the model is validated against implementations written by people (IFPRI's GAMS code, pycge, statsmodels), against the published equations, and against official statistics. See `docs/ai_use.md`.

## Citation

See `CITATION.cff`. Please also cite Lofgren, Harris and Robinson (2002) for the model and IFPRI for the SAMs.

## Contributing

Issues and pull requests are welcome (`CONTRIBUTING.md`). Every change must keep `python -m pytest` passing; new features must be opt-in, so the regression test R0 is unchanged.

## References

- Lofgren, H., Harris, R. L. and Robinson, S. (2002). *A Standard Computable General Equilibrium (CGE) Model in GAMS*. Microcomputers in Policy Research 5. International Food Policy Research Institute.
- IFPRI (2025). *2023 Social Accounting Matrix for Philippines*. Harvard Dataverse, doi:10.7910/DVN/WQXUQW.
- IFPRI (2021). *2018 Social Accounting Matrix for the Philippines*. Harvard Dataverse, doi:10.7910/DVN/XSEXEP.
- Hosoe, N., Gasawa, K. and Hashimoto, H. (2010). *Textbook of Computable General Equilibrium Modelling: Programming and Simulations*. Palgrave Macmillan.
- Thurlow, J. (2004). A dynamic computable general equilibrium (CGE) model for South Africa. TIPS Working Paper 1-2004.
