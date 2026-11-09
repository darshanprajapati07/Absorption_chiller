# Transient dataset generator: single-effect H₂O–LiBr absorption chiller

This folder holds a complete MATLAB project. **One command** does all of the following:

1. Calibrates a dynamic chiller model on your validated Aspen Plus base case.
2. Validates the model against Aspen.
3. Simulates about 200 transient scenarios.
4. Exports the transient dataset for ML.

Requirements: base MATLAB R2021a or newer, with no toolboxes. It was tested on R2025a.

---

## 1. How to run (step by step)

### Option A: from inside MATLAB (easiest)
1. Open **MATLAB**.
2. In the **Current Folder** bar at the top, go to the `Transient` folder of this repository.
   You can also type this in the Command Window (adjust the path to where you cloned the repository):
   ```matlab
   cd('C:\path\to\Absorption_chiller\Transient')
   ```
3. *(Optional, about 2 min)* Run a quick test first, to check that everything works:
   ```matlab
   run_all('quick')
   ```
4. Generate the **full dataset**:
   ```matlab
   run_all
   ```
5. Wait. The Command Window shows progress, such as `run 50 / 199 (… min elapsed, … min left)`. The full run takes about **5–10 minutes**; it took 4.7 min on this PC.
6. When it prints `All files written to: ...\Transient\output`, you're done.

### Option B: from Windows Command Prompt (no MATLAB window)
```bat
cd /d "C:\path\to\Absorption_chiller\Transient"
matlab -batch "run_all"
```

> The dataset is **reproducible**: the random seeds are fixed, so running it again gives exactly the same data.

---

## 2. What you get (folder `output/`)

| File | What it is |
|---|---|
| **`transient_dataset.csv`** | **Main ML file.** Only valid runs, one row every 10 s. It has 7 inputs, 26 outputs, a split column and flags. |
| `run_summary.csv` | One row per run: type, description, checks (max x_strong, min T_evap, energy error), VALID, reason, train/validation/test split |
| `data_dictionary.csv` | Every column with its unit and meaning |
| `model_parameters.csv` | All calibrated and assumed model parameters, with their source |
| `validation_report.txt` | **Validation for your report:** model vs Aspen base case, vs 163 SENS-1 cases, step-response time constants, dataset checks |
| `transient_dataset_all.mat` | All runs, including invalid ones, plus the parameters (for MATLAB users) |
| `figures/validation_vs_aspen_SENS1.png` | COP and refrigerant flow, model vs Aspen |
| `figures/step_response_hot_water.png` | Response to a +10 K hot-water step |
| `figures/example_runs.png` | Example step, ramp, random and daily runs |

---

## 3. Folder structure

```
Transient/
├── run_all.m                 <- the ONLY file you run
├── README.md                 <- this guide
├── Transient_plan.md         <- method / plan
├── data/
│   └── SENS1_ML_dataset.csv  <- validated Aspen steady-state data (163 cases)
├── src/
│   ├── design_point.m        <- Aspen base case, water design, masses (edit here)
│   ├── calibrate_model.m     <- UA, equilibrium offsets, conductances
│   ├── model_ode.m           <- the dynamic model (9 ODEs)
│   ├── model_algebraic.m     <- flows, duties, SHX, external heat transfer
│   ├── steady_state.m        <- steady state for constant inputs
│   ├── make_scenarios.m      <- the ~200 transient input profiles
│   ├── simulate_scenario.m   <- runs one scenario + validity checks
│   ├── validate_model.m      <- validation vs Aspen
│   └── psat_w, tsat_w, water_h, h_sol, T_from_h_sol, duhring_T, p_sol, spos
│                              <- property functions (IAPWS-IF97, ASHRAE LiBr-H2O)
└── output/                   <- created by run_all
```

---

## 4. The model in brief (for your report)

