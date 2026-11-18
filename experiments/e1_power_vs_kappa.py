"""E1: organiser power vs cyclic share κ (CLAUDE.md §5).

n = 8, exhaustive over all 315 brackets: κ ∈ {0, 0.1, ..., 1} × 3 scales × M matrices × {skew, bc2} cycles.
Per matrix: K (number of kingmakeable players), Π (mean rigging range) and whether the weakest player is kingmakeable.
"Weakest" = lowest Hodge ranking potential s = row mean of L (= the least-squares BT strength); we also record the
lowest-Borda player (lowest mean win probability), which can differ when κ > 0.
Then: local-search validation at n = 8 against the exhaustive optimum, and a reduced n = 16 run with local search
(lower bounds on Wmax and K, upper bounds on Wmin).

Usage: python experiments/e1_power_vs_kappa.py [--quick | --full] [--seed S]
Outputs: outputs/csv/e1_scales.csv, e1_n8_raw.csv, e1_n8_summary.csv, e1_ls_validation.csv, e1_n16.csv,
         outputs/fig/F2_power_vs_kappa_skew.pdf, F2_power_vs_kappa_bc2.pdf
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from km.bracket import enumerate_brackets, exhaustive_metrics, local_search, objective
from km.models import SCALE_TARGETS, calibrate_scale, logit, make_P
from km.plotting import COLORS, FULL, save, use_style

MARKERS = {"close": "o", "medium": "s", "decisive": "^"}
from km.runlog import write_csv

KAPPAS = np.round(np.linspace(0, 1, 11), 2)


def boot_ci(x: np.ndarray, rng: np.random.Generator, n_boot: int = 2000) -> tuple[float, float]:
    """95% percentile bootstrap CI of the mean."""
    x = np.asarray(x, dtype=float)
    means = x[rng.integers(0, len(x), (n_boot, len(x)))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def player_ranks(P: np.ndarray) -> tuple[np.ndarray, int, int]:
    """Rank of each player by Hodge potential (1 = strongest), the s-weakest and the Borda-weakest player."""
    s = logit(P).mean(axis=1)
    rank = np.empty(len(P), dtype=int)
    rank[np.argsort(-s)] = np.arange(1, len(P) + 1)
    borda = (P.sum(axis=1) - 0.5) / (len(P) - 1)
    return rank, int(np.argmin(s)), int(np.argmin(borda))


def run_n8(scales: dict, reps: int, rng: np.random.Generator) -> pd.DataFrame:
    brackets = enumerate_brackets(8)
    rows = []
    for variant in ("skew", "bc2"):
        for scale_name, scale in scales.items():
            for k in KAPPAS:
                for rep in range(reps):
                    P = make_P(8, k, scale, rng, variant)
                    m = exhaustive_metrics(P, brackets)
                    rank, weak_s, weak_b = player_ranks(P)
                    km = m["kingmakeable"]
                    rows.append({"variant": variant, "scale": scale_name, "kappa": k, "rep": rep, "K": m["K"], "Pi": m["Pi"],
                                 "weakest_kingmakeable": bool(km[weak_s]), "borda_weakest_kingmakeable": bool(km[weak_b]),
                                 "worst_rank_kingmakeable": int(rank[km].max()),
                                 "mean_abs_P_minus_half": float(np.abs(P - 0.5)[~np.eye(8, dtype=bool)].mean())})
    return pd.DataFrame(rows)


def summarise(raw: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    out = []
    for (variant, scale, k), g in raw.groupby(["variant", "scale", "kappa"], sort=False):
        row = {"variant": variant, "scale": scale, "kappa": k, "n_matrices": len(g)}
        for col in ("K", "Pi", "weakest_kingmakeable", "borda_weakest_kingmakeable", "worst_rank_kingmakeable"):
            lo, hi = boot_ci(g[col].to_numpy(), rng)
            row.update({col: g[col].mean(), f"{col}_lo": lo, f"{col}_hi": hi})
        out.append(row)
    return pd.DataFrame(out)


def validate_local_search(scale: float, n_mats: int, restart_grid: tuple, rng: np.random.Generator) -> pd.DataFrame:
    """At n = 8, how often does local search reach the exhaustive optimum of W_i (max/min) and find kingmakeability?"""
    rows = []
    for t in range(n_mats):
        k = KAPPAS[t % len(KAPPAS)]
        P = make_P(8, k, scale, rng)
        m = exhaustive_metrics(P)
        W = m["W"]
        for i in range(8):
            others = np.delete(W, i, axis=1).max(axis=1)
            margin_exact = float((W[:, i] - others).max())
            exact = {"max": m["Wmax"][i], "min": -m["Wmin"][i], "margin": margin_exact}
            for R in restart_grid:
                for kind in ("max", "min", "margin"):
                    val, _ = local_search(P, objective(kind, i), rng, restarts=R)
                    rows.append({"matrix": t, "kappa": k, "player": i, "restarts": R, "objective": kind,
                                 "exact": exact[kind], "local": val, "gap": exact[kind] - val,
                                 "hit": abs(exact[kind] - val) < 1e-12,
                                 "kingmakeable_exact": margin_exact > 1e-12, "kingmakeable_found": val > 1e-12 if kind == "margin" else None})
    return pd.DataFrame(rows)


def run_n16(scale: float, kappas, reps: int, restarts: int, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for k in kappas:
        for rep in range(reps):
            P = make_P(16, k, scale, rng)
            rank, weak_s, _ = player_ranks(P)
            wmax = np.array([local_search(P, objective("max", i), rng, restarts)[0] for i in range(16)])
            wmin = -np.array([local_search(P, objective("min", i), rng, restarts)[0] for i in range(16)])
            km = np.array([local_search(P, objective("margin", i), rng, restarts)[0] > 1e-12 for i in range(16)])
            rows.append({"kappa": k, "rep": rep, "K_lb": int(km.sum()), "Pi_lb": float(np.mean(wmax - wmin)),
                         "weakest_kingmakeable_found": bool(km[weak_s]),
                         "worst_rank_kingmakeable": int(rank[km].max()) if km.any() else 0})
    return pd.DataFrame(rows)


def plot(summary: pd.DataFrame, variant: str) -> None:
    import matplotlib.pyplot as plt
    use_style()
    d = summary[summary.variant == variant]
    fig, axes = plt.subplots(1, 2, figsize=FULL)
    for scale in SCALE_TARGETS:
        g = d[d.scale == scale]
        for ax, col in zip(axes, ("K", "Pi")):
            ax.fill_between(g.kappa, g[f"{col}_lo"], g[f"{col}_hi"], color=COLORS[scale], alpha=0.2, lw=0)
            ax.plot(g.kappa, g[col], color=COLORS[scale], marker=MARKERS[scale], label=f"{scale} (mean |P−½| = {SCALE_TARGETS[scale]})")
    axes[0].set_ylabel("kingmakeable players K (of 8)")
    axes[1].set_ylabel("organiser power Π")
    for ax in axes:
        ax.set_xlabel("cyclic share κ")
        ax.set_xlim(0, 1)
    axes[0].set_ylim(bottom=0)
    axes[1].set_ylim(bottom=0)
    axes[0].legend(loc="upper left", title="match decisiveness", title_fontsize=8)
    fig.tight_layout()
    save(fig, f"F2_power_vs_kappa_{variant}")


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    ap.add_argument("--seed", type=int, default=20261119)
    ap.add_argument("--plot-only", action="store_true", help="redraw F2 from outputs/csv/e1_n8_summary.csv")
    args = ap.parse_args()
    if args.plot_only:
        summary = pd.read_csv("outputs/csv/e1_n8_summary.csv", comment="#")
        for v in ("skew", "bc2"):
            plot(summary, v)
        return
    full = not args.quick
    p = {"mode": "full" if full else "quick", "n8_reps": 200 if full else 10, "ls_val_matrices": 33 if full else 3,
         "ls_restart_grid": [1, 5, 10, 50] if full else [1, 10], "n16_kappas": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
         "n16_reps": 20 if full else 1, "n16_restarts": 10, "scale_targets": SCALE_TARGETS, "cycle_variants_n8": ["skew", "bc2"],
         "n16_variant": "skew", "n16_scale": "medium", "weakest": "lowest Hodge potential s"}
    rngs = [np.random.default_rng([args.seed, i]) for i in range(6)]  # independent stream per section

    t0 = time.time()
    scales = {n: {name: round(calibrate_scale(n, t, rngs[0]), 3) for name, t in SCALE_TARGETS.items()} for n in (8, 16)}
    p["scales"] = scales
    write_csv(pd.DataFrame([{"n": n, "scale_name": k, "target_mean_abs_P": SCALE_TARGETS[k], "scale": v}
                            for n, d in scales.items() for k, v in d.items()]), "e1_scales", seed=args.seed, params=p, runtime_s=time.time() - t0)
    print("scales:", scales)

    t = time.time()
    raw = run_n8(scales[8], p["n8_reps"], rngs[1])
    summary = summarise(raw, rngs[2])
    t_n8 = time.time() - t
    write_csv(raw, "e1_n8_raw", seed=args.seed, params=p, runtime_s=t_n8)
    write_csv(summary, "e1_n8_summary", seed=args.seed, params=p, runtime_s=t_n8)
    print(f"n=8 grid: {len(raw)} matrices in {t_n8:.1f}s")
    for v in ("skew", "bc2"):
        plot(summary, v)

    t = time.time()
    val = validate_local_search(scales[8]["medium"], p["ls_val_matrices"], tuple(p["ls_restart_grid"]), rngs[3])
    write_csv(val, "e1_ls_validation", seed=args.seed, params=p, runtime_s=time.time() - t)
    print(val.groupby(["restarts", "objective"]).agg(hit_rate=("hit", "mean"), mean_gap=("gap", "mean"), max_gap=("gap", "max")))
    print(f"local-search validation in {time.time() - t:.1f}s")

    t = time.time()
    n16 = run_n16(scales[16]["medium"], p["n16_kappas"], p["n16_reps"], p["n16_restarts"], rngs[4])
    write_csv(n16, "e1_n16", seed=args.seed, params=p, runtime_s=time.time() - t)
    print(n16.groupby("kappa")[["K_lb", "Pi_lb", "weakest_kingmakeable_found"]].mean())
    print(f"n=16 in {time.time() - t:.1f}s; total {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
