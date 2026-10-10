"""IFPRI validation, route A, step 3: pystdcge vs IFPRI's own model on the same condensed Philippine SAM.

Reads gams_ph/ifpri_results.csv (written by IFPRI's model, 1DMODEL_PH.GMS, run with GAMS 54.5 demo licence) and runs
pystdcge on the same netted SAM (gams_ph/sam_netted.csv), with the same four shocks and the same two closures:
  SAV  saving rates fixed, investment adjusts   (pystdcge closure="savings")
  INV  real investment fixed, household saving rates adjust   (pystdcge closure="investment")
Both: CPI numeraire, flexible exchange rate, fixed foreign savings, fixed real government consumption and tax rates,
full employment, mobile factors. Measures are percent changes from each model's own base.
Run:  py validation/ifpri/compare.py   (after running GAMS on gams_ph/1DMODEL_PH.GMS)
      py validation/ifpri/compare.py split   (0.3, verification Phase 3: pystdcge with IFPRI-style margins,
      CGE(margins="split"); writes out/comparison_pystdcge_vs_ifpri_split_margins.csv)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from pystdcge.cge import CGE      # noqa: E402
from pystdcge.sam import SAM      # noqa: E402

G = HERE / "gams_ph"
ifp = pd.read_csv(G / "ifpri_results.csv")
ifp["closure"] = ifp["closure"].str.upper(); ifp["shock"] = ifp["shock"].str.upper()

t = pd.read_csv(G / "sam_netted.csv", index_col=0)
sam = SAM(t, {}, "condensed 2023 SAM, IFPRI netting")
SHOCKS = {"T1": {"pwm_scale": {"cchem": 1.10}}, "T2": {"qinv_scale": {"ccons": 0.90}},
          "T3": {"remit_scale": 0.90}, "T4": {"tfp_scale": {"aagri": 1.05}}}
NAMES = {"T1": "World import price of chemicals & petroleum +10%", "T2": "Construction investment -10%",
         "T3": "Remittances -10%", "T4": "Agricultural productivity +5%"}
CLOS = {"SAV": "savings", "INV": "investment"}

MARGINS = sys.argv[1] if len(sys.argv) > 1 else "composite"
rows = []
for cl, closure in CLOS.items():
    m = CGE(sam, closure=closure, margins=MARGINS)
    b = m.solve()
    assert b.ok and b.residual_max < 1e-7
    def measures(s):
        out = {("MACRO", "RGDP"): m.gdp(s)["real"], ("MACRO", "RCONS"): float(s["QH"].sum()),
               ("MACRO", "REXP"): float(s["QE"].sum()), ("MACRO", "RIMP"): float(s["QM"].sum()), ("MACRO", "EXR"): float(s["EXR"])}
        for k, f in enumerate(m.F):
            out[("WF", f)] = float(s["WF"][k])
        for i, a in enumerate(m.A):
            out[("QA", a)] = float(s["QA"][i])
        for i, h in enumerate(m.H):
            out[("RCONSH", h)] = float(s["QH"][:, i].sum())
        return out
    mb = measures(b)
    for sh, spec in SHOCKS.items():
        s = m.solve(spec)
        assert s.ok, (cl, sh)
        ms = measures(s)
        sub = ifp[(ifp.closure == cl)]
        for (grp, item), v in ms.items():
            ib = sub[(sub.shock == "BASE") & (sub.group == grp) & (sub["item"] == item)]["value"]
            iv = sub[(sub.shock == sh) & (sub.group == grp) & (sub["item"] == item)]["value"]
            if ib.empty or iv.empty:
                continue
            ours = (v / mb[(grp, item)] - 1) * 100
            ifpri = (float(iv.iloc[0]) / float(ib.iloc[0]) - 1) * 100
            rows.append(dict(closure=cl, shock=sh, group=grp, item=item, pystdcge_pct=ours, ifpri_pct=ifpri,
                             diff_pp=ours - ifpri))
res = pd.DataFrame(rows)
suffix = "" if MARGINS == "composite" else f"_{MARGINS}_margins"
res.to_csv(HERE / "out" / f"comparison_pystdcge_vs_ifpri{suffix}.csv", index=False)
print("pystdcge margins option:", MARGINS)

pd.set_option("display.width", 200)
key = res[res.group.isin(["MACRO"]) & res["item"].isin(["RGDP", "RCONS", "EXR"])]
print(key.pivot_table(index=["closure", "shock"], columns="item", values=["pystdcge_pct", "ifpri_pct"]).round(4).to_string())
print("\nLargest absolute differences (percentage points) by closure and shock:")
print(res.assign(absd=res.diff_pp.abs()).groupby(["closure", "shock"]).absd.max().round(4).to_string())
print("\nMax abs difference overall:", round(res.diff_pp.abs().max(), 4), "pp;  median:", round(res.diff_pp.abs().median(), 5))
