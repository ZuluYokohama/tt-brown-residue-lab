# T.T. Brown / Biefeld–Brown — residue lab package

Investigation of Thomas Townsend Brown claims using the same multi-axis /
RPL audit posture as the protein and FRB work.

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
python3 tt_brown_lab_run.py --backend sim --dwell 0.2 --analyze
```

## Hardware path

1. Implement or adapt `SerialLineBackend` / `SCPIStubBackend` in `tt_brown_instruments.py`
2. Run: `python3 tt_brown_lab_run.py --backend serial --port /dev/ttyUSB0`
3. Analyze: `python3 tt_brown_analyze.py --csv tt_brown_runs/run_XXXX.csv`

## Files

- `docs/TT_BROWN_CLAIMS_LEDGER.md` — formal claims
- `docs/TT_BROWN_RESIDUE_EXPERIMENT.md` — H0/H1, R0–R7, systematics S1–S10
- `docs/TT_BROWN_RESIDUE_BOM.md` — fixture, BOM, cost bands, schedule
- `tt_brown_instruments.py` — sim / serial / SCPI driver surface
- `tt_brown_residue_daq.py` — state machine + interlock
- `tt_brown_analyze.py` — F_odd, k_anom bound, verdict
- `tt_brown_lab_run.py` — entrypoint
- `docs/TT_BROWN_INDEX.md` — full index

## Decision rule (claim #7)

- F_odd ≈ 0 within floor after S1–S10 → **OPEN_NULL**, close residue
- F_odd survives controls, beats low-K, I=0, hard vac → reopen residue with coefficient bounds only
