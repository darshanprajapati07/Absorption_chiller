"""Draws the figures of the AI/ML final report from the project's own data and trained networks.

Usage (from the Report folder):  py -3.12 make_ml_figures.py
Writes figures/ml_*.png and figures/ml_numbers.json (numbers quoted in the text).
"""
import json
import re
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ML = ROOT / 'ML_model'
sys.path.insert(0, str(ML))
from ml.data import INPUTS, TARGETS, WARMUP, load_runs, with_warmup  # noqa: E402
from ml.models import SeqNet  # noqa: E402

FIG = HERE / 'figures'
BLUE, ORANGE, GREY, BLACK = '#1f4e9a', '#d9822b', '#8a8a8a', '#111111'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 9,
                     'axes.grid': True, 'grid.alpha': .3, 'grid.linewidth': .6,
                     'axes.spines.top': False, 'axes.spines.right': False})
NICE = {'T_hw_in_C': 'Hot water in, °C', 'm_hw_kg_s': 'Hot water flow, kg/s', 'T_cw_in_C': 'Cooling water in, °C',
        'm_cw_kg_s': 'Cooling water flow, kg/s', 'T_chw_in_C': 'Chilled water return, °C',
        'm_chw_kg_s': 'Chilled water flow, kg/s', 'm_pump_kg_s': 'Solution pump, kg/s'}
SHORT = {'Q_evap_kW': 'Cooling output', 'T_chw_out_C': 'Chilled water out', 'Q_gen_kW': 'Heat input',
         'Q_cond_kW': 'Condenser duty', 'Q_abs_kW': 'Absorber duty', 'T_hw_out_C': 'Hot water out',
         'T_cw_out_C': 'Cooling water out', 'T_gen_C': 'Generator temp.', 'T_cond_C': 'Condenser temp.',
         'T_evap_C': 'Evaporator temp.', 'T_abs_C': 'Absorber temp.', 'x_strong_wt': 'Strong solution conc.',
         'x_weak_wt': 'Weak solution conc.', 'P_high_kPa': 'High pressure', 'P_low_kPa': 'Low pressure',
         'm_ref_gen_kg_s': 'Refrigerant flow', 'COP_avg30': 'COP (30 min)'}
NUM = {}


def save(fig, name):
    fig.savefig(FIG / name, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('  wrote', name)


# ------------------------------------------------------------------ load data, scalers and networks
meta = json.load(open(ML / 'outputs/models/scalers_and_meta.json'))
xm, xs = np.array(meta['x_mean'], np.float32), np.array(meta['x_std'], np.float32)
ym, ys = np.array(meta['y_mean'], np.float32), np.array(meta['y_std'], np.float32)
nets = []
for s in range(3):
    n = SeqNet(7, 16, hidden=128, layers=2, cell='lstm')
    n.load_state_dict(torch.load(ML / f'outputs/models/lstm_seed{s}.pt'))
    n.eval(); nets.append(n)
torch.set_num_threads(8)


def run_members(U, warm=True):
    """Return (3, T, 16) predictions in physical units for input array U (T, 7)."""
    X = (U - xm) / xs
    if warm:
        X = with_warmup(X)
    X = torch.from_numpy(X.astype(np.float32)[None])
    with torch.no_grad():
        P = np.stack([n(X)[0].numpy() for n in nets])
    if warm:
        P = P[:, WARMUP:]
    return P * ys + ym


print('loading dataset ...')
runs = load_runs(ROOT / 'Transient/output/transient_dataset.csv')
test = [r for r in runs if r['split'] == 'test']
train = [r for r in runs if r['split'] == 'train']
u0 = np.array([105.0, 4.1128, 27.0, 9.0286, 12.0, 3.8756, 1.0], np.float32)

# ------------------------------------------------------------------ 1. architecture / simulation-mode diagram
print('fig: architecture')
fig, ax = plt.subplots(figsize=(11, 3.3))
ax.set_xlim(0, 110); ax.set_ylim(0, 33); ax.axis('off'); ax.grid(False)
blocks = [(1, '7 inputs', 'temperatures,\nflows, pump\n(every 60 s)', '#f3f3f1'),
          (17, 'Scaling', 'z-score with\ntraining-set\nmean and std', '#f3f3f1'),
          (33, 'LSTM layer 1', '128 memory\ncells', '#e6edf7'),
          (49, 'LSTM layer 2', '128 memory\ncells', '#e6edf7'),
          (65, 'Dense head', '128 → tanh\n→ 16', '#f3f3f1'),
          (81, 'Un-scaling', 'back to kW,\n°C, kPa, wt%', '#f3f3f1'),
          (97, '16 outputs', 'duties, temps,\npressures,\nconcentrations', '#f3f3f1')]
w, h, y0 = 12.5, 15, 11
for i, (x, t, s, c) in enumerate(blocks):
    ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle='square,pad=0', fc=c, ec='#222', lw=1))
    ax.text(x + w / 2, y0 + h - 2.6, t, ha='center', va='center', weight='bold', fontsize=8.6)
    ax.text(x + w / 2, y0 + h / 2 - 1.8, s, ha='center', va='center', fontsize=7.4, color='#333', linespacing=1.35)
    if i < len(blocks) - 1:
        ax.annotate('', xy=(x + w + 3.3, y0 + h / 2), xytext=(x + w + 0.2, y0 + h / 2),
                    arrowprops=dict(arrowstyle='-|>', color='#222', lw=1))
