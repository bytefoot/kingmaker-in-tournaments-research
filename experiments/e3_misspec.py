"""E3: Elo seeding in a cyclic world (misspecification), CLAUDE.md §5.

Seed by a BT fit with standard seeding (1v8, 4v5, 2v7, 3v6).  "Predicted" W = DP under the BT fit; "actual" W = DP
under the cyclic P.  For each player we also report where the Elo-seeded bracket ranks among all 315 brackets for that
player's actual W (percentile = share of brackets giving the player a W no larger).

Worlds: make_P (n = 8, medium scale, skew cycles) at κ ∈ {0, 0.3, 0.6}, 200 matrices each (κ = 0 is the control:
the BT fit is exact there), and the archetype game (20 instances, 50 matches/pair): BT fit vs BC fit from the same data.
Usage: python experiments/e3_misspec.py [--quick | --full] [--seed S]
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from km.bracket import enumerate_brackets, standard_seeding, win_probs
from km.data import make_archetype_game, sample_matches
from km.models import bt_logits, fit_bc, fit_bt, fit_bt_mle, logit, make_P, sigmoid
from km.plotting import COLORS, FULL, MUTED, save, use_style
from km.runlog import ROOT, write_csv

SCALE_MEDIUM_N8 = 7.334  # outputs/csv/e1_scales.csv
GAME = {"sigma_g": 0.5, "s": 0.8, "sigma_v": 0.3}
BRACKETS = enumerate_brackets(8)


def elo_analysis(P_actual: np.ndarray, P_bt: np.ndarray) -> pd.DataFrame:
    """Per-player predicted vs actual W for the BT-seeded bracket, and its percentile among all brackets."""
    seeds = np.argsort(-logit(P_bt).mean(axis=1), kind="stable")  # seeds[r] = player with seed r+1
    bracket = seeds[standard_seeding(8)]
    pred, act = win_probs(P_bt, bracket), win_probs(P_actual, bracket)
    W_all = win_probs(P_actual, BRACKETS)
    pct = (W_all <= act[None, :] + 1e-12).mean(axis=0)
    seed_of = np.empty(8, dtype=int)
    seed_of[seeds] = np.arange(1, 9)
    return pd.DataFrame({"player": np.arange(8), "seed": seed_of, "W_pred": pred, "W_actual": act,
                         "gain": act - pred, "percentile": pct, "W_best": W_all.max(0), "W_worst": W_all.min(0)})


def plot(examples: dict) -> None:
    import matplotlib.pyplot as plt
    use_style()
    fig, axes = plt.subplots(1, 2, figsize=FULL)
    for ax, (title, df) in zip(axes, examples.items()):
        hi = max(df.W_pred.max(), df.W_actual.max()) * 1.1
        ax.plot([0, hi], [0, hi], color=MUTED, lw=1)
        ax.scatter(df.W_pred, df.W_actual, color=COLORS["BC"], s=28, edgecolors="white", linewidths=0.6, zorder=3)
        show = set(df.gain.abs().nlargest(3).index) | set(df.index[df.seed == 1])  # label seed 1 + 3 biggest misses
        for k, r in df.loc[sorted(show)].iterrows():
            right = r.W_pred > 0.6 * hi  # labels near the right edge go to the left of the point
            ax.annotate(f"seed {int(r.seed)} ({r.gain:+.2f})", (r.W_pred, r.W_actual), textcoords="offset points",
                        xytext=(-5 if right else 5, -9 if r.gain < 0 else 3), ha="right" if right else "left", fontsize=7)
        ax.set_xlim(0, hi), ax.set_ylim(0, hi)
        ax.set_xlabel("predicted title chance (BT fit)")
        ax.set_ylabel("actual title chance")
        ax.set_title(title, fontsize=9)
    fig.tight_layout()
    save(fig, "F4_elo_pred_vs_actual")


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    ap.add_argument("--seed", type=int, default=20261125)
    args = ap.parse_args()
    full = not args.quick
    p = {"mode": "full" if full else "quick", "kappas": [0.0, 0.3, 0.6], "reps": 200 if full else 10,
         "scale": SCALE_MEDIUM_N8, "game": GAME, "game_instances": 20 if full else 2, "N_per_pair": 50, "bc_lambda": 1000.0, "bc_regulariser": "paper"}
    rng = np.random.default_rng(args.seed)
    t0 = time.time()
    rows, examples = [], {}
    for k in p["kappas"]:
        for rep in range(p["reps"]):
            P = make_P(8, k, SCALE_MEDIUM_N8, rng)
            df = elo_analysis(P, sigmoid(bt_logits(fit_bt(P))))
            rows.append(df.assign(world=f"make_P kappa={k}", rep=rep))
            if k == 0.6 and rep == 0:
                examples["synthetic, κ = 0.6"] = df
    for inst in range(p["game_instances"]):
        game = make_archetype_game(8, rng, **GAME)
        wins = sample_matches(game["P"], p["N_per_pair"], rng)
        P_bt, P_bc = fit_bt_mle(wins), fit_bc(wins, 2, p["bc_lambda"], rng, reg="paper")
        df = elo_analysis(P_bc, P_bt)
        rows.append(df.assign(world="archetype: BC fit vs BT fit", rep=inst))
        rows.append(elo_analysis(game["P"], P_bt).assign(world="archetype: true P vs BT fit", rep=inst))
        if inst == 0:
            examples["archetype game: BC fit vs BT fit"] = df
    out = pd.concat(rows, ignore_index=True)
    write_csv(out, "e3_misspec", seed=args.seed, params=p, runtime_s=time.time() - t0)
    plot(examples)
    pd.set_option("display.width", 200)
    g = out.groupby(["world", "rep"])
    per = pd.DataFrame({"max_abs_gain": g.gain.apply(lambda x: x.abs().max()),
                        "top_seed_gain": g.apply(lambda d: d.loc[d.seed == 1, "gain"].iloc[0]),
                        "top_seed_pct": g.apply(lambda d: d.loc[d.seed == 1, "percentile"].iloc[0]),
                        "mean_pct": g.percentile.mean()}).reset_index()
    print(per.groupby("world")[["max_abs_gain", "top_seed_gain", "top_seed_pct", "mean_pct"]].agg(["mean", "sem"]).round(3).to_string())
    for title, df in examples.items():
        print("\n", title, "\n", df.round(3).to_string(index=False))
    print(f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
