"""Knockout brackets: enumeration, exact win probabilities (DP), Monte Carlo, and per-player bracket metrics.

A bracket is a seeding of n players (n a power of 2) into the leaves of a balanced binary tree: leaves (0,1)
meet in round 1, the winners of (0,1) and (2,3) meet in round 2, and so on.  Two seedings are the same
bracket if one becomes the other by swapping the two subtrees under any node, so there are n! / 2^(n-1)
distinct brackets (n=4: 3, n=8: 315, n=16: 638,512,875).

Canonical representative: under every node the subtree containing the smaller player index goes left.

Exact DP: for node v with children A, B and i in A,
    q_v(i) = q_A(i) · Σ_{j∈B} q_B(j) · P[i, j],   q_leaf = 1,   W_i(σ) = q_root(i).
"""
from __future__ import annotations

from itertools import combinations
from math import factorial

import numpy as np


def n_brackets(n: int) -> int:
    """Number of distinct brackets, n! / 2^(n-1)."""
    return factorial(n) // 2 ** (n - 1)


def _canonical_seedings(players: tuple[int, ...]) -> list[tuple[int, ...]]:
    if len(players) == 1:
        return [players]
    first, rest = players[0], players[1:]  # players is sorted, so `first` is the minimum
    half = len(players) // 2
    out = []
    for partners in combinations(rest, half - 1):
        left = (first,) + partners
        right = tuple(p for p in rest if p not in partners)
        for sl in _canonical_seedings(left):
            for sr in _canonical_seedings(right):
                out.append(sl + sr)
    return out


def enumerate_brackets(n: int) -> np.ndarray:
    """All distinct brackets as canonical seedings, shape (n!/2^(n-1), n); row b, column k = player at leaf k."""
    if n < 2 or n & (n - 1):
        raise ValueError("n must be a power of 2, at least 2")
    out = np.array(_canonical_seedings(tuple(range(n))), dtype=np.int64)
    assert len(out) == n_brackets(n)
    return out


def canonicalize(seeding: np.ndarray) -> tuple[int, ...]:
    """Canonical representative of the bracket containing ``seeding`` (smaller-minimum subtree goes left)."""
    s = list(seeding)
    if len(s) == 1:
        return tuple(s)
    h = len(s) // 2
    a, b = canonicalize(s[:h]), canonicalize(s[h:])
    return a + b if min(a) < min(b) else b + a


def standard_seeding(n: int) -> np.ndarray:
    """Leaf order of seeds 0..n-1 (0 = top seed) in standard seeding, e.g. n=8 -> seeds 1v8, 4v5, 2v7, 3v6."""
    seeds = [1]
    while len(seeds) < n:
        m = 2 * len(seeds) + 1
        seeds = [x for s in seeds for x in (s, m - s)]
    return np.array(seeds) - 1


