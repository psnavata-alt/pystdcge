import sys, os, json, importlib.util, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore"); sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
def load_pkg(name, folder):
    spec = importlib.util.spec_from_file_location(name, os.path.join(folder, "__init__.py"), submodule_search_locations=[folder])
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return importlib.import_module(name + ".cge"), importlib.import_module(name + ".sam")
# Engine: the options are in pystdcge's own engine (since 0.3.1); the comparison runs on the package of the folder
# this file sits in (test V5).
if os.environ.get("HOSOE_ENGINE") == "copy":
    cge, sam = load_pkg("pystdcge_copy", os.path.join(HERE, "engine_copy", "pystdcge"))
else:
    cge, sam = load_pkg("pystdcge_dev", os.path.join(HERE, "..", "..", "pystdcge"))

# Hosoe et al. stdcge SAM (stdcge.gms lines 22-33) in pystdcge account names. Column pays row.
acc = ["abrd","amlk","cbrd","cmlk","flab-s","fcap","ent","hhd","gov","s-i","dstk","row","atax","mtax","stax","dtax","trc"]
T = pd.DataFrame(0.0, index=acc, columns=acc)
def f(r, c, x): T.loc[r, c] = x
f("cbrd","abrd",21); f("cmlk","abrd",17); f("fcap","abrd",20); f("flab-s","abrd",15); f("atax","abrd",5)
f("cbrd","amlk",8);  f("cmlk","amlk",9);  f("fcap","amlk",30); f("flab-s","amlk",25); f("atax","amlk",4)
f("abrd","cbrd",78); f("row","cbrd",13); f("mtax","cbrd",1)          # make (gross output incl. tax), imports, tariff
f("amlk","cmlk",76); f("row","cmlk",11); f("mtax","cmlk",2)
f("hhd","flab-s",40); f("ent","fcap",50); f("hhd","ent",50)           # capital income passes through 'ent' unchanged
f("cbrd","hhd",20); f("cmlk","hhd",30); f("dtax","hhd",23); f("s-i","hhd",17)
f("gov","dtax",23); f("gov","atax",9); f("gov","mtax",3)
f("cbrd","gov",19); f("cmlk","gov",14); f("s-i","gov",2)
f("cbrd","s-i",16); f("cmlk","s-i",15)
f("cbrd","row",8); f("cmlk","row",4); f("s-i","row",12)
S = sam.SAM(T)
gap = (T.sum(axis=1) - T.sum(axis=0)).abs().max()

ref = json.load(open(os.path.join(HERE, "pycge_results.json")))
B, Sm = ref["base"], ref["sim"]
alpha = np.array([20, 30]) / 50
UU = lambda xp: float(np.prod(np.asarray(xp) ** alpha))
k = lambda d, n, i=None: d[f"{n}[{i}]"] if i is not None else d[n]
I = ["BRD", "MLK"]
def pyc(d):
    pf = k(d, "pf", "LAB")
    out = {}
    for n in ["Z","Xp","Xg","Xv","E","M","Q","D","Y"]:
        for i in I: out[f"{n} {i}"] = k(d, n, i)
    for h in ["CAP","LAB"]:
        for i in I: out[f"F {h},{i}"] = k(d, "F", (h, i)) if f"F[('{h}', '{i}')]" not in d else d[f"F[('{h}', '{i}')]"]
    for n in ["pq","pd","pe","pz","py"]:
        for i in I: out[f"{n} {i} / pf LAB"] = k(d, n, i) / pf
    out["pf CAP / pf LAB"] = k(d, "pf", "CAP") / pf
    out["exchange rate / pf LAB"] = k(d, "epsilon") / pf
    for n in ["Td","Sp","Sg"]: out[f"{n} / pf LAB"] = k(d, n) / pf
    for i in I: out[f"Tz {i} / pf LAB"] = k(d, "Tz", i) / pf; out[f"Tm {i} / pf LAB"] = k(d, "Tm", i) / pf
    out["utility"] = UU([k(d, "Xp", i) for i in I])
    return out

