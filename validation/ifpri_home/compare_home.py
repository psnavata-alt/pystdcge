"""pystdcge CGE(home="separate") against IFPRI's own model, both with HOME CONSUMPTION kept (8 Oct 2026).

Same design as ../ifpri/compare.py (four test shocks, closures SAV and INV), on gams_ph/sam_netted_home.csv. Real
household consumption, real GDP and household real consumption include home consumption valued at base producer prices
in both models; RHOME is home consumption alone.
Run:  py validation/ifpri_home/compare_home.py [composite|split]   (pystdcge margins option; default composite)
Writes out/comparison_home_<margins>.csv
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
(HERE / "out").mkdir(exist_ok=True)
ifp = pd.read_csv(G / "ifpri_results.csv")
ifp["closure"] = ifp["closure"].str.upper(); ifp["shock"] = ifp["shock"].str.upper()
sam = SAM(pd.read_csv(G / "sam_netted_home.csv", index_col=0), {}, "condensed 2023 SAM, home consumption kept, IFPRI netting")
SHOCKS = {"T1": {"pwm_scale": {"cchem": 1.10}}, "T2": {"qinv_scale": {"ccons": 0.90}},
          "T3": {"remit_scale": 0.90}, "T4": {"tfp_scale": {"aagri": 1.05}}}
CLOS = {"SAV": "savings", "INV": "investment"}
MARGINS = sys.argv[1] if len(sys.argv) > 1 else "composite"


def run(margins: str) -> pd.DataFrame:
    rows = []
    for cl, closure in CLOS.items():
        m = CGE(sam, closure=closure, margins=margins, home="separate")
        b = m.solve()
        assert b.ok and b.residual_max < 1e-7

        def measures(s):
            out = {("MACRO", "RGDP"): m.gdp(s)["real"], ("MACRO", "RCONS"): float(s["QH"].sum() + s["QHA"].sum()),
                   ("MACRO", "RHOME"): float(s["QHA"].sum()),
                   ("MACRO", "REXP"): float(s["QE"].sum()), ("MACRO", "RIMP"): float(s["QM"].sum()), ("MACRO", "EXR"): float(s["EXR"])}
            for k, f in enumerate(m.F):
                out[("WF", f)] = float(s["WF"][k])
            for i, a in enumerate(m.A):
                out[("QA", a)] = float(s["QA"][i])
            for i, h in enumerate(m.H):
                out[("RCONSH", h)] = float(s["QH"][:, i].sum() + s["QHA"][:, i].sum())
            return out
        mb = measures(b)
        for sh, spec in SHOCKS.items():
            s = m.solve(spec)
            assert s.ok, (cl, sh)
            ms = measures(s)
            sub = ifp[ifp.closure == cl]
            for (grp, item), v in ms.items():
                ib = sub[(sub.shock == "BASE") & (sub.group == grp) & (sub["item"] == item)]["value"]
                iv = sub[(sub.shock == sh) & (sub.group == grp) & (sub["item"] == item)]["value"]
                if ib.empty or iv.empty:
                    continue
                ours = (v / mb[(grp, item)] - 1) * 100
                ifpri = (float(iv.iloc[0]) / float(ib.iloc[0]) - 1) * 100
                rows.append(dict(closure=cl, shock=sh, group=grp, item=item, pystdcge_pct=ours, ifpri_pct=ifpri, diff_pp=ours - ifpri))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    res = run(MARGINS)
    res.to_csv(HERE / "out" / f"comparison_home_{MARGINS}.csv", index=False)
    print("pystdcge: home='separate', margins =", MARGINS, "|", len(res), "comparisons")
    pd.set_option("display.width", 200)
    key = res[res["item"].isin(["RGDP", "RCONS", "RHOME"])]
    print(key.pivot_table(index=["closure", "shock"], columns="item", values=["pystdcge_pct", "ifpri_pct"]).round(4).to_string())
    a = res.diff_pp.abs()
    print(f"\nWithin 0.01 pp: {(a < 0.01).sum()}  within 0.1 pp: {(a < 0.1).sum()}  of {len(res)};  largest {a.max():.4f} pp; "
          f"GDP and consumption largest {a[res['item'].isin(['RGDP', 'RCONS'])].max():.4f} pp; home consumption largest "
          f"{a[res['item'] == 'RHOME'].max():.4f} pp")
    print(res.loc[a.sort_values(ascending=False).index[:6]].round(4).to_string(index=False))
