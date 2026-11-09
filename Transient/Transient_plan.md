# Transient dataset and ML plan: single-effect H₂O–LiBr absorption chiller

Starting point: the validated steady state in `Steady_state/SENS1_clean_dataset.xlsx`. It has 163 valid cases, a base-case COP of 0.608, and an energy residual below 0.24 %.
Tools: MATLAB R2025a (installed on this PC) for the dynamic model and dataset; MATLAB or Python for the ML.

---

## 1. Why not Aspen Plus Dynamics

| Requirement for a dynamic model | Current Aspen model |
|---|---|
| Liquid and vapour hold-ups (vessel volumes, levels) | Heater and Flash blocks with no geometry |
| Heat-transfer area and UA to external water circuits | Process-side duties only. There are no hot, cooling or chilled water streams |
| Closed recirculation loop | Intentional cycle break at streams 1 and 1A |
| Pressure-driven flows at 0.7–10 kPa with an electrolyte | ELECNRTL plus adiabatic flashes at vacuum, which is known to be fragile in pressure-driven mode |

Converting the model would mean redesigning most of the flowsheet. That breaks the "do not rebuild" rule and is a large risk for the deadline. The standard approach in the literature is a **lumped-parameter dynamic model** whose steady state is calibrated to the validated simulation. Examples are Kohlenbach & Ziegler (2008), *Int. J. Refrigeration* 31, parts I and II, and the model in Herold, Radermacher & Klein. **This plan follows that approach.**

---

## 2. Dynamic model structure (MATLAB, ODE system)

There are four main vessels (Generator G, Condenser C, Evaporator E, Absorber A), plus the solution heat exchanger (SHX), the pump and two throttles. Each vessel is a lumped control volume: metal mass plus fluid inventory at one temperature.

### State variables (about 10 ODEs)
| State | Vessel | Equation |
|---|---|---|
| T_G, T_C, T_E, T_A | all four | Energy balance: (M·c)_k dT_k/dt = Σ ṁh_in − Σ ṁh_out + Q_ext,k |
| M_sol,G, M_LiBr,G | generator sump | Total and LiBr mass balances, which give x_strong(t) |
| M_sol,A, M_LiBr,A | absorber sump | Total and LiBr mass balances, which give x_weak(t). This **removes the fixed 57.4 % limitation** |
| M_ref,E | evaporator pool | Refrigerant inventory |
| (optional) transport delays | solution lines | First-order lags, as in Kohlenbach |

### Algebraic relations (at every time step)
- **External heat transfer:** Q_ext,k = ṁ_w·c_p·(T_w,in − T_w,out), where T_w,out = T_k + (T_w,in − T_k)·exp(−UA_k/(ṁ_w·c_p)). This is the ε-NTU form for a vessel at uniform temperature.
- **Pressures:** P_high = Psat(T_C) and P_low = Psat(T_E), using IAPWS (already coded and verified for the steady-state checks).
- **Equilibrium:** T_G = f(x_strong, P_high) and T_A = f(x_weak, P_low). Use the ASHRAE Dühring correlation, **shifted by the measured Aspen offsets** (+0.58 wt % in the generator, −2.1 K in the absorber). The dynamic model then reproduces the Aspen steady state exactly.
- **Vapour flows:** desorbed flow from generator equilibrium. Absorbed flow uses an absorber effectiveness (or mass-transfer coefficient), set so that it matches the Aspen base case.
- **Pump:** fixed volumetric flow (3600 kg/h nominal). This can also be a varied input.
- **Enthalpies:** steam-table approximations for water, which matched Aspen within 0.05 %, and an h(x, T) correlation for the LiBr solution.

### Inputs (the variables that will drive the transients)
| Input | Nominal (to be fixed at calibration) |
|---|---|
| Hot-water inlet temperature and flow (generator) | ~105 °C, sized so that T_G = 89.9 °C |
| Cooling-water inlet temperature and flow (absorber, then condenser in series) | ~28 °C |
| Chilled-water inlet temperature and flow (evaporator) | ~12 °C |
| Solution pump flow | 3600 kg/h |

---

## 3. Calibration and validation against the Aspen steady state

1. **Fix the external design point.** Choose the water inlet temperatures and flows for the base case.
2. **Back-calculate the UA values** from the Aspen base-case duties and the chosen water temperatures:
   - UA_G from Q_gen = 133.3 kW;
   - UA_C from Q_cond = 86.1 kW;
   - UA_E from Q_evap = 81.1 kW;
   - UA_A from Q_abs = 128.1 kW;
   - UA_SHX from Q_SHX = 68.0 kW.
