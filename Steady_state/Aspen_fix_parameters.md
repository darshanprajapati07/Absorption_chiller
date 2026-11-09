# Aspen Plus absorption chiller: energy-balance and COP audit, with corrected parameter values

Sources: `Streams_result.xlsx` (latest 35 °C absorber run), `Steady_state_dataset.xlsx` (SENS-1, 1,297 rows), `absorption.apw`, and the flowsheet screenshot.
Sign convention (Aspen): a positive duty means heat goes into the process stream. All duties below are recomputed from stream enthalpy flows: Q_block = ΣH_out − ΣH_in.

---

## 1. Root causes (from the attached files)

| # | Problem | Evidence | Effect |
|---|---|---|---|
| 1 | **DFLASH (FLASH2) is specified at T = 89.9 °C, so it is a heat exchanger, not an adiabatic separator.** DESAT heats the solution to 103.5 °C and produces 419.08 kg/h of vapour (stream B). DFLASH then cools the mixture back to 89.9 °C and condenses 292.6 kg/h of it again. | Streams 4 and C are both at exactly 89.9 °C. Stream B vapour is 419.08 kg/h, but stream C is only 126.46 kg/h. Q_DFLASH = H4 + HC − HB = **−206,253.5 kcal/h**. | About 63% of the DESAT duty is thrown away inside DFLASH. That duty is not recorded anywhere in the dataset, which explains the 255,402 kcal/h residual and the COP of about 0.21. |
| 2 | **"Generator temperature" in SENS-1 (DESAT T) is not the real generator temperature.** The real generator outlet is set by DFLASH at 89.9 °C. | In the dataset, Q_EVAP and Q_COND are identical at every DESAT value (100 to 106 °C). Only Q_DES increases (281k to 360k), so COP *falls* from 0.249 to 0.195 as the generator gets hotter. | The trend is physically wrong. A real chiller's COP rises with generator temperature until crystallisation sets in. |
| 3 | **DESHEAT1 cools the solution before the generator** (67.34 → 63.8 °C, −5,975 kcal/h). | COLD's temperature spec (63.8 °C) is overridden by the QSHX heat stream, which gives 67.34 °C. DESHEAT1 then forces the solution back to 63.8 °C. | 5,975 kcal/h is rejected to no defined sink, and DESAT has to supply it again. |
| 4 | **The cycle break does not close: stream 1A ≠ stream 1.** | 1A is at 35 °C and 697 Pa with 61.06 kg/h of unabsorbed vapour. Stream 1 is at 32.71 °C and 672 Pa, all liquid. H1A − H1 = **+42,437.9 kcal/h**. | The absorber duty is under-reported by 42,438 kcal/h, because the absorber never returns the solution to the pump-inlet state. |
| 5 | **SENS-1 cannot produce a meaningful dataset.** All pressures are fixed, and stream 1 is a fixed feed. | Changing CONDENS T only alters subcooling. Q_EVAP changes by 0.7%, and EVAP T only alters superheat. ABSORB T only changes Q_ABS, and COP is constant across ABSORB values (0.2196). | The four "independent" variables do not drive the cycle. |

The following were checked and are acceptable:
- Component balances close: Li⁺ and Br⁻ are 23.794 kmol/h everywhere, and 3600 = 3473.537 + 126.463.
- The QSHX loop is internal: HOT −58,503.4 vs COLD +58,502.8 kcal/h.
- Both valves are isenthalpic: VALVE gives 0; SOLVALVE gives −81 kcal/h, which is 0.001%.
- The low-side pressure is consistent: 697 Pa ≈ Psat(1.8 °C) = 696 Pa.
- The high-side pressure gives a 2.2 K subcooled condenser outlet: 10,200 Pa ≈ Psat(46.2 °C), and the outlet is at 44 °C.
- ELECNRTL gives weak/strong concentrations of 57.40 / 59.49 wt%, and the absorber equilibrium at 35 °C/697 Pa is 58.39 wt%. These are consistent with published H₂O–LiBr data, so there is **no need to change the property method**.

## 2. Full energy balance of the current (35 °C) run