for x in (33, 49):   # recurrent self-loops: the memory carried to the next minute
    ax.annotate('', xy=(x + w * .3, y0 + h + .2), xytext=(x + w * .7, y0 + h + .2),
                arrowprops=dict(arrowstyle='-|>', color=BLUE, lw=1.1, connectionstyle='arc3,rad=1.6'))
ax.text(47.25, 31.5, 'state (h, c) carried to the next minute', ha='center', fontsize=7.6, color=BLUE, style='italic')
ax.plot([33, 74.5], [8.5, 8.5], color='#555', lw=.8)
ax.text(53.75, 6, 'three copies (seeds 0, 1, 2) trained separately, outputs averaged', ha='center', fontsize=7.6,
        color='#444')
ax.text(55, 1.5, 'Outputs are never fed back: the network keeps track of the plant on its own ("simulation mode").',
        ha='center', fontsize=7.8, color='#444', style='italic')
save(fig, 'ml_arch.png')

# ------------------------------------------------------------------ 2. dataset split
print('fig: split + coverage')
order = ['aprbs', 'step', 'ramp', 'startup', 'shutdown', 'daily']
label = {'aprbs': 'random\nsequences', 'step': 'steps', 'ramp': 'ramps', 'startup': 'start-up',
         'shutdown': 'shut-down', 'daily': 'daily\nprofiles'}
cnt = {sp: [sum(1 for r in runs if r['type'] == t and r['split'] == sp) for t in order]
       for sp in ('train', 'validation', 'test')}
fig, axs = plt.subplots(1, 2, figsize=(11, 3.0), gridspec_kw=dict(width_ratios=[1.05, 1]))
ax = axs[0]
x = np.arange(len(order)); bw = .26
for k, (sp, c) in enumerate([('train', '#9bb3d6'), ('validation', GREY), ('test', BLUE)]):
    b = ax.bar(x + (k - 1) * bw, cnt[sp], bw, color=c, label=f'{sp} ({sum(cnt[sp])})')
    for xi, v in zip(x + (k - 1) * bw, cnt[sp]):
        if v:
            ax.text(xi, v + 1.5, str(v), ha='center', fontsize=7)
ax.set_xticks(x, [label[t] for t in order], fontsize=8); ax.set_ylabel('number of runs')
ax.set_title('(a) Runs per scenario type and split'); ax.legend(fontsize=7.5, frameon=False); ax.grid(axis='x', visible=False)
ax = axs[1]
rows_per = {sp: sum(len(r['t']) for r in runs if r['split'] == sp) for sp in cnt}
hours = {sp: sum(r['t'][-1] / 3600 for r in runs if r['split'] == sp) for sp in cnt}
ax.barh(['train', 'validation', 'test'], [hours[s] for s in ('train', 'validation', 'test')],
        color=['#9bb3d6', GREY, BLUE])
for i, s in enumerate(('train', 'validation', 'test')):
    ax.text(hours[s] + 6, i, f'{hours[s]:.0f} h  ·  {rows_per[s]:,} steps of 60 s', va='center', fontsize=7.8)
ax.set_xlim(0, max(hours.values()) * 1.6); ax.invert_yaxis(); ax.set_xlabel('simulated plant time, hours')
ax.set_title('(b) Amount of data seen by the model'); ax.grid(axis='y', visible=False)
fig.tight_layout(); save(fig, 'ml_split.png')
NUM['hours'] = hours; NUM['rows60'] = rows_per

