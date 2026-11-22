"""E2 tennis supplement: κ and held-out log-loss of the BC fit along the λ path (time-ordered 80/20 split), showing how
much apparent cyclicity survives out of sample.  Same player selection as e2_real.run_tennis.
Usage: python experiments/e2_tennis_lambda_path.py"""
import time

import numpy as np
import pandas as pd

from km.data import load_tennis
from km.models import fit_bc, fit_bt_mle, kappa, log_loss, logit
from km.runlog import ROOT, write_csv

t0 = time.time()
rng = np.random.default_rng(20261124)
df = load_tennis(ROOT / "data" / "raw" / "tennis_atp", range(2015, 2020))
counts = pd.concat([df.winner, df.loser]).value_counts()
players = list(counts.index[:60])
while len(players) > 16:
    sub = df[df.winner.isin(players) & df.loser.isin(players)]
    c = pd.concat([sub.winner, sub.loser]).value_counts().reindex(players).fillna(0)
    players.remove(c.idxmin())
sub = df[df.winner.isin(players) & df.loser.isin(players)].reset_index(drop=True)
idx = {p: k for k, p in enumerate(players)}


def to_wins(part):
    w = np.zeros((16, 16), dtype=int)
    np.add.at(w, (part.winner.map(idx).to_numpy(), part.loser.map(idx).to_numpy()), 1)
    return w


cut = int(0.8 * len(sub))
train, test = to_wins(sub.iloc[:cut]), to_wins(sub.iloc[cut:])
rows = [{"model": "BT", "lambda": np.nan, "kappa": 0.0, "train_logloss": log_loss(fit_bt_mle(train), train),
         "test_logloss": log_loss(fit_bt_mle(train), test)}]
for lam in (0.01, 0.1, 1.0, 3.0, 10.0, 30.0, 100.0):
    P = fit_bc(train, 2, lam, rng)
    rows.append({"model": "BC", "lambda": lam, "kappa": kappa(logit(P)), "train_logloss": log_loss(P, train),
                 "test_logloss": log_loss(P, test)})
out = pd.DataFrame(rows)
write_csv(out, "e2_tennis_lambda_path", seed=20261124, params={"years": "2015-2019", "split": "time-ordered 80/20",
          "n_matches": len(sub)}, runtime_s=time.time() - t0)
print(out.round(4).to_string(index=False))
