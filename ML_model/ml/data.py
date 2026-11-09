"""Data loading, scaling and sequence building for the transient chiller dataset."""
import numpy as np
import pandas as pd

INPUTS = ['T_hw_in_C', 'm_hw_kg_s', 'T_cw_in_C', 'm_cw_kg_s',
          'T_chw_in_C', 'm_chw_kg_s', 'm_pump_kg_s']
TARGETS = ['Q_evap_kW', 'T_chw_out_C', 'Q_gen_kW', 'Q_cond_kW', 'Q_abs_kW',
           'T_hw_out_C', 'T_cw_out_C', 'T_gen_C', 'T_cond_C', 'T_evap_C',
           'T_abs_C', 'x_strong_wt', 'x_weak_wt', 'P_high_kPa', 'P_low_kPa',
           'm_ref_gen_kg_s']
DT = 60          # model time step [s] (dataset is 10 s; time constants are 18-47 min)
WARMUP = 60      # steps of constant initial inputs prepended (1 h) -> steady start
COP_WINDOW = 1800 // DT


def load_runs(csv_path):
    """Return a list of runs, each a dict with time, inputs U and targets Y."""
    cols = ['run_id', 'scenario_type', 'time_s', 'split'] + INPUTS + TARGETS
    d = pd.read_csv(csv_path, usecols=cols)
    d = d[d.time_s % DT == 0]
    runs = []
    for rid, g in d.groupby('run_id', sort=True):
        g = g.sort_values('time_s')
        runs.append(dict(run_id=int(rid), type=g.scenario_type.iloc[0], split=g.split.iloc[0],
                         t=g.time_s.to_numpy(float), U=g[INPUTS].to_numpy(np.float32),
                         Y=g[TARGETS].to_numpy(np.float32)))
    return runs


class Scaler:
    """Per-column z-score scaling fitted on training data only."""
    def __init__(self, data):
        self.mean = data.mean(0).astype(np.float32)
        self.std = (data.std(0) + 1e-8).astype(np.float32)

    def fwd(self, a):
        return (a - self.mean) / self.std

    def inv(self, a):
        return a * self.std + self.mean


def with_warmup(a, n=WARMUP):
    """Prepend n copies of the first row (the chiller is at steady state before t=0)."""
    return np.concatenate([np.repeat(a[:1], n, 0), a], 0)


def cop_avg(q_evap, q_gen, window=COP_WINDOW):
    """Energy-based COP over a trailing window (same definition as COP_avg30)."""
    ce, cg = np.cumsum(q_evap), np.cumsum(q_gen)
    se = ce - np.concatenate([np.zeros(window), ce[:-window]])[:len(ce)]
    sg = cg - np.concatenate([np.zeros(window), cg[:-window]])[:len(cg)]
    return se / sg
