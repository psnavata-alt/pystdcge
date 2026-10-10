"""Split the IFPRI 2023 SAM's "chemicals and petroleum" into refined petroleum and other chemicals.

The IFPRI Nexus SAM puts ISIC 19-22 (coke and refined petroleum; chemicals incl. fertilizers; pharmaceuticals; rubber and
plastics) in one activity/commodity pair (achem/cchem; IFPRI 2023 data paper, Table A1). PSA's 2018 input-output table
(240 sectors) separates them: refined petroleum = sectors 107-108, the rest = 109-118 (also Cororaton's GTAP mapping,
docs/references/cge_models/gtap/12059.pdf, Table 8.87). The 2023 SAM itself was built on the 2018 table (data paper,
Table 7), so its shares are the consistent source.

New accounts: apetr / cpetr (refined petroleum); achem / cchem keep the code but now mean chemicals, pharmaceuticals,
rubber and plastics only. Every other account keeps exactly its row and column totals and cells.

Rules (all shares from PSA 2018, Table C.1, 240-industry transactions, data/raw/io/240-Industry20Table202018.xlsx):
  uses of cchem (row)       each cell split by PSA's share of sectors 107-108 in that buyer's purchases of 107-118:
                            intermediate use by the PSA sectors mapped to each SAM activity; household final consumption
                            (same share for all ten household groups: the FIES public file has no fuel detail);
                            government consumption; gross capital formation (construction, durable equipment, breeding
                            stock, intellectual property); changes in inventories; exports
  the 2x2 block cchem x achem  PSA's flows among 107-108 and 109-118
  imports (row x cchem)     PSA imports column
  import duties (mtax)      in proportion to imports (ASSUMPTION: same average duty rate)
  sales taxes (stax)        excise on petroleum products to cpetr in full (FUEL_EXCISE_2023), the rest in proportion to
                            domestic use (VAT and other product taxes at a common average rate; ASSUMPTION)
  margins (trc)             in proportion to domestic use (purchases other than exports; ASSUMPTION)
  output (activity -> commodity)  closes each commodity account: output = uses - imports - duties - taxes - margins
  inputs of achem (column)  each input row split by PSA's input purchases of sectors 107-108 vs 109-118 (PSA rows mapped
                            to SAM commodities); labour types by compensation of employees, capital by gross operating
                            surplus; then each activity's capital income is adjusted so its column total equals its output
                            (the adjustments are equal and opposite, so the capital account total is unchanged)
Output: data/processed/IFPRI_SAM_PHL_2023_SAM_petroleum_split.csv (same format as the IFPRI file) and a report in
outputs/sam_petroleum_split_<date>.md. Run:  py tools/build_sam_petroleum_split.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pystdcge import paths                       # noqa: E402
from pystdcge.sam import SAM                     # noqa: E402

# Excise tax on petroleum products collected in 2023 by BIR and BOC (₱ bn). SOURCE TO VERIFY: CPBRD Facts in Figures
# FF2025-42, "Excise Tax on Petroleum Products in the Philippines" (May 2025), as quoted in a search-result snippet on
# 2 Oct 2026 (the PDF is behind a bot check). Status: ATTRIBUTED until the PDF is opened.
FUEL_EXCISE_2023 = 139.7
PETR = list(range(107, 109))
CHEM = list(range(109, 119))
OUT = paths.DATA_PROCESSED / "IFPRI_SAM_PHL_2023_SAM_petroleum_split.csv"


def psa_activity(k: int) -> str:
    """PSA 2018 240-industry sector number -> IFPRI 2023 SAM activity (IFPRI data paper Table A1, ISIC Rev. 4)."""
    crops = {1: "arice", 2: "amaiz", 3: "aoils", 4: "asugr", 5: "afrui", 6: "afrui", 7: "afrui", 8: "acoff", 9: "aroot",
             10: "aocrp", 11: "acoff", 12: "acott", 13: "atoba", 14: "aroot", 15: "afrui", 16: "afrui", 17: "afrui",
             18: "avege", 19: "avege", 20: "avege", 21: "aocrp", 22: "aocrp", 23: "aoliv", 24: "acatt", 25: "acatt",
             26: "aoliv", 27: "acatt", 28: "apoul", 29: "apoul", 30: "aoliv", 31: "afore", 38: "aocrp"}
    if k in crops:
        return crops[k]
    for lo, hi, a in ((32, 37, "afish"), (39, 45, "amine"), (46, 68, "afood"), (69, 77, "abeve"), (78, 94, "atext"),
                      (95, 106, "awood"), (107, 118, "achem"), (119, 122, "anmet"), (123, 131, "ametl"),
                      (132, 161, "amach"), (162, 171, "aoman"), (172, 173, "aelec"), (174, 175, "awatr"),
                      (176, 176, "acons"), (177, 179, "atrad"), (180, 190, "atran"), (191, 193, "ahotl"),
                      (194, 203, "acomm"), (204, 208, "afsrv"), (209, 210, "areal"), (211, 227, "absrv"),
                      (228, 228, "apadm"), (229, 230, "aeduc"), (231, 233, "aheal"), (234, 240, "aosrv")):
        if lo <= k <= hi:
            return a
    raise KeyError(k)


def load_psa():
    ws = openpyxl.load_workbook(paths.DATA_RAW / "io" / "240-Industry20Table202018.xlsx", read_only=True,
                                data_only=True)["240 TT"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h).strip() if h is not None else "" for h in rows[9]]
    num = lambda v: float(v) if isinstance(v, (int, float)) else 0.0
    T = np.array([[num(rows[9 + i][1 + j]) for j in range(1, 241)] for i in range(1, 241)])   # 240 x 240 flows
    col = lambda name: np.array([num(rows[9 + i][hdr.index(name)]) for i in range(1, 241)])
    fd = {"hfce": col("Household Final Consumption Expenditure"),
          "gfce": col("Government Final Consumption Expenditure"),
          "gcf": col("Construction") + col("Durable Equipment") + col("Breeding Stocks and Orchard Development")
          + col("Intellectual Property Products"),
          "inv": col("Changes in Inventories"), "exp": col("Exports of Goods and Services"),
          "imp": col("Imports of Goods and Services")}
    lab = {str(r[0]).strip(): r for r in rows if r and r[0] is not None}
    va = {k: np.array([num(lab[k][1 + j]) for j in range(1, 241)]) for k in ("COE", "GOS", "T-S")}
    # check the layout: sector 107 is 'Refined petroleum products'
    assert "Refined petroleum" in str(rows[9 + 107][1]), rows[9 + 107][:3]
    return T, fd, va


def write_ifpri_csv(S, path):
    """Write a SAM in the IFPRI layout read by SAM.load: title/Code header, label and code columns, totals."""
    import csv
    t, codes = S.table, list(S.table.index)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["2023 Social Accounting Matrix for Philippines, petroleum split (pystdcge 0.3)", "Code"] + codes + ["total"])
        for r in codes:
            w.writerow([S.labels.get(r, r), r] + [("%.10f" % v if v else "") for v in t.loc[r].values] + ["%.10f" % t.loc[r].sum()])
        w.writerow(["Total", "total"] + ["%.10f" % v for v in t.sum(axis=0).values] + [""])


def share(x_p, x_c):
    s = x_p + x_c
    return x_p / s if s > 0 else 0.0


def main():
    T, fd, va = load_psa()
    s = SAM.load(paths.SAM_2023)
    t = s.table.copy()
    A, H = s.accounts("a"), s.accounts("hhd")
    P, C = [k - 1 for k in PETR], [k - 1 for k in CHEM]                # 0-based PSA indices
    act_of = {k: psa_activity(k) for k in range(1, 241)}
    cols_of = {a: [k - 1 for k in range(1, 241) if act_of[k] == a] for a in set(act_of.values())}

    # --- new accounts, inserted after achem / cchem
    codes = list(t.index)
    new = codes[:codes.index("achem") + 1] + ["apetr"] + codes[codes.index("achem") + 1:codes.index("cchem") + 1] \
        + ["cpetr"] + codes[codes.index("cchem") + 1:]
    t = t.reindex(index=new, columns=new, fill_value=0.0)
    labels = dict(s.labels)
    labels["apetr"] = "Activities - Refined petroleum (split from chemicals and petroleum, pystdcge 0.3)"
    labels["cpetr"] = "Commodities - Refined petroleum (split from chemicals and petroleum, pystdcge 0.3)"
    labels["achem"] = "Activities - Chemicals, pharmaceuticals, rubber and plastics (petroleum split off, pystdcge 0.3)"
    labels["cchem"] = "Commodities - Chemicals, pharmaceuticals, rubber and plastics (petroleum split off, pystdcge 0.3)"
    orig = s.table
    rep = []

    # --- 1. uses of the commodity (row cchem)
    for a in A:
        x = orig.loc["cchem", a]
        if not x:
            continue
        if a == "achem":                                           # set with the refinery technology (step 3)
            continue
        j = cols_of.get(a)
        if j:
            sh = share(T[np.ix_(P, j)].sum(), T[np.ix_(C, j)].sum())
        else:                                                      # no PSA sector (e.g. pulses): economy-wide average
            sh = share(T[P, :].sum(), T[C, :].sum())
        t.loc["cpetr", a], t.loc["cchem", a] = x * sh, x * (1 - sh)
        rep.append((f"cchem -> {a}", x, round(sh, 4)))
    fdmap = {**{h: "hfce" for h in H}, "gov": "gfce", "s-i": "gcf", "dstk": "inv", "row": "exp"}
    for c_, key in fdmap.items():
        x = orig.loc["cchem", c_]
        if not x:
            continue
        sh = share(fd[key][P].sum(), fd[key][C].sum())
        t.loc["cpetr", c_], t.loc["cchem", c_] = x * sh, x * (1 - sh)
        if c_ == H[0] or c_ in ("gov", "s-i", "dstk", "row"):
            rep.append((f"cchem -> {c_ if c_ not in H else 'households (all groups)'}", x if c_ not in H else
                        float(orig.loc["cchem", H].sum()), round(sh, 4)))
    # --- 2-3. refinery technology, supply and output, solved together (output feeds back through own use)
    row_of = {}
    for k in range(1, 241):                                         # PSA rows -> SAM commodity
        row_of.setdefault("c" + act_of[k][1:], []).append(k - 1)
    row_of["cpetr"], row_of["cchem"] = P, C
    # refinery inputs: commodities the SAM's chemicals-and-petroleum activity buys in material amounts (>= ₱1 bn);
    # smaller cells (e.g. ₱0.0002 bn of oilseeds) stay with chemicals, and the refinery coefficients are renormalised
    comm_in = [r for r in orig.index if r.startswith("c") and orig.loc[r, "achem"] >= 1.0 and r != "cchem"] + ["cpetr", "cchem"]
    out_b = T[:, P].sum() + va["COE"][P].sum() + va["GOS"][P].sum()   # basic prices: product taxes stay in stax
    coef = {r: T[np.ix_(row_of[r], P)].sum() / out_b for r in comm_in}
    dropped = 1 - sum(coef.values()) - (va["COE"][P].sum() + va["GOS"][P].sum()) / out_b
    lab = va["COE"][P].sum() / out_b
    cap = va["GOS"][P].sum() / out_b
    scale = 1 / (sum(coef.values()) + lab + cap)                     # renormalise (inputs the SAM's achem never buys)
    coef = {r: v * scale for r, v in coef.items()}
    lab, cap = lab * scale, cap * scale
    labs = [f for f in orig.index if f.startswith("flab") and orig.loc[f, "achem"]]
    labmix = {f: orig.loc[f, "achem"] / sum(orig.loc[g, "achem"] for g in labs) for f in labs}
    pc = T[np.ix_(P, C)].sum() / (T[np.ix_(P, C)].sum() + T[np.ix_(C, C)].sum())   # petroleum share of chemicals' own-group inputs
    M = float(orig.loc["row", "cchem"]); mt = float(orig.loc["mtax", "cchem"])
    st = float(orig.loc["stax", "cchem"]); tr = float(orig.loc["trc", "cchem"])
    if FUEL_EXCISE_2023 > st:
        raise ValueError("Fuel excise exceeds the SAM's sales taxes on chemicals and petroleum")
    shm = share(fd["imp"][P].sum(), fd["imp"][C].sum())
    total_make = float(orig.loc["achem", "cchem"])
    make_p = 0.3 * total_make
    for _ in range(200):
        for r in [r for r in orig.index if r.startswith("c") and orig.loc[r, "achem"] and r not in comm_in]:
            t.loc[r, "achem"] = orig.loc[r, "achem"]
        for r in comm_in:
            if r not in ("cpetr", "cchem"):
                t.loc[r, "apetr"] = coef[r] * make_p
                t.loc[r, "achem"] = orig.loc[r, "achem"] - t.loc[r, "apetr"]
        t.loc["cpetr", "apetr"] = coef["cpetr"] * make_p
        t.loc["cchem", "apetr"] = coef["cchem"] * make_p
        rem = orig.loc["cchem", "achem"] - t.loc["cpetr", "apetr"] - t.loc["cchem", "apetr"]
        t.loc["cpetr", "achem"], t.loc["cchem", "achem"] = rem * pc, rem * (1 - pc)
        for f in labs:
            t.loc[f, "apetr"] = lab * make_p * labmix[f]
            t.loc[f, "achem"] = orig.loc[f, "achem"] - t.loc[f, "apetr"]
        t.loc["fcap", "apetr"] = cap * make_p
        t.loc["fcap", "achem"] = orig.loc["fcap", "achem"] - t.loc["fcap", "apetr"]
        U = {k: float(t.loc[k].sum()) for k in ("cpetr", "cchem")}
        absorb = {k: U[k] - float(t.loc[k, "row"]) for k in U}
        sha = absorb["cpetr"] / (absorb["cpetr"] + absorb["cchem"])
        t.loc["row", "cpetr"], t.loc["row", "cchem"] = M * shm, M * (1 - shm)
        t.loc["mtax", "cpetr"], t.loc["mtax", "cchem"] = mt * shm, mt * (1 - shm)
        t.loc["stax", "cpetr"] = FUEL_EXCISE_2023 + (st - FUEL_EXCISE_2023) * sha
        t.loc["stax", "cchem"] = (st - FUEL_EXCISE_2023) * (1 - sha)
        t.loc["trc", "cpetr"], t.loc["trc", "cchem"] = tr * sha, tr * (1 - sha)
        new_p = U["cpetr"] - float(t.loc[["row", "mtax", "stax", "trc"], "cpetr"].sum())
        if abs(new_p - make_p) < 1e-11:
            make_p = new_p
            break
        make_p = new_p
    else:
        raise RuntimeError("Refinery output did not converge")
    make = {"cpetr": make_p, "cchem": total_make - make_p}
    t.loc["apetr", "cpetr"], t.loc["achem", "cchem"] = make["cpetr"], make["cchem"]
    neg = {r: round(float(t.loc[r, "achem"]), 3) for r in t.index if t.loc[r, "achem"] < -1e-9}
    if neg or min(make.values()) <= 0:
        raise ValueError(f"Negative cells in the chemicals column after the split: {neg}; output {make}")
    rep.append(("imports", M, round(shm, 4)))
    rep.append(("domestic use (for margins and non-excise taxes)", absorb["cpetr"] + absorb["cchem"], round(sha, 4)))
    rep.append(("refinery cost structure (PSA 107-108, basic prices; renormalised by)", scale, {r: round(v, 4) for r, v in coef.items() if v > 0.002}))
    rep.append(("refinery labour / capital shares", lab, round(cap, 4)))
    rep.append(("petroleum share of chemicals' purchases from the group", float(orig.loc["cchem", "achem"]), round(pc, 4)))

    # --- checks: balance, and every other account unchanged
    S = SAM(t, labels, f"{paths.SAM_2023.name} with petroleum split (pystdcge 0.3)")
    chk = S.check(tol=1e-6, verbose=False)
    keep = [c for c in orig.index if c not in ("achem", "cchem")]
    d_rows = float(np.abs(t.loc[keep].sum(axis=1) - orig.loc[keep].sum(axis=1)).max())
    d_cells = float(np.abs(t.loc[keep, keep] - orig.loc[keep, keep]).to_numpy().max())
    if not chk["balanced"] or d_rows > 1e-9 or d_cells > 1e-9:
        raise ValueError(f"Split SAM fails checks: balanced={chk['balanced']}, other totals {d_rows:.2e}, cells {d_cells:.2e}")
    write_ifpri_csv(S, OUT)
    psa_out_share = share(T[:, P].sum() + va["COE"][P].sum() + va["GOS"][P].sum() + va["T-S"][P].sum(),
                          T[:, C].sum() + va["COE"][C].sum() + va["GOS"][C].sum() + va["T-S"][C].sum())
    summary = {"output, refined petroleum (₱ bn)": make["cpetr"], "output, other chemicals (₱ bn)": make["cchem"],
               "petroleum share of output, SAM 2023 split": make["cpetr"] / sum(make.values()),
               "petroleum share of output, PSA 2018": psa_out_share,
               "imports, petroleum (₱ bn)": float(t.loc["row", "cpetr"]), "imports, chemicals (₱ bn)": float(t.loc["row", "cchem"]),
               "household purchases, petroleum (₱ bn)": float(t.loc["cpetr", H].sum()),
               "household purchases, chemicals (₱ bn)": float(t.loc["cchem", H].sum()),
               "sales taxes, petroleum (₱ bn)": float(t.loc["stax", "cpetr"]), "max account imbalance": chk["max_row_col_gap"],
               "largest change in any other account's total": d_rows}
    return S, summary, rep


if __name__ == "__main__":
    S, summary, rep = main()
    lines = [f"# SAM petroleum split (added in 0.3), {dt.date.today():%d %b %Y}", "",
             f"File: `{OUT.relative_to(ROOT)}`. Builder: `tools/build_sam_petroleum_split.py` (rules in its docstring).", "",
             "## Summary", "", "| Item | Value |", "|---|---|"]
    lines += [f"| {k} | {v:,.4f} |" if isinstance(v, float) else f"| {k} | {v} |" for k, v in summary.items()]
    lines += ["", "## Cell splits (petroleum share)", "", "| Cell | ₱ bn | Petroleum share |", "|---|---|---|"]
    lines += [f"| {a} | {b:,.2f} | {c} |" for a, b, c in rep]
    lines += ["", f"Fuel excise 2023 used: ₱{FUEL_EXCISE_2023} bn (CPBRD FF2025-42 as quoted; ATTRIBUTED until the PDF is opened)."]
    rp = paths.OUTPUTS / f"sam_petroleum_split_{dt.date.today():%Y%m%d}.md"
    rp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for k, v in summary.items():
        print(f"{k}: {v:,.4f}" if isinstance(v, float) else f"{k}: {v}")
    print("report:", rp)
