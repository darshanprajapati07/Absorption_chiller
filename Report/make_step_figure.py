"""Fig. 4: response to a +10 K hot-water step, plotted from run 2 of the transient dataset."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

cols = ['run_id', 'time_s', 'Q_evap_kW', 'T_chw_out_C', 'Q_gen_kW', 'x_strong_wt']
d = pd.read_csv('../Transient/output/transient_dataset.csv', usecols=cols)
r = d[d.run_id == 2]
t = (r.time_s - 900) / 60          # step applied at 15 min
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})
fig, axs = plt.subplots(1, 4, figsize=(11, 2.6), dpi=200)
for ax, (c, lab) in zip(axs, [('Q_evap_kW', 'Cooling output, kW'), ('T_chw_out_C', 'Chilled water out, °C'),
                              ('Q_gen_kW', 'Heat input, kW'), ('x_strong_wt', 'Strong solution, wt% LiBr')]):
    ax.plot(t, r[c], color='#1f4e9a', lw=1.4)
    ax.set_title(lab, fontsize=9); ax.set_xlabel('minutes after the step'); ax.set_xlim(-15, 165)
    ax.grid(alpha=.3, lw=.6); ax.axvline(0, color='#888', lw=.8, ls='--')
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig('figures/fig4_step.png', facecolor='white'); print('ok', len(r))
