"""Named model settings: "default" and "extended".

    from pystdcge.settings import cge_model, dynamic_model
    m = cge_model("extended", closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
    d = dynamic_model("extended", public_capital="low")

A named setting, not changed code defaults: "default" stays selectable and the regression test keeps passing.

"default"   the original settings: combined 2023 SAM, elasticities 0.8 / 2.0 / 2.0 for all sectors, Cobb-Douglas
            household demand, margins on the composite good; dynamic: placeholder baseline, one mobile capital stock,
            long-run closure every year.
"extended"  every sourced extension that combines with the others:
            - 2023 SAM with refined petroleum split from chemicals (oil shocks enter as cpetr and crude inside mining,
              pystdcge/oil.py);
            - Philippine elasticity set "ph" (GTAP value added; Kapuscinski and Warr 1999 Armington);
            - LES household demand, Briones et al. 2023;
            - IFPRI-style trade margins, margins="split";
            dynamic, in addition: documented baseline (DBCC growth, PWT depreciation and capital, PSA labour growth
            by skill), capital tied to its industry (putty-clay, omega 3), hybrid closure, and public capital as a
            low-high range (IMF ICSD 2019, phi 0.083-0.122).
            NOT included:
            - home consumption as own produce (home="separate"): not yet combined with LES; its effect on aggregate
              results is small (examples/home_consumption_sensitivity.py);
            - the industry baseline is an OPTION (industry_baseline=True), not the default: it contains the actual
              2025 construction slump, so a 2025 construction shock must not be added on top of it.
"""
from __future__ import annotations

from . import paths

SETTINGS = ("extended", "default")
DEFAULT = "extended"
# public capital: the two extreme (phi, public capital / GDP) pairs span the documented range.
# phi: output elasticity of public capital, Bom and Ligthart (2014) meta-analysis, 0.083 short run, 0.122 long run;
# KG/GDP: IMF ICSD, 2019, 0.296 (constant 2017 PPP) and 0.397 (current pesos). The marginal return on public
# capital rises with phi / KG, so low = (0.083, 0.397) and high = (0.122, 0.296).
PUBLIC_CAPITAL = {"off": None,
                  "low": dict(phi=0.083, kg_gdp=0.397),
                  "high": dict(phi=0.122, kg_gdp=0.296)}

DESCRIPTION = {
    "extended": "Sourced upgrades on: petroleum split from chemicals, Philippine elasticities, LES household demand, "
                       "IFPRI-style trade margins; over time also the documented baseline, capital tied to its industry, "
                       "job losses in shock years, and public capital as a low-high range.",
    "default": "The original model settings (the regression test reproduces their results exactly).",
}


def _check(setting):
    if setting not in SETTINGS:
        raise KeyError(f"Unknown setting '{setting}' ({', '.join(SETTINGS)})")


def cge_kwargs(setting: str = DEFAULT) -> dict:
    """Keyword arguments for CGE.from_sam(path, **kw) (without closure arguments). 'path' is the SAM file."""
    _check(setting)
    if setting == "default":
        return dict(path=None)
    from .demand import les_briones2023
    from .elasticities import elasticity_set
    return dict(path=paths.SAM_2023_PETR, elasticities=elasticity_set("ph"), les=les_briones2023(), margins="split")


def cge_model(setting: str = DEFAULT, **closure):
    """A calibrated CGE under a named setting; closure arguments (closure, unemployed, capital) pass through."""
    from .cge import CGE
    kw = cge_kwargs(setting)
    return CGE.from_sam(kw.pop("path"), **kw, **closure)


def dynamic_kwargs(setting: str = DEFAULT, public_capital: str = "off", industry_baseline: bool = False,
                   hybrid: bool | None = None) -> dict:
    """Keyword arguments for DynamicCGE(**kw). public_capital: 'off', 'low' or 'high' (extended setting only).
    industry_baseline: PSA industry growth 2024-2025 (contains the 2025 construction slump: do not add a 2025 construction shock).
    hybrid: None = the setting's own choice (default off, extended on)."""
    _check(setting)
    if setting == "default":
        if public_capital != "off" or industry_baseline:
            raise ValueError("public capital and the industry baseline are options of the extended setting")
        return dict(hybrid=bool(hybrid))
    from .dynamic import documented_baseline, psa_industry_growth
    from .sam import SAM
    kw = cge_kwargs(setting)
    d = dict(sam=SAM.load_for_model(kw.pop("path")), **kw, **documented_baseline(),
             capital_allocation="putty-clay", hybrid=True if hybrid is None else bool(hybrid),
             public_capital=PUBLIC_CAPITAL[public_capital])
    if industry_baseline:
        d["industry_targets"] = psa_industry_growth()
    return d


def dynamic_model(setting: str = DEFAULT, **kw):
    from .dynamic import DynamicCGE
    return DynamicCGE(**dynamic_kwargs(setting, **kw))
