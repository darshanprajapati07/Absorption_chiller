# 3. Stage 2 — MATLAB dynamic model and transient dataset

Folder: [`Transient/`](../Transient/). How to run: [`Transient/README.md`](../Transient/README.md). Design notes: [`Transient/Transient_plan.md`](../Transient/Transient_plan.md).

## 3.1 Model type

The model is a lumped-parameter dynamic model of a single-effect H₂O–LiBr chiller, following Kohlenbach & Ziegler (2008) and Herold, Radermacher & Klein (2016). It has four vessels (generator G, condenser C, evaporator E and absorber A), plus a counter-flow solution heat exchanger (SHX), the solution pump and two throttles.

Each vessel is one control volume at a single temperature. It contains metal with heat capacity Mc plus a fluid inventory.

### States (9 ODEs, solved with `ode15s`)

| State | Meaning |
|---|---|
| T_G, M_G, L_G | Generator temperature, solution mass, LiBr mass (x_strong = L_G/M_G) |
| T_C | Condenser temperature (no liquid hold-up) |
| T_E, M_E | Evaporator temperature and refrigerant pool mass |
| T_A, M_A, L_A | Absorber temperature, solution mass, LiBr mass (x_weak = L_A/M_A) |

### Balances (`src/model_ode.m`)

Generator:

```
dM_G/dt = m_p − m_ss − m_GC
dL_G/dt = m_p·x_A − m_ss·x_G
(Mc_G + M_G·∂h/∂T)·dT_G/dt = m_p(h3 − h_G) − m_GC(h_vG − h_G) + Q_gen − M_G·∂h/∂x·dx_G/dt
```

Condenser:

```
Mc_C·dT_C/dt = m_GC(h_vG − h_fC) − Q_cond
```

Evaporator:

```
dM_E/dt = m_GC − m_EA
(Mc_E + M_E·cp)·dT_E/dt = m_GC(h_fC − h_fE) − m_EA(h_vE − h_fE) + Q_evap
```

Absorber:

```
dM_A/dt = m_ss + m_EA − m_p
dL_A/dt = m_ss·x_G − m_p·x_A
(Mc_A + M_A·∂h/∂T)·dT_A/dt = m_ss(h5 − h_A) + m_EA(h_vE − h_A) − Q_abs − M_A·∂h/∂x·dx_A/dt
```

### Algebraic relations (`src/model_algebraic.m`)

- **Pressures:** P_high = Psat(T_C) and P_low = Psat(T_E), from IAPWS-IF97 (`psat_w`, `tsat_w`).
- **Vapour flows** are driven by pressure differences, smoothed with `spos`, a smooth max(·,0):
  - m_GC = k_G·spos(P_sol(T_G, x_G) − P_C)
  - m_EA = k_A·f_E·spos(P_E − P_sol(T_A, x_A)), where f_E = M_E/(M_E + 1 kg) prevents dry-out.
- **Strong-solution flow:** m_ss = m_ss,0·M_G/M_G,0 (sump level).
- **Solution enthalpy** h(x, T) and its derivatives come from the ASHRAE correlation (`h_sol`, `T_from_h_sol`).
- **Equilibrium:** the ASHRAE Dühring correlation (`duhring_T`, `p_sol`), with offsets calibrated to Aspen ELECNRTL.
- **SHX:** counter-flow ε-NTU. It gives Q_shx, h3/T3 (to the generator) and h5/T5 (to the absorber).
- **External heat transfer:** each vessel is at a uniform temperature, so ε = 1 − exp(−UA/(ṁc_p)).
  - Q_gen = C_hw(T_hw,in − T_G)·ε
  - Q_abs = C_cw(T_A − T_cw,in)·ε
  - Q_cond = C_cw(T_C − T_cw,mid)·ε, because the cooling water passes through the **absorber first, then the condenser**.
  - Q_evap = C_chw(T_chw,in − T_E)·ε
- **Water outlet temperatures:** from energy balances on each circuit.
- **Stored energy U:** computed for the conservation check.

### Property functions (`src/`)

| File | Content |
|---|---|
| `psat_w.m`, `tsat_w.m` | IAPWS-IF97 saturation pressure and temperature of water |
| `water_h.m` | h_f = 4.186·T, h_v = 2501 + 1.86·T (kJ/kg) |
| `h_sol.m` | ASHRAE LiBr–H₂O enthalpy h(x, T), plus ∂h/∂T and ∂h/∂x |
| `T_from_h_sol.m` | Inverse of h_sol |
| `duhring_T.m` | ASHRAE Dühring equilibrium T(x, T_ref) |
| `p_sol.m` | Vapour pressure over solution, with equilibrium offset |
| `spos.m` | Smooth positive part |

## 3.2 Design of the external water circuits (chosen)

