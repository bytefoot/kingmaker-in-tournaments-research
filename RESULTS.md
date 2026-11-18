# RESULTS — Kingmakers & Formats (lab notebook)

## 1. Headline findings

_None yet — only E0 (sanity checks) has been run._

**Surprises:** none yet.

## 2. Theory items

| Item | Status | Statement | File |
|---|---|---|---|
| P1 | not attempted | deterministic outcomes: transitive ⇒ K = 1; cyclic ⇒ tournament-fixing literature | — |
| P2 | not attempted (re-verification pending) | BT is not organiser-proof | — |
| P3 | not attempted | BT swap-monotonicity | — |
| P4 | not attempted (re-verification pending) | cycles break P3 | — |
| P5 | not attempted | E[K] monotone in κ? | — |

(P1(a) is exercised numerically by `tests/test_bracket.py::test_exhaustive_metrics_deterministic_transitive` for one
n = 8 instance; that is a test, not a proof.)

## 3. Experiments

### E0 — sanity checks (done, 26/26 pass)

- Command: `python experiments/e0_sanity.py --full`; seed 20261118; git commit 4f4e13c; runtime 2.4 s.
- Params: 10⁵ Monte Carlo runs for DP-vs-MC, 10⁵ runs per format check, 1,000 random matrices per n for Hodge checks.
- Output: `outputs/csv/e0.csv` (one row per check), `outputs/fig/E0_dp_vs_mc.pdf`.
- `pytest`: 40 tests green.

| Check | Result |
|---|---|
| Bracket counts | n = 4: 3, n = 8: 315 canonical brackets; enumerating all n! seedings gives exactly these classes, each of size 2^(n−1). n = 16 count 638,512,875 checked from the formula only. |
| Hodge split | max \|⟨T, C⟩_F\| / ‖L‖² = 1.0e-16; rows of C sum to 0 (max 2.5e-14); n = 4, 8, 16. |
| `make_P` κ | max \|κ(L) − target\| = 4.4e-16 over 2,970 draws (n = 4, 8, 16 × variants skew/bc1/bc2 × κ ∈ {0, 0.1, …, 1} × 3 scales). |
| DP vs MC (n = 8) | 5 random P, random brackets, 10⁵ runs: max \|DP − MC\| = 2.37 s.e. (limit 4). |
| DP vs exact rational (n = 4) | brute force over all 2³ outcomes in `Fraction`: max diff 1.1e-16. |
| scale → ∞, κ = 0 | round robin P(top wins) = 0.9945 / 1 / 1 / 1 at smallest pairwise logit 0.5 / 2 / 8 / 32; at 32 all five formats give 1.000. |
| scale = 0 | KO-random, KO-elo exactly uniform; Swiss, Groups+KO, round robin pass χ² uniformity (p = 0.21, 0.11, 0.53; max \|p − 1/8\| ≤ 0.0026). |
| KO-random exact vs MC | max 1.22 s.e. |
| Match counts | 7, 7, 12, 15, 28. |
| Nash LP | RPS → (1/3, 1/3, 1/3), unique; BT (n = 8) → the top player, unique; RPS with scissors duplicated → flagged non-unique, max-entropy Nash = (1/3, 1/3, 1/6, 1/6). |

Implementation notes and choices made:
- **Swiss pairing.** Players are ordered by score (random order within a score group). The pairing is the first
  rematch-free perfect matching in depth-first backtracking order (all 105 matchings of 8 players are precomputed),
  which is exactly what a backtracking pairer outputs; this makes it possible to vectorise over runs (≈ 0.07 s per
  10⁴ tournaments). With 8 players and 3 rounds exactly one player finishes 3–0, so Swiss never needs a tie-break.
- **KO-elo.** BT fit = least squares on L, i.e. g = row means of L (the Hodge potential); ties in g broken by player index.
- **Nash.** The LP gives one maximin strategy; uniqueness is checked with 2n LPs (min and max of each x_i over the Nash
  polytope). If not unique, the max-entropy Nash is computed with SLSQP. `refs.nash` reports which one it used.
- **BC cyclic variants.** `bc1` / `bc2` take the cyclic part of b cᵀ − c bᵀ from random blade/chest vectors in R¹ / R².
  The paper's inner-product model (Chen & Joachims 2016, eq. 4) is `M(a, b) = a_blade·b_chest − b_blade·a_chest + γ_a − γ_b`,
  which matches §2; its regulariser (§3.4) is λ Σ_a ‖a_blade − a_chest‖², which we will use for `fit_bc` in E2.

Caveats: the error bars in `E0_dp_vs_mc` are smaller than the markers at 10⁵ runs, so the figure only shows agreement;
the s.e. values are in the CSV. The three scale values (close/medium/decisive) are not calibrated yet; that is the first
step of E1.

## 4. Limitations and threats to validity

_To be filled in as experiments run._

## 5. Draft of report Section 1

_To be written after E1._