- **Reference method:** a lumped-parameter dynamic model of a single-effect absorption chiller, following Kohlenbach & Ziegler (2008), *A dynamic simulation model for transient absorption chiller performance*, Int. J. Refrigeration 31 (parts I and II). The thermodynamics follow Herold, Radermacher & Klein, *Absorption Chillers and Heat Pumps*.
- **Nine state variables:**
  - generator: temperature, solution mass, LiBr mass;
  - condenser: temperature;
  - evaporator: temperature, refrigerant mass;
  - absorber: temperature, solution mass, LiBr mass.
- **Properties:**
  - water: IAPWS-IF97 saturation;
  - LiBr–H₂O: ASHRAE Dühring equilibrium and enthalpy correlations, with equilibrium offsets calibrated to Aspen ELECNRTL.
- **Heat transfer:** each vessel exchanges heat with its water circuit through a UA value (ε-NTU). The solution heat exchanger is counter-flow ε-NTU.
- **Calibration:** the UA values, equilibrium offsets and vapour conductances are fitted so that the model's steady state at the design inputs **equals the Aspen base case**: T_gen 89.89 °C, T_cond 46.14 °C, T_evap 1.74 °C, T_abs 33.30 °C, x 57.40/59.49 wt %, refrigerant flow 126.35 kg/h.
- **External water design (chosen):**
  - hot water 105 °C (8 K drop);
  - cooling water 27 °C, through the absorber then the condenser;
  - chilled water 12 → 7 °C.
- **Assumed values:** thermal masses and inventories, scaled from the 10 kW unit of Kohlenbach & Ziegler to about 80 kW. You can change them in `src/design_point.m`.

### Validity filters applied to every run
- Strong solution ≤ 64 wt % (crystallisation risk)
- Evaporator ≥ 0 °C (refrigerant freezing)
- No evaporator dry-out
- Energy conservation error ≤ 1 %: the change in stored energy must equal ∫(Q_gen + Q_evap − Q_cond − Q_abs) dt

Invalid runs are kept in `.mat` and `run_summary.csv`, but are **not** included in `transient_dataset.csv`.

### Known limitations (state these in your report)
- Duties differ from Aspen by up to about 3.5 % (Q_gen, Q_abs), and COP by about 3 %. This is because the dynamic model uses ASHRAE enthalpies, whereas Aspen uses ELECNRTL. The states match exactly, and Q_evap matches exactly.
- Vapour hold-ups and pressure drops are neglected, and condenser liquid hold-up is neglected.
- Thermal masses are assumed, so they set the time constants (about 18 min to 63 % for Q_evap after a hot-water step).

---

## 5. Using the data for ML
- **Inputs (features):** `T_hw_in_C, m_hw_kg_s, T_cw_in_C, m_cw_kg_s, T_chw_in_C, m_chw_kg_s, m_pump_kg_s`, plus past values of the outputs (sequence models).
- **Main targets:** `Q_evap_kW`, `T_chw_out_C`, `Q_gen_kW`, `COP_avg30`.
  - Use `COP_avg30`, not `COP_inst`. The instantaneous ratio swings, and can even go negative, when the hot water suddenly drops, because of thermal storage. That is real physics, but it is not an efficiency.

### Result of the reference run (4.7 min, R2025a)
- **199 runs, 197 valid.** 2 runs were excluded for evaporator freezing risk. **291,437 rows**, 40 columns, about 174 MB.
- **Split:** 134 train / 29 validation / 34 test runs.
- **Energy conservation:** error at most 0.032 %. Total charge (350 kg) and LiBr mass (186.19 kg) are conserved exactly.
- **Data ranges:**
  - Q_evap 29.6–115.0 kW
  - T_chw_out 5.1–12.5 °C
  - x_strong 54.6–61.5 wt %
  - T_evap 0.07–8.6 °C
- **Split:** use the `split` column. It splits by **whole run**, so the model is tested on unseen transients, never on neighbouring time steps. The daily profiles are always in the test set.
- **Group by `run_id`** when you make sequences. Never let a sequence cross from one run into another.

The full model documentation, with equations, calibration and validation tables, is in [docs/03_transient_model_matlab.md](../docs/03_transient_model_matlab.md).
