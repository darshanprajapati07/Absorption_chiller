# 8. Project log

A chronological record of the work: what was done, the problems met, and how each was solved. Dates are from November 2026.

## Phase 1 — Aspen Plus audit and correction (4 Nov)

| Step | What happened | Resolution |
|---|---|---|
| 1.1 | Studied the inputs: `Streams_result.xlsx`, `Steady_state_dataset.xlsx`, the flowsheet and the brief (`Prompt.txt`). Spreadsheet COP was 0.21, the energy balance did not close, and COP fell with generator temperature | Recomputed every block duty from stream enthalpy flows |
| 1.2 | Found 5 root causes: DFLASH at fixed T destroying 206,254 kcal/h; DESAT T not being the generator T; DESHEAT1 cooling; tear 1A ≠ 1 (+42,438 kcal/h); SENS-1 inputs not acting on the cycle | Documented in `Aspen_fix_parameters.md` §1–2 |
| 1.3 | Proposed 7 specification changes with no new blocks and no property-method change | `Aspen_fix_parameters.md` §3 |
| 1.4 | The user applied the fixes. The validation run (`stream2.xlsx`) gave COP 0.611 and residual 0.046 % | Accepted |
| 1.5 | Stream A was at 3,672 Pa because DESHEAT1 had *T + duty*, so Aspen solved for pressure | Changed to *pressure + duty* (§5a) |

## Phase 2 — Sensitivity study SENS-1 (4–5 Nov)

| Step | What happened | Resolution |
|---|---|---|
| 2.1 | Error: SENS-1 vary sentences 3 and 4 were not specified after the spec changes | Deactivated SENS-1, then rebuilt it with 3 physical inputs |
| 2.2 | Wrote a click-by-click setup guide | `SENS-1_setup_guide.md` |
| 2.3 | Calculator C-PLOW Calculate tab stayed red | The Fortran had also been typed into the *Fortran Declarations* box; clearing it fixed the error. Variable P1 (Stream-Var stream 1 PRES, Export) had to be added |
| 2.4 | First export (`NEW.xlsx`): T8 = 44 and T10 = 1.7426 were constant, and MREF did not depend on PHIGH, so the high-side, CONDENS, EVAP and ABSORB changes had not been applied. QABS and WPUMP were empty | The user re-applied Part 1, defined QABS = ABSORB QCALC and dropped WPUMP |
| 2.5 | Second export (`NEW (1).xlsx`): all 241 runs OK, residual ≤ 0.24 % | Cleaned: 78 crystallisation cases removed, 163 valid |
| 2.6 | In-depth verification: 15 independent checks (mass, energy, IAPWS saturation, steam-table duties, second law, Dühring equilibrium, monotonic trends) | `SENS1_clean_dataset.xlsx` → `Verification` sheet. Absorber offset of −2.1 K vs ASHRAE noted as a limitation |

## Phase 3 — Transient model and dataset (5 Nov)

| Step | What happened | Resolution |
|---|---|---|
| 3.1 | Chose a MATLAB lumped dynamic model instead of Aspen Plus Dynamics (no hold-ups, no water circuits, tear, no-rebuild rule) | `Transient/Transient_plan.md` |
| 3.2 | Chose the design and reference values: Kohlenbach & Ziegler (2008) model structure; water design 105 °C/8 K, 27 °C/3.5 K, 12 → 7 °C; thermal masses scaled to 80 kW | `src/design_point.m` |
| 3.3 | Built the 9-ODE model, ASHRAE/IAPWS properties, calibration, scenarios, validation and export, all from one command (`run_all`) | `Transient/` |
| 3.4 | First full run: **70 APRBS runs** were excluded for evaporator freezing | Narrowed the APRBS ranges (T_hw 90–110, T_cw 25–32, T_chw 11.5–16 °C, flows 0.80–1.15, pump 0.85–1.10). Now 2 excluded |
| 3.5 | `COP_inst` spiked to 3.47 after hot-water drops (stored refrigerant keeps cooling) | Added `COP_avg30` (energy over a trailing 30 min) as the recommended target, and documented it |
| 3.6 | Final run: 197/197 valid of 199, 291,437 rows, energy error ≤ 0.032 %, states match Aspen, COP R = 0.9998 vs SENS-1 | `output/validation_report.txt` |

## Phase 4 — Machine learning (7–8 Nov)

| Step | What happened | Resolution |
|---|---|---|
| 4.1 | Framed the task as simulation mode (inputs only → 16 outputs), split by run, scaling fitted on train only, 60 steps of warm-up | `ml/data.py` |
| 4.2 | A GRU took 14–76 s per epoch on the CPU, too slow | Switched to LSTM 2×128 with batch 32 (1.4–2.4 s per epoch). Resampled from 30 s to 60 s |
| 4.3 | Quick test: Static GBM R² 0.745, Lag GBM R² 0.9785, LSTM (20 epochs) R² 0.886 | Full training: 600 epochs × 3 seeds |
| 4.4 | Full training, 141.7 min: LSTM ensemble R² **0.99914**, NRMSE 0.38 %; daily profiles R² 0.99993 | Selected as the final model |
| 4.5 | ONNX export failed (the `onnx` package was not installed) | Made it optional; a portable JSON of the weights is used for the web |

## Phase 5 — Dashboard (8–9 Nov)

| Step | What happened | Resolution |
|---|---|---|
| 5.1 | v1: 2D SVG schematic dashboard with the LSTM in JavaScript | `twin_engine.js` verified against PyTorch (0.0014 kW) and stable over 50 h |
| 5.2 | `dashboard_data.json` contained `NaN` (MAPE of outputs near zero), which is invalid JSON | Replaced with `null` and set `allow_nan=False` |
| 5.3 | The schematic pipes overlapped the vessel readings, and the energy table overflowed the page width | Rerouted the pipes and let the table cells wrap |
| 5.4 | The user asked for a simpler interface and realistic CAD equipment laid out like the Aspen flowsheet | v2: three.js plant, equipment modelled in code, flowsheet layout, live stream values, guided tour, plain-language panels, stream table |
| 5.5 | SHX outlet temperatures are not model outputs | Derived with effectiveness 0.606/0.645 (RMSE 0.85/0.95 K vs MATLAB) and marked ≈ |
| 5.6 | Labels crowded together; lighting was washed out; equipment looked too small | Priority-based label decluttering, lower exposure, equipment scaled 1.5×, fewer rack posts, zoom-out on narrow screens |
| 5.7 | The user found the interface looked AI-generated | v1.3: full restyle following ISA-101 HMI and engineering-software patterns: model browser, properties grid, readout strip, status bar, report-style Validation and Notes pages, plot-style figures |

## Phase 6 — Documentation and repository (9 Nov)

- Wrote this documentation set (`README.md`, `docs/01–10`) and stage READMEs.
- Added `.gitignore` and `.gitattributes`, and stored the 174 MB dataset and the 56 MB `.mat` file with Git LFS.
- Organised the commits by stage and pushed to `github.com/darshanprajapati07/Absorption_chiller`.
