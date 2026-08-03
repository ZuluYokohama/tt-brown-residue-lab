#!/usr/bin/env python3
"""
tt_brown_instruments.py
-----------------------
Driver interface + stubs for residue-experiment hardware.

Real labs: subclass InstrumentBackend and implement read/write.
Simulation backend is the default for CI / dry-run.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict
import numpy as np


@dataclass
class Channels:
    V_kV: float = 0.0
    polarity: int = 1
    I_nA: float = 0.0
    P_torr: float = 1e-6
    deflection_counts: float = 0.0
    T_coupon_C: float = 24.0
    T_wall_C: float = 23.5


class InstrumentBackend(ABC):
    @abstractmethod
    def set_voltage_kV(self, v_kV: float, polarity: int = 1) -> None: ...

    @abstractmethod
    def hv_off(self) -> None: ...

    @abstractmethod
    def read(self) -> Channels: ...

    def close(self) -> None:
        self.hv_off()


class SimulatedBackend(InstrumentBackend):
    """Null-ish physics + rare current spikes for interlock testing."""

    def __init__(self, seed: int = 0):
        self.rng = np.random.RandomState(seed)
        self._V = 0.0
        self._pol = 1

    def set_voltage_kV(self, v_kV: float, polarity: int = 1) -> None:
        self._V = abs(float(v_kV))
        self._pol = 1 if polarity >= 0 else -1

    def hv_off(self) -> None:
        self._V = 0.0
        self._pol = 1

    def read(self) -> Channels:
        base_I = 0.5 + 0.01 * self._V
        spike = 250.0 if (self.rng.rand() < 0.0015 and self._V > 20) else 0.0
        I = base_I + spike + self.rng.randn() * 0.05
        sys = 0.25 * (self._V / 30.0) ** 2 * self._pol
        defl = sys + self.rng.randn() * 0.5
        return Channels(
            V_kV=self._V * self._pol,
            polarity=self._pol,
            I_nA=float(I),
            P_torr=float(8e-7 + self.rng.rand() * 2e-7),
            deflection_counts=float(defl),
            T_coupon_C=float(24.0 + 0.01 * self._V),
            T_wall_C=23.5,
        )


class SerialLineBackend(InstrumentBackend):
    """ASCII serial pattern — adapt to Trek/Spellman/Keithley dialects."""

    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._ser = None
        self._V = 0.0
        self._pol = 1

    def _open(self):
        if self._ser is not None:
            return
        try:
            import serial  # type: ignore
        except ImportError as e:
            raise RuntimeError("pyserial required for SerialLineBackend") from e
        self._ser = serial.Serial(self.port, self.baud, timeout=self.timeout)

    def _cmd(self, line: str) -> str:
        self._open()
        assert self._ser is not None
        self._ser.write((line.strip() + "\n").encode())
        return self._ser.readline().decode(errors="ignore").strip()

    def set_voltage_kV(self, v_kV: float, polarity: int = 1) -> None:
        self._V = abs(v_kV)
        self._pol = 1 if polarity >= 0 else -1
        self._cmd(f"VSET {self._V:.3f} POL {self._pol}")

    def hv_off(self) -> None:
        self._V = 0.0
        self._pol = 1
        self._cmd("HOFF")

    def read(self) -> Channels:
        raw = self._cmd("READ?")
        vals: Dict[str, float] = {}
        for part in raw.replace(";", ",").split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                try:
                    vals[k.strip().upper()] = float(v)
                except ValueError:
                    pass
        return Channels(
            V_kV=vals.get("V", self._V * self._pol),
            polarity=self._pol,
            I_nA=vals.get("I", 0.0),
            P_torr=vals.get("P", 1e-6),
            deflection_counts=vals.get("D", 0.0),
            T_coupon_C=vals.get("TC", 24.0),
            T_wall_C=vals.get("TW", 23.5),
        )

    def close(self) -> None:
        super().close()
        if self._ser is not None:
            self._ser.close()
            self._ser = None


class SCPIStubBackend(InstrumentBackend):
    """Illustrative SCPI surface (Keithley EM + HV). Wire pyvisa resources."""

    def __init__(self, hv_resource: str = "GPIB0::10::INSTR", em_resource: str = "GPIB0::22::INSTR"):
        self.hv_resource = hv_resource
        self.em_resource = em_resource
        self._rm = None
        self._hv = None
        self._em = None
        self._V = 0.0
        self._pol = 1

    def _ensure(self):
        if self._hv is not None:
            return
        try:
            import pyvisa  # type: ignore
        except ImportError as e:
            raise RuntimeError("pyvisa required for SCPIStubBackend") from e
        self._rm = pyvisa.ResourceManager()
        self._hv = self._rm.open_resource(self.hv_resource)
        self._em = self._rm.open_resource(self.em_resource)

    def set_voltage_kV(self, v_kV: float, polarity: int = 1) -> None:
        self._ensure()
        self._V = abs(v_kV)
        self._pol = 1 if polarity >= 0 else -1
        self._hv.write(f"SOUR:VOLT {self._V * self._pol * 1e3}")
        self._hv.write("OUTP ON")

    def hv_off(self) -> None:
        self._V = 0.0
        self._pol = 1
        if self._hv is not None:
            self._hv.write("OUTP OFF")

    def read(self) -> Channels:
        self._ensure()
        try:
            I_A = float(self._em.query("MEAS:CURR?"))
            I_nA = I_A * 1e9
        except Exception:
            I_nA = 0.0
        return Channels(
            V_kV=self._V * self._pol,
            polarity=self._pol,
            I_nA=float(I_nA),
            P_torr=1e-6,
            deflection_counts=0.0,
            T_coupon_C=24.0,
            T_wall_C=23.5,
        )

    def close(self) -> None:
        super().close()
        for r in (self._hv, self._em):
            if r is not None:
                try:
                    r.close()
                except Exception:
                    pass
        self._hv = self._em = None


def make_backend(kind: str = "sim", **kwargs) -> InstrumentBackend:
    kind = kind.lower()
    if kind in ("sim", "simulate", "simulated"):
        return SimulatedBackend(seed=int(kwargs.get("seed", 0)))
    if kind in ("serial", "ascii"):
        return SerialLineBackend(port=kwargs.get("port", "/dev/ttyUSB0"), baud=int(kwargs.get("baud", 9600)))
    if kind in ("scpi", "visa", "pyvisa"):
        return SCPIStubBackend(
            hv_resource=kwargs.get("hv_resource", "GPIB0::10::INSTR"),
            em_resource=kwargs.get("em_resource", "GPIB0::22::INSTR"),
        )
    raise ValueError(f"unknown backend kind: {kind}")
