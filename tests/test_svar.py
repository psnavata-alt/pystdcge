"""Structural VARs (svar.py) and the VAR-to-CGE link (macrolink.py).

V7 checks the VAR code against statsmodels (an independent, widely used implementation) and against exact properties
on simulated data with a known structure; M2 checks the link to the CGE."""
import numpy as np
import pandas as pd
import pytest

from pystdcge import svar

A1 = np.array([[0.5, 0, 0], [0.2, 0.4, 0.1], [0.1, -0.2, 0.3]])
A2 = np.array([[0.2, 0, 0], [0, 0.1, 0], [0.05, 0, 0.1]])        # variable a is exogenous to b and c
P = np.array([[1.0, 0, 0], [0.5, 0.8, 0], [0.3, 0.2, 0.6]])


@pytest.fixture(scope="module")
def data():
    rng = np.random.default_rng(7)
    Y = np.zeros((3000, 3))
    for t in range(2, len(Y)):
        Y[t] = 0.1 + A1 @ Y[t - 1] + A2 @ Y[t - 2] + P @ rng.standard_normal(3)
    return pd.DataFrame(Y, columns=["a", "b", "c"])


def test_equals_statsmodels(data):
    from statsmodels.tsa.api import VAR
    m, r = svar.fit(data, 2, sigma_dof="ols"), VAR(data).fit(2)
    assert np.abs(np.hstack(r.coefs) - m.A).max() < 1e-12
    assert np.abs(r.intercept - m.C[:, 0]).max() < 1e-12
    assert np.abs(r.sigma_u.values - m.Sigma).max() < 1e-12
    assert np.abs(r.irf(10).orth_irfs - svar.irf(m, svar.cholesky(m), 10)).max() < 1e-12


def test_recovers_truth(data):
    m = svar.fit(data, 2)
    assert np.abs(m.lag(1) - A1).max() < 0.08 and np.abs(svar.cholesky(m) - P).max() < 0.05


def test_block_exogeneity(data):
    m = svar.fit(data, 2, exog_block=["a"])
    assert np.all(m.A[0, [1, 2, 4, 5]] == 0)
    assert np.abs(svar.irf(m, svar.cholesky(m), 24)[:, 0, 1:]).max() == 0


def test_historical_decomposition_is_exact(data):
    m = svar.fit(data, 2, exog_block=["a"])
    hd = svar.historical_decomposition(m, svar.cholesky(m))
    assert np.abs(hd["baseline"] + hd["contribution"].sum(axis=2) - data.to_numpy()[2:]).max() < 1e-10


def test_counterfactual_holds_variable(data):
    m = svar.fit(data, 2, exog_block=["a"])
    assert np.abs(svar.counterfactual_irf(m, svar.cholesky(m), 1, "c", 12)[:, 2]).max() < 1e-12


def test_sign_restrictions(data):
    m = svar.fit(data, 2)
    acc = svar.sign_restrictions(m, 1, {"b": 1, "c": 1}, horizons=(0, 1), draws=100)
    assert len(acc) == 100
    for B in acc:
        assert np.abs(B @ B.T - m.Sigma).max() < 1e-12
        assert (svar.irf(m, B, 1)[:, [1, 2], 1] > 0).all()


def test_ar_surprise_orthogonal(data):
    s = svar.ar_surprise(data["b"], 2)
    X = np.column_stack([data["b"].shift(1).iloc[2:], data["b"].shift(2).iloc[2:], np.ones(len(s))])
    assert np.abs(X.T @ s.values).max() < 1e-8


def test_bvar_limits(data):
    loose, tight = svar.bvar_minnesota(data, 2, lam=1e4).model(), svar.bvar_minnesota(data, 2, lam=1e-5).model()
    assert np.abs(loose.A - svar.fit(data, 2).A).max() < 1e-8
    assert np.abs(tight.A).max() < 1e-5
    B, S = svar.bvar_minnesota(data, 2).draw(2)[0]
    assert B.shape == (7, 3) and np.all(np.linalg.eigvalsh(S) > 0)


def test_bootstrap_bands_cover_point(data):
    m = svar.fit(data.iloc[:400], 2)
    b = svar.bootstrap_irf(m, 8, reps=100, seed=3)
    assert (b["lower"] <= b["point"] + 1e-9).mean() > 0.95 and (b["upper"] >= b["point"] - 1e-9).mean() > 0.95


def test_macrolink():
    """M2: zero change = base; an FDI fall enters as foreign savings by its share of GDP and lowers investment in the
    savings-driven closure; the keynesian closure refuses the foreign-savings channel."""
    from pystdcge.cge import CGE
    from pystdcge import macrolink as ML
    m = CGE.from_sam(closure="savings")
    b = m.solve()
    assert np.abs(m.solve(ML.cge_shocks(m))["QA"] - b["QA"]).max() == 0
    sp = ML.cge_shocks(m, fdi_usd_m=-1000, php_per_usd=58.0, gdp_bn=28009.93)
    assert abs(sp["fsav_scale"] - (1 - 1000 * 58.0 / 1000 / 28009.93 * ML.sam_gdp(m) / m.fsav)) < 1e-12
    s = m.solve(sp)
    assert s.ok and s["QINV"].sum() < b["QINV"].sum()
    k = CGE.from_sam(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
    with pytest.raises(ValueError):
        ML.cge_shocks(k, fdi_usd_m=-1000, php_per_usd=58.0, gdp_bn=28009.93, fdi_channel="foreign_savings")
    assert ML.annual(np.arange(1, 13), 12) == 6.5
