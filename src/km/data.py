"""Data sources for E2.

Archetype game (purely synthetic; not based on any real game's rules).  It stands in for a strategy game with three
play styles that counter each other in a rock-paper-scissors loop.  Each archetype k is a direction u_k in R^2 at
angle 120°·k; an archetype-k player has blade ≈ s·u_k and chest ≈ s·u_{k-1}, so in the BC model
b_i·c_j - b_j·c_i = s²(1 - cos 240°) = 1.5 s² > 0 when i is archetype k and j is archetype k+1: k beats k+1, and
same-archetype pairs cancel.  Each player adds individual noise (sd sigma_v) to both vectors and a personal skill
g ~ N(0, sigma_g²).

Tennis: loader for Jeff Sackmann's tennis_atp CSVs (atp_matches_YYYY.csv) placed in data/raw/tennis_atp/.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .models import bc_logits, sigmoid


def make_archetype_game(n: int, rng: np.random.Generator, sigma_g: float, s: float, sigma_v: float = 0.3) -> dict:
    """Returns {"P", "L", "archetype", "g", "blade", "chest"}; archetypes assigned round-robin (n=8 -> 3,3,2)."""
    arch = np.arange(n) % 3
    u = np.stack([np.cos(2 * np.pi * np.arange(3) / 3), np.sin(2 * np.pi * np.arange(3) / 3)], axis=1)
    blade = s * u[arch] + sigma_v * rng.standard_normal((n, 2))
    chest = s * u[(arch - 1) % 3] + sigma_v * rng.standard_normal((n, 2))
    g = sigma_g * rng.standard_normal(n)
    L = bc_logits(g, blade, chest)
    return {"P": sigmoid(L), "L": L, "archetype": arch, "g": g, "blade": blade, "chest": chest}


def sample_matches(P: np.ndarray, n_per_pair: int, rng: np.random.Generator) -> np.ndarray:
    """Win counts: ``wins[i, j]`` = times i beat j in ``n_per_pair`` independent matches per pair."""
    n = len(P)
    i, j = np.triu_indices(n, 1)
    k = rng.binomial(n_per_pair, P[i, j])
    wins = np.zeros((n, n), dtype=int)
    wins[i, j], wins[j, i] = k, n_per_pair - k
    return wins


def load_tennis(raw_dir: Path, years: range) -> pd.DataFrame:
    """All matches from atp_matches_YYYY.csv as (date, winner, loser), sorted by date then match number."""
    frames = []
    for y in years:
        df = pd.read_csv(Path(raw_dir) / f"atp_matches_{y}.csv", usecols=["tourney_date", "match_num", "winner_name", "loser_name"])
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df.tourney_date.astype(str), format="%Y%m%d")
    return df.sort_values(["date", "match_num"]).rename(columns={"winner_name": "winner", "loser_name": "loser"})[["date", "winner", "loser"]]
