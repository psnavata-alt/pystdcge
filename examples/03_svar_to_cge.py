"""From a structural VAR to the CGE, on SIMULATED data (replace them with your own series).

1. A monthly VAR in which a block of world variables (oil price growth, a risk index) cannot be affected by the
   domestic block (exchange-rate depreciation, remittance growth, FDI), identified by a Cholesky ordering.
2. The responses to a risk shock: total, and with the exchange rate held at baseline (the part that runs through it).
3. Year-one changes of the external variables become a CGE shock (macrolink.cge_shocks); the CGE's own GDP and
   exchange-rate changes are compared with the VAR's (macrolink.consistency).
Run from the repository root:  python examples/03_svar_to_cge.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pystdcge import macrolink as ML, svar  # noqa: E402
from pystdcge.cge import CGE  # noqa: E402

# --- 1. simulated data from a known VAR(1): oil, risk | depreciation, remittances, FDI (US$ million)
rng = np.random.default_rng(2026)
names = ["oil", "risk", "depr", "remit", "fdi"]
A = np.array([[0.30, 0.00, 0, 0, 0], [0.05, 0.50, 0, 0, 0], [0.02, 0.30, 0.2, 0.0, 0.0],
              [0.01, -0.10, 0.1, 0.3, 0.0], [0.00, -40.0, -5.0, 0.0, 0.2]])
L = np.diag([8.0, 0.5, 0.8, 1.5, 150.0])
Y = np.zeros((300, 5))
for t in range(1, len(Y)):
    Y[t] = A @ Y[t - 1] + L @ rng.standard_normal(5)
df = pd.DataFrame(Y, columns=names)

# --- 2. estimate and identify
m = svar.fit(df, 2, exog_block=["oil", "risk"])
B = svar.cholesky(m)
j = names.index("risk")
size = 1.0 / B[j, j]                                   # a one-unit rise in the risk index
total = svar.irf(m, B, 24)[:, :, j] * size
held = svar.counterfactual_irf(m, B, shock=j, hold="depr", H=24, size=size)
k = names.index("fdi")
print("cumulative depreciation after 12 months: %.2f%%" % total[:12, 2].sum())
print("FDI over 12 months (US$ million): total %.1f; with the exchange rate held at baseline %.1f; through the "
      "exchange rate %.1f" % (total[:12, k].sum(), held[:12, k].sum(), total[:12, k].sum() - held[:12, k].sum()))

# --- 3. to the CGE (savings-driven closure, so lower FDI lowers investment through foreign savings)
oil_y1 = ML.annual(total[:, 0], 12, cumulative=True)      # oil: month-on-month growth, cumulated, averaged over year 1
remit_y1 = ML.annual(total[:, 3], 12, cumulative=True)
fdi_y1 = ML.annual(total[:, 4], 12, how="sum")            # FDI: US$ million over year 1
cge = CGE.from_sam(closure="savings")
spec = ML.cge_shocks(cge, oil_pct=oil_y1, remit_pct=remit_y1, fdi_usd_m=fdi_y1, php_per_usd=58.0, gdp_bn=28009.93)
base, sim = cge.solve(), cge.solve(spec)
print("CGE shock:", spec)
print(ML.consistency(cge, base, sim, {"real_exchange_rate": ML.annual(total[:, 2], 12, cumulative=True)}).round(3))
