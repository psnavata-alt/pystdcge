"""Model extensions (E1, H1, S1, S2): sourced elasticities, LES household demand, petroleum-split SAM, named settings."""
import numpy as np
import pytest

from conftest import SHORT_RUN
from pystdcge import paths

pytestmark = pytest.mark.slow


def test_elasticity_sets():
    """E1: each sourced elasticity set covers every sector, reproduces the benchmark and is homogeneous."""
    from pystdcge.cge import CGE
    from pystdcge.elasticities import elasticity_set
    for name in ("gtap", "ph", "ph_pcgem_cet"):
        el = elasticity_set(name)
        for kw in ({}, SHORT_RUN):
            m = CGE.from_sam(elasticities=el, **kw)
            assert all(len(el[k]) == n for k, n in (("sigma_va", len(m.A)), ("sigma_q", len(m.C)), ("omega_t", len(m.C))))
            assert np.abs(m.evaluate(m.x0(), m.make_shocks())[0]).max() < 1e-7
            h = m.solve({"exr": 2.0} if m.closure == "keynesian" else {"cpi": 2.0})
            assert np.abs(h["QA"] / m.QA0 - 1).max() < 1e-7, (name, kw)


def test_les_demand():
    """H1: LES demand (Briones et al. 2023) reproduces the SAM, is homogeneous, satisfies Engel aggregation, has
    plausible Frisch parameters, and makes food a necessity (food consumption falls less than with Cobb-Douglas)."""
    from pystdcge.cge import CGE
    from pystdcge.demand import les_briones2023, les_usda2011, usda_frisch
    les = les_briones2023()
    for name, kw in (("long", {}), ("short", SHORT_RUN)):
        m = CGE.from_sam(les=les, **kw)
        b = m.solve()
        S = m.rebuild_sam(b)
        assert b.ok and (S - m.sam.table.loc[S.index, S.columns]).abs().to_numpy().max() < 1e-6
        if name == "long":
            assert np.abs(m.solve({"cpi": 1.1})["QA"] / b["QA"] - 1).max() < 1e-8
        assert np.abs(m.les["mb"].sum(axis=0) - 1).max() < 1e-12
        assert (m.les["gamma"] <= m.sam.table.loc[m.C, m.H].values + 1e-9).all()
        assert -3 < m.les["frisch"].min() and m.les["frisch"].max() < -0.5
    cd, le = CGE.from_sam(), CGE.from_sam(les=les)
    i = cd.C.index("cfood")
    d = {}
    for nm, mm in (("CD", cd), ("LES", le)):
        b0, s1 = mm.solve(), mm.solve({"pwm_scale": {"cchem": 1.12}})
        d[nm] = s1["QH"][i].sum() / b0["QH"][i].sum() - 1
    assert d["LES"] > d["CD"]
    mu = CGE.from_sam(les=les_usda2011())
    bu = mu.solve()
    Su = mu.rebuild_sam(bu)
    assert bu.ok and (Su - mu.sam.table.loc[Su.index, Su.columns]).abs().to_numpy().max() < 1e-6
    assert -3 < usda_frisch() < -0.5


def test_petroleum_split_sam():
    """S1: the petroleum-split SAM leaves every other account unchanged, balances, calibrates, is homogeneous, and
    world oil +20% raises the refined-petroleum price substantially. (Rebuilding it needs the PSA I-O tables.)"""
    from pystdcge.cge import CGE
    from pystdcge.oil import cge_oil_shock
    from pystdcge.sam import SAM
    saved = SAM.load(paths.SAM_2023_PETR)
    orig = SAM.load(paths.SAM_2023).table
    keep = [c for c in orig.index if c not in ("achem", "cchem")]
    assert (saved.table.loc[keep, keep] - orig.loc[keep, keep]).abs().to_numpy().max() < 1e-9
    assert saved.check(tol=1e-6, verbose=False)["balanced"]
    m = CGE.from_sam(paths.SAM_2023_PETR)
    b = m.solve()
    Sm = m.rebuild_sam(b)
    assert (Sm - m.sam.table.loc[Sm.index, Sm.columns]).abs().to_numpy().max() < 1e-6
    assert np.abs(m.solve({"cpi": 1.1})["QA"] / b["QA"] - 1).max() < 1e-8
    s = m.solve(cge_oil_shock(m, 0.2))
    assert s.ok and s["PQ"][m.C.index("cpetr")] / b["PQ"][m.C.index("cpetr")] - 1 > 0.05


def test_named_settings():
    """S2: "default" builds exactly the default model; "extended" passes C2-C5 and its dynamic model passes Y1."""
    from pystdcge import settings as ST
    from pystdcge.cge import CGE
    from pystdcge.dynamic import DynamicCGE
    a, b = ST.cge_model("default").solve(), CGE.from_sam().solve()
    assert all(np.array_equal(np.asarray(a[k]), np.asarray(b[k])) for k in ("QA", "PQ", "EH", "WF"))
    for cl in (SHORT_RUN, {}):
        m = ST.cge_model("extended", **cl)
        bs = m.solve()
        assert bs.ok and (m.rebuild_sam(bs) - m.sam.table).abs().values.max() < 1e-5
        h = m.solve({"exr": 2.0} if m.closure == "keynesian" else {"cpi": 2.0})
        assert np.abs(h["QA"] / m.QA0 - 1).max() < 1e-7
        s = m.solve({"pwm_scale": {"cpetr": 1.3}, "remit_scale": 0.8, "qinv_scale": {"ccons": 0.8}})
        g = m.gdp(s)
        assert s.ok and abs(s["WALRAS"]) / m.qinv.sum() < 1e-9 and abs(g["nominal_expenditure"] - g["nominal_income"]) < 1e-6
    d = DynamicCGE(**ST.dynamic_kwargs("extended"))
    base = d.baseline()
    assert np.abs(base.table["real_gdp_growth_pct"].values[1:] - np.array([d.growth[t] for t in d.years[1:]])).max() < 1e-6
    assert (d.scenario({}).table.real_gdp - base.table.real_gdp).abs().max() < 1e-6
