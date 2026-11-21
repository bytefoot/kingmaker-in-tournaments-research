"""E4: which tournament format crowns a sensible winner under cycles, and at what cost in matches? (CLAUDE.md §5)

n = 8, medium scale, skew cycles, κ ∈ {0, 0.2, ..., 1}, 200 matrices per κ.  For each format: winner distribution
(exact for KO-random / KO-elo, 10,000 Monte Carlo runs otherwise) and
  P(winner ∈ Copeland set), expected Nash mass of the winner Σ_i P(i wins) x_i, P(winner = Borda winner)
  (Borda ties split credit), entropy of the winner distribution (bits), matches played.
Nash x: unique LP solution, or the max-entropy Nash if the Nash set is not a single point (refs.nash).
CIs: 95% percentile bootstrap over matrices.
Usage: python experiments/e4_formats.py [--quick | --full] [--seed S]
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from km.formats import FORMATS, run_format
from km.models import make_P
from km.plotting import COLORS, FULL, MARKERS, save, use_style
from km.refs import borda, copeland, nash
from km.runlog import write_csv

SCALE_MEDIUM_N8 = 7.334  # outputs/csv/e1_scales.csv
KAPPAS = np.round(np.arange(0, 1.01, 0.2), 2)
METRICS = ("p_copeland", "nash_mass", "p_borda", "entropy_bits")


def boot_ci(x: np.ndarray, rng: np.random.Generator, n_boot: int = 2000) -> tuple[float, float]:
    means = x[rng.integers(0, len(x), (n_boot, len(x)))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def plot(summary: pd.DataFrame, n_matches: dict) -> None:
    import matplotlib.pyplot as plt
    use_style()
    fig, axes = plt.subplots(1, 2, figsize=FULL)
    for ax, (col, label) in zip(axes, (("p_copeland", "P(winner is a Copeland winner)"),
                                       ("nash_mass", "expected Nash mass of the winner"))):
        for f in FORMATS:
            g = summary[summary.format == f]
            ax.fill_between(g.kappa, g[f"{col}_lo"], g[f"{col}_hi"], color=COLORS[f], alpha=0.15, lw=0)
            ax.plot(g.kappa, g[col], color=COLORS[f], marker=MARKERS[f], label=f"{f} ({n_matches[f]})")
        ax.set_xlabel("cyclic share κ")
        ax.set_ylabel(label)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1 if col == "p_copeland" else None)
    axes[1].set_ylim(bottom=0)
    axes[0].legend(loc="lower left", title="format (matches)", title_fontsize=8, fontsize=7)
    fig.tight_layout()
    save(fig, "F5_formats_vs_kappa")


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    ap.add_argument("--seed", type=int, default=20261126)
    ap.add_argument("--plot-only", action="store_true", help="redraw F5 from outputs/csv/e4_summary.csv")
    args = ap.parse_args()
    if args.plot_only:
        s = pd.read_csv("outputs/csv/e4_summary.csv", comment="#")
        plot(s, s.groupby("format").matches.first().to_dict())
        return
    full = not args.quick
    p = {"mode": "full" if full else "quick", "n": 8, "scale": SCALE_MEDIUM_N8, "variant": "skew", "kappas": KAPPAS.tolist(),
         "reps": 200 if full else 5, "mc_runs": 10_000 if full else 2_000}
    rng = np.random.default_rng(args.seed)
    t0 = time.time()
    rows = []
    for k in KAPPAS:
        for rep in range(p["reps"]):
            P = make_P(8, k, SCALE_MEDIUM_N8, rng)
            cop_set = copeland(P) > 0
            bor = borda(P)
            nx = nash(P)
            for f in FORMATS:
                dist, m = run_format(f, P, p["mc_runs"], rng)
                nz = dist[dist > 0]
                rows.append({"kappa": k, "rep": rep, "format": f, "matches": m,
                             "p_copeland": float(dist @ cop_set), "nash_mass": float(dist @ nx["x"]),
                             "p_borda": float(dist @ bor), "entropy_bits": float(-(nz * np.log2(nz)).sum()),
                             "copeland_set_size": int(cop_set.sum()), "nash_unique": nx["unique"],
                             "nash_support": int((nx["x"] > 1e-9).sum())})
        print(f"κ={k}: {time.time() - t0:.0f}s")
    raw = pd.DataFrame(rows)
    out = []
    for (k, f), g in raw.groupby(["kappa", "format"]):
        r = {"kappa": k, "format": f, "matches": int(g.matches.iloc[0]), "n_matrices": len(g)}
        for c in METRICS:
            lo, hi = boot_ci(g[c].to_numpy(), rng)
            r.update({c: g[c].mean(), f"{c}_lo": lo, f"{c}_hi": hi})
        out.append(r)
    summary = pd.DataFrame(out)
    runtime = time.time() - t0
    write_csv(raw, "e4_raw", seed=args.seed, params=p, runtime_s=runtime)
    write_csv(summary, "e4_summary", seed=args.seed, params=p, runtime_s=runtime)
    plot(summary, raw.groupby("format").matches.first().to_dict())
    pd.set_option("display.width", 220)
    print(summary.pivot(index="kappa", columns="format", values="p_copeland").round(3))
    print(summary.pivot(index="kappa", columns="format", values="nash_mass").round(3))
    print(summary.pivot(index="kappa", columns="format", values="p_borda").round(3))
    print(summary.pivot(index="kappa", columns="format", values="entropy_bits").round(2))
    print(raw.groupby("kappa")[["copeland_set_size", "nash_unique", "nash_support"]].mean())
    print(f"total {runtime:.0f}s")


if __name__ == "__main__":
    main()
