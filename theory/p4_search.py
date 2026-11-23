"""P4 search (CLAUDE.md §4): 4-player matrices where the *weakest* player is the unique favourite of some bracket.

1. Grid: every matrix with upper-triangle probabilities in {0.1, 0.2, ..., 0.9} (9^6 = 531,441).  (The coarser
   {0.1, 0.3, ..., 0.9} grid has 47 matrices crowning the s-weakest player, but in each the Borda-weakest is tied or a
   different player, so it has no example that is unambiguous under both definitions.)  "Weakest" must hold
   under both definitions: lowest strength score s (row mean of logit P, our main definition) and lowest Borda score.
   Among those where the weakest player is crowned, report the smallest κ (cleanest example) and the largest margin.
2. Continuous: minimise κ subject to "weakest (by s) is the unique favourite of some bracket", by random search plus
   hill-climbing over L = scale·(sqrt(1-κ) T̂ + sqrt(κ) Ĉ).  This shows how little cyclicity is needed at n = 4.
Usage: python theory/p4_search.py
"""
import itertools
import json
import time

import numpy as np
import pandas as pd

from km.bracket import enumerate_brackets, win_probs
from km.models import kappa, logit, sigmoid
from km.runlog import write_csv

BR = enumerate_brackets(4)
IU = np.triu_indices(4, 1)


def from_upper(u: np.ndarray) -> np.ndarray:
    """Batch of 4x4 P matrices from upper-triangle probabilities (B, 6)."""
    P = np.full((len(u), 4, 4), 0.5)
    P[:, IU[0], IU[1]] = u
    P[:, IU[1], IU[0]] = 1 - u
    return P


def weakest_crowned(P: np.ndarray):
    """Per matrix: weakest by s, weakest by Borda, best margin of the s-weakest over all 3 brackets, best bracket index."""
    B = len(P)
    W = win_probs(np.repeat(P, 3, axis=0), np.tile(BR, (B, 1))).reshape(B, 3, 4)
    s = logit(P).mean(axis=2)
    borda = (P.sum(axis=2) - 0.5) / 3
    ws, wb = np.argmin(s, 1), np.argmin(borda, 1)
    Wi = W[np.arange(B), :, ws]
    others = np.where(np.arange(4)[None, None, :] == ws[:, None, None], -np.inf, W).max(axis=2)
    margin = Wi - others  # (B, 3)
    return ws, wb, margin.max(1), margin.argmax(1), s, borda


def kappas(P: np.ndarray) -> np.ndarray:
    return np.array([kappa(logit(p)) for p in P])


def grid_search() -> pd.DataFrame:
    vals = np.round(np.arange(1, 10) / 10, 1)
    U = np.array(list(itertools.product(vals, repeat=6)))
    P = from_upper(U)
    ws, wb, m, b, s, borda = weakest_crowned(P)
    # weakest must be unique under both definitions and the same player
    s_sorted, b_sorted = np.sort(s, 1), np.sort(borda, 1)
    clean = (ws == wb) & (s_sorted[:, 1] - s_sorted[:, 0] > 1e-9) & (b_sorted[:, 1] - b_sorted[:, 0] > 1e-9)
    hit = clean & (m > 1e-12)
    k = kappas(P[hit])
    rows = [{"upper_P": json.dumps(U[i].tolist()), "weakest": int(ws[i]), "margin": float(m[i]), "bracket": int(b[i]),
             "kappa": float(kk)} for i, kk in zip(np.flatnonzero(hit), k)]
    print(f"grid: {len(U)} matrices, weakest well-defined in {clean.sum()}, weakest crowned in {hit.sum()}")
    return pd.DataFrame(rows).sort_values("kappa")


def continuous_min_kappa(rng: np.random.Generator, n_random: int = 400_000, iters: int = 3000) -> dict:
    """Minimise κ over P with the s-weakest player the unique favourite of some bracket (margin > 1e-6)."""
    from km.models import random_cyclic_unit, random_ranking_unit

    def build(params):  # params: (B, 3 + 6 + 2): g, raw upper-triangle for C, log-scale, logit-kappa
        B = len(params)
        g = np.c_[np.zeros(B), params[:, :3]]
        T = g[:, :, None] - g[:, None, :]
        T /= np.linalg.norm(T, axis=(1, 2), keepdims=True)
        A = np.zeros((B, 4, 4))
        A[:, IU[0], IU[1]] = params[:, 3:9]
        A = A - A.transpose(0, 2, 1)
        sA = A.mean(axis=2)
        C = A - (sA[:, :, None] - sA[:, None, :])
        C /= np.linalg.norm(C, axis=(1, 2), keepdims=True)
        k = sigmoid(params[:, 10])
        scale = np.exp(params[:, 9])
        L = scale[:, None, None] * (np.sqrt(1 - k)[:, None, None] * T + np.sqrt(k)[:, None, None] * C)
        return sigmoid(L), k

    def objective(params):
        P, k = build(params)
        ws, wb, m, _, s, borda = weakest_crowned(P)
        ss, bb = np.sort(s, 1), np.sort(borda, 1)
        ok = (m > 1e-3) & (ws == wb) & (ss[:, 1] - ss[:, 0] > 1e-3) & (bb[:, 1] - bb[:, 0] > 1e-3)
        ok &= (P.min(axis=(1, 2)) >= 0.05)  # no near-certain matches
        viol = np.maximum(1e-3 - m, 0) + (ws != wb) + np.maximum(0.05 - P.min(axis=(1, 2)), 0) * 10
        return np.where(ok, k, 2.0 + viol), k, m  # feasible: κ; infeasible: 2 + violation

    params = np.c_[rng.standard_normal((n_random, 9)) * 2, rng.uniform(-1, 3, n_random), rng.uniform(-4, 4, n_random)]
    f, k, m = objective(params)
    top = np.argsort(f)[:200]
    pop, cur = params[top].copy(), f[top].copy()
    for t in range(iters):
        step = 0.5 * 0.998**t + 1e-3
        cand = pop + step * rng.standard_normal(pop.shape)
        fc, _, _ = objective(cand)
        better = fc < cur
        pop[better], cur[better] = cand[better], fc[better]
    best = int(np.argmin(cur))
    P, k = build(pop[best:best + 1])
    ws, wb, m, b, s, borda = weakest_crowned(P)
    return {"min_kappa": float(k[0]), "P": np.round(P[0], 6).tolist(), "weakest_s": int(ws[0]), "weakest_borda": int(wb[0]),
            "margin": float(m[0]), "bracket": BR[int(b[0])].tolist(),
            "mean_abs_P_minus_half": float(np.abs(P[0] - 0.5)[~np.eye(4, dtype=bool)].mean())}


if __name__ == "__main__":
    t0 = time.time()
    g = grid_search()
    print(g.head(10).to_string(index=False))
    # Pareto front: for each κ threshold, the largest margin achievable at or below it
    front, best = [], -1
    for _, r in g.iterrows():
        if r.margin > best + 1e-9:
            best = r.margin
            front.append(r)
    print("Pareto front (κ ↑, margin ↑):")
    print(pd.DataFrame(front).to_string(index=False))
    c = continuous_min_kappa(np.random.default_rng(20261123))
    print("continuous:", c)
    write_csv(g, "p4_grid", seed=0, params={"values": "0.1..0.9 step 0.1"}, runtime_s=time.time() - t0)
    write_csv(pd.DataFrame([c]), "p4_min_kappa", seed=20261123, params={"n_random": 400000, "iters": 3000}, runtime_s=time.time() - t0)
    print(f"{time.time() - t0:.0f}s")
