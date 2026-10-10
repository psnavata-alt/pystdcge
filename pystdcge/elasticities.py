"""Elasticity sets for the CGE (added in 0.3).

    from pystdcge.elasticities import elasticity_set
    m = CGE.from_sam(elasticities=elasticity_set("ph"))

Sets (built by tools/build_elasticities.py into data/processed/elasticities_ph_v1.csv; sources and grades in
docs/parameters.md):
  "default"  pystdcge 0.2: value added 0.8, Armington 2.0, CET 2.0 for every sector (common defaults; placeholder).
  "gtap"     GTAP 9 standard parameters (via the World Bank MANAGE-WB template), aggregated to pystdcge sectors with
             Philippine weights: value added ESUBVA by activity, Armington ESUBD by commodity; CET set equal to ESUBD
             (MANAGE-WB's convention: no estimated CET exists).
  "ph"       As "gtap", but Armington from Kapuscinski and Warr (1999), the only econometric Philippine estimates, where
             significant, positive and covering at least half of the sector's imports (13 commodities).
  "ph_pcgem_cet"  As "ph", with CET from Cororaton's PCGEM (2000, Table 3; assumed values) — sensitivity only.
The 2018 SAM's commodities are a subset of the 2023 SAM's, so the same table serves both.
"""
from __future__ import annotations

import pandas as pd

from . import paths
from .cge import DEFAULT_ELASTICITIES

TABLE = paths.DATA_PROCESSED / "elasticities_ph_v1.csv"


def elasticity_set(name: str = "default") -> dict:
    if name == "default":
        return dict(DEFAULT_ELASTICITIES)
    t = pd.read_csv(TABLE)
    com, act = t[t.kind == "commodity"].set_index("code"), t[t.kind == "activity"].set_index("code")
    va = act.sigma_va_gtap.to_dict()
    if name == "gtap":
        return {"sigma_va": va, "sigma_q": com.sigma_q_gtap.to_dict(), "omega_t": com.omega_t_gtap.to_dict()}
    if name == "ph":
        return {"sigma_va": va, "sigma_q": com.sigma_q_ph.to_dict(), "omega_t": com.omega_t_gtap.to_dict()}
    if name == "ph_pcgem_cet":
        return {"sigma_va": va, "sigma_q": com.sigma_q_ph.to_dict(), "omega_t": com.omega_t_pcgem.to_dict()}
    raise KeyError(f"Unknown elasticity set '{name}' (default, gtap, ph, ph_pcgem_cet)")
