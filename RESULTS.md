# RESULTS — Kingmakers & Formats (lab notebook)

## 1. Headline findings

- **Organiser power grows steadily with the cyclic share κ.** n = 8, all 315 brackets, 200 matrices per point, medium
  scale, random-skew cycles: kingmakeable players K rises from 1.98 [1.82, 2.15] at κ = 0 to 3.46 [3.29, 3.65] at κ = 0.6
  and 7.93 [7.89, 7.96] at κ = 1; organiser power Π rises from 0.092 to 0.153 to 0.197. Same shape for BC-d2 cycles
  (K 1.94 → 3.45 → 7.74). (`outputs/fig/F2_power_vs_kappa_skew.pdf`, `..._bc2.pdf`; `outputs/csv/e1_n8_summary.csv`)
- **Decisive matches amplify the effect of cycles on Π about fivefold.** Decisive scale: Π = 0.091 at κ = 0 vs 0.490 at κ = 1;
  close scale: 0.045 vs 0.072. At κ = 0 decisive matches give the *fewest* kingmakeable players (K = 1.45), at high κ the most.
- **The very weakest player needs a lot of cyclicity.** It is kingmakeable in 0/200 matrices in every cell with κ ≤ 0.5
  (both variants, all scales); first appears at κ ≈ 0.6–0.8; at κ = 0.9 the rate is 3% (close), 13% (medium), 43% (decisive).
  So "low-ranked players become kingmakeable" holds gradually (worst kingmakeable rank 1.98 → 3.52 → 8.0, medium), but the
  *bottom* player only at high κ.
- **Trend holds at n = 16** (local search, lower bounds, 20 matrices/point, medium): K ≥ 4.9 [3.95, 5.75] at κ = 0,
  ≥ 9.5 [8.65, 10.3] at κ = 0.6, 16 at κ = 1; Π ≥ 0.106 → 0.158 → 0.204. (`outputs/csv/e1_n16.csv`)

**Surprises:**
1. **P6 (new conjecture): under BT the kingmakeable set is always a top segment {1, …, K} of the strength order.** True in all
   1,200 BT matrices at n = 8. It fails with cycles (top-segment share 0.987 at κ = 0.1, 0.878 at κ = 0.6). See `theory/P6.md`.
2. BT is more riggable than our hypothesis said: K = 1 in only 642/1,200 BT matrices, and one matrix had K = 6 of 8.
   The "small kingmakeable set under BT" claim should be "a top segment, typically 1–3 players".

## 2. Theory items

| Item | Status | Statement | File |
|---|---|---|---|
| P1 | not attempted | deterministic outcomes: transitive ⇒ K = 1; cyclic ⇒ tournament-fixing literature | — |
| P2 | example re-verified exactly (sympy, 30 digits); characterisation not attempted | BT is not organiser-proof; the example has K = 3 (A, B, C each favourite of one bracket) | `theory/P2.md` |
| P3 | not attempted | BT swap-monotonicity | — |
| P4 | example re-verified exactly (Fraction): W_B = 293/1000 is the unique max | cycles break P3; lowest-Borda B is crowned by {A,C}\|{B,D} | `theory/P4.md` |
| P5 | not attempted; E1 data: mean K increases in κ in 59 of 60 adjacent steps (n = 8, 6 cells; the exception is within noise) | E[K] monotone in κ? threshold κ* for the weakest player | — |
| P6 (new) | conjecture, 1,200 + 20 tests, no counterexample search yet | under BT the kingmakeable set is a top segment | `theory/P6.md` |

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

### E1 — organiser power vs κ (done)

- Command: `python experiments/e1_power_vs_kappa.py --full`; seed 20261119; git commit d023b7e; runtime 311 s
  (n = 8 grid 3.8 s, local-search validation 15 s, n = 16 291 s).
- Scales (calibrated so mean off-diagonal |P − ½| at κ = 0 hits the target; 4,000 draws; `outputs/csv/e1_scales.csv`):
  n = 8: close 2.960, medium 7.334, decisive 18.222; n = 16: close 6.262, medium 15.668, decisive 39.744.
