# 4. Stage 3 — Machine learning

Folder: [`ML_model/`](../ML_model/). How to run: [`ML_model/README.md`](../ML_model/README.md).

## 4.1 Problem formulation

**Task:** predict the time series of 16 chiller outputs from the time series of 7 external inputs.

**Mode:** *simulation mode*. Only the inputs are fed to the model; measured or predicted outputs are never fed back. This is the hardest and most useful setting for a digital twin, because errors cannot be corrected by measurements. The model must carry the plant's state internally.

| Inputs (7) | Targets (16) |
|---|---|
| T_hw_in, m_hw, T_cw_in, m_cw, T_chw_in, m_chw, m_pump | Q_evap, T_chw_out, Q_gen, Q_cond, Q_abs, T_hw_out, T_cw_out, T_gen, T_cond, T_evap, T_abs, x_strong, x_weak, P_high, P_low, m_ref_gen |

A 17th output, **COP_avg30** = ΣQ_evap/ΣQ_gen over a trailing 30 min, is *computed* from the predicted duties. It is not learned separately, so it cannot be tuned.

## 4.2 Data preparation (`ml/data.py`)

| Step | Choice | Reason |
|---|---|---|
| Source | `Transient/output/transient_dataset.csv`, 197 valid runs | — |
| Resampling | Keep rows with time_s % 60 = 0, giving a **60 s step** | The plant time constants are 18–47 min, so 60 s keeps all the dynamics. It also cuts the sequence length six-fold, which makes CPU training feasible |
| Split | By whole run, from the `split` column: **134 train / 29 validation / 34 test** | No leakage between neighbouring time steps. The 5 daily profiles are test-only, to check generalisation to unseen operation |
| Scaling | Per-column z-score. Mean and standard deviation are fitted on the **training runs only** | No information from the test set |
| Warm-up | **60 steps (1 h)** of the first input row are prepended to every sequence | Before t = 0 the plant is at steady state with those inputs. The LSTM starts from a zero state and needs time to reach that steady state. Predictions during warm-up are discarded |
| Batching | Padded sequences with a validity mask. Padding repeats the last input | Runs have different lengths (3–12 h) |

## 4.3 Models compared

| Model | Description | Purpose |
|---|---|---|
| Static GBM | `HistGradientBoostingRegressor` per target, on the current 7 inputs only (600 iterations, learning rate 0.08, 48 leaves, L2 1e-3) | Shows what a model with no memory can do |
| Lag-feature GBM | The same GBM on engineered dynamic features: inputs, lags of 1/2/5/10/20/40 steps, and first-order filters with τ = 5/15/30/60 steps (`ml/baselines.py`) | Strong physics-inspired baseline (FIR/Hammerstein style) |
| **LSTM** | 2-layer LSTM, 128 hidden units, followed by Linear(128,128) → tanh → Linear(128,16) (`ml/models.py`, `SeqNet`) | Recurrent digital twin with internal state |
| **LSTM ensemble** | Mean of 3 LSTMs trained with seeds 0, 1 and 2 | Lower variance. The spread between members serves as a confidence band |

A GRU was tried first. It was 14–76 s per epoch on this CPU, against 1.4–2.4 s for the LSTM, so the LSTM was chosen.

## 4.4 Training (`run_ml.py`, `ml/models.py`)

| Setting | Value |
|---|---|
| Loss | MSE on standardised outputs, masked to valid time steps |
| Optimiser | AdamW, learning rate 3 × 10⁻³, weight decay 1 × 10⁻⁵ |
| Schedule | Cosine annealing to lr/50 over 600 epochs |
| Gradient clipping | Norm 1.0 |
| Batch | 32 full sequences (full-sequence back-propagation through time) |
| Model selection | Validation MSE every 5 epochs; the best checkpoint is kept |
| Threads | 8 CPU threads |
| Training time | 141.7 min for all 3 seeds plus the baselines (≈ 30–47 min per seed) |

| Seed | Best validation MSE (scaled) |
|---|---|
| 0 | 0.00095 |
| 1 | 0.00092 |
| 2 | 0.00094 |

The training curves are in `outputs/figures/training_curves.png`, and the full log in `outputs/training_log.txt` and `outputs/full_run_console.txt`.

## 4.5 Results on the 34 unseen test runs

### Model comparison

| Model | Mean R² | Min R² | Mean NRMSE |
|---|---|---|---|
| Static GBM (no memory) | 0.7449 | −0.663 | 6.09 % |
| Lag-feature GBM | 0.9785 | 0.931 | 2.07 % |
| LSTM (single) | 0.99910 | 0.9953 | 0.39 % |
| **LSTM ensemble (3)** | **0.99914** | **0.9954** | **0.38 %** |

### Best model, per output

