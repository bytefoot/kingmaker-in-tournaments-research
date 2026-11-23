"""F1: the P4 example drawn as a bracket (theory/P4.md, cleaner one-decimal example).

Left: bracket {A, C} | {B, D}, each leaf labelled with the player's average win rate, each edge with the chance of
getting through that round.  Right: exact title chances in this bracket; D (lowest average win rate) is the favourite.
Usage: python experiments/f1_example.py
"""
from fractions import Fraction as F

import matplotlib.pyplot as plt
import numpy as np

from km.plotting import COLORS, FULL, INK, MUTED, save, use_style

NAMES = "ABCD"
P = [[None, F(7, 10), F(3, 10), F(9, 10)],
     [F(3, 10), None, F(7, 10), F(4, 10)],
     [F(7, 10), F(3, 10), None, F(4, 10)],
     [F(1, 10), F(6, 10), F(6, 10), None]]
BRACKET = ((0, 2), (1, 3))  # {A, C} | {B, D}


def exact() -> tuple[dict, dict]:
    (a, c), (b, d) = BRACKET
    semi = {a: P[a][c], c: P[c][a], b: P[b][d], d: P[d][b]}
    W = {}
    for mine, theirs in (((a, c), (b, d)), ((b, d), (a, c))):
        for i in mine:
            W[i] = semi[i] * sum(semi[j] * P[i][j] for j in theirs)
    assert sum(W.values()) == 1 and W[3] == F(27, 100)
    return semi, W


def main() -> None:
    semi, W = exact()
    borda = {i: sum(P[i][j] for j in range(4) if j != i) / 3 for i in range(4)}
    use_style()
    fig, (ax, bx) = plt.subplots(1, 2, figsize=FULL, gridspec_kw={"width_ratios": [1.35, 1]})
    ax.axis("off")
    ax.set_xlim(-0.2, 3.6)
    ax.set_ylim(-1.0, 4.1)
    ys = {0: 3.6, 2: 2.4, 1: 1.2, 3: 0.0}  # A, C top semi; B, D bottom semi
    for i, y in ys.items():
        hl = i == 3
        ax.text(0, y, f"{NAMES[i]}", ha="center", va="center", fontsize=11, fontweight="bold",
                color="white", bbox=dict(boxstyle="circle,pad=0.3", fc=COLORS["BC"] if hl else MUTED, ec="none"))
        ax.text(-0.05, y - 0.42, f"avg win rate {float(borda[i]):.3f}" + ("  (lowest)" if hl else ""),
                ha="left", fontsize=7, color=INK)
    semis = {"top": (3.0, (0, 2)), "bot": (0.6, (1, 3))}
    for _, (ym, (p, q)) in semis.items():
        for i in (p, q):
            ax.plot([0.25, 1.2, 1.2], [ys[i], ys[i], ym], color=MUTED, lw=1.2)
            ax.text(0.72, ys[i] + 0.08, f"{float(semi[i]):.0%}", ha="center", va="bottom", fontsize=8,
                    color=COLORS["BC"] if i == 3 else INK)
        ax.plot([1.2, 2.1, 2.1], [ym, ym, 1.8], color=MUTED, lw=1.2)
    ax.plot([2.1, 2.8], [1.8, 1.8], color=MUTED, lw=1.2)
    ax.text(2.85, 1.8, "champion", va="center", fontsize=8, color=INK)
    ax.text(2.2, 2.2, "final: D beats C 60%\n(C knocks out A 70%),\nD loses to A 90%", fontsize=7, color=INK, va="bottom")
    ax.set_title("bracket {A vs C} | {B vs D}", fontsize=9)
    ax.text(-0.05, -0.95, "% on each line = chance of winning the semi-final", fontsize=7, color=MUTED)

    order = [3, 2, 0, 1]
    vals = [float(W[i]) for i in order]
    bx.barh(range(4), vals, color=[COLORS["BC"] if i == 3 else MUTED for i in order], height=0.6)
    for k, (i, v) in enumerate(zip(order, vals)):
        bx.text(v + 0.004, k, f"{W[i]} = {v:.3f}" if i == 3 else f"{v:.3f}", va="center", fontsize=8, color=INK)
    bx.set_yticks(range(4), [NAMES[i] for i in order])
    bx.invert_yaxis()
    bx.set_xlim(0, 0.36)
    bx.set_xlabel("chance of winning the tournament")
    bx.set_title("title chances: weakest player D is favourite", fontsize=9)
    bx.grid(axis="y", visible=False)
    fig.tight_layout()
    save(fig, "F1_p4_example")


if __name__ == "__main__":
    main()
