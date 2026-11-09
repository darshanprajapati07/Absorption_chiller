# AI model: transient prediction for a single-effect H2O-LiBr absorption chiller

An LSTM "digital twin" that predicts 16 chiller outputs, plus the 30-min average COP, over time. It uses only the 7 measured external inputs (hot, cooling and chilled water temperatures and flows, and the solution pump flow). It was trained on the MATLAB transient dataset (`../Transient/output/transient_dataset.csv`), which is calibrated to the Aspen Plus steady state.

## How to run

```
cd ML_model
py -3.12 run_ml.py            # full training (about 2.4 h on this laptop CPU)
py -3.12 run_ml.py --quick    # smoke test (about 5 min)
```

Requirements: Python 3.12. Install the packages with `pip install -r requirements.txt` (numpy, pandas, scikit-learn, torch, matplotlib). On Linux or macOS, use `python` instead of `py -3.12`.

## Method

| Item | Choice |
|---|---|
| Data | 197 valid runs (steps, ramps, startup/shutdown, APRBS, 12-h daily profiles), resampled to 60 s |
| Split | By run: 134 train, 29 validation, 34 test. All 5 daily profiles are test-only. |
| Inputs (7) | T_hw_in, m_hw, T_cw_in, m_cw, T_chw_in, m_chw, m_pump |
| Outputs (16) | Q_evap, T_chw_out, Q_gen, Q_cond, Q_abs, T_hw_out, T_cw_out, T_gen, T_cond, T_evap, T_abs, x_strong, x_weak, P_high, P_low, m_ref |
| Derived | COP_avg30 = ΣQ_evap / ΣQ_gen over a trailing 30 min, computed from the predicted Q values (no extra fitting) |
| Main model | 2-layer LSTM (128 units) + MLP head, simulation mode: the model never sees measured outputs, only inputs. 1 h steady-state warm-up. |
| Training | Full-sequence BPTT, AdamW, cosine learning rate, 600 epochs; best-on-validation checkpoint; ensemble of 3 seeds |
| Baselines | Static gradient boosting (current inputs only) and lag/filter-feature gradient boosting |
| Scaling | z-score, fitted on training runs only (no leakage) |

## Results on 34 unseen test runs

| Model | Mean R² | Min R² | Mean NRMSE |
|---|---|---|---|
| Static GBM (no memory) | 0.7449 | -0.663 | 6.09 % |
| Lag-feature GBM | 0.9785 | 0.931 | 2.07 % |
| LSTM (single) | 0.99910 | 0.9953 | 0.39 % |
| **LSTM ensemble (3)** | **0.99914** | **0.9954** | **0.38 %** |

Selected outputs for the best model:
- Q_evap: RMSE 0.31 kW, MAPE 0.17 %
- T_chw_out: RMSE 0.024 °C
- Q_gen: RMSE 0.77 kW
- x_strong: RMSE 0.012 wt%
- COP_avg30: RMSE 0.0014

On the 12-h daily profiles alone (never seen in training), the mean R² is 0.99993.

The full per-output table is in `outputs/results/best_model_metrics.csv`.

**Limitation:** these metrics compare the model against the physics-based simulator, not against plant measurements. They show that the AI reproduces the lumped-parameter model's dynamics. Accuracy against a real chiller depends on how well that model represents the plant.

## Outputs

- `outputs/models/`:
  - `lstm_seed{0,1,2}.pt` (PyTorch weights);
  - `scalers_and_meta.json`;
  - `lstm_portable.json`, the weights and scalers that the dashboard uses to run the model in the browser.
- `outputs/results/`:
  - metric tables;
  - `summary.json`;
  - `test_predictions_best_model.csv`.
- `outputs/figures/`:
  - model comparison;
  - test-run predictions;
  - parity plots;
  - training curves.
- `outputs/training_log.txt`: the full log.

The full documentation is in [docs/04_machine_learning.md](../docs/04_machine_learning.md).
