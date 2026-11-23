"""F0: setup schematic (data -> BT/BC fit -> P -> {bracket DP + search, format simulator} -> metrics).
Usage: python experiments/f0_setup.py
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from km.plotting import INK, MUTED, save, use_style

BOX_FILL, ACCENT_FILL = "#f2f2f2", "#fbe3d4"


def box(ax, x, y, w, h, title, body, fill=BOX_FILL):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fill, ec=MUTED, lw=0.8))
    ax.text(x + w / 2, y + h - 0.13, title, ha="center", va="top", fontsize=8.5, fontweight="bold", color=INK)
    ax.text(x + w / 2, y + h - 0.42, body, ha="center", va="top", fontsize=6.8, color=INK, linespacing=1.35)


def arrow(ax, p, q, label=None, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9, lw=0.9, color=MUTED,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.08, label, ha="center", va="bottom", fontsize=6.5, color=MUTED)


def main():
    use_style()
    fig, ax = plt.subplots(figsize=(6.8, 3.0))
    ax.set_xlim(-0.1, 10.1)
    ax.set_ylim(0, 4.4)
    ax.axis("off")
    # column 1: sources
    box(ax, 0.05, 2.45, 2.15, 1.75, "Match data", "ATP tennis 2015–19:\n16 players, 614 games;\narchetype game\n(synthetic, 10 or 50\nmatches per pair)")
    box(ax, 0.05, 0.2, 2.15, 1.85, "Synthetic P", "make_P(κ, scale):\nladder + cycles mixed\nκ ∈ {0, 0.1, …, 1}\n3 decisiveness levels")
    # column 2: fit
    box(ax, 2.6, 2.45, 1.85, 1.75, "Fit model", "Bradley–Terry or\nBlade–Chest (d=2);\nλ by held-out\nlog-loss", fill=ACCENT_FILL)
    # column 3: P
    box(ax, 4.85, 1.25, 2.05, 2.0, "Win matrix P", "P[i, j] = chance\ni beats j\nlogits L = T + C\n(ladder + cycles)\nκ = ‖C‖² / ‖L‖²")
    # column 4: analyses
    box(ax, 7.3, 2.45, 2.7, 1.75, "Bracket analysis", "exact DP over all 315\nbrackets (n = 8);\nlocal search (n = 16)\n→ K, Π, $R_i$", fill=ACCENT_FILL)
    box(ax, 7.3, 0.2, 2.7, 1.85, "Format simulator", "KO-random, KO-elo, Swiss,\nGroups+KO, round robin\n→ winner vs Copeland,\nBorda, Nash", fill=ACCENT_FILL)
    arrow(ax, (2.2, 3.3), (2.6, 3.3))
    arrow(ax, (4.45, 3.0), (4.85, 2.75))
    arrow(ax, (2.2, 1.1), (4.85, 1.7))
    arrow(ax, (6.9, 2.75), (7.3, 3.2))
    arrow(ax, (6.9, 1.7), (7.3, 1.1))
    ax.text(5.875, 0.75, "theory P1–P6: exact and\nsymbolic checks on small P", fontsize=6.5, color=MUTED, ha="center", va="center")
    save(fig, "F0_setup")


if __name__ == "__main__":
    main()
