"""Train, compare and export AI models for transient absorption-chiller prediction.

Usage (from the ML_model folder):
    py -3.12 run_ml.py            # full training (~30-40 min on 8 CPU cores)
    py -3.12 run_ml.py --quick    # short smoke test (~3 min)

Models compared (all predict 16 outputs from the 7 measured inputs):
    Static GBM   - gradient boosting on current inputs only (no dynamics)
    Lag GBM      - gradient boosting on lagged + filtered inputs
    LSTM (x3)    - recurrent digital twin, ensemble of 3 seeds  <- main model
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from ml.data import INPUTS, TARGETS, DT, WARMUP, load_runs, Scaler, with_warmup, cop_avg
from ml.models import train_seqnet, predict
from ml.baselines import lag_features, fit_gbm, predict_gbm

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / 'Transient' / 'output' / 'transient_dataset.csv'
OUT = ROOT / 'outputs'
UNITS = {'Q_evap_kW': 'kW', 'T_chw_out_C': 'C', 'Q_gen_kW': 'kW', 'Q_cond_kW': 'kW', 'Q_abs_kW': 'kW',
         'T_hw_out_C': 'C', 'T_cw_out_C': 'C', 'T_gen_C': 'C', 'T_cond_C': 'C', 'T_evap_C': 'C',
         'T_abs_C': 'C', 'x_strong_wt': 'wt%', 'x_weak_wt': 'wt%', 'P_high_kPa': 'kPa',
         'P_low_kPa': 'kPa', 'm_ref_gen_kg_s': 'kg/s', 'COP_avg30': '-'}


def log(msg):
    print(msg, flush=True)
    with open(OUT / 'training_log.txt', 'a', encoding='utf-8') as f:
        f.write(msg + '\n')


def metrics(y, p):
    """Per-column R2, RMSE, MAE, NRMSE (% of range) and MAPE (if strictly positive)."""
    res = {}
    for j in range(y.shape[1]):
        e = p[:, j] - y[:, j]
        rmse = float(np.sqrt(np.mean(e ** 2)))
        r2 = float(1 - np.sum(e ** 2) / np.sum((y[:, j] - y[:, j].mean()) ** 2))
        rng = float(y[:, j].max() - y[:, j].min())
        mape = float(np.mean(np.abs(e) / np.abs(y[:, j])) * 100) if y[:, j].min() > 0.5 else float('nan')
        res[j] = dict(R2=r2, RMSE=rmse, MAE=float(np.mean(np.abs(e))), NRMSE_pct=rmse / rng * 100, MAPE_pct=mape)
    return res


def add_cop(Y_list):
    """Append COP_avg30 computed from Q_evap and Q_gen of each run."""
    return [np.column_stack([Y, cop_avg(Y[:, 0], Y[:, 2])]) for Y in Y_list]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true')
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    (OUT / 'figures').mkdir(exist_ok=True)
    (OUT / 'training_log.txt').unlink(missing_ok=True)
    torch.set_num_threads(8)
    t0 = time.time()
    epochs = 20 if args.quick else 600
    seeds = [0] if args.quick else [0, 1, 2]

    # ------------------------------------------------------------------ data
    runs = load_runs(DATA)
    tr = [r for r in runs if r['split'] == 'train']
    va = [r for r in runs if r['split'] == 'validation']
    te = [r for r in runs if r['split'] == 'test']
    log(f'Data: {len(runs)} runs at {DT} s  (train {len(tr)}, validation {len(va)}, test {len(te)})')
    sx = Scaler(np.concatenate([r['U'] for r in tr]))
    sy = Scaler(np.concatenate([r['Y'] for r in tr]))
    Ytrue = add_cop([r['Y'] for r in te])
    names = TARGETS + ['COP_avg30']
    preds = {}

    # ------------------------------------------------------------ baselines
    log('\n[1/3] Baselines')
    Xs = np.concatenate([r['U'] for r in tr]); Ys = np.concatenate([r['Y'] for r in tr])
    m_static = fit_gbm(Xs, Ys)
    preds['Static GBM (no memory)'] = add_cop([predict_gbm(m_static, r['U']) for r in te])
    log('    static GBM done')
    Xl = np.concatenate([lag_features(r['U']) for r in tr])
    m_lag = fit_gbm(Xl, Ys)
    preds['Lag-feature GBM'] = add_cop([predict_gbm(m_lag, lag_features(r['U'])) for r in te])
    log('    lag-feature GBM done')

    # ------------------------------------------------------------------ LSTM
    log(f'\n[2/3] LSTM digital twin: 2 x 128 units, {epochs} epochs, ensemble of {len(seeds)} seeds')
    seq = lambda rr: [(with_warmup(sx.fwd(r['U'])), with_warmup(sy.fwd(r['Y']))) for r in rr]
    S_tr, S_va = seq(tr), seq(va)
    nets, hists = [], []
    for s in seeds:
        net, hist = train_seqnet(S_tr, S_va, len(INPUTS), len(TARGETS), 'lstm', 128, 2,
                                 epochs=epochs, batch=32, lr=3e-3, seed=s, log=log)
        nets.append(net); hists.append(hist)
        log(f'    seed {s} best validation MSE {min(h[2] for h in hist):.5f}  ({(time.time() - t0) / 60:.1f} min)')

    def lstm_predict(U, members):
        Xn = with_warmup(sx.fwd(U))
        P = np.mean([predict(n, Xn) for n in members], 0)[WARMUP:]
        return sy.inv(P)

    preds['LSTM (single)'] = add_cop([lstm_predict(r['U'], nets[:1]) for r in te])
    if len(nets) > 1:
        preds[f'LSTM ensemble ({len(nets)})'] = add_cop([lstm_predict(r['U'], nets) for r in te])

    # ------------------------------------------------------------ evaluation
    log('\n[3/3] Test-set evaluation (34 unseen runs incl. 5 daily profiles)')
    yt = np.concatenate(Ytrue)
    summary = {}
    for name, P in preds.items():
        m = metrics(yt, np.concatenate(P))
        summary[name] = m
        r2 = np.mean([m[j]['R2'] for j in range(len(names))])
        nr = np.mean([m[j]['NRMSE_pct'] for j in range(len(names))])
        log(f'  {name:26s} mean R2 {r2:.5f}   mean NRMSE {nr:.3f} %')
    best = max(summary, key=lambda k: np.mean([summary[k][j]['R2'] for j in range(len(names))]))
    log(f'\n  BEST MODEL: {best}')
    bm = summary[best]
    log(f'  {"Output":18s} {"unit":>5s} {"R2":>9s} {"RMSE":>9s} {"MAE":>9s} {"NRMSE%":>8s} {"MAPE%":>8s}')
    for j, n in enumerate(names):
        log(f'  {n:18s} {UNITS[n]:>5s} {bm[j]["R2"]:9.5f} {bm[j]["RMSE"]:9.4f} {bm[j]["MAE"]:9.4f} '
            f'{bm[j]["NRMSE_pct"]:8.3f} {bm[j]["MAPE_pct"]:8.3f}')
    # generalisation: daily profiles only
    di = [i for i, r in enumerate(te) if r['type'] == 'daily']
    md = metrics(np.concatenate([Ytrue[i] for i in di]), np.concatenate([preds[best][i] for i in di]))
    log(f'  Daily-profile runs only (12 h, never seen in training): mean R2 {np.mean([md[j]["R2"] for j in md]):.5f}, '
        f'Q_evap RMSE {md[0]["RMSE"]:.3f} kW, T_chw_out RMSE {md[1]["RMSE"]:.4f} C')

    # ---------------------------------------------------------------- export
    import export
    export.save_all(OUT, nets, sx, sy, summary, names, UNITS, best, preds, Ytrue, te, hists, md)
    log(f'\nDone in {(time.time() - t0) / 60:.1f} min. Results in {OUT}')


if __name__ == '__main__':
    main()
