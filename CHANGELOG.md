# Changelog

## 0.3.3 (10 October 2026): first public release

The public release continues the version numbers of the code base it comes from, so the version notes in the code
("added in 0.3") stay meaningful.

- **0.1 (26 September 2026):** SAM tools and multipliers; input-output models; the static standard CGE model in three
  closures; the recursive-dynamic model; poverty microsimulation; Newey-West regressions, VARs and local projections;
  16 automated checks.
- **0.2 (1 October 2026):** data checksums; regression reference; documentation of every equation.
- **0.3 (8 October 2026):** validation against IFPRI's own GAMS model (V2) and IFPRI-style trade margins (V3);
  balancing and calibration on the 2018 SAM (C8); LES household demand (H1); sourced elasticity sets (E1); refined
  petroleum split from chemicals (S1); hybrid dynamic closure (Y2); public capital (Y3); capital by industry and a
  documented baseline (Y4); industry baselines from national accounts (Y5); labour growth by skill (L1).
- **0.3.1 (8 October 2026):** home consumption as own produce, validated against IFPRI (V4); Hosoe options validated
  against pycge (V5); named settings (S2); 16-industry input-output table.
- **0.3.2 (9 October 2026):** structural VARs (`svar`: block exogeneity, sign restrictions, bootstrap, historical
  decompositions, counterfactuals, Minnesota BVAR; V7) and the VAR-to-CGE link (`macrolink`; M2); public test suite;
  input-output tables, household survey and labour-force data are downloaded by the user.
- **0.3.3 (10 October 2026):** fixes from an audit for "rigging" (results typed in, plugs, hidden failures, weak tests):
  an unbalanced SAM is refused unless declared as published in rounded figures; solves stop on failure; skipped
  bootstrap draws are counted; tests that depend on another test's models fail instead of passing vacuously.