# ------------------------------------------------------------------ 3. input coverage train vs test
Utr = np.concatenate([r['U'] for r in train]); Ute = np.concatenate([r['U'] for r in test])
fig, axs = plt.subplots(1, 7, figsize=(12, 2.0))
for k, ax in enumerate(axs):
    lo, hi = min(Utr[:, k].min(), Ute[:, k].min()), max(Utr[:, k].max(), Ute[:, k].max())
    bins = np.linspace(lo, hi, 26)
    ax.hist(Utr[:, k], bins, density=True, color='#9bb3d6', label='train')
    ax.hist(Ute[:, k], bins, density=True, histtype='step', color=BLACK, lw=1, label='test')
    ax.set_title(NICE[INPUTS[k]], fontsize=7.4); ax.set_yticks([]); ax.tick_params(labelsize=6.5)
    ax.grid(False); ax.spines['left'].set_visible(False)
axs[0].legend(fontsize=6.5, frameon=False, loc='upper left')
fig.tight_layout(w_pad=.6); save(fig, 'ml_coverage.png')

# ------------------------------------------------------------------ 4. training curves from the log
print('fig: training curves')
log = (ML / 'outputs/training_log.txt').read_text(encoding='utf-8')
seeds, cur = [], None
for line in log.splitlines():
    m = re.search(r'lstm epoch\s+(\d+)\s+train MSE ([\d.]+)\s+val MSE ([\d.]+)', line)
    if m:
        ep = int(m.group(1))
        if ep == 25:
            cur = []; seeds.append(cur)
        cur.append((ep, float(m.group(2)), float(m.group(3))))
fig, axs = plt.subplots(1, 2, figsize=(10, 3.0))
cols = [BLUE, ORANGE, '#4d8b3f']
for s, h in enumerate(seeds):
    h = np.array(h)
    axs[0].semilogy(h[:, 0], h[:, 1], color=cols[s], lw=1.2, label=f'seed {s} train')
    axs[0].semilogy(h[:, 0], h[:, 2], color=cols[s], lw=1.2, ls='--', label=f'seed {s} validation')
axs[0].set_xlabel('epoch'); axs[0].set_ylabel('mean squared error (scaled)')
axs[0].set_title('(a) Loss during training'); axs[0].legend(fontsize=6.8, ncol=2, frameon=False)
ep = np.arange(1, 601); lr = 3e-3 / 50 + (3e-3 - 3e-3 / 50) * (1 + np.cos(np.pi * ep / 600)) / 2
axs[1].plot(ep, lr * 1e3, color=BLACK, lw=1.2)
axs[1].set_xlabel('epoch'); axs[1].set_ylabel('learning rate (× 10⁻³)'); axs[1].set_title('(b) Cosine learning-rate schedule')
fig.tight_layout(); save(fig, 'ml_curves.png')
NUM['val_best'] = [min(x[2] for x in h) for h in seeds]

# ------------------------------------------------------------------ 5. model comparison per output
print('fig: comparison')
mall = pd.read_csv(ML / 'outputs/results/metrics_all_models.csv')
models = ['Static GBM (no memory)', 'Lag-feature GBM', 'LSTM ensemble (3)']
mlab = {'Static GBM (no memory)': 'Gradient boosting, no memory', 'Lag-feature GBM': 'Gradient boosting + input history',
        'LSTM ensemble (3)': 'LSTM ensemble (final)'}
outs = list(mall[mall.model == models[0]].output)
fig, ax = plt.subplots(figsize=(10.5, 4.0))
yy = np.arange(len(outs))
for m, c, mk in zip(models, [GREY, ORANGE, BLUE], ['s', 'D', 'o']):
    v = mall[mall.model == m].set_index('output').loc[outs, 'NRMSE_pct'].values
    ax.plot(v, yy, mk, color=c, ms=5, label=mlab[m], ls='none')
ax.set_xscale('log'); ax.set_yticks(yy, [SHORT[o] for o in outs], fontsize=7.8); ax.invert_yaxis()
ax.set_xlabel('error on unseen test runs: RMSE as % of the output\'s range (log scale, lower is better)')
ax.legend(fontsize=7.8, frameon=False, loc='lower center', bbox_to_anchor=(.5, 1.0), ncol=3); ax.grid(axis='y', visible=False)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:g}'))
fig.tight_layout(); save(fig, 'ml_compare.png')

