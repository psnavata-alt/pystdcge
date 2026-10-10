"""A public investment programme in the recursive-dynamic model, 2023-2030.

Real construction investment +5% in 2027 and 2028, with the documented baseline, capital tied to its industry,
the hybrid closure (short run in shock years) and, as a range, the public-capital productivity channel.
Run from the repository root:  python examples/02_dynamic_investment_programme.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pystdcge.settings import dynamic_model  # noqa: E402

PROGRAMME = {2027: {"qinv_scale": {"ccons": 1.05}}, 2028: {"qinv_scale": {"ccons": 1.05}}}

for pc in ("off", "low", "high"):
    d = dynamic_model("extended", public_capital=pc)
    base = d.baseline()
    res = d.compare(base, d.scenario(PROGRAMME))
    print(f"\npublic capital channel: {pc}")
    print(res[["gdp_gap_bn", "gdp_gap_pct"]].round(3).to_string())
