"""Build the self-contained dashboard HTML.

Packs the trained LSTM ensemble (float32, base64), the scalers, the test metrics
and a few unseen test runs into dashboard_template.html -> chiller_dashboard.html.

Usage (from this folder):  py -3.12 build_dashboard.py
"""
import base64
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ML = HERE.parent / 'ML_model'
sys.path.insert(0, str(ML))
from ml.data import INPUTS, TARGETS, cop_avg  # noqa: E402

port = json.loads((ML / 'outputs/models/lstm_portable.json').read_text())
meta = port['meta']


def pack(member):
    parts = []
    for L in member['lstm']:
        parts += [np.array(L['W_ih']).ravel(), np.array(L['W_hh']).ravel(), np.array(L['b']).ravel()]
    for H in member['head']:
        parts += [np.array(H['W']).ravel(), np.array(H['b']).ravel()]
    return base64.b64encode(np.concatenate(parts).astype('<f4').tobytes()).decode()


weights = [pack(m) for m in port['members']]
hidden = len(port['members'][0]['lstm'][0]['b']) // 4

# ---- training-range of every input (used to flag extrapolation in the UI)
d = pd.read_csv(HERE.parent / 'Transient/output/transient_dataset.csv')
d = d[d.time_s % 60 == 0]
tr = d[d.split == 'train']
rng = {k: [float(tr[k].min()), float(tr[k].max())] for k in INPUTS}
first = d[d.scenario_type == 'step'].sort_values(['run_id', 'time_s']).iloc[0]
u0 = [round(float(first[k]), 4) for k in INPUTS]

# ---- unseen test runs for the validation replay
want = [('daily', 45), ('aprbs', 54), ('step', None), ('ramp', None), ('startup', None)]
te = d[d.split == 'test']
runs = []
for typ, rid in want:
    ids = sorted(te[te.scenario_type == typ].run_id.unique())
    rid = rid if rid in ids else ids[0]
    g = te[te.run_id == rid].sort_values('time_s')
    Y = g[TARGETS].to_numpy()
    cop = cop_avg(Y[:, 0], Y[:, 2])
    runs.append(dict(id=int(rid), type=typ, t=(g.time_s / 60).round(1).tolist(),
                     U=np.round(g[INPUTS].to_numpy(), 4).tolist(),
                     Y=np.round(np.column_stack([Y, cop]), 5).tolist()))

met = pd.read_csv(ML / 'outputs/results/best_model_metrics.csv')
comp = pd.read_csv(ML / 'outputs/results/model_comparison.csv')
summ = json.loads((ML / 'outputs/results/summary.json').read_text())

DATA = dict(
    inputs=INPUTS, targets=TARGETS, hidden=hidden, layers=len(port['members'][0]['lstm']),
    x_mean=meta['x_mean'], x_std=meta['x_std'], y_mean=meta['y_mean'], y_std=meta['y_std'],
    warmup=meta['warmup_steps'], dt=meta['dt_s'], weights=weights, input_range=rng, u0=u0,
    metrics=json.loads(met.to_json(orient='records')),
    comparison=json.loads(comp.to_json(orient='records')),
    daily=summ.get('daily_profiles', {}),
    n_runs=dict(train=int(d[d.split == 'train'].run_id.nunique()),
                validation=int(d[d.split == 'validation'].run_id.nunique()),
                test=int(te.run_id.nunique())),
    test_runs=runs,
)



def clean(o):
    if isinstance(o, float):
        return None if o != o else o
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    return o


DATA = clean(DATA)
tpl = (HERE / 'dashboard_template.html').read_text(encoding='utf-8')
engine = (HERE / 'twin_engine.js').read_text(encoding='utf-8')
html = tpl.replace('/*__ENGINE__*/', engine).replace('/*__DATA__*/null', json.dumps(DATA, separators=(',', ':'), allow_nan=False))
(HERE / 'artifact_page.html').write_text(html, encoding='utf-8')       # published page (host adds the skeleton)
HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>body{margin:0}[hidden]{display:none!important}</style>
</head>
<body>
"""
standalone = HEAD + html + '\n</body>\n</html>\n'
out = HERE / 'chiller_dashboard.html'                                     # double-click to open offline
out.write_text(standalone, encoding='utf-8')
(HERE / 'dashboard_data.json').write_text(json.dumps(DATA, separators=(',', ':'), allow_nan=False))
print(f'wrote {out.name}: {out.stat().st_size / 1e6:.2f} MB')
