"""F0: setup schematic, drawn as a four-step story with real mini-graphics.

1 matchups (ladder vs cycle, the κ dial, data sources) -> 2 win matrix P (the F1 example, split into ladder + cycle)
-> 3 the organiser's bracket (D crowned) -> 4 the answer (E1 curve K vs κ, from outputs/csv/e1_n8_summary.csv).
Usage: python experiments/f0_setup.py
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch

from km.models import hodge_split, kappa, logit
from km.plotting import COLORS, INK, MUTED, save, use_style
from km.runlog import CSV_DIR

LADDER, CYCLE = COLORS["BT"], COLORS["BC"]  # ladder part = blue (BT), cycle part = vermillion (BC), as elsewhere
CARD = "#f6f6f6"
P = np.array([[.5, .7, .3, .9], [.3, .5, .7, .4], [.7, .3, .5, .4], [.1, .6, .6, .5]])  # F1 example (theory/P4.md)
NAMES = "ABCD"


def card(fig, x, w, step, title):
    fig.patches.append(FancyBboxPatch((x, 0.03), w, 0.80, boxstyle="round,pad=0,rounding_size=0.015",
                                      transform=fig.transFigure, fc=CARD, ec="none", zorder=-10))
    fig.patches.append(Ellipse((x + 0.022, 0.785), 0.034 * 3.2 / 6.8, 0.034, transform=fig.transFigure, fc=INK, ec="none"))
    fig.text(x + 0.022, 0.785, str(step), ha="center", va="center", color="white", fontsize=8.5, fontweight="bold")
    fig.text(x + 0.046, 0.785, title, ha="left", va="center", color=INK, fontsize=9, fontweight="bold")


def arrow(fig, x0, x1, y=0.43):
    fig.patches.append(FancyArrowPatch((x0, y), (x1, y), transform=fig.transFigure, arrowstyle="-|>",
                                       mutation_scale=11, lw=1.2, color=MUTED))


def node(ax, xy, label, color, r=0.13):
    ax.add_patch(Circle(xy, r, fc=color, ec="none"))
    ax.text(*xy, label, ha="center", va="center", color="white", fontsize=8, fontweight="bold")


def edge(ax, p, q, color, r=0.15):
    p, q = np.array(p), np.array(q)
    u = (q - p) / np.linalg.norm(q - p)
    ax.add_patch(FancyArrowPatch(p + r * u, q - r * u, arrowstyle="-|>", mutation_scale=8, lw=1.1, color=color))


def panel_matchups(fig):
    ax = fig.add_axes([0.015, 0.25, 0.22, 0.49])
    ax.set_xlim(0, 2.2)
    ax.set_ylim(0, 1.75)
    ax.set_aspect("equal")
    ax.axis("off")
    for k, y in enumerate((1.45, 1.0, 0.55)):  # ladder: each beats everyone below
        node(ax, (0.35, y), "ABC"[k], LADDER)
    edge(ax, (0.35, 1.45), (0.35, 1.0), LADDER)
    edge(ax, (0.35, 1.0), (0.35, 0.55), LADDER)
    ax.text(0.35, 0.2, "ladder\n(Bradley–\nTerry)", ha="center", va="center", fontsize=6.8, color=INK)
    tri = {"A": (1.6, 1.45), "B": (1.95, 0.75), "C": (1.25, 0.75)}  # cycle: A > B > C > A
    for k, xy in tri.items():
        node(ax, xy, k, CYCLE)
    edge(ax, tri["A"], tri["B"], CYCLE)
    edge(ax, tri["B"], tri["C"], CYCLE)
    edge(ax, tri["C"], tri["A"], CYCLE)
    ax.text(1.6, 0.2, "cycle\n(rock–paper–\nscissors)", ha="center", va="center", fontsize=6.8, color=INK)
    # κ dial: a gradient bar from ladder to cycle
    bx = fig.add_axes([0.035, 0.19, 0.18, 0.03])
    bx.imshow(np.linspace(0, 1, 100)[None, :], aspect="auto", extent=(0, 1, 0, 1),
              cmap=plt.matplotlib.colors.LinearSegmentedColormap.from_list("lc", [LADDER, "#dddddd", CYCLE]))
    bx.set_yticks([])
    bx.set_xticks([0, 0.5, 1], ["0", "cyclic share κ", "1"], fontsize=7)
    bx.tick_params(length=0, pad=2)
    for s in bx.spines.values():
        s.set_visible(False)
    bx.grid(False)
    fig.text(0.125, 0.07, "data: κ-dial (synthetic),\nstrategy game, ATP tennis", ha="center", va="center", fontsize=6.5, color=MUTED)


def panel_matrix(fig):
    L = logit(P)
    T, C = hodge_split(L)
    ax = fig.add_axes([0.305, 0.37, 0.15, 0.29])
    ax.imshow(P, cmap="RdBu_r", vmin=0, vmax=1)
    for i in range(4):
        for j in range(4):
            if i != j:
                ax.text(j, i, f"{P[i, j]:.1f}".lstrip("0"), ha="center", va="center", fontsize=7,
                        color="white" if abs(P[i, j] - 0.5) > 0.25 else INK)
    ax.set_xticks(range(4), list(NAMES), fontsize=7)
    ax.set_yticks(range(4), list(NAMES), fontsize=7)
    ax.tick_params(length=0, pad=1.5)
    ax.xaxis.set_ticks_position("top")
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.text(0.38, 0.325, "P[row beats column]", ha="center", va="center", fontsize=6.5, color=MUTED)
    for x, M, col, lab in ((0.285, T, LADDER, "ladder"), (0.405, C, CYCLE, "cycle")):
        mx = fig.add_axes([x, 0.13, 0.075, 0.11])
        mx.imshow(M, cmap="RdBu_r", vmin=-np.abs(L).max(), vmax=np.abs(L).max())
        mx.set_xticks([])
        mx.set_yticks([])
        for s in mx.spines.values():
            s.set_edgecolor(col)
            s.set_linewidth(1.5)
        mx.grid(False)
        mx.set_title(lab, fontsize=6.5, color=col, pad=1.5)
    fig.text(0.37, 0.185, "+", ha="center", va="center", fontsize=10, color=INK)
    fig.text(0.38, 0.07, f"κ = ‖cycle‖² / ‖total‖²\n= {kappa(L):.2f} here", ha="center", va="center", fontsize=6.5, color=MUTED)


def panel_bracket(fig):
    ax = fig.add_axes([0.515, 0.14, 0.225, 0.58])
    ax.set_xlim(0, 3.1)
    ax.set_ylim(-0.4, 3.9)
    ax.set_aspect("equal")
    ax.axis("off")
    ys = {"A": 3.3, "C": 2.3, "B": 1.3, "D": 0.3}
    for k, y in ys.items():
        node(ax, (0.25, y), k, CYCLE if k == "D" else MUTED, r=0.22)
    for (a, b), ym in ((("A", "C"), 2.8), (("B", "D"), 0.8)):
        for k in (a, b):
            ax.plot([0.5, 1.05, 1.05], [ys[k], ys[k], ym], color=MUTED, lw=1)
        ax.plot([1.05, 1.7, 1.7], [ym, ym, 1.8], color=MUTED, lw=1)
    ax.plot([1.7, 2.15], [1.8, 1.8], color=MUTED, lw=1)
    node(ax, (2.45, 1.8), "D", CYCLE, r=0.26)
    ax.text(2.45, 1.25, "27% ★", ha="center", fontsize=7.5, color=CYCLE, fontweight="bold")
    ax.text(0.65, ys["A"] + 0.1, "C knocks out A", fontsize=6.3, color=INK, va="bottom")
    ax.text(0.65, ys["D"] - 0.12, "weakest player", fontsize=6.3, color=CYCLE, va="top")
    fig.text(0.625, 0.07, "exact title chances in\nall 315 brackets (8 players)", ha="center", va="center", fontsize=6.5, color=MUTED)


def panel_answer(fig):
    df = pd.read_csv(CSV_DIR / "e1_n8_summary.csv", comment="#")
    d = df[(df.variant == "skew") & (df.scale == "medium")].sort_values("kappa")
    ax = fig.add_axes([0.835, 0.26, 0.14, 0.42])
    ax.fill_between(d.kappa, d.K_lo, d.K_hi, color=CYCLE, alpha=0.2, lw=0)
    ax.plot(d.kappa, d.K, color=CYCLE, lw=1.6)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 8.3)
    ax.set_xticks([0, 0.5, 1], ["0", ".5", "1"], fontsize=7)
    ax.set_yticks([0, 4, 8], ["0", "4", "8"], fontsize=7)
    ax.set_xlabel("cyclic share κ", fontsize=7, labelpad=1)
    ax.set_ylabel("crownable players", fontsize=7, labelpad=1)
    fig.text(0.875, 0.07, "8 players; then: which\nformat crowns a fair winner?", ha="center", va="center", fontsize=6.5, color=MUTED)


def main():
    use_style()
    plt.rcParams["axes.facecolor"] = "none"
    fig = plt.figure(figsize=(6.8, 3.2))
    fig.text(0.5, 0.95, "Same players, different bracket, different champion: how much does the organiser decide?",
             ha="center", va="center", fontsize=9.5, color=INK, fontweight="bold")
    xs, w = (0.005, 0.255, 0.505, 0.755), 0.24
    for x, step, title in zip(xs, (1, 2, 3, 4), ("Matchups", "Who beats whom", "The bracket", "The answer")):
        card(fig, x, w, step, title)
    for x in xs[1:]:
        arrow(fig, x - 0.012, x + 0.004)
    panel_matchups(fig)
    panel_matrix(fig)
    panel_bracket(fig)
    panel_answer(fig)
    fig.text(0.38, 0.735, "fitted with BT or Blade–Chest", ha="center", fontsize=6.5, color=MUTED)
    save(fig, "F0_setup")


if __name__ == "__main__":
    main()
