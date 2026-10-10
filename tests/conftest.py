"""Shared fixtures. Run all tests from the repository root:  python -m pytest
Slow tests (dynamic model, external benchmarks) are marked; run only the fast ones with  python -m pytest -m "not slow".
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pystdcge import paths  # noqa: E402

SHORT_RUN = dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
# a large mixed shock used by several tests: import price of chemicals and petroleum +30%, remittances -20%,
# real construction investment -20%
SHOCK = {"pwm_scale": {"cchem": 1.3}, "remit_scale": 0.8, "qinv_scale": {"ccons": 0.8}}


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: takes more than a few seconds")


@pytest.fixture(scope="session")
def models():
    """The three closures used throughout: long run (investment-driven), savings-driven, short run (Keynesian)."""
    from pystdcge.cge import CGE
    return {"long run": CGE.from_sam(),
            "savings": CGE.from_sam(closure="savings"),
            "short run": CGE.from_sam(**SHORT_RUN)}


needs_io = pytest.mark.skipif(not paths.IO_2018.exists(), reason="PSA input-output tables not downloaded (data/raw/io/README.md)")
needs_fies = pytest.mark.skipif(not paths.FIES_PUF.exists(), reason="PSA FIES 2023 public-use file not supplied (data/raw/fies/README.md)")