def ours(m, s):
    v = s.v; wl = v["WF"][m.F.index("flab-s")]; ta = m.ta
    out = {}
    nm = {"Z": v["QA"] * (1 - ta) * 0 + v["QA"] * np.array([73, 76 - 4 - 0]) / np.array([78, 76]) * 0}  # placeholder
    QAnet = v["QA"] / m.QA0 * np.array([73.0, 72.0])                        # net output Z (Hosoe Z0 = 73, 72)
    vals = {"Z": QAnet, "Xp": v["QH"][:, 0], "Xg": v["QG"], "Xv": v["QINV"], "E": v["QE"], "M": v["QM"], "Q": v["QQ"],
            "D": v["QD"], "Y": v["QVA"]}
    for n, arr in vals.items():
        for j, i in enumerate(I): out[f"{n} {i}"] = float(arr[j])
    for h, fc in [("CAP", "fcap"), ("LAB", "flab-s")]:
        for j, i in enumerate(I): out[f"F {h},{i}"] = float(v["QF"][m.F.index(fc), j])
    pz = v["PA"] * (1 - ta)                                                  # Hosoe pz = net-of-tax supply price
    pr = {"pq": v["PQ"], "pd": v["PDS"], "pe": v["PE"], "pz": pz, "py": v["PVA"]}
    for n, arr in pr.items():
        for j, i in enumerate(I): out[f"{n} {i} / pf LAB"] = float(arr[j] / wl)
    out["pf CAP / pf LAB"] = float(v["WF"][m.F.index("fcap")] / wl)
    out["exchange rate / pf LAB"] = float(v["EXR"] / wl)
    out["Td / pf LAB"] = float((m.tins * v["YH"]).sum() / wl)
    out["Sp / pf LAB"] = float(v["HSAV"].sum() / wl); out["Sg / pf LAB"] = float(v["GSAV"] / wl)
    for j, i in enumerate(I): out[f"Tz {i} / pf LAB"] = float(v["ATAX"][j] / wl); out[f"Tm {i} / pf LAB"] = float(v["MTAX"][j] / wl)
    out["utility"] = UU(v["QH"][:, 0])
    return out

rows = {}
for label, sv in [("CD exact", 1.0), ("sigma 0.9999", 0.9999), ("sigma 1.0001", 1.0001)]:
    m = cge.CGE(S, elasticities={"sigma_va": sv, "sigma_q": 2.0, "omega_t": 2.0}, closure="savings", gov="cd", inv="value_shares")
    b = m.solve(); s = m.solve({"tm_scale": 0.0})
    samgap = float((m.rebuild_sam(b) - m.sam.table).abs().values.max())
    rows[label] = (m, b, s, samgap)
m, b, s, samgap = rows["CD exact"]
P0, P1 = pyc(B), pyc(Sm); G0, G1 = ours(m, b), ours(m, s)
tab = pd.DataFrame({"pycge base": P0, "pystdcge base": G0, "pycge after": P1, "pystdcge after": G1})
tab["pycge % change"] = (tab["pycge after"] / tab["pycge base"] - 1) * 100
tab["pystdcge % change"] = (tab["pystdcge after"] / tab["pystdcge base"] - 1) * 100
tab["level gap after"] = (tab["pystdcge after"] - tab["pycge after"]).abs()
tab["level gap base"] = (tab["pystdcge base"] - tab["pycge base"]).abs()
ev_p = (P1["utility"] - P0["utility"]) / np.prod(alpha ** alpha); ev_s = (G1["utility"] - G0["utility"]) / np.prod(alpha ** alpha)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
if __name__ == "__main__":
    tab.to_csv(os.path.join(HERE, "hosoe_comparison.csv"))
print(f"SAM rows = columns: max gap {gap:.1e}; pystdcge reproduces the SAM at the base: {samgap:.1e}; solves ok: base {b.ok}, sim {s.ok}; Walras {s['WALRAS']:.1e}")
print(tab[["pycge % change", "pystdcge % change", "level gap after"]].round(6).to_string())
print(f"\nLargest level gap, base: {tab['level gap base'].max():.2e}; after the shock: {tab['level gap after'].max():.2e}")
print(f"Equivalent variation: pycge {ev_p:.6f}, pystdcge {ev_s:.6f}")
for lab in ("sigma 0.9999", "sigma 1.0001"):
    mm, bb, ss, _ = rows[lab]; Gx0, Gx1 = ours(mm, bb), ours(mm, ss)
    d = max(abs(Gx1[key] - P1[key]) for key in P1)
    print(f"{lab}: largest level gap vs pycge after the shock {d:.2e} (should be small and bracket the exact CD result)")

print("\n--- summary excluding pz (unit normalisation: Hosoe per unit of net output, pystdcge per unit of gross output) ---")
keys = [k_ for k_ in P1 if not k_.startswith("pz")]
pct_gap = max(abs(tab.loc[k_, "pycge % change"] - tab.loc[k_, "pystdcge % change"]) for k_ in keys if k_ in tab.index and np.isfinite(tab.loc[k_, "pycge % change"]))
print(f"CD exact: largest level gap base {max(abs(G0[k_]-P0[k_]) for k_ in keys):.2e}, after {max(abs(G1[k_]-P1[k_]) for k_ in keys):.2e}; largest % change gap {pct_gap:.2e} pp")
print(f"pz: % change gap {max(abs(tab.loc[k_, 'pycge % change'] - tab.loc[k_, 'pystdcge % change']) for k_ in P1 if k_.startswith('pz')):.2e} pp; base levels pycge {P0['pz BRD / pf LAB']:.4f} vs pystdcge {G0['pz BRD / pf LAB']:.4f} (73/78 = {73/78:.4f})")
for lab in ("sigma 0.9999", "sigma 1.0001"):
    mm, bb, ss, _ = rows[lab]; Gx1 = ours(mm, ss)
    print(f"{lab}: largest level gap vs pycge after the shock {max(abs(Gx1[k_]-P1[k_]) for k_ in keys):.2e}")
