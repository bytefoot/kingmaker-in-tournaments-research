"""E2: real(istic) matchups, BT vs BC (CLAUDE.md §5).

Archetype game (synthetic, sigma_g = 0.5, s = 0.8, sigma_v = 0.3 -> mean κ ≈ 0.62): for each game instance, sample N
matches per pair (N ∈ {10, 50}), fit BT (MLE) and BC (d = 2, λ chosen on an independent validation sample by log-loss),
score log-loss on a third independent test sample, and compute bracket metrics on the true, BT-fitted and BC-fitted P.
n = 8 exhaustive; n = 16 with local search (lower bounds).

ATP tennis (if data/raw/tennis_atp/atp_matches_2015..2019.csv exist): the 16 players with most matches among
themselves; time-ordered 80/20 split for log-loss; metrics on fits to all matches (n = 16, local search).

Usage: python experiments/e2_real.py [--quick | --full] [--seed S]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from km.bracket import exhaustive_metrics, local_search, objective
from km.data import load_tennis, make_archetype_game, sample_matches
from km.models import fit_bc, fit_bt_mle, kappa, log_loss, logit
from km.plotting import COLORS, FULL, save, use_style
from km.runlog import ROOT, write_csv

GAME = {"sigma_g": 0.5, "s": 0.8, "sigma_v": 0.3}
# BC regulariser and its λ grid (see km.models.fit_bc).  "paper" (Chen & Joachims' λΣ||b-c||²) is the main analysis; it
# needs a wide grid because it restrains vector scale only weakly (best λ ~1e3-1e4).  "ridge" is the sensitivity check.
LAMBDA_GRIDS = {"ridge": (0.01, 0.1, 1.0, 3.0, 10.0, 30.0, 100.0),
                "paper": (0.01, 0.1, 1.0, 10.0, 100.0, 1e3, 1e4, 1e5, 1e6)}
REG = "paper"
TENNIS_DIR = ROOT / "data" / "raw" / "tennis_atp"


def fit_both(train: np.ndarray, val: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, float]:
    """BT MLE on train; BC d=2 with λ minimising validation log-loss.  Returns (P_bt, P_bc, λ)."""
    fits = {lam: fit_bc(train, 2, lam, rng, reg=REG) for lam in LAMBDA_GRIDS[REG]}
    lam = min(fits, key=lambda l: log_loss(fits[l], val))
    return fit_bt_mle(train), fits[lam], lam


def metrics(P: np.ndarray, rng: np.random.Generator, restarts: int) -> dict:
    """Bracket metrics: exhaustive for n <= 8, local search (bounds) for n = 16."""
    n = len(P)
    s = logit(P).mean(axis=1)
    weakest = int(np.argmin(s))
    if n <= 8:
        m = exhaustive_metrics(P)
        R, km = m["R"], m["kingmakeable"]
    else:
        wmax = np.array([local_search(P, objective("max", i), rng, restarts)[0] for i in range(n)])
        wmin = -np.array([local_search(P, objective("min", i), rng, restarts)[0] for i in range(n)])
        km = np.array([local_search(P, objective("margin", i), rng, restarts)[0] > 1e-12 for i in range(n)])
        R = wmax - wmin
    return {"kappa": kappa(logit(P)), "K": int(km.sum()), "Pi": float(R.mean()), "R": R, "kingmakeable": km,
            "weakest_kingmakeable": bool(km[weakest])}


def run_archetype(n: int, n_instances: int, Ns, restarts: int, rng: np.random.Generator, data_seed: int) -> tuple[pd.DataFrame, list]:
    """``rng`` drives fitting and local search; games and match samples come from their own stream (``data_seed``),
    so runs with different regularisers see identical data."""
    rows, per_player = [], []
    data_rng = np.random.default_rng([data_seed, n])
    for inst in range(n_instances):
        game = make_archetype_game(n, data_rng, **GAME)
        truth = metrics(game["P"], rng, restarts)
        for N in Ns:
            train, val, test = (sample_matches(game["P"], N, data_rng) for _ in range(3))
            P_bt, P_bc, lam = fit_both(train, val, rng)
            for model, P in (("true", game["P"]), ("BT", P_bt), ("BC", P_bc)):
                m = truth if model == "true" else metrics(P, rng, restarts)
                jacc = (m["kingmakeable"] & truth["kingmakeable"]).sum() / max(1, (m["kingmakeable"] | truth["kingmakeable"]).sum())
                rows.append({"n": n, "instance": inst, "N_per_pair": N, "model": model, "lambda_bc": lam,
                             "test_logloss": log_loss(P, test), "kappa": m["kappa"], "K": m["K"], "Pi": m["Pi"],
                             "weakest_kingmakeable": m["weakest_kingmakeable"], "jaccard_kingmakeable_vs_true": jacc,
                             "max_abs_P_err": float(np.abs(P - game["P"]).max())})
                per_player += [{"n": n, "instance": inst, "N_per_pair": N, "model": model, "player": i,
                                "archetype": int(game["archetype"][i]), "R": float(m["R"][i]),
                                "kingmakeable": bool(m["kingmakeable"][i])} for i in range(n)]
    return pd.DataFrame(rows), per_player


def run_tennis(rng: np.random.Generator, restarts: int) -> tuple[pd.DataFrame, list, dict]:
    df = load_tennis(TENNIS_DIR, range(2015, 2020))
    counts = pd.concat([df.winner, df.loser]).value_counts()
    players = list(counts.index[:60])
    while len(players) > 16:  # drop whoever has the fewest matches against the remaining group
        sub = df[df.winner.isin(players) & df.loser.isin(players)]
        c = pd.concat([sub.winner, sub.loser]).value_counts().reindex(players).fillna(0)
        players.remove(c.idxmin())
    sub = df[df.winner.isin(players) & df.loser.isin(players)].reset_index(drop=True)
    idx = {p: k for k, p in enumerate(players)}

    def to_wins(part):
        w = np.zeros((16, 16), dtype=int)
        np.add.at(w, (part.winner.map(idx).to_numpy(), part.loser.map(idx).to_numpy()), 1)
        return w

    cut, inner = int(0.8 * len(sub)), int(0.64 * len(sub))  # time-ordered: train | test; λ chosen on train's last 20%
    P_bt_tr, P_bc_tr, lam = fit_both(to_wins(sub.iloc[:inner]), to_wins(sub.iloc[inner:cut]), rng)
    train, test = to_wins(sub.iloc[:cut]), to_wins(sub.iloc[cut:])
    P_bt_80, P_bc_80 = fit_bt_mle(train), fit_bc(train, 2, lam, rng, reg=REG)
    ll = {"BT": log_loss(P_bt_80, test), "BC": log_loss(P_bc_80, test),
          "coin": float(np.log(2))}
    allw = to_wins(sub)
    rows, per_player = [], []
    for model, P in (("BT", fit_bt_mle(allw)), ("BC", fit_bc(allw, 2, lam, rng, reg=REG))):
        m = metrics(P, rng, restarts)
        rows.append({"model": model, "test_logloss": ll[model], "lambda_bc": lam, "kappa": m["kappa"], "K_lb": m["K"],
                     "Pi_lb": m["Pi"], "weakest_kingmakeable_found": m["weakest_kingmakeable"]})
        per_player += [{"model": model, "player": players[i], "R_lb": float(m["R"][i]),
                        "kingmakeable_found": bool(m["kingmakeable"][i])} for i in range(16)]
    info = {"n_matches": len(sub), "n_train": cut, "n_test": len(sub) - cut, "players": players, "coin_logloss": ll["coin"]}
    return pd.DataFrame(rows), per_player, info


def plot(pp: pd.DataFrame, summary: pd.DataFrame, tennis_pp: pd.DataFrame | None) -> None:
    import matplotlib.pyplot as plt
    use_style()
    fig, axes = plt.subplots(1, 2, figsize=FULL)
    # panel 1: one archetype instance (n = 8, N = 50), per-player rigging range for true / BT / BC
    d = pp[(pp.n == 8) & (pp.instance == 0) & (pp.N_per_pair == 50)]
    ax = axes[0]
    width = 0.27
    for k, (model, color) in enumerate((("true", "#777777"), ("BT", COLORS["BT"]), ("BC", COLORS["BC"]))):
        g = d[d.model == model].sort_values("player")
        ax.bar(g.player + (k - 1) * width, g.R, width=width * 0.92, color=color, label={"true": "true P"}.get(model, f"{model} fit"))
    ax.set_xticks(range(8), [f"{p}\n{'RPS'[a]}" for p, a in zip(range(8), d[d.model == 'true'].sort_values('player').archetype)])
    ax.set_xlabel("player (archetype)")
    ax.set_ylabel(r"rigging range $R_i$ = Wmax − Wmin")
    ax.set_title("archetype game (one instance, N = 50)", fontsize=9)
    ax.legend(loc="upper right")
    ax = axes[1]
    if tennis_pp is not None:
        order = tennis_pp[tennis_pp.model == "BT"].sort_values("R_lb", ascending=False).player.tolist()
        for k, model in enumerate(("BT", "BC")):
            g = tennis_pp[tennis_pp.model == model].set_index("player").loc[order]
            ax.bar(np.arange(16) + (k - 0.5) * 0.4, g.R_lb, width=0.37, color=COLORS[model], label=f"{model} fit")
        surname = {"Juan Martin del Potro": "del Potro", "Roberto Bautista Agut": "Bautista Agut"}
        ax.set_xticks(range(16), [surname.get(p, p.split()[-1]) for p in order], rotation=60, ha="right", fontsize=7)
        ax.set_ylabel("rigging range (local-search bound)")
        ax.set_title("ATP 2015–2019, 16 players", fontsize=9)
        ax.legend()
    else:  # tennis unavailable: estimated vs true organiser power across archetype instances
        s = summary[summary.n == 8]
        true = s[s.model == "true"].set_index(["instance", "N_per_pair"]).Pi
        for model, mk in (("BT", "o"), ("BC", "s")):
            for N, fill in ((10, "none"), (50, None)):
                e = s[(s.model == model) & (s.N_per_pair == N)].set_index(["instance", "N_per_pair"]).Pi
                ax.scatter(true.loc[e.index], e, marker=mk, s=18, facecolors=fill or COLORS[model], edgecolors=COLORS[model],
                           label=f"{model} fit, N = {N}")
        lim = [0, max(s.Pi.max(), 0.01) * 1.05]
        ax.plot(lim, lim, color="#777777", lw=1)
        ax.set_xlim(lim), ax.set_ylim(lim)
        ax.set_xlabel("organiser power Π, true P")
        ax.set_ylabel("Π estimated from fitted P")
        ax.set_title("archetype game, n = 8, all instances", fontsize=9)
        ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    save(fig, "F3_rigging_bt_vs_bc")


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    ap.add_argument("--seed", type=int, default=20261124)
    ap.add_argument("--plot-only", action="store_true", help="redraw F3 from the E2 CSVs")
    ap.add_argument("--reg", choices=["paper", "ridge"], default="paper", help="BC regulariser (ridge = sensitivity check)")
    args = ap.parse_args()
    global REG
    REG = args.reg
    sfx = "" if REG == "paper" else "_ridge"
    if args.plot_only:
        rd = lambda name: pd.read_csv(ROOT / "outputs" / "csv" / f"{name}.csv", comment="#")
        tp = rd("e2_tennis_players") if (ROOT / "outputs" / "csv" / "e2_tennis_players.csv").exists() else None
        plot(rd("e2_archetype_players"), rd("e2_archetype"), tp)
        return
    full = not args.quick
    p = {"mode": "full" if full else "quick", "game": GAME, "lambdas": LAMBDA_GRIDS[REG], "N_per_pair": [10, 50],
         "n8_instances": 20 if full else 2, "n16_instances": 3 if full else 1, "restarts_n16": 10, "bc_restarts": 3, "bc_regulariser": REG}
    rng = np.random.default_rng(args.seed)
    t0 = time.time()
    s8, pp8 = run_archetype(8, p["n8_instances"], p["N_per_pair"], 0, rng, args.seed)
    print(f"archetype n=8 done {time.time() - t0:.0f}s")
    s16, pp16 = run_archetype(16, p["n16_instances"], p["N_per_pair"], p["restarts_n16"], rng, args.seed)
    print(f"archetype n=16 done {time.time() - t0:.0f}s")
    summary, pp = pd.concat([s8, s16], ignore_index=True), pd.DataFrame(pp8 + pp16)
    write_csv(summary, "e2_archetype" + sfx, seed=args.seed, params=p, runtime_s=time.time() - t0)
    write_csv(pp, "e2_archetype_players" + sfx, seed=args.seed, params=p, runtime_s=time.time() - t0)

    tennis_pp = None
    if all((TENNIS_DIR / f"atp_matches_{y}.csv").exists() for y in range(2015, 2020)):
        t_rows, t_pp, info = run_tennis(rng, p["restarts_n16"])
        p["tennis"] = info
        write_csv(t_rows, "e2_tennis" + sfx, seed=args.seed, params=p, runtime_s=time.time() - t0)
        tennis_pp = pd.DataFrame(t_pp)
        write_csv(tennis_pp, "e2_tennis_players" + sfx, seed=args.seed, params=p, runtime_s=time.time() - t0)
        print(t_rows.to_string(index=False))
    else:
        print("tennis: CSVs not found in data/raw/tennis_atp/ -- skipped")
    if REG == "paper":  # F3 shows the main analysis only
        plot(pp, summary, tennis_pp)
    pd.set_option("display.width", 200)
    print(summary.groupby(["n", "N_per_pair", "model"])[["test_logloss", "kappa", "K", "Pi", "weakest_kingmakeable",
                                                          "jaccard_kingmakeable_vs_true", "max_abs_P_err"]].mean().round(3))
    print(f"total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
