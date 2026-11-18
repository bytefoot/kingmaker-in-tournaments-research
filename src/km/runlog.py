"""Provenance for experiment outputs: seed, parameters, git commit and runtime as '#' comment lines atop each CSV."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CSV_DIR = ROOT / "outputs" / "csv"
FIG_DIR = ROOT / "outputs" / "fig"


def git_commit() -> str:
    """Short commit hash, with '+dirty' if the tracked tree has uncommitted changes; 'nogit' outside a repo."""
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        return h + ("+dirty" if dirty else "")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "nogit"


def write_csv(df: pd.DataFrame, name: str, *, seed: int, params: dict, runtime_s: float) -> Path:
    """Write ``outputs/csv/<name>.csv`` with a provenance header; read back with ``pd.read_csv(path, comment='#')``."""
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    path = CSV_DIR / f"{name}.csv"
    header = [
        f"# experiment: {name}",
        f"# date_utc: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"# git_commit: {git_commit()}",
        f"# seed: {seed}",
        f"# params: {json.dumps(params, sort_keys=True)}",
        f"# runtime_s: {runtime_s:.2f}",
    ]
    with open(path, "w") as f:
        f.write("\n".join(header) + "\n")
        df.to_csv(f, index=False)
    return path