| Block | Duty (kcal/h) | Role |
|---|---:|---|
| PUMP | +2.57 | work (Aspen electricity: 5.16 kcal/h) |
| COLD | +58,502.82 | internal (QSHX) |
| HOT | −58,503.39 | internal (QSHX) |
| DESHEAT1 | −5,975.27 | generator boundary |
| DESAT | +328,543.52 | generator boundary |
| **DFLASH** | **−206,253.50** | **generator boundary (hidden duty)** |
| DESHEAT3 | −656.55 | generator boundary (vapour leaves at 78.4 °C) |
| CONDENS | −74,408.46 | external rejection |
| VALVE | 0.00 | adiabatic |
| EVAP | +70,083.18 | external input (cooling effect) |
| SOLVALVE | −81.20 | flash tolerance |
| ABSORB | −68,815.86 | external rejection (to 1A) |
| **Sum** | **+42,437.86** | **= H1A − H1 exactly (cycle-break mismatch)** |

The overall control volume encloses all blocks and closes the loop at stream 1. Within it:

- Q_gen,ext = H4 + H7 − H3 = DESHEAT1 + DESAT + DFLASH + DESHEAT3 = **115,658.2 kcal/h** (134.5 kW)
- Q_abs,closed = H1 − H6 − H10 = **−111,253.7 kcal/h**
- In: 115,658.2 + 70,083.2 + 2.6 = 185,743.9 kcal/h
- Out: 74,408.5 + 111,253.7 = 185,662.2 kcal/h
- **Residual: 81.8 kcal/h (0.044%)**, which is the SOLVALVE flash tolerance.

**The current model's thermodynamic states are actually correct. Only the duty bookkeeping is wrong.**

Correct thermal COP for the current states:

COP = Q_EVAP / Q_gen,ext = 70,083.2 / 115,658.2 = **0.606**

The old spreadsheet COP was 70,083/328,544 = 0.213. That figure is wrong because it ignores the −206,254 kcal/h in DFLASH.

Electrical COP: 70,083 / (115,658 + 5.16) = 0.606. The pump work is negligible in this ideal-pump model.

---

## 3. Corrected Aspen parameter values

Apply the changes **one at a time, in this order**. Re-run after each step and run the listed check before going to the next.

| Step | Block / stream | Current spec | **New spec** | Expected result after re-run (check) |
|---|---|---|---|---|
| 1 | **DESAT** (Heater) | T = 103.5 °C, P = 10,200 Pa | **T = 89.9 °C**, P = 10,200 Pa | Stream B at 89.9 °C with 126.46 kg/h vapour. DFLASH duty ≈ 0. Streams 4 and C are unchanged. Q_DESAT ≈ **+122,290 kcal/h**. |
| 2 | **DFLASH** (Flash2) | T = 89.9 °C, P = 10,200 Pa | **Heat duty = 0 kcal/h**, P = 10,200 Pa | Same results as step 1. The block is now a true adiabatic separator, and stream 4 temperature = DESAT temperature in every future case. |
| 3 | **DESHEAT1** (Heater) | T = 63.8 °C, P = 10,200 Pa | **Heat duty = 0 kcal/h**, P = 10,200 Pa (pass-through) | Stream A = stream 3 = 67.34 °C. Q_DESAT ≈ **+116,315 kcal/h**. Streams 4 and C are unchanged. |
| 4 | **ABSORB** (Heater) | T = 35 °C, P = 697 Pa | **Vapour fraction = 0**, P = 697 Pa | 1A is saturated liquid with no vapour, at about 32.5–33.5 °C (Aspen computes it). Composition is 57.40 wt% LiBr. Q_ABS ≈ **−111,000 kcal/h**. |
| 5 | **Stream 1** (cycle-break feed) | T = 32.706 °C, P = 672 Pa | **Vapour fraction = 0, P = 697 Pa**. Keep 3600 kg/h and the same component flows. | Stream 1 has the same T, P and H as 1A, so H1A − H1 ≈ 0 and the cycle break no longer creates energy. |
| 6 | **EVAP** (Heater) | T = 1.8 °C, P = 697 Pa | **Vapour fraction = 1**, P = 697 Pa | Saturated vapour at Tsat(697 Pa) ≈ 1.74–1.8 °C. Q_EVAP ≈ +70,070 kcal/h. The evaporator temperature now follows from pressure, as in a real chiller. |
| 7 | **COLD** (Heater) | P = 10,200 Pa + T = 63.8 °C (ignored) | **Pressure only** (10,200 Pa). The duty comes from the QSHX heat stream. | No numerical change; this removes the misleading 63.8 °C entry. |
| none | DESHEAT3, CONDENS, PUMP, VALVE, SOLVALVE, HOT | (as is) | **No change** | DESHEAT3 stays at 78.4 °C, which is the vapour leaving temperature, and its duty belongs to the generator boundary. CONDENS stays at 44 °C, liquid, 2.2 K subcooled. |

