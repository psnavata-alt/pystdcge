"""Structural VARs for pystdcge (0.3.3, 9 Oct 2026): block exogeneity, Cholesky and sign-restriction
identification, bootstrap bands, historical decompositions, "channel shut off" counterfactuals, shocks as AR
surprises, and a Bayesian VAR with a Minnesota prior. Plain numpy, so every step can be read and checked.

Generalises a typical applied set-up (a monthly VAR in which a block of world variables cannot be affected by the
domestic block, Cholesky ordering, a counterfactual with the exchange rate held at baseline, and a historical
decomposition) to any variables, block and ordering. The simpler helpers in `pystdcge.var` (Newey-West, statsmodels
VAR, local projections) remain available.

Model
    y_t = c + D_t g + A_1 y_{t-1} + ... + A_p y_{t-p} + u_t,   E[u u'] = Sigma,   u_t = B0inv e_t,  E[e e'] = I
    y: k variables; D: deterministic or exogenous terms (constant added automatically; month dummies, a trend ...).
Block exogeneity (Cushman and Zha 1997): the equations of the variables in `exog_block` use only the lags of those
    variables, so the rest of the system cannot affect them at any horizon. Estimated equation by equation by OLS
    (the regressors differ across equations; OLS is consistent).
Identification
    cholesky(m)            B0inv = chol(Sigma): the column order is the causal order (earlier variables do not respond
                           within the period to later ones).
    sign_restrictions(...) Rubio-Ramirez, Waggoner and Zha (2010): B0inv = chol(Sigma) Q with Q drawn uniformly
                           (QR of a Gaussian matrix); keep the draws whose responses have the required signs.
Responses
    irf(m, B0inv, H)       Theta_h = Phi_h B0inv, Phi_0 = I, Phi_h = sum_j A_j Phi_{h-j}. Element [h, i, j]: response of
                           variable i at horizon h to a one-standard-deviation structural shock j.
    counterfactual_irf     Bernanke, Gertler and Watson (1997), Sims and Zha (2006): a sequence of the held variable's
                           own structural shocks keeps that variable at its baseline; the difference from the total
                           response is the part that runs through that variable.
    historical_decomposition  y_t = baseline_t + sum_j contribution_{j,t}, exactly (tests/test_svar.py).
    bootstrap_irf          residual bootstrap (recursive design), re-estimating with the same restrictions.
Bayesian VAR
    bvar_minnesota         Minnesota prior by dummy observations (Banbura, Giannone and Reichlin 2010; Litterman 1986)
                           with a natural-conjugate normal-inverse-Wishart posterior: closed-form posterior mean and
                           exact posterior draws. Prior mean of the own first lag `delta` (1 for levels, 0 for growth
                           rates), overall tightness `lam` (0.2 is the usual value; larger = closer to OLS).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class VARModel:
    names: list
    p: int
    A: np.ndarray                    # k x (k p): [A_1 ... A_p]
    C: np.ndarray                    # k x m: coefficients on the deterministic terms D (first column = constant)
    Sigma: np.ndarray                # k x k residual covariance
    U: np.ndarray                    # (T - p) x k residuals
    Y: np.ndarray                    # T x k data
    D: np.ndarray                    # T x m deterministic terms
    exog_block: list = field(default_factory=list)
    index: object = None             # time index of Y (optional)
    sigma_dof: str = "ml"

    @property
    def k(self):
        return len(self.names)

    def lag(self, j):                # A_j, j = 1..p
        return self.A[:, (j - 1) * self.k: j * self.k]

    def ma(self, H):
        """Reduced-form moving-average matrices Phi_0..Phi_H, shape (H+1, k, k)."""
        k, p = self.k, self.p
        Phi = np.zeros((H + 1, k, k))
        Phi[0] = np.eye(k)
        for h in range(1, H + 1):
            Phi[h] = sum(self.lag(j) @ Phi[h - j] for j in range(1, min(h, p) + 1))
        return Phi

    def stable(self):
        k, p = self.k, self.p
        F = np.zeros((k * p, k * p))
        F[:k] = self.A
        F[k:, :-k] = np.eye(k * (p - 1)) if p > 1 else F[k:, :-k]
        return float(np.abs(np.linalg.eigvals(F)).max()) < 1


def _lags(Y, p):
    T = len(Y)
    return np.hstack([Y[p - j:T - j] for j in range(1, p + 1)])          # (T-p) x (k p): [y_{t-1} ... y_{t-p}]


def fit(data, p: int, deterministic=None, exog_block=(), constant=True, sigma_dof: str = "ml") -> VARModel:
    """Estimate a VAR(p) by OLS, equation by equation.
    data: DataFrame (columns = variables, in the Cholesky order you intend) or array.
    deterministic: optional DataFrame/array of extra deterministic or exogenous terms (e.g. month dummies), same rows.
    exog_block: names of variables whose equations use only their own block's lags (block exogeneity).
    sigma_dof: 'ml' (U'U/T_eff, maximum likelihood) or 'ols' (U'U/(T_eff - regressors), as statsmodels)."""
    if isinstance(data, pd.DataFrame):
        names, index, Y = list(data.columns), data.index, data.to_numpy(float)
    else:
        Y = np.asarray(data, float)
        names, index = [f"y{i}" for i in range(Y.shape[1])], None
    if np.isnan(Y).any():
        raise ValueError("missing values in the VAR data")
    T, k = Y.shape
    D = np.ones((T, 1)) if constant else np.zeros((T, 0))
    if deterministic is not None:
        D = np.hstack([D, np.asarray(deterministic, float)])
    Z, Yt, Dt = _lags(Y, p), Y[p:], D[p:]
    blk = [names.index(n) for n in exog_block]
    blk_cols = [(j - 1) * k + i for j in range(1, p + 1) for i in blk]
    A, C, U = np.zeros((k, k * p)), np.zeros((k, D.shape[1])), np.zeros_like(Yt)
    nreg = []
    for i in range(k):
        cols = blk_cols if i in blk else list(range(k * p))
        X = np.hstack([Z[:, cols], Dt])
        beta = np.linalg.lstsq(X, Yt[:, i], rcond=None)[0]
        A[i, cols], C[i] = beta[:len(cols)], beta[len(cols):]
        U[:, i] = Yt[:, i] - X @ beta
        nreg.append(X.shape[1])
    dof = len(U) if sigma_dof == "ml" else len(U) - max(nreg)
    return VARModel(names, p, A, C, U.T @ U / dof, U, Y, D, list(exog_block), index, sigma_dof)


# --------------------------------------------------------------------------------------- identification
def cholesky(m: VARModel) -> np.ndarray:
    return np.linalg.cholesky(m.Sigma)


def irf(m: VARModel, B0inv: np.ndarray, H: int) -> np.ndarray:
    """Structural responses Theta_h = Phi_h B0inv, shape (H+1, k, k): [h, response i, shock j]."""
    return np.einsum("hik,kj->hij", m.ma(H), B0inv)


def sign_restrictions(m: VARModel, shock: int, signs: dict, horizons=(0,), draws: int = 2000, seed: int = 1,
                      max_tries: int = 200000) -> list:
    """Draw B0inv = chol(Sigma) Q and keep those whose column `shock` gives responses with the required signs.
    signs: {variable name or index: +1 or -1} at every horizon in `horizons`. A draw whose column has exactly the
    opposite signs is kept with the column multiplied by -1. Returns the accepted B0inv matrices (up to `draws`)."""
    rng = np.random.default_rng(seed)
    P, k = cholesky(m), m.k
    req = {(m.names.index(v) if isinstance(v, str) else v): s for v, s in signs.items()}
    H = max(horizons)
    Phi = m.ma(H)
    out, tries = [], 0
    while len(out) < draws and tries < max_tries:
        tries += 1
        Q, R = np.linalg.qr(rng.standard_normal((k, k)))
        Q = Q @ np.diag(np.sign(np.diag(R)))                 # uniform (Haar) draw
        B = P @ Q
        col = np.einsum("hik,k->hi", Phi, B[:, shock])        # responses to the candidate shock
        for sgn in (1, -1):
            if all(np.all(sgn * col[list(horizons), i] * s > 0) for i, s in req.items()):
                B2 = B.copy()
                B2[:, shock] *= sgn
                out.append(B2)
                break
    return out


# --------------------------------------------------------------------------------------- responses
def counterfactual_irf(m: VARModel, B0inv: np.ndarray, shock: int, hold, H: int, size: float = 1.0) -> np.ndarray:
    """Responses (H+1, k) to structural shock `shock` (size in standard deviations), with variable `hold` kept at its
    baseline by a sequence of its own structural shocks (column `hold` of B0inv, which must have a non-zero entry for
    the held variable, as with a Cholesky B0inv)."""
    hi = m.names.index(hold) if isinstance(hold, str) else hold
    k, p = m.k, m.p
    x = np.zeros((H + 1, k))
    for h in range(H + 1):
        v = sum(m.lag(j) @ x[h - j] for j in range(1, min(h, p) + 1)) if h else np.zeros(k)
        if h == 0:
            v = v + B0inv[:, shock] * size
        v = v - B0inv[:, hi] * (v[hi] / B0inv[hi, hi])
        x[h] = v
    return x


def structural_shocks(m: VARModel, B0inv: np.ndarray) -> np.ndarray:
    """e_t = B0inv^{-1} u_t, shape (T - p, k)."""
    return np.linalg.solve(B0inv, m.U.T).T


def historical_decomposition(m: VARModel, B0inv: np.ndarray) -> dict:
    """y_t = baseline_t + sum_j contribution[:, :, j]_t for t = p..T-1, exactly.
    contribution[t, i, j]: effect on variable i at t of structural shocks j from the start of the sample to t.
    baseline: deterministic terms and initial conditions propagated with no shocks."""
    E = structural_shocks(m, B0inv)
    n, k, p = len(E), m.k, m.p
    contrib = np.zeros((n, k, k))
    for j in range(k):
        x = np.zeros((n, k))
        for t in range(n):
            v = sum(m.lag(L) @ x[t - L] for L in range(1, min(t, p) + 1)) if t else np.zeros(k)
            x[t] = v + B0inv[:, j] * E[t, j]
        contrib[:, :, j] = x
    base = np.zeros((len(m.Y), k))
    base[:p] = m.Y[:p]
    for t in range(p, len(m.Y)):
        base[t] = m.C @ m.D[t] + sum(m.lag(L) @ base[t - L] for L in range(1, p + 1))
    return {"contribution": contrib, "baseline": base[p:], "shocks": E,
            "index": None if m.index is None else m.index[p:], "names": m.names}


def bootstrap_irf(m: VARModel, H: int, reps: int = 1000, seed: int = 1, identify=cholesky, level: float = 0.90,
                  extra=None) -> dict:
    """Residual bootstrap (recursive design): resample the residuals, rebuild the data from the estimated model and the
    first p observations, re-estimate with the same lags, terms, block and dof convention, re-identify.
    Returns point, lower and upper responses (H+1, k, k) and the draws; `extra(model, B0inv)` adds any statistic."""
    rng = np.random.default_rng(seed)
    B0 = identify(m)
    point = irf(m, B0, H)
    T, p = len(m.Y), m.p
    draws, extras = [], []
    for _ in range(reps):
        Ub = m.U[rng.integers(0, len(m.U), len(m.U))]
        Ys = m.Y.copy()
        for t in range(p, T):
            Ys[t] = m.C @ m.D[t] + sum(m.lag(L) @ Ys[t - L] for L in range(1, p + 1)) + Ub[t - p]
        mb = fit(pd.DataFrame(Ys, columns=m.names), p, deterministic=m.D[:, 1:] if m.D.shape[1] > 1 else None,
                 exog_block=m.exog_block, sigma_dof=m.sigma_dof)
        Bb = identify(mb)
        draws.append(irf(mb, Bb, H))
        if extra is not None:
            extras.append(extra(mb, Bb))
    Dr = np.array(draws)
    a = (1 - level) / 2 * 100
    return {"point": point, "lower": np.percentile(Dr, a, axis=0), "upper": np.percentile(Dr, 100 - a, axis=0),
            "draws": Dr, "extra": extras}


def irf_frame(resp: np.ndarray, names: list, shock: int, scale: float = 1.0, cumulative=()) -> pd.DataFrame:
    """Tidy table of the responses to one shock; `cumulative` names variables to report as running sums
    (e.g. variables in first differences, whose levels are the cumulated responses)."""
    x = resp[:, :, shock] * scale
    df = pd.DataFrame(x, columns=names)
    for c in cumulative:
        df[c] = df[c].cumsum()
    df.index.name = "horizon"
    return df


# --------------------------------------------------------------------------------------- shocks as surprises
def ar_surprise(series: pd.Series, lags: int = 2, constant=True) -> pd.Series:
    """The unexpected part of a series: residuals of an AR(lags) regression estimated by OLS (e.g. geopolitical-risk
    shocks as the part of the index not predictable from its own past)."""
    s = pd.Series(series, dtype=float).dropna()
    Y = s.to_numpy()
    X = _lags(Y[:, None], lags)
    if constant:
        X = np.hstack([np.ones((len(X), 1)), X])
    b = np.linalg.lstsq(X, Y[lags:], rcond=None)[0]
    return pd.Series(Y[lags:] - X @ b, index=s.index[lags:], name=f"{s.name}_surprise")


# --------------------------------------------------------------------------------------- Bayesian VAR
@dataclass
class BVAR:
    names: list
    p: int
    B_mean: np.ndarray               # (k p + 1) x k, rows: [y_{t-1} ... y_{t-p}, constant]
    XtX_inv: np.ndarray
    S: np.ndarray
    dof: int
    Y: np.ndarray

    def model(self, B=None, Sigma=None) -> VARModel:
        """A VARModel with the posterior mean (or a given draw) for use with irf, historical_decomposition ..."""
        B = self.B_mean if B is None else B
        k, p = len(self.names), self.p
        Sigma = self.S / (self.dof - k - 1) if Sigma is None else Sigma     # posterior mean of Sigma
        Z = _lags(self.Y, p)
        Xr = np.hstack([Z, np.ones((len(Z), 1))])
        U = self.Y[p:] - Xr @ B
        return VARModel(self.names, p, B[:k * p].T.copy(), B[k * p:].T.copy(), Sigma, U, self.Y,
                        np.ones((len(self.Y), 1)), [], None, "posterior")

    def draw(self, n: int, seed: int = 1):
        """Exact draws from the normal-inverse-Wishart posterior: Sigma ~ IW(S, dof), vec(B) | Sigma ~ N(B_mean, Sigma kron (X'X)^-1)."""
        from scipy.stats import invwishart
        rng = np.random.default_rng(seed)
        L = np.linalg.cholesky(self.XtX_inv)
        out = []
        for _ in range(n):
            Sig = invwishart.rvs(df=self.dof, scale=self.S, random_state=rng)
            Z = rng.standard_normal(self.B_mean.shape)
            out.append((self.B_mean + L @ Z @ np.linalg.cholesky(Sig).T, Sig))
        return out


def bvar_minnesota(data, p: int, lam: float = 0.2, delta=0.0, decay: float = 1.0, eps: float = 1e-4) -> BVAR:
    """Minnesota-prior BVAR by dummy observations (Banbura, Giannone and Reichlin 2010, eqs. 5-6).
    lam: overall tightness (smaller = closer to the prior); delta: prior mean of each variable's own first lag
    (number or one per variable; 0 for growth rates, 1 for levels); decay: lag l has prior std lam / l**decay;
    eps: tightness on the constant (small = nearly flat prior). Scales sigma_i from AR(1) residuals."""
    if isinstance(data, pd.DataFrame):
        names, Y = list(data.columns), data.to_numpy(float)
    else:
        Y = np.asarray(data, float)
        names = [f"y{i}" for i in range(Y.shape[1])]
    T, k = Y.shape
    delta = np.full(k, delta, float) if np.ndim(delta) == 0 else np.asarray(delta, float)
    sig = np.zeros(k)
    for i in range(k):
        X1 = np.column_stack([np.ones(T - 1), Y[:-1, i]])
        r = Y[1:, i] - X1 @ np.linalg.lstsq(X1, Y[1:, i], rcond=None)[0]
        sig[i] = np.sqrt(r @ r / (len(r) - 2))
    Jp = np.diag(np.arange(1, p + 1) ** decay)
    Yd = np.vstack([np.diag(delta * sig) / lam, np.zeros((k * (p - 1), k)), np.diag(sig), np.zeros((1, k))])
    Xd = np.vstack([np.hstack([np.kron(Jp, np.diag(sig)) / lam, np.zeros((k * p, 1))]),
                    np.zeros((k, k * p + 1)),
                    np.hstack([np.zeros((1, k * p)), np.full((1, 1), eps)])])
    Z = _lags(Y, p)
    X = np.hstack([Z, np.ones((len(Z), 1))])
    Ys, Xs = np.vstack([Y[p:], Yd]), np.vstack([X, Xd])
    XtX_inv = np.linalg.inv(Xs.T @ Xs)
    B = XtX_inv @ Xs.T @ Ys
    E = Ys - Xs @ B
    dof = len(Ys) - X.shape[1] + 2
    return BVAR(names, p, B, XtX_inv, E.T @ E, dof, Y)
