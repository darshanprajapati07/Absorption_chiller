# 9. File reference

Every file in the repository, grouped by folder. "Generated" means the file is produced by a script and can be rebuilt.

## Root

| File | Description |
|---|---|
| `README.md` | Project overview, results, structure, quick start, documentation index |
| `.gitignore` | Ignores Python caches, MATLAB autosaves, Aspen temporary files, Office lock files, OS files and local tool configuration |
| `.gitattributes` | Line-ending rules, binary types, and Git LFS tracking of the two large dataset files |

## `docs/`

| File | Description |
|---|---|
| `README.md` | Documentation index |
| `01_project_overview.md` | Problem, objectives, constraints, flowsheet blocks and streams, approach, deliverables |
| `02_steady_state_aspen.md` | Aspen audit, root causes, fixes, SENS-1 design, cleaning, verification |
| `03_transient_model_matlab.md` | Dynamic model equations, properties, calibration, scenarios, validation, dataset columns |
| `04_machine_learning.md` | ML formulation, data preparation, models, training, full results, artefacts, usage |
| `05_digital_twin_dashboard.md` | Dashboard architecture, JS engine verification, derived values, 3D plant, interface design |
| `06_results_summary.md` | All key numbers |
| `07_reproducibility_guide.md` | Commands to reproduce every stage |
| `08_project_log.md` | Chronological log, problems and fixes |
| `09_file_reference.md` | This file |
| `10_limitations_and_future_work.md` | Assumptions, limitations, next steps |
| `images/aspen_flowsheet.png` | Aspen Plus flowsheet (same as the screenshot in `Steady_state/`) |
| `images/dashboard_plant_light.jpg`, `images/dashboard_plant_dark.jpg` | Plant screen of the dashboard (v1.3) |
| `images/dashboard_validation_report.jpg` | Validation page of the dashboard |
| `images/dashboard_3d_generator_closeup.jpg` | 3D close-up of the generator during the tour (v2 interface) |

## `Steady_state/` — Stage 1, Aspen Plus

| File | Description |
|---|---|
| `absorption.apw` | Aspen Plus model (ELECNRTL; 12 blocks; streams 1–10, 1A, A, B, C; heat stream QSHX), with the corrected specifications and the SENS-1 / C-PLOW setup |
| `Aspen_fix_parameters.md` | Full audit: root causes, energy balance, corrected specifications, validation runs §5a–5d, SENS-1 construction, cleaning rules, limitations |
| `SENS-1_setup_guide.md` | Click-by-click guide to set up the sensitivity block, the Calculator and the export |
| `SENS1_clean_dataset.xlsx` | **Final steady-state dataset.** Sheets: `ML_dataset` (163 valid cases), `Verification` (15 checks per case), `All_cases` (241 with VALID flag and reason), `Data_dictionary` |
| `Streams_result.xlsx` | Original stream and heat-stream results before the fixes (absorber at 35 °C). Input to the audit |
| `Steady_state_dataset.xlsx` | Original SENS-1 export (1,297 rows). **Invalid** (see 02 §2.3, cause 5), kept for the record |
| `Prompt.txt` | Original project brief and constraints |
| `Screenshot 2026-11-04 164508.png` | Aspen flowsheet screenshot |
| `README.md` | Stage summary |

## `Transient/` — Stage 2, MATLAB

