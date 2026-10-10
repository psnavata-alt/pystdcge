# Use of generative AI in this software

Journals and software reviewers ask authors to state how AI tools were used (for example JOSS's AI-usage policy and Elsevier's declaration of generative AI in writing). This is that statement.

## Tools

- **Claude Code** (Anthropic), command-line coding assistant, with the **Claude Opus 5.5** model, September-October 2026.

## What the AI did

- Wrote the Python code of the package from the published model (Lofgren, Harris and Robinson 2002) and other cited sources, under the author's direction: model structure, closures, calibration, the dynamic extensions, the time-series modules.
- Wrote the tests, the validation scripts (including the modified IFPRI GAMS data and run files, marked as altered under the GPL) and the documentation.
- Transcribed published tables (e.g. elasticities) from source documents; each transcription is cited in `data/DATA_SOURCES.md`.

## What the author did

- Chose the model, the data and the questions; set the standards (sourced parameters, opt-in extensions, regression tests); decided every design choice; reviewed the results.
- Is responsible for the content.

## Why the results can be trusted without trusting the AI

AI-written code needs checks that do not depend on the AI. The package is checked against work written by people:

| Check | Independent, human-written reference | Agreement |
|---|---|---|
| V2-V4 | IFPRI's own GAMS implementation of the model, run on the same data | Real GDP and consumption within 0.0006 pp (IFPRI-style margins); every remaining gap explained by measurement conventions |
| V5 | pycge, a human-written Python port (2017) of Hosoe et al.'s standard CGE model | 1e-12 |
| V7 | statsmodels' VAR implementation | 1e-15 |
| D2, Y5, L1 | Official statistics (IFPRI SAMs; PSA national accounts, labour force survey, population projections) | Exact or within stated tolerances |
| C1-C5 | Mathematical properties any correct CGE must satisfy (benchmark replication, homogeneity, Walras' law, GDP identity) | Machine precision |
| `docs/equations.md` | The published equations, line by line (cited lines checked by `tests/test_docs.py`) | 32 of 48 as published; every difference stated |

All checks run with one command (`python -m pytest`).