# ------------------------------------------------------------------ ensemble predictions on all test runs
print('running the 3 networks on the 34 test runs ...')
P_all = [run_members(r['U']) for r in test]
Y_all = [r['Y'] for r in test]

# timing (Python, per 60 s step, whole ensemble)
U = test[0]['U']; t0 = time.perf_counter()
for _ in range(3):
    run_members(U)
NUM['py_ms_per_step'] = (time.perf_counter() - t0) / 3 / (len(U) + WARMUP) * 1e3

# ------------------------------------------------------------------ 6. parity
print('fig: parity')
yt = np.concatenate(Y_all); yp = np.concatenate([p.mean(0) for p in P_all])
pick = [('Q_evap_kW', 'Cooling output, kW'), ('T_chw_out_C', 'Chilled water out, °C'),
        ('Q_abs_kW', 'Absorber duty, kW'), ('x_strong_wt', 'Strong solution, wt% LiBr')]
fig, axs = plt.subplots(1, 4, figsize=(11.5, 2.9))
for ax, (c, lab) in zip(axs, pick):
    j = TARGETS.index(c)
    ax.plot(yt[:, j], yp[:, j], '.', ms=1.4, alpha=.35, color=BLUE, rasterized=True)
    lim = [yt[:, j].min(), yt[:, j].max()]; ax.plot(lim, lim, color=BLACK, lw=.8, ls='--')
    r2 = 1 - np.sum((yp[:, j] - yt[:, j]) ** 2) / np.sum((yt[:, j] - yt[:, j].mean()) ** 2)
    ax.set_title(f'{lab}\nR² = {r2:.4f}', fontsize=8.3); ax.set_xlabel('dynamic model (truth)', fontsize=8)
axs[0].set_ylabel('LSTM prediction', fontsize=8)
fig.tight_layout(); save(fig, 'ml_parity.png')

# ------------------------------------------------------------------ 7. one daily profile: inputs + outputs
print('fig: daily profile')
iday = next(i for i, r in enumerate(test) if r['type'] == 'daily')
r, P = test[iday], P_all[iday]
th = r['t'] / 3600
fig, axs = plt.subplots(2, 3, figsize=(11.5, 4.6), sharex=True)
for ax, k in zip(axs[0], [0, 2, 4]):
    ax.plot(th, r['U'][:, k], color=BLACK, lw=1)
    ax.set_title('input: ' + NICE[INPUTS[k]], fontsize=8.3)
for ax, c, lab in zip(axs[1], ['Q_evap_kW', 'T_chw_out_C', 'Q_gen_kW'],
                      ['Cooling output, kW', 'Chilled water out, °C', 'Heat input, kW']):
    j = TARGETS.index(c)
    ax.plot(th, r['Y'][:, j], color=BLACK, lw=2.0, label='dynamic model (truth)')
    ax.plot(th, P.mean(0)[:, j], color=BLUE, lw=1.1, ls='--', label='LSTM prediction')
    ax.set_title('output: ' + lab, fontsize=8.3); ax.set_xlabel('time of the run, hours')
axs[1, 0].legend(fontsize=7, frameon=False)
fig.tight_layout(); save(fig, 'ml_daily.png')
NUM['daily_run'] = int(r['run_id'])

# ------------------------------------------------------------------ 8. error by scenario type and by horizon
print('fig: error analysis')
rng_all = yt.max(0) - yt.min(0)
types = ['aprbs', 'step', 'ramp', 'startup', 'daily']
per_type = {}
for t in types:
    idx = [i for i, rr in enumerate(test) if rr['type'] == t]
    e = np.concatenate([P_all[i].mean(0) - Y_all[i] for i in idx])
    per_type[t] = (np.sqrt((e ** 2).mean(0)) / rng_all * 100).mean()
NUM['nrmse_by_type'] = per_type
NUM['runs_by_type'] = {t: sum(1 for rr in test if rr['type'] == t) for t in types}
fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.0))
ax = axs[0]
ax.bar([label[t].replace('\n', ' ') for t in types], [per_type[t] for t in types], color=BLUE, width=.55)
for i, t in enumerate(types):
    ax.text(i, per_type[t] + .01, f'{per_type[t]:.2f}', ha='center', fontsize=7.5)
