"""pystdcge: an open-source Python implementation of the IFPRI standard CGE model, with SAM and input-output
multipliers, a recursive-dynamic extension, poverty microsimulation and time-series tools, calibrated to the
Philippines.

Modules
-------
paths        Folder locations (data, outputs), resolved relative to the repository.
sam          Load, check, balance and aggregate IFPRI-style Social Accounting Matrices.
multiplier   SAM and input-output multipliers (fixed-price models).
iomodel      Input-output (Leontief) quantity, cost-push price and job-equivalent models (PSA tables, user-supplied).
cge          Static CGE model calibrated to a SAM (Lofgren, Harris and Robinson 2002, IFPRI standard model).
dynamic      Recursive-dynamic extension (capital accumulation, labour growth, productivity, closures over time).
demand       Linear Expenditure System (LES) household demand parameters from published elasticities.
elasticities Sourced elasticity sets for the CGE.
oil          World oil-price shocks with sourced shares.
settings     Named model settings ("default", "extended").
microsim     Links model results to household survey data for poverty and distribution (user-supplied survey).
var          Time-series tools: OLS with Newey-West errors, VARs, structural VARs, local projections.

Start with README.md; the model equations are in docs/equations.md and the tests in tests/.
"""
__version__ = "0.3.3"
