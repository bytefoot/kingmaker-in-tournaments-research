"""Matchup models: Bradley-Terry (BT), Blade-Chest (BC), the Hodge split and the synthetic generator.

Conventions (CLAUDE.md §2)
--------------------------
* ``P[i, j]`` is the probability that player i beats player j; ``P + P.T = 1`` and ``diag(P) = 0.5``.
* ``L = logit(P)`` is skew-symmetric.
* BT:  ``L[i, j] = g[i] - g[j]``.
* BC (inner-product form, Chen & Joachims 2016, eq. 4):
  ``L[i, j] = g[i] - g[j] + b[i]·c[j] - b[j]·c[i]`` with blade ``b[i]`` and chest ``c[i]`` in R^d.

Hodge split on the complete graph
---------------------------------
For skew-symmetric L, ``s = L.mean(axis=1)`` and ``T[i, j] = s[i] - s[j]`` is the ranking (gradient) part,
``C = L - T`` is the cyclic part (every row of C sums to 0).  T and C are orthogonal in the Frobenius inner
product, so ``||L||² = ||T||² + ||C||²`` and the cyclic share is ``κ = ||C||_F² / ||L||_F²`` ∈ [0, 1].
"""
from __future__ import annotations

import numpy as np

CYCLE_VARIANTS = ("skew", "bc1", "bc2")


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Logistic function, written via tanh so it never overflows."""
    return 0.5 * (1.0 + np.tanh(0.5 * np.asarray(x, dtype=float)))


def logit(p: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Inverse of :func:`sigmoid`; probabilities are clipped to [eps, 1-eps]."""
    p = np.clip(np.asarray(p, dtype=float), eps, 1.0 - eps)
    return np.log(p) - np.log1p(-p)


def hodge_split(L: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split a skew-symmetric L into ranking part T (``T[i,j] = s[i]-s[j]``, ``s`` = row means) and cyclic part C = L - T."""
    s = L.mean(axis=1)
    T = s[:, None] - s[None, :]
    return T, L - T


def kappa(L: np.ndarray) -> float:
    """Cyclic share κ = ||C||_F² / ||L||_F² of a skew-symmetric logit matrix (0 for L = 0)."""
    total = float(np.sum(L**2))
    if total == 0.0:
        return 0.0
    _, C = hodge_split(L)
    return float(np.sum(C**2)) / total


def bt_logits(g: np.ndarray) -> np.ndarray:
    """BT logits ``L[i, j] = g[i] - g[j]``."""
    g = np.asarray(g, dtype=float)
    return g[:, None] - g[None, :]


def bc_logits(g: np.ndarray, blade: np.ndarray, chest: np.ndarray) -> np.ndarray:
    """BC-inner logits ``L[i, j] = g[i] - g[j] + b[i]·c[j] - b[j]·c[i]``; blade/chest have shape (n, d)."""
    M = blade @ chest.T
    return bt_logits(g) + M - M.T


def _unit(A: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(A)
    if norm < 1e-12:
        raise ValueError("cannot normalise a (numerically) zero matrix")
    return A / norm


def random_ranking_unit(n: int, rng: np.random.Generator) -> np.ndarray:
    """T̂: BT logits from g ~ N(0, 1), normalised to ||T̂||_F = 1."""
    return _unit(bt_logits(rng.standard_normal(n)))


def random_cyclic_unit(n: int, rng: np.random.Generator, variant: str = "skew") -> np.ndarray:
    """Ĉ: a unit-norm purely cyclic skew-symmetric matrix.

    ``variant="skew"``: upper triangle N(0, 1) (unstructured cycles).
    ``variant="bc1"`` / ``"bc2"``: ``b c^T - c b^T`` from random blade/chest vectors in R^1 / R^2 (structured cycles).
    In every case the ranking part is subtracted before normalising, so Ĉ ⟂ any BT matrix.
    """
    if variant == "skew":
        U = np.triu(rng.standard_normal((n, n)), k=1)
        A = U - U.T
    elif variant in ("bc1", "bc2"):
        d = int(variant[-1])
        A = bc_logits(np.zeros(n), rng.standard_normal((n, d)), rng.standard_normal((n, d)))
    else:
        raise ValueError(f"unknown cycle variant {variant!r}; choose from {CYCLE_VARIANTS}")
    _, C = hodge_split(A)
    return _unit(C)


def make_L(n: int, kappa_target: float, scale: float, rng: np.random.Generator, variant: str = "skew") -> np.ndarray:
    """Synthetic logits ``L = scale · (sqrt(1-κ)·T̂ + sqrt(κ)·Ĉ)`` with realised cyclic share exactly κ (asserted to 1e-9)."""
    if not 0.0 <= kappa_target <= 1.0:
        raise ValueError("kappa_target must lie in [0, 1]")
    if scale <= 0:
        raise ValueError("scale must be positive (use P = 0.5 everywhere for scale 0)")
    T_hat = random_ranking_unit(n, rng)
    C_hat = random_cyclic_unit(n, rng, variant)
    L = scale * (np.sqrt(1.0 - kappa_target) * T_hat + np.sqrt(kappa_target) * C_hat)
    realised = kappa(L)
    assert abs(realised - kappa_target) < 1e-9, f"realised κ {realised} != target {kappa_target}"
    return L


def make_P(n: int, kappa_target: float, scale: float, rng: np.random.Generator, variant: str = "skew") -> np.ndarray:
    """Synthetic win-probability matrix ``P = sigmoid(make_L(...))``; see :func:`make_L`."""
    return sigmoid(make_L(n, kappa_target, scale, rng, variant))


def fit_bt(P: np.ndarray) -> np.ndarray:
    """Least-squares BT fit to ``L = logit(P)``: minimises Σ (L[i,j] - g[i] + g[j])², solved by g = row means of L.

    This is exactly the Hodge ranking potential ``s``; g is centred (sums to 0).
    """
    return logit(P).mean(axis=1)


SCALE_TARGETS = {"close": 0.08, "medium": 0.18, "decisive": 0.32}


def calibrate_scale(n: int, target: float, rng: np.random.Generator, n_draws: int = 4000) -> float:
    """Scale at which, at κ = 0, the mean off-diagonal |P - 0.5| over random T̂ equals ``target``.

    Uses one fixed set of T̂ draws (common random numbers), so the mean is a smooth increasing function of scale and
    a bracketing root-finder applies.
    """
    from scipy.optimize import brentq

    off = ~np.eye(n, dtype=bool)
    T = np.stack([random_ranking_unit(n, rng)[off] for _ in range(n_draws)])
    return float(brentq(lambda s: np.mean(np.abs(sigmoid(s * T) - 0.5)) - target, 1e-6, 1e4, xtol=1e-10))
