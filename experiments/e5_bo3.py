"""E5 (optional): best-of-3 series.  Each match becomes a best-of-3, p -> p²(3 - 2p).  Paired with single games on the
same matrices: n = 8, medium scale, skew cycles, κ ∈ {0, 0.1, ..., 1}, 200 matrices per κ, exhaustive over 315 brackets.
Also records the κ and mean |P - ½| of the best-of-3 matrix (the map is nonlinear in logits, so κ can change).
Usage: python experiments/e5_bo3.py [--quick | --full] [--seed S]
"""
import argparse
import time

import numpy as np
import pandas as pd

from km.bracket import enumerate_brackets, exhaustive_metrics
from km.models import kappa, logit, make_P
from km.plotting import COLORS, FULL, save, use_style
from km.runlog import write_csv

SCALE_MEDIUM_N8 = 7.334


def bo3(P: np.ndarray) -> np.ndarray:
    return P**2 * (3 - 2 * P)


def boot_ci(x, rng, n_boot=2000):
    m = x[rng.integers(0, len(x), (n_boot, len(x)))].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    ap.add_argument("--seed", type=int, default=20261127)
    args = ap.parse_args()
    reps = 10 if args.quick else 200
    rng = np.random.default_rng(args.seed)
    br = enumerate_brackets(8)
    t0 = time.time()
    rows = []
    off = ~np.eye(8, dtype=bool)
    for k in np.round(np.linspace(0, 1, 11), 2):
        for rep in range(reps):
            P = make_P(8, k, SCALE_MEDIUM_N8, rng)
            for series, Q in (("single", P), ("best-of-3", bo3(P))):
                m = exhaustive_metrics(Q, br)
                s = logit(Q).mean(1)
                rows.append({"kappa_target": k, "rep": rep, "series": series, "kappa_realised": kappa(logit(Q)),
                             "mean_abs_P_minus_half": float(np.abs(Q - 0.5)[off].mean()), "K": m["K"], "Pi": m["Pi"],
                             "weakest_kingmakeable": bool(m["kingmakeable"][np.argmin(s)])})
    raw = pd.DataFrame(rows)
    out = []
    for (k, sname), g in raw.groupby(["kappa_target", "series"]):
        r = {"kappa_target": k, "series": sname, "kappa_realised": g.kappa_realised.mean(),
             "mean_abs_P_minus_half": g.mean_abs_P_minus_half.mean()}
        for c in ("K", "Pi", "weakest_kingmakeable"):
            lo, hi = boot_ci(g[c].to_numpy(dtype=float), rng)
            r.update({c: g[c].mean(), f"{c}_lo": lo, f"{c}_hi": hi})
        out.append(r)
    summary = pd.DataFrame(out)
    p = {"n": 8, "scale": SCALE_MEDIUM_N8, "variant": "skew", "reps": reps, "series_map": "p^2(3-2p)"}
    write_csv(raw, "e5_raw", seed=args.seed, params=p, runtime_s=time.time() - t0)
    write_csv(summary, "e5_summary", seed=args.seed, params=p, runtime_s=time.time() - t0)

    import matplotlib.pyplot as plt
    use_style()
    fig, axes = plt.subplots(1, 2, figsize=FULL)
    for sname, color, mk in (("single", COLORS["medium"], "o"), ("best-of-3", COLORS["BC"], "s")):
        g = summary[summary.series == sname]
        for ax, c in zip(axes, ("K", "Pi")):
            ax.fill_between(g.kappa_target, g[f"{c}_lo"], g[f"{c}_hi"], color=color, alpha=0.2, lw=0)
            ax.plot(g.kappa_target, g[c], color=color, marker=mk, label=sname + " matches")
    axes[0].set_ylabel("kingmakeable players K (of 8)")
    axes[1].set_ylabel("organiser power Π")
    for ax in axes:
        ax.set_xlabel("cyclic share κ of single-game P")
        ax.set_xlim(0, 1)
        ax.set_ylim(bottom=0)
    axes[0].legend(loc="upper left")
    fig.tight_layout()
    save(fig, "F6_bo3")
    pd.set_option("display.width", 200)
    print(summary.pivot(index="kappa_target", columns="series", values=["K", "Pi", "kappa_realised", "mean_abs_P_minus_half", "weakest_kingmakeable"]).round(3))
    w = raw.pivot_table(index=["kappa_target", "rep"], columns="series", values=["K", "Pi"])
    for c in ("K", "Pi"):
        d = (w[c]["best-of-3"] - w[c]["single"]).groupby(level=0)
        print(c, "bo3 - single:", {k: (round(v.mean(), 3), boot_ci(v.to_numpy(), rng)) for k, v in d})
    print(f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
