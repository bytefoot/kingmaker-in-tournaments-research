import numpy as np
import pytest

from km.bracket import enumerate_brackets, win_probs
from km.formats import FORMATS, _matchings, ko_random, run_format, swiss
from km.models import bt_logits, make_P, sigmoid
from km.refs import borda, copeland, nash

EXPECTED_MATCHES = {"KO-random": 7, "KO-elo": 7, "Swiss": 12, "Groups+KO": 15, "Round robin": 28}


@pytest.mark.parametrize("name", FORMATS)
def test_format_match_counts_and_distribution(name):
    rng = np.random.default_rng(0)
    dist, n_matches = run_format(name, make_P(8, 0.5, 2.0, rng), 2_000, rng)
    assert n_matches == EXPECTED_MATCHES[name]
    assert dist.shape == (8,) and abs(dist.sum() - 1) < 1e-12 and (dist >= 0).all()


def test_ko_random_exact_vs_mc():
    rng = np.random.default_rng(1)
    P = make_P(8, 0.7, 3.0, rng)
    exact, _ = ko_random(P)
    mc, _ = ko_random(P, rng, n_runs=100_000)
    assert np.all(np.abs(exact - mc) <= 4 * np.sqrt(exact * (1 - exact) / 100_000))
    assert np.allclose(exact, win_probs(P, enumerate_brackets(8)).mean(axis=0))


def test_matchings_dfs_order():
    M = _matchings(4)
    assert M.tolist() == [[[0, 1], [2, 3]], [[0, 2], [1, 3]], [[0, 3], [1, 2]]]
    assert len(_matchings(8)) == 105


def test_swiss_unique_3_0_player():
    # with 8 players and 3 rounds exactly one player goes 3-0, so a player who wins every match always wins
    P = sigmoid(60 * np.sign(bt_logits(-np.arange(8.0))))
    dist, _ = swiss(P, 1_000, np.random.default_rng(2))
    assert dist[0] == 1.0


def test_nash_rps_and_bt():
    rps = np.array([[0.5, 0.9, 0.1], [0.1, 0.5, 0.9], [0.9, 0.1, 0.5]])
    out = nash(rps)
    assert out["unique"] and np.allclose(out["x"], 1 / 3, atol=1e-8) and abs(out["value"]) < 1e-9
    P = sigmoid(bt_logits(np.array([0.2, 1.5, -0.3, 0.9])))
    out = nash(P)
    assert out["unique"] and np.allclose(out["x"], [0, 1, 0, 0], atol=1e-8)


def test_nash_maxent_on_duplicated_player():
    # RPS with scissors duplicated: Nash set {x_S + x_S' = 1/3}; max-entropy splits it evenly
    P = np.array([[0.5, 0.1, 0.9, 0.9],
                  [0.9, 0.5, 0.1, 0.1],
                  [0.1, 0.9, 0.5, 0.5],
                  [0.1, 0.9, 0.5, 0.5]])
    out = nash(P)
    assert not out["unique"] and out["method"] == "maxent"
    assert np.allclose(out["x"], [1 / 3, 1 / 3, 1 / 6, 1 / 6], atol=1e-5)


def test_copeland_borda():
    rps = np.array([[0.5, 0.9, 0.1], [0.1, 0.5, 0.9], [0.9, 0.1, 0.5]])
    assert np.allclose(copeland(rps), 1 / 3) and np.allclose(borda(rps), 1 / 3)
    P = sigmoid(bt_logits(np.array([0.2, 1.5, -0.3])))
    assert copeland(P).tolist() == [0, 1, 0] and borda(P).tolist() == [0, 1, 0]


def test_nash_unique_on_low_scale_bt():
    # regression: a fixed LP slack once made near-flat BT games look non-unique
    rng = np.random.default_rng(3)
    for scale in (0.05, 1.0, 7.0):
        out = nash(make_P(8, 0.0, scale, rng))
        assert out["unique"] and out["x"].max() > 1 - 1e-6