| Output | Unit | R² | RMSE | MAE | NRMSE % | MAPE % |
|---|---|---|---|---|---|---|
| Q_evap | kW | 0.99899 | 0.3109 | 0.1254 | 0.430 | 0.173 |
| T_chw_out | °C | 0.99962 | 0.0235 | 0.0105 | 0.373 | 0.120 |
| Q_gen | kW | 0.99845 | 0.7666 | 0.2955 | 0.327 | 0.408 |
| Q_cond | kW | 0.99910 | 0.3455 | 0.1300 | 0.475 | 0.170 |
| Q_abs | kW | 0.99543 | 1.0055 | 0.3043 | 0.478 | 0.447 |
| T_hw_out | °C | 0.99977 | 0.0768 | 0.0350 | 0.249 | 0.038 |
| T_cw_out | °C | 0.99968 | 0.0303 | 0.0123 | 0.356 | 0.036 |
| T_gen | °C | 0.99961 | 0.0869 | 0.0346 | 0.320 | 0.040 |
| T_cond | °C | 0.99925 | 0.0634 | 0.0236 | 0.484 | 0.052 |
| T_evap | °C | 0.99930 | 0.0388 | 0.0151 | 0.478 | — |
| T_abs | °C | 0.99909 | 0.0487 | 0.0166 | 0.593 | 0.049 |
| x_strong | wt% | 0.99985 | 0.0121 | 0.0074 | 0.180 | 0.013 |
| x_weak | wt% | 0.99986 | 0.0096 | 0.0061 | 0.182 | 0.011 |
| P_high | kPa | 0.99924 | 0.0326 | 0.0122 | 0.502 | 0.122 |
| P_low | kPa | 0.99925 | 0.0023 | 0.0009 | 0.483 | 0.110 |
| m_ref_gen | kg/s | 0.99970 | 0.0001 | 0.0000 | 0.268 | — |
| COP_avg30 (derived) | – | 0.99921 | 0.0014 | 0.0009 | 0.314 | — |

MAPE is left blank when the output can be close to zero (T_evap) or is very small (m_ref in kg/s).

**Daily profiles only** (5 × 12 h, never seen in training): mean R² **0.99993**, Q_evap RMSE 0.040 kW, T_chw,out RMSE 0.0035 K.

### R² for every model and output

| Output | Static GBM | Lag GBM | LSTM | LSTM ×3 |
|---|---|---|---|---|
| Q_evap | 0.729 | 0.973 | 0.9989 | 0.9990 |
| T_chw_out | 0.916 | 0.973 | 0.9996 | 0.9996 |
| Q_gen | 0.699 | 0.984 | 0.9984 | 0.9984 |
| Q_cond | 0.913 | 0.982 | 0.9991 | 0.9991 |
| Q_abs | 0.626 | 0.978 | 0.9953 | 0.9954 |
| T_hw_out | 0.983 | 0.996 | 0.9998 | 0.9998 |
| T_cw_out | 0.980 | 0.995 | 0.9997 | 0.9997 |
| T_gen | 0.930 | 0.994 | 0.9996 | 0.9996 |
| T_cond | 0.930 | 0.990 | 0.9992 | 0.9993 |
| T_evap | 0.788 | 0.967 | 0.9993 | 0.9993 |
| T_abs | 0.930 | 0.994 | 0.9991 | 0.9991 |
| x_strong | 0.686 | 0.983 | 0.9998 | 0.9998 |
| x_weak | 0.582 | 0.971 | 0.9998 | 0.9999 |
| P_high | 0.928 | 0.989 | 0.9992 | 0.9992 |
| P_low | 0.788 | 0.963 | 0.9992 | 0.9993 |
| m_ref_gen | 0.920 | 0.972 | 0.9997 | 0.9997 |
| COP_avg30 | −0.663 | 0.931 | 0.9991 | 0.9992 |

### Interpretation

- The static model fails worst on COP (R² < 0), Q_abs and the concentrations. These are exactly the quantities dominated by stored heat and mass.
- Lagged features recover most of the dynamics. They still miss the final steady value after steps, because a fixed set of lags cannot represent slow, state-dependent responses (see `outputs/figures/test_runs_prediction.png`).
- The LSTM follows steps, fast random changes and full days almost exactly. Its weakest output is Q_abs (R² 0.995). This output has short spikes after hot-water drops, which are hard to time.

Figures in `ML_model/outputs/figures/`:
- `model_comparison.png`
- `test_runs_prediction.png`
- `parity_best_model.png`
- `training_curves.png`

## 4.6 Exported artefacts (`export.py`, `outputs/`)

| File | Content |
|---|---|
| `models/lstm_seed{0,1,2}.pt` | PyTorch `state_dict` of each ensemble member |
| `models/scalers_and_meta.json` | Inputs, targets, step, warm-up, scaler means and standard deviations, architecture |
| `models/lstm_portable.json` | Framework-free weights for JavaScript. Per member: `lstm[l] = {W_ih, W_hh, b = b_ih + b_hh}` (PyTorch gate order i, f, g, o) and `head = [{W, b}, {W, b}]` |
| `results/metrics_all_models.csv` | R², RMSE, MAE, NRMSE, MAPE for every model × output |
| `results/model_comparison.csv` | Mean and min R², mean NRMSE per model |
| `results/best_model_metrics.csv` | Per-output metrics of the ensemble |
| `results/summary.json` | Best model and daily-profile metrics |
| `results/test_predictions_best_model.csv` | Inputs, truth and prediction for every test time step |
| `training_log.txt`, `full_run_console.txt` | Complete training logs |

ONNX export is attempted and skipped if the `onnx` package is not installed. The portable JSON is used instead.

## 4.7 Using the model in Python

```python
import json, numpy as np, torch
from ml.models import SeqNet
from ml.data import with_warmup, WARMUP

meta = json.load(open('outputs/models/scalers_and_meta.json'))
nets = []
for s in range(3):
    n = SeqNet(7, 16, hidden=128, layers=2, cell='lstm')
    n.load_state_dict(torch.load(f'outputs/models/lstm_seed{s}.pt')); n.eval(); nets.append(n)

U = np.array(...)                        # (T, 7) inputs at 60 s, physical units
Xn = with_warmup((U - meta['x_mean']) / np.array(meta['x_std'])).astype(np.float32)
with torch.no_grad():
    P = np.mean([n(torch.from_numpy(Xn[None]))[0].numpy() for n in nets], 0)[WARMUP:]
Y = P * np.array(meta['y_std']) + np.array(meta['y_mean'])   # (T, 16) physical units
```