ax.set_ylabel('mean error, % of range'); ax.set_title('(a) Error by kind of test run'); ax.grid(axis='x', visible=False)
ax.tick_params(axis='x', labelsize=7.8)
ax = axs[1]
j = TARGETS.index('Q_evap_kW')
bins = np.arange(0, 13)
med, p90 = [], []
for b in bins[:-1]:
    ee = np.concatenate([np.abs(P_all[i].mean(0)[:, j] - Y_all[i][:, j])[(test[i]['t'] / 3600 >= b) &
                                                                       (test[i]['t'] / 3600 < b + 1)]
                         for i in range(len(test)) if test[i]['type'] == 'daily'])
    med.append(np.median(ee)); p90.append(np.percentile(ee, 90))
ax.plot(bins[:-1] + .5, p90, 'o-', color=ORANGE, ms=3.5, lw=1, label='90th percentile')
ax.plot(bins[:-1] + .5, med, 'o-', color=BLUE, ms=3.5, lw=1, label='median')
ax.set_ylim(0, max(p90) * 1.4)

ax.set_xlabel('hours since the start of the run'); ax.set_ylabel('cooling-output error, kW')
ax.set_title('(b) Error through the five 12-hour test days'); ax.legend(fontsize=7.5, frameon=False)
fig.tight_layout(); save(fig, 'ml_errors.png')

# ------------------------------------------------------------------ 9. ensemble spread as a confidence signal
print('fig: ensemble')
ia = next(i for i, rr in enumerate(test) if rr['type'] == 'aprbs')
r, P = test[ia], P_all[ia]
j = TARGETS.index('Q_abs_kW')
th = r['t'] / 3600
fig, axs = plt.subplots(1, 2, figsize=(11, 3.0), gridspec_kw=dict(width_ratios=[1.6, 1]))
ax = axs[0]
win = (th >= 1.75) & (th <= 2.25)
ax.fill_between(th[win] * 60, P[:, win, j].min(0), P[:, win, j].max(0), color=BLUE, alpha=.3, lw=0,
                label='spread of the 3 networks')
ax.plot(th[win] * 60, r['Y'][win, j], color=BLACK, lw=1.6, label='dynamic model (truth)')
ax.plot(th[win] * 60, P[:, win, j].mean(0), color=BLUE, lw=1, ls='--', label='ensemble mean')
ax.set_xlabel('time, minutes'); ax.set_ylabel('absorber duty, kW')
ax.set_title(f'(a) Test run {r["run_id"]} (random inputs), 30-minute close-up')
ax.legend(fontsize=7, frameon=False)
spread = np.concatenate([(p.max(0) - p.min(0)) / rng_all for p in P_all]).mean(1)
err = np.concatenate([np.abs(p.mean(0) - y) / rng_all for p, y in zip(P_all, Y_all)]).mean(1)
qs = np.quantile(spread, np.linspace(0, 1, 11))
cb = np.clip(np.digitize(spread, qs[1:-1]), 0, 9)
ax = axs[1]
ax.bar(np.arange(10) + 1, [err[cb == k].mean() * 100 for k in range(10)], color=BLUE, width=.65)
ax.set_xlabel('ensemble spread, from smallest (1) to largest (10) tenth')
ax.set_ylabel('actual error, % of range'); ax.set_title('(b) Larger spread, larger error'); ax.grid(axis='x', visible=False)
ax.set_xticks(range(1, 11))
fig.tight_layout(); save(fig, 'ml_ensemble.png')
NUM['spread_err_corr'] = float(np.corrcoef(spread, err)[0, 1])
NUM['err_top_vs_bottom'] = float(err[cb == 9].mean() / err[cb == 0].mean())
single = [np.concatenate([p[s] - y for p, y in zip(P_all, Y_all)]) for s in range(3)]
NUM['single_nrmse'] = [float((np.sqrt((e ** 2).mean(0)) / rng_all * 100).mean()) for e in single]
NUM['ens_nrmse_16'] = float((np.sqrt(((yp - yt) ** 2).mean(0)) / rng_all * 100).mean())

# ------------------------------------------------------------------ 10. input importance (freeze one input)
print('fig: input importance')
base = NUM['ens_nrmse_16']
imp = []
for k in range(7):
    Pk = []
    for rr in test:
        Uk = rr['U'].copy(); Uk[:, k] = Uk[0, k]
        Pk.append(run_members(Uk).mean(0))
    e = np.concatenate(Pk) - yt
    imp.append(float((np.sqrt((e ** 2).mean(0)) / rng_all * 100).mean()) - base)
