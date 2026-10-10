"""The static CGE's mathematical properties (C1-C8): calibration, replication, homogeneity, Walras' law, GDP identity,
direction of effects, multiplier bounds, and the same tests on a second SAM."""
import numpy as np
import pytest

from conftest import SHOCK, SHORT_RUN
from pystdcge import paths


def test_benchmark_residuals(models):
    """C1: every equation holds at the SAM values."""
    for k, m in models.items():
        R, _ = m.evaluate(m.x0(), m.make_shocks())
        assert np.abs(R).max() < 1e-7, k


def test_reproduces_sam(models):
    """C2: the SAM rebuilt from the benchmark solution equals the SAM."""
    m = models["long run"]
    gap = float((m.rebuild_sam(m.solve()) - m.sam.table).abs().values.max())
    assert gap < 1e-5


def test_homogeneity(models):
    """C3: doubling the numeraire doubles all prices and leaves all quantities unchanged."""
    for k, m in models.items():
        s = m.solve({"exr": 2.0} if m.closure == "keynesian" else {"cpi": 2.0})
        assert np.abs(s["QA"] / m.QA0 - 1).max() < 1e-7, k
        assert np.abs(s["PQ"][m.iQ] / 2 - 1).max() < 1e-7, k


def test_walras(models):
    """C4: the savings-investment slack is zero after a large shock, in every closure."""
    for k, m in models.items():
        s = m.solve(SHOCK)
        assert s.ok, k
        assert abs(s["WALRAS"]) / m.qinv.sum() < 1e-9, k


def test_gdp_identity(models):
    """C5: GDP by expenditure equals GDP by income in every shocked solution."""
    for k, m in models.items():
        g = m.gdp(m.solve(SHOCK))
        assert abs(g["nominal_expenditure"] - g["nominal_income"]) < 1e-6, k


def test_direction_of_effects(models):
    """C6: an import-price rise for chemicals and petroleum lowers real GDP and consumption; a remittance cut lowers
    consumption; a construction-investment cut lowers real GDP in the short run."""
    m = models["long run"]
    b = m.solve()
    s = m.solve({"pwm_scale": {"cchem": 1.2}})
    assert m.gdp(s)["real"] < m.gdp(b)["real"] and s["QH"].sum() < b["QH"].sum()
    assert m.solve({"remit_scale": 0.9})["QH"].sum() < b["QH"].sum()
    k = models["short run"]
    assert k.gdp(k.solve({"qinv_scale": {"ccons": 0.9}}))["real"] < k.gdp(k.solve())["real"]


def test_multiplier_bounds(models):
    """C7: the short-run CGE GDP multiplier of construction investment is positive and below the fixed-price SAM bound."""
    from pystdcge.multiplier import SAMMultiplier
    k = models["short run"]
    kb, ks = k.solve(), k.solve({"qinv_scale": {"ccons": 0.9}})
    cut = 0.1 * k.qinv[k.C.index("ccons")]
    cge_mult = (k.gdp(kb)["real"] - k.gdp(ks)["real"]) / cut
    dy = SAMMultiplier(k.sam0).shock({"ccons": 1.0})
    va = sum(dy[f] for f in ("flab-n", "flab-p", "flab-s", "flnd", "fcap"))
    assert 0 < cge_mult < va


@pytest.mark.slow
def test_second_sam_2018():
    """C8: on the IFPRI 2018 SAM (balanced first; activity tax instead of a capital tax) C1-C5 hold in all closures."""
    from pystdcge.cge import CGE
    for kw in ({}, {"closure": "savings"}, SHORT_RUN):
        m = CGE.from_sam(paths.SAM_2018, **kw)
        assert np.abs(m.evaluate(m.x0(), m.make_shocks())[0]).max() < 1e-7
        b = m.solve()
        assert (m.rebuild_sam(b) - m.sam.table).abs().values.max() < 1e-5
        h = m.solve({"exr": 2.0} if m.closure == "keynesian" else {"cpi": 2.0})
        assert np.abs(h["QA"] / m.QA0 - 1).max() < 1e-7
        s = m.solve(SHOCK)
        g = m.gdp(s)
        assert s.ok and abs(s["WALRAS"]) / m.qinv.sum() < 1e-9 and abs(g["nominal_expenditure"] - g["nominal_income"]) < 1e-6
