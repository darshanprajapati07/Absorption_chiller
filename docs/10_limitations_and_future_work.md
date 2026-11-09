# 10. Limitations and future work

## 10.1 Assumptions and limitations

### Steady-state model (Aspen Plus)
- The generator and absorber are equilibrium Heater/Flash blocks. They have no transfer coefficients and no water streams, so their duties are process-side.
- The pump is ideal (efficiency 1, NPSHa = 0, because the absorber outlet is saturated liquid). A real unit needs a static head above the pump.
- The SHX is fixed by T5 = 53.3 °C, so its effectiveness varies between SENS-1 cases (0.62–0.77).
- Because of the cycle break, the weak concentration (57.40 wt%) and the solution flow (3600 kg/h) are fixed in SENS-1. The dataset represents constant-weak-concentration operation.
- The ELECNRTL absorber equilibrium is 2.06–2.18 K below the ASHRAE correlation (a systematic offset).
- COP 0.61 is lower than the textbook ≈ 0.74 because the high side is at 10.2 kPa. This is correct for the chosen pressures.

### Dynamic model (MATLAB)
- Thermal masses and inventories are **assumed**, scaled from Kohlenbach & Ziegler's 10 kW unit to ≈ 80 kW. They set the time constants (t63 ≈ 18 min).
- Vapour hold-ups, pressure drops, condenser liquid hold-up and transport delays in the solution lines are neglected.
- ASHRAE enthalpies differ from ELECNRTL: Q_gen and Q_abs are +3.3 % vs Aspen, and COP is 0.589 vs 0.608. States and Q_evap match exactly.
- No controller is modelled. The plant runs open loop with the given inputs. Real chillers have capacity and anti-crystallisation control.
- The crystallisation limit is a fixed 64 wt%. A temperature-dependent crystallisation line would be more exact.

### AI model
- It reproduces the **MATLAB model**, not measured data. Errors in the physics model are inherited.
- It is valid only inside the training input range. The dashboard limits the inputs to that range.
- Runs that crystallised or froze were removed, so the model cannot predict behaviour beyond those limits.
- The 60 s step cannot resolve phenomena faster than about 1 minute.
- The ensemble spread is an indication of confidence, not a calibrated uncertainty.

### Dashboard
- Several stream values are derived with simple relations (≈ ±1 K for the SHX outlets).
- The 3D equipment is generic and not to scale.
- The 3D library and the fonts load from CDNs, so the first view needs internet. The model and the numbers work offline.

## 10.2 Future work

1. **Plant data:** calibrate the thermal masses and UA values on measured transients from a real chiller, then fine-tune the LSTM (transfer learning).
2. **Control:** add chilled-water temperature control (hot-water valve) and anti-crystallisation logic. Use the LSTM as the prediction model in model predictive control (MPC).
3. **Uncertainty:** add Monte-Carlo dropout or deep-ensemble calibration to give calibrated prediction intervals.
4. **Wider envelope:** add explicit crystallisation and freezing physics, so that the model can warn before reaching unsafe states and predict what happens near them.
5. **Faster physics:** export the dynamic model to a Functional Mock-up Unit (FMU) and compare it with the LSTM.
6. **Real geometry:** replace the generic 3D equipment with CAD of the actual unit, if drawings become available.
7. **Deployment:** stream live sensor data (OPC UA / MQTT) into the twin, so it runs alongside a real plant in observer mode.
