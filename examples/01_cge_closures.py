"""One shock, three closures, and the fixed-price SAM bound.

World import price of chemicals and petroleum +20% and, separately, real construction investment -10%, in the
long-run (investment-driven), savings-driven and short-run Keynesian closures of the standard CGE model.
Run from the repository root:  python examples/01_cge_closures.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd  # noqa: E402

from pystdcge.cge import CGE  # noqa: E402

CLOSURES = {"long run (investment-driven)": {}, "savings-driven": {"closure": "savings"},
            "short run (Keynesian)": {"closure": "keynesian", "unemployed": ("flab-n", "flab-p"), "capital": "fixed"}}
SHOCKS = {"import price of chemicals and petroleum +20%": {"pwm_scale": {"cchem": 1.2}},
          "real construction investment -10%": {"qinv_scale": {"ccons": 0.9}}}

rows = []
for cname, kw in CLOSURES.items():
    m = CGE.from_sam(**kw)
    base = m.solve()
    for sname, spec in SHOCKS.items():
        s = m.solve(spec)
        g0, g1 = m.gdp(base), m.gdp(s)
        rows.append({"closure": cname, "shock": sname,
                     "real GDP (%)": (g1["real"] / g0["real"] - 1) * 100,
                     "household consumption (%)": (s["QH"].sum() / base["QH"].sum() - 1) * 100,
                     "solved": s.ok, "equation residual": float(abs(s["WALRAS"]))})
print(pd.DataFrame(rows).set_index(["shock", "closure"]).round(3).to_string())