### Expected nominal results after steps 1–7

| Quantity | Value |
|---|---:|
| Q_gen,ext = Q_DESHEAT1 + Q_DESAT + Q_DFLASH + Q_DESHEAT3 | ≈ 0 + 116,315 + 0 − 657 = **115,658 kcal/h (134.5 kW)** |
| Q_EVAP | ≈ **70,080 kcal/h (81.5 kW)** |
| Q_COND (CONDENS) | −74,408 kcal/h |
| Q_ABS | ≈ −111,250 kcal/h |
| W_pump | 5.2 kcal/h |
| **Thermal COP** | **≈ 0.606** |
| Energy residual: Q_gen + Q_EVAP + W − \|Q_COND\| − \|Q_ABS\| | ≈ 80 kcal/h (< 0.1%) |
| Refrigerant flow | 126.46 kg/h |
| Weak / strong LiBr | 57.40 / 59.49 wt% |
| Circulation ratio (solution / refrigerant) | 28.5 |

Steps 4–6 move T1 slightly, so the last few digits will change. Use Aspen's numbers as the final values, and accept the run if the residual is below 0.5%.

**Generator heat formula for the spreadsheet:** Q_gen = QDESHEAT1 + QDESAT + QDFLASH + QDESHEAT3. Add QDFLASH and QDESHEAT3 as defined variables in the sensitivity block. Do not use QDESAT alone.
**Energy check column:** R = QDESHEAT1 + QDESAT + QDFLASH + QDESHEAT3 + QCOND + QEVAP + QABS + W_PUMP + (H6 − H5). It should be ≈ 0.

### Why the COP is 0.61, not the textbook ~0.74 (Herold et al.)

The model runs the high side at 10,200 Pa, which is Psat at 46.2 °C. The textbook case uses 7,445 Pa. At a generator temperature of 89.9 °C, the higher pressure only allows the solution to concentrate from 57.40 to 59.49 wt% (Δx = 2.1%, versus about 5.4% in the textbook case). That means 28.5 kg of solution must be heated per kg of refrigerant. The resulting COP of 0.61 is a **physically correct result for these pressures**, not an error.

---

## 4. Optional step 8: physically consistent high-side pressure

This step is justified but does change the COP, so apply it only after steps 1–7 validate.

| Block | Current | New |
|---|---|---|
| PUMP discharge | 10,200 Pa | **9,112 Pa** (= Psat of water at 44 °C) |
| COLD, HOT, DESHEAT1, DESAT, DFLASH, DESHEAT3, CONDENS pressure | 10,200 Pa | **0** (Aspen treats P ≤ 0 as pressure drop, so 0 inherits the pump pressure) |
| CONDENS | T = 44 °C | **Vapour fraction = 0** (saturated liquid at 44 °C) |

Expected effect: more desorption at 89.9 °C, more refrigerant flow, and a higher Q_EVAP and COP. Aspen will give the exact numbers. Re-check that stream 4 stays above the crystallisation line; it should, at about 60 wt% and 53 °C.

---

## 5. Sensitivity dataset (only after the nominal model passes)

**Discard the existing 1,297-row dataset.** Its four input variables do not act on the cycle (see problem 5 in section 1).

