"""Social Accounting Matrix (SAM) tools for IFPRI Nexus-style SAMs.

A SAM is a square table of flows (here in billions of pesos). Row i, column j holds the
payment FROM account j TO account i. Every account's row total (receipts) must equal its
column total (payments). The IFPRI SAMs for the Philippines use these account codes:

  a*        activities (industries that produce)
  c*        commodities (goods and services, supplied by activities and imports)
  trc       transaction costs (trade and transport margins)
  flab-*    labour by education (n = low, p = medium, s = high); flnd = land; fcap = capital
  ent       enterprises
  hhd-r1..5, hhd-u1..5   rural and urban households by per-capita expenditure quintile
  gov       government;  dtax, ftax, mtax, stax  direct, factor, import and sales taxes;
            atax  activity (production) taxes, in the 2018 SAM instead of ftax
  s-i       savings-investment;  dstk  change in stocks;  row  rest of the world

Usage
-----
>>> from pystdcge.sam import SAM
>>> s = SAM.load()                  # 2023 SAM
>>> s.check()                       # balance and sign report
>>> s.block("c", "hhd")             # household consumption by commodity (DataFrame)
"""
from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import paths


def _to_float(x: str) -> float:
    """IFPRI files write large cells with thousands separators ("4,886"). Strip them;
    otherwise large flows silently become zero or fail to parse."""
    x = (x or "").strip().replace(",", "")
    return float(x) if x else 0.0


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def content_hash(path) -> str:
    """Checksum of an Excel workbook's cell values (all sheets, in order). Some file-sharing services rewrite
    spreadsheet files (they add library metadata), which changes the file bytes but not the data; this hash
    changes only if a value changes. Use it for .xlsx files; use sha256() for CSV and other files."""
    import openpyxl
    h = hashlib.sha256()
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        h.update(ws.title.encode())
        for row in ws.iter_rows(values_only=True):
            h.update(repr(row).encode())
    return h.hexdigest()


def file_checksum(path) -> str:
    return content_hash(path) if str(path).lower().endswith(".xlsx") else sha256(path)


TAX_ACCOUNTS = ("atax", "dtax", "ftax", "mtax", "stax")


def group_of(code: str) -> str:
    """Account group used for block operations. Tax accounts are their own group: 'atax' (the 2018 SAM's
    activity tax) starts with 'a' but is not an activity (0.3: before, it was taken for one, which broke the
    CGE on the 2018 SAM)."""
    if code in TAX_ACCOUNTS:
        return code
    if code.startswith("a"):
        return "a"
    if code.startswith("c"):
        return "c"
    if code.startswith("flab"):
        return "flab"
    if code.startswith("hhd"):
        return "hhd"
    return code