| File | Description |
|---|---|
| `run_all.m` | **Single entry point.** `run_all` (full) or `run_all('quick')`. It calibrates, validates, simulates all scenarios, checks validity, splits by run, and exports the CSV, MAT, run summary, dictionary, parameters, report and figures |
| `README.md` | How to run, outputs, model summary, ML usage |
| `Transient_plan.md` | Design rationale and plan for the dynamic model and dataset |
| `data/SENS1_ML_dataset.csv` | The 163 valid Aspen cases (CSV), used for validation section B |
| `src/design_point.m` | Aspen base case, water-circuit design, thermal masses, inventories, numerical settings, limits |
| `src/calibrate_model.m` | Solves the UA values, equilibrium offsets and vapour conductances so the steady state equals Aspen |
| `src/model_ode.m` | The 9 ODEs (mass, LiBr and energy balances) |
| `src/model_algebraic.m` | Pressures, vapour flows, enthalpies, SHX ε-NTU, external heat transfer, stored energy |
| `src/steady_state.m` | Steady state for constant inputs |
| `src/make_scenarios.m` | Steps, ramps, startup/shutdown, daily profiles, APRBS (`rng(2026)`) |
| `src/simulate_scenario.m` | Runs one scenario with `ode15s`, samples at 10 s, checks validity, adds COP_avg30 |
| `src/validate_model.m` | Validation against the Aspen base case, SENS-1 and the step response |
| `src/psat_w.m`, `src/tsat_w.m` | IAPWS-IF97 saturation pressure and temperature |
| `src/water_h.m` | Liquid and vapour enthalpy of water |
| `src/h_sol.m`, `src/T_from_h_sol.m` | ASHRAE LiBr–H₂O enthalpy and its inverse |
| `src/duhring_T.m`, `src/p_sol.m` | ASHRAE Dühring equilibrium and solution vapour pressure |
| `src/spos.m` | Smooth max(x, 0) |
| `output/transient_dataset.csv` | **Main dataset** (generated, Git LFS, 174 MB): 291,437 rows × 40 columns, valid runs only |
| `output/transient_dataset_all.mat` | All 199 runs, including invalid ones, plus parameters (generated, Git LFS, 56 MB) |
| `output/run_summary.csv` | One row per run: type, description, duration, solver OK, max x_strong, min T_evap, min M_evap, energy error, valid, reason, split |
| `output/data_dictionary.csv` | Unit and meaning of every dataset column |
| `output/model_parameters.csv` | Calibrated and assumed parameters, with sources |
| `output/validation_report.txt` | Validation sections A–D |
| `output/figures/validation_vs_aspen_SENS1.png` | COP and refrigerant flow, model vs Aspen |
| `output/figures/step_response_hot_water.png` | Response to a +10 K hot-water step |
| `output/figures/example_runs.png` | Example step, ramp, random and daily runs |

## `ML_model/` — Stage 3, machine learning

| File | Description |
|---|---|
| `run_ml.py` | **Single entry point.** Loads data, trains the baselines and the 3-seed LSTM, evaluates on test and daily runs, exports. `--quick` for a smoke test |
| `export.py` | Saves `.pt` weights, scalers and meta, portable JSON, (optional) ONNX, metric tables, test predictions, figures |
| `ml/__init__.py` | Package marker |
| `ml/data.py` | Input and target lists, DT = 60 s, warm-up, run loader, scaler, `cop_avg` |
| `ml/models.py` | `SeqNet` (GRU or LSTM + MLP head), padded batching, training loop, prediction |
| `ml/baselines.py` | Lag and filter feature builder, HistGradientBoosting fit and predict |
| `requirements.txt` | Python package versions |
| `README.md` | How to run, method, results |
| `outputs/models/lstm_seed{0,1,2}.pt` | Trained PyTorch weights (generated) |
| `outputs/models/scalers_and_meta.json` | Scalers and model metadata (generated) |
| `outputs/models/lstm_portable.json` | Weights in framework-free JSON for the dashboard (generated, 6 MB) |
| `outputs/results/metrics_all_models.csv` | Metrics for 4 models × 17 outputs |
| `outputs/results/model_comparison.csv` | Mean and min R², mean NRMSE per model |
| `outputs/results/best_model_metrics.csv` | Ensemble metrics per output |
| `outputs/results/summary.json` | Best model name and daily-profile metrics |
| `outputs/results/test_predictions_best_model.csv` | Inputs, truth and prediction for all test time steps (7 MB) |
| `outputs/figures/model_comparison.png` | R² and NRMSE bars per model |
| `outputs/figures/test_runs_prediction.png` | Truth vs ensemble vs Lag GBM on APRBS, step and daily test runs |
| `outputs/figures/parity_best_model.png` | Parity plots for 8 outputs |
| `outputs/figures/training_curves.png` | Train and validation MSE per seed |
| `outputs/training_log.txt`, `outputs/full_run_console.txt` | Full training logs |

## `Dashboard/` — Stage 4, digital twin

| File | Description |
|---|---|
| `chiller_dashboard.html` | **Deliverable.** Standalone dashboard (generated, ≈ 4 MB) |
| `artifact_page.html` | The same page without the HTML skeleton, for publishing (generated) |
| `build_dashboard.py` | Packs the weights, scalers, metrics, ranges, design inputs and 5 test runs into the template |
| `twin_engine.js` | LSTM forward pass in JavaScript (browser and Node.js) |
| `ui_v3_shell.html` | Current interface (v1.3): HTML, CSS and UI logic, with placeholders for the core code |
| `make_template_v3.py` | Builds `dashboard_template.html` from the shell plus the tested core sections of v2 |
| `dashboard_template.html` | Current page template (generated by `make_template_v3.py`) |
| `dashboard_template_v2_3d.html` | v2 interface; source of the physics helpers, scenarios, descriptions and 3D plant code |
| `dashboard_template_v1_2d.html` | v1 interface (2D schematic) |
| `dashboard_data.json` | Packed data alone (generated), used for Node.js verification |
| `README.md` | How to open, views, derived values, rebuild |