| Independent variable | Aspen variable | Notes |
|---|---|---|
| Generator temperature | DESAT TEMP (DFLASH adiabatic follows it) | Screen first. The lower bound must be above the bubble point of the 57.4 wt% solution at P_high, otherwise there is no refrigerant flow. |
| Condenser temperature | PUMP PRES = Psat(T_cond), with high-side blocks at P = 0 | Use a list of pressures for 42 to 46 °C: 8,209, 8,642, 9,112, 9,594, 10,099 Pa. |
| Evaporator temperature | VALVE P_out = Psat(T_evap). A Calculator block copies the value to SOLVALVE P_out, ABSORB P, EVAP P and stream 1 P. | A Calculator is a flowsheet option, not a unit block, so the "no new blocks" rule still holds. |
| (remove) ABSORB temperature | — | With ABSORB at vapour fraction 0, the absorber temperature is an **output** and must not be an input. |

Outputs to record:
- QDESHEAT1, QDESAT, QDFLASH, QDESHEAT3, QCOND, QEVAP, QABS and pump power.
- Mass flow of C (refrigerant).
- LiBr wt% in streams 1 and 4, and the temperatures T1A, T4 and T6.
- Q_gen, COP and the residual R.

Reject a case if any of these hold:
- Stream C flow ≤ 0.
- Stream 8 vapour fraction > 0.
- Stream 10 vapour fraction < 1.
- Stream 1A vapour fraction > 0.
- Strong solution at or beyond the crystallisation line.
- |R| / Q_gen > 0.5%.

---

## 5a. Validation run after steps 1–7 (`stream2.xlsx`, 4 Nov 2026)

| Block | Duty (kcal/h) | kW |
|---|---:|---:|
| PUMP | +2.54 | 0.003 |
| COLD / HOT (QSHX, internal) | +58,494.3 / −58,498.7 | ±68.03 |
| DESHEAT1 | −1.2 | ≈ 0 |
| DESAT | +115,308.3 | 134.10 |
| DFLASH | −46.1 | ≈ 0 |
| DESHEAT3 | −656.0 | −0.76 |
| CONDENS | −74,370.9 | −86.49 |
| EVAP | +70,044.6 | 81.46 |
| SOLVALVE | −81.2 | ≈ 0 |
| ABSORB | −110,195.6 | −128.16 |
| **Sum of all block duties** | **≈ 0.00** | (H1A − H1 = 0, so the loop is closed) |

- Q_gen,ext = H4 + H7 − H3 = **114,604.9 kcal/h (133.29 kW)**
- **Thermal COP = 70,044.6 / 114,604.9 = 0.611**
- In = 184,652.1 kcal/h and out = 184,566.5 kcal/h. The **residual is 85.6 kcal/h (0.046%)**. It equals the SOLVALVE flash tolerance (−81.2) plus the QSHX tear tolerance (−4.4).
- Streams 1 and 1A are identical: 33.30 °C, 697 Pa, liquid. Refrigerant flow is 126.40 kg/h. LiBr concentration is 57.40% weak and 59.49% strong.

**One spec still needs correcting.** Stream A is at **3,672 Pa** with 0.3% vapour, when it should be at 10,200 Pa. DESHEAT1 was given *Temperature = 63.8 °C + Duty = 0*, so Aspen solved for the pressure instead. Change DESHEAT1 to **Pressure = 10,200 Pa (or 0 = no drop) + Duty = 0**. Stream A will then equal stream 3: 67.94 °C, 10,200 Pa, liquid. Q_gen and COP stay the same, because enthalpy is a state function and the DESAT outlet state is fixed.

## 5b. Building the new sensitivity block, step by step

Do this only after the DESHEAT1 fix in section 5a. Steps A–C change no physics at the base case, so **re-run after each and confirm that COP ≈ 0.611 and the residual is < 0.1%** before moving on.

### Step A: let the pumps and valves set the pressures

In Aspen, a Heater or Flash pressure of **0** means "no pressure drop", so the block inherits its inlet pressure. Make one pressure in each loop the master value and set every other block to 0.

