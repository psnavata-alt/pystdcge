# Contributing

Thank you for helping. Issues (bugs, questions, results that look wrong) and pull requests are welcome.

## Rules for changes

1. **Every test must pass**: `python -m pytest`. Tests that need data you have not downloaded are skipped, not failed.
2. **New features are opt-in.** With default arguments the model must give exactly the results in `tests/reference_results.json` (test R0). If a deliberate correction changes a default result, explain it in the pull request and in `CHANGELOG.md`, then refreeze the reference with `python tests/test_regression.py --update`.
3. **Every parameter needs a source** you have opened, cited in the code or in `docs/parameters.md` with page or table number.
4. **Data:** add only files whose licence allows redistribution, with their source, licence and checksum in `data/DATA_SOURCES.md`; otherwise add download instructions.
5. **Equations:** if you change one, update `docs/equations.md` (published numbering, GAMS name, Python line).

## Reporting a result that looks wrong

Please include the shock, the closure, the settings, the version (`pystdcge.__version__`) and the numbers you expected, with their source. Comparisons with other models (GAMS, MPSGE, GEMPACK) are especially useful.