- Grid at n = 8: κ ∈ {0, 0.1, …, 1} × 3 scales × {skew, bc2} × 200 matrices = 13,200 matrices, exhaustive over 315 brackets.
  CIs: 95% percentile bootstrap of the mean over the 200 matrices (2,000 resamples).
- "Weakest player" = lowest Hodge potential s (row mean of L, the least-squares BT strength). The lowest-Borda player is
  also recorded (`borda_weakest_kingmakeable`); it is kingmakeable somewhat less often at high κ (e.g. decisive κ = 0.9:
  0.215 vs 0.425).
- Figures: `outputs/fig/F2_power_vs_kappa_skew.pdf` (headline) and `F2_power_vs_kappa_bc2.pdf`.

Key numbers (skew cycles; mean [95% CI]; `outputs/csv/e1_n8_summary.csv`):

| scale | K at κ = 0 | K at 0.6 | K at 1 | Π at 0 | Π at 0.6 | Π at 1 | weakest kingmakeable at 0.9 |
|---|---|---|---|---|---|---|---|
| close | 2.04 [1.89, 2.20] | 3.12 [2.96, 3.29] | 7.97 | 0.045 | 0.061 | 0.072 | 0.03 [0.01, 0.06] |
| medium | 1.98 [1.82, 2.15] | 3.46 [3.29, 3.65] | 7.93 | 0.092 | 0.153 | 0.197 | 0.13 [0.09, 0.18] |
| decisive | 1.45 [1.34, 1.57] | 4.19 [3.98, 4.39] | 7.64 | 0.091 | 0.327 | 0.490 | 0.43 [0.36, 0.50] |

Interpretation: both K and Π increase with κ at every scale and for both cycle types; the effect on Π is driven by
decisiveness (cycles only matter if matches are lopsided enough for the matchup to decide things). Kingmakeability spreads
down the ranking gradually; the bottom player is only reachable at κ ≳ 0.8. The two cycle generators give very similar
curves (bc2 slightly lower Π at high κ: decisive κ = 1, 0.452 vs 0.490).

**Local-search validation (n = 8, medium, 33 matrices × 8 players, `outputs/csv/e1_ls_validation.csv`):** hit rate of the
exhaustive optimum with 1 / 5 / 10 / 50 restarts: Wmax 0.70 / 0.94 / 0.977 / 1.00; Wmin 0.74 / 0.98 / 0.992 / 1.00;
kingmakeability margin 0.59 / 0.90 / 0.981 / 1.00. Mean gap at 10 restarts ≤ 2.1e-4. n = 16 used 10 restarts to fit the
time budget, so its K and Π are lower bounds and could be noticeably low (the search space is far larger than at n = 8).

**Independent check** (`experiments/e1_independent_check.py`, `outputs/csv/e1_independent.csv`): a separate pure-Python
recursion over all 40,320 seedings (no km.bracket code) reproduces K exactly on 96/96 matrices (skew and bc2, κ ∈ {0, 0.3,
0.6, 1}, medium scale) and Π to 2.8e-17. Not checked independently: `make_P` (covered by E0) and the bootstrap.

Caveats: 200 matrices per cell gives CI half-widths on K of ~0.15–0.2, under 10% of the κ = 0 → 0.6 change (1.5 at medium).
Mean K increases in 59 of 60 adjacent κ steps; the one exception (bc2 close, κ = 0.4 → 0.5: 2.845 → 2.780) is within the CIs. n = 16 is a single scale
and cycle type with 20 matrices per point.

## 4. Limitations and threats to validity

- Synthetic P only so far; whether real data has high κ is E2's question.
- n = 16 results are local-search lower bounds with 10 restarts.
- "Weakest" is defined by the Hodge/BT potential; under cycles there is no canonical weakest player (Borda alternative recorded).
- The scales are calibrated at κ = 0; at higher κ the same scale gives slightly less decisive matches
  (medium: mean |P − ½| 0.179 at κ = 0, 0.176 at 0.5, 0.172 at 1; recorded per matrix in `e1_n8_raw.csv`), so the rise
  in Π with κ is not an artefact of matches becoming more decisive.

## 5. Draft of report Section 1

_To be written after E1._
