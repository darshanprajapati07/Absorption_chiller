# 2. Stage 1 — Aspen Plus steady state

Folder: [`Steady_state/`](../Steady_state/).

Detailed working documents:
- [`Aspen_fix_parameters.md`](../Steady_state/Aspen_fix_parameters.md): the full audit with every number.
- [`SENS-1_setup_guide.md`](../Steady_state/SENS-1_setup_guide.md): click-by-click setup of the sensitivity block.

## 2.1 Starting point

| File | Content |
|---|---|
| `absorption.apw` | Aspen Plus model. ELECNRTL, components H₂O and LiBr (true species Li⁺, Br⁻). The blocks and streams are listed in [01_project_overview.md](01_project_overview.md#aspen-flowsheet) |
| `Streams_result.xlsx` | Stream and heat-stream results of the original run, with the absorber at 35 °C |
| `Steady_state_dataset.xlsx` | Original SENS-1 export, 1,297 rows, four varied inputs |

Observed symptoms:
- The energy balance did not close.
- The spreadsheet COP was **0.213**.
- COP *fell* as the generator got hotter, which is physically wrong.

## 2.2 Method of the audit

All block duties were **recomputed from stream enthalpy flows**, Q_block = ΣH_out − ΣH_in, using Aspen's sign convention (positive means heat into the process). Then an overall control volume was drawn round the whole plant, closed at stream 1.

## 2.3 Root causes found

| # | Problem | Evidence | Effect |
|---|---|---|---|
| 1 | DFLASH (Flash2) was specified at T = 89.9 °C, so it acted as a heat exchanger, not an adiabatic separator. DESAT boiled to 103.5 °C (419 kg/h vapour) and DFLASH condensed 292.6 kg/h back | Q_DFLASH = H4 + HC − HB = **−206,253.5 kcal/h** | 63 % of the DESAT duty was destroyed and never counted, which gave COP ≈ 0.21 |
| 2 | The "generator temperature" in SENS-1 (DESAT T) was not the real generator temperature, because DFLASH fixed the outlet at 89.9 °C | Q_EVAP and Q_COND were constant for DESAT 100–106 °C | COP fell with T_gen (0.249 → 0.195), which is unphysical |
| 3 | DESHEAT1 cooled the solution before the generator (67.34 → 63.8 °C) | −5,975 kcal/h to no sink | Heat thrown away and supplied again |
| 4 | The cycle break did not close: stream 1A ≠ stream 1 | 1A at 35 °C with 61 kg/h of unabsorbed vapour; H1A − H1 = **+42,437.9 kcal/h** | Absorber duty under-reported; energy created at the tear |
| 5 | SENS-1 varied inputs that do not drive the cycle (all pressures were fixed, and stream 1 was a fixed feed) | COP constant over ABSORB T; Q_EVAP changed by only 0.7 % | Dataset useless for ML |

Checked and found correct:
- **Mass balances:** Li⁺ and Br⁻ balance at 23.794 kmol/h everywhere.
- **QSHX loop:** internal, −58,503.4 vs +58,502.8 kcal/h.
- **Valves:** isenthalpic.
- **Low-side pressure:** consistent with Psat(1.8 °C).
- **Property method:** ELECNRTL weak and strong concentrations (57.40 / 59.49 wt%) agree with published data, so the property method was not changed.

The thermodynamic **states were correct; only the duty bookkeeping was wrong**. With the correct generator boundary:
- Q_gen,ext = H4 + H7 − H3 = 115,658 kcal/h (134.5 kW).
- The energy residual becomes 81.8 kcal/h (0.044 %).
- COP = 70,083 / 115,658 = **0.606**.

## 2.4 Corrected specifications (applied one at a time)

| Step | Block / stream | Before | After |
|---|---|---|---|
| 1 | DESAT (Heater) | T = 103.5 °C | **T = 89.9 °C** |
| 2 | DFLASH (Flash2) | T = 89.9 °C | **Duty = 0** (adiabatic separator) |
| 3 | DESHEAT1 (Heater) | T = 63.8 °C | **Duty = 0, P = 10,200 Pa (or 0 = no drop)** (pass-through) |
| 4 | ABSORB (Heater) | T = 35 °C | **Vapour fraction = 0** |
| 5 | Stream 1 (tear feed) | T = 32.706 °C, 672 Pa | **Vapour fraction = 0, P = 697 Pa** (same flows) |
| 6 | EVAP (Heater) | T = 1.8 °C | **Vapour fraction = 1** |
| 7 | COLD (Heater) | P + T (T ignored) | **Pressure only.** The duty comes from QSHX |
| — | DESHEAT3, CONDENS, PUMP, VALVE, SOLVALVE, HOT | — | unchanged |

A first attempt left DESHEAT1 at *T + duty*. Aspen then solved for pressure, and stream A ended up at 3,672 Pa. The fix was to specify **pressure + duty**.

### Validation run after the fixes (4 Nov 2026)

| Quantity | Value |
|---|---|
| Sum of all block duties | ≈ 0 (H1A = H1, so the loop is closed) |
| Q_gen,ext | 114,604.9 kcal/h (133.29 kW) |
| Q_evap | 70,044.6 kcal/h (81.46 kW) |
| **Thermal COP** | **0.611** |
| Energy residual | 85.6 kcal/h (**0.046 %**) = SOLVALVE flash tolerance + QSHX tear tolerance |
| Refrigerant flow | 126.40 kg/h |
| Weak / strong LiBr | 57.40 / 59.49 wt% |

Why the COP is 0.61 and not the textbook ≈ 0.74: the high side runs at 10,200 Pa (Psat at 46.2 °C). At 89.9 °C this allows only Δx = 2.1 wt%, giving a circulation ratio of 28.5. **This is correct physics for these pressures, not an error.**

## 2.5 New sensitivity study SENS-1

The pressures were made "masters", so that the pump and the valve set them:
- PUMP discharge = P_high.
- VALVE outlet = P_low.
- Every other block uses P = 0, which means no pressure drop.
- CONDENS is set to vapour fraction 0, so T_cond = Tsat(P_high).

A Calculator **C-PLOW** copies the VALVE outlet pressure to the SOLVALVE outlet and to stream 1. It is a flowsheet option, not a block:

```fortran
      PSV = PLOW
      P1  = PLOW
```

Varied inputs (8 × 5 × 6 = 240 cases, plus the base case = 241 runs):

| Vary | Variable | Values | Physical meaning |
|---|---|---|---|
| 1 | DESAT TEMP | 86, 88, 90, 92, 94, 96, 98, 100 °C | Generator temperature |
| 2 | PUMP PRES | 6632, 7384, 8209, 9112, 10200 Pa | T_cond = 38, 40, 42, 44, 46.2 °C |
| 3 | VALVE P-OUT | 696, 758, 814, 873, 935, 1002 Pa | T_evap = 1.8, 3, 4, 5, 6, 7 °C |

Collected results (Define tab):
- Duties: QD1, QDES, QDFL, QDS3, QCOND, QEVAP, QABS, QSHX and WPUMP.
- Flows: MREF (stream C) and M4.
- Temperatures: T1, T3, T4, T6, T8 and T10.
- Vapour fractions: VF1A, VF8 and VF10.

Derived columns:
- Q_gen = QD1 + QDES + QDFL + QDS3
- COP = QEVAP / Q_gen
- Residual R = Q_gen + QEVAP + WPUMP + QCOND + QABS
- x_strong = 2066.4 / M4 × 100

Problems met during setup, and their fixes (details in [08_project_log.md](08_project_log.md)):
- **Vary sentences 3 and 4 not specified:** SENS-1 was deactivated and rebuilt with 3 vary rows.
- **The Calculator stayed red:** the Fortran had been typed into the *Declarations* box. Clearing that box fixed it. Variable P1 (Stream-Var, stream 1, PRES, Export) also had to be added.
- **The first export had unchanged high-side specs, and QABS/WPUMP were empty:** the specs were re-applied, QABS was defined, and WPUMP was dropped.

## 2.6 Cleaning and verification

A case was rejected if:
- it did not converge;
- MREF ≤ 0.5 kg/h;
- there was a wrong phase (VF8 > 0, VF10 < 0.999 or VF1A > 0.001);
- there was an SHX temperature cross;
- **x_strong > 64 wt%** (crystallisation risk);
- or |R|/Q_gen > 0.5 %.

Results:
- All 241 runs converged. Every residual is ≤ 0.24 % (mean 0.025 %).
- **78** runs were rejected for crystallisation risk, leaving **163 valid cases** with COP 0.227–0.791.
- Base case: Q_gen = 114,654 kcal/h, Q_evap = 69,750 kcal/h, **COP 0.608**, residual 0.14 %.

**Independent verification** was computed outside Aspen; per-case values are in the `Verification` sheet:

| # | Check | Result |
|---|---|---|
| 1 | Overall mass balance | 0.000 kg/h |
| 2 | LiBr balance | 0.000 kg/h |
| 3 | Energy balance | 0.006–0.238 %, mean 0.036 % |
| 4 | Condenser saturation vs IAPWS | −0.06 K |
| 5 | Evaporator saturation vs IAPWS | −0.08 K |
| 6 | Q_evap from steam tables | within 0.012 % |
| 7 | Q_cond from steam tables | within 0.053 % |
| 8 | Second law: COP < COP_reversible | 0 violations; COP/COP_rev 0.33–0.87 |
| 9 | Generator equilibrium vs ASHRAE Dühring | +0.47 to +0.66 wt% (typical ELECNRTL deviation) |
| 10 | Absorber equilibrium vs ASHRAE | −2.06 to −2.18 K (systematic offset; stated as a limitation) |
| 11 | Implied SHX effectiveness | 0.62–0.77 |
| 12 | Monotonic trends: COP ↑ with T_gen, ↓ with P_high, ↑ with P_low | 0 violations |
| 13 | Duplicates or missing values | 0 / 0 |
| 14 | Crystallisation filter | 78 removed |
| 15 | Base case reproduced | COP 0.608 |

Physical trends confirmed:
- At 10,200 Pa, COP rises with T_gen, from 0.23 to 0.75.
- At T_gen = 90 °C, COP falls as T_cond rises: 0.757 at 38 °C, 0.613 at 46 °C.
- COP rises with T_evap: 0.613 at 1.7 °C, 0.675 at 6.9 °C.

## 2.7 Final steady-state dataset

`SENS1_clean_dataset.xlsx`:

| Sheet | Content |
|---|---|
| `ML_dataset` | 163 valid cases, SI units |
| `Verification` | Per-case results of the 15 checks |
| `All_cases` | All 241 cases with a VALID flag and the reject reason |
| `Data_dictionary` | Column definitions |

A CSV copy used by MATLAB is `Transient/data/SENS1_ML_dataset.csv`.

## 2.8 Limitations of the steady-state model

- The generator and absorber are equilibrium Heater/Flash blocks. They have no transfer coefficients and no water streams, so the duties are process-side.
- The pump is ideal (η = 1, NPSHa = 0).
- The SHX is specified by T5 = 53.3 °C, not by an effectiveness, so its effectiveness drifts between cases.
- Because of the cycle break, the weak concentration (57.40 wt%) and the flow (3600 kg/h) are fixed in SENS-1. The dynamic model removes this limitation.
