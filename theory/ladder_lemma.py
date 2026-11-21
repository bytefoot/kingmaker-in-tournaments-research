"""Symbolic check of the Ladder Lemma (theory/P3.md) for ladder depth h = 0, 1, 2, 3.

BT with odds a_k = exp(g_k) > 0, P(u beats v) = a_u / (a_u + a_v).  Ladder Λ(x; y; w_1..w_h): y faces w_1, the
survivor faces w_2, ..., the final survivor faces x; Λ = P(x wins).  Lemma: a_x > a_y  =>  Λ(x; y; w) >= Λ(y; x; w).

We clear the (positive) denominators and factor the numerator of Λ(x; y; w) - Λ(y; x; w).  If it equals (x - y) times
a polynomial with only non-negative coefficients, the lemma is proved for that h (all variables are positive).
Usage: python theory/ladder_lemma.py
"""
import sympy as sp


def beat(u, v):
    return u / (u + v)


def ladder(x, y, ws):
    """P(x beats the survivor), with survivor distribution tracked exactly as {player: prob}."""
    dist = {y: sp.Integer(1)}
    for w in ws:
        new = {}
        for k, p in dist.items():
            new[k] = new.get(k, 0) + p * beat(k, w)
            new[w] = new.get(w, 0) + p * beat(w, k)
        dist = new
    return sum(p * beat(x, k) for k, p in dist.items())


def check(h):
    x, y = sp.symbols("x y", positive=True)
    ws = sp.symbols(f"z1:{h + 1}", positive=True)
    num, den = sp.fraction(sp.together(ladder(x, y, ws) - ladder(y, x, ws)))
    num = sp.expand(num)
    quotient, remainder = sp.div(num, x - y, x, y, *ws)
    coeffs = sp.Poly(sp.expand(quotient), x, y, *ws).coeffs()
    den_ok = all(c > 0 for c in sp.Poly(sp.expand(den), x, y, *ws).coeffs())
    print(f"h={h}: numerator divisible by (x-y): {remainder == 0}; quotient has {len(coeffs)} terms, "
          f"min coefficient {min(coeffs)}; all >= 0: {all(c >= 0 for c in coeffs)}; denominator all-positive coeffs: {den_ok}")
    return remainder == 0 and all(c >= 0 for c in coeffs) and den_ok


if __name__ == "__main__":
    for h in range(4):
        check(h)
