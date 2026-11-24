"""E4 paired differences: each format minus KO-random on the same matrices, with 95% bootstrap CIs.

Reads outputs/csv/e4_raw.csv (from e4_formats.py) and writes outputs/csv/e4_paired.csv.
Usage: python experiments/e4_paired.py [--seed S]
"""
import argparse
import time

import numpy as np
import pandas as pd

from km.runlog import CSV_DIR, write_csv

METRICS = ("p_copeland", "nash_mass", "p_borda")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261124)
    args = ap.parse_args()
    t0 = time.time()
    rng = np.random.default_rng(args.seed)
    raw = pd.read_csv(CSV_DIR / "e4_raw.csv", comment="#")
    rows = []
    for m in METRICS:
        wide = raw.pivot_table(index=["kappa", "rep"], columns="format", values=m)
        for f in wide.columns.drop("KO-random"):
            for k, g in wide.groupby(level="kappa"):
                d = (g[f] - g["KO-random"]).to_numpy()
                boot = d[rng.integers(0, len(d), (2000, len(d)))].mean(axis=1)
                rows.append({"metric": m, "format": f, "kappa": k, "diff": d.mean(),
                             "lo": np.percentile(boot, 2.5), "hi": np.percentile(boot, 97.5)})
    write_csv(pd.DataFrame(rows), "e4_paired", seed=args.seed, params={"baseline": "KO-random", "boot": 2000},
              runtime_s=time.time() - t0)


if __name__ == "__main__":
    main()
