#!/usr/bin/env python3
"""tt_brown_residue_daq.py — R0–R7 capable DAQ with I/P interlock (compact)."""
from __future__ import annotations
import argparse, csv, json, time, enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np

@dataclass
class Config:
    v_steps_kV: List[float] = field(default_factory=lambda: [0, 5, 10, 15, 20, 25, 30])
    polarity_cycles: int = 3
    dwell_s: float = 5.0
    sample_hz: float = 10.0
    i_interlock_nA: float = 50.0
    p_reject_torr: float = 5e-6
    p_target_torr: float = 1e-6
    force_cal_N_per_count: float = 1e-8
    out_dir: str = "tt_brown_runs"
    simulate: bool = True
    run_ids: List[str] = field(default_factory=lambda: ["R1", "R2", "R3", "R6"])

class Instruments:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._V = 0.0
        self._polarity = 1
    def set_voltage_kV(self, v: float, polarity: int = 1):
        self._V = abs(v)
        self._polarity = 1 if polarity >= 0 else -1
        if not self.cfg.simulate:
            raise NotImplementedError("wire HV or use tt_brown_lab_run BackendBridge")
    def read_current_nA(self) -> float:
        if self.cfg.simulate:
            base = 0.5 + 0.01 * abs(self._V)
            spike = 200.0 if (np.random.rand() < 0.002 and abs(self._V) > 20) else 0.0
            return float(base + spike + np.random.randn() * 0.05)
        raise NotImplementedError
    def read_pressure_torr(self) -> float:
        if self.cfg.simulate:
            return float(8e-7 + np.random.rand() * 2e-7)
        raise NotImplementedError
    def read_deflection_counts(self) -> float:
        if self.cfg.simulate:
            sys = 0.3 * (self._V / 30.0) ** 2 * self._polarity
            return float(sys + np.random.randn() * 0.5)
        raise NotImplementedError
    def read_temps_C(self) -> Dict[str, float]:
        if self.cfg.simulate:
            return {"coupon": 24.0 + 0.01 * abs(self._V), "wall": 23.5}
        raise NotImplementedError
    def hv_off(self):
        self._V = 0.0
        self._polarity = 1

class State(enum.Enum):
    IDLE="IDLE"; PUMPDOWN="PUMPDOWN"; ZERO="ZERO"; STEP_V="STEP_V"
    POLARITY="POLARITY"; DWELL="DWELL"; LOG="LOG"
    INTERLOCK_TRIP="INTERLOCK_TRIP"; SAFE="SAFE"; COMPLETE="COMPLETE"; ABORT="ABORT"

@dataclass
class Sample:
    t: float; run_id: str; V_kV: float; polarity: int; I_nA: float
    P_torr: float; deflection: float; F_N: float; T_coupon: float; T_wall: float; flag: str

