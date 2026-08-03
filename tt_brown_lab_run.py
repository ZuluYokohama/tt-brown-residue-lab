#!/usr/bin/env python3
"""
tt_brown_lab_run.py — one entrypoint for sim or hardware-backed residue runs.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tt_brown_instruments import make_backend, InstrumentBackend, Channels


def load_daq():
    spec = importlib.util.spec_from_file_location("tt_brown_residue_daq", ROOT / "tt_brown_residue_daq.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # required for dataclasses on 3.12
    spec.loader.exec_module(mod)
    return mod


class BackendBridge:
    """Adapt InstrumentBackend to the DAQ Instruments duck-type."""

    def __init__(self, backend: InstrumentBackend, force_cal_N_per_count: float = 1e-8):
        self.b = backend
        self.force_cal = force_cal_N_per_count
        self._ch = Channels()

    def set_voltage_kV(self, v, polarity=1):
        self.b.set_voltage_kV(v, polarity)

    def hv_off(self):
        self.b.hv_off()

    def read_current_nA(self):
        self._ch = self.b.read()
        return self._ch.I_nA

    def read_pressure_torr(self):
        return self._ch.P_torr if self._ch else self.b.read().P_torr

    def read_deflection_counts(self):
        return self._ch.deflection_counts

    def read_temps_C(self):
        return {"coupon": self._ch.T_coupon_C, "wall": self._ch.T_wall_C}


def main():
    ap = argparse.ArgumentParser(description="TT Brown residue lab runner")
    ap.add_argument("--backend", default="sim", choices=["sim", "serial", "scpi"])
    ap.add_argument("--dwell", type=float, default=0.25)
    ap.add_argument("--out", default=str(ROOT / "tt_brown_runs"))
    ap.add_argument("--port", default="/dev/ttyUSB0")
    ap.add_argument("--analyze", action="store_true")
    args = ap.parse_args()

    daq = load_daq()
    cfg = daq.Config(
        simulate=(args.backend == "sim"),
        dwell_s=args.dwell,
        out_dir=args.out,
        v_steps_kV=[0, 10, 20, 30],
        polarity_cycles=1,
        run_ids=["R1", "R2"],
    )
    exp = daq.Experiment(cfg)

    if args.backend != "sim":
        backend = make_backend(args.backend, port=args.port)
        exp.inst = BackendBridge(backend)
        print(f"hardware backend: {args.backend}")
    else:
        print("simulation backend")

    exp.run()
    if args.analyze:
        csvs = sorted(Path(args.out).glob("run_*.csv"))
        if csvs:
            import subprocess
            subprocess.check_call([
                sys.executable, str(ROOT / "tt_brown_analyze.py"),
                "--csv", str(csvs[-1]),
                "--out", str(ROOT / "tt_brown_analysis"),
            ])


if __name__ == "__main__":
    main()
