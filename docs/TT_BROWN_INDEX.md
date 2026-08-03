# T.T. Brown investigation — package index

Same tech stack as protein/FRB audits: multi-axis features, model residuals, claims ledger, residue experiment.

## Claims & audit
| File | Role |
|------|------|
| `TT_BROWN_CLAIMS_LEDGER.md` | OPEN / OPEN_NULL / RESIDUE claims |
| `TT_BROWN_CLAIMS_LEDGER.json` | Machine-readable ledger |
| `tt_brown_claim_audit.json` | Regime cloud RPL pass |
| `tt_brown_model_audit.json` | EHD vs V² vs Brown-grav residuals |
| `tt_brown_continued.json` | Geometry toy + breakdown carrier + bounds |

## Residue experiment
| File | Role |
|------|------|
| `TT_BROWN_RESIDUE_EXPERIMENT.md` | H0/H1, run matrix R0–R7, systematics S1–S10 |
| `TT_BROWN_RESIDUE_BOM.md` | Fixture, BOM, cost bands, schedule |
| `tt_brown_residue_daq.py` | DAQ state machine + interlock (sim mode) |
| `tt_brown_analyze.py` | Odd/even, k_anom fit, ledger verdict |
| `tt_brown_instruments.py` | sim / serial / SCPI backends |
| `tt_brown_lab_run.py` | Entrypoint |

## Verdict spine
1. Air asymmetric HV thrust → **OPEN** (EHD)
2. Force needs current/corona → **OPEN**
3. Hard vacuum + I=0 → **OPEN_NULL** at ~nN floors (gas-gap)
4. Gravity / vacuum-equivalent thrust → **RESIDUE**
5. High-K solid gravitor → **RESIDUE** pending experiment above

## Quick sim
```bash
python3 tt_brown_lab_run.py --backend sim --dwell 0.2 --analyze
```
