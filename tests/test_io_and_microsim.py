"""Input-output identities (I3, I4) and the poverty microsimulation baseline (P1). These need data that may not be
redistributed (PSA input-output tables; PSA FIES public-use file); the tests are skipped until you download them."""
import numpy as np

from conftest import needs_fies, needs_io


@needs_io
def test_io_price_identity():
    """I3: raising every primary-input cost by 10% raises every industry's price by exactly 10%."""
    from pystdcge.iomodel import IOTable
    io = IOTable()
    assert np.abs(io.price_from_primary_inputs(0.10).values - 0.10).max() < 1e-7


@needs_io
def test_io_value_added_identity():
    """I4: with the total inverse, one peso of final demand returns one peso of value added; with the domestic
    inverse, value added plus imported inputs return one peso."""
    from pystdcge.iomodel import IOTable
    io = IOTable()
    m = ((1 - io.dom_share)[:, None] * io.A).sum(axis=0)
    assert np.abs(io.v @ io.L - 1).max() < 1e-7
    assert np.abs(io.v @ io.Ld + m @ io.Ld - 1).max() < 1e-7
    assert ((io.v > 0) & (io.v < 1)).all()


def test_oil_import_shares_match_psa():
    """The stored PSA 2018 import shares used for oil shocks equal the ones computed from PSA's table (when present)."""
    import pytest
    from pystdcge import oil
    if not oil.PSA_240.exists():
        pytest.skip("PSA 240-industry table not downloaded (data/raw/io/README.md)")
    got = oil._imports_240() is not None and {k: v for k, v in oil.import_shares().items()}
    assert all(abs(got[k] - v) < 1e-12 for k, v in oil.IMPORT_SHARES_PSA2018.items())


@needs_fies
def test_microsim_baseline():
    """P1: the FIES 2023 baseline reproduces PSA's official count of poor people (17.54 million) within 0.1%."""
    from pystdcge.microsim import Microsim, OFFICIAL_POOR_2023
    b = Microsim().baseline()
    assert abs(b["poor"] / OFFICIAL_POOR_2023 - 1) < 0.001