| Block | Current pressure spec | New pressure spec | Other spec (unchanged unless stated) |
|---|---|---|---|
| PUMP | 10,200 Pa | **10,200 Pa (master P_high)** | — |
| COLD, HOT, DESHEAT1, DESAT, DFLASH, DESHEAT3 | 10,200 Pa | **0** | COLD: none (QSHX); HOT: T = 53.3 °C; DESHEAT1: duty 0; DESAT: T = 89.9 °C; DFLASH: duty 0; DESHEAT3: T = 78.4 °C |
| CONDENS | 10,200 Pa, T = 44 °C | **0**, **vapour fraction = 0** | The condenser outlet becomes saturated liquid, and T_cond = Tsat(P_high) |
| VALVE | P_out = 697 Pa | **697 Pa (master P_low)** | — |
| SOLVALVE | P_out = 697 Pa | 697 Pa (Step B overwrites it) | — |
| EVAP | 697 Pa, VF = 1 | **0**, VF = 1 | — |
| ABSORB | 697 Pa, VF = 0 | **0**, VF = 0 | With two inlets, Aspen uses the lowest inlet pressure (= P_low) |

Expected base-case change: CONDENS is now saturated at about 46.2 °C instead of 2.2 K subcooled at 44 °C. Q_COND and Q_EVAP each drop by a few hundred kcal/h, and the COP will be about 0.60–0.61. **Save this run as the new validated base case.**

### Step B: Calculator `C-PLOW` (a flowsheet option, not a unit block)

This keeps the solution side and stream 1 at the same low pressure as the refrigerant valve.

To create it: Flowsheeting Options → Calculator → New → `C-PLOW`.

| Name | Type | Definition | Units |
|---|---|---|---|
| PLOW | Import | Block-Var, block VALVE, variable **P-OUT** | N/sqm |
| PSV | Export | Block-Var, block SOLVALVE, variable **P-OUT** | N/sqm |
| P1 | Export | Stream-Var, stream 1, variable **PRES** | N/sqm |

Fortran (each line starts in column 7):
```
      PSV = PLOW
      P1  = PLOW
```
Sequence: keep the default (use import/export variables). Run the base case. It must give identical results.

### Step C: re-activate SENS-1 and replace its Vary tab

Right-click SENS-1 → Activate. Delete all four old vary rows and enter these three:

| Vary | Type | Block | Variable | Units | Values (List) | Physical meaning |
|---|---|---|---|---|---|---|
| 1 | Block-Var | DESAT | TEMP | C | 86, 88, 90, 92, 94, 96, 98, 100 | generator temperature (DFLASH is adiabatic, so T4 = T_gen) |
| 2 | Block-Var | PUMP | PRES | N/sqm | 6632, 7384, 8209, 9112, 10200 | T_cond = 38, 40, 42, 44, 46.2 °C (saturation) |
| 3 | Block-Var | VALVE | P-OUT | N/sqm | 696, 758, 814, 873, 935, 1002 | T_evap = 1.8, 3, 4, 5, 6, 7 °C (saturation) |

That gives 8 × 5 × 6 = **240 cases**. The validated base case is (≈90, 10200, 696). **ABSORB TEMP and EVAP TEMP are no longer varied.** They are results: the absorber outlet is saturated liquid at P_low, and the evaporator outlet is saturated vapour at P_low.

### Step D: Define tab (all results to collect)

| Name | Type | Block / stream | Variable | Units |
|---|---|---|---|---|
| QD1 | Block-Var | DESHEAT1 | QCALC | kcal/hr |
| QDES | Block-Var | DESAT | QCALC | kcal/hr |
| QDFL | Block-Var | DFLASH | QCALC | kcal/hr |
| QDS3 | Block-Var | DESHEAT3 | QCALC | kcal/hr |
| QCOND | Block-Var | CONDENS | QCALC | kcal/hr |
| QEVAP | Block-Var | EVAP | QCALC | kcal/hr |
| QABS | Block-Var | ABSORB | QCALC | kcal/hr |
| QSHX | Block-Var | HOT | QCALC | kcal/hr |
| WPUMP | Block-Var | PUMP | WNET (net work) | kcal/hr |
| MREF | Stream-Var | C | MASS-FLOW (component WATER) | kg/hr |
| M4 | Stream-Var | 4 | MASS-FLOW | kg/hr |
| T1 | Stream-Var | 1A | TEMP | C |
| T3 | Stream-Var | 3 | TEMP | C |
| T4 | Stream-Var | 4 | TEMP | C |
| T6 | Stream-Var | 6 | TEMP | C |
| T8 | Stream-Var | 8 | TEMP | C |
| T10 | Stream-Var | 10 | TEMP | C |
| VF1A | Stream-Var | 1A | VFRAC | — |
| VF8 | Stream-Var | 8 | VFRAC | — |
| VF10 | Stream-Var | 10 | VFRAC | — |

