"""Data integrity (checksums), SAM balance and SAM multipliers."""
import hashlib

import numpy as np
import pandas as pd

from conftest import ROOT
from pystdcge import paths
from pystdcge.sam import SAM


def test_data_checksums():
    """D1: every CSV in data/ matches data/SHA256SUMS.txt."""
    rows = [l.split("  ", 1) for l in (ROOT / "data" / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert rows
    bad = [p for h, p in rows if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
    assert not bad, f"checksum mismatch: {bad}"


def test_sam_balance():
    """D2: the 2023 SAM balances exactly; the 2018 SAM, published in whole billions, to within rounding."""
    r23 = SAM.load(paths.SAM_2023).check(verbose=False)
    r18 = SAM.load(paths.SAM_2018).check(verbose=False)
    assert r23["balanced"]
    assert r18["max_row_col_gap"] < 6


def _population_shares(year, path):
    pop = pd.read_csv(path.parent / f"003_IFPRI_SAM_PHL_{year}_POP.csv", encoding="utf-8-sig", skiprows=1 if year == 2023 else 0)
    pop.columns = ["name", "code", "num", "shr"][: len(pop.columns)]
    ps = {}
    for _, r in pop.iterrows():
        c = str(r["code"]).lower()
        for a, full in (("r", "rur"), ("u", "urb")):
            for q in range(1, 6):
                if c in (f"h_{full}{q}", f"hhd-{a}{q}"):
                    ps[f"hhd-{a}{q}"] = float(str(r["num"]).replace(",", ""))
    return ps


def test_sam_multiplier_regression():
    """M1: household-income multipliers of a transfer to poor households (regression values).
    Transfer split 50/30/20 to rural quintile 1, rural quintile 2 and urban quintile 1, and to the bottom 40% by
    population; IFPRI 2018 and 2023 SAMs."""
    from pystdcge.multiplier import SAMMultiplier
    vals = {}
    for yr, p in ((2018, paths.SAM_2018), (2023, paths.SAM_2023)):
        ps = _population_shares(yr, p)
        q12 = ["hhd-r1", "hhd-u1", "hhd-r2", "hhd-u2"]
        mult = SAMMultiplier(SAM.load(p))
        vals[yr] = (mult.household_income_multiplier({"hhd-r1": .5, "hhd-r2": .3, "hhd-u1": .2}),
                    mult.household_income_multiplier({h: ps[h] / sum(ps[k] for k in q12) for h in q12}))
    expected = {2018: (2.170, 2.162), 2023: (2.200, 2.197)}
    for y in expected:
        assert np.allclose(vals[y], expected[y], atol=5e-4), (y, vals[y])
