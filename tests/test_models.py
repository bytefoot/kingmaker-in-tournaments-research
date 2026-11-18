import numpy as np
import pytest

from km.models import (CYCLE_VARIANTS, bc_logits, bt_logits, fit_bt, hodge_split, kappa, logit, make_L, make_P,
                       sigmoid)


def test_sigmoid_logit_roundtrip():
    x = np.linspace(-20, 20, 41)
    assert np.allclose(logit(sigmoid(x)), x, atol=1e-6)
    assert sigmoid(np.array([1e6, -1e6])).tolist() == [1.0, 0.0]


@pytest.mark.parametrize("n", [3, 4, 8, 16])
def test_hodge_split_orthogonal(n):
    rng = np.random.default_rng(n)
    U = np.triu(rng.standard_normal((n, n)), 1)
    L = U - U.T
    T, C = hodge_split(L)
    assert abs(np.sum(T * C)) < 1e-12
    assert np.allclose(C.sum(axis=1), 0)
    assert np.allclose(T + C, L) and np.allclose(C, -C.T)


def test_kappa_of_pure_parts():
    rng = np.random.default_rng(0)
    assert kappa(bt_logits(rng.standard_normal(8))) < 1e-28
    rps = np.array([[0, 1, -1], [-1, 0, 1], [1, -1, 0]], float)
    assert abs(kappa(rps) - 1) < 1e-15


@pytest.mark.parametrize("variant", CYCLE_VARIANTS)
@pytest.mark.parametrize("k", [0.0, 0.3, 0.7, 1.0])
def test_make_P_hits_target_kappa(variant, k):
    rng = np.random.default_rng(1)
    L = make_L(8, k, 2.0, rng, variant)
    assert abs(kappa(L) - k) < 1e-9
    P = sigmoid(L)
    assert np.allclose(P + P.T, 1) and np.allclose(np.diag(P), 0.5)


def test_make_P_seeded_reproducible():
    a = make_P(8, 0.4, 1.0, np.random.default_rng(7))
    b = make_P(8, 0.4, 1.0, np.random.default_rng(7))
    assert np.array_equal(a, b)


def test_bc_logits_skew_and_bt_special_case():
    rng = np.random.default_rng(2)
    g = rng.standard_normal(5)
    L = bc_logits(g, rng.standard_normal((5, 2)), rng.standard_normal((5, 2)))
    assert np.allclose(L, -L.T)
    assert np.allclose(bc_logits(g, np.zeros((5, 2)), np.zeros((5, 2))), bt_logits(g))


def test_fit_bt_recovers_bt():
    g = np.array([1.0, 0.3, -0.2, -1.1])
    assert np.allclose(fit_bt(sigmoid(bt_logits(g))), g - g.mean())