### Step E: Tabulate tab

List all the defined variables as columns. Then add these Fortran-expression columns:

| Column | Expression |
|---|---|
| QGEN | `QD1+QDES+QDFL+QDS3` |
| COP | `QEVAP/(QD1+QDES+QDFL+QDS3)` |
| RES | `QD1+QDES+QDFL+QDS3+QEVAP+WPUMP+QCOND+QABS` (should be ≈ 0; it absorbs the ~80 kcal/h SOLVALVE flash tolerance) |
| XSTRONG | `2066.4/M4*100` (wt% LiBr in stream 4; the weak solution stays at 57.40 wt%) |

Reinitialize, then Run. Export the Sensitivity Results table to Excel.

### Step F: filter invalid cases (in Excel, before any ML)

Reject a row if **any** of these is true:

| Check | Reason |
|---|---|
| Status ≠ OK | did not converge |
| MREF ≤ 0.5 kg/h | T_gen is below the weak-solution bubble point, so nothing is desorbed |
| VF8 > 0 or VF10 < 0.999 or VF1A > 0.001 | wrong phase at the condenser, evaporator or absorber outlet |
| T3 ≥ T4 | temperature cross in the SHX, which is infeasible (HOT is fixed at 53.3 °C) |
| XSTRONG > 64 | crystallisation risk (a common single-effect design limit). Also check (XSTRONG, T6) against a LiBr crystallisation chart |
| \|RES\| / QGEN > 0.5% | energy balance not closed |

Expected trends to sanity-check the surviving rows:
- COP rises with T_gen and then flattens.
- COP rises with T_evap.
- COP falls with T_cond.
- MREF increases with T_gen and falls as T_cond rises.
- **MREF does not change with T_evap.** P_low only acts on the low side. Q_EVAP per kg and the absorber temperature change, but the refrigerant flow does not, because stream 1 fixes the weak concentration (see section 6).

### Optional 4th input, only if time allows

The weak-solution concentration (stream 1 LiBr wt%, e.g. 55–58%) represents absorber cooling-water temperature. Varying it needs a second Calculator that sets the stream 1 component flows. Use it only if your guide wants absorber-side effects in the dataset.

## 5c. SENS-1 results (`NEW (1).xlsx`, 241 runs) and the clean dataset

- All 241 runs have status OK. The energy residual is at most 0.24% and averages 0.025%, so **every case closes**.
- Phases are correct in every case:
  - the condenser outlet (stream 8) is liquid at Tsat(P_high): 37.9 / 39.9 / 41.9 / 43.9 / 46.1 °C;
  - the evaporator outlet (stream 10) is saturated vapour: 1.7 to 6.9 °C;
  - the absorber outlet (stream 1A) is liquid.
- There are no SHX temperature crosses, and every case desorbs (m_ref ≥ 19 kg/h).
- **78 cases are rejected** because x_strong > 64 wt%, which is a crystallisation risk. Those are high T_gen combined with low P_high. **163 valid cases remain** (including the base case), with COP from 0.227 to 0.791.
- The trends are physically correct:
  - COP rises with T_gen. For example, at P_high = 10,200 Pa: 0.23 → 0.75.
  - COP falls as T_cond rises. At T_gen = 90 °C: 0.757 at 38 °C → 0.613 at 46 °C.
  - COP rises with T_evap. At T_gen = 90 °C and 10,200 Pa: 0.613 at 1.7 °C → 0.675 at 6.9 °C.
  - m_ref does not change with P_low, as expected with the cycle break (see section 6).
