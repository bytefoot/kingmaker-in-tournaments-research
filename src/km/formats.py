"""Tournament formats (CLAUDE.md §2), n = 8.  Each function returns (winner distribution over players, #matches).

| Format       | Rules                                                                             | Matches |
|--------------|-----------------------------------------------------------------------------------|---------|
| KO-random    | uniform random bracket; exact = average W over all brackets                       | 7       |
| KO-elo       | seed by BT fit to P, standard seeding (1v8, 4v5, 2v7, 3v6); exact DP              | 7       |
| Swiss        | 3 rounds; round 1 random; then pair within score groups, no rematches             | 12      |
|              | (backtracking pairing); most wins, ties uniformly random                          |         |
| Groups+KO    | random split into two round-robin groups of 4, top 2 by wins (ties random),       | 15      |
|              | semis A1 v B2 and B1 v A2, final                                                  |         |
| Round robin  | everyone plays everyone once; most wins, ties uniformly random                    | 28      |

Monte Carlo formats are vectorised over runs.  Ties are broken uniformly at random by adding U[0, 0.5) noise
to integer win counts, which never overturns a strict difference.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

import numpy as np

from .bracket import enumerate_brackets, simulate_knockout, standard_seeding, win_probs
from .models import fit_bt

FORMATS = ("KO-random", "KO-elo", "Swiss", "Groups+KO", "Round robin")


def _play(P: np.ndarray, a: np.ndarray, b: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """True where a beats b (elementwise)."""
    return rng.random(np.shape(a)) < P[a, b]


def _argmax_random_ties(wins: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    return np.argmax(wins + 0.5 * rng.random(wins.shape), axis=-1)


def ko_random(P: np.ndarray, rng: np.random.Generator | None = None, n_runs: int = 0) -> tuple[np.ndarray, int]:
    """Uniform random bracket.  Exact (average over all brackets) when n_runs == 0, else Monte Carlo.

    Each canonical bracket is the image of exactly 2^(n-1) seedings, so averaging over canonical brackets is the
    same as drawing a uniformly random seeding.
    """
    n = len(P)
    if n_runs == 0:
        return win_probs(P, enumerate_brackets(n)).mean(axis=0), n - 1
    seedings = rng.permuted(np.tile(np.arange(n), (n_runs, 1)), axis=1)
    return np.bincount(simulate_knockout(P, seedings, rng), minlength=n) / n_runs, n - 1


def ko_elo(P: np.ndarray) -> tuple[np.ndarray, int]:
    """Seed by the least-squares BT fit (ties by player index), standard seeding, exact DP."""
    n = len(P)
    by_strength = np.argsort(-fit_bt(P), kind="stable")  # by_strength[r] = player with seed r
    return win_probs(P, by_strength[standard_seeding(n)]), n - 1


def round_robin(P: np.ndarray, n_runs: int, rng: np.random.Generator) -> tuple[np.ndarray, int]:
    n = len(P)
    i, j = np.triu_indices(n, k=1)
    i_wins = rng.random((n_runs, len(i))) < P[i, j]
    eye = np.eye(n)
    wins = i_wins @ eye[i] + (~i_wins) @ eye[j]  # (n_runs, n) win counts
    return np.bincount(_argmax_random_ties(wins, rng), minlength=n) / n_runs, len(i)


def groups_ko(P: np.ndarray, n_runs: int, rng: np.random.Generator) -> tuple[np.ndarray, int]:
    n = len(P)
    assert n == 8, "Groups+KO is defined for n = 8"
    perm = rng.permuted(np.tile(np.arange(n), (n_runs, 1)), axis=1)
    rows = np.arange(n_runs)[:, None]
    qualifiers = []
    for group in (perm[:, :4], perm[:, 4:]):
        wins = np.zeros((n_runs, 4))
        for a, b in combinations(range(4), 2):
            a_wins = _play(P, group[:, a], group[:, b], rng)
            wins[:, a] += a_wins
            wins[:, b] += ~a_wins
        order = np.argsort(-(wins + 0.5 * rng.random(wins.shape)), axis=1)
        qualifiers.append(group[rows, order[:, :2]])  # columns: 1st, 2nd
    (A1, A2), (B1, B2) = qualifiers[0].T, qualifiers[1].T
    s1 = np.where(_play(P, A1, B2, rng), A1, B2)
    s2 = np.where(_play(P, B1, A2, rng), B1, A2)
    champ = np.where(_play(P, s1, s2, rng), s1, s2)
    return np.bincount(champ, minlength=n) / n_runs, 12 + 3


@lru_cache(maxsize=None)
def _matchings(n: int) -> np.ndarray:
    """All perfect matchings of positions 0..n-1 in depth-first (backtracking) order, shape (M, n/2, 2).

    Order: position 0 is paired with 1, then 2, ...; recursively on the remaining positions.  Taking the first
    matching that avoids rematches is exactly what a backtracking pairer produces.
    """
    def rec(pos: tuple[int, ...]):
        if not pos:
            yield ()
            return
        first, rest = pos[0], pos[1:]
        for k, partner in enumerate(rest):
            for m in rec(rest[:k] + rest[k + 1:]):
                yield ((first, partner),) + m
    return np.array(list(rec(tuple(range(n)))), dtype=np.int64)


def swiss(P: np.ndarray, n_runs: int, rng: np.random.Generator, n_rounds: int = 3) -> tuple[np.ndarray, int]:
    """Swiss system.  Round 1 random; later rounds order players by score (random within a score group) and pair
    by backtracking: the top unpaired player meets the next player in order they have not met, backtracking if
    the rest cannot be paired without rematches.  Vectorised: each run picks the first rematch-free matching in
    the depth-first list from :func:`_matchings`."""
    n = len(P)
    M = _matchings(n)  # (n_match, n/2, 2) positions
    rows = np.arange(n_runs)[:, None]
    score = np.zeros((n_runs, n))
    met = np.zeros((n_runs, n, n), dtype=bool)
    n_games = 0
    for r in range(n_rounds):
        if r == 0:
            order = rng.permuted(np.tile(np.arange(n), (n_runs, 1)), axis=1)
            pairs_pos = np.broadcast_to(M[0], (n_runs,) + M[0].shape)  # (0,1), (2,3), ...
        else:
            order = np.argsort(-(score + 0.5 * rng.random(score.shape)), axis=1)  # order[:, k] = player at position k
            pa, pb = order[:, M[:, :, 0]], order[:, M[:, :, 1]]  # (n_runs, n_match, n/2)
            ok = ~met[rows[:, :, None], pa, pb].any(axis=2)
            assert ok.any(axis=1).all(), "no rematch-free pairing exists"
            pairs_pos = M[np.argmax(ok, axis=1)]  # first valid matching per run
        a = np.take_along_axis(order, pairs_pos[:, :, 0], axis=1)
        b = np.take_along_axis(order, pairs_pos[:, :, 1], axis=1)
        score[rows, np.where(_play(P, a, b, rng), a, b)] += 1  # winners within a run are distinct
        met[rows, a, b] = met[rows, b, a] = True
        n_games += n // 2
    return np.bincount(_argmax_random_ties(score, rng), minlength=n) / n_runs, n_games


def run_format(name: str, P: np.ndarray, n_runs: int, rng: np.random.Generator) -> tuple[np.ndarray, int]:
    """Winner distribution and match count for the format ``name`` (one of :data:`FORMATS`)."""
    if name == "KO-random":
        return ko_random(P)
    if name == "KO-elo":
        return ko_elo(P)
    if name == "Swiss":
        return swiss(P, n_runs, rng)
    if name == "Groups+KO":
        return groups_ko(P, n_runs, rng)
    if name == "Round robin":
        return round_robin(P, n_runs, rng)
    raise ValueError(f"unknown format {name!r}")
