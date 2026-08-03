#!/usr/bin/env python3
"""
tt_brown_analyze.py
-------------------
Consume DAQ CSV → polarity-odd/even, V^2 fit, anomalous bound, ledger verdict.

Usage:
  python3 tt_brown_analyze.py --csv path/to/run.csv --out report_dir
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

try:
    import pandas as pd
except ImportError:
    raise SystemExit("pandas required: pip install pandas")


def load_run(csv_path: Path) -> "pd.DataFrame":
    df = pd.read_csv(csv_path)
    required = {"run_id", "V_kV", "polarity", "F_N", "I_nA", "P_torr", "flag"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")
    return df


def clean(df: "pd.DataFrame", i_max_nA: float, p_max_torr: float) -> "pd.DataFrame":
    d = df.copy()
    d = d[d["flag"].isin(["OK", "ZERO"]) | d["flag"].isna()]
    d = d[d["I_nA"] <= i_max_nA]
    d = d[d["P_torr"] <= p_max_torr]
    d["V_abs"] = d["V_kV"].abs()
    return d


def odd_even_table(df: "pd.DataFrame") -> List[Dict[str, Any]]:
    rows = []
    for (run, vabs), g in df.groupby(["run_id", "V_abs"]):
        plus = g[g["polarity"] > 0]["F_N"]
        minus = g[g["polarity"] < 0]["F_N"]
        if len(plus) == 0 or len(minus) == 0:
            continue
        fp, fm = float(plus.mean()), float(minus.mean())
        sp, sm = float(plus.std(ddof=1) or 0), float(minus.std(ddof=1) or 0)
        n = len(plus) + len(minus)
        se = 0.5 * np.sqrt((sp**2 / max(len(plus), 1)) + (sm**2 / max(len(minus), 1)))
        rows.append({
            "run_id": run,
            "V_abs_kV": float(vabs),
            "F_odd": 0.5 * (fp - fm),
            "F_even": 0.5 * (fp + fm),
            "F_odd_se": float(se),
            "n": int(n),
            "I_mean_nA": float(g["I_nA"].mean()),
            "P_mean_torr": float(g["P_torr"].mean()),
        })
    return rows


def fit_k_anom(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """F_odd ≈ k * (V_kV)^2 → k in N/kV^2."""
    V = np.array([r["V_abs_kV"] for r in rows], float)
    F = np.array([r["F_odd"] for r in rows], float)
    W = np.array([1.0 / max(r["F_odd_se"], 1e-12)**2 for r in rows], float)
    mask = V > 0
    if mask.sum() < 2:
        return {"k_N_per_kV2": 0.0, "k_se": None, "k_abs_upper_95": None, "n_points": int(mask.sum())}
    V2 = V[mask] ** 2
    y = F[mask]
    w = W[mask]
    k = float(np.sum(w * V2 * y) / np.sum(w * V2 * V2))
    resid = y - k * V2
    dof = max(len(y) - 1, 1)
    sigma = float(np.sqrt(np.sum(w * resid**2) / dof / (np.mean(w) + 1e-30)))
    se_k = float(sigma / np.sqrt(np.sum(V2**2) + 1e-30))
    upper = abs(k) + 1.96 * se_k
    return {
        "k_N_per_kV2": k,
        "k_se": se_k,
        "k_abs_upper_95": float(upper),
        "n_points": int(mask.sum()),
        "rms_resid_N": float(np.sqrt(np.mean(resid**2))),
    }


def verdict(fit: Dict[str, Any], floor_N: float) -> Dict[str, Any]:
    k_up = fit.get("k_abs_upper_95")
    if k_up is None:
        return {"status": "INSUFFICIENT_DATA", "detail": "need V>0 polarity pairs"}
    F_at_30 = k_up * (30.0 ** 2)
    if F_at_30 <= floor_N * 3:
        return {
            "status": "OPEN_NULL",
            "detail": f"|k| upper implies F(30kV)={F_at_30:.2e} N ≤ 3×floor ({floor_N:.2e})",
            "F_at_30kV_upper_N": F_at_30,
        }
    return {
        "status": "REOPEN_RESIDUE",
        "detail": f"|k| upper implies F(30kV)={F_at_30:.2e} N exceeds 3×floor; inspect systematics before physics claim",
        "F_at_30kV_upper_N": F_at_30,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default="tt_brown_analysis")
    ap.add_argument("--i-max-nA", type=float, default=50.0)
    ap.add_argument("--p-max-torr", type=float, default=5e-6)
    ap.add_argument("--floor-N", type=float, default=1e-8)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df = load_run(Path(args.csv))
    dfc = clean(df, args.i_max_nA, args.p_max_torr)
    rows = odd_even_table(dfc)
    fit = fit_k_anom(rows)
    verd = verdict(fit, args.floor_N)

    report = {
        "source_csv": str(args.csv),
        "n_raw": int(len(df)),
        "n_clean": int(len(dfc)),
        "odd_even": rows,
        "fit": fit,
        "verdict": verd,
        "gates": {"i_max_nA": args.i_max_nA, "p_max_torr": args.p_max_torr, "floor_N": args.floor_N},
    }
    (out / "analysis_report.json").write_text(json.dumps(report, indent=2))

    md = [
        "# TT Brown residue — analysis report",
        f"**Source:** `{args.csv}`",
        f"**Clean samples:** {report['n_clean']} / {report['n_raw']}",
        "",
        "## Fit F_odd ≈ k V²",
        f"- k = {fit.get('k_N_per_kV2'):.3e} N/kV²",
        f"- |k| 95% upper ≈ {fit.get('k_abs_upper_95')}",
        f"- rms residual ≈ {fit.get('rms_resid_N')}",
        "",
        f"## Verdict: **{verd['status']}**",
        verd["detail"],
        "",
        "## Odd/even table",
    ]
    for r in rows:
        md.append(
            f"- {r['run_id']} V={r['V_abs_kV']:.0f} kV: "
            f"F_odd={r['F_odd']:.3e}±{r['F_odd_se']:.3e} N  F_even={r['F_even']:.3e}"
        )
    (out / "analysis_report.md").write_text("\n".join(md))
    print("\n".join(md))
    print(f"\nwrote {out}/analysis_report.json")


if __name__ == "__main__":
    main()
