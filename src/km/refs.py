"""Reference notions of "who should win" (there may be no best player under cycles).

* Copeland: maximise #{j : P[i, j] > 0.5}; ties split credit equally.
* Borda: maximise the mean of P[i, :] excluding the diagonal; ties split credit equally.
* Nash: maximin strategy x of the symmetric zero-sum game with payoff A = P - 0.5 (skew-symmetric, value 0),
  by linear programming: maximise v s.t. Aᵀx ≥ v, Σx = 1, x ≥ 0.  The Nash set is the polytope
  {x ≥ 0, Σx = 1, Aᵀx ≥ 0}.  When it is not a single point we return its maximum-entropy element
  (Balduzzi et al. 2018, "Re-evaluating evaluation", Nash averaging).
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linprog, minimize


def _split_credit(score: np.ndarray, tol: float = 1e-12) -> np.ndarray:
    best = score >= score.max() - tol
    return best / best.sum()


def copeland(P: np.ndarray) -> np.ndarray:
    """Credit vector: 1/|S| on each Copeland winner (S = argmax of #opponents beaten with P > 0.5), else 0."""
    return _split_credit((P > 0.5).sum(axis=1).astype(float))


def borda(P: np.ndarray) -> np.ndarray:
    """Credit vector: 1/|S| on each Borda winner (S = argmax of mean off-diagonal win probability), else 0."""
    n = len(P)
    return _split_credit((P.sum(axis=1) - np.diag(P)) / (n - 1))


def nash_lp(P: np.ndarray) -> tuple[np.ndarray, float]:
    """One maximin strategy x and the game value v (0 up to solver tolerance for a valid P)."""
    n = len(P)
    A = P - 0.5
    c = np.r_[np.zeros(n), -1.0]  # minimise -v
    A_ub = np.c_[-A.T, np.ones(n)]  # v - (Aᵀx)_j ≤ 0
    res = linprog(c, A_ub=A_ub, b_ub=np.zeros(n), A_eq=np.r_[np.ones(n), 0.0][None, :], b_eq=[1.0],
                  bounds=[(0, None)] * n + [(None, None)], method="highs")
    assert res.status == 0, res.message
    return res.x[:n], res.x[n]


def nash_is_unique(P: np.ndarray, tol: float = 1e-6) -> bool:
    """True if every coordinate x_i has the same min and max (within tol) over the Nash polytope (2n LPs).

    The polytope is {x >= 0, Σx = 1, Aᵀx >= v - 1e-12}, where v is the LP game value (0 up to solver error).
    Relaxing by a fixed slack instead would let x drift by ~slack/|A|, which is large when payoffs are tiny.
    """
    n = len(P)
    A = P - 0.5
    slack = max(0.0, -nash_lp(P)[1]) + 1e-12
    for i in range(n):
        lo_hi = []
        for sign in (1.0, -1.0):
            c = np.zeros(n)
            c[i] = sign
            res = linprog(c, A_ub=-A.T, b_ub=np.full(n, slack), A_eq=np.ones((1, n)), b_eq=[1.0],
                          bounds=[(0, None)] * n, method="highs")
            assert res.status == 0, res.message
            lo_hi.append(res.x[i])
        if abs(lo_hi[0] - lo_hi[1]) > tol:
            return False
    return True


def nash_maxent(P: np.ndarray) -> np.ndarray:
    """Maximum-entropy element of the Nash polytope (SLSQP from the LP solution)."""
    n = len(P)
    A = P - 0.5
    x_lp, v = nash_lp(P)
    slack = max(0.0, -v) + 1e-10
    x0 = 0.99 * x_lp + 0.01 / n  # interior-ish start
    eps = 1e-12
    res = minimize(lambda x: np.sum(x * np.log(x + eps)), x0, jac=lambda x: np.log(x + eps) + 1.0,
                   method="SLSQP", bounds=[(0, 1)] * n,
                   constraints=[{"type": "eq", "fun": lambda x: x.sum() - 1.0},
                                {"type": "ineq", "fun": lambda x: A.T @ x + slack}],
                   options={"ftol": 1e-13, "maxiter": 500})
    assert res.success, res.message
    x = np.clip(res.x, 0, None)
    return x / x.sum()


def nash(P: np.ndarray) -> dict:
    """Nash mass of each player: the LP solution if the Nash set is a single point, else the max-entropy Nash.

    Returns {"x": strategy, "unique": bool, "method": "lp" | "maxent", "value": game value}.
    """
    x, v = nash_lp(P)
    if nash_is_unique(P):
        return {"x": x, "unique": True, "method": "lp", "value": v}
    return {"x": nash_maxent(P), "unique": False, "method": "maxent", "value": v}
