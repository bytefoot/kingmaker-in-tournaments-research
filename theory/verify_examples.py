"""Exact re-verification of the P2 and P4 examples from CLAUDE.md §4.

Written from the definitions, independently of src/km: a 4-player bracket {x, y} | {z, w} is won by i in {x, y} with
probability P[i, other] · Σ_{j in {z,w}} P(j wins its semi) · P[i, j].  P2 uses sympy (exact exp), P4 uses Fraction.
Usage: python theory/verify_examples.py
"""
from fractions import Fraction
from itertools import combinations

import sympy as sp


def four_player_win(P, bracket):
    """Exact W for bracket ((a, b), (c, d)); P is any indexable exact matrix."""
    (a, b), (c, d) = bracket
    semi = {a: P[a][b], b: P[b][a], c: P[c][d], d: P[d][c]}
    W = {}
    for mine, theirs in (((a, b), (c, d)), ((c, d), (a, b))):
        for i in mine:
            W[i] = semi[i] * sum(semi[j] * P[i][j] for j in theirs)
    return W


def all_brackets4():
    return [((0, j), tuple(k for k in (1, 2, 3) if k != j)) for j in (1, 2, 3)]


def p2():
    names = "ABCD"
    g = [sp.Rational(1), sp.Rational(95, 100), sp.Rational(8, 10), sp.Rational(-3)]
    P = [[sp.Rational(1, 2) if i == j else 1 / (1 + sp.exp(g[j] - g[i])) for j in range(4)] for i in range(4)]
    print("P2: BT with gamma = (1.0, 0.95, 0.8, -3.0) for A, B, C, D")
    for br in all_brackets4():
        W = four_player_win(P, br)
        total = sp.N(sum(W.values()), 30)  # exact expressions evaluated to 30 digits
        label = "{" + ",".join(names[i] for i in br[0]) + "} | {" + ",".join(names[i] for i in br[1]) + "}"
        vals = ", ".join(f"W_{names[i]} = {sp.N(W[i], 15)}" for i in range(4))
        fav = max(range(4), key=lambda i: sp.N(W[i], 30))
        print(f"  {label}: {vals}  (sum = {total}); favourite {names[fav]}")


def p4():
    names = "ABCD"
    f = Fraction
    upper = {(0, 1): f(95, 100), (0, 2): f(20, 100), (0, 3): f(62, 100), (1, 2): f(72, 100), (1, 3): f(50, 100), (2, 3): f(39, 100)}
    P = [[f(1, 2)] * 4 for _ in range(4)]
    for (i, j), p in upper.items():
        P[i][j], P[j][i] = p, 1 - p
    print("\nP4: cyclic 4-player matrix (row beats column)")
    for i in range(4):
        print(f"  {names[i]}: mean win rate vs others = {float(sum(P[i][j] for j in range(4) if j != i) / 3):.4f}"
              f"  (exact {sum(P[i][j] for j in range(4) if j != i) / 3})")
    for br in all_brackets4():
        W = four_player_win(P, br)
        assert sum(W.values()) == 1
        label = "{" + ",".join(names[i] for i in br[0]) + "} | {" + ",".join(names[i] for i in br[1]) + "}"
        fav = max(W, key=W.get)
        print(f"  {label}: " + ", ".join(f"W_{names[i]} = {W[i]} = {float(W[i]):.4f}" for i in range(4)) + f"; favourite {names[fav]}")


if __name__ == "__main__":
    p2()
    p4()
