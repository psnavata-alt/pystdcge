"""IFPRI validation, route A, step 1: a condensed 2023 SAM and pystdcge's results on it.

The free GAMS demo solves nonlinear models of at most 1,000 variables and 1,000 equations, so IFPRI's standard model
cannot run on the full 41-sector SAM. Both models are therefore run on the SAME condensed SAM (9 sectors, 10 household
groups). The equations are identical for every sector, so agreement on the condensed SAM validates the model.

Like-for-like choices (so that differences come from the models, not the data):
  - home consumption is moved to marketed consumption first (pystdcge's treatment; SAM.move_home_consumption_to_market);
  - IFPRI's model is to be run with Leontief top-level production, Cobb-Douglas-equivalent household demand
    (LES with no subsistence), one region, no factor nests, and pystdcge's elasticities (0.8, 2.0, 2.0).

Outputs (validation/ifpri/out/): condensed SAM (CSV), the mapping, and pystdcge's results for the test shocks in the
long-run closure (real investment fixed, saving rates adjust, CPI numeraire, full employment, mobile factors), which is
the closure IFPRI's model will be set to.
Run:  py validation/ifpri/build_condensed_sam.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pystdcge import paths                     # noqa: E402
from pystdcge.cge import CGE                    # noqa: E402
from pystdcge.sam import SAM                    # noqa: E402

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

GROUPS = {   # condensed sector: 2023 SAM sectors (activity and commodity codes without the a/c prefix)
    "agri": ["maiz", "rice", "ocer", "puls", "oils", "root", "vege", "sugr", "toba", "cott", "frui", "coff", "ocrp",
             "catt", "poul", "oliv", "fore", "fish"],
    "mine": ["mine"],
    "food": ["food", "beve"],
    "chem": ["chem"],                              # chemicals and petroleum: kept separate for the oil-price test
    "oman": ["text", "wood", "nmet", "metl", "mach", "oman"],
    "util": ["elec", "watr"],
    "cons": ["cons"],
    "trad": ["trad", "tran"],
    "serv": ["hotl", "comm", "fsrv", "real", "bsrv", "padm", "educ", "heal", "osrv"],
}

sam = SAM.load(paths.SAM_2023).move_home_consumption_to_market()
mapping = {}
for g, members in GROUPS.items():
    for m in members:
        for p in "ac":
            if p + m in sam.codes:
                mapping[p + m] = p + g
missing = [c for c in sam.accounts("a") + sam.accounts("c") if c not in mapping]
assert not missing, f"unmapped sectors: {missing}"
small = sam.aggregate(mapping)
chk = small.check(verbose=False)
assert chk["balanced"], chk
small.table.to_csv(OUT / "sam2023_condensed_9sectors.csv")
pd.Series(mapping, name="condensed").to_csv(OUT / "mapping_41_to_9.csv")

SHOCKS = {
    "T1 world import price of chemicals and petroleum +10%": {"pwm_scale": {"cchem": 1.10}},
    "T2 construction investment -10% (real)": {"qinv_scale": {"ccons": 0.90}},
    "T3 remittances -10%": {"remit_scale": 0.90},
    "T4 agricultural productivity +5%": {"tfp_scale": {"aagri": 1.05}},
}
m = CGE(small)                     # long run: investment closure, CPI numeraire, full employment, mobile capital
base = m.solve()
assert base.ok and base.residual_max < 1e-7
res = {}
for name, spec in SHOCKS.items():
    s = m.solve(spec)
    assert s.ok, name
    gb, gs = m.gdp(base), m.gdp(s)
    pct = lambda new, old: float((new / old - 1) * 100)
    r = {"real GDP": pct(gs["real"], gb["real"]),
         "real household consumption": pct(s["QH"].sum(), base["QH"].sum()),
         "real exports": pct(s["QE"].sum(), base["QE"].sum()),
         "real imports": pct(s["QM"].sum(), base["QM"].sum()),
         "exchange rate": pct(s["EXR"], base["EXR"])}
    for k, f in enumerate(m.F):
        r[f"factor price {f}"] = pct(s["WF"][k], base["WF"][k])
    for i, a in enumerate(m.A):
        r[f"output {a}"] = pct(s["QA"][i], base["QA"][i])
    for i, h in enumerate(m.H):
        r[f"real consumption {h}"] = pct(s["EH"][i] / s["CPI"], base["EH"][i] / base["CPI"])
    r["Walras slack"] = float(s["WALRAS"])
    res[name] = r
df = pd.DataFrame(res)
df.to_csv(OUT / "pystdcge_results_condensed_long_run.csv")
(OUT / "pystdcge_results_condensed_long_run.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(f"Condensed SAM: {len(small.codes)} accounts ({len(m.A)} activities, {len(m.C)} commodities, {len(m.H)} households); "
      f"balanced (max gap {chk['max_row_col_gap']:.1e}); benchmark residual {base.residual_max:.1e}")
print(df.round(3).to_string())
