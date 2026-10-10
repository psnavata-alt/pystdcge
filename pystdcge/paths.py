"""Folder locations, resolved from this file so scripts work from any working directory.

Set the environment variable PYSTDCGE_DATA to use a data folder elsewhere (it must have the same layout as data/),
and PYSTDCGE_OUTPUTS to write results somewhere other than outputs/.
"""
import os as _os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(_os.environ.get("PYSTDCGE_DATA", str(ROOT / "data")))
DATA_RAW = DATA / "raw"
DATA_PROCESSED = DATA / "processed"
OUTPUTS = Path(_os.environ.get("PYSTDCGE_OUTPUTS", str(ROOT / "outputs")))

# IFPRI Social Accounting Matrices for the Philippines (CC BY 4.0; data/DATA_SOURCES.md)
SAM_2023 = DATA_RAW / "sam" / "002_IFPRI_SAM_PHL_2023_SAM.csv"
SAM_2018 = DATA_RAW / "sam" / "002_IFPRI_SAM_PHL_2018_SAM.csv"
POP_2023 = DATA_RAW / "sam" / "003_IFPRI_SAM_PHL_2023_POP.csv"
# 2023 SAM with refined petroleum split from chemicals (built by tools/build_sam_petroleum_split.py)
SAM_2023_PETR = DATA_PROCESSED / "IFPRI_SAM_PHL_2023_SAM_petroleum_split.csv"

# PSA 2018 input-output tables: NOT redistributed; download them as data/raw/io/README.md explains
IO_2018 = DATA_RAW / "io" / "80-Industry20Table202018.csv"
IO_2018_16 = DATA_RAW / "io" / "16-Industry_Table_2018.csv"

# PSA Family Income and Expenditure Survey 2023 (public-use file): NOT redistributed (PSA terms); each user downloads
# it from the PSA Data Archive and saves it as data/raw/fies/README.md explains. Without it, microsim is unavailable.
FIES_PUF = DATA_RAW / "fies" / "FIES-LFS PUF 2023 Household Sum.csv"
FIES_POVLINES = DATA_RAW / "fies" / "FIES2023_official_poverty_lines_extract.csv"


def output_dir(*sub: str) -> Path:
    """Folder to save results in (created if needed): outputs/<sub>."""
    d = OUTPUTS.joinpath(*sub)
    d.mkdir(parents=True, exist_ok=True)
    return d


def output_dirs(*sub: str) -> list[Path]:
    """Folders to read saved results from."""
    d = OUTPUTS.joinpath(*sub)
    return [d] if d.is_dir() else []


def can_write(folder: Path) -> bool:
    """True if files can be created in `folder`."""
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / f"~pystdcge_write_test_{_os.getpid()}.tmp"
        probe.write_text("x", encoding="ascii")
        probe.unlink()
        return True
    except OSError:
        return False
