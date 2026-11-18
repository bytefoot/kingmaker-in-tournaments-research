from fractions import Fraction
from itertools import permutations, product

import numpy as np
import pytest

from km.bracket import (canonicalize, enumerate_brackets, exhaustive_metrics, n_brackets, standard_seeding,
                        win_probs, win_probs_mc)
from km.models import make_P


def test_bracket_counts():
    assert n_brackets(4) == 3 and n_brackets(8) == 315 and n_brackets(16) == 638_512_875
    assert len(enumerate_brackets(4)) == 3
    assert len(enumerate_brackets(8)) == 315


@pytest.mark.parametrize("n", [4, 8])
def test_brackets_are_the_equivalence_classes(n):
    reps = {tuple(b) for b in enumerate_brackets(n)}
    assert len(reps) == n_brackets(n)
    assert all(canonicalize(np.array(b)) == b for b in reps)
    classes = {}
    for perm in permutations(range(n)):
        classes.setdefault(canonicalize(np.array(perm)), 0)
        classes[canonicalize(np.array(perm))] += 1
    assert set(classes) == reps
    assert set(classes.values()) == {2 ** (n - 1)}  # every class has the same size


def test_standard_seeding():
    assert (standard_seeding(8) + 1).tolist() == [1, 8, 4, 5, 2, 7, 3, 6]
    assert (standard_seeding(4) + 1).tolist() == [1, 4, 2, 3]


def _brute_force_n4(P, seeding):
    """Exact W by enumerating all 2^3 match outcomes, in rational arithmetic."""
    W = [Fraction(0)] * 4
    a, b, c, d = seeding
    for r1, r2, r3 in product([0, 1], repeat=3):
        x = a if r1 == 0 else b
        y = c if r2 == 0 else d
        z = x if r3 == 0 else y
        p = (P[a][b] if r1 == 0 else P[b][a]) * (P[c][d] if r2 == 0 else P[d][c]) * (P[x][y] if r3 == 0 else P[y][x])
        W[z] += p
    return W


def test_dp_matches_exact_rational_n4():
    rng = np.random.default_rng(3)
    Pf = make_P(4, 0.5, 2.0, rng)
    P = [[Fraction(Pf[i, j]) for j in range(4)] for i in range(4)]  # exact rational copy of the float matrix
    for br in enumerate_brackets(4):
        exact = _brute_force_n4(P, br)
        assert np.allclose(win_probs(Pf, br), [float(w) for w in exact], atol=1e-15)


def test_dp_sums_to_one_and_is_seeding_invariant():
    rng = np.random.default_rng(4)
    P = make_P(8, 0.6, 3.0, rng)
    W = win_probs(P, enumerate_brackets(8))
    assert np.allclose(W.sum(axis=1), 1)
    seeding = rng.permutation(8)
    assert np.allclose(win_probs(P, seeding), win_probs(P, np.array(canonicalize(seeding))))


def test_dp_matches_mc():
    rng = np.random.default_rng(5)
    P = make_P(8, 0.5, 2.0, rng)
    br = rng.permutation(8)
    n_runs = 50_000
    W, Wmc = win_probs(P, br), win_probs_mc(P, br, n_runs, rng)
    se = np.sqrt(W * (1 - W) / n_runs)
    assert np.all(np.abs(W - Wmc) <= 4 * se + 1e-12)


def test_exhaustive_metrics_deterministic_transitive():
    # P1(a): deterministic transitive outcomes -> top player wins every bracket, K = 1
    P = np.triu(np.ones((8, 8)), 1)
    P = P + 0.5 * np.eye(8)  # player 0 beats everyone, 1 beats 2..7, ...
    m = exhaustive_metrics(P)
    assert m["K"] == 1 and m["kingmakeable"][0]
    assert np.allclose(m["W"][:, 0], 1)
