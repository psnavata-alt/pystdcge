"""Test of the explanation for the last nominal gap with IFPRI (8 Oct 2026).

With IFPRI-style margins (check V3), all nominal results (exchange rate, factor prices) differ from IFPRI's by about the
same 0.05 pp under T1, while real results agree. Explanation offered on 7 Oct: the numeraire. Both models fix a CPI,
but IFPRI's CPI weights each good by its base composite price PQ0, which includes sales tax and margins
(1DMODEL_PH.GMS: cwts line 698, CPI0 line 711, PQ0 line 642), while pystdcge's base prices are all 1.

Test, without changing either model: a CGE is homogeneous of degree zero in prices, so pystdcge's solution can be
rescaled so that IFPRI's CPI, rather than pystdcge's, equals its base value. Divide every pystdcge nominal result by
  k = sum_c w_c * PQ_c / PQ0_c,   w_c = cwts_c * PQ0_c / sum(cwts * PQ0)   (IFPRI's index, relative to base)
If the explanation is right, the rescaled nominal results match IFPRI's and real results are unchanged.
IFPRI's PQ0 and cwts are recomputed here from the same SAM with IFPRI's own formulas (lines 590-642, 698).
Run:  py validation/ifpri/matched_cpi_test.py      writes out/matched_cpi_test.csv
"""
from __future__ import annotations

import sys
from pathlib import Path


import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from pystdcge.cge import CGE      # noqa: E402
from pystdcge.sam import SAM      # noqa: E402

G = HERE / "gams_ph"
t = pd.read_csv(G / "sam_netted.csv", index_col=0)
A = [c for c in t.index if c.startswith("a")]
C = [c for c in t.index if c.startswith("c")]
H = [c for c in t.index if c.startswith("hhd")]

# ---- IFPRI's base composite prices, with the margin split used for IFPRI's inputs (build_ifpri_inputs.py)
out_val = t.loc[A, C].sum()
QE0 = t.loc[C, "row"]
QD0 = (out_val - QE0).clip(lower=0)                       # PDS0 = PE0 = 1
imp = t.loc["row", C]
share_d = (QD0 / (QD0 + imp)).fillna(1.0)
trcdom, trcimp = t.loc["trc", C] * share_d, t.loc["trc", C] * (1 - share_d)
PDD0 = ((QD0 + trcdom) / QD0.where(QD0 > 0)).fillna(1.0)
PM0 = PDD0.where(QD0 > 0, 1.0)
QM0 = (imp + t.loc["mtax", C] + trcimp) / PM0
QQ0 = QD0 + QM0
PQ0 = (t.loc[C].sum(axis=1) - QE0) / QQ0                  # (SAM(C,'TOTAL') - SAM(C,'ROW')) / QQ0
cwts = t.loc[C, H].sum(axis=1) / t.loc[C, H].values.sum()
w = cwts * PQ0 / (cwts * PQ0).sum()                         # IFPRI's effective CPI weights
print("IFPRI base composite prices PQ0:", PQ0.round(4).to_dict())

ifp = pd.read_csv(G / "ifpri_results.csv")
ifp["closure"] = ifp["closure"].str.upper(); ifp["shock"] = ifp["shock"].str.upper()
sam = SAM(t, {}, "condensed 2023 SAM, IFPRI netting")
SHOCKS = {"T1": {"pwm_scale": {"cchem": 1.10}}, "T2": {"qinv_scale": {"ccons": 0.90}},
          "T3": {"remit_scale": 0.90}, "T4": {"tfp_scale": {"aagri": 1.05}}}
rows = []
for cl, closure in {"SAV": "savings", "INV": "investment"}.items():
    m = CGE(sam, closure=closure, margins="split")
    b = m.solve()
    wv = w.loc[m.C].values
    for sh, spec in SHOCKS.items():
        s = m.solve(spec)
        k = float(wv @ (s["PQ"] / b["PQ"]))                  # IFPRI's CPI at pystdcge's solution (base = 1)
        sub = ifp[ifp.closure == cl]
        def ifpri(grp, item):
            vb = float(sub[(sub.shock == "BASE") & (sub.group == grp) & (sub["item"] == item)]["value"].iloc[0])
            vs = float(sub[(sub.shock == sh) & (sub.group == grp) & (sub["item"] == item)]["value"].iloc[0])
            return (vs / vb - 1) * 100
        items = [("MACRO", "EXR", s["EXR"] / b["EXR"])] + [("WF", f, s["WF"][i] / b["WF"][i]) for i, f in enumerate(m.F)]
        # real imports: IFPRI adds import quantities measured in purchaser-price units (QM0 = value incl. tariff and
        # margin / PDD0, lines 617-632); pystdcge in world-price units. Re-weight pystdcge's quantities into IFPRI units.
        u = (QM0 / imp.where(imp > 0)).fillna(0.0).loc[m.C].values  # IFPRI import units per pystdcge unit
        items.append(("MACRO", "RIMP", float(u @ s["QM"]) / float(u @ b["QM"])))
        rimp_raw = float(s["QM"].sum() / b["QM"].sum())
        for grp, item, ratio in items:
            if item == "RIMP":                               # a quantity: no price rescaling; 'raw' = unweighted sum
                raw_, adj = (rimp_raw - 1) * 100, (ratio - 1) * 100
            else:
                raw_ = (ratio - 1) * 100
                adj = (ratio / k - 1) * 100
            ip = ifpri(grp, item)
            rows.append(dict(closure=cl, shock=sh, item=item, ifpri_pct=ip, pystdcge_pct=raw_, pystdcge_rescaled_pct=adj,
                             gap_before_pp=raw_ - ip, gap_after_pp=adj - ip, ifpri_cpi_at_pystdcge_solution=k))
df = pd.DataFrame(rows)
(HERE / "out").mkdir(exist_ok=True)
df.to_csv(HERE / "out" / "matched_cpi_test.csv", index=False)
pd.set_option("display.width", 200)
print(df[df.shock == "T1"].round(4).to_string(index=False))
nom, ri = df[df["item"] != "RIMP"], df[df["item"] == "RIMP"]
print(f"\nNominal results (exchange rate, 5 factor prices; 4 shocks x 2 closures = {len(nom)}): largest gap "
      f"{nom.gap_before_pp.abs().max():.4f} pp before, {nom.gap_after_pp.abs().max():.4f} pp after rescaling to IFPRI's CPI")
print(f"Real imports ({len(ri)}): largest gap {ri.gap_before_pp.abs().max():.4f} pp as an unweighted sum, "
      f"{ri.gap_after_pp.abs().max():.4f} pp in IFPRI's purchaser-price units")
