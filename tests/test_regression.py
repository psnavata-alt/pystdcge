"""R0: key results with default settings equal the frozen reference (tests/reference_results.json, relative 1e-9).

Any change to the code that moves a default result fails this test. New features must be opt-in. To refreeze after a
deliberate, documented change:  python tests/test_regression.py --update
"""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
REF = HERE / "reference_results.json"
SHORT_RUN = dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")


def compute() -> dict:
    from pystdcge.cge import CGE
    from pystdcge.dynamic import DynamicCGE
    from pystdcge.multiplier import SAMMultiplier
    from pystdcge.sam import SAM
    from pystdcge import paths
    out = {}
    mult = SAMMultiplier(SAM.load(paths.SAM_2023))
    out["sam_2023_household_multiplier_rural_q1"] = mult.household_income_multiplier({"hhd-r1": 1.0})
    shocks = {"oil20": {"pwm_scale": {"cchem": 1.2}}, "remit_m10": {"remit_scale": 0.9},
              "cons_inv_m10": {"qinv_scale": {"ccons": 0.9}}}
    for cname, kw in (("long_run", {}), ("savings", {"closure": "savings"}), ("short_run", SHORT_RUN)):
        m = CGE.from_sam(**kw)
        b = m.solve()
        for sname, sh in shocks.items():
            s = m.solve(sh)
            out[f"cge_{cname}_{sname}_real_gdp_pct"] = (m.gdp(s)["real"] / m.gdp(b)["real"] - 1) * 100
            out[f"cge_{cname}_{sname}_household_consumption_pct"] = (s["QH"].sum() / b["QH"].sum() - 1) * 100
    d = DynamicCGE()
    base = d.baseline()
    sc = d.scenario({2025: {"qinv_scale": {"ccons": 0.9}}})
    out["dynamic_construction_m10_2025_cumulative_gdp_gap_bn"] = float(d.compare(base, sc).loc["cumulative", "gdp_gap_bn"])
    out["dynamic_baseline_real_gdp_2030"] = float(base.table.loc[2030, "real_gdp"])
    return {k: float(v) for k, v in out.items()}


@pytest.mark.slow
def test_regression():
    ref = json.loads(REF.read_text(encoding="utf-8"))
    now = compute()
    bad = {k: (ref[k], now.get(k)) for k in ref if now.get(k) is None or abs(now[k] - ref[k]) > 1e-9 * max(1.0, abs(ref[k]))}
    assert not bad, bad


if __name__ == "__main__" and "--update" in sys.argv:
    REF.write_text(json.dumps(compute(), indent=1), encoding="utf-8")
    print("written", REF)
