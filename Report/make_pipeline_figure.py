"""Draws Fig. 1 of the report: the project workflow, as a plain block diagram."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9.5})
fig, ax = plt.subplots(figsize=(11, 2.5), dpi=200)
ax.set_xlim(-0.5, 101.5); ax.set_ylim(0, 26); ax.axis('off')
boxes = [
    ('Aspen Plus', 'steady-state model\nfixed and validated', 'COP 0.608'),
    ('Sensitivity study', '241 cases run\n163 kept', 'SENS-1'),
    ('MATLAB model', 'dynamic, 9 equations\ncalibrated to Aspen', '197 runs, 291k rows'),
    ('LSTM network', '3 models averaged\ntrained in PyTorch', 'R² 0.9991'),
    ('Web dashboard', '3D plant, live AI\nhosted on Vercel', 'runs in browser'),
]
w, h, gap, x0, y0 = 17.6, 15, 2.9, 0.5, 6
for i, (t, s, n) in enumerate(boxes):
    x = x0 + i * (w + gap)
    ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle='square,pad=0', fc='#f3f3f1', ec='#222', lw=1))
    ax.text(x + w / 2, y0 + h - 3, t, ha='center', va='center', weight='bold', fontsize=9.6)
    ax.text(x + w / 2, y0 + h / 2 - 1.2, s, ha='center', va='center', fontsize=8.2, color='#333', linespacing=1.4)
    ax.text(x + w / 2, y0 - 2.6, n, ha='center', va='center', fontsize=8.2, color='#555', style='italic')
    if i < len(boxes) - 1:
        ax.annotate('', xy=(x + w + gap - 0.4, y0 + h / 2), xytext=(x + w + 0.4, y0 + h / 2),
                    arrowprops=dict(arrowstyle='-|>', color='#222', lw=1.1))
fig.savefig('figures/fig1_workflow.png', bbox_inches='tight', facecolor='white')
print('ok')
