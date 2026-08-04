"""Offline smoke tests for tt-brown-residue-lab (simulation path only)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_instruments_sim_backend():
    from tt_brown_instruments import make_backend
    b = make_backend("sim")
    ch = b.read()
    assert hasattr(ch, "I_nA")
    assert hasattr(ch, "P_torr")


def test_daq_config_import():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "tt_brown_residue_daq", ROOT / "tt_brown_residue_daq.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    cfg = mod.Config(simulate=True, dwell_s=0.05, out_dir=tempfile.mkdtemp())
    assert cfg.simulate is True


def test_sim_run_short():
    """Minimal sim dwell — must complete without hardware."""
    import subprocess

    out = tempfile.mkdtemp()
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tt_brown_lab_run.py"),
            "--backend", "sim",
            "--dwell", "0.05",
            "--out", out,
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, r.stderr
    csvs = list(Path(out).glob("run_*.csv"))
    assert csvs, "expected at least one run_*.csv from sim"


def test_analyze_module_imports():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "tt_brown_analyze", ROOT / "tt_brown_analyze.py"
    )
    assert spec is not None


if __name__ == "__main__":
    test_instruments_sim_backend()
    test_daq_config_import()
    test_sim_run_short()
    test_analyze_module_imports()
    print("all smoke OK")
