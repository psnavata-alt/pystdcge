"""Recursive-dynamic CGE: the static model solved year by year, linked by capital accumulation.

How it works
------------
Year 0 is the SAM year (2023). Each later year t:
  1. Factor supplies are updated:  labour grows at g_L (by type); land is fixed;
     capital:  K[t] = (1 - dep) * K[t-1] + kappa * I[t-1]
     where I is real investment in the previous year and kappa converts investment (pesos at
     benchmark prices) into capital-income units. kappa is calibrated so that, in the benchmark,
     capital grows at `g_K0` (net of depreciation).
  2. Exogenous demand and foreign flows grow with the baseline GDP path: government consumption,
     the investment level, real transfers, foreign savings, remittances and factor income from abroad.
  3. Baseline only: total factor productivity (TFP, uniform across activities) is solved so that
     real GDP grows at the target rate for that year. Scenarios keep the baseline TFP path.
  4. The static model is solved; its investment feeds next year's capital stock.

Hybrid closure (0.3, opt-in: DynamicCGE(hybrid=True))
  The baseline is unchanged (long-run closure every year). In a scenario, every year that carries a shock is
  solved with the SHORT-RUN model (Keynesian closure: real wages of low- and medium-skill labour fixed, so their
  employment follows demand; capital fixed by activity; exchange rate fixed), anchored to that year's baseline
  equilibrium (same capital allocation, real wages, exchange rate and saving rates), so a zero shock reproduces
  the baseline exactly (check Y2). The employment gap it opens closes gradually afterwards: in later years the
  long-run closure is solved with labour supply reduced by the remaining gap, which shrinks by the factor
  `gap_persistence` each year (default 0.5: half the gap is left after one year, an eighth after three).
  One run therefore shows both the first-year demand loss and its persistence.

Public capital (0.3, opt-in: DynamicCGE(public_capital={...}))
  Lost roads and bridges lower the productivity of every industry, not only the capital stock. In a scenario,
  the change in construction investment relative to the baseline is treated as public investment (true for the
  infrastructure scenarios: the shock is to public construction, and the closures fix other investment). It
  changes the public capital stock:   dKG[t+1] = (1 - delta_g) dKG[t] + e * dIG[t]
  and productivity in all activities by the factor  (1 + dKG[t] / KG_base[t]) ** phi,  with
  KG_base[t] = kg_gdp * baseline real GDP[t] (public capital assumed to keep its share of GDP on the baseline).
  Parameters (each needs a source opened before use):
    phi       output elasticity of public capital. Bom and Ligthart (2014, Journal of Economic Surveys 28(5),
              889-916), meta-analysis of 578 estimates: 0.083 short run, 0.122 long run (central government);
              average 0.106. Run as a range. Mostly OECD estimates.
    kg_gdp    public capital stock / GDP in the base year (e.g. IMF Investment and Capital Stock Dataset, general
              government, Philippines). NO DEFAULT: must be supplied from a source.
    delta_g   public capital depreciation; default 0.0352 (IMF ICSD 2021 Manual, Table 1: middle-income, 2016;
              docs/references/parameters/IMF_ICSD_2021_Manual_FAQ_May2021.pdf).
    e         share of public investment that becomes usable capital; default 0.77 (IMF Country Report 19/137,
              Philippines PIMA: efficiency gap about 23%, "based on perceived quality").
  With phi = 0, or no shock, results equal the model without public capital (check Y3).

Capital by industry ("putty-clay", 0.3, opt-in: DynamicCGE(capital_allocation="putty-clay"))
  Installed capital stays in its industry (each year is solved with capital fixed by activity, rental rates differing
  by activity); only new investment is mobile. New capital is shared out as in IFPRI's recursive dynamic model
  (Thurlow 2004, TIPS WP 1-2004, eqs P-U, pp. 53-54; Diao and Thurlow, eqs 22' and 23):
      share_a = (K_a / sum K) * (omega * (R_a / AR - 1) + 1),   AR = sum(R_a K_a) / sum K
      K_a[t+1] = (1 - d) K_a[t] + share_a * kappa * I[t]
  The shares sum to one by construction; a negative share (an industry with a very low return) is set to zero and the
  rest rescaled. omega = 3.0 is IFPRI's own setting (1dmodel.gms, beta1 = beta2 = 3.00). With omega = 0 new capital
  follows the existing capital shares. Tested 2 Oct 2026: for omega 0-5, higher omega steadily narrows the differences in
  rental rates; for omega 10 or more the linear rule overshoots (many industries get no new capital in some years and
  rental rates oscillate), so use 1-5 for sensitivity.

Documented baseline (0.3, opt-in: DynamicCGE(**documented_baseline())): growth path from the 193rd DBCC statement
  (8 July 2026; midpoints: 2026 4.0%, 2027-2030 5.5%; PSA actuals 2024-2025); depreciation 5.02% (Penn World Table 11.0
  capital detail, Philippines 2023: capital consumption / previous-year net stock); capital stock 1.96 x GDP for
  rent-earning capital (PWT net capital stock 2.42 x GDP less public capital, about 19% in IMF ICSD 2019), which sets
  kappa, the capital added per peso of investment. Labour growth by skill from PSA (below; 2 Oct 2026); the 1.5%
  placeholder is kept with documented_baseline(labour="placeholder").
  Sources and grades: docs/parameters.md.

Labour growth by skill (0.3, opt-in: labour_growth=psa_labour_growth(); in documented_baseline() since 2 Oct 2026)
  labour_growth may be one rate for all labour types (as before) or {year: {labour type: rate}}. psa_labour_growth()
  builds it from PSA data (data/raw/lfs, data/raw/population; OpenSTAT tables 0141B3FEMP7 and 0021A3BPOP1):
    2024, 2025  LFS annual employed persons by highest grade completed, mapped to the SAM's labour types:
                low (flab-n) = no grade completed + elementary undergraduate; medium (flab-p) = elementary graduate
                + junior high undergraduate; high (flab-s) = junior high completed and above (senior high,
                post-secondary, college). The SAM defines high as "finished secondary and/or tertiary schooling".
    2026        LFS January-July 2026 against January-July 2025, same mapping (the latest months published).
    2027-2030   total employment grows with PSA's projected population aged 15+ (2020 CPH-based; constant
                employment rate); the skill shares continue their 2023-2025 average annual change ("trend", default)
                or stay at their 2025 values ("constant", sensitivity).
  In the full-employment closure, labour supply = employment, so observed employment is the right series.

Industry baseline (0.3, opt-in: industry_targets=psa_industry_growth())
  Instead of one productivity rate for all activities, each of PSA's 16 industries (GVA by industry at constant 2018
  prices, OpenSTAT 0052B5BPRA1) grows as it did in 2024 and 2025. The instrument depends on what drives the
  industry in the model:
    construction            real investment demand for construction (the 2025 slump was the public investment cut);
    public administration   real government consumption of public administration;
    trade, financial        input intensity: that service used per unit of output by every industry (and, for trade,
                            per unit of trade margin). In the SAM, trade has no household demand (71% intermediate use,
                            29% margins) and financial services 69% intermediate and 30% government use;
    the other 12 industries productivity (TFP) of their SAM activities (same factor within an industry).
  Construction, public administration, trade and finance are pinned by demand in this closure, so productivity
  cannot move them (tried 2 Oct 2026: trade then needed +28% TFP in 2025). Later years (no industry data) keep the 2025 differences and grow together (one TFP rate,
  solved to hit the growth path); construction investment and public administration keep their 2025 level
  relative to the economy. With this option the baseline CONTAINS the actual 2025 construction slump: use it for
  shocks from 2026 on (e.g. a 2027 investment programme). Do not add a 2025 construction shock on top of it (that would count it twice).
  Real GDP is not targeted in those years; it follows from the industries (reported in the baseline table).

A scenario = the baseline exogenous path + shocks in chosen years. Because a shock that lowers
investment lowers the capital stock, its effect on GDP persists after the shock ends; this is the
effect a static model cannot show.

Every parameter below is an ASSUMPTION to be reviewed and documented by the team (see
docs/model.md, "Calibrating the dynamic baseline").

Usage
-----
>>> from pystdcge.dynamic import DynamicCGE
>>> d = DynamicCGE()                                   # default assumptions
>>> base = d.baseline()                                # calibrates TFP to the growth path
>>> sim = d.scenario({2025: {"qinv_scale": {"ccons": 0.85}}, 2026: {"qinv_scale": {"ccons": 0.85}}})
>>> d.compare(base, sim)
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from .cge import CGE

# Real GDP growth path (%). 2024-2025: PSA actual. 2026 onward: ASSUMPTIONS for illustration
# (2026 near the S&P 2.9% and ADB 3.3% forecasts of September 2026; 2027+ a recovery path).
# Replace with your own or the government's (DBCC) assumptions before use.
DEFAULT_GROWTH = {2024: 5.7, 2025: 4.4, 2026: 3.0, 2027: 5.0, 2028: 5.5, 2029: 5.5, 2030: 5.5}
# 193rd DBCC statement (8 July 2026): 2026 3.5-4.5%, 2027-2030 5.0-6.0% (midpoints); 2024-2025 PSA actual
DBCC_GROWTH = {2024: 5.7, 2025: 4.4, 2026: 4.0, 2027: 5.5, 2028: 5.5, 2029: 5.5, 2030: 5.5}
DEFAULT_ASSUMPTIONS = dict(
    base_year=2023,
    labour_growth=0.015,          # per year, all labour types (replace with LFS-based projections)
    depreciation=0.05,            # capital depreciation rate
    capital_growth_base=0.05,     # net capital growth in the benchmark year (calibrates kappa)
    closure="investment",         # long-run: full employment, investment-driven
    unemployed=(),
    capital="mobile",
    hybrid=False,                 # 0.3: short-run closure in shock years, gap closing afterwards (opt-in)
    gap_persistence=0.5,          # share of the employment gap left the next year (ASSUMPTION; 0 = closes at once)
    short_run_unemployed=("flab-n", "flab-p"),
    public_capital=None,          # 0.3: dict(phi=..., kg_gdp=..., delta_g=0.0352, e=0.77); None = off
    capital_allocation="mobile",  # 0.3: "putty-clay" = capital fixed by industry, new investment chases returns
    omega=3.0,                    # investment mobility (IFPRI 1dmodel.gms beta = 3.00); used with putty-clay
    capital_output=None,          # 0.3: rent-earning capital stock / GDP; if given, sets kappa (else capital_growth_base)
    industry_targets=None,        # 0.3: {year: {PSA industry: real GVA growth %}}; None = one TFP rate
    les=None,                     # 0.3: LES household demand (pystdcge.demand.les_briones2023()); None = Cobb-Douglas
    elasticities=None,            # 0.3.1: CGE elasticities (pystdcge.elasticities.elasticity_set); None = 0.2 defaults
    margins="composite",          # 0.3.1: CGE trade margins ("split" = IFPRI-style); "composite" = 0.2
)

# PSA GVA industries (OpenSTAT 0052B5BPRA1) -> activities of the IFPRI 2023 SAM
PSA_INDUSTRIES = {
    "Agriculture, forestry, and fishing": ["amaiz", "arice", "apuls", "aoils", "aroot", "avege", "asugr", "atoba", "acott",
                                           "afrui", "acoff", "aocrp", "acatt", "apoul", "aoliv", "afore", "afish"],
    "Mining and quarrying": ["amine"],
    "Manufacturing": ["afood", "abeve", "atext", "awood", "achem", "apetr", "anmet", "ametl", "amach", "aoman"],   # apetr: split SAM only
    "Electricity, steam, water and waste management": ["aelec", "awatr"],
    "Construction": ["acons"],
    "Wholesale and retail trade; repair of motor vehicles and motorcycles": ["atrad"],
    "Transportation and storage": ["atran"],
    "Accommodation and food service activities": ["ahotl"],
    "Information and communication": ["acomm"],
    "Financial and insurance activities": ["afsrv"],
    "Real estate and ownership of dwellings": ["areal"],
    "Professional and business services": ["absrv"],
    "Public administration and defense; compulsory social activities": ["apadm"],
    "Education": ["aeduc"],
    "Human health and social work activities": ["aheal"],
    "Other services": ["aosrv"],
}
# industries whose output is pinned by demand in the model, and the lever used for them: (instrument, commodity)
#   qinv: real investment demand; qg: real government consumption; use: input intensity of that service for all
#   industries (and per unit of trade margin). Trade has no household demand in the SAM (71% intermediate use,
#   29% margins); financial services 69% intermediate, 30% government. Productivity cannot move them.
INDUSTRY_DEMAND_INSTRUMENT = {"Construction": ("qinv", "ccons"),
                              "Public administration and defense; compulsory social activities": ("qg", "cpadm"),
                              "Wholesale and retail trade; repair of motor vehicles and motorcycles": ("use", "ctrad"),
                              "Financial and insurance activities": ("use", "cfsrv")}
LABOUR_EDUCATION = {"flab-n": ["No grade completed", "Elementary Undergraduate"],
                    "flab-p": ["Elementary Graduate", "Junior High Undergraduate"],
                    "flab-s": ["Junior High Completed", "Senior High School", "Post Secondary", "College"]}


def psa_industry_growth(years=(2024, 2025)) -> dict:
    """{year: {PSA industry: real GVA growth %}} from PSA OpenSTAT 0052B5BPRA1 (constant 2018 prices)."""
    from . import paths
    df = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GVA_by_industry_annual_2000-2025.csv", comment="#")
    df = df[(df["valuation"] == "At Constant 2018 Prices") & df["industry"].isin(list(PSA_INDUSTRIES))]
    v = df.pivot(index="year", columns="industry", values="value_million_php")
    return {y: {k: float((v.loc[y, k] / v.loc[y - 1, k] - 1) * 100) for k in PSA_INDUSTRIES} for y in years}


def psa_labour_growth(shares="trend", last_year=2030) -> dict:
    """{year: {labour type: growth rate}} from PSA LFS (2024-2026) and population projections (2027 on)."""
    from . import paths
    lfs = pd.read_csv(paths.DATA_RAW / "lfs" / "PSA_OpenSTAT_LFS_employed_by_highest_grade_2023-2026.csv", comment="#")
    by_type = lambda d: np.array([d[d["highest_grade_completed"].isin(v)]["employed_thousands"].sum()
                                  for v in LABOUR_EDUCATION.values()])
    ann = {y: by_type(lfs[(lfs["year"] == y) & (lfs["month"] == "Annual")]) for y in (2023, 2024, 2025)}
    months = ["January", "February", "March", "April", "May", "June", "July"]
    jj = {y: by_type(lfs[(lfs["year"] == y) & lfs["month"].isin(months)]) for y in (2025, 2026)}
    keys = list(LABOUR_EDUCATION)
    out = {y: dict(zip(keys, ann[y] / ann[y - 1] - 1)) for y in (2024, 2025)}
    out[2026] = dict(zip(keys, jj[2026] / jj[2025] - 1))
    pop = pd.read_csv(paths.DATA_RAW / "population" / "PSA_OpenSTAT_population_projections_2020CPH_2020-2030.csv", comment="#")
    p15 = pop[(pop["sex"] == "Both Sexes") & ~pop["age_group"].isin(["All Ages", "0-4", "5-9", "10-14"])]
    p15 = p15.groupby("year")["population_thousands"].sum()
    level = ann[2025] * (1 + np.array(list(out[2026].values())))      # 2026 level by type
    sh = level / level.sum()
    dsh = (ann[2025] / ann[2025].sum() - ann[2023] / ann[2023].sum()) / 2 if shares == "trend" else np.zeros(3)
    if shares not in ("trend", "constant"):
        raise ValueError("shares must be 'trend' or 'constant'")
    for y in range(2027, last_year + 1):
        new_sh = np.clip(sh + dsh, 0.01, None)
        new_sh = new_sh / new_sh.sum()
        new_level = level.sum() * float(p15[y] / p15[y - 1]) * new_sh
        out[y] = dict(zip(keys, new_level / level - 1))
        level, sh = new_level, new_sh
    return {y: {k: float(v) for k, v in d.items()} for y, d in out.items()}


def documented_baseline(labour="psa") -> dict:
    """The sourced baseline assumptions (0.3): DBCC growth path, PWT depreciation and capital stock, and (since
    2 Oct 2026) PSA labour growth by skill. labour="placeholder" keeps the 1.5% for all types (results of 2 Oct, 1:45 PM)."""
    d = dict(growth=dict(DBCC_GROWTH), depreciation=0.0502, capital_output=1.96)
    if labour == "psa":
        d["labour_growth"] = psa_labour_growth()
    elif labour != "placeholder":
        raise ValueError("labour must be 'psa' or 'placeholder'")
    return d
PUBLIC_CAPITAL_DEFAULTS = dict(delta_g=0.0352, e=0.77)


class _SolveFailed(Exception):
    """A trial solve inside the TFP search did not converge."""


def _robust_root(f, x0, xtol=1e-10):
    """Root of f near x0: widen a bracket outward (1%, 2%, 4%, ... up to 40%) using only points where the model
    solves, then brentq inside it. Used when the wide default bracket hits points where the model cannot solve."""
    f0 = f(x0)
    if f0 == 0:
        return x0
    for step in (0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.4):
        for x1 in (x0 * (1 + step), x0 * (1 - step)):
            try:
                f1 = f(x1)
            except _SolveFailed:
                continue
            if np.sign(f1) != np.sign(f0):
                lo, hi = sorted((x0, x1))
                return brentq(f, lo, hi, xtol=xtol)
    raise RuntimeError("TFP search: no bracket found within +-40% of last year's value")


@dataclass
class Path:
    years: list
    solutions: dict
    tfp: dict
    capital: dict
    table: pd.DataFrame = field(default=None)
    demand: dict = field(default=None)            # industry baseline levers: {year: {"qinv:ccons": f, ...}}


class DynamicCGE:
    def __init__(self, growth=None, sam=None, **assumptions):
        a = dict(DEFAULT_ASSUMPTIONS)
        a.update(assumptions)
        self.a = a
        self.growth = dict(DEFAULT_GROWTH if growth is None else growth)
        self.putty = a["capital_allocation"] == "putty-clay"
        if a["capital_allocation"] not in ("mobile", "putty-clay"):
            raise ValueError("capital_allocation must be 'mobile' or 'putty-clay'")
        kw = dict(closure=a["closure"], unemployed=a["unemployed"], capital="fixed" if self.putty else a["capital"],
                  les=a["les"], elasticities=a["elasticities"], margins=a["margins"])
        self.m = CGE(sam, **kw) if sam is not None else CGE.from_sam(**kw)
        if a["public_capital"] is not None:
            pc = dict(PUBLIC_CAPITAL_DEFAULTS, **a["public_capital"])
            missing = [k for k in ("phi", "kg_gdp") if k not in pc]
            if missing:
                raise ValueError(f"public_capital needs {missing}: take them from a source (see the module notes)")
            self.pc = pc
        if a["hybrid"]:
            kw_sr = dict(closure="keynesian", unemployed=a["short_run_unemployed"], capital="fixed", les=a["les"],
                         elasticities=a["elasticities"], margins=a["margins"])
            self.ms = CGE(sam, **kw_sr) if sam is not None else CGE.from_sam(**kw_sr)
        m = self.m
        self.kc = m.F.index("fcap")
        self.K0 = m.QFS0[self.kc]
        self.K0a = m.QF0[self.kc].copy()             # capital by activity (capital-income units, base rental 1)
        I0 = m.qinv.sum()
        if a["capital_output"]:
            b0 = m.solve()
            if not b0.ok:                            # 0.3.3 (rigging audit finding 3): never use an unsolved benchmark
                raise RuntimeError(f"Benchmark did not solve ({b0.message}, residual {b0.residual_max:.2e})")
            gdp0 = m.gdp(b0)["nominal_expenditure"]
            self.kappa = self.K0 / (a["capital_output"] * gdp0)   # capital units added per peso of real investment
        else:
            self.kappa = (a["capital_growth_base"] + a["depreciation"]) * self.K0 / I0
        self.years = [a["base_year"]] + sorted(self.growth)
        # labour by type (0.3): one rate (as before) or {year: {labour type: rate}}
        lg = a["labour_growth"]
        self.labs = [f for f in m.F if f.startswith("flab")]
        if isinstance(lg, dict):
            missing = [t for t in self.years[1:] if t not in lg]
            if missing:
                raise ValueError(f"labour_growth has no rates for {missing}")
            self.L_path, idx = {self.years[0]: {f: 1.0 for f in self.labs}}, {f: 1.0 for f in self.labs}
            for t in self.years[1:]:
                idx = {f: idx[f] * (1 + lg[t][f]) for f in self.labs}
                self.L_path[t] = idx
        else:
            self.L_path = None
        # industry baseline (0.3)
        self.ind_targets = a["industry_targets"] or {}
        self.groups = []
        if self.ind_targets:
            for name, acts in PSA_INDUSTRIES.items():
                inst = INDUSTRY_DEMAND_INSTRUMENT.get(name, ("tfp", None))
                self.groups.append((name, inst, np.array([m.A.index(x) for x in acts if x in m.A])))   # apetr: split SAM only

    # ------------------------------------------------------------------ one year
    def _spec(self, t, K, L_index, Y_index, tfp, extra=None, dem=None):
        m = self.m
        if isinstance(L_index, dict):
            qfs = {f: L_index[f] for f in m.F if f.startswith("flab")}
        else:
            qfs = {f: L_index for f in m.F if f.startswith("flab")}
        if self.putty:
            qfs["fcap"] = 1.0
        else:
            qfs["fcap"] = K / self.K0
        if np.ndim(tfp):                               # productivity by activity (industry baseline)
            tfp = {a: float(tfp[i]) for i, a in enumerate(m.A)}
        spec = {"qfs_scale": qfs, "tfp_scale": tfp, "qg_scale": Y_index, "iadj": Y_index,
                "trg_scale": Y_index, "fsav_scale": Y_index, "remit_scale": Y_index, "frow_in_scale": Y_index}
        items_of = {"qfs_scale": m.F, "tfp_scale": m.A, "qg_scale": m.C, "remit_scale": m.H, "frow_in_scale": m.F}
        for k, v in (extra or {}).items():
            if k in spec and not isinstance(v, dict) and not isinstance(spec[k], dict):
                spec[k] = spec[k] * v                  # scenario factors multiply the baseline level
            elif k in spec and k in items_of:
                # 0.3.1: a scenario dict (by commodity, activity, factor or household) multiplies the
                # baseline path too, instead of replacing it (before, e.g. a TFP shock for one industry wiped the
                # baseline productivity path; no published run used such a shock: they all shock qinv_scale only)
                base = spec[k] if isinstance(spec[k], dict) else {i: float(spec[k]) for i in items_of[k]}
                vv = v if isinstance(v, dict) else {i: float(v) for i in items_of[k]}
                spec[k] = {i: base.get(i, 1.0) * vv.get(i, 1.0) for i in dict.fromkeys(list(base) + list(vv))}
            else:
                spec[k] = v
        for key, f in (dem or {}).items():             # industry baseline levers, times any scenario factor
            inst, com = key.split(":")
            if inst == "qinv":
                q = dict(spec.get("qinv_scale") or {})
                q[com] = q.get(com, 1.0) * f
                spec["qinv_scale"] = q
            elif inst == "qg":
                g = spec["qg_scale"]
                g = dict(g) if isinstance(g, dict) else {c: float(g) for c in m.C}
                g[com] = g.get(com, 1.0) * f
                spec["qg_scale"] = g
            elif inst == "use":
                for k in ("ica_scale", "sm_scale"):
                    u = dict(spec.get(k) or {})
                    u[com] = u.get(com, 1.0) * f
                    spec[k] = u
        if self.putty:
            spec["kscale"] = {a: float(K[i] / self.K0a[i]) for i, a in enumerate(m.A) if self.K0a[i] > 0}
        return spec

    def _calibrate_industries(self, t, K, L_index, Y_index, extra, x, va_prev, tf_prev, dem_prev):
        """Industry baseline: productivity by industry and the two demand levels so each PSA industry's real value added grows
        as PSA reports for year t."""
        from scipy.optimize import root
        m, target = self.m, self.ind_targets[t]
        prev = np.full(len(m.A), float(tf_prev)) if np.ndim(tf_prev) == 0 else np.asarray(tf_prev, float)

        def unpack(z):
            tfv, dem = prev.copy(), dict(dem_prev)
            for j, (name, (inst, com), idx) in enumerate(self.groups):
                if inst == "tfp":
                    tfv[idx] = prev[idx] * np.exp(z[j])
                else:
                    key = f"{inst}:{com}"
                    dem[key] = dem_prev.get(key, 1.0) * np.exp(z[j])
            return tfv, dem

        state = {"x": x}

        def resid(z):
            tfv, dem = unpack(z)
            s = m.solve(self._spec(t, K, L_index, Y_index, tfv, extra, dem), x_start=state["x"])
            if not s.ok:
                return np.full(len(self.groups), 1e3)
            state["x"] = s.x
            va = s["QVA"]
            return np.array([va[idx].sum() / va_prev[idx].sum() - 1 - target[name] / 100
                             for name, _, idx in self.groups])

        g_all = self.growth[t] / 100
        z0 = np.array([np.log((1 + target[name] / 100) / (1 + g_all)) for name, _, _ in self.groups])
        out = root(resid, z0, method="hybr", options={"xtol": 1e-12})
        if np.abs(out.fun).max() > 1e-7:
            raise RuntimeError(f"Year {t}: industry calibration failed (max gap {np.abs(out.fun).max():.2e})")
        self._calib_x = state["x"]                    # a solution near the calibrated point (restart for the final solve)
        return unpack(out.x)

    def _short_run_spec(self, spec, t, K):
        """Anchor the short-run model to the baseline equilibrium of year t (hybrid closure)."""
        ms, bsol = self.ms, self.base.solutions[t]
        kc = ms.F.index("fcap")
        kshare = np.where(ms.QF0[kc] > 0, bsol["QF"][kc] / np.where(ms.QF0[kc] > 0, ms.QF0[kc], 1), 1.0)
        spec = dict(spec)
        spec["qfs_scale"] = dict(spec["qfs_scale"], fcap=1.0)
        if self.putty:
            spec["kscale"] = {a: float(K[i] / self.K0a[i]) for i, a in enumerate(ms.A) if self.K0a[i] > 0}
        else:
            spec["kscale"] = {a: float(kshare[i] * K / self.base.capital[t]) for i, a in enumerate(ms.A)}
        spec["exr"] = float(bsol["EXR"])
        spec["mpsadj"] = float(bsol["MPSADJ"])
        spec["wbar"] = {f: float(bsol["WF"][k] / bsol["CPI"]) for k, f in enumerate(ms.F) if f in ms.unemployed}
        return spec

    def _short_run_start(self, t):
        """Starting point for the short-run solver: the baseline solution of year t in its layout."""
        ms, b = self.ms, self.base.solutions[t]
        x = ms.x0()
        x[ms.slices["QA"]] = b["QA"] / ms.QA0
        x[ms.slices["PDS"]] = b["PDS"][ms.iD]
        x[ms.slices["PQ"]] = b["PQ"][ms.iQ]
        x[ms.slices["WF"]] = b["WF"][ms.iFM]
        x[ms.slices["RK"]] = b["W"][ms.kcap, ms.iK]
        x[ms.slices["EXR"]] = b["FSAV"] / ms.fsav
        x[ms.slices["WALRAS"]] = 0.0
        return x

    def _run(self, shocks=None, tfp_path=None, calibrate=False):
        m = self.m
        hybrid = bool(self.a["hybrid"]) and shocks is not None and not calibrate
        unemp = [k for k, f in enumerate(m.F) if f in self.a["short_run_unemployed"]]
        gap = np.zeros(len(m.F))                     # employment gap carried into the year (share of supply)
        pubcap = self.a["public_capital"] is not None and shocks is not None and not calibrate
        dKG = 0.0                                    # public capital relative to the baseline (₱ bn, SAM prices)
        icons = m.C.index("ccons")
        sols, tfps, caps, rows, dems = {}, {}, {}, [], {}
        K = self.K0a.copy() if self.putty else self.K0
        Ktot0 = float(np.sum(self.K0a)) if self.putty else self.K0
        Y_index = 1.0
        x = None
        real0 = None
        for i, t in enumerate(self.years):
            if self.L_path is not None:
                L_index = self.L_path[t]
            else:
                L_index = (1 + self.a["labour_growth"]) ** i
            if i > 0:
                Y_index *= 1 + self.growth[t] / 100
            extra = (shocks or {}).get(t)
            dem = {}
            if calibrate and i > 0:
                prev_t = self.years[i - 1]
                dem = dict(dems[prev_t])
                if t in self.ind_targets:
                    tf, dem = self._calibrate_industries(t, K, L_index, Y_index, extra, x, sols[prev_t]["QVA"],
                                                         tfps[prev_t], dems[prev_t])
                elif np.ndim(tfps[prev_t]) == 0:
                    target = real_prev * (1 + self.growth[t] / 100)
                    def gap(tf):
                        s = m.solve(self._spec(t, K, L_index, Y_index, tf, extra, dem), x_start=x)
                        if not s.ok:
                            raise _SolveFailed
                        return m.gdp(s)["real"] - target
                    try:
                        tf = brentq(gap, tfps[prev_t] * 0.8, tfps[prev_t] * 1.3, xtol=1e-10)
                    except _SolveFailed:             # 0.3: search outward from last year's value instead
                        tf = _robust_root(gap, tfps[prev_t], xtol=1e-10)
                else:                                # industry baseline after the data years: one common TFP rate
                    target = real_prev * (1 + self.growth[t] / 100)
                    tprev = np.asarray(tfps[prev_t], float)
                    def gap(sc):
                        s = m.solve(self._spec(t, K, L_index, Y_index, sc * tprev, extra, dem), x_start=x)
                        if not s.ok:
                            raise _SolveFailed
                        return m.gdp(s)["real"] - target
                    tf = _robust_root(gap, 1.0, xtol=1e-12) * tprev
            else:
                tf = 1.0 if i == 0 else tfp_path[t]
                if i > 0 and not calibrate and getattr(self, "base", None) is not None and self.base.demand:
                    dem = dict(self.base.demand[t])
            tf_used = tf
            dKG_start = dKG
            if pubcap and dKG:
                KGb = self.pc["kg_gdp"] * float(self.base.table.loc[t, "real_gdp"])
                tf_used = tf * (1 + dKG / KGb) ** self.pc["phi"]
            spec = self._spec(t, K, L_index, Y_index, tf_used, extra, dem)
            short = hybrid and t in shocks
            if short:
                model = self.ms
                sol = model.solve(self._short_run_spec(spec, t, K), x_start=self._short_run_start(t))
            else:
                model = m
                if hybrid and gap.any():
                    spec["qfs_scale"] = {f: v * (1 - gap[m.F.index(f)]) for f, v in spec["qfs_scale"].items()}
                sol = m.solve(spec, x_start=x)
                if not sol.ok and calibrate and t in self.ind_targets:     # 0.3: restart from the calibration's point
                    sol = m.solve(spec, x_start=self._calib_x)
                if not sol.ok and not calibrate and getattr(self, "base", None) is not None:
                    sol = m.solve(spec, x_start=self.base.solutions[t].x)  # 0.3: restart from the baseline's solution
            if not sol.ok:
                raise RuntimeError(f"Year {t}: solve failed ({sol.message}, residual {sol.residual_max:.2e})")
            if not short:
                x = sol.x
            if hybrid:
                if short:                            # gap opened this year, relative to the labour supply
                    Lv = (np.array([L_index.get(f, 1.0) for f in m.F]) if isinstance(L_index, dict) else L_index)
                    supply = m.QFS0 * Lv
                    gap = np.zeros(len(m.F))
                    gap[unemp] = 1 - sol["EMP"][unemp] / supply[unemp]
                gap_now = gap.copy()
                gap = gap * self.a["gap_persistence"]
            if pubcap:
                dIG = float(sol["QINV"][icons] - self.base.solutions[t]["QINV"][icons])
                dKG = (1 - self.pc["delta_g"]) * dKG + self.pc["e"] * dIG
            g = model.gdp(sol)
            real_prev = g["real"]
            if real0 is None:
                real0 = g["real"]
            sols[t], tfps[t], caps[t], dems[t] = sol, tf, (K.copy() if self.putty else K), dem
            Ktot = float(np.sum(K)) if self.putty else K
            rows.append(dict(year=t, real_gdp=g["real"], nominal_gdp=g["nominal_expenditure"],
                             real_consumption=float(sol["QH"].sum()), real_investment=float(sol["QINV"].sum()),
                             capital_stock_index=Ktot / Ktot0, tfp=tf, cpi=sol["CPI"], exr=sol["EXR"],
                             walras=sol["WALRAS"],
                             **({"closure": "short run" if short else "long run",
                                 "employment_gap_low_skill_pct": -gap_now[unemp[0]] * 100 if unemp else 0.0}
                                if hybrid else {}),
                             **({"public_capital_gap_pct": dKG_start / (self.pc["kg_gdp"] * float(self.base.table.loc[t, "real_gdp"])) * 100}
                                if pubcap else {})))
            # capital for next year from this year's real investment
            if self.putty:
                K = (1 - self.a["depreciation"]) * K + self.allocation(sol) * self.kappa * float(sol["QINV"].sum())
            else:
                K = (1 - self.a["depreciation"]) * K + self.kappa * float(sol["QINV"].sum())
        df = pd.DataFrame(rows).set_index("year")
        df["real_gdp_growth_pct"] = df["real_gdp"].pct_change() * 100
        return Path(self.years, sols, tfps, caps, df, dems if any(dems.values()) else None)

    def allocation(self, sol) -> np.ndarray:
        """Shares of new capital by activity (Thurlow 2004, eq. Q; IFPRI recursive dynamic model)."""
        QF = np.asarray(sol["QF"][self.kc], float)
        R = np.asarray(sol["W"][self.kc], float)
        AR = float((R * QF).sum() / QF.sum())
        share = QF / QF.sum() * (self.a["omega"] * (R / AR - 1) + 1)
        share = np.clip(share, 0.0, None)
        return share / share.sum()

    # ------------------------------------------------------------------ public API
    def baseline(self) -> Path:
        """Calibrate the TFP path so real GDP follows `growth`."""
        self.base = self._run(calibrate=True)
        return self.base

    def scenario(self, shocks: dict) -> Path:
        """shocks = {year: CGE shock spec}. Uses the baseline TFP path (run baseline() first)."""
        if not hasattr(self, "base"):
            self.baseline()
        return self._run(shocks=shocks, tfp_path=self.base.tfp)

    @staticmethod
    def compare(base: Path, sim: Path) -> pd.DataFrame:
        b, s = base.table, sim.table
        out = pd.DataFrame({
            "base_growth_pct": b["real_gdp_growth_pct"],
            "sim_growth_pct": s["real_gdp_growth_pct"],
            "gdp_gap_pct": (s["real_gdp"] / b["real_gdp"] - 1) * 100,
            "gdp_gap_bn": s["real_gdp"] - b["real_gdp"],
            "consumption_gap_pct": (s["real_consumption"] / b["real_consumption"] - 1) * 100,
            "capital_gap_pct": (s["capital_stock_index"] / b["capital_stock_index"] - 1) * 100,
        })
        out.loc["cumulative", "gdp_gap_bn"] = out["gdp_gap_bn"].sum()
        return out
