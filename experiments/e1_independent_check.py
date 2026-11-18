"""Independent re-derivation of the E1 bracket metrics (CLAUDE.md §8 "independent check").

Written from the definitions in CLAUDE.md §2 without using km.bracket: win probabilities come from a plain recursive
function over *all* 8! = 40,320 seedings (not the 315 canonical brackets), and K, Π are computed from those.
Only km.models.make_P is shared (it is checked separately in E0).  Compares with km.bracket.exhaustive_metrics.

Usage: python experiments/e1_independent_check.py [--quick | --full] [--seed S]
"""
from __future__ import annotations

import argparse
import time
from functools import lru_cache
from itertools import permutations

import numpy as np
import pandas as pd

from km.bracket import exhaustive_metrics
from km.models import make_P
from km.runlog import write_csv


def metrics_from_definitions(P: np.ndarray) -> tuple[int, float]:
    n = len(P)
    Pl = P.tolist()

    @lru_cache(maxsize=None)
    def win(players: tuple) -> dict:
        """P(each player comes out of this subtree), by direct recursion."""
        if len(players) == 1:
            return {players[0]: 1.0}
        h = len(players) // 2
        left, right = win(players[:h]), win(players[h:])
        out = {}
        for i, qi in left.items():
            out[i] = qi * sum(qj * Pl[i][j] for j, qj in right.items())
        for j, qj in right.items():
            out[j] = qj * sum(qi * Pl[j][i] for i, qi in left.items())
        return out

    wmax, wmin = [0.0] * n, [1.0] * n
    favourites = set()
    for seeding in permutations(range(n)):
        w = win(seeding)
        vals = sorted(w.values())
        for i, x in w.items():
            wmax[i], wmin[i] = max(wmax[i], x), min(wmin[i], x)
        if vals[-1] - vals[-2] > 1e-12:
            favourites.add(max(w, key=w.get))
    return len(favourites), sum(a - b for a, b in zip(wmax, wmin)) / n


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    ap.add_argument("--seed", type=int, default=777)
    args = ap.parse_args()
    reps = 3 if args.quick else 12
    rng = np.random.default_rng(args.seed)
    t0 = time.time()
    rows = []
    for variant in ("skew", "bc2"):
        for k in (0.0, 0.3, 0.6, 1.0):
            for _ in range(reps):
                P = make_P(8, k, 7.334, rng, variant)  # medium scale for n = 8 (outputs/csv/e1_scales.csv)
                K_ind, Pi_ind = metrics_from_definitions(P)
                m = exhaustive_metrics(P)
                rows.append({"variant": variant, "kappa": k, "K_independent": K_ind, "K_km": m["K"],
                             "Pi_independent": Pi_ind, "Pi_km": m["Pi"], "Pi_absdiff": abs(Pi_ind - m["Pi"])})
    df = pd.DataFrame(rows)
    write_csv(df, "e1_independent", seed=args.seed, params={"reps_per_cell": reps, "scale": 7.334}, runtime_s=time.time() - t0)
    print(f"{len(df)} matrices: K agrees on {(df.K_independent == df.K_km).sum()}/{len(df)}; "
          f"max |Π diff| = {df.Pi_absdiff.max():.2e}; {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
