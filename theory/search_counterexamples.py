"""Counterexample search for the BT claims (CLAUDE.md §4: numerical falsification first, proof second).

Claims tested, all under Bradley-Terry P[i, j] = sigmoid(g[i] - g[j]):
  P3      swap-monotonicity: g[i] > g[j], σ' = σ with i and j exchanged  =>  W_i(σ') >= W_j(σ).
  P3(ii)  W_i(σ) is non-decreasing in g[i] (others fixed).
  P3(i)   the weakest player is never the unique favourite of any bracket.
  P6      the kingmakeable set is a top segment {1, ..., K} of the strength order.
Random search draws g from several families (normal at many scales, clustered "P2-like", heavy-tailed, near-ties);
adversarial search hill-climbs on g (and σ) to push each claim's slack below zero.  A violation is slack < -1e-12.

Usage: python theory/search_counterexamples.py [--quick | --full] [--seed S]
Output: outputs/csv/p3_search.csv (one row per test family) with the worst case found.
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd

from km.bracket import enumerate_brackets, win_probs
from km.models import sigmoid
from km.runlog import write_csv

TOL = 1e-12
FAMILIES = ("normal", "clustered", "heavy", "near_ties")


def draw_g(B: int, n: int, rng: np.random.Generator) -> np.ndarray:
    """B strength vectors from a mixture of families (clipped to [-15, 15] to stay away from float underflow)."""
    fam = rng.integers(0, len(FAMILIES), B)
    scale = np.exp(rng.uniform(np.log(0.05), np.log(8), (B, 1)))
    g = rng.standard_normal((B, n)) * scale
    # clustered: 2-3 groups, tiny spread inside a group, big random gaps between groups (like the P2 example)
    groups = rng.integers(0, 3, (B, n))
    centres = rng.standard_normal((B, 3)) * 4
    clustered = np.take_along_axis(centres, groups, 1) + 0.05 * rng.standard_normal((B, n))
    heavy = np.clip(rng.standard_cauchy((B, n)), -15, 15) * scale / 2
    near = 0.01 * rng.standard_normal((B, n))
    near[np.arange(B), rng.integers(0, n, B)] += rng.choice([-5.0, 5.0], B)
    g = np.where((fam == 1)[:, None], clustered, g)
    g = np.where((fam == 2)[:, None], heavy, g)
    g = np.where((fam == 3)[:, None], near, g)
    return np.clip(g, -15, 15)


def bt(g: np.ndarray) -> np.ndarray:
    return sigmoid(g[:, :, None] - g[:, None, :])


def swap_slack(g: np.ndarray, sig: np.ndarray, i: np.ndarray, j: np.ndarray) -> np.ndarray:
    """W_i(σ') - W_j(σ) per row, with σ' = σ with players i and j exchanged; requires g[i] > g[j]."""
    B = len(g)
    P = bt(g)
    rows = np.arange(B)
    sig2 = sig.copy()
    pos_i, pos_j = np.argmax(sig == i[:, None], 1), np.argmax(sig == j[:, None], 1)
    sig2[rows, pos_i], sig2[rows, pos_j] = j, i
    return win_probs(P, sig2)[rows, i] - win_probs(P, sig)[rows, j]


def random_pairs(g: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Random distinct (i, j) per row, relabelled so that g[i] >= g[j]."""
    B, n = g.shape
    i = rng.integers(0, n, B)
    j = (i + rng.integers(1, n, B)) % n
    swap = g[np.arange(B), i] < g[np.arange(B), j]
    return np.where(swap, j, i), np.where(swap, i, j)


def worst_record(name, n, n_tests, slack, g, extra=None) -> dict:
    k = int(np.argmin(slack))
    return {"claim": name, "n": n, "n_tests": int(n_tests), "min_slack": float(slack[k]),
            "n_violations": int((slack < -TOL).sum()), "worst_g": json.dumps(np.round(g[k], 6).tolist()),
            "worst_extra": json.dumps(extra[k]) if extra is not None else ""}


def random_p3(n: int, total: int, rng: np.random.Generator, batch: int = 20_000) -> list[dict]:
    rows = {"P3": [], "P3(ii)": []}
    done = 0
    while done < total:
        B = min(batch, total - done)
        g = draw_g(B, n, rng)
        sig = rng.permuted(np.tile(np.arange(n), (B, 1)), axis=1)
        i, j = random_pairs(g, rng)
        keep = g[np.arange(B), i] > g[np.arange(B), j]
        s = swap_slack(g, sig, i, j)
        s = np.where(keep, s, np.inf)
        rows["P3"].append((s, g, [[int(a), int(b), list(map(int, x))] for a, b, x in zip(i, j, sig)]))
        # (ii): raise g[i] by delta, W_i(σ) must not fall
        delta = np.exp(rng.uniform(np.log(1e-3), np.log(5), B))
        g2 = g.copy()
        g2[np.arange(B), i] += delta
        s2 = win_probs(bt(g2), sig)[np.arange(B), i] - win_probs(bt(g), sig)[np.arange(B), i]
        rows["P3(ii)"].append((s2, g, [[int(a), float(d), list(map(int, x))] for a, d, x in zip(i, delta, sig)]))
        done += B
    out = []
    for name, parts in rows.items():
        s = np.concatenate([p[0] for p in parts])
        g = np.concatenate([p[1] for p in parts])
        extra = sum((p[2] for p in parts), [])
        n_valid = int(np.isfinite(s).sum())
        out.append(worst_record(name, n, n_valid, np.where(np.isfinite(s), s, np.inf), g, extra))
    return out


def adversarial_p3(n: int, pop: int, iters: int, rng: np.random.Generator) -> dict:
    """Hill-climb a population of (g, σ, i, j) to minimise the relative slack W_i(σ')/W_j(σ) - 1."""
    g = draw_g(pop, n, rng)
    sig = rng.permuted(np.tile(np.arange(n), (pop, 1)), axis=1)
    i, j = random_pairs(g, rng)

    def score(g, sig):
        ok = g[np.arange(pop), i] > g[np.arange(pop), j] + 1e-9
        s = swap_slack(g, sig, i, j)
        wj = win_probs(bt(g), sig)[np.arange(pop), j]
        return np.where(ok, s / np.maximum(wj, 1e-300), np.inf), s

    cur, cur_abs = score(g, sig)
    for t in range(iters):
        step = 2.0 * 0.995**t + 1e-3
        g2 = np.clip(g + step * rng.standard_normal(g.shape) * (rng.random(g.shape) < 0.5), -15, 15)
        sig2 = sig.copy()
        mv = rng.random(pop) < 0.3
        a, b = rng.integers(0, n, pop), rng.integers(0, n, pop)
        r = np.arange(pop)[mv]
        sig2[r, a[mv]], sig2[r, b[mv]] = sig[r, b[mv]], sig[r, a[mv]]
        new, new_abs = score(g2, sig2)
        better = new < cur
        g[better], sig[better], cur[better], cur_abs[better] = g2[better], sig2[better], new[better], new_abs[better]
    extra = [[int(a), int(b), list(map(int, x))] for a, b, x in zip(i, j, sig)]
    rec = worst_record("P3 adversarial", n, pop * iters, cur_abs, g, extra)
    rec["min_relative_slack"] = float(np.min(cur))
    return rec


def margins_by_rank(g: np.ndarray, brackets: np.ndarray, chunk: int = 256) -> np.ndarray:
    """M[b, r] = max over brackets of (W - best other W) for the rank-r player (r = 0 strongest) of matrix b."""
    B, n = g.shape
    nb = len(brackets)
    out = np.empty((B, n))
    for s in range(0, B, chunk):
        gg = g[s:s + chunk]
        m = len(gg)
        P = np.repeat(bt(gg), nb, axis=0)
        W = win_probs(P, np.tile(brackets, (m, 1))).reshape(m, nb, n)
        top2 = np.sort(W, axis=2)[:, :, -2:]
        best_other = np.where(W >= top2[:, :, 1:2], top2[:, :, 0:1], top2[:, :, 1:2])
        M = (W - best_other).max(axis=1)  # (m, n) by player
        order = np.argsort(-gg, axis=1)
        out[s:s + m] = np.take_along_axis(M, order, 1)
    return out


def p6_slack(M: np.ndarray) -> np.ndarray:
    """Top-segment slack: min over r of max(-M_r, M_{r-1}); negative iff rank r is kingmakeable but rank r-1 is not."""
    return np.min(np.maximum(-M[:, 1:], M[:, :-1]), axis=1)


def random_p6(n: int, total: int, rng: np.random.Generator) -> list[dict]:
    brackets = enumerate_brackets(n)
    g = draw_g(total, n, rng)
    M = margins_by_rank(g, brackets)
    return [worst_record("P6 top segment", n, total, p6_slack(M), g),
            worst_record("P3(i) weakest never favourite", n, total, -M[:, -1], g)]


def adversarial_p6(n: int, pop: int, iters: int, rng: np.random.Generator) -> list[dict]:
    brackets = enumerate_brackets(n)
    out = []
    for name, f in (("P6 adversarial", p6_slack), ("P3(i) adversarial", lambda M: -M[:, -1])):
        g = draw_g(pop, n, rng)
        cur = f(margins_by_rank(g, brackets))
        for t in range(iters):
            step = 2.0 * 0.99**t + 1e-3
            g2 = np.clip(g + step * rng.standard_normal(g.shape), -15, 15)
            new = f(margins_by_rank(g2, brackets))
            better = new < cur
            g[better], cur[better] = g2[better], new[better]
        out.append(worst_record(name, n, pop * iters, cur, g))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    ap.add_argument("--seed", type=int, default=20261122)
    args = ap.parse_args()
    full = not args.quick
    p = {"mode": "full" if full else "quick",
         "p3_random": {4: 400_000, 8: 400_000, 16: 200_000} if full else {4: 20_000, 8: 20_000, 16: 5_000},
         "p3_adv": {"pop": 2000, "iters": 400} if full else {"pop": 200, "iters": 50},
         "p6_random": {4: 200_000, 8: 30_000} if full else {4: 5_000, 8: 500},
         "p6_adv": {4: (2000, 300), 8: (100, 150)} if full else {4: (100, 20), 8: (20, 5)},
         "families": FAMILIES, "violation_tol": TOL}
    rng = np.random.default_rng(args.seed)
    t0 = time.time()
    rows = []
    for n, total in p["p3_random"].items():
        rows += random_p3(n, total, rng)
        print(f"P3 random n={n}: {time.time() - t0:.0f}s")
    for n in (4, 8, 16):
        rows.append(adversarial_p3(n, p["p3_adv"]["pop"], p["p3_adv"]["iters"], rng))
        print(f"P3 adversarial n={n}: {time.time() - t0:.0f}s")
    for n, total in p["p6_random"].items():
        rows += random_p6(n, total, rng)
        print(f"P6 random n={n}: {time.time() - t0:.0f}s")
    for n, (pop, iters) in p["p6_adv"].items():
        rows += adversarial_p6(n, pop, iters, rng)
        print(f"P6 adversarial n={n}: {time.time() - t0:.0f}s")
    df = pd.DataFrame(rows)
    write_csv(df, "p3_search", seed=args.seed, params={k: str(v) for k, v in p.items()}, runtime_s=time.time() - t0)
    pd.set_option("display.width", 200)
    print(df[["claim", "n", "n_tests", "min_slack", "n_violations"]].to_string(index=False))


if __name__ == "__main__":
    main()
