"""How large can K be under BT?  Hill-climb on g (n = 4, 8) to make the second-weakest player kingmakeable,
i.e. maximise its best margin M_{n-1}; report the largest K found.  Usage: python theory/max_K_bt.py"""
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "theory")
from search_counterexamples import draw_g, margins_by_rank  # noqa: E402
from km.bracket import enumerate_brackets  # noqa: E402
from km.runlog import write_csv  # noqa: E402

rng = np.random.default_rng(20261123)
t0 = time.time()
rows = []
for n, pop, iters in ((4, 2000, 300), (8, 200, 200)):
    br = enumerate_brackets(n)
    g = draw_g(pop, n, rng)
    cur = margins_by_rank(g, br)[:, -2]
    for t in range(iters):
        g2 = np.clip(g + (1.5 * 0.99**t + 1e-3) * rng.standard_normal(g.shape), -15, 15)
        new = margins_by_rank(g2, br)[:, -2]
        better = new > cur
        g[better], cur[better] = g2[better], new[better]
    M = margins_by_rank(g, br)
    K = (M > 1e-12).sum(axis=1)
    k = int(np.argmax(cur))
    rows.append({"n": n, "max_margin_second_weakest": float(cur[k]), "max_K_found": int(K.max()),
                 "g_best": np.round(np.sort(g[k])[::-1], 4).tolist(), "K_of_best": int(K[k])})
    print(rows[-1])
write_csv(pd.DataFrame(rows), "p3_max_K_bt", seed=20261123, params={"n4": [2000, 300], "n8": [200, 200]}, runtime_s=time.time() - t0)