def win_probs(P: np.ndarray, brackets: np.ndarray) -> np.ndarray:
    """Exact win probabilities by the DP, vectorised over brackets.

    ``brackets`` has shape (B, n) or (n,).  Returns W of the same leading shape with W[b, i] = P(player i wins
    bracket b), indexed by *player* (not leaf).  ``P`` may also be a stack of shape (B, n, n), one matrix per bracket.
    """
    br = np.atleast_2d(brackets)
    B, n = br.shape
    if P.ndim == 3:  # Q[b, k, l] = P_b[player at leaf k, player at leaf l]
        Q = P[np.arange(B)[:, None, None], br[:, :, None], br[:, None, :]]
    else:
        Q = P[br[:, :, None], br[:, None, :]]
    q = np.ones((B, n))
    leaf = np.arange(n)
    size = 1
    while size < n:
        # sibling[k, l] = 1 if leaf l is in the sibling block of leaf k at this level
        sibling = ((leaf[:, None] // size) ^ 1) == (leaf[None, :] // size)
        q = q * np.einsum("bkl,kl,bl->bk", Q, sibling, q)
        size *= 2
    W = np.empty_like(q)
    np.put_along_axis(W, br, q, axis=1)
    return W[0] if np.ndim(brackets) == 1 else W


def simulate_knockout(P: np.ndarray, seedings: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Play one knockout per row of ``seedings`` (shape (R, n)); return the winner of each run, shape (R,)."""
    cur = np.array(seedings, copy=True)
    while cur.shape[1] > 1:
        a, b = cur[:, 0::2], cur[:, 1::2]
        cur = np.where(rng.random(a.shape) < P[a, b], a, b)
    return cur[:, 0]


def win_probs_mc(P: np.ndarray, bracket: np.ndarray, n_runs: int, rng: np.random.Generator) -> np.ndarray:
    """Monte Carlo estimate of W(σ) for a single bracket; returns empirical win frequencies per player."""
    winners = simulate_knockout(P, np.tile(bracket, (n_runs, 1)), rng)
    return np.bincount(winners, minlength=len(bracket)) / n_runs


def exhaustive_metrics(P: np.ndarray, brackets: np.ndarray | None = None, tie_tol: float = 1e-12) -> dict:
    """Per-player bracket metrics over all brackets (CLAUDE.md §2).

    Returns Wmax, Wmin, R = Wmax - Wmin, kingmakeable (i is the unique argmax of W(σ) for some σ, with a
    margin > tie_tol over the runner-up), K = #kingmakeable, Pi = mean R, argmax_bracket[i] (the bracket
    maximising W_i), and the full W matrix.
    """
    if brackets is None:
        brackets = enumerate_brackets(len(P))
    W = win_probs(P, brackets)
    top2 = np.sort(W, axis=1)[:, -2:]
    fav = np.argmax(W, axis=1)
    unique = (top2[:, 1] - top2[:, 0]) > tie_tol
    n = len(P)
    kingmakeable = np.zeros(n, dtype=bool)
    kingmakeable[np.unique(fav[unique])] = True
    Wmax, Wmin = W.max(axis=0), W.min(axis=0)
    return {
        "W": W,
        "Wmax": Wmax,
        "Wmin": Wmin,
        "R": Wmax - Wmin,
        "kingmakeable": kingmakeable,
        "K": int(kingmakeable.sum()),
        "Pi": float(np.mean(Wmax - Wmin)),
        "argmax_bracket": brackets[np.argmax(W, axis=0)],
    }


def objective(kind: str, i: int):
    """Objective on W (shape (B, n)) for player i, to be maximised: 'max' -> W_i, 'min' -> -W_i,
    'margin' -> W_i - max_{j != i} W_j (positive iff i is the unique favourite)."""
    if kind == "max":
        return lambda W: W[:, i]
    if kind == "min":
        return lambda W: -W[:, i]
    if kind == "margin":
        return lambda W: W[:, i] - np.max(np.delete(W, i, axis=1), axis=1)
    raise ValueError(kind)


def local_search(P: np.ndarray, f, rng: np.random.Generator, restarts: int = 50) -> tuple[float, np.ndarray]:
    """Maximise f(W(σ)) over brackets by first-improvement hill-climbing on leaf swaps, with random restarts.

    Each restart starts from a uniformly random seeding; at every step all n(n-1)/2 swaps of two leaves are scored
    at once with the DP and the first improving one in a random order is taken; stops at a local optimum.
    Returns (best value, best seeding).  For n >= 16 this is a lower bound on the true maximum.
    """
    n = len(P)
    a, b = np.triu_indices(n, k=1)
    best_val, best_s = -np.inf, None
    for _ in range(restarts):
        s = rng.permutation(n)
        val = f(win_probs(P, s[None]))[0]
        while True:
            cand = np.tile(s, (len(a), 1))
            cand[np.arange(len(a)), a], cand[np.arange(len(a)), b] = s[b], s[a]
            vals = f(win_probs(P, cand))
            order = rng.permutation(len(a))
            improving = vals[order] > val + 1e-15
            if not improving.any():
                break
            k = order[np.argmax(improving)]
            s, val = cand[k], vals[k]
        if val > best_val:
            best_val, best_s = val, s
    return float(best_val), best_s