@dataclass
class SAM:
    table: pd.DataFrame                       # square, index = columns = account codes
    labels: dict = field(default_factory=dict)  # code -> long label
    source: str = ""

    # ------------------------------------------------------------------ loading
    @classmethod
    def load(cls, path=None) -> "SAM":
        path = path or paths.SAM_2023
        rows = list(csv.reader(open(path, encoding="utf-8-sig")))
        codes = [r[1].strip() for r in rows[1:]]
        n = codes.index("total")
        codes = codes[:n]
        header = [c.strip() for c in rows[0][2:2 + n]]
        if header != codes:
            raise ValueError("Row and column account codes differ; not a square SAM file.")
        M = np.array([[_to_float(x) for x in r[2:2 + n]] for r in rows[1:1 + n]])
        labels = {r[1].strip(): r[0].strip() for r in rows[1:1 + n]}
        return cls(pd.DataFrame(M, index=codes, columns=codes), labels, str(path))

    # ------------------------------------------------------------------ views
    @property
    def codes(self) -> list:
        return list(self.table.index)

    def accounts(self, group: str) -> list:
        return [c for c in self.codes if group_of(c) == group]

    def block(self, row_group: str, col_group: str) -> pd.DataFrame:
        """Sub-matrix of flows from accounts in col_group to accounts in row_group.
        A group is 'a', 'c', 'flab', 'hhd' or a single account code such as 'gov'."""
        r = self.accounts(row_group) or [row_group]
        c = self.accounts(col_group) or [col_group]
        return self.table.loc[r, c]

    def v(self, row: str, col: str) -> float:
        return float(self.table.loc[row, col])

    # ------------------------------------------------------------------ checks
    def check(self, tol: float = 1e-6, verbose: bool = True) -> dict:
        M = self.table.values
        diff = M.sum(axis=1) - M.sum(axis=0)
        worst = int(np.argmax(np.abs(diff)))
        neg = [(self.codes[i], self.codes[j], M[i, j]) for i, j in zip(*np.where(M < 0))]
        rep = {
            "accounts": len(self.codes),
            "total_flows": float(M.sum()),
            "max_row_col_gap": float(np.abs(diff).max()),
            "worst_account": self.codes[worst],
            "balanced": bool(np.abs(diff).max() <= tol * max(1.0, M.sum() / len(M))),
            "negative_cells": neg,
        }
        if verbose:
            print(f"SAM check: {rep['accounts']} accounts, total flows {rep['total_flows']:,.2f}")
            print(f"  largest row-column gap: {rep['max_row_col_gap']:.3g} ({rep['worst_account']})"
                  f" -> {'BALANCED' if rep['balanced'] else 'NOT BALANCED'}")
            for r, c, x in neg:
                print(f"  negative cell {r} <- {c}: {x:,.2f} (allowed for stock change and savings)")
        return rep

    def block_summary(self) -> pd.DataFrame:
        """Total flow in every non-empty (row group, column group) block."""
        g = [group_of(c) for c in self.codes]
        s = self.table.copy()
        s.index, s.columns = g, g
        out = s.T.groupby(level=0, sort=False).sum().T.groupby(level=0, sort=False).sum()
        return out.loc[:, (out != 0).any()].loc[(out != 0).any(axis=1)]

    # ------------------------------------------------------------------ edits
    def copy(self) -> "SAM":
        return SAM(self.table.copy(), dict(self.labels), self.source)

    def aggregate(self, mapping: dict) -> "SAM":
        """Aggregate accounts: mapping = {old_code: new_code}; unmapped codes keep their name.
        Flows are summed, so balance is preserved exactly."""
        new = [mapping.get(c, c) for c in self.codes]
        order = list(dict.fromkeys(new))
        t = self.table.copy()
        t.index, t.columns = new, new
        t = t.groupby(level=0, sort=False).sum().T.groupby(level=0, sort=False).sum().T
        t = t.loc[order, order]
        labels = {mapping.get(k, k): v for k, v in self.labels.items()}
        return SAM(t, labels, self.source + " (aggregated)")

    def move_home_consumption_to_market(self) -> "SAM":
        """IFPRI SAMs record home consumption as payments from households to activities
        (row a, column hhd). This model treats it as marketed consumption: the value is moved
        to the matching commodity row (row c, column hhd) and added to the activity's sales to
        that commodity (row a, column c). Row and column totals are unchanged."""
        s = self.copy()
        t = s.table
        for a in self.accounts("a"):
            c = "c" + a[1:]
            if c not in t.index:
                raise KeyError(f"No commodity {c} matching activity {a}")
            for h in self.accounts("hhd"):
                x = t.loc[a, h]
                if x:
                    t.loc[a, h] = 0.0
                    t.loc[c, h] += x
                    t.loc[a, c] += x
        return s

    def balance(self, tol: float = 1e-9) -> tuple["SAM", pd.DataFrame]:
        """Make row totals equal column totals with the smallest proportional changes (0.3).

        The IFPRI 2018 SAM is published in whole billions, so accounts are out of balance by up to about 5.
        Weighted least squares: minimise sum (x_ij - a_ij)^2 / |a_ij| subject to every account balancing. The
        solution is x_ij = a_ij + |a_ij| (l_i - l_j) for one multiplier l per account, so empty cells stay empty,
        signs are kept for small gaps, and large cells absorb most of the change. Returns the balanced SAM and a
        table of the changes by account."""
        a = self.table.values.astype(float)
        w = np.abs(a)
        n = len(a)
        gap = a.sum(axis=1) - a.sum(axis=0)                      # receipts - payments
        # balance condition for account k: sum_j x_kj - sum_i x_ik = 0  ->  L l = -gap
        L = np.zeros((n, n))
        rw, cw = w.sum(axis=1), w.sum(axis=0)
        L[np.diag_indices(n)] = rw + cw - 2 * np.diag(w)
        L -= w + w.T
        L[np.diag_indices(n)] += 2 * np.diag(w)
        lam = np.linalg.lstsq(L, -gap, rcond=None)[0]
        x = a + w * (lam[:, None] - lam[None, :])
        x[np.abs(x) < 1e-9] = 0.0                                # cells balanced away entirely (e.g. a ₱1 bn account)
        out = SAM(pd.DataFrame(x, index=self.codes, columns=self.codes), dict(self.labels), self.source + " (balanced)")
        new_gap = np.abs(x.sum(axis=1) - x.sum(axis=0)).max()
        if new_gap > tol * max(1.0, np.abs(a).sum() / n):
            raise ValueError(f"Balancing failed (largest remaining gap {new_gap:.3g})")
        rep = pd.DataFrame({"gap_before": gap, "total_before": a.sum(axis=1), "total_after": x.sum(axis=1),
                            "largest_cell_change": np.abs(x - a).max(axis=1)}, index=self.codes)
        return out, rep

    def drop_empty(self) -> tuple["SAM", list]:
        """Remove accounts with no receipts and no payments (0.3). In the balanced 2018 SAM, 'other cereals'
        (aocer/cocer: ₱1 bn of sales and no recorded costs, a rounding artefact) balances to zero."""
        t = self.table
        empty = [c for c in self.codes if (t.loc[c].abs().sum() == 0) and (t[c].abs().sum() == 0)]
        keep = [c for c in self.codes if c not in empty]
        return SAM(t.loc[keep, keep].copy(), {k: v for k, v in self.labels.items() if k in keep},
                   self.source + (f" (empty accounts dropped: {', '.join(empty)})" if empty else "")), empty

    @classmethod
    def load_for_model(cls, path=None, rounded=None) -> "SAM":
        """Load a SAM for the CGE (0.3). A SAM that already balances (the 2023 SAM, to 4e-8) is returned
        unchanged, so results on it are exactly as before. A SAM published in rounded figures (the 2018 SAM) is
        balanced with `balance()` and emptied accounts are dropped; the CGE needs exact balance to calibrate.
        0.3.3 (rigging audit finding 2): only a SAM declared as rounded is balanced (rounded=True; by default the 2018
        SAM, paths.SAM_2018). Any other SAM that does not balance is refused with the size of the imbalance, so an
        edited or damaged data file cannot be balanced away without anyone noticing."""
        s = cls.load(path)
        rep = s.check(tol=1e-6, verbose=False)
        if rep["balanced"]:
            return s
        if rounded is None:
            rounded = path is not None and Path(path).resolve() == Path(paths.SAM_2018).resolve()
        if not rounded:
            raise ValueError(f"The SAM {Path(path or paths.SAM_2023).name} does not balance: largest row-column gap "
                             f"{rep['max_row_col_gap']:.4g} (account {rep['worst_account']}). If it is published in "
                             "rounded figures, load it with SAM.load_for_model(path, rounded=True); otherwise check the file.")
        b, _ = s.balance()
        return b.drop_empty()[0]

    def to_csv(self, path):
        self.table.to_csv(path)
