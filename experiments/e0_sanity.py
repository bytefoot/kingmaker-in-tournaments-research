"""E0: sanity checks (CLAUDE.md §5).  Writes outputs/csv/e0.csv (one row per check) and outputs/fig/E0_dp_vs_mc.pdf.

Usage: python experiments/e0_sanity.py [--quick | --full] [--seed S]
"""
from __future__ import annotations

import argparse
import sys
import time
from fractions import Fraction
from itertools import permutations, product

import numpy as np
import pandas as pd
from scipy.stats import chisquare

from km.bracket import canonicalize, enumerate_brackets, n_brackets, win_probs, win_probs_mc
from km.formats import FORMATS, ko_random, run_format
from km.models import CYCLE_VARIANTS, bt_logits, hodge_split, kappa, make_L, make_P, sigmoid
from km.plotting import COLORS, INK, MUTED, SINGLE, save, use_style
from km.refs import nash
from km.runlog import write_csv

rows: list[dict] = []


def record(check: str, value: float, threshold: str, passed: bool, detail: str = "") -> None:
    rows.append({"check": check, "value": value, "threshold": threshold, "passed": bool(passed), "detail": detail})
    print(f"[{'PASS' if passed else 'FAIL'}] {check}: {value:.4g} ({threshold}) {detail}")


def check_brackets() -> None:
    for n in (4, 8):
        reps = {tuple(b) for b in enumerate_brackets(n)}
        sizes = {}
        for perm in permutations(range(n)):
            c = canonicalize(np.array(perm))
            sizes[c] = sizes.get(c, 0) + 1
        ok = len(reps) == n_brackets(n) and set(sizes) == reps and set(sizes.values()) == {2 ** (n - 1)}
        record(f"bracket_count_n{n}", len(reps), f"== {n_brackets(n)}; all {len(sizes)} classes of size 2^{n-1}", ok)
    record("bracket_count_formula_n16", n_brackets(16), "== 638512875", n_brackets(16) == 638_512_875)


