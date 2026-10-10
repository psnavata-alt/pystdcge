"""Home consumption (own produce) moved to market vs kept separate (book equations 18 and 34): does it matter?
Run from the repository root:  python examples/home_consumption_sensitivity.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd  # noqa: E402

from pystdcge.cge import CGE  # noqa: E402

SHORT = {"closure": "keynesian", "unemployed": ("flab-n", "flab-p"), "capital": "fixed"}
SHOCKS = {"construction investment -10%": {"qinv_scale": {"ccons": 0.9}},
          "import price of chemicals and petroleum +20%": {"pwm_scale": {"cchem": 1.2}},
          "remittances -10%": {"remit_scale": 0.9}}
rows = []
for home in ("market", "separate"):
    m = CGE.from_sam(home=home, **SHORT)
    b = m.solve()
    for name, spec in SHOCKS.items():
        s = m.solve(spec)
        rows.append({"shock": name, "home consumption": home,
                     "real GDP (%)": (m.gdp(s)["real"] / m.gdp(b)["real"] - 1) * 100,
                     "household consumption (%)": (s["QH"].sum() / b["QH"].sum() - 1) * 100})
print(pd.DataFrame(rows).pivot(index="shock", columns="home consumption").round(4).to_string())