- Base case: Q_gen = 114,654 kcal/h, Q_evap = 69,750 kcal/h, **COP = 0.608**, residual 0.14%.

`SENS1_clean_dataset.xlsx` has three sheets: `ML_dataset` (163 valid rows, SI units), `All_cases` (241 rows with a VALID flag and the reject reason), and `Data_dictionary`.

## 5d. Independent verification of the final dataset

These checks were computed **outside Aspen**. Per-case values are in the `Verification` sheet of `SENS1_clean_dataset.xlsx`. The ranges below cover the 163 valid cases.

| # | Check | Method | Result | Verdict |
|---|---|---|---|---|
| 1 | Overall mass balance | m_ref + m_strong − 3600 | 0.000 kg/h | ✓ |
| 2 | LiBr balance | x_strong·m_strong − 2066.4 | 0.000 kg/h | ✓ |
| 3 | Energy balance | (Q_gen + Q_evap + Q_cond + Q_abs) / Q_gen | 0.006–0.238 %, mean 0.036 % | ✓ (< 0.5 %) |
| 4 | Condenser saturation | T8 − Tsat_IAPWS(P_high) | −0.06 K | ✓ |
| 5 | Evaporator saturation | T10 − Tsat_IAPWS(P_low) | −0.08 K | ✓ |
| 6 | Q_evap, independent | m_ref·(h_g(T_evap) − h_f(T_cond)), steam tables | within 0.012 % | ✓ |
| 7 | Q_cond, independent | m_ref·(h_vap(78.4 °C) − h_f(T_cond)) | within 0.053 % | ✓ |
| 8 | Second law | COP < COP_reversible = (1 − T_a/T_g)·T_e/(T_a − T_e) | 0 violations; COP/COP_rev = 0.33–0.87 (mean 0.74) | ✓ |
| 9 | Generator equilibrium vs ASHRAE Dühring correlation | x_strong(Aspen) − x_strong(ASHRAE) | +0.47 to +0.66 wt % | ✓ (typical ELECNRTL deviation) |
| 10 | Absorber equilibrium vs ASHRAE | T_abs,out(Aspen) − T(ASHRAE) | −2.06 to −2.18 K | ⚠ systematic offset; state it in the report |
| 11 | SHX effectiveness implied by T5 = 53.3 °C | (T4 − 53.3)/(T4 − T1) | 0.62–0.77 | ✓ realistic |
| 12 | Monotonic trends | COP vs T_gen ↑, vs P_high ↓, vs P_low ↑ | 0 / 132, 0 / 114, 0 / 135 violations | ✓ |
| 13 | Duplicates / missing values | input triplets, empty cells | 0 / 0 | ✓ |
| 14 | Crystallisation | x_strong ≤ 64 wt % | 78 cases removed | ✓ (conservative rule) |
| 15 | Base case | COP 0.608, x_strong 59.49 %, residual 0.14 % | matches validated run | ✓ |

Notes:
- The 6 valid cases at T_gen = 86 °C and P_high = 10,200 Pa have a circulation ratio of about 191 and COP of about 0.23–0.25. The generator is barely above the bubble point there. The data are physically correct, but they are an extreme operating region. Keep them, and flag them if the ML model struggles.
- Pump work (about 0.006 kW) is not in the exported residual. It is negligible.

## 6. Limitations to state in the report

- ABSORB and the generator are equilibrium Heater/Flash representations. They have no transfer coefficients and no cooling- or heating-water streams, so Q values are process-side duties.
- The pump is ideal (efficiency 1.0) and NPSHa = 0, because the absorber outlet is saturated liquid. A real unit needs an elevation head above the pump.
- The SHX (HOT/COLD) is specified by T5 = 53.3 °C, not by an effectiveness. In the sensitivity cases, the implied SHX effectiveness will drift.
- Because of the cycle break, the weak-solution concentration (57.40 wt%) and flow (3600 kg/h) are fixed inputs. In a real chiller they float with the absorber cooling-water temperature. The dataset therefore represents a chiller operated at constant weak concentration.