NUM['importance'] = dict(zip(INPUTS, imp))
o = np.argsort(imp)
fig, ax = plt.subplots(figsize=(7.5, 2.8))
ax.barh([NICE[INPUTS[k]] for k in o], [imp[k] for k in o], color=BLUE, height=.55)
for i, k in enumerate(o):
    ax.text(imp[k] + .05, i, f'+{imp[k]:.2f}', va='center', fontsize=7.5)
ax.set_xlabel('increase in mean error (% of range) when this input is frozen at its starting value')
ax.grid(axis='y', visible=False); ax.set_xlim(0, max(imp) * 1.15)
fig.tight_layout(); save(fig, 'ml_importance.png')

# ------------------------------------------------------------------ 11. learned steady-state trends
print('fig: learned trends')
rngs = json.load(open(ROOT / 'Dashboard/dashboard_data.json'))['input_range']
fig, axs = plt.subplots(1, 3, figsize=(11, 2.9))
trend = {}
for ax, k in zip(axs, [0, 2, 4]):
    lo, hi = rngs[INPUTS[k]]
    vals = np.linspace(lo, hi, 15)
    q, cop = [], []
    for v in vals:
        U = np.repeat(u0[None], 240, 0); U[:, k] = v
        p = run_members(U).mean(0)[-1]
        q.append(p[0]); cop.append(p[0] / p[2])
    trend[INPUTS[k]] = (vals.tolist(), q, cop)
    ax.plot(vals, q, 'o-', color=BLUE, ms=3, lw=1.2)
    ax.set_xlabel(NICE[INPUTS[k]]); ax.set_ylabel('cooling output, kW', color=BLUE)
    a2 = ax.twinx(); a2.plot(vals, cop, 's--', color=ORANGE, ms=3, lw=1); a2.set_ylabel('COP', color=ORANGE)
    a2.grid(False); a2.spines['top'].set_visible(False)
    ax.axvline(u0[k], color=GREY, lw=.8, ls=':')
fig.tight_layout(); save(fig, 'ml_trends.png')
NUM['trend_design_Q'] = float(run_members(np.repeat(u0[None], 240, 0)).mean(0)[-1][0])

# ------------------------------------------------------------------ 12. warm-up and long-run stability
print('fig: warm-up and stability')
U = np.repeat(u0[None], 3000, 0)
Pcold = run_members(U, warm=False).mean(0)
j = TARGETS.index('Q_evap_kW')
fig, axs = plt.subplots(1, 2, figsize=(10.5, 2.8))
axs[0].plot(np.arange(120), Pcold[:120, j], color=BLUE, lw=1.3)
axs[0].axvspan(0, WARMUP, color=GREY, alpha=.15, lw=0)
axs[0].text(WARMUP / 2, 0.08, 'warm-up (discarded)', ha='center', fontsize=7.5, color='#444',
             transform=axs[0].get_xaxis_transform())
axs[0].set_xlabel('minutes from a cold (zero) memory'); axs[0].set_ylabel('cooling output, kW')
axs[0].set_title('(a) Memory settling from zero at design inputs')
axs[1].plot(np.arange(WARMUP, 3000) / 60, Pcold[WARMUP:, j], color=BLUE, lw=1.2)
axs[1].set_ylim(Pcold[200:, j].mean() - 0.5, Pcold[200:, j].mean() + 0.5)
axs[1].set_xlabel('hours at constant design inputs'); axs[1].set_ylabel('cooling output, kW')
axs[1].set_title('(b) 50 hours with nothing changing: no drift')
fig.tight_layout(); save(fig, 'ml_stability.png')
NUM['drift_50h_kW'] = float(np.ptp(Pcold[WARMUP:, j]))
NUM['steady_design_Q'] = float(Pcold[-1, j])

json.dump(NUM, open(FIG / 'ml_numbers.json', 'w'), indent=1, default=float)
print(json.dumps(NUM, indent=1, default=float))

# ------------------------------------------------------------------ 13. step + day rows of the training-stage comparison figure
from PIL import Image  # noqa: E402
im = Image.open(ML / 'outputs/figures/test_runs_prediction.png')
im.crop((0, int(im.height * 0.333), im.width, im.height)).save(FIG / 'ml_test_runs_step_day.png')
print('  wrote ml_test_runs_step_day.png')
