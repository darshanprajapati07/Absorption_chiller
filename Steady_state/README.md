# Stage 1 — Aspen Plus steady state

Single-effect H₂O–LiBr absorption chiller modelled in Aspen Plus (ELECNRTL, true species). The full explanation is in [docs/02_steady_state_aspen.md](../docs/02_steady_state_aspen.md).

| File | What it is |
|---|---|
| `absorption.apw` | Aspen Plus model with the corrected specifications, the SENS-1 sensitivity block and the C-PLOW Calculator |
| `Aspen_fix_parameters.md` | Energy-balance and COP audit: 5 root causes, corrected parameter values, validation runs, SENS-1 build steps, cleaning rules, 15-point verification, limitations |
| `SENS-1_setup_guide.md` | Click-by-click guide to set up SENS-1, the Calculator and the export |
| `SENS1_clean_dataset.xlsx` | **Final steady-state dataset**: 163 valid cases (`ML_dataset`), `Verification`, `All_cases` (241), `Data_dictionary` |
| `Streams_result.xlsx` | Stream results before the fixes. Input to the audit |
| `Steady_state_dataset.xlsx` | Original SENS-1 export. Not physically meaningful; kept for the record |
| `Prompt.txt` | Project brief and constraints |
| `Screenshot 2026-11-04 164508.png` | Flowsheet |

## Key results

| | Before | After |
|---|---|---|
| COP | 0.213 | **0.608** (base case) |
| Energy residual | 42,438 kcal/h (+ a hidden 206,254 kcal/h in DFLASH) | **< 0.05 %** |
| Valid sensitivity cases | 0 meaningful | **163** of 241 |

## Specification changes made (no blocks added or removed)

1. DESAT: T = 89.9 °C
2. DFLASH: duty = 0 (adiabatic)
3. DESHEAT1: duty = 0 with pressure spec (pass-through)
4. ABSORB: vapour fraction = 0
5. Stream 1: vapour fraction = 0, P = P_low
6. EVAP: vapour fraction = 1
7. COLD: pressure only (the duty comes from QSHX)

On top of these, pressure masters were set up:
- PUMP P = P_high and VALVE P_out = P_low;
- every other block P = 0;
- CONDENS vapour fraction = 0;
- Calculator C-PLOW copies P_low to SOLVALVE and stream 1.

Generator heat: **Q_gen = Q_DESHEAT1 + Q_DESAT + Q_DFLASH + Q_DESHEAT3**. COP = Q_EVAP / Q_gen.
