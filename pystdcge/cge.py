"""pystdcge static CGE model, calibrated to an IFPRI Nexus-style SAM.

The structure follows the IFPRI Standard CGE model (Lofgren, Harris and Robinson, 2002,
"A Standard Computable General Equilibrium (CGE) Model in GAMS", IFPRI Microcomputers in Policy
Research 5), simplified where the Philippine SAM allows:

Production   Each activity combines value added (CES over labour types, land and capital) and
             intermediate inputs (fixed coefficients, Leontief) in fixed proportions.
Outputs      Activities produce commodities in fixed shares (the SAM's make matrix).
Exports      Domestic output is split between exports and domestic sales by a CET function;
             world prices are given (small open economy).
Imports      Domestic demand is for a composite of imports and domestic goods (Armington CES).
Margins      Each unit of composite supply needs trade and transport services (fixed per unit).
Taxes        Import tariffs, sales taxes, a factor tax on capital (2023 SAM) or an activity tax on
             output (2018 SAM, 'atax'; added in 0.3), direct taxes on enterprises and households:
             all at fixed rates.
Households   Ten groups (rural and urban quintiles) receive factor income, enterprise and
             government transfers and remittances; pay taxes; save a fixed share; spend the rest
             in fixed budget shares (Cobb-Douglas), or (0.3, option les=) a Linear Expenditure System with
             Philippine income elasticities (pystdcge/demand.py).
Government   Fixed real consumption and real transfers; its savings adjust.
Rest of world Foreign savings fixed in foreign currency; the real exchange rate adjusts.
Investment   Closure choice: 'investment' (real investment fixed; household saving rates adjust)
             or 'savings' (saving rates fixed; investment adjusts).
Numeraire    Consumer price index = 1.

Home consumption in the SAM is treated as marketed consumption (see SAM.move_home_consumption_to_market).

Solving
-------
The model is written as a square system F(x) = 0 in activity levels, domestic and composite
prices, factor prices, the exchange rate, a closure variable and a Walras slack. At the benchmark
every residual is zero by construction; after a shock the solver (scipy) finds the new x.
The Walras slack must be zero in every solution: if it is not, the model's accounts do not close.

Usage
-----
>>> from pystdcge.cge import CGE
>>> m = CGE.from_sam()                 # calibrate to the 2023 SAM
>>> base = m.solve()                   # benchmark (reproduces the SAM)
>>> sim = m.solve({"qinv_scale": {"ccons": 0.9}})   # 10% less construction investment
>>> m.compare(base, sim)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import root

from .sam import SAM

FACTORS = ("flab-n", "flab-p", "flab-s", "flnd", "fcap")
DEFAULT_ELASTICITIES = {"sigma_va": 0.8, "sigma_q": 2.0, "omega_t": 2.0}


def _by_code(value, codes, default):
    """One elasticity for all codes (a number) or one per code (a dict; missing codes take the default)."""
    if isinstance(value, dict):
        return np.array([float(value.get(c, default)) for c in codes])
    return np.full(len(codes), float(value))


def _pos(x):
    return np.maximum(x, 1e-12)


@dataclass
class Solution:
    x: np.ndarray
    v: dict            # every model variable, as numpy arrays or floats
    ok: bool
    message: str
    residual_max: float
    shocks: dict = field(default_factory=dict)

    def __getitem__(self, k):
        return self.v[k]


class CGE:
    # ================================================================== calibration
    def __init__(self, sam: SAM, elasticities=None, closure="investment", unemployed=(), capital="mobile", les=None,
                 margins="composite", home="market", gov="real", inv="fixed"):
        """closure: 'investment' (real investment fixed, saving rates adjust), 'savings' (saving rates
        fixed, investment adjusts) or 'keynesian' (short-run, demand-driven: investment AND saving rates
        fixed; the exchange rate is fixed and serves as numeraire; foreign savings (the current account)
        adjust; unemployed labour types have a fixed real wage, so output and employment are set by
        demand. Without any `unemployed` labour type the closure still solves, but output is then
        supply-determined and the current account absorbs demand shocks).
        unemployed: labour types with a fixed real wage and variable employment, e.g. ('flab-n', 'flab-p').
        capital: 'mobile' (one economy-wide rental rate) or 'fixed' (each activity keeps its capital;
        rental rates differ by activity) - the usual short-run assumption.
        les: None (Cobb-Douglas household demand, as before) or LES parameters (0.3), e.g.
        pystdcge.demand.les_briones2023(): {'eta': {commodity: income elasticity}, 'own_price': {...},
        'fit': 'all'|'food'} or with an explicit 'frisch' (a number or {household: value}). See pystdcge/demand.py.
        margins: 'composite' (default, as before: trade and transport margins are charged per unit of the composite
        good, after the import/domestic choice) or 'split' (0.3, verification Phase 3: IFPRI's treatment, Lofgren
        et al. 2002 eq. 1, 3 and 27: the margin is added to the import price and to the domestic demand price
        BEFORE buyers choose between them; the SAM's margin on each good is shared between domestic sales and
        imports in proportion to their values, as in validation/ifpri/build_ifpri_inputs.py; no export margins,
        because the SAM records none).
        home: 'market' (default, as before: the SAM's home consumption, households' own produce, is treated as if bought
        on the market; SAM.move_home_consumption_to_market) or 'separate' (0.3.1, verification Phase 3: IFPRI's
        treatment, Lofgren et al. 2002 eq. 18 and 34: own produce is valued at the producer price PX and consumed
        directly, with no trade margin, sales tax or import competition; marketed output = gross output - home use;
        a fixed share of each household's budget, as for market goods; CPI weights cover market purchases only, as
        in IFPRI's code). Not yet combined with les=.
        gov: 'real' (default: fixed real government consumption; government saving adjusts) or 'cd' (0.3.1, Hosoe
        et al. 2010 stdcge: the government saves a fixed share of its revenue and spends the rest in fixed value shares).
        inv: 'fixed' (default: fixed real proportions) or 'value_shares' (Hosoe et al.: fixed value shares of total
        savings). Both options exist for the Hosoe cross-check (validation/hosoe/, check V5)."""
        if margins not in ("composite", "split"):
            raise ValueError("margins must be 'composite' or 'split'")
        if home not in ("market", "separate"):
            raise ValueError("home must be 'market' or 'separate'")
        if home == "separate" and les is not None:
            raise NotImplementedError("home='separate' with les= is not built yet")
        self.margins = margins
        self.home = home
        if gov not in ("real", "cd") or inv not in ("fixed", "value_shares"):
            raise ValueError("gov must be 'real' or 'cd'; inv must be 'fixed' or 'value_shares'")
        self.gov, self.inv = gov, inv
        el = dict(DEFAULT_ELASTICITIES)
        el.update(elasticities or {})
        # 0.3: each elasticity may be one number (all sectors, as before) or a dict {code: value} by activity
        # (sigma_va) or commodity (sigma_q, omega_t); codes missing from a dict take the default value.
        # sigma_va exactly 1 selects the Cobb-Douglas limit (closed form); values within 1e-6 of 1 but not 1 are refused.
        for k in ("sigma_va", "sigma_q"):
            vals = el[k].values() if isinstance(el[k], dict) else [el[k]]
            if any(abs(v - 1.0) < 1e-6 and not (k == "sigma_va" and v == 1.0) for v in vals):
                raise ValueError(f"{k} = 1 (Cobb-Douglas) divides by zero in the CES formulas; use 0.99 or 1.01")
        self.el = el
        self.closure = closure
        self.unemployed = list(unemployed)
        self.capital = capital
        self.sam0 = sam
        s = sam.move_home_consumption_to_market()
        self.sam = s
        t = s.table
        self.has_ftax, self.has_atax = "ftax" in t.index, "atax" in t.index
        self.A = s.accounts("a")
        self.C = s.accounts("c")
        self.H = s.accounts("hhd")
        self.F = [f for f in FACTORS if f in t.index]
        A, C, H, F = self.A, self.C, self.H, self.F
        nA, nC = len(A), len(C)

        # ---- production
        self.QA0 = t.loc[A].sum(axis=1).values                      # activity output (row = col totals)
        # activity tax on the value of output (2018 SAM); zero when the SAM has no 'atax' account (2023)
        self.ta = t.loc["atax", A].values / self.QA0 if self.has_atax else np.zeros(nA)
        self.ica = (t.loc[C, A].values / self.QA0)                  # C x A
        self.QF0 = t.loc[F, A].values                               # F x A (value units, WF0 = 1)
        self.QVA0 = self.QF0.sum(axis=0)
        self.iva = self.QVA0 / self.QA0
        self.delta = self.QF0 / np.where(self.QVA0 == 0, 1, self.QVA0)   # CES share parameters (sum to 1)
        self.use = self.QF0 > 0
        self.sigva = _by_code(el["sigma_va"], A, DEFAULT_ELASTICITIES["sigma_va"])
        self.tfp = np.ones(nA)
        self.QFS0 = self.QF0.sum(axis=1)                            # factor supplies

        # ---- make matrix, output and trade
        make = t.loc[A, C].values                                   # A x C: activity a's sales of commodity c
        self.theta = make / self.QA0[:, None]
        # 0.3.1 (home='separate'): home consumption by commodity and household at benchmark prices (PX0 = 1), read
        # from the SAM's activity -> household cells before they were moved to the market; zero by default
        self.HC = np.zeros((nC, len(H)))
        if home == "separate":
            t0 = sam.table
            for a in A:
                for j, h in enumerate(H):
                    if h in t0.columns and t0.loc[a, h]:
                        self.HC[C.index("c" + a[1:]), j] = t0.loc[a, h]
        hcs = self.HC.sum(axis=1)
        self.QX0 = make.sum(axis=0) - hcs                           # marketed output (= all output by default)
        self.QE0 = t.loc[C, "row"].values
        self.QD0 = self.QX0 - self.QE0
        self.QM0 = t.loc["row", C].values
        mtax = t.loc["mtax", C].values
        stax = t.loc["stax", C].values
        trc = t.loc["trc", C].values
        # Re-exports: where recorded exports exceed domestic output (e.g. electronics, 'cmach'), the
        # excess is treated as imported goods exported again at world prices, with no tariff, margin or
        # domestic value added. They enter both sides of the current account in fixed quantities.
        self.rex = np.maximum(self.QE0 - self.QX0, 0.0)
        self.QE0 = self.QE0 - self.rex
        self.QM0 = self.QM0 - self.rex
        if (self.QM0 < -1e-9).any():
            raise ValueError("Re-exports exceed imports")
        self.QD0 = np.maximum(self.QX0 - self.QE0, 0.0)
        uses = ["trc"] + H + ["gov", "s-i", "dstk"]
        self.QQ0 = t.loc[C, A].sum(axis=1).values + t.loc[C, uses].sum(axis=1).values - hcs
        with np.errstate(divide="ignore", invalid="ignore"):
            self.tm = np.where(self.QM0 > 0, mtax / np.where(self.QM0 > 0, self.QM0, 1), 0.0)
            base = self.QD0 + self.QM0 + mtax + trc
            self.tq = np.where(base > 0, stax / np.where(base > 0, base, 1), 0.0)
            self.icq = np.where(self.QQ0 > 0, trc / np.where(self.QQ0 > 0, self.QQ0, 1), 0.0)
        if ((mtax > 1e-9) & (self.QM0 <= 0)).any():
            raise ValueError("Import tax without imports")
        gap = self.QQ0 - (self.QD0 + self.QM0 + mtax + trc + stax)
        if np.abs(gap).max() > 1e-6:
            raise ValueError(f"Commodity accounts do not close (max gap {np.abs(gap).max():.3g})")
        msrv = t.loc[C, "trc"].values
        self.sm = msrv / msrv.sum() if msrv.sum() > 0 else np.zeros(nC)   # margin services mix (none in a SAM without margins)
        self.pwm = np.ones(nC)
        self.pwe = np.ones(nC)

        # masks
        self.hasX = self.QX0 > 1e-12
        self.hasE = self.QE0 > 1e-12
        self.hasD = self.QD0 > 1e-12
        self.hasM = self.QM0 > 1e-12
        self.hasQ = self.QQ0 > 1e-12

        # CET (exports vs domestic sales), only where both exist
        om = el["omega_t"]
        self.omega = _by_code(om, C, DEFAULT_ELASTICITIES["omega_t"])
        self.rt = (self.omega + 1) / self.omega
        both = self.hasE & self.hasD
        self.gam = np.full(nC, 0.5)
        self.gamc = np.full(nC, 0.5)          # 1 - gam, computed directly (0.3: stable for low CET elasticities)
        self.kgam = np.ones(nC)               # (1 - gam) / gam
        self.at = np.ones(nC)
        r0 = np.where(both, self.QE0 / np.where(self.hasD, self.QD0, 1), 1.0)
        self.kgam[both] = r0[both] ** (1.0 / self.omega[both])
        self.gam[both] = 1.0 / (1.0 + self.kgam[both])
        self.gamc[both] = self.kgam[both] / (1.0 + self.kgam[both])
        g, rt = self.gam, self.rt
        self.at[both] = self.QX0[both] / (g[both] * self.QE0[both] ** rt[both]
                                          + self.gamc[both] * self.QD0[both] ** rt[both]) ** (1 / rt[both])

        # Armington (imports vs domestic), only where both exist
        sq = el["sigma_q"]
        self.sigq = _by_code(sq, C, DEFAULT_ELASTICITIES["sigma_q"])
        mix = self.hasM & self.hasD
        # 0.3 (margins='split'): margin per unit of domestic sales and of imports (IFPRI icd = icm here); zero by default
        with np.errstate(divide="ignore", invalid="ignore"):
            dm = self.QD0 + self.QM0
            self.icx = np.where(dm > 0, trc / np.where(dm > 0, dm, 1), 0.0) if margins == "split" else np.zeros(nC)
        PM0 = 1 + self.tm + self.icx                     # margin-inclusive import price (= 1 + tm by default)
        PDD0 = 1 + self.icx                              # margin-inclusive domestic demand price (= 1 by default)
        self.dq = np.zeros(nC)
        self.aq = np.ones(nC)
        ratio = np.where(mix, self.QM0 / np.where(self.hasD, self.QD0, 1) * (PM0 / PDD0) ** self.sigq, 0.0)
        self.dq[mix] = ratio[mix] / (1 + ratio[mix])
        V0 = PM0 * self.QM0 + PDD0 * self.QD0
        PARM0 = np.where(self.hasQ, V0 / np.where(self.hasQ, self.QQ0, 1), 1.0)
        s_ = self.sigq
        self.aq[mix] = (self.dq[mix] * PM0[mix] ** (1 - s_[mix]) + (1 - self.dq[mix]) * PDD0[mix] ** (1 - s_[mix])) \
            ** (1 / (1 - s_[mix])) / PARM0[mix]
        # import-only and domestic-only composites: X = QQ with a fixed price wedge
        self.k_m = np.where(self.hasM & ~self.hasD, PARM0 / np.where(PM0 > 0, PM0, 1), 1.0)
        self.k_d = np.where(self.hasD & ~self.hasM, PARM0 / PDD0, 1.0)

        # ---- institutions
        v = lambda r, c: s.v(r, c) if (r in t.index and c in t.columns) else 0.0   # missing account = 0
        self.frow_in = np.array([v(f, "row") for f in F])          # factor income from abroad (FCU)
        self.frow_out = np.array([v("row", f) for f in F])
        YF0 = self.QFS0 + self.frow_in
        self.tf = np.array([v("ftax", f) for f in F]) / YF0
        dist0 = (1 - self.tf) * YF0 - self.frow_out
        self.inst = H + ["ent"]
        self.shif = np.array([[v(i, f) / dist0[k] for k, f in enumerate(F)] for i in self.inst])   # I x F
        # enterprises
        self.trg_ent = v("ent", "gov")
        self.erow_in = v("ent", "row")
        YE0 = sum(v("ent", f) for f in F) + self.trg_ent + self.erow_in
        self.te = v("dtax", "ent") / YE0
        self.she = np.array([v(h, "ent") for h in H]) / YE0
        self.sheg = v("gov", "ent") / YE0
        self.erow_out = v("row", "ent")
        # households
        self.trg_h = np.array([v(h, "gov") for h in H])
        self.hrow_in = np.array([v(h, "row") for h in H])
        YH0 = t.loc[H].sum(axis=1).values
        self.tins = np.array([v("dtax", h) for h in H]) / YH0
        self.tgh = np.array([v("gov", h) for h in H]) / YH0
        self.hrow_out = np.array([v("row", h) for h in H])
        DY0 = YH0 * (1 - self.tins - self.tgh) - self.hrow_out
        self.mps = np.array([v("s-i", h) for h in H]) / DY0
        EH0 = DY0 * (1 - self.mps)
        self.beta = (t.loc[C, H].values - self.HC) / EH0            # C x H budget shares (market purchases)
        self.beta_h = self.HC / EH0                                 # C x H budget shares of own produce (0 by default)
        self.les = None
        if les is not None:                                         # 0.3: Linear Expenditure System
            from .demand import fit_frisch
            eta0 = np.array([float(les["eta"].get(c, 1.0)) for c in C])
            q0 = t.loc[C, H].values                                 # benchmark quantities (benchmark prices = 1)
            mb, gam, frisch, aggs = np.zeros_like(q0), np.zeros_like(q0), [], []
            for h in range(len(H)):
                w = self.beta[:, h]
                agg = float(w @ eta0)
                e = eta0 / agg                                      # Engel aggregation: w @ e = 1
                if "frisch" in les:
                    fr = les["frisch"]
                    phi = float(fr[H[h]] if isinstance(fr, dict) else fr)
                else:
                    eps = np.array([float(les["own_price"].get(c, -1.0)) for c in C])
                    mask = None
                    if les.get("fit", "all") == "food":
                        from .demand import FOOD
                        mask = np.array([c in FOOD for c in C])
                    phi = fit_frisch(w, e, eps, mask)
                mb[:, h] = e * w                                    # marginal budget shares (sum to 1)
                gam[:, h] = q0[:, h] - mb[:, h] * (-EH0[h] / phi)   # subsistence quantities
                frisch.append(phi); aggs.append(agg)
            if (q0 - gam < -1e-9).any():
                raise ValueError("LES calibration gives negative supernumerary quantities")
            self.les = dict(mb=mb, gamma=gam, frisch=np.array(frisch), engel_sum=np.array(aggs))
        # government
        self.qg = t.loc[C, "gov"].values
        self.grow_in = v("gov", "row")
        self.grow_out = v("row", "gov")
        if gov == "cd":                     # Hosoe: Sg = ssg * revenue; consumption = fixed value shares of the rest
            YG0 = float(t.loc["gov"].sum())                           # total government receipts (row total)
            self.ssg = v("s-i", "gov") / YG0
            self.gsh = self.qg / self.qg.sum()
        # investment, stocks, foreign savings
        self.qinv = t.loc[C, "s-i"].values
        self.qdst = t.loc[C, "dstk"].values
        self.fsav = v("s-i", "row")
        # CPI weights (household consumption)
        hc = t.loc[C, H].sum(axis=1).values - hcs                   # market purchases (all purchases by default)
        self.cwts = hc / hc.sum()
        self.YH0, self.YE0, self.EH0 = YH0, YE0, EH0

        # ---- unknown vector layout
        self.iD = np.where(self.hasD)[0]
        self.iQ = np.where(self.hasQ)[0]
        self.nF_active = [k for k in range(len(F)) if self.QFS0[k] > 0]
        self.kcap = F.index("fcap")
        self.iFM = [k for k in self.nF_active if F[k] not in self.unemployed
                    and not (k == self.kcap and self.capital == "fixed")]
        self.iU = [k for k in self.nF_active if F[k] in self.unemployed]
        self.iK = np.where(self.QF0[self.kcap] > 0)[0] if self.capital == "fixed" else np.array([], dtype=int)
        self._layout()

    def _layout(self):
        nA = len(self.A)
        sizes = [("QA", nA), ("PDS", len(self.iD)), ("PQ", len(self.iQ)), ("WF", len(self.iFM)),
                 ("RK", len(self.iK)), ("EXR", 1), ("CLOS", 0 if self.closure == "keynesian" else 1),
                 ("GADJ", 1 if self.gov == "cd" else 0), ("WALRAS", 1)]
        self.slices, pos = {}, 0
        for k, n in sizes:
            self.slices[k] = slice(pos, pos + n)
            pos += n
        self.n = pos

    @classmethod
    def from_sam(cls, path=None, **kw):
        """Calibrate to a SAM file (default: 2023). A SAM published in rounded figures (2018) is balanced first
        (SAM.load_for_model); the 2023 SAM is used exactly as before."""
        return cls(SAM.load_for_model(path), **kw)

    # ================================================================== model equations
    def x0(self):
        x = np.zeros(self.n)
        x[self.slices["QA"]] = 1.0          # activity levels relative to benchmark
        x[self.slices["PDS"]] = 1.0
        x[self.slices["PQ"]] = 1.0
        x[self.slices["WF"]] = 1.0
        x[self.slices["RK"]] = 1.0
        x[self.slices["EXR"]] = 1.0
        x[self.slices["GADJ"]] = 1.0
        if self.closure == "investment":
            x[self.slices["CLOS"]] = 0.0
        elif self.closure == "savings":
            x[self.slices["CLOS"]] = 1.0
        return x

    def evaluate(self, x, sh):
        """Compute every variable from the unknowns x under shocks sh; return (residuals, vars)."""
        nC, nA = len(self.C), len(self.A)
        g = lambda k: x[self.slices[k]]
        QA = g("QA") * self.QA0
        PDS = np.ones(nC); PDS[self.iD] = g("PDS")
        PQ = np.ones(nC); PQ[self.iQ] = g("PQ")
        WF = np.ones(len(self.F)); WF[self.iFM] = g("WF")
        if self.closure == "keynesian":         # fixed exchange rate (numeraire); foreign savings adjust
            EXR, FSAVS = sh["exr"], g("EXR")[0]
        else:
            EXR, FSAVS = g("EXR")[0], sh["fsav_scale"]
        WALRAS = g("WALRAS")[0]
        if self.closure == "investment":
            MPSADJ, IADJ = g("CLOS")[0], sh["iadj"]
        elif self.closure == "savings":
            MPSADJ, IADJ = sh["mpsadj"], g("CLOS")[0]
        else:
            MPSADJ, IADJ = sh["mpsadj"], sh["iadj"]

        pwm = self.pwm * sh["pwm_scale"]
        pwe = self.pwe * sh["pwe_scale"]
        tm = self.tm * sh["tm_scale"]
        tq = self.tq * sh["tq_scale"]
        PM = pwm * EXR * (1 + tm)
        PE = pwe * EXR
        # 0.3: input-intensity TWIST. A commodity's coefficient is scaled for every user and all other
        # intermediate inputs are scaled the other way, so total intermediate input per unit of output (at benchmark
        # prices) is unchanged; likewise for the mix of margin services. 1 = benchmark (no effect, no computation).
        ica, sm = self.ica, self.sm
        s_ica, s_sm = sh["ica_scale"], sh["sm_scale"]
        if np.any(s_ica != 1.0):
            tw = s_ica != 1.0
            ica = self.ica.copy()
            ica[tw] = self.ica[tw] * s_ica[tw][:, None]
            rest0 = self.ica[~tw].sum(axis=0)
            need = self.ica.sum(axis=0) - ica[tw].sum(axis=0)
            ica[~tw] = self.ica[~tw] * np.where(rest0 > 0, need / np.where(rest0 > 0, rest0, 1), 1.0)[None, :]
        if np.any(s_sm != 1.0):
            tw = s_sm != 1.0
            sm = self.sm.copy()
            sm[tw] = self.sm[tw] * s_sm[tw]
            rest0 = self.sm[~tw].sum()
            sm[~tw] = self.sm[~tw] * (1.0 - sm[tw].sum()) / rest0
        PTRC = float(sm @ PQ)
        if self.margins == "split":             # 0.3: IFPRI eq. 1 (import price includes its margin)
            PM = PM + self.icx * PTRC
        CPI = float(self.cwts @ PQ)
        for k in self.iU:                       # fixed real wage (nominal in the Keynesian closure)
            WF[k] = sh["wbar"][k] * CPI

        # ---- supply side: CET split of domestic output
        QX = self.theta.T @ QA
        QE = np.zeros(nC); QDs = np.zeros(nC)
        both = self.hasE & self.hasD
        r = np.zeros(nC)
        r[both] = ((PE[both] / _pos(PDS[both])) * self.kgam[both]) ** self.omega[both]
        rt = self.rt
        denom = np.ones(nC)
        denom[both] = self.at[both] * (self.gam[both] * r[both] ** rt[both] + self.gamc[both]) ** (1 / rt[both])
        QDs[both] = QX[both] / denom[both]
        QE[both] = r[both] * QDs[both]
        onlyD = self.hasD & ~self.hasE
        onlyE = self.hasE & ~self.hasD
        QDs[onlyD] = QX[onlyD]
        QE[onlyE] = QX[onlyE]
        PX = np.ones(nC)
        m = self.hasX
        PX[m] = (PE[m] * QE[m] + PDS[m] * QDs[m]) / _pos(QX[m])
        PA = self.theta @ PX

        # ---- value added (CES) and zero profit
        W = WF[:, None] * np.ones((1, nA))
        if self.capital == "fixed":
            W[self.kcap, self.iK] = g("RK")       # activity-specific rental rates
        sig = self.sigva
        cd = sig == 1.0                                       # Cobb-Douglas limit: PVA = prod(W ** delta)
        sig_ = np.where(cd, 0.5, sig)                         # placeholder exponent for the CD columns (overwritten)
        with np.errstate(divide="ignore", invalid="ignore"):
            terms = np.where(self.use, self.delta * _pos(W) ** (1 - sig_), 0.0)
            PVA = terms.sum(axis=0) ** (1 / (1 - sig_))
            PVA_cd = np.exp(np.where(self.use, self.delta * np.log(_pos(W)), 0.0).sum(axis=0))
        PVA = np.where(cd, PVA_cd, PVA) / (self.tfp * sh["tfp_scale"])
        ta = self.ta * sh["ta_scale"]
        ZP = PA * (1 - ta) - (ica.T @ PQ + self.iva * PVA)
        QVA = self.iva * QA
        # factor demand: QF = (QVA / TFP) * delta * (TFP * PVA / W)^sigma   (= QVA * delta at the benchmark)
        tfp = self.tfp * sh["tfp_scale"]
        QF = np.where(self.use, QVA / tfp * self.delta * (PVA * tfp / _pos(W)) ** sig, 0.0)

        # ---- incomes
        YFva = (W * QF).sum(axis=1)
        frow_in = self.frow_in * sh["frow_in_scale"]
        YF = YFva + frow_in * EXR
        dist = (1 - self.tf) * YF - self.frow_out * EXR
        YIF = self.shif * dist[None, :]
        nH = len(self.H)
        trg_ent = self.trg_ent * sh["trg_scale"]
        YE = YIF[nH].sum() + trg_ent * CPI + self.erow_in * EXR
        ESAV = YE * (1 - self.te - self.she.sum() - self.sheg) - self.erow_out * EXR
        trg_h = self.trg_h * sh["trg_scale"] * sh["trg_h_scale"]
        hrow_in = self.hrow_in * sh["remit_scale"]
        trg_add = sh["trg_h_add"]                # additional real transfers, ₱ bn at benchmark prices (e.g. a cash-transfer programme)
        YH = YIF[:nH].sum(axis=1) + self.she * YE + (trg_h + trg_add) * CPI + hrow_in * EXR
        tins = self.tins * sh["tins_scale"]
        DY = YH * (1 - tins - self.tgh) - self.hrow_out * EXR
        mps = np.clip(self.mps * (1 + MPSADJ), -1, 1)
        HSAV = mps * DY
        EH = DY - HSAV
        if self.les is None:
            QH = self.beta * EH[None, :] / _pos(PQ)[:, None]
        else:                                    # LES: subsistence + marginal share of supernumerary spending
            g_, mb_ = self.les["gamma"], self.les["mb"]
            QH = g_ + mb_ * (EH - PQ @ g_)[None, :] / _pos(PQ)[:, None]
        if self.home == "separate":
            # 0.3.1, book eq. 34: own produce valued at the producer price, PX * QHA = beta_h * EH; book eq. 18:
            # marketed output = gross output - home use, split by the CET at the prices found above (PX does not
            # depend on the quantity: constant returns)
            QHA = self.beta_h * EH[None, :] / _pos(PX)[:, None]
            QXm = QX - QHA.sum(axis=1)
            QDs[both] = QXm[both] / denom[both]
            QE[both] = r[both] * QDs[both]
            QDs[onlyD] = QXm[onlyD]
            QE[onlyE] = QXm[onlyE]
            QX = QXm
        else:
            QHA = np.zeros_like(self.HC)

        # ---- demand for composite goods
        if self.gov == "cd":                     # fixed value shares; GADJ = nominal spending index (solved)
            QG = self.qg * g("GADJ")[0] / _pos(PQ)
        else:
            QG = self.qg * sh["qg_scale_vec"] * sh["qg_scale"]
        if self.inv == "value_shares":           # fixed value shares; IADJ = nominal investment index
            QINV = self.qinv * IADJ * sh["qinv_scale_vec"] / _pos(PQ)
        else:
            QINV = self.qinv * IADJ * sh["qinv_scale_vec"]
        QINT = ica @ QA
        D = QINT + QH.sum(axis=1) + QG + QINV + self.qdst
        if self.margins == "composite":
            icq = self.icq
            T = float(icq @ D) / (1 - float(icq @ sm))
            QQ = D + sm * T

            # ---- Armington split and composite price
            PDD = PDS
            QDd = np.zeros(nC); QM = np.zeros(nC); PARM = np.ones(nC)
            mix = self.hasM & self.hasD
            s_ = self.sigq
            PARM[mix] = (self.dq[mix] * PM[mix] ** (1 - s_[mix]) + (1 - self.dq[mix]) * PDD[mix] ** (1 - s_[mix])) \
                ** (1 / (1 - s_[mix])) / self.aq[mix]
            # CES demands: QM = (QQ / aq) * dq * (aq * PARM / PM)^sigma,  QD = (QQ / aq) * (1 - dq) * (aq * PARM / PDD)^sigma
            QM[mix] = QQ[mix] / self.aq[mix] * self.dq[mix] * (self.aq[mix] * PARM[mix] / PM[mix]) ** s_[mix]
            QDd[mix] = QQ[mix] / self.aq[mix] * (1 - self.dq[mix]) * (self.aq[mix] * PARM[mix] / _pos(PDD[mix])) ** s_[mix]
            onlyM = self.hasM & ~self.hasD
            onlyDd = self.hasD & ~self.hasM
            PARM[onlyM] = PM[onlyM] * self.k_m[onlyM]
            QM[onlyM] = QQ[onlyM] * self.k_m[onlyM]
            PARM[onlyDd] = PDD[onlyDd] * self.k_d[onlyDd]
            QDd[onlyDd] = QQ[onlyDd] * self.k_d[onlyDd]
        else:
            # 0.3, margins='split' (IFPRI eq. 3, 24-27): margins enter the demand prices of imports (PM, above) and of
            # domestic goods (PDD) before the Armington choice. Import and domestic demand per unit of composite good
            # depend on prices only (um, ud), so the margin requirement per unit of composite good is
            # kappa = icx * (um + ud), and margin demand T solves T = kappa . (D + sm * T).
            icq = np.zeros(nC)
            PDD = PDS + self.icx * PTRC
            um = np.zeros(nC); ud = np.zeros(nC); PARM = np.ones(nC)
            mix = self.hasM & self.hasD
            s_ = self.sigq
            PARM[mix] = (self.dq[mix] * PM[mix] ** (1 - s_[mix]) + (1 - self.dq[mix]) * PDD[mix] ** (1 - s_[mix])) \
                ** (1 / (1 - s_[mix])) / self.aq[mix]
            um[mix] = self.dq[mix] / self.aq[mix] * (self.aq[mix] * PARM[mix] / PM[mix]) ** s_[mix]
            ud[mix] = (1 - self.dq[mix]) / self.aq[mix] * (self.aq[mix] * PARM[mix] / _pos(PDD[mix])) ** s_[mix]
            onlyM = self.hasM & ~self.hasD
            onlyDd = self.hasD & ~self.hasM
            PARM[onlyM] = PM[onlyM] * self.k_m[onlyM]
            um[onlyM] = self.k_m[onlyM]
            PARM[onlyDd] = PDD[onlyDd] * self.k_d[onlyDd]
            ud[onlyDd] = self.k_d[onlyDd]
            kappa = self.icx * (um + ud)
            T = float(kappa @ D) / (1 - float(kappa @ sm))
            QQ = D + sm * T
            QM = um * QQ
            QDd = ud * QQ
        PQcalc = (1 + tq) * (PARM + icq * PTRC)

        # ---- government
        ATAX = ta * PA * QA
        MTAX = tm * pwm * EXR * QM
        STAX = tq * (PARM + icq * PTRC) * QQ
        YG = (self.te * YE + (tins * YH).sum() + (self.tf * YF).sum() + MTAX.sum() + STAX.sum() + ATAX.sum()
              + self.sheg * YE + (self.tgh * YH).sum() + self.grow_in * EXR)
        GEXP = float(PQ @ QG) + ((trg_h + trg_add) * CPI).sum() + trg_ent * CPI + self.grow_out * EXR
        GSAV = YG - GEXP

        # ---- residuals
        res = []
        res.append(ZP)                                                    # zero profit
        res.append((QDs[self.iD] - QDd[self.iD]) / self.QD0[self.iD])     # domestic sales market
        res.append(PQ[self.iQ] - PQcalc[self.iQ])                          # composite price
        k = self.iFM
        res.append((QF.sum(axis=1)[k] - self.QFS0[k] * sh["qfs_scale"][k]) / self.QFS0[k])  # factor markets
        if self.capital == "fixed":
            kk, ia = self.kcap, self.iK
            res.append((QF[kk, ia] - self.QF0[kk, ia] * sh["kscale"][ia] * sh["qfs_scale"][kk]) / self.QF0[kk, ia])
        fcu_out = (pwm * (QM + self.rex)).sum() + self.frow_out.sum() + self.erow_out + self.hrow_out.sum() + self.grow_out
        fcu_in = (pwe * (QE + self.rex)).sum() + frow_in.sum() + self.erow_in + hrow_in.sum() + self.grow_in + self.fsav * FSAVS
        res.append(np.array([(fcu_out - fcu_in) / self.QM0.sum()]))        # current account
        INVV = float(PQ @ (QINV + self.qdst))
        SAV = HSAV.sum() + ESAV + GSAV + self.fsav * FSAVS * EXR
        res.append(np.array([(SAV - INVV - WALRAS) / self.qinv.sum()]))    # savings = investment
        if self.closure != "keynesian":
            res.append(np.array([CPI - sh["cpi"]]))                        # numeraire (the fixed exchange rate is the numeraire otherwise)
        if self.gov == "cd":
            res.append(np.array([(GEXP - (1 - self.ssg) * YG) / self.qg.sum()]))   # government spends revenue net of saving
        R = np.concatenate(res)

        V = dict(W=W, EMP=QF.sum(axis=1), pwm=pwm, pwe=pwe, QA=QA, QX=QX, QE=QE, QD=QDd, QM=QM, QQ=QQ, QF=QF, QVA=QVA, QINT=QINT, QH=QH, QHA=QHA, QG=QG,
                 QINV=QINV, PA=PA, PX=PX, PDS=PDS, PE=PE, PM=PM, PQ=PQ, PVA=PVA, WF=WF, EXR=EXR,
                 CPI=CPI, PTRC=PTRC, YF=YF, YIF=YIF, YE=YE, YH=YH, DY=DY, EH=EH, HSAV=HSAV, ESAV=ESAV,
                 YG=YG, GEXP=GEXP, GSAV=GSAV, MTAX=MTAX, STAX=STAX, ATAX=ATAX, T=T, MPSADJ=MPSADJ, IADJ=IADJ,
                 WALRAS=WALRAS, fcu_out=fcu_out, fcu_in=fcu_in, FSAV=self.fsav * FSAVS)
        return R, V

    # ================================================================== shocks and solving
    def default_shocks(self):
        nC, nA, nF = len(self.C), len(self.A), len(self.F)
        return dict(iadj=1.0, mpsadj=0.0, pwm_scale=np.ones(nC), pwe_scale=np.ones(nC), tm_scale=np.ones(nC),
                    tq_scale=np.ones(nC), tfp_scale=np.ones(nA), frow_in_scale=np.ones(nF), trg_scale=1.0,
                    trg_h_scale=np.ones(len(self.H)), remit_scale=np.ones(len(self.H)), tins_scale=np.ones(len(self.H)),
                    qg_scale=1.0, qg_scale_vec=np.ones(nC), qinv_scale_vec=np.ones(nC), qfs_scale=np.ones(nF),
                    fsav_scale=1.0, cpi=1.0, exr=1.0, wbar=np.ones(nF), kscale=np.ones(nA),
                    trg_h_add=np.zeros(len(self.H)), ta_scale=np.ones(nA), ica_scale=np.ones(nC), sm_scale=np.ones(nC))

    def make_shocks(self, spec=None):
        """Translate a readable shock spec into arrays. Keys:
        'qinv_scale': {commodity: factor}   real investment demand (e.g. {'ccons': 0.9})
        'qg_scale': factor or {commodity: factor}   real government consumption
        'pwm_scale' / 'pwe_scale': {commodity: factor}   world import / export prices
        'tm_scale', 'tq_scale': {commodity: factor}   tariff and sales-tax rates
        'tfp_scale': {activity: factor}   productivity
        'qfs_scale': {factor: factor}   factor supplies (e.g. {'fcap': 1.05})
        'remit_scale': factor or {household: factor}   remittances (foreign currency)
        'trg_scale': factor   all government transfers (real);  'trg_h_scale': {household: factor}
        'trg_h_add': {household: ₱ bn}   additional real government transfers (negative = a cut), e.g. a cash-transfer programme;
                     needed because the SAM records only ₱103.7 bn of transfers to households
        'tins_scale': factor or {household: factor}   household direct-tax rates
        'ta_scale': factor or {activity: factor}   activity-tax rates (2018 SAM only; 0.3)
        'ica_scale': {commodity: factor}   input-intensity twist: that commodity per unit of output, for every activity,
                     with all other intermediate inputs scaled down so total input per unit is unchanged (0.3)
        'sm_scale': {commodity: factor}   the same twist within the mix of margin services (0.3)
        'fsav_scale': factor   foreign savings;  'iadj' / 'mpsadj': closure levels;  'cpi': numeraire level
        """
        sh = self.default_shocks()
        idx = {"c": {c: i for i, c in enumerate(self.C)}, "a": {a: i for i, a in enumerate(self.A)},
               "f": {f: i for i, f in enumerate(self.F)}, "h": {h: i for i, h in enumerate(self.H)}}
        vec_keys = {"qinv_scale": ("qinv_scale_vec", "c"), "pwm_scale": ("pwm_scale", "c"), "pwe_scale": ("pwe_scale", "c"),
                    "tm_scale": ("tm_scale", "c"), "tq_scale": ("tq_scale", "c"), "tfp_scale": ("tfp_scale", "a"),
                    "qfs_scale": ("qfs_scale", "f"), "remit_scale": ("remit_scale", "h"), "trg_h_scale": ("trg_h_scale", "h"),
                    "tins_scale": ("tins_scale", "h"), "frow_in_scale": ("frow_in_scale", "f"),
                    "wbar": ("wbar", "f"), "kscale": ("kscale", "a"), "trg_h_add": ("trg_h_add", "h"),
                    "ta_scale": ("ta_scale", "a"), "ica_scale": ("ica_scale", "c"), "sm_scale": ("sm_scale", "c")}
        for k, val in (spec or {}).items():
            if k == "qg_scale":
                if isinstance(val, dict):
                    for c, f in val.items(): sh["qg_scale_vec"][idx["c"][c]] = f
                else:
                    sh["qg_scale"] = float(val)
            elif k in vec_keys:
                tgt, kind = vec_keys[k]
                if isinstance(val, dict):
                    for name, f in val.items(): sh[tgt][idx[kind][name]] = f
                else:
                    sh[tgt][:] = float(val)
            elif k in ("trg_scale", "fsav_scale", "iadj", "mpsadj", "cpi", "exr"):
                sh[k] = float(val)
            else:
                raise KeyError(f"Unknown shock '{k}'")
        return sh

    def solve(self, spec=None, x_start=None, tol=1e-10, verbose=False) -> Solution:
        sh = self.make_shocks(spec)
        x0 = self.x0() if x_start is None else x_start.copy()
        f = lambda x: self.evaluate(x, sh)[0]
        r0 = f(x0)
        if np.abs(r0).max() < tol:
            R, V = self.evaluate(x0, sh)
            return Solution(x0, V, True, "starting point already solves the model", float(np.abs(R).max()), spec or {})
        out = root(f, x0, method="hybr", options={"xtol": 1e-12, "maxfev": 200 * (self.n + 1)})
        if not out.success or np.abs(out.fun).max() > 1e-7:
            out2 = root(f, out.x if np.isfinite(out.x).all() else x0, method="lm", options={"xtol": 1e-13, "maxiter": 20000})
            if np.abs(out2.fun).max() < np.abs(out.fun).max():
                out = out2
        R, V = self.evaluate(out.x, sh)
        ok = bool(np.abs(R).max() < 1e-7)
        if verbose:
            print(f"solve: {'OK' if ok else 'FAILED'}  max residual {np.abs(R).max():.2e}  Walras {V['WALRAS']:.2e}  ({out.message})")
        return Solution(out.x, V, ok, str(out.message), float(np.abs(R).max()), spec or {})

    # ================================================================== reporting
    def gdp(self, sol: Solution) -> dict:
        """Nominal GDP by expenditure and by income, and real GDP at benchmark prices."""
        v = sol.v
        C_ = float(v["PQ"] @ v["QH"].sum(axis=1)) + float(v["PX"] @ v["QHA"].sum(axis=1))   # + own produce (0.3.1)
        G_ = float(v["PQ"] @ v["QG"])
        I_ = float(v["PQ"] @ (v["QINV"] + self.qdst))
        X_ = float(v["PE"] @ v["QE"]) + float(v["EXR"] * (v["pwe"] @ self.rex))
        M_ = float(v["EXR"] * (v["pwm"] @ (v["QM"] + self.rex)))
        gdp_exp = C_ + G_ + I_ + X_ - M_
        va = float((v["W"] * v["QF"]).sum())
        gdp_inc = va + float(v["MTAX"].sum() + v["STAX"].sum() + v["ATAX"].sum())
        real = float(v["QH"].sum() + v["QHA"].sum() + v["QG"].sum() + (v["QINV"] + self.qdst).sum() + v["QE"].sum() - v["QM"].sum())
        return dict(nominal_expenditure=gdp_exp, nominal_income=gdp_inc, real=real,
                    C=C_, G=G_, I=I_, X=X_, M=M_)

    def compare(self, base: Solution, sim: Solution) -> pd.DataFrame:
        gb, gs = self.gdp(base), self.gdp(sim)
        rows = [("Real GDP (benchmark prices)", gb["real"], gs["real"]),
                ("Real household consumption", base["QH"].sum() + base["QHA"].sum(), sim["QH"].sum() + sim["QHA"].sum()),
                ("Real investment", base["QINV"].sum(), sim["QINV"].sum()),
                ("Real exports", base["QE"].sum(), sim["QE"].sum()),
                ("Real imports", base["QM"].sum(), sim["QM"].sum()),
                ("Exchange rate (index)", base["EXR"], sim["EXR"]),
                ("Consumer price index", base["CPI"], sim["CPI"]),
                ("Government savings", base["GSAV"], sim["GSAV"])]
        for k, f in enumerate(self.F):
            rows.append((f"Factor price {f}", base["WF"][k], sim["WF"][k]))
            rows.append((f"Employment {f}", base["EMP"][k], sim["EMP"][k]))
        rows.append(("Capital rental (average)", float((base["W"][self.kcap] * base["QF"][self.kcap]).sum() / base["QF"][self.kcap].sum()),
                     float((sim["W"][self.kcap] * sim["QF"][self.kcap]).sum() / sim["QF"][self.kcap].sum())))
        for i, h in enumerate(self.H):
            rows.append((f"Real consumption {h}", base["EH"][i] / base["CPI"], sim["EH"][i] / sim["CPI"]))
        df = pd.DataFrame(rows, columns=["variable", "base", "sim"])
        df["pct_change"] = (df["sim"] / df["base"] - 1) * 100
        return df

    def rebuild_sam(self, sol: Solution) -> pd.DataFrame:
        """Rebuild the SAM implied by a solution (used by the replication check)."""
        v = sol.v
        idx = self.sam.codes
        S = pd.DataFrame(0.0, index=idx, columns=idx)
        A, C, H, F = self.A, self.C, self.H, self.F
        EXR, CPI = v["EXR"], v["CPI"]
        S.loc[A, C] = self.theta * v["QA"][:, None] * v["PX"][None, :]
        if self.home == "separate":                  # 0.3.1: own produce goes back to the activity -> household cells
            for a in A:
                k = C.index("c" + a[1:])
                val = v["PX"][k] * v["QHA"][k]
                S.loc[a, "c" + a[1:]] -= val.sum()
                S.loc[a, H] = val
        S.loc[C, A] = self.ica * v["QA"][None, :] * v["PQ"][:, None]
        S.loc[F, A] = v["W"] * v["QF"]
        S.loc[C, "trc"] = v["PQ"] * self.sm * v["T"]
        if self.margins == "split":
            S.loc["trc", C] = self.icx * (v["QM"] + v["QD"]) * v["PTRC"]
        else:
            S.loc["trc", C] = self.icq * v["QQ"] * v["PTRC"]
        S.loc[C, H] = v["QH"] * v["PQ"][:, None]
        S.loc[C, "gov"] = v["QG"] * v["PQ"]
        S.loc[C, "s-i"] = v["QINV"] * v["PQ"]
        S.loc[C, "dstk"] = self.qdst * v["PQ"]
        S.loc[C, "row"] = v["QE"] * v["PE"] + v["pwe"] * EXR * self.rex
        S.loc["row", C] = v["pwm"] * EXR * (v["QM"] + self.rex)
        S.loc["mtax", C] = v["MTAX"]
        S.loc["stax", C] = v["STAX"]
        for k, f in enumerate(F):
            S.loc[f, "row"] = self.frow_in[k] * EXR
            S.loc["row", f] = self.frow_out[k] * EXR
            if self.has_ftax:
                S.loc["ftax", f] = self.tf[k] * v["YF"][k]
            for i, inst in enumerate(self.inst):
                S.loc[inst, f] = v["YIF"][i, k]
        S.loc["ent", "gov"] = self.trg_ent * CPI
        S.loc["ent", "row"] = self.erow_in * EXR
        S.loc["dtax", "ent"] = self.te * v["YE"]
        S.loc[H, "ent"] = self.she * v["YE"]
        S.loc["gov", "ent"] = self.sheg * v["YE"]
        S.loc["row", "ent"] = self.erow_out * EXR
        S.loc["s-i", "ent"] = v["ESAV"]
        S.loc[H, "gov"] = self.trg_h * CPI
        S.loc[H, "row"] = self.hrow_in * EXR
        S.loc["dtax", H] = self.tins * v["YH"]
        S.loc["gov", H] = self.tgh * v["YH"]
        S.loc["row", H] = self.hrow_out * EXR
        S.loc["s-i", H] = v["HSAV"]
        S.loc["gov", "dtax"] = self.te * v["YE"] + (self.tins * v["YH"]).sum()
        if self.has_ftax:
            S.loc["gov", "ftax"] = (self.tf * v["YF"]).sum()
        if self.has_atax:
            S.loc["atax", A] = v["ATAX"]
            S.loc["gov", "atax"] = float(v["ATAX"].sum())
        S.loc["gov", "mtax"] = v["MTAX"].sum()
        S.loc["gov", "stax"] = v["STAX"].sum()
        S.loc["gov", "row"] = self.grow_in * EXR
        S.loc["row", "gov"] = self.grow_out * EXR
        S.loc["s-i", "gov"] = v["GSAV"]
        S.loc["s-i", "row"] = self.fsav * EXR
        S.loc["dstk", "s-i"] = float(v["PQ"] @ self.qdst)
        return S