def check_hodge_and_kappa(rng: np.random.Generator, reps: int) -> None:
    worst_inner, worst_rowsum = 0.0, 0.0
    for n in (4, 8, 16):
        for _ in range(reps):
            U = np.triu(rng.standard_normal((n, n)) * rng.exponential(3), 1)
            L = U - U.T
            T, C = hodge_split(L)
            worst_inner = max(worst_inner, abs(np.sum(T * C)) / np.sum(L**2))
            worst_rowsum = max(worst_rowsum, np.abs(C.sum(axis=1)).max())
    record("hodge_orthogonality", worst_inner, "max |<T,C>_F| / ||L||^2 < 1e-12", worst_inner < 1e-12, f"n in 4,8,16; {reps} each")
    record("hodge_cyclic_rowsums", worst_rowsum, "max |row sum of C| < 1e-12", worst_rowsum < 1e-12)

    worst = 0.0
    count = 0
    for n in (4, 8, 16):
        for variant in CYCLE_VARIANTS:
            for k in np.linspace(0, 1, 11):
                for scale in (0.5, 2.0, 8.0):
                    for _ in range(max(1, reps // 100)):
                        worst = max(worst, abs(kappa(make_L(n, k, scale, rng, variant)) - k))
                        count += 1
    record("make_P_kappa_target", worst, "max |kappa(L) - target| < 1e-9", worst < 1e-9,
           f"{count} draws: n in 4,8,16 x variants {CYCLE_VARIANTS} x 11 kappas x 3 scales")


def check_dp(rng: np.random.Generator, n_runs: int) -> list[dict]:
    """DP vs Monte Carlo on 5 random n=8 matrices (random kappa, scale, cycle variant, bracket)."""
    pts = []
    worst_z = 0.0
    for t in range(5):
        k, scale, variant = rng.uniform(0, 1), rng.choice([1.0, 3.0, 6.0]), rng.choice(CYCLE_VARIANTS)
        P = make_P(8, k, scale, rng, variant)
        br = rng.permutation(8)
        W, Wmc = win_probs(P, br), win_probs_mc(P, br, n_runs, rng)
        se = np.sqrt(W * (1 - W) / n_runs)
        z = np.abs(W - Wmc) / np.where(se > 0, se, np.inf)
        worst_z = max(worst_z, z.max())
        pts += [{"matrix": t, "player": i, "W_dp": W[i], "W_mc": Wmc[i], "se": se[i]} for i in range(8)]
    record("dp_vs_mc_n8", worst_z, "max |DP - MC| / s.e. <= 4", worst_z <= 4, f"5 matrices x 8 players, {n_runs} runs each")

    # exact rational brute force over all 2^3 outcomes for n = 4
    worst = 0.0
    for _ in range(20):
        Pf = make_P(4, rng.uniform(0, 1), 3.0, rng)
        Pq = [[Fraction(x) for x in row] for row in Pf]
        for br in enumerate_brackets(4):
            a, b, c, d = br
            exact = [Fraction(0)] * 4
            for r1, r2, r3 in product([0, 1], repeat=3):
                x, y = (a, b)[r1], (c, d)[r2]
                z = (x, y)[r3]
                exact[z] += Pq[x][(a, b)[1 - r1]] * Pq[y][(c, d)[1 - r2]] * Pq[z][(x, y)[1 - r3]]
            worst = max(worst, np.abs(win_probs(Pf, br) - np.array([float(e) for e in exact])).max())
    record("dp_vs_exact_rational_n4", worst, "max abs diff < 1e-14", worst < 1e-14, "20 matrices x 3 brackets")
    return pts


def check_formats(rng: np.random.Generator, n_runs: int) -> None:
    # scale -> infinity at kappa = 0: P(top player wins) -> 1.  Fixed BT direction, growing scale; the scale is
    # expressed as the smallest |logit| between any two players.
    L = make_L(8, 0.0, 1.0, np.random.default_rng(123))
    L = L / np.abs(L[~np.eye(8, dtype=bool)]).min()
    top = int(np.argmax(L.sum(axis=1)))
    for min_logit in (0.5, 2, 8, 32):
        dist, _ = run_format("Round robin", sigmoid(min_logit * L), n_runs, rng)
        final = min_logit == 32
        record(f"top_wins_Round robin_minlogit{min_logit}", dist[top], ">= 0.999" if final else "info (convergence)",
               dist[top] >= 0.999 or not final)
    for name in FORMATS[:-1]:
        dist, _ = run_format(name, sigmoid(32 * L), n_runs, rng)
        record(f"top_wins_{name}_minlogit32", dist[top], ">= 0.999", dist[top] >= 0.999)

    # scale 0: uniform winner distribution
    P0 = np.full((8, 8), 0.5)
    for name in FORMATS:
        dist, _ = run_format(name, P0, n_runs, rng)
        if name.startswith("KO"):
            err = np.abs(dist - 1 / 8).max()
            record(f"uniform_scale0_{name}", err, "exact: max |p - 1/8| < 1e-12", err < 1e-12)
        else:
            p = chisquare(dist * n_runs).pvalue
            record(f"uniform_scale0_{name}", p, "chi-square p > 0.001", p > 1e-3, f"{n_runs} runs; max |p-1/8| = {np.abs(dist-1/8).max():.4f}")

    # KO-random exact vs Monte Carlo over random seedings
    P = make_P(8, 0.6, 3.0, rng)
    exact, _ = ko_random(P)
    mc, _ = ko_random(P, rng, n_runs=n_runs)
    z = (np.abs(exact - mc) / np.sqrt(exact * (1 - exact) / n_runs)).max()
    record("ko_random_exact_vs_mc", z, "max |exact - MC| / s.e. <= 4", z <= 4, f"{n_runs} runs")

    # match counts
    counts = {name: run_format(name, make_P(8, 0.5, 2.0, rng), 100, rng)[1] for name in FORMATS}
    expected = {"KO-random": 7, "KO-elo": 7, "Swiss": 12, "Groups+KO": 15, "Round robin": 28}
    record("format_match_counts", sum(counts.values()), "7, 7, 12, 15, 28", counts == expected, str(counts))


def check_nash() -> None:
    rps = np.array([[0.5, 0.9, 0.1], [0.1, 0.5, 0.9], [0.9, 0.1, 0.5]])
    out = nash(rps)
    err = np.abs(out["x"] - 1 / 3).max()
    record("nash_rps", err, "max |x - 1/3| < 1e-8, unique", err < 1e-8 and out["unique"], f"x = {np.round(out['x'], 6).tolist()}")
    g = np.array([0.2, 1.5, -0.3, 0.9, -1.0, 0.0, 0.4, -0.6])
    out = nash(sigmoid(bt_logits(g)))
    err = np.abs(out["x"] - np.eye(8)[np.argmax(g)]).max()
    record("nash_bt_top_player", err, "max |x - e_top| < 1e-8, unique", err < 1e-8 and out["unique"])
    dup = np.array([[0.5, 0.1, 0.9, 0.9], [0.9, 0.5, 0.1, 0.1], [0.1, 0.9, 0.5, 0.5], [0.1, 0.9, 0.5, 0.5]])
    out = nash(dup)
    err = np.abs(out["x"] - np.array([1 / 3, 1 / 3, 1 / 6, 1 / 6])).max()
    record("nash_maxent_duplicate_scissors", err, "non-unique, maxent = (1/3,1/3,1/6,1/6) within 1e-5",
           err < 1e-5 and not out["unique"], f"x = {np.round(out['x'], 6).tolist()}")


def plot(pts: list[dict]) -> None:
    use_style()
    import matplotlib.pyplot as plt
    df = pd.DataFrame(pts)
    fig, ax = plt.subplots(figsize=SINGLE)
    hi = df[["W_dp", "W_mc"]].to_numpy().max() * 1.05
    ax.plot([0, hi], [0, hi], color=MUTED, lw=1, zorder=1, label="y = x")
    ax.errorbar(df.W_dp, df.W_mc, yerr=4 * df.se, fmt="o", ms=4, color=COLORS["BT"], ecolor=COLORS["BT"],
                elinewidth=0.8, mec="white", mew=0.6, zorder=2, label="MC estimate ± 4 s.e.")
    ax.set_xlabel("exact win probability (DP)")
    ax.set_ylabel("Monte Carlo win frequency")
    ax.set_xlim(0, hi), ax.set_ylim(0, hi)
    ax.legend(loc="upper left", labelcolor=INK)
    save(fig, "E0_dp_vs_mc")


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    ap.add_argument("--seed", type=int, default=20261118)
    args = ap.parse_args()
    full = not args.quick
    params = {"mode": "full" if full else "quick", "dp_mc_runs": 100_000 if full else 10_000,
              "format_runs": 100_000 if full else 10_000, "hodge_reps": 1000 if full else 100}
    rng = np.random.default_rng(args.seed)
    t0 = time.time()
    check_brackets()
    check_hodge_and_kappa(rng, params["hodge_reps"])
    pts = check_dp(rng, params["dp_mc_runs"])
    check_formats(rng, params["format_runs"])
    check_nash()
    plot(pts)
    df = pd.DataFrame(rows)
    path = write_csv(df, "e0", seed=args.seed, params=params, runtime_s=time.time() - t0)
    print(f"\n{df.passed.sum()}/{len(df)} checks passed -> {path}  ({time.time() - t0:.1f}s)")
    return 0 if df.passed.all() else 1


if __name__ == "__main__":
    sys.exit(main())
