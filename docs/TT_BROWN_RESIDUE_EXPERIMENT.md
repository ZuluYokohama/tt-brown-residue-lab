# Residue experiment design — high-K gravitor in hard vacuum

**Objective:** Measure net force on a sealed high-K dielectric capacitor under high DC in hard vacuum with no breakdown; bound residual force after systematics.

**H0:** With I_discharge=0, hard vacuum, systematics controlled → force consistent with zero within metrology floor.

**H1:** Polarity-reversible force remains scaling as V²·f(K,m) after systematics — would reopen gravitor residue.

## Run matrix
- **R0**: Atmosphere baseline (EHD leak paths)
- **R1**: Vacuum, V=0 — drift floor
- **R2**: Vacuum, V steps, I=0 enforced — primary null
- **R3**: Polarity reverse — odd/even systematics
- **R4**: Brief controlled discharge — confirm force when I≠0
- **R5**: Thermal-only match to HV ΔT
- **R6**: Low-K control same mass/geometry
- **R7**: Symmetric vs slight asymmetry

## Systematics S1–S10
S1 residual gas/wind · S2 leakage current interlock · S3 chamber electrostatics · S4 cable forces · S5 piezo/electrostriction · S6 thermal/radiometer · S7 Lorentz · S8 outgassing momentum · S9 balance tilt · S10 analysis bias

## Decision rule
- F_odd ≈ 0 within floor on R2/R3/R6/R7 → claim #7 **OPEN_NULL**
- F_odd survives S1–S10, beats low-K, I=0, hard vac → **reopen residue** with coefficient bounds only (no gravity claim without replication)
