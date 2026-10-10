"""The equation map (docs/equations.md) cites lines of pystdcge/cge.py: check that each cited line still holds the
code it describes, so the map cannot silently go out of date when the code changes."""
from conftest import ROOT

# line -> text that must be on that line of cge.py (book equation in the comment)
CITED = {
    397: "PM = pwm * EXR * (1 + tm)",                      # eq. 1
    419: "PM = PM + self.icx * PTRC",                      # eq. 1, split margins
    398: "PE = pwe * EXR",                                 # eq. 2
    518: "PDD = PDS",                                      # eq. 3
    539: "PDD = PDS + self.icx * PTRC",                    # eq. 3, split margins
    558: "PQcalc = (1 + tq) * (PARM + icq * PTRC)",        # eq. 4
    441: "PX[m] = (PE[m] * QE[m] + PDS[m] * QDs[m])",      # eq. 5
    442: "PA = self.theta @ PX",                           # eq. 6
    457: "ZP = PA * (1 - ta) - (ica.T @ PQ + self.iva * PVA)",   # eq. 7-8
    456: "ta = self.ta * sh[\"ta_scale\"]",                # activity tax
    420: "CPI = float(self.cwts @ PQ)",                    # eq. 9
    586: "CPI - sh[\"cpi\"]",                              # numeraire
    458: "QVA = self.iva * QA",                            # eq. 13
    510: "QINT = ica @ QA",                                # eq. 14, 17
    452: "terms = np.where(self.use, self.delta",          # eq. 15
    461: "QF = np.where(self.use, QVA / tfp * self.delta", # eq. 16
    447: "W[self.kcap, self.iK] = g(\"RK\")",              # activity-specific rents
    425: "QX = self.theta.T @ QA",                         # eq. 18-20
    427: "both = self.hasE & self.hasD",                   # eq. 21
    429: "r[both] = ((PE[both] / _pos(PDS[both])) * self.kgam[both]) ** self.omega[both]",   # eq. 22
    435: "onlyD = self.hasD & ~self.hasE",                 # eq. 23
    522: "PARM[mix] = (self.dq[mix] * PM[mix] ** (1 - s_[mix])",   # eq. 24
    543: "PARM[mix] = (self.dq[mix] * PM[mix] ** (1 - s_[mix])",   # eq. 24, split margins
    525: "QM[mix] = QQ[mix] / self.aq[mix] * self.dq[mix]",        # eq. 25
    527: "onlyM = self.hasM & ~self.hasD",                 # eq. 26
    513: "icq = self.icq",                                 # eq. 27
    553: "kappa = self.icx * (um + ud)",                   # eq. 27, split margins
    464: "YFva = (W * QF).sum(axis=1)",                    # eq. 28
    467: "dist = (1 - self.tf) * YF - self.frow_out * EXR",  # eq. 29
    471: "YE = YIF[nH].sum() + trg_ent * CPI",             # eq. 30
    476: "YH = YIF[:nH].sum(axis=1) + self.she * YE",      # eq. 30-31
    478: "DY = YH * (1 - tins - self.tgh)",                # eq. 32
    483: "QH = self.beta * EH[None, :] / _pos(PQ)[:, None]",       # eq. 33, Cobb-Douglas
    486: "QH = g_ + mb_ * (EH - PQ @ g_)[None, :]",        # eq. 33, LES
    509: "QINV = self.qinv * IADJ * sh[\"qinv_scale_vec\"]",      # eq. 35
    505: "QG = self.qg * sh[\"qg_scale_vec\"] * sh[\"qg_scale\"]",  # eq. 36
    564: "YG = (self.te * YE + (tins * YH).sum()",         # eq. 37
    566: "GEXP = float(PQ @ QG)",                          # eq. 38
    575: "QF.sum(axis=1)[k] - self.QFS0[k]",               # eq. 39
    421: "for k in self.iU:",                              # unemployment closure
    578: "QF[kk, ia] - self.QF0[kk, ia]",                  # capital fixed by sector
    572: "QDs[self.iD] - QDd[self.iD]",                    # eq. 40
    579: "fcu_out = (pwm * (QM + self.rex)).sum()",        # eq. 41
    567: "GSAV = YG - GEXP",                               # eq. 42
    477: "tins = self.tins * sh[\"tins_scale\"]",          # eq. 43
    479: "mps = np.clip(self.mps * (1 + MPSADJ), -1, 1)",  # eq. 44
    584: "(SAV - INVV - WALRAS) / self.qinv.sum()",        # eq. 45
}


def test_cited_lines_hold_their_code():
    lines = (ROOT / "pystdcge" / "cge.py").read_text(encoding="utf-8").splitlines()
    wrong = {n: lines[n - 1].strip()[:80] for n, s in CITED.items() if s not in lines[n - 1]}
    assert not wrong, f"docs/equations.md cites lines that moved: {wrong}"


def test_every_cited_line_is_in_the_map():
    doc = (ROOT / "docs" / "equations.md").read_text(encoding="utf-8")
    missing = [n for n in CITED if str(n) not in doc]
    assert not missing, missing
