"""Sequence models: recurrent 'digital twin' (inputs history -> all outputs)."""
import numpy as np
import torch
from torch import nn


class SeqNet(nn.Module):
    """GRU or LSTM encoder + small MLP head, run in simulation mode
    (only the measured inputs are fed; outputs are never fed back)."""

    def __init__(self, n_in, n_out, hidden=96, layers=2, cell='gru', dropout=0.0):
        super().__init__()
        self.cell = cell
        rnn = nn.GRU if cell == 'gru' else nn.LSTM
        self.rnn = rnn(n_in, hidden, layers, batch_first=True, dropout=dropout)
        self.head = nn.Sequential(nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, n_out))

    def forward(self, x):
        h, _ = self.rnn(x)
        return self.head(h)


def pad_batch(seqs):
    """Pad a list of (X, Y) arrays to a batch with a validity mask."""
    L = max(len(x) for x, _ in seqs)
    nb, ni, no = len(seqs), seqs[0][0].shape[1], seqs[0][1].shape[1]
    X = np.zeros((nb, L, ni), np.float32)
    Y = np.zeros((nb, L, no), np.float32)
    M = np.zeros((nb, L, 1), np.float32)
    for i, (x, y) in enumerate(seqs):
        n = len(x)
        X[i, :n], Y[i, :n], M[i, :n] = x, y, 1
        X[i, n:] = x[-1]                       # hold last input in padding
    return torch.from_numpy(X), torch.from_numpy(Y), torch.from_numpy(M)


def train_seqnet(train, val, n_in, n_out, cell='gru', hidden=96, layers=2, epochs=300,
                 batch=8, lr=3e-3, seed=0, log=print):
    """Full-sequence BPTT training with cosine LR and best-on-validation selection."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    net = SeqNet(n_in, n_out, hidden, layers, cell)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs, eta_min=lr / 50)
    Xv, Yv, Mv = pad_batch(val)
    best, best_state, hist = np.inf, None, []
    for ep in range(1, epochs + 1):
        net.train()
        order = rng.permutation(len(train))
        tl = 0.0
        for k in range(0, len(order), batch):
            Xb, Yb, Mb = pad_batch([train[i] for i in order[k:k + batch]])
            loss = (((net(Xb) - Yb) ** 2) * Mb).sum() / (Mb.sum() * Yb.shape[2])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step()
            tl += loss.item() * len(order[k:k + batch])
        sched.step()
        if ep % 5 == 0 or ep == epochs:
            net.eval()
            with torch.no_grad():
                vl = ((((net(Xv) - Yv) ** 2) * Mv).sum() / (Mv.sum() * Yv.shape[2])).item()
            hist.append((ep, tl / len(train), vl))
            if vl < best:
                best, best_state = vl, {k: v.clone() for k, v in net.state_dict().items()}
            if ep % 25 == 0:
                log(f'    {cell} epoch {ep:4d}  train MSE {tl / len(train):.5f}  val MSE {vl:.5f}  (best {best:.5f})')
    net.load_state_dict(best_state)
    net.eval()
    return net, hist


def predict(net, X):
    with torch.no_grad():
        return net(torch.from_numpy(X[None])).numpy()[0]
