"""Input-output (Leontief) models on PSA's 2018 input-output tables (80 or 16 industries).

The 16-industry table, IOTable(paths.IO_2018_16), has industries that match the Labour Force Survey's major industry
groups (for labour-market microsimulation). Same domestic (import-adjusted) inverse, same GDP-share conversion of the
shock, and job-equivalents from LFS employment summed into the 16 industries.

The PSA tables are not redistributed with this package: data/raw/io/README.md explains how to download them.

Price model (cost push)
    A rise in the price of one or more industries' output (e.g. refined petroleum +10%) is passed on,
    in full and at fixed input shares, to every industry that buys from them, directly and indirectly:
        dp_r = (I - A_rr')^-1  A_Kr' dp_K     (K = industries whose price is set, r = all others)
    For a single industry k this equals the common spreadsheet formula p = (I - A')^-1 d with
    d_k = shock / L'_kk (it scales the k-th column of the inverse so that p_k equals the shock).
    Consumer prices: dp weighted by household final consumption (HFCE) shares.
    Producer prices: dp weighted by total output shares.
    GDP (a common shortcut): real consumption falls by CPI change x an assumed price elasticity, and GDP
    by that x the consumption share of GDP. Both numbers are assumptions the user must supply.

Quantity (demand) model
    A change in final demand dF changes gross output by dX = (I - A)^-1 dF (Type I: no induced household
    spending). The PSA transactions table includes imported inputs in A, so with the total inverse every
    peso of final demand returns exactly one peso of value added (v'(I - A)^-1 = 1'). The import-adjusted
    ("domestic") inverse removes the imported share of each product from A, which is the usual choice and
    gives, for construction, about 0.68 of GDP per peso.
    Value added = TPI row / output; compensation = COE row / output; imported inputs = the removed share.

Job-equivalents (optional)
    Employment by industry moves in proportion to output: jobs_i = dX_i / X_i x employed_i,
    with employment by major industry group supplied by the user (data/raw/lfs, from PSA LFS). This is an
    upper bound on short-run job losses (hours and pay adjust too).

Units: the table is in ₱ million at 2018 prices. Shocks given in pesos of a later year are converted to
the same share of GDP in the 2018 table and results converted back (linear peso results are unchanged by
this; output shares and job-equivalents need it).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import paths

FINAL_DEMAND = ("Household Final Consumption Expenditure", "Government Final Consumption Expenditure", "Construction",
                "Durable Equipment", "Breeding Stocks and Orchard Development", "Intellectual Property Products",
                "Changes in Inventories", "Valuables", "Exports of Goods and Services", "Imports of Goods and Services",
                "Total Final Demand", "Total Output")


def _num(s):
    return pd.to_numeric(pd.Series(s).astype(str).str.replace(",", ""), errors="coerce").fillna(0).values.astype(float)


class IOTable:
    def __init__(self, path=None):
        raw = pd.read_csv(path or paths.IO_2018, header=None)
        hdr = [str(h).strip() for h in raw.iloc[9].tolist()]
        # industry rows start at row 10 and run while the code column holds a number: 80 in PSA's 80-industry table,
        # 16 in its 16-industry table (path=paths.IO_2018_16)
        col0 = [str(c).strip() for c in raw.iloc[10:, 0].tolist()]
        n_ind = next(i for i, c in enumerate(col0) if not c.isdigit())
        rows = slice(10, 10 + n_ind)
        self.codes = raw.iloc[rows, 0].astype(str).str.strip().tolist()
        self.names = raw.iloc[rows, 1].astype(str).str.strip().tolist()
        self.n = len(self.names)
        self.Z = np.column_stack([_num(raw.iloc[rows, j]) for j in range(2, 2 + self.n)])
        fd_cols = {}
        for key in FINAL_DEMAND:                      # final-demand block starts after the 80 industry columns
            j = next(i for i, h in enumerate(hdr) if i >= 2 + self.n and h.startswith(key))
            fd_cols[key] = _num(raw.iloc[rows, j])
        self.fd = pd.DataFrame(fd_cols, index=self.names)
        self.X = self.fd["Total Output"].values
        lab = [str(t).strip() for t in raw.iloc[:, 0].tolist()]
        row = lambda code: _num(raw.iloc[lab.index(code), 2:2 + self.n])
        self.COE, self.GOS, self.TS, self.TPI = row("COE"), row("GOS"), row("T-S"), row("TPI")
        Xs = np.where(self.X == 0, 1, self.X)
        self.A = self.Z / Xs
        self.v = self.TPI / Xs                        # value added per peso of output
        self.w = self.COE / Xs                        # compensation of employees per peso of output
        self.L = np.linalg.inv(np.eye(self.n) - self.A)
        imp, exp = -self.fd["Imports of Goods and Services"].values, self.fd["Exports of Goods and Services"].values
        imp = np.abs(imp)                             # PSA records imports as a negative column
        supply = self.X + imp - exp
        self.dom_share = np.clip(1 - imp / np.where(supply <= 0, 1, supply), 0, 1)
        self.Ad = self.A * self.dom_share[:, None]
        self.Ld = np.linalg.inv(np.eye(self.n) - self.Ad)
        self.gdp = float(self.TPI.sum())              # ₱ million, 2018
        self.hfce_w = self.fd["Household Final Consumption Expenditure"].values / \
            self.fd["Household Final Consumption Expenditure"].sum()
        self.out_w = self.X / self.X.sum()

    def index(self, name: str) -> int:
        return self.names.index(name)

    # ------------------------------------------------------------------ price model
    def price(self, shocks: dict) -> pd.Series:
        """shocks = {industry name: proportional price change (0.10 = +10%)}. Returns dp for all industries."""
        K = [self.index(k) for k in shocks]
        r = [i for i in range(self.n) if i not in K]
        dp = np.zeros(self.n)
        dpK = np.array([shocks[self.names[k]] for k in K])
        dp[K] = dpK
        dp[r] = np.linalg.solve(np.eye(len(r)) - self.A[np.ix_(r, r)].T, self.A[np.ix_(K, r)].T @ dpK)
        return pd.Series(dp, index=self.names)

    def price_summary(self, shocks: dict) -> dict:
        dp = self.price(shocks)
        cpi = float(dp.values @ self.hfce_w)
        ppi = float(dp.values @ self.out_w)
        contrib = pd.Series(dp.values * self.hfce_w, index=self.names)
        return dict(dp=dp, cpi=cpi, ppi=ppi, cpi_contrib=contrib)

    def price_from_primary_inputs(self, change) -> pd.Series:
        """Cost-push from primary inputs (value added: compensation, operating surplus, taxes less subsidies).
        change: one proportional change for all industries (0.10 = +10%) or one per industry (array or dict).
        dp = (I - A')^-1 (v * change). Added in 0.3 for identity check I3: because PSA's table records imported
        inputs inside A, raising every primary-input cost by 10% must raise every price by exactly 10%."""
        g = np.zeros(self.n)
        if isinstance(change, dict):
            for k, val in change.items():
                g[self.index(k)] = val
        else:
            g[:] = change
        dp = np.linalg.solve(np.eye(self.n) - self.A.T, self.v * g)
        return pd.Series(dp, index=self.names)

    @staticmethod
    def gdp_from_prices(cpi_change: float, elasticity: float, consumption_share: float) -> dict:
        """A common shortcut: real consumption change = CPI change x elasticity; GDP change = that x C/GDP."""
        dc = cpi_change * elasticity
        return dict(real_consumption=dc, gdp=dc * consumption_share)

    # ------------------------------------------------------------------ quantity model
    def quantity(self, dF: dict, inverse: str = "domestic", gdp_other_year: float | None = None) -> dict:
        """dF = {industry name: change in final demand, ₱ bn in the pesos of the year whose GDP is given}.
        inverse: 'domestic' (import-adjusted, recommended) or 'total' (PSA's published inverse).
        gdp_other_year: nominal GDP (₱ bn) of the year the shock is expressed in; the shock is converted to
        the same share of the table's 2018 GDP and results are converted back. None = apply as entered."""
        scale = 1.0 if gdp_other_year is None else (self.gdp / 1000) / gdp_other_year
        f = np.zeros(self.n)
        for k, val in dF.items():
            f[self.index(k)] += val * 1000 * scale      # ₱ million, 2018 table units
        Linv = self.Ld if inverse == "domestic" else self.L
        dX = Linv @ f
        dVA, dCOE = self.v * dX, self.w * dX
        dM = ((1 - self.dom_share)[:, None] * self.A * dX[None, :]).sum(axis=0) if inverse == "domestic" else np.full(self.n, np.nan)
        back = 1.0 / scale / 1000                       # to ₱ bn of the shock's year
        ind = pd.DataFrame({"output (₱ bn)": dX * back, "output (%)": dX / np.where(self.X == 0, 1, self.X) * 100,
                            "value added (₱ bn)": dVA * back, "compensation (₱ bn)": dCOE * back,
                            "imported inputs (₱ bn)": dM * back}, index=self.names)
        tot_f = f.sum()
        return dict(industries=ind, final_demand_bn=tot_f * back, output_bn=dX.sum() * back, va_bn=dVA.sum() * back,
                    coe_bn=dCOE.sum() * back, imports_bn=float(np.nansum(dM)) * back if inverse == "domestic" else float("nan"),
                    va_pct_gdp=dVA.sum() / self.gdp * 100,
                    output_multiplier=dX.sum() / tot_f if tot_f else float("nan"),
                    va_multiplier=dVA.sum() / tot_f if tot_f else float("nan"))

    def multipliers(self, inverse: str = "domestic") -> pd.DataFrame:
        """Type I output and value-added multipliers per peso of final demand, by industry."""
        Linv = self.Ld if inverse == "domestic" else self.L
        return pd.DataFrame({"output multiplier": Linv.sum(axis=0), "value-added multiplier": self.v @ Linv,
                             "compensation multiplier": self.w @ Linv}, index=self.names)

    # ------------------------------------------------------------------ jobs
    def jobs(self, output_pct: pd.Series, employment: pd.DataFrame | None = None) -> pd.DataFrame:
        """Job-equivalents by major industry group: output change (%) aggregated to the group with output
        weights, times the group's employment. employment: DataFrame with columns 'group', 'employed_thousand'
        and the map from industries to groups (default: data/raw/lfs files)."""
        emp, mp = employment if employment is not None else load_employment(self.n)
        grp = pd.Series(mp).reindex(self.names)
        if grp.isna().any():
            raise KeyError(f"Industries without an employment group: {list(grp[grp.isna()].index)}")
        w = pd.Series(self.X, index=self.names)
        pct = (output_pct * w).groupby(grp).sum() / w.groupby(grp).sum()
        out = emp.set_index("group").join(pct.rename("output change (%)"))
        out["job-equivalents"] = out["output change (%)"] / 100 * out["employed_thousand"] * 1000
        return out


def load_employment(industries: int = 80):
    """PSA LFS employment by major industry group and a map from the I-O industries to those groups.
    industries=80 (default): the 19 LFS groups, each fed by one or more of the 80 I-O industries.
    industries=16: the LFS groups summed into the 16 I-O industries (each LFS group belongs to
    one of them), so job-equivalents come out by the same 16 industries as the table, ready for LFS microsimulation."""
    d = paths.DATA_RAW / "lfs"
    emp = pd.read_csv(d / "LFS_2025_employed_by_major_industry.csv", comment="#")
    if industries == 16:
        mp16 = pd.read_csv(d / "io16_to_lfs_group_map.csv", comment="#")
        g = dict(zip(mp16["lfs_group"], mp16["io16_industry"]))
        missing = sorted(set(emp["group"]) - set(g))
        if missing:
            raise KeyError(f"LFS groups without a 16-industry match: {missing}")
        emp16 = emp.assign(group=emp["group"].map(g)).groupby("group", sort=False, as_index=False)["employed_thousand"].sum()
        return emp16, {n: n for n in emp16["group"]}
    mp = pd.read_csv(d / "io80_to_lfs_group_map.csv", comment="#")
    return emp, dict(zip(mp["io_industry"], mp["group"]))
