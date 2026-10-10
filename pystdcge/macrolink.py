"""From macro-econometric results to CGE shocks, and back (0.3.3, 9 Oct 2026).

A VAR or local projection estimates how the economy responded, on average, to a shock such as higher geopolitical
risk. A CGE explains how a given set of EXTERNAL changes spreads through industries, prices and households. This
module links the two in the standard way:

1. Only what the CGE treats as external enters it: world oil prices, remittances, and capital inflows (FDI) as
   foreign savings or as investment. The exchange rate, GDP, investment, imports and exports are OUTCOMES of the CGE,
   so the VAR's responses of those variables are not imposed (imposing a depreciation in the short-run closure, where
   the exchange rate is the numeraire, would only rescale prices).
2. The CGE's own outcomes are then compared with the VAR's (consistency()): if the CGE's real depreciation and GDP
   change are close to the VAR's, the two tell one story; if not, the gap shows what the CGE leaves out (expectations,
   financial channels) or what the VAR cannot separate.

Units. VAR responses are in % (growth rates) or in levels (FDI, US$ million) by month or quarter; annual() turns a
response path into the change for one year. Peso amounts are converted to the SAM's year by their share of GDP (the
same rule used throughout the package): x_SAM = x / GDP_year * GDP_SAM.

Closures. Foreign savings are exogenous in the 'investment' and 'savings' closures; in the short-run 'keynesian'
closure the exchange rate is fixed and foreign savings adjust, so an FDI change must enter as investment there
(fdi_channel='investment', with a pass-through to real investment; Bosworth and Collins 1999 estimate 0.81-0.90 for
developing and emerging economies, 1.0 = one for one).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .oil import cge_oil_shock


def annual(path, periods_per_year: int, year: int = 1, how: str = "mean", cumulative: bool = False) -> float:
    """Change in year `year` (1 = the first year after impact) from a response path indexed by horizon 0, 1, ...
    how='mean' for rates or levels relative to baseline (e.g. % deviation of the price of oil), 'sum' for flows
    (e.g. FDI in US$ million per month). cumulative=True if `path` is a per-period change to be cumulated first
    (e.g. month-on-month depreciation)."""
    x = np.asarray(path, float)
    if cumulative:
        x = np.cumsum(x)
    seg = x[(year - 1) * periods_per_year: year * periods_per_year]
    if len(seg) < periods_per_year:
        raise ValueError(f"the path has {len(x)} horizons: too short for year {year}")
    return float(seg.mean() if how == "mean" else seg.sum())


def sam_gdp(m) -> float:
    """Nominal GDP in the model's SAM (₱ bn, base year), from the benchmark solution."""
    b = m.solve()
    if not b.ok:                                     # 0.3.3 (rigging audit): never use an unsolved benchmark
        raise RuntimeError(f"Benchmark did not solve ({b.message}, residual {b.residual_max:.2e})")
    return float(m.gdp(b)["nominal_expenditure"])


def cge_shocks(m, oil_pct: float = 0.0, remit_pct: float = 0.0, fdi_usd_m: float = 0.0,
               php_per_usd: float | None = None, gdp_bn: float | None = None, fdi_channel: str | None = None,
               investment_passthrough: float = 1.0, combined_oil_share: float = 0.6) -> dict:
    """CGE shock spec for one year from external changes.
    oil_pct: world oil price, % change. remit_pct: remittances, % change (foreign currency).
    fdi_usd_m: change in FDI inflows, US$ million in the year (negative = less FDI); needs php_per_usd and gdp_bn
    (nominal GDP of that year, ₱ bn) to convert it to the SAM's units by share of GDP.
    fdi_channel: 'foreign_savings' (default outside the keynesian closure) or 'investment' (default in it)."""
    spec: dict = {}
    if oil_pct:
        spec.update(cge_oil_shock(m, oil_pct / 100, combined_share=combined_oil_share))
    if remit_pct:
        spec["remit_scale"] = 1 + remit_pct / 100
    if fdi_usd_m:
        if php_per_usd is None or gdp_bn is None:
            raise ValueError("an FDI change needs php_per_usd and gdp_bn to convert it to the SAM's units")
        d_sam = fdi_usd_m * php_per_usd / 1000 / gdp_bn * sam_gdp(m)          # ₱ bn in the SAM's year
        ch = fdi_channel or ("investment" if m.closure == "keynesian" else "foreign_savings")
        if ch == "foreign_savings":
            if m.closure == "keynesian":
                raise ValueError("foreign savings adjust in the keynesian closure: use fdi_channel='investment'")
            spec["fsav_scale"] = 1 + d_sam / m.fsav
        elif ch == "investment":
            spec["qinv_scale"] = {c: 1 + investment_passthrough * d_sam / m.qinv.sum() for c, q in zip(m.C, m.qinv) if q > 0}
        else:
            raise ValueError("fdi_channel: 'foreign_savings' or 'investment'")
    return spec


def consistency(m, base, sim, var_changes: dict) -> pd.DataFrame:
    """Compare CGE outcomes (% change from base) with the VAR's for the same year.
    var_changes: {'real_gdp': %, 'real_exchange_rate': %, 'real_investment': %, 'imports': %, 'exports': %} (any subset;
    + = depreciation for the exchange rate). The CGE's real exchange rate is EXR deflated by the CPI numeraire."""
    gb, gs = m.gdp(base), m.gdp(sim)
    cge = {"real_gdp": (gs["real"] / gb["real"] - 1) * 100,
           "real_investment": (sim["QINV"].sum() / base["QINV"].sum() - 1) * 100,
           "imports": (gs["M"] / gb["M"] - 1) * 100, "exports": (gs["X"] / gb["X"] - 1) * 100}
    try:
        cge["real_exchange_rate"] = (float(sim["EXR"][0] if np.ndim(sim["EXR"]) else sim["EXR"])
                                     / float(base["EXR"][0] if np.ndim(base["EXR"]) else base["EXR"]) - 1) * 100
    except (KeyError, TypeError):
        pass
    rows = [dict(variable=k, cge_pct=cge.get(k), var_pct=v, gap_pp=None if cge.get(k) is None else cge[k] - v)
            for k, v in var_changes.items()]
    return pd.DataFrame(rows).set_index("variable")
