"""External benchmarks (V2-V5): the same model and data solved by other people's code.

V2-V4 compare with IFPRI's own GAMS model (Lofgren, Harris and Robinson 2002; Thurlow's extended version), whose
results on the same condensed Philippine SAM are saved in validation/ifpri*/gams_ph/ifpri_results.csv (GAMS is not
needed to run these tests; validation/ifpri/README.md explains how to rerun GAMS). V5 compares with pycge, a
human-written Python port of Hosoe, Gasawa and Hashimoto's standard CGE model (results saved in validation/hosoe/).
"""
import contextlib
import io
import runpy
import sys

import numpy as np
import pytest

from conftest import ROOT

pytestmark = pytest.mark.slow


def _run(script, argv=None, run_name="__main__"):
    old = sys.argv
    try:
        sys.argv = [str(script)] + (argv or [])
        with contextlib.redirect_stdout(io.StringIO()):
            return runpy.run_path(str(script), run_name=run_name)
    finally:
        sys.argv = old


def _summary(r):
    core = r[(r.group == "MACRO") & r["item"].isin(["RGDP", "RCONS"])]
    return float(core.diff_pp.abs().max()), float((r.diff_pp.abs() < 0.1).mean()), float(r.diff_pp.abs().max())


def test_ifpri_default_margins():
    """V2: real GDP and consumption within 0.01 pp of IFPRI's model (4 shocks x 2 closures); 95% of 232 results within
    0.1 pp; none beyond 0.6 pp (the remaining gap is the treatment of trade margins, closed by V3)."""
    core, share, largest = _summary(_run(ROOT / "validation" / "ifpri" / "compare.py")["res"])
    assert core < 0.01 and share >= 0.95 and largest < 0.6


def test_ifpri_split_margins():
    """V3: with IFPRI-style trade margins the model reproduces its SAM and IFPRI's results within 0.001 pp for GDP and
    consumption; 99% of results within 0.1 pp; none beyond 0.15 pp (measurement conventions, validation/ifpri)."""
    from pystdcge.cge import CGE
    m = CGE.from_sam(margins="split")
    b = m.solve()
    S = m.rebuild_sam(b)
    assert (S - m.sam.table.loc[S.index, S.columns]).abs().values.max() < 1e-6
    assert np.abs(m.solve({"cpi": 2.0})["QA"] / m.QA0 - 1).max() < 1e-7
    core, share, largest = _summary(_run(ROOT / "validation" / "ifpri" / "compare.py", ["split"])["res"])
    assert core < 0.001 and share >= 0.99 and largest < 0.15


def test_ifpri_home_consumption():
    """V4: home consumption as own produce (home='separate'): reproduces the published SAM with its home cells and
    IFPRI's model with home consumption kept."""
    from pystdcge.cge import CGE
    m = CGE.from_sam(home="separate")
    b = m.solve()
    S = m.rebuild_sam(b)
    assert (S - m.sam0.table.loc[S.index, S.columns]).abs().values.max() < 1e-6
    assert np.abs(m.solve({"cpi": 2.0})["QA"] / m.QA0 - 1).max() < 1e-7
    mod = _run(ROOT / "validation" / "ifpri_home" / "compare_home.py", run_name="v4")
    for mg, lim in (("composite", (0.01, 0.01, 0.95, 0.6)), ("split", (0.001, 0.002, 0.99, 0.15))):
        r = mod["run"](mg)
        a = r.diff_pp.abs()
        assert a[r["item"].isin(["RGDP", "RCONS"])].max() < lim[0]
        assert a[r["item"] == "RHOME"].max() < lim[1]
        assert (a < 0.1).mean() >= lim[2] and a.max() < lim[3]


def test_hosoe_pycge():
    """V5: on Hosoe et al.'s stdcge SAM, the model reproduces every compared result of pycge after abolishing tariffs:
    within 1e-9 in levels and 1e-8 pp in % changes."""
    mod = _run(ROOT / "validation" / "hosoe" / "compare_hosoe.py", run_name="v5")
    P0, P1, G0, G1, tab = mod["P0"], mod["P1"], mod["G0"], mod["G1"], mod["tab"]
    keys = [k for k in P1 if not k.startswith("pz")]          # pz: unit normalisation differs (validation/hosoe/README.md)
    assert mod["samgap"] < 1e-9
    assert max(max(abs(G0[k] - P0[k]) for k in keys), max(abs(G1[k] - P1[k]) for k in keys)) < 1e-9
    pct_cols = [c for c in tab.columns if c.endswith("% change")]
    assert len(pct_cols) == 2
    pct = max(abs(tab.loc[k, pct_cols[0]] - tab.loc[k, pct_cols[1]]) for k in P1 if np.isfinite(tab.loc[k, pct_cols[0]]))
    assert pct < 1e-8
