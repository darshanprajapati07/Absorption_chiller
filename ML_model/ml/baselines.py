"""Baseline models for comparison with the LSTM digital twin.

1. Static  : gradient boosting on the current inputs only (no memory).
2. Lag-GBM : gradient boosting on engineered dynamic features
             (input lags + first-order filtered inputs, i.e. a FIR / Hammerstein-
             type model). This is a strong, physics-inspired baseline.
"""
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

LAGS = [1, 2, 5, 10, 20, 40]          # steps (x 60 s)
TAUS = [5, 15, 30, 60]                # first-order filter time constants [steps]


def lag_features(U):
    """Causal dynamic features for one run; before t=0 the inputs were constant."""
    n = len(U)
    feats = [U]
    for k in LAGS:
        idx = np.maximum(np.arange(n) - k, 0)
        feats.append(U[idx])
    for tau in TAUS:
        a = 1 - np.exp(-1 / tau)
        f = np.empty_like(U)
        f[0] = U[0]
        for i in range(1, n):
            f[i] = f[i - 1] + a * (U[i] - f[i - 1])
        feats.append(f)
    return np.concatenate(feats, 1)


def fit_gbm(X, Y, seed=0):
    models = []
    for j in range(Y.shape[1]):
        m = HistGradientBoostingRegressor(max_iter=600, learning_rate=0.08, max_leaf_nodes=48,
                                          l2_regularization=1e-3, random_state=seed)
        m.fit(X, Y[:, j])
        models.append(m)
    return models


def predict_gbm(models, X):
    return np.stack([m.predict(X) for m in models], 1)
