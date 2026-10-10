"""Convert PSA's 2018 input-output transactions tables (Excel, as downloaded from PSA) to the CSV layout pystdcge reads.

PSA's tables are not redistributed with pystdcge (see README.md in this folder). Download them from PSA, save them in
this folder, then run from the repository root:

    python data/raw/io/psa_io_to_csv.py

Values are copied cell by cell; nothing is computed. Files read (names as PSA publishes them):
    80-Industry20Table202018.xlsx   Table B.1, 80-industry transactions table   -> 80-Industry20Table202018.csv
    16-Industry20Table202018.xlsx   Table A.1, 16-industry transactions table   -> 16-Industry_Table_2018.csv
"""
import csv
import hashlib
import sys
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
TABLES = {"80-Industry20Table202018.xlsx": "80-Industry20Table202018.csv",
          "16-Industry20Table202018.xlsx": "16-Industry_Table_2018.csv"}


def convert(src: Path, out: Path):
    ws = openpyxl.load_workbook(src, data_only=True, read_only=True).worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    width = max(len(r) for r in rows)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(["" if x is None else (repr(x) if isinstance(x, float) else str(x)) for x in r + [None] * (width - len(r))])
    print(f"wrote {out.name}: {len(rows)} rows x {width} columns from {src.name} (SHA-256 {hashlib.sha256(src.read_bytes()).hexdigest()})")


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    found = False
    for src, out in TABLES.items():
        if (folder / src).exists():
            convert(folder / src, folder / out)
            found = True
    if not found:
        sys.exit(f"No PSA table found in {folder}: download them first (README.md).")
