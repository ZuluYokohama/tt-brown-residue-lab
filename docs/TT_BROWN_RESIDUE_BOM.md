# Residue experiment — BOM & pipeline (summary)

## Fixture
Torsion-fiber vacuum capacitor stand: sample on axis, optical lever, HV along fiber with slack loop, in situ µN calibrator, high-K vs low-K differential.

## Cost bands (USD)
- Scavenge existing vacuum lab: **2k–15k**
- New small chamber: 15k–50k
- + RGA + fine metrology: 40k–80k

## Metrology budget
- Force floor goal: **1e-8 N** (accept 1e-7 N)
- V steps: 0→30 kV
- ≥3 polarity A/B/A cycles per step
- I interlock: 10–100 nA

## Analysis pipeline
1. Ingest V, I, P, T, deflection
2. Flag interlock / pressure / thermal outliers
3. Deflection → force via in situ cal
4. Polarity-odd / even decomposition
5. Bound k_anom in F ≈ k_anom V² f(K)
6. Optional RPL embed of runs

## Schedule
~13–18 weeks typical (fixture → bringup → systematics → matrix → ledger update)
