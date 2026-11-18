"""One shared figure style (CLAUDE.md §6): vector PDF + PNG, report sizes, ≥ 9 pt fonts, colour-blind-safe colours.

Colours are Okabe-Ito hues with a fixed mapping per format/model, so the same entity has the same colour in every
figure.  The palette passes the dataviz validator (lightness, chroma, normal-vision separation); its weakest CVD
pair (pink/green, ΔE 7.6) is only legal with secondary encoding, so every series also gets its own marker.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .runlog import FIG_DIR  # noqa: E402

SINGLE = (3.4, 2.6)  # single column, inches
FULL = (6.8, 3.0)  # full width, inches

COLORS = {
    "KO-random": "#0072B2", "KO-elo": "#E69F00", "Swiss": "#009E73", "Groups+KO": "#CC79A7", "Round robin": "#D55E00",
    "BT": "#0072B2", "BC": "#D55E00",
    "close": "#56B4E9", "medium": "#0072B2", "decisive": "#000000",
}
MARKERS = {"KO-random": "o", "KO-elo": "s", "Swiss": "^", "Groups+KO": "D", "Round robin": "v", "BT": "o", "BC": "s"}
INK = "#222222"
MUTED = "#777777"


def use_style() -> None:
    plt.rcParams.update({
        "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9, "legend.fontsize": 8,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "font.family": "sans-serif",
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6,
        "lines.linewidth": 1.5, "lines.markersize": 4, "legend.frameon": False,
        "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.dpi": 300,
    })


def save(fig: plt.Figure, name: str) -> Path:
    """Save ``outputs/fig/<name>.pdf`` and ``.png``; returns the PDF path."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    pdf = FIG_DIR / f"{name}.pdf"
    fig.savefig(pdf)
    fig.savefig(FIG_DIR / f"{name}.png")
    plt.close(fig)
    return pdf