| Circuit | Design inlet | Design | Nominal flow |
|---|---|---|---|
| Hot water → generator | 105 °C | 8 K drop | 4.113 kg/s |
| Cooling water → absorber, then condenser | 27 °C | 3.5 K rise in the absorber | 9.029 kg/s |
| Chilled water → evaporator | 12 °C | 12 → 7 °C | 3.876 kg/s |
| Solution pump | — | — | 1.0 kg/s (3600 kg/h, as in Aspen) |

## 3.3 Calibration (`src/calibrate_model.m`)

The unknown parameters are solved so that the **steady state at the design inputs equals the Aspen base case**. The base-case targets are:
- T_gen 89.893, T_cond 46.140, T_evap 1.743 and T_abs 33.304 °C;
- x 57.40/59.49 wt%;
- m_ref 126.354 kg/h;
- T5 53.3 °C.

| Parameter | Value | Unit | Source |
|---|---|---|---|
| UA_gen | 12.98 | kW/K | calibrated |
| UA_cond | 5.985 | kW/K | calibrated |
| UA_evap | 10.84 | kW/K | calibrated |
| UA_abs | 30.62 | kW/K | calibrated |
| UA_shx | 3.250 | kW/K | calibrated to Aspen T5 |
| k_vap_gen | 3.45 × 10⁻⁴ | kg/s/Pa | calibrated |
| k_vap_abs | 5.23 × 10⁻³ | kg/s/Pa | calibrated |
| dT_eq_gen / dT_eq_abs | −1.244 / −2.092 | K | Aspen vs ASHRAE equilibrium |
| dT_dyn_gen / dT_dyn_abs | −1.471 / −1.930 | K | including vapour driving ΔP |
| Mc G / C / E / A | 800 / 400 / 600 / 800 | kJ/K | assumed, scaled from the 10 kW unit of Kohlenbach & Ziegler to ≈ 80 kW |
| Solution hold-up G / A, refrigerant E | 120 / 200 / 30 | kg | assumed |

The full table is in `Transient/output/model_parameters.csv`. The assumed values can be changed in `src/design_point.m`.

## 3.4 Scenarios (`src/make_scenarios.m`, `rng(2026)`)

| Type | Runs | Description | Duration |
|---|---|---|---|
| step | 20 | Single-input steps at 15 min. T_hw ±5/±10 K, flows ±20 %, T_cw ±2/±4 K, T_chw +2/−2/+3/−1.5 K, pump ±10 % | 3 h |
| ramp | 16 | T_hw ±10 K over 10/30/60 min; T_cw ±3 K, T_chw +2.5/−2 K over 30/60 min; combined hot+cooling ramps | 4 h |
| startup / shutdown | 4 + 4 | Hot water 80/85 °C ↔ 105/110 °C | 4 h |
| daily | 5 | Solar-type profile: T_hw = 92 + (15…19)·sin(πt/12h) + noise (85–115 °C), with matching ambient cooling water and load | 12 h |
| aprbs | 150 | Amplitude-modulated pseudo-random binary sequences on all 7 inputs at once. Each input holds 5–30 min, with 30 s transitions | 4 h |

APRBS ranges:
- T_hw 90–110 °C, T_cw 25–32 °C, T_chw 11.5–16 °C;
- flows 0.80–1.15 × design;
- pump 0.85–1.10 × design.

The first attempt used wider ranges, and **70 runs** were excluded for evaporator freezing. The ranges were narrowed to the values above, which left only 2 excluded runs.

## 3.5 Simulation and validity checks (`src/simulate_scenario.m`)

- Inputs are interpolated with `griddedInterpolant`. Steps are applied as 1 s ramps.
- The ODEs are solved with `ode15s`, and the results are sampled every **10 s**.

A run is **invalid** if any of these holds:

| Check | Condition |
|---|---|
| Crystallisation risk | x_strong > 64 wt% |
| Refrigerant freezing | T_evap < 0 °C |
| Evaporator dry-out | Refrigerant pool runs dry |
| Energy conservation | \|ΔU − ∫(Q_gen + Q_evap − Q_cond − Q_abs)dt\| / ∫\|Q\| > 1 % |
| Solver | Solver failure |

Invalid runs are kept in the `.mat` file and in `run_summary.csv`, but not in the CSV dataset.

`COP_inst` = Q_evap/Q_gen swings, and can exceed 3 briefly when the hot water drops, because stored refrigerant keeps cooling. A **`COP_avg30`** was therefore added: ΣQ_evap/ΣQ_gen over a trailing 30 min. This is the recommended efficiency target.

## 3.6 Validation (`src/validate_model.m`, `output/validation_report.txt`)

### A. Steady state vs the Aspen base case