class Experiment:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.inst = Instruments(cfg)
        self.state = State.IDLE
        self.run_id = cfg.run_ids[0]
        self.run_idx = 0
        self.v_idx = 0
        self.pol_idx = 0
        self.dwell_t0 = 0.0
        self.samples: List[Sample] = []
        self.events: List[Dict[str, Any]] = []
        self.out = Path(cfg.out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
    def log_event(self, msg: str, **kw):
        ev = {"t": time.time(), "state": self.state.value, "msg": msg, **kw}
        self.events.append(ev)
        print(f"[{self.state.value}] {msg} {kw if kw else ''}")
    def polarity_now(self) -> int:
        return 1 if (self.pol_idx % 2 == 0) else -1
    def V_now(self) -> float:
        return self.cfg.v_steps_kV[self.v_idx]
    def interlock_check(self, I_nA: float, P_torr: float) -> Optional[str]:
        if I_nA > self.cfg.i_interlock_nA: return "I_TRIP"
        if P_torr > self.cfg.p_reject_torr: return "P_TRIP"
        return None
    def take_sample(self, flag: str = "OK") -> Sample:
        I = self.inst.read_current_nA()
        P = self.inst.read_pressure_torr()
        d = self.inst.read_deflection_counts()
        temps = self.inst.read_temps_C()
        F = d * self.cfg.force_cal_N_per_count
        trip = self.interlock_check(I, P)
        if trip and flag == "OK": flag = trip
        s = Sample(time.time(), self.run_id, self.V_now() * (1 if self.polarity_now() > 0 else -1),
                   self.polarity_now(), I, P, d, F, temps["coupon"], temps["wall"], flag)
        self.samples.append(s)
        return s
    def step(self) -> State:
        if self.state == State.IDLE:
            self.log_event("start", run=self.run_id); self.state = State.PUMPDOWN; return self.state
        if self.state == State.PUMPDOWN:
            P = self.inst.read_pressure_torr(); self.log_event("pumpdown_check", P=P)
            if P <= self.cfg.p_target_torr * 1.5 or self.cfg.simulate: self.state = State.ZERO
            return self.state
        if self.state == State.ZERO:
            self.inst.hv_off()
            for _ in range(max(3, int(self.cfg.sample_hz))):
                self.take_sample("ZERO"); time.sleep(1.0 / self.cfg.sample_hz)
            self.v_idx = 0; self.pol_idx = 0; self.state = State.STEP_V; return self.state
        if self.state == State.STEP_V:
            self.log_event("set_V", V=self.V_now(), pol=self.polarity_now()); self.state = State.POLARITY; return self.state
        if self.state == State.POLARITY:
            try: self.inst.set_voltage_kV(self.V_now(), polarity=self.polarity_now())
            except Exception as e:
                self.log_event("hv_error", err=str(e)); self.state = State.ABORT; return self.state
            self.dwell_t0 = time.time(); self.state = State.DWELL; return self.state
        if self.state == State.DWELL:
            s = self.take_sample()
            if s.flag in ("I_TRIP", "P_TRIP"):
                self.log_event("interlock", flag=s.flag, I=s.I_nA, P=s.P_torr); self.state = State.INTERLOCK_TRIP; return self.state
            if time.time() - self.dwell_t0 >= self.cfg.dwell_s: self.state = State.LOG
            else: time.sleep(1.0 / self.cfg.sample_hz)
            return self.state
        if self.state == State.LOG:
            self.pol_idx += 1
            if self.pol_idx >= 2 * self.cfg.polarity_cycles:
                self.pol_idx = 0; self.v_idx += 1
                if self.v_idx >= len(self.cfg.v_steps_kV):
                    self.inst.hv_off(); self.run_idx += 1
                    if self.run_idx >= len(self.cfg.run_ids):
                        self.state = State.COMPLETE; return self.state
                    self.run_id = self.cfg.run_ids[self.run_idx]; self.v_idx = 0; self.state = State.ZERO; return self.state
            self.state = State.STEP_V; return self.state
        if self.state == State.INTERLOCK_TRIP:
            self.inst.hv_off(); self.take_sample("SAFE"); self.state = State.SAFE; return self.state
        if self.state == State.SAFE:
            self.log_event("safe_hold"); self.pol_idx += 1
            if self.pol_idx >= 2 * self.cfg.polarity_cycles:
                self.pol_idx = 0; self.v_idx += 1
            self.state = State.COMPLETE if self.v_idx >= len(self.cfg.v_steps_kV) else State.STEP_V
            return self.state
        if self.state in (State.COMPLETE, State.ABORT):
            self.inst.hv_off(); return self.state
        return self.state
    def run(self):
        self.state = State.IDLE; guard = 0
        while self.state not in (State.COMPLETE, State.ABORT) and guard < 100000:
            self.step(); guard += 1
        self.save(); self.log_event("finished", state=self.state.value, n_samples=len(self.samples))
    def save(self):
        ts = time.strftime("%Y%m%d_%H%M%S")
        csv_path = self.out / f"run_{ts}.csv"
        with csv_path.open("w", newline="") as f:
            if self.samples:
                w = csv.DictWriter(f, fieldnames=list(asdict(self.samples[0]).keys()))
                w.writeheader()
                for s in self.samples: w.writerow(asdict(s))
        (self.out / f"events_{ts}.jsonl").write_text("\n".join(json.dumps(e) for e in self.events) + "\n")
        (self.out / f"meta_{ts}.json").write_text(json.dumps({"config": asdict(self.cfg), "n_samples": len(self.samples), "final_state": self.state.value}, indent=2))
        print(f"wrote {csv_path}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dwell", type=float, default=0.3)
    p.add_argument("--out", default="tt_brown_runs")
    args = p.parse_args()
    cfg = Config(simulate=True, dwell_s=args.dwell, out_dir=args.out, v_steps_kV=[0, 10, 20, 30], polarity_cycles=1, run_ids=["R1", "R2"])
    Experiment(cfg).run()

if __name__ == "__main__":
    main()
