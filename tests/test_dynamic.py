"""Recursive-dynamic model (Y1-Y5, L1): baselines hit their targets and a zero shock reproduces them exactly."""
import numpy as np
import pandas as pd
import pytest

from pystdcge import paths

pytestmark = pytest.mark.slow
CUT = {2025: {"qinv_scale": {"ccons": 0.9}}}          # real construction investment -10% in 2025


def test_baseline_and_zero_shock():
    """Y1: the baseline hits the target growth path; a zero-shock scenario reproduces it."""
    from pystdcge.dynamic import DynamicCGE
    d = DynamicCGE()
    b = d.baseline()
    target = np.array([d.growth[t] for t in d.years[1:]])
    assert np.abs(b.table["real_gdp_growth_pct"].values[1:] - target).max() < 1e-6
    assert (d.scenario({}).table.real_gdp - b.table.real_gdp).abs().max() < 1e-6


def test_hybrid_closure():
    """Y2: zero shock in a short-run year reproduces the baseline; the low-skill employment gap decays by the
    persistence factor; the cumulative GDP loss exceeds the long-run closure's."""
    from pystdcge.dynamic import DynamicCGE
    d = DynamicCGE(hybrid=True)
    b = d.baseline()
    assert (d.scenario({2025: {}}).table.real_gdp - b.table.real_gdp).abs().max() < 1e-6
    s = d.scenario(CUT)
    g = s.table["employment_gap_low_skill_pct"]
    rho = d.a["gap_persistence"]
    assert g.loc[2025] < 0
    assert np.abs(g.loc[2026:].values - g.loc[2025] * rho ** np.arange(1, len(g.loc[2026:]) + 1)).max() < 1e-6
    lr = DynamicCGE()
    lr.baseline()
    cum_h = d.compare(b, s).loc["cumulative", "gdp_gap_bn"]
    cum_l = lr.compare(lr.base, lr.scenario(CUT)).loc["cumulative", "gdp_gap_bn"]
    assert cum_h < cum_l < 0


def test_public_capital_channel():
    """Y3: phi = 0 equals the model without the channel; the extra loss is close to proportional to phi.
    kg_gdp = 1.0 is a TEST VALUE, not an estimate."""
    from pystdcge.dynamic import DynamicCGE
    ref = DynamicCGE()
    rb = ref.baseline()
    r = ref.compare(rb, ref.scenario(CUT))
    res = {}
    for phi in (0.0, 0.1, 0.2):
        d = DynamicCGE(public_capital={"phi": phi, "kg_gdp": 1.0})
        b = d.baseline()
        res[phi] = d.compare(b, d.scenario(CUT))
    assert (res[0.0]["gdp_gap_pct"] - r["gdp_gap_pct"]).abs().max() < 1e-9
    x1 = res[0.1].loc[2030, "gdp_gap_pct"] - r.loc[2030, "gdp_gap_pct"]
    x2 = res[0.2].loc[2030, "gdp_gap_pct"] - r.loc[2030, "gdp_gap_pct"]
    assert x1 < 0 and abs(x2 / x1 - 2) < 0.1


def test_putty_clay_capital():
    """Y4: capital by industry with the documented baseline: growth path hit, zero shock exact, new-capital shares valid,
    plausible capital growth, higher investment mobility narrows rental-rate dispersion."""
    from pystdcge.dynamic import DynamicCGE, documented_baseline, DBCC_GROWTH
    d = DynamicCGE(capital_allocation="putty-clay", **documented_baseline())
    b = d.baseline()
    assert np.abs(b.table["real_gdp_growth_pct"].values[1:] - np.array([DBCC_GROWTH[t] for t in d.years[1:]])).max() < 1e-6
    assert (d.scenario({2025: {}}).table.real_gdp - b.table.real_gdp).abs().max() < 1e-6
    assert all(abs(x.sum() - 1) < 1e-12 and x.min() >= 0 for x in (d.allocation(b.solutions[t]) for t in d.years))
    assert 5 <= (b.table.loc[2024, "capital_stock_index"] - 1) * 100 <= 9
    cv = []
    for om in (0.0, 1.0, 3.0, 5.0):
        dd = DynamicCGE(capital_allocation="putty-clay", omega=om, **documented_baseline())
        R = dd.baseline().solutions[2030]["W"][dd.kc]
        cv.append(float(R.std() / R.mean()))
    assert cv == sorted(cv, reverse=True)
    s = d.scenario(CUT)
    ia = d.m.A.index("acons")
    assert s.capital[2030][ia] < b.capital[2030][ia]


def test_industry_baseline():
    """Y5: each of PSA's 16 industries grows as PSA reports for 2024 and 2025; real GDP then within 0.2 pp of PSA."""
    from pystdcge.dynamic import DynamicCGE, documented_baseline, psa_industry_growth, PSA_INDUSTRIES
    tg = psa_industry_growth()
    d = DynamicCGE(capital_allocation="putty-clay", industry_targets=tg, **documented_baseline())
    b = d.baseline()
    m, miss = d.m, 0.0
    for t in (2024, 2025):
        va, vp = b.solutions[t]["QVA"], b.solutions[t - 1]["QVA"]
        for n, acts in PSA_INDUSTRIES.items():
            ix = [m.A.index(a) for a in acts if a in m.A]
            miss = max(miss, abs((va[ix].sum() / vp[ix].sum() - 1) * 100 - tg[t][n]))
    assert miss < 1e-6
    psa_gdp = {2024: 5.71, 2025: 4.40}                       # PSA real GDP growth, constant 2018 prices
    assert max(abs(b.table.loc[t, "real_gdp_growth_pct"] - g) for t, g in psa_gdp.items()) < 0.2
    assert (d.scenario({}).table.real_gdp / b.table.real_gdp - 1).abs().max() < 1e-9


def test_labour_growth_by_skill():
    """L1: labour supply growth by skill reproduces PSA's Labour Force Survey and the population projections."""
    from pystdcge.dynamic import DynamicCGE, psa_labour_growth, LABOUR_EDUCATION
    lg = psa_labour_growth()
    lfs = pd.read_csv(paths.DATA_RAW / "lfs" / "PSA_OpenSTAT_LFS_employed_by_highest_grade_2023-2026.csv", comment="#")
    ann = lambda y, k: lfs[(lfs.year == y) & (lfs.month == "Annual") & lfs.highest_grade_completed.isin(LABOUR_EDUCATION[k])].employed_thousands.sum()
    assert max(abs(lg[y][k] - (ann(y, k) / ann(y - 1, k) - 1)) for y in (2024, 2025) for k in LABOUR_EDUCATION) < 1e-12
    d = DynamicCGE(labour_growth=lg)
    b = d.baseline()
    k = d.m.F.index("flab-s")
    cum = np.prod([1 + lg[y]["flab-s"] for y in range(2024, 2031)])
    assert abs(b.solutions[2030]["EMP"][k] / d.m.QFS0[k] - cum) < 1e-8
