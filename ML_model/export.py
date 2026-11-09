"""Save trained models, metrics, predictions and figures."""
import json

import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ml.data import INPUTS, TARGETS, DT, WARMUP


def _r(a, d=6):
    return np.round(np.asarray(a, dtype=float), d).tolist()


def save_all(out, nets, sx, sy, summary, names, units, best, preds, Ytrue, te, hists, daily):
    mdir, rdir, fdir = out / 'models', out / 'results', out / 'figures'
    mdir.mkdir(exist_ok=True); rdir.mkdir(exist_ok=True); fdir.mkdir(exist_ok=True)

    # ---- models: PyTorch weights + scalers + portable JSON (for the dashboard)
    meta = dict(inputs=INPUTS, targets=TARGETS, dt_s=DT, warmup_steps=WARMUP,
                x_mean=_r(sx.mean), x_std=_r(sx.std), y_mean=_r(sy.mean), y_std=_r(sy.std),
                architecture='LSTM 2x128 + Linear(128,128)-tanh-Linear(128,16), simulation mode',
                ensemble=len(nets))
    (mdir / 'scalers_and_meta.json').write_text(json.dumps(meta, indent=1))
    portable = dict(meta=meta, members=[])
    for i, n in enumerate(nets):
        torch.save(n.state_dict(), mdir / f'lstm_seed{i}.pt')
        sd = {k: v.numpy() for k, v in n.state_dict().items()}
        layers = [dict(W_ih=_r(sd[f'rnn.weight_ih_l{l}']), W_hh=_r(sd[f'rnn.weight_hh_l{l}']),
                       b=_r(sd[f'rnn.bias_ih_l{l}'] + sd[f'rnn.bias_hh_l{l}'])) for l in range(n.rnn.num_layers)]
        portable['members'].append(dict(lstm=layers, head=[dict(W=_r(sd['head.0.weight']), b=_r(sd['head.0.bias'])),
                                                           dict(W=_r(sd['head.2.weight']), b=_r(sd['head.2.bias']))]))
    (mdir / 'lstm_portable.json').write_text(json.dumps(portable, separators=(',', ':')))
    try:
        dummy = torch.zeros(1, 300, len(INPUTS))
        torch.onnx.export(nets[0], dummy, mdir / 'lstm_seed0.onnx', input_names=['inputs_scaled'],
                          output_names=['outputs_scaled'], dynamic_axes={'inputs_scaled': {1: 'time'}},
                          dynamo=False)
    except Exception as e:  # ONNX is optional
        print(f'    (ONNX export skipped: {e})')

    # ---- metrics tables
    rows = []
    for model, m in summary.items():
        for j, n in enumerate(names):
            rows.append(dict(model=model, output=n, unit=units[n], **m[j]))
    df = pd.DataFrame(rows)
    df.to_csv(rdir / 'metrics_all_models.csv', index=False)
    comp = df.groupby('model', sort=False).agg(mean_R2=('R2', 'mean'), min_R2=('R2', 'min'),
                                               mean_NRMSE_pct=('NRMSE_pct', 'mean')).reset_index()
    comp.to_csv(rdir / 'model_comparison.csv', index=False)
    df[df.model == best].to_csv(rdir / 'best_model_metrics.csv', index=False)
    json.dump(dict(best_model=best, daily_profiles={names[j]: daily[j] for j in daily}),
              open(rdir / 'summary.json', 'w'), indent=1)

    # ---- test predictions of the best model
    recs = []
    for i, r in enumerate(te):
        d = pd.DataFrame({'run_id': r['run_id'], 'scenario_type': r['type'], 'time_s': r['t']})
        for k, n in enumerate(INPUTS):
            d[n] = r['U'][:, k]
        for j, n in enumerate(names):
            d[n + '_true'] = Ytrue[i][:, j]
            d[n + '_pred'] = preds[best][i][:, j]
        recs.append(d)
    pd.concat(recs).to_csv(rdir / 'test_predictions_best_model.csv', index=False)

    # ---- figures
    plt.rcParams.update({'figure.dpi': 130, 'axes.grid': True, 'grid.alpha': 0.3})
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    ax[0].barh(comp.model, comp.mean_R2, color='#2a7fbf'); ax[0].set_xlim(min(0.9, comp.mean_R2.min() - 0.01), 1)
    ax[0].set_title('Mean R² on test runs (higher is better)')
    ax[1].barh(comp.model, comp.mean_NRMSE_pct, color='#e07b39'); ax[1].set_title('Mean NRMSE % (lower is better)')
    fig.tight_layout(); fig.savefig(fdir / 'model_comparison.png'); plt.close(fig)

    show = [0, 1, 2, len(names) - 1]
    pick = [next(i for i, r in enumerate(te) if r['type'] == t) for t in ['aprbs', 'step', 'daily']
            if any(r['type'] == t for r in te)]
    others = [k for k in preds if k != best and 'Lag' in k]
    fig, axs = plt.subplots(len(pick), len(show), figsize=(16, 3.2 * len(pick)), squeeze=False)
    for a, i in enumerate(pick):
        th = te[i]['t'] / 3600
        for b, j in enumerate(show):
            axx = axs[a, b]
            axx.plot(th, Ytrue[i][:, j], 'k', lw=2, label='Simulation (truth)')
            axx.plot(th, preds[best][i][:, j], color='#2a7fbf', lw=1.4, ls='--', label=best)
            for o in others:
                axx.plot(th, preds[o][i][:, j], color='#e07b39', lw=1, alpha=0.8, label=o)
            axx.set_title(f'{te[i]["type"]} run {te[i]["run_id"]}: {names[j]}', fontsize=9)
            if a == len(pick) - 1:
                axx.set_xlabel('time [h]')
    axs[0, 0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(fdir / 'test_runs_prediction.png'); plt.close(fig)

    yt = np.concatenate(Ytrue); yp = np.concatenate(preds[best])
    fig, axs = plt.subplots(2, 4, figsize=(15, 7))
    for axx, j in zip(axs.ravel(), [0, 1, 2, 3, 4, 9, 11, len(names) - 1]):
        axx.plot(yt[:, j], yp[:, j], '.', ms=1.5, alpha=0.4)
        lim = [yt[:, j].min(), yt[:, j].max()]; axx.plot(lim, lim, 'k--', lw=1)
        axx.set_title(f'{names[j]}  R²={summary[best][j]["R2"]:.4f}', fontsize=9)
        axx.set_xlabel('true'); axx.set_ylabel('predicted')
    fig.suptitle(f'Parity plots, test runs: {best}'); fig.tight_layout()
    fig.savefig(fdir / 'parity_best_model.png'); plt.close(fig)

    fig, axx = plt.subplots(figsize=(7, 4))
    for s, h in enumerate(hists):
        h = np.array(h); axx.semilogy(h[:, 0], h[:, 1], lw=1, label=f'train seed {s}')
        axx.semilogy(h[:, 0], h[:, 2], lw=1, ls='--', label=f'validation seed {s}')
    axx.set_xlabel('epoch'); axx.set_ylabel('MSE (scaled)'); axx.legend(fontsize=7); axx.set_title('LSTM training curves')
    fig.tight_layout(); fig.savefig(fdir / 'training_curves.png'); plt.close(fig)
