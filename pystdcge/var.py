"""Time-series tools: regressions with Newey-West errors, VARs (statsmodels), Cholesky SVARs, local projections.
For block-exogenous, sign-restricted and Bayesian VARs, historical decompositions and counterfactuals, see svar.py.

Two p-value conventions are offered for Newey-West regressions, and both should be reported when samples are small:
  'large'  statsmodels default: normal distribution, no small-sample scaling.
  'stata'  Stata's `newey`: t distribution with n-k degrees of freedom and an n/(n-k) scaling.

Usage
-----
>>> from pystdcge import var
>>> df = var.load_quarterly("my_quarterly_panel.csv")        # a date column and one column per variable
>>> var.newey_west(df, "fx", ["gpr", "oil"], lags=4, convention="stata")
>>> res = var.fit_var(df[["oil", "gpr", "fx", "gdp"]], lags=1)     # Cholesky order = column order
>>> var.irf_table(res, impulse="gpr", steps=8)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.tsa.api import VAR

def load_quarterly(path, date_col: str = "quarter") -> pd.DataFrame:
    """A quarterly panel from a CSV file: a column of quarters ('2015Q1', ...) and one column per variable.
    Raises an error on missing values, which VARs cannot handle."""
    raw = pd.read_csv(path)
    raw.index = pd.PeriodIndex(raw.pop(date_col), freq="Q")
    raw = raw.apply(pd.to_numeric, errors="coerce")
    if raw.isna().any().any():
        raise ValueError("Missing values in the panel")
    return raw


def add_lags(df, col, lags):
    out = df.copy()
    for L in range(1, lags + 1):
        out[f"L{L}.{col}"] = out[col].shift(L)
    return out


def newey_west(df, y, xs, lags=4, convention="large", test=None) -> dict:
    """OLS of y on xs (with a constant), Newey-West (Bartlett) standard errors with `lags` lags.
    convention: 'large' (statsmodels) or 'stata' (t with n-k df and n/(n-k) scaling).
    test: list of regressors for a joint Wald test (e.g. the lags)."""
    d = df[[y] + xs].dropna()
    X = sm.add_constant(d[xs])
    fit = sm.OLS(d[y], X).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
    n, k = X.shape
    cov = fit.cov_params()
    if convention == "stata":
        cov = cov * n / (n - k)
    se = np.sqrt(np.diag(cov))
    tvals = fit.params.values / se
    if convention == "stata":
        p = 2 * stats.t.sf(np.abs(tvals), n - k)
    else:
        p = 2 * stats.norm.sf(np.abs(tvals))
    table = pd.DataFrame({"coef": fit.params.values, "se": se, "t": tvals, "p": p}, index=X.columns)
    out = dict(table=table, n=n, k=k, r2=fit.rsquared, convention=convention)
    if test:
        R = np.zeros((len(test), k))
        for i, name in enumerate(test):
            R[i, list(X.columns).index(name)] = 1
        b = fit.params.values
        W = float((R @ b) @ np.linalg.solve(R @ cov.values @ R.T, R @ b))
        q = len(test)
        if convention == "stata":
            F = W / q
            out["joint_p"] = float(stats.f.sf(F, q, n - k))
        else:
            out["joint_p"] = float(stats.chi2.sf(W, q))
    return out


def fit_var(data: pd.DataFrame, lags=1):
    """Reduced-form VAR by OLS. The Cholesky ordering of the SVAR is the column order:
    earlier variables are assumed not to respond within the quarter to later ones."""
    return VAR(data).fit(lags)


def irf_table(res, impulse, steps=8, bootstrap=500, level=0.90, seed=1) -> pd.DataFrame:
    """Orthogonalised (Cholesky) impulse responses to a one-standard-deviation shock in `impulse`,
    with residual-bootstrap percentile bands: simulate new samples from the fitted VAR by resampling
    its residuals, re-estimate, recompute the responses, and take the percentiles.
    (statsmodels' own errband_mc returned identical lower and upper bands in testing, so it is not used.)"""
    names = list(res.names)
    j = names.index(impulse)
    p = res.k_ar
    point = res.irf(steps).orth_irfs[:, :, j]
    Y = res.endog
    resid = res.resid if isinstance(res.resid, np.ndarray) else res.resid.values
    coefs, const = res.coefs, res.intercept
    rng = np.random.default_rng(seed)
    T, k = Y.shape
    draws = []
    for _ in range(bootstrap):
        e = resid[rng.integers(0, len(resid), size=T - p)]
        Ysim = np.zeros_like(Y, dtype=float)
        Ysim[:p] = Y[:p]
        for t in range(p, T):
            Ysim[t] = const + sum(coefs[L] @ Ysim[t - L - 1] for L in range(p)) + e[t - p]
        try:
            r = VAR(Ysim).fit(p)
            draws.append(r.irf(steps).orth_irfs[:, :, j])
        except Exception:                   # a simulated sample the VAR cannot be fitted to is skipped, and counted
            continue
    dropped = bootstrap - len(draws)        # 0.3.3: report how many draws were skipped
    if dropped:
        import warnings
        warnings.warn(f"irf_table: {dropped} of {bootstrap} bootstrap draws could not be fitted and were skipped")
    D = np.array(draws)
    lo = np.percentile(D, (1 - level) / 2 * 100, axis=0)
    hi = np.percentile(D, (1 + level) / 2 * 100, axis=0)
    rows = []
    for h in range(steps + 1):
        for i, n in enumerate(names):
            rows.append(dict(horizon=h, response=n, irf=point[h, i], lower=lo[h, i], upper=hi[h, i]))
    out = pd.DataFrame(rows)
    out.attrs.update(bootstrap_draws=len(draws), bootstrap_dropped=dropped)
    return out


def local_projection(df, y, shock, controls=(), horizons=8, lags=1, nw_lags=4) -> pd.DataFrame:
    """Jorda (2005) local projections: for each horizon h, regress y(t+h) on shock(t) and controls
    (plus `lags` lags of y and the shock), Newey-West errors. Robust to VAR misspecification;
    noisier in small samples."""
    rows = []
    for h in range(horizons + 1):
        d = df.copy()
        d["lead"] = d[y].shift(-h)
        xs = [shock] + list(controls)
        for L in range(1, lags + 1):
            d[f"L{L}.{y}"] = d[y].shift(L); d[f"L{L}.{shock}"] = d[shock].shift(L)
            xs += [f"L{L}.{y}", f"L{L}.{shock}"]
        r = newey_west(d, "lead", xs, lags=nw_lags)
        t = r["table"].loc[shock]
        rows.append(dict(horizon=h, coef=t["coef"], se=t["se"], p=t["p"], n=r["n"]))
    return pd.DataFrame(rows)