| Quantity | Aspen | Model | Diff |
|---|---|---|---|
| T_gen / T_cond / T_evap / T_abs | 89.893 / 46.140 / 1.743 / 33.304 | identical | 0.000 |
| x strong / weak | 59.488 / 57.400 | identical | 0.000 |
| m_ref (kg/h) | 126.354 | 126.355 | +0.001 |
| T5 / T3 (°C) | 53.300 / 67.943 | 53.300 / 67.588 | 0 / −0.355 |
| Q_gen (kW) | 133.34 | 137.73 | +3.29 % |
| Q_evap (kW) | 81.12 | 81.12 | 0.00 % |
| Q_cond (kW) | 86.15 | 86.57 | +0.49 % |
| Q_abs (kW) | 128.13 | 132.28 | +3.24 % |
| COP | 0.608 | 0.589 | −3.19 % |

The duty differences come from the ASHRAE enthalpy correlation, which has a different heat of mixing from ELECNRTL. The states and Q_evap (pure water) match exactly. The model's own energy residual is −2.8 × 10⁻¹⁴ kW.

### B. Thermodynamic core vs the 163 valid SENS-1 cases

| Quantity | Mean \|err\| | Max \|err\| | Mean \|err\| % |
|---|---|---|---|
| x_strong | 0.034 wt% | 0.093 | 0.06 % |
| m_ref | 1.84 kg/h | 5.02 | 1.21 % |
| T_abs,out | 0.066 K | 0.128 | 0.17 % |
| Q_gen | 7.31 kW | 14.96 | 3.44 % |
| Q_evap | 1.20 kW | 3.27 | 1.21 % |
| COP | 0.026 | 0.032 | 3.78 % |

The COP correlation between the model and Aspen is **R = 0.9998**. See `output/figures/validation_vs_aspen_SENS1.png`.

### C. Step response, hot water +10 K

| Output | Initial | Final | t63 | t95 |
|---|---|---|---|---|
| Q_evap | 81.12 kW | 93.57 kW | 18.2 min | 46.5 min |
| T_chw,out | 7.000 °C | 6.232 °C | 18.2 min | 46.5 min |
| x_strong | 59.49 wt% | 61.32 wt% | 12.7 min | 41.0 min |
| Q_gen | 137.7 kW | 157.7 kW | peak 228.9 kW just after the step | |

See `output/figures/step_response_hot_water.png`.

### D. Dataset

| Item | Value |
|---|---|
| Runs | 199 simulated, **197 valid** (2 excluded for T_evap < 0 °C) |
| Valid runs by type | aprbs 149/150, daily 5/5, ramp 16/16, shutdown 4/4, startup 4/4, step 19/20 |
| Rows | **291,437** at 10 s, 40 columns |
| Split by whole run | train 134, validation 29, **test 34**. The 5 daily profiles are always test |
| Energy error per run | max 0.032 %, mean 0.0011 % |
| Conservation | Total charge (350 kg) and LiBr mass (186.19 kg) conserved exactly |
| Ranges | COP_avg30 0.364–1.082, Q_evap 29.6–115.0 kW, T_chw,out 5.1–12.5 °C, x_strong 54.64–61.54 wt%, T_evap 0.07–8.59 °C |
| Runtime | 4.8 min (full) on the project laptop, R2025a |

## 3.7 Dataset columns (`output/data_dictionary.csv`)

| Group | Columns |
|---|---|
| Identification | `run_id`, `scenario_type`, `time_s`, `split` |
| **Inputs (7)** | `T_hw_in_C`, `m_hw_kg_s`, `T_cw_in_C`, `m_cw_kg_s`, `T_chw_in_C`, `m_chw_kg_s`, `m_pump_kg_s` |
| Temperatures | `T_gen_C`, `T_cond_C`, `T_evap_C`, `T_abs_C`, `T_shx_weak_out_C` (stream 3), `T_shx_strong_out_C` (stream 5) |
| Concentrations / pressures | `x_strong_wt`, `x_weak_wt`, `P_high_kPa`, `P_low_kPa` |
| Flows / inventories | `m_ref_gen_kg_s`, `m_ref_abs_kg_s`, `m_strong_kg_s`, `M_gen_kg`, `M_abs_kg`, `M_evap_kg` |
| Duties | `Q_gen_kW`, `Q_cond_kW`, `Q_evap_kW`, `Q_abs_kW`, `Q_shx_kW` |
| Water outlets | `T_hw_out_C`, `T_cw_mid_C`, `T_cw_out_C`, `T_chw_out_C` |
| Performance | `COP_inst`, `COP_avg30` |
| Flags | `flag_crystallisation`, `flag_freezing` (always false in the valid file) |

## 3.8 Outputs (`Transient/output/`)

| File | Content |
|---|---|
| `transient_dataset.csv` | Valid runs only, 10 s (Git LFS) |
| `transient_dataset_all.mat` | All runs, including invalid ones, plus parameters (Git LFS) |
| `run_summary.csv` | One row per run: type, description, duration, checks, VALID, reason, split |
| `data_dictionary.csv` | Units and meaning of every column |
| `model_parameters.csv` | Calibrated and assumed parameters, with sources |
| `validation_report.txt` | Sections A–D above |
| `figures/*.png` | Validation vs SENS-1, step response, example runs |