3. **Set the thermal masses (M·c).** Scale the literature values (Kohlenbach's 10 kW unit) to ~80 kW, and document the assumption.
4. **Steady-state check.** Run the dynamic model to steady state:
   - At the base case: Q_gen, Q_evap, COP, T and x must match Aspen within **±1 %**.
   - At 10–15 other SENS-1 cases: match within **±5 %**. Adjust the water inlet temperatures so the internal temperatures match the Aspen case.
5. **Dynamic plausibility.** Check that the time constants are realistic (minutes), that energy is conserved during transients (∫ balance ≈ change in stored energy), and that there is no crystallisation.

The model only proceeds to dataset generation after step 4 passes. That gives the transient data a traceable link back to the validated Aspen model.

---

## 4. Transient scenarios (dataset generation)

| Scenario type | Example | Number of runs |
|---|---|---|
| Single steps | Hot-water T ±5 and ±10 K; cooling-water T ±2 and ±4 K; chilled-water T ±2 K; flows ±20 % | ~40 |
| Ramps | Hot-water T ramp over 10–30 min (a solar or waste-heat profile) | ~20 |
| Random multi-input (APRBS) | All inputs change together, with random amplitudes and hold times of 2–20 min | ~150 |
| Start-up and shut-down | From ambient or equilibrium to nominal, and back | ~10 |
| Daily profile | Realistic 24 h hot-water and load profile | ~5 |

- Time step: **10 s** saved (the solver is variable-step). Run length: 2–6 h.
- Total: about 200–250 runs, which is roughly 0.5–1 million time-step rows.
- Every run is filtered with the same rules as the steady-state data:
  - x_strong ≤ 64 %
  - correct phases
  - energy closure |∫(Q_in − Q_out)dt − ΔE_stored| < 1 %

### Variables saved at each time step
- **Inputs:** T_hw,in, ṁ_hw, T_cw,in, ṁ_cw, T_chw,in, ṁ_chw, ṁ_pump.
- **States and outputs:** T_G, T_C, T_E, T_A, P_high, P_low, x_strong, x_weak, ṁ_ref, Q_gen, Q_cond, Q_evap, Q_abs, T_chw,out, T_hw,out, T_cw,out, instantaneous COP.
- **Run metadata:** run ID and scenario type.

---

## 5. ML model plan

| Stage | Model | Purpose |
|---|---|---|
| Baseline 1 | Steady-state surrogate (ANN or Gaussian process) trained on SENS1 (163 cases) | Predicts the final operating point. Use it as a feature or a sanity check |
| Baseline 2 | Steady-state surrogate plus a first-order lag | The simple "physics-like" benchmark that the ML must beat |
| **Main** | **LSTM or GRU** sequence model (input history → future outputs) | Transient prediction of Q_evap(t), T_chw,out(t) and COP(t) |
| Alternative | NARX network (MATLAB Deep Learning Toolbox) | Easier to explain, and works well for system identification |

- **Split by run, not by time step:** 70 % train, 15 % validation, 15 % test. Also hold out whole scenario types (for example daily profiles) to test generalisation.
- **Metrics:** RMSE and MAPE on Q_evap and T_chw,out. Report both one-step-ahead and multi-step (free-run) errors, settling-time error, and steady-state error against Aspen.

---

## 6. Work plan

| Step | Deliverable | Validation gate |
|---|---|---|
| 1 | Choose the design point and back-calculate UA values | UA values in the expected range for an ~80 kW chiller |
| 2 | MATLAB dynamic model (`chiller_dynamic.m`) | Base case reproduces Aspen within ±1 % |
| 3 | Multi-case steady-state validation | 10–15 SENS-1 cases within ±5 % |
| 4 | Step-response tests | Realistic time constants, energy conserved |
| 5 | Scenario generator and dataset export (`transient_dataset.csv` / `.mat`) | Filters pass, data dictionary written |
| 6 | ML models and comparison against the baselines | Test-set metrics, plots |
| 7 | Report: methods, validation chain (Aspen → dynamic → ML), limitations | — |

## 7. Decisions needed from you
1. **Reference paper.** Does your guide want a specific dynamic-model paper followed (for example Kohlenbach & Ziegler 2008)? If not, I will use it as the default.
2. **External water conditions.** Do you have design values for the hot, cooling and chilled water (from the paper or your guide)? If not, I will use typical values: 105 / 28 / 12 °C.
