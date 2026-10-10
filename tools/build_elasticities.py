"""Build pystdcge's Philippine elasticity sets (added in 0.3).

Sources (all opened 2 Oct 2026; see docs/parameters.md):
  KW   Kapuscinski and Warr (1999), Economic Modelling 16: 257-278, Table 4, column 7 (basic ECM, the authors'
       preferred specification): Armington elasticities for 33 Philippine commodities, with import shares from
       Table 1. Transcribed from the page images: data/raw/elasticities/Kapuscinski_Warr_1999_Table4_ECM.csv.
  GTAP GTAP 9 standard parameters as carried in the World Bank MANAGE-WB template (MIT licence;
       data/raw/elasticities/MANAGE-WB_GTAP9_template_*.csv): Armington ESUBD by commodity ('sigmam0'), value-added
       substitution ESUBVA by activity (= 'va New' / 2, which reproduces GTAP's published ESUBVA). Aggregated to the model's
       GEM's sectors with Philippine weights from the GTAP 9 flows in MANAGE-WB's gtapData9.gdx: imports into the
       Philippines (viws), exports (vxwd), value added (vfm).
  PCGEM Cororaton (2000), PIDS DP 2000-33, Table 3: CET (export transformation) by 34 sectors: assumed values.

Rule for the 'ph' Armington set: use KW where the estimate is significant (10%) and positive and the significant
estimates cover at least half of the model group's imports (KW Table 1 import shares); otherwise GTAP.

Output: data/processed/elasticities_ph_v1.csv (one row per model commodity or activity, with source and grade).
Run:  py tools/build_elasticities.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pystdcge import paths          # noqa: E402
from pystdcge.sam import SAM        # noqa: E402

E = ROOT / "data" / "raw" / "elasticities"
GDX = ROOT / "external" / "MANAGE-WB-main" / "dat" / "gtapData9.gdx"
GDXDUMP = Path(r"C:/GAMS/54/gdxdump.exe")

# ---- pystdcge 2023 SAM sectors -> GTAP 9 sectors
G = {"maiz": ["GRO"], "rice": ["PDR"], "ocer": ["GRO"], "puls": ["V_F"], "oils": ["OSD"], "root": ["V_F"], "vege": ["V_F"],
     "sugr": ["C_B"], "toba": ["OCR"], "cott": ["PFB"], "frui": ["V_F"], "coff": ["OCR"], "ocrp": ["OCR"], "catt": ["CTL"],
     "poul": ["OAP"], "oliv": ["OAP", "RMK", "WOL"], "fore": ["FRS"], "fish": ["FSH"], "mine": ["COA", "OIL", "GAS", "OMN"],
     "food": ["CMT", "OMT", "VOL", "MIL", "PCR", "SGR", "OFD"], "beve": ["B_T"], "text": ["TEX", "WAP", "LEA"],
     "wood": ["LUM", "PPP"], "chem": ["P_C", "CRP"], "nmet": ["NMM"], "metl": ["I_S", "NFM", "FMP"],
     "mach": ["ELE", "OME", "MVH", "OTN"], "oman": ["OMF"], "elec": ["ELY", "GDT"], "watr": ["WTR"], "cons": ["CNS"],
     "trad": ["TRD"], "tran": ["OTP", "WTP", "ATP"], "hotl": ["TRD"], "comm": ["CMN"], "fsrv": ["OFI", "ISR"],
     "real": ["OBS", "DWE"], "bsrv": ["OBS"], "padm": ["OSG"], "educ": ["OSG"], "heal": ["OSG"], "osrv": ["ROS"]}
# ---- pystdcge sectors -> Kapuscinski-Warr commodity numbers (Table 1/4)
KWMAP = {"maiz": [1], "frui": [2], "vege": [3], "root": [4], "ocrp": [5], "toba": [5], "coff": [5], "catt": [6], "poul": [7],
         "oliv": [8], "fish": [9], "fore": [10], "mine": [11, 12], "rice": [13], "food": [14, 15, 16, 17, 18, 19, 20],
         "beve": [21], "text": [22, 23], "wood": [24, 25], "chem": [26, 27, 28], "nmet": [29], "metl": [30],
         "mach": [30, 31, 32], "oman": [33]}
# ---- pystdcge sectors -> PCGEM 34-sector CET (Table 3, tau_e)
PCGEM_CET = {1: 0.30, 2: 1.50, 3: 2.00, 4: 0.30, 5: 1.50, 6: 0.30, 7: 0.30, 8: 1.50, 9: 0.30, 10: 0.80, 11: 0.80, 12: 2.00,
             13: 1.50, 14: 0.70, 15: 0.70, 16: 2.50, 17: 1.50, 18: 0.90, 19: 1.30, 20: 0.30, 21: 1.50, 22: 1.50, 23: 3.00,
             24: 1.30, 25: 0.60, 26: 0.30, 27: 0.30, 28: 0.30, 29: 0.30, 30: 0.30, 34: 0.30}
PCMAP = {"maiz": [1], "rice": [1], "ocer": [1], "puls": [2], "root": [2], "vege": [2], "frui": [2], "oils": [3], "sugr": [3],
         "toba": [6], "cott": [6], "coff": [6], "ocrp": [6], "catt": [4], "poul": [4], "oliv": [4], "fore": [7], "fish": [5],
         "mine": [8], "food": [9, 10, 11, 12, 14], "beve": [13], "text": [15, 16], "wood": [17, 18], "chem": [19, 20],
         "nmet": [21], "metl": [22], "mach": [23, 24], "oman": [25], "elec": [27], "watr": [27], "cons": [26],
         "fsrv": [28], "educ": [29], "heal": [30], "trad": [34], "tran": [34], "hotl": [34], "comm": [34], "real": [34],
         "bsrv": [34], "padm": [34], "osrv": [34]}


def gtap_phl():
    """Philippine imports, exports (by GTAP commodity) and value added (by GTAP activity), GTAP 9."""
    out = {}
    for sym in ("viws", "vxwd", "vfm"):
        raw = subprocess.run([str(GDXDUMP), str(GDX), f"symb={sym}", "format=csv"], capture_output=True, text=True).stdout
        df = pd.read_csv(pd.io.common.StringIO(raw))
        if sym == "viws":
            out["imp"] = df[df.Dim3 == "PHL"].groupby("Dim1").Val.sum()
        elif sym == "vxwd":
            out["exp"] = df[df.Dim2 == "PHL"].groupby("Dim1").Val.sum()
        else:
            out["va"] = df[df.Dim3 == "PHL"].groupby("Dim2").Val.sum()
    return out


def wavg(values: dict, weights: pd.Series, keys: list) -> float:
    v = np.array([values[k] for k in keys], float)
    w = np.array([float(weights.get(k, 0.0)) for k in keys], float)
    return float(v.mean()) if w.sum() <= 0 else float((v * w).sum() / w.sum())


def main():
    com = pd.read_csv(E / "MANAGE-WB_GTAP9_template_comPar.csv")
    esubd = {c.split("-")[1].upper(): float(v) for c, v in zip(com.commodity, com.sigmam0)}
    act = pd.read_csv(E / "MANAGE-WB_GTAP9_template_actPar.csv")
    esubva = {a.split("-")[1].upper(): float(v) / 2 for a, v in zip(act.activity, act.va_new)}
    kw = pd.read_csv(E / "Kapuscinski_Warr_1999_Table4_ECM.csv", comment="#").set_index("no")
    w = gtap_phl()
    sam = SAM.load(paths.SAM_2023)
    rows = []
    for c in sam.accounts("c"):
        s = c[1:]
        g = G[s]
        arm_gtap = wavg(esubd, w["imp"], g)
        cet_gtap = wavg(esubd, w["exp"], g)          # MANAGE-WB sets CET = Armington by default
        arm_ph, src = arm_gtap, "GTAP 9 ESUBD (PHL import-weighted)"
        if s in KWMAP:
            sub = kw.loc[KWMAP[s]]
            sig = sub[(sub.significant == 1) & (sub.ecm > 0)]
            cover = sig.import_share.sum() / sub.import_share.sum() if sub.import_share.sum() > 0 else 0.0
            if len(sig) and cover >= 0.5:
                arm_ph = float((sig.ecm * sig.import_share).sum() / sig.import_share.sum()) if sig.import_share.sum() > 0 else float(sig.ecm.mean())
                src = f"Kapuscinski-Warr 1999 ECM (commodities {list(sig.index)}; {cover:.0%} of group imports)"
        cet_pc = float(np.mean([PCGEM_CET[k] for k in PCMAP[s]])) if s in PCMAP else np.nan
        rows.append(dict(kind="commodity", code=c, gtap=" ".join(g), sigma_q_gtap=round(arm_gtap, 4), sigma_q_ph=round(arm_ph, 4),
                         sigma_q_ph_source=src, omega_t_gtap=round(cet_gtap, 4), omega_t_pcgem=round(cet_pc, 4)))
    for a in sam.accounts("a"):
        s = a[1:]
        g = G[s]
        rows.append(dict(kind="activity", code=a, gtap=" ".join(g), sigma_va_gtap=round(wavg(esubva, w["va"], g), 4)))
    out = pd.DataFrame(rows)
    dst = ROOT / "data" / "processed" / "elasticities_ph_v1.csv"
    out.to_csv(dst, index=False)
    print(f"Wrote {dst}")
    with pd.option_context("display.width", 220, "display.max_colwidth", 70):
        print(out[out.kind == "commodity"][["code", "gtap", "sigma_q_gtap", "sigma_q_ph", "omega_t_gtap", "omega_t_pcgem", "sigma_q_ph_source"]].to_string(index=False))
        print(out[out.kind == "activity"][["code", "gtap", "sigma_va_gtap"]].to_string(index=False))


if __name__ == "__main__":
    main()
