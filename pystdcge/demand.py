"""Household demand parameters for the LES option of the CGE (added in 0.3).

    from pystdcge.demand import les_briones2023
    m = CGE.from_sam(les=les_briones2023())          # Linear Expenditure System instead of Cobb-Douglas

Source: Briones et al. (2023), PIDS DP 2023-23, Table 5 (the LES elasticities of AMPLE-CGE, a Philippine CGE),
with Table 4 for other cereals: data/raw/elasticities/Briones_et_al_2023_Table5_LES_elasticities.csv.
  Income (expenditure) elasticities: Briones's group values mapped to the SAM's 42 commodities. Processed foods and
    beverages & tobacco combine several Briones groups; they are weighted by PSA's CPI weights (2018-based, all income
    households; data/raw/cpi): processed foods = rice & corn (rice, corn), other food (flour, bread and other cereals;
    ready-made and n.e.c. food), meat, processed fish (dried, salted, preparations; fresh fish is the SAM's fisheries),
    milk & dairy (excluding eggs, which are poultry and eggs), oils & fats, sugar & confectionery, processed fruit and
    vegetables; beverages & tobacco = non-alcoholic beverages, alcoholic beverages, tobacco.
  Engel aggregation: for each household group the elasticities are scaled so that budget-share-weighted elasticities
    sum to one (IFPRI standard model practice; Lofgren et al. 2002). On the 2023 SAM the unscaled sums are 0.96-1.12.
  Frisch parameter (one per household group): chosen so the LES own-price elasticities come as close as possible to
    Briones's own-price elasticities (budget-share-weighted least squares). An LES has a single price parameter per
    household, so it cannot reproduce every own-price elasticity; fit="all" uses all commodities (central),
    fit="food" only the food commodities (Briones's econometric QAIDS estimates; the non-food -0.90 are imputations).
LES own-price elasticity (Marshallian): eps_i = -1 + (1 - b_i) * (1 + e_i / frisch), with b_i = e_i * w_i the marginal
budget share; subsistence quantity gamma_i = q_i - b_i * S, supernumerary spending S = -spending / frisch.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

from . import paths

TABLE = paths.DATA_RAW / "elasticities" / "Briones_et_al_2023_Table5_LES_elasticities.csv"
CPI = paths.DATA_RAW / "cpi" / "PSA_CPI_weights_2018base_AllHouseholds_Philippines.csv"

# SAM commodity -> Briones group (one group), or a dict {group: [CPI item codes, with sign]} for composites
COMMODITY_GROUP = {
    "cmaiz": "Maize", "crice": "Palay", "cocer": "Other cereals", "cpuls": "Other crops", "coils": "Coconut",
    "croot": "Cassava", "cvege": "Leafy & stem vegetables", "csugr": "Sugarcane", "ctoba": "Other crops",
    "ccott": "Other crops", "cfrui": "Banana", "ccoff": "Coffee", "cocrp": "Other crops", "ccatt": "Cattle",
    "cpoul": "Chicken", "coliv": "Hog", "cfore": "Other agri-related activity", "cfish": "Fishing", "cmine": "Mining",
    "cfood": {"Rice & corn": ["01.1.1.12", "01.1.1.16"], "Other food": ["01.1.1.20", "01.1.9"],
              "Meat fresh and processed": ["01.1.2"], "Processed fish": ["01.1.3.2", "01.1.3.3", "01.1.3.6"],
              "Milk & dairy": ["01.1.4", "-01.1.4.8"], "Fats & oil": ["01.1.5"], "Sugar & sugar products": ["01.1.8"],
              "Processed fruit & vegetables": ["01.1.6.7", "01.1.6.9", "01.1.7.9"]},
    "cbeve": {"Beverages": ["01.2"], "Alcoholic beverages": ["02.1"], "Tobacco": ["02.3"]},
    "ctext": "Textiles, apparel, footwear", "cwood": "Wood, paper, printing", "cchem": "Chemicals & plastics",
    "cpetr": "Chemicals & plastics",   # split SAM: AMPLE-CGE maps refined petroleum (PSA 107) to chemicals & plastics
    "cnmet": "Mineral & metal products", "cmetl": "Mineral & metal products", "cmach": "Machinery & vehicles",
    "coman": "Other manufacturing", "celec": "Electricity, gas & water", "cwatr": "Electricity, gas & water",
    "ccons": "Construction", "ctrad": "Trade", "ctran": "Transport & logistics", "chotl": "Food & accommodation",
    "ccomm": "Information & communications", "cfsrv": "Finance & real estate", "creal": "Finance & real estate",
    "cbsrv": "Professional & technical", "cpadm": "Public sector", "ceduc": "Public sector", "cheal": "Public sector",
    "cosrv": "Other services"}
FOOD = ("cmaiz", "crice", "cocer", "cpuls", "coils", "croot", "cvege", "csugr", "cfrui", "ccoff", "cocrp", "ccatt",
        "cpoul", "coliv", "cfish", "cfood", "cbeve")


def _cpi_weights() -> dict:
    t = pd.read_csv(CPI, comment="#")
    code = t["Commodity Description"].str.split(" - ").str[0].str.strip()
    return dict(zip(code, t["Weights"].astype(float)))


def commodity_elasticities(codes) -> pd.DataFrame:
    """Income and own-price elasticity for each SAM commodity code (before Engel aggregation)."""
    b = pd.read_csv(TABLE, comment="#").set_index("group")
    w = _cpi_weights()
    rows = {}
    for c in codes:
        g = COMMODITY_GROUP[c]
        if isinstance(g, str):
            rows[c] = (b.loc[g, "income_elasticity"], b.loc[g, "own_price_elasticity"], g)
        else:
            wts = {k: sum((-1 if s.startswith("-") else 1) * w[s.lstrip("-")] for s in items) for k, items in g.items()}
            tot = sum(wts.values())
            rows[c] = (sum(v * b.loc[k, "income_elasticity"] for k, v in wts.items()) / tot,
                       sum(v * b.loc[k, "own_price_elasticity"] for k, v in wts.items()) / tot,
                       "; ".join(f"{k} {v / tot:.1%}" for k, v in wts.items()))
    return pd.DataFrame(rows, index=["income", "own_price", "source_group"]).T


def fit_frisch(w, eta, eps, mask=None) -> float:
    """Frisch parameter whose LES own-price elasticities best match `eps` (budget-share-weighted least squares).
    w: budget shares; eta: income elasticities already satisfying Engel aggregation (w @ eta = 1)."""
    w, eta, eps = map(lambda a: np.asarray(a, float), (w, eta, eps))
    k = np.ones(len(w), bool) if mask is None else np.asarray(mask, bool)
    b = eta * w
    loss = lambda phi: float(w[k] @ ((-1 + (1 - b[k]) * (1 + eta[k] / phi)) - eps[k]) ** 2)
    return float(minimize_scalar(loss, bounds=(-20.0, -0.2), method="bounded", options={"xatol": 1e-10}).x)


USDA = paths.DATA_RAW / "elasticities" / "USDA_ERS_2005ICP_Philippines_elasticities.csv"
# SAM commodity -> USDA ERS category: "f:<food subgroup>" or "b:<broad group>", or {category: [CPI codes]} for composites
COMMODITY_USDA = {
    "cmaiz": "f:cereals", "crice": "f:cereals", "cocer": "f:cereals", "cpuls": "f:fruits", "coils": "f:oils",
    "croot": "f:fruits", "cvege": "f:fruits", "csugr": "f:food other", "ctoba": "f:bev", "ccott": "b:clothing",
    "cfrui": "f:fruits", "ccoff": "f:bev", "cocrp": "f:food other", "ccatt": "f:meats", "cpoul": "f:meats",
    "coliv": "f:meats", "cfore": "b:other", "cfish": "f:fish", "cmine": "b:other",
    "cfood": {"f:cereals": ["01.1.1.12", "01.1.1.16", "01.1.1.20"], "f:meats": ["01.1.2"],
              "f:fish": ["01.1.3.2", "01.1.3.3", "01.1.3.6"], "f:dairy": ["01.1.4", "-01.1.4.8"], "f:oils": ["01.1.5"],
              "f:food other": ["01.1.8", "01.1.9"], "f:fruits": ["01.1.6.7", "01.1.6.9", "01.1.7.9"]},
    "cbeve": "f:bev", "ctext": "b:clothing", "cwood": "b:other",
    "cchem": {"b:housing": ["04.5.2", "04.5.3", "04.5.4"], "b:transport": ["07.2.2"], "b:medical": ["06.1"],
              "b:other": ["13.1"]},
    "cpetr": {"b:housing": ["04.5.2", "04.5.3", "04.5.4"], "b:transport": ["07.2.2"]},   # split SAM
    "cnmet": "b:house", "cmetl": "b:house", "cmach": {"b:house": ["05.3"], "b:transport": ["07.1"]},
    "coman": "b:house", "celec": "b:housing", "cwatr": "b:housing", "ccons": "b:housing", "ctrad": "b:other",
    "ctran": "b:transport", "chotl": "b:other", "ccomm": "b:transport", "cfsrv": "b:other", "creal": "b:housing",
    "cbsrv": "b:other", "cpadm": "b:other", "ceduc": "b:education", "cheal": "b:medical", "cosrv": "b:recreation"}


def _usda_tables():
    t = pd.read_csv(USDA, comment="#")

    def k(cat, food):
        c = cat.strip().lower()
        if food:
            for p in ("cereals", "meats", "fish", "dairy", "oils", "fruits", "food other", "bev"):
                if c.startswith(p):
                    return "f:" + p
        else:
            for p, kk in (("food", "food"), ("clothing", "clothing"), ("housing", "housing"), ("house", "house"),
                          ("medical", "medical"), ("transport", "transport"), ("recreation", "recreation"),
                          ("education", "education"), ("other", "other")):
                if c.startswith(p):
                    return "b:" + kk
        raise KeyError(cat)
    out = {}
    for tab, g in t.groupby("table"):
        food = tab.endswith("food_sub")
        out[tab] = {k(c, food): float(str(v).rstrip("a")) for c, v in zip(g["category"], g["philippines"])}
    return out


def usda_frisch() -> float:
    """Frisch parameter implied by USDA ERS for the Philippines: in their additive model the own-price elasticity at
    constant marginal utility of income equals income elasticity / Frisch, the same ratio for every broad group."""
    u = _usda_tables()
    r = [u["income_broad"][c] / u["own_price_frisch_broad"][c] for c in u["income_broad"]]
    return float(np.mean(r))


def les_usda2011(split: bool = False) -> dict:
    """LES parameters from USDA ERS (Muhammad et al. 2011; 2005 ICP; Philippines row): income elasticities for food
    subgroups and broad non-food groups, mapped to the SAM (composites weighted by PSA CPI weights); one Frisch for all
    households, implied by the same source (usda_frisch(), about -1.36). Benchmark for les_briones2023()."""
    u, w = _usda_tables(), _cpi_weights()
    val = lambda key: u["income_food_sub"][key] if key.startswith("f:") else u["income_broad"][key]
    eta = {}
    mapping = dict(COMMODITY_USDA)
    if split:                       # petroleum-split SAM: fuels are cpetr, so cchem = medicines and personal care
        mapping["cchem"] = {"b:medical": ["06.1"], "b:other": ["13.1"]}
    for c, g in mapping.items():
        if isinstance(g, str):
            eta[c] = val(g)
        else:
            wts = {k: sum((-1 if s.startswith("-") else 1) * w[s.lstrip("-")] for s in items) for k, items in g.items()}
            eta[c] = sum(v * val(k) for k, v in wts.items()) / sum(wts.values())
    return {"eta": eta, "frisch": usda_frisch()}


def les_briones2023(fit: str = "all") -> dict:
    """LES parameters for CGE(les=...): {'eta': {commodity: income elasticity}, 'own_price': {...}, 'fit': fit}.
    The Engel scaling and the Frisch fit are done inside the CGE, which knows each household's budget shares."""
    if fit not in ("all", "food"):
        raise ValueError("fit must be 'all' or 'food'")
    e = commodity_elasticities(list(COMMODITY_GROUP))
    return {"eta": e["income"].astype(float).to_dict(), "own_price": e["own_price"].astype(float).to_dict(), "fit": fit}


GTAP10 = paths.DATA_RAW / "elasticities" / "GTAP10_2014_Philippines_household_demand.csv"


def les_gtap10() -> dict:
    """LES benchmark from GTAP 10 (2014, Philippines; Aguiar et al. 2019): income and uncompensated own-price elasticities of
    GTAP's CDE demand system (tools/gtap10_philippines.py), aggregated to SAM commodities with GTAP's Philippine budget
    shares; the Frisch parameter is fitted per household group to GTAP's own-price elasticities (as for Briones)."""
    t = pd.read_csv(GTAP10, comment="#")
    w = t["budget_share"]
    eta, eps = {}, {}
    for c, g in t.groupby("sam"):
        ww = w[g.index]
        if ww.sum() > 0:
            eta[c] = float((ww * g["income_elasticity"]).sum() / ww.sum())
            eps[c] = float((ww * g["own_price_uncompensated"]).sum() / ww.sum())
        else:
            eta[c] = float(g["income_elasticity"].mean())
            eps[c] = float(g["own_price_uncompensated"].mean())
    eta.setdefault("cchem", eta.get("cpetr", 1.0))           # combined SAM: chemicals and petroleum
    return {"eta": eta, "own_price": eps, "fit": "all"}
