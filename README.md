# tt-brown-residue-lab

**T.T. Brown / Biefeld–Brown — residue lab package**

Investigation of Thomas Townsend Brown claims using the same multi-axis / RPL audit posture as the protein and FRB work.

> **License: Proprietary source-available.** Evaluation and academic citation only without a written commercial grant. See [`LICENSE`](LICENSE) and [`COMMERCIAL.md`](COMMERCIAL.md). Not open source.

**Author:** Blake A. Jones (JtechAI) · [b.jones@jtech.ai](mailto:b.jones@jtech.ai)  
**Related:** [rplc-sheaf](https://github.com/ZuluYokohama/rplc-sheaf) (operator series) · [protein-rpl-validation](https://github.com/ZuluYokohama/protein-rpl-validation) (domain app)

---

## Design law

Same verification discipline as the rest of the portfolio:

```
state claim → isolate controls → measure residual → OPEN / OPEN_NULL / RESIDUE
```

Residue is never forced open. Air thrust is not vacuum thrust.

## Verdict spine

| Claim | Status |
|-------|--------|
| Asymmetric HV thrust **in air** | **OPEN** — electrohydrodynamics (ion wind) |
| Thrust requires current / corona / breakdown | **OPEN** |
| Hard vacuum, no breakdown | **OPEN_NULL** (~nN floors) |
| Isolation excluding wind | **OPEN_NULL** |
| Vacuum thrust ≈ air thrust | **RESIDUE** |
| High-K solid “gravitor” weight change | **RESIDUE** (experiment designed) |
| EM–gravity coupling ontology | **RESIDUE** |

## Quick start (simulation)

```bash
pip install -r requirements.txt
python3 tt_brown_lab_run.py --backend sim --dwell 0.2 --analyze
python3 tests/test_smoke.py
```

## Hardware path

1. Implement or adapt `SerialLineBackend` / `SCPIStubBackend` in `tt_brown_instruments.py`
2. Run: `python3 tt_brown_lab_run.py --backend serial --port /dev/ttyUSB0`
3. Analyze: `python3 tt_brown_analyze.py --csv tt_brown_runs/run_XXXX.csv`

## Package map

| Path | Role |
|------|------|
| `docs/TT_BROWN_CLAIMS_LEDGER.md` | Formal claims |
| `docs/TT_BROWN_RESIDUE_EXPERIMENT.md` | H0/H1, R0–R7, systematics S1–S10 |
| `docs/TT_BROWN_RESIDUE_BOM.md` | Fixture, BOM, cost bands, schedule |
| `tt_brown_instruments.py` | sim / serial / SCPI driver surface |
| `tt_brown_residue_daq.py` | State machine + interlock |
| `tt_brown_analyze.py` | F_odd, k_anom bound, verdict |
| `tt_brown_lab_run.py` | Entrypoint |
| `docs/TT_BROWN_INDEX.md` | Full index |
| `docs/METHODOLOGY_BRIDGE.md` | Link to RPL audit posture |

## Decision rule (claim #7)

- F_odd ≈ 0 within floor after S1–S10 → **OPEN_NULL**, close residue
- F_odd survives controls, beats low-K, I=0, hard vac → reopen residue with coefficient bounds only

## What this is not

Not a claim that electrogravitics is real. Not a device design for propulsion.  
OPEN claims are EHD / ion-wind class. RESIDUE items remain closed until hardware gates pass.

## Tests

```bash
python3 tests/test_smoke.py
# → all smoke OK
```

CI: `.github/workflows/sim.yml` (sim-smoke).

## License

**Proprietary source-available** — Copyright © 2026 Blake A. Jones (JtechAI / ZuluYokohama).  
Evaluation Use and citation permitted. **Commercial Use requires a written license:** b.jones@jtech.ai  
Full terms: [`LICENSE`](LICENSE) · Summary: [`COMMERCIAL.md`](COMMERCIAL.md)

## Version

**v0.1.1-professional** — same technical core as v0.1.0; proprietary issuance + résumé-grade packaging.
