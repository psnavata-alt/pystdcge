"""Fixed-price models: SAM multipliers and input-output (Leontief) quantity and price models.

These are the standard fixed-price models. They assume prices do not change and that
supply responds fully to demand, so they give UPPER BOUNDS on output and income effects. The CGE
(`pystdcge.cge`) relaxes both assumptions; comparing the two is one of the standard checks.

SAM multiplier
--------------
Split accounts into endogenous (activities, commodities, factors, enterprises, households, margins)
and exogenous (government, taxes, savings-investment, stock change, rest of world). With A the
matrix of endogenous column shares, a change in exogenous injections dx changes endogenous
incomes by  dy = (I - A)^-1 dx.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .sam import SAM
from . import paths

DEFAULT_EXOGENOUS = ("gov", "dtax", "ftax", "mtax", "stax", "atax", "s-i", "dstk", "row")


class SAMMultiplier:
    def __init__(self, sam: SAM, exogenous=DEFAULT_EXOGENOUS):
        self.sam = sam
        t = sam.table
        self.endo = [c for c in sam.codes if c not in exogenous]
        totals = t.sum(axis=0)
        cols = totals[self.endo].replace(0, 1.0)
        self.A = t.loc[self.endo, self.endo] / cols
        I = np.eye(len(self.endo))
        self.spectral_radius = float(max(abs(np.linalg.eigvals(self.A.values))))
        self.M = pd.DataFrame(np.linalg.inv(I - self.A.values), index=self.endo, columns=self.endo)

    def shock(self, injections: dict) -> pd.Series:
        """injections = {account: change in exogenous receipts (₱ bn)}; returns change in every
        endogenous account's total receipts."""
        dx = pd.Series(0.0, index=self.endo)
        for k, v in injections.items():
            dx[k] += v
        return self.M @ dx

    def household_income_multiplier(self, allocation: dict) -> float:
        """Total household income generated per peso injected into households in these shares."""
        dy = self.shock({h: s for h, s in allocation.items()})
        hh = [c for c in self.endo if c.startswith("hhd")]
        return float(dy[hh].sum())


# ------------------------------------------------------------------ PSA 80-industry I-O table
def load_io80(path=None):
    """PSA 2018 Input-Output transactions table (Table B.1), 80 industries.
    Returns (names, Z intermediate flows, X total output, final-demand DataFrame)."""
    path = path or paths.IO_2018
    raw = pd.read_csv(path, header=None)
    hdr = raw.iloc[9].astype(str).tolist()
    num = lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce").fillna(0).values
    names = raw.iloc[10:90, 1].astype(str).str.strip().tolist()
    Z = raw.iloc[10:90, 2:82].apply(num).values.astype(float)
    col = lambda key: next(i for i, h in enumerate(hdr) if str(h).startswith(key))
    X = num(raw.iloc[10:90, col("Total Output")]).astype(float)
    fd = {k: num(raw.iloc[10:90, col(k)]).astype(float)
          for k in ("Household Final Co",) if any(str(h).startswith(k) for h in hdr)}
    return names, Z, X, pd.DataFrame(fd, index=names)


def leontief_quantity(Z, X, dfinal):
    """Change in gross output from a change in final demand: dX = (I - A)^-1 dF."""
    A = Z / np.where(X == 0, 1, X)
    return np.linalg.solve(np.eye(len(X)) - A, dfinal)


def leontief_price_exogenous(Z, X, k, shock):
    """Cost-push price model with sector k's price set exogenously (+shock, e.g. 0.20):
    dp_r = (I - A_rr')^-1 A_kr' dp_k for all other sectors r."""
    A = Z / np.where(X == 0, 1, X)
    n = len(X)
    r = [i for i in range(n) if i != k]
    dp = np.zeros(n)
    dp[k] = shock
    dp[r] = np.linalg.solve(np.eye(n - 1) - A[np.ix_(r, r)].T, A[k, r] * shock)
    return dp
