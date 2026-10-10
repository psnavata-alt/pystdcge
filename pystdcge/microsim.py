"""Top-down microsimulation: CGE (or multiplier) results -> FIES 2023 households -> poverty.

Method (the "representative household group" approach used by IFPRI, the World Bank and PIDS):
  1. Each FIES 2023 household is assigned to one of the SAM's ten groups: urban or rural
     (PSA's URB flag) x national per-capita income quintile (from PSA's decile NPCINC).
  2. For each group the model gives the change in nominal consumption spending (EH) and in the
     group's own price index (its budget shares x commodity prices). The ratio is the change in
     real consumption.
  3. Every household's per-capita income is scaled by its group's real change, and poverty is
     recomputed against PSA's official household poverty thresholds (pline_2023), weighted by
     the population weight (mem_rfact). The baseline reproduces PSA's official 17.54 million poor.

Limits: households within a group move together (no within-group change in inequality); income is
used as the welfare measure, as in PSA's official poverty statistics. A behavioural microsimulation
(re-ranking, labour-market transitions) is on the roadmap.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import paths

OFFICIAL_POOR_2023 = 17_540_000     # PSA, 2023 Full-Year Official Poverty Statistics


class Microsim:
    def __init__(self, path=None):
        f = pd.read_csv(path or paths.FIES_POVLINES)
        f.columns = [c.upper() for c in f.columns]
        f = f.rename(columns={"PLINE_2023": "PLINE", "FLINE_2023": "FLINE"})
        for c in ["W_PROV", "FSIZE", "TOINC", "RFACT", "MEM_RFACT", "URB", "NPCINC", "PLINE", "FLINE"]:
            f[c] = pd.to_numeric(f[c], errors="coerce")
        f = f.dropna(subset=["FSIZE", "TOINC", "RFACT", "NPCINC", "PLINE"])
        f["POP"] = f["MEM_RFACT"]
        f["PCI"] = f["TOINC"] / f["FSIZE"]
        f["grp"] = np.where(f["URB"] == 1, "hhd-u", "hhd-r") + np.ceil(f["NPCINC"] / 2).astype(int).astype(str)
        self.f = f

    def poverty(self, factor=None) -> dict:
        """Poverty with per-capita income scaled by `factor` (Series aligned to households, or None)."""
        f = self.f
        pci = f["PCI"] * (1.0 if factor is None else factor)
        poor = pci < f["PLINE"]
        food_poor = pci < f["FLINE"]
        pop = f["POP"]
        gap = ((f["PLINE"] - pci).clip(lower=0) / f["PLINE"] * pop).sum() / pop.sum()
        return dict(poor=float(pop[poor].sum()), rate_pct=float(pop[poor].sum() / pop.sum() * 100),
                    food_poor=float(pop[food_poor].sum()), poverty_gap_pct=float(gap * 100),
                    population=float(pop.sum()))

    def baseline(self) -> dict:
        return self.poverty()

    def group_factors_from_cge(self, model, base, sim) -> pd.Series:
        """Real consumption change by SAM household group: (EH_sim/EH_base) / (P_h,sim / P_h,base)."""
        out = {}
        for i, h in enumerate(model.H):
            w = model.beta[:, i]
            p_b, p_s = float(w @ base["PQ"]), float(w @ sim["PQ"])
            wh = getattr(model, "beta_h", None)                  # 0.3.1: own produce, valued at producer prices
            if wh is not None and wh[:, i].any():
                p_b += float(wh[:, i] @ base["PX"])
                p_s += float(wh[:, i] @ sim["PX"])
            out[h] = (sim["EH"][i] / base["EH"][i]) / (p_s / p_b)
        return pd.Series(out)

    def simulate(self, group_factors: pd.Series) -> dict:
        factor = self.f["grp"].map(group_factors).fillna(1.0)
        b, s = self.baseline(), self.poverty(factor)
        b30 = self.f["NPCINC"] <= 3
        loss = (self.f["PCI"] * (1 - factor) * self.f["POP"])
        return dict(baseline=b, simulated=s, new_poor=s["poor"] - b["poor"],
                    new_food_poor=s["food_poor"] - b["food_poor"],
                    bottom30_share_of_loss=float(loss[b30].sum() / loss.sum()) if loss.sum() != 0 else float("nan"),
                    group_factors=group_factors.round(5).to_dict())

    def from_cge(self, model, base, sim) -> dict:
        return self.simulate(self.group_factors_from_cge(model, base, sim))
