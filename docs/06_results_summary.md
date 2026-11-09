# 6. Results summary

All key numbers of the project in one place. The detailed tables are in docs 02–05.

## 6.1 Aspen Plus steady state

| Item | Before | After |
|---|---|---|
| Energy residual of the overall control volume | +42,437.9 kcal/h (tear mismatch) plus a hidden −206,253.5 kcal/h in DFLASH | **85.6 kcal/h (0.046 %)** |
| COP | 0.213 (spreadsheet) | **0.611** (validation run); **0.608** (final base case with pressure masters) |
| COP trend vs generator T | falling (wrong) | rising (correct) |
| Blocks added or removed, property method changed | — | none |

## 6.2 Steady-state dataset (SENS-1)

| Item | Value |
|---|---|
| Cases run | 241 (8 T_gen × 5 P_high × 6 P_low, plus the base case), all converged |
| Rejected | 78 (x_strong > 64 wt%) |
| **Valid** | **163** |
| COP range | 0.227–0.791 |
| Energy residual | ≤ 0.24 %, mean 0.025–0.036 % |
| Independent checks | 15 / 15 passed (absorber offset −2.1 K vs ASHRAE stated as a limitation) |

## 6.3 Dynamic model

| Item | Value |
|---|---|
| States vs Aspen base case | identical (Δ ≤ 0.001) |
| Q_evap vs Aspen | 0.00 % |
| Q_gen, Q_abs vs Aspen | +3.3 %, +3.2 % (ASHRAE vs ELECNRTL enthalpy) |
| COP model / Aspen | 0.589 / 0.608 |
| COP vs 163 SENS-1 cases | R = 0.9998, mean \|err\| 0.026 |
| Hot water +10 K step | Q_evap 81.1 → 93.6 kW, t63 = 18.2 min, t95 = 46.5 min |

## 6.4 Transient dataset

| Item | Value |
|---|---|
| Runs simulated / valid | 199 / 197 |
| Rows, sample time, columns | 291,437, 10 s, 40 |
| Split (by run) | 134 / 29 / 34 |
| Max energy conservation error | 0.032 % |
| Generation time | 4.8 min |

## 6.5 AI model (34 unseen test runs)

| Model | Mean R² | Mean NRMSE |
|---|---|---|
| Static gradient boosting | 0.7449 | 6.09 % |
| Lag-feature gradient boosting | 0.9785 | 2.07 % |
| LSTM, one seed | 0.99910 | 0.39 % |
| **LSTM ensemble of 3 (final)** | **0.99914** | **0.38 %** |

| Key output | RMSE | R² |
|---|---|---|
| Cooling capacity Q_evap | 0.31 kW | 0.9990 |
| Chilled-water supply T_chw,out | 0.024 K | 0.9996 |
| Generator heat Q_gen | 0.77 kW | 0.9984 |
| Strong solution x_strong | 0.012 wt% | 0.9998 |
| COP_avg30 (derived) | 0.0014 | 0.9992 |
| 12 h daily profiles (all outputs) | — | 0.99993 |

## 6.6 Digital twin

| Item | Value |
|---|---|
| JavaScript vs PyTorch, max difference | 0.0014 kW |
| Inference | ≈ 1.5 ms per 60 s step (3 networks) |
| Stability | 50 h constant inputs, drift < 0.003 kW |
| Page size | ≈ 4 MB, single file |
