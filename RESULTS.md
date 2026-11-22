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

- **Fitting the wrong model hides the organiser's power.** Archetype game (synthetic, true κ ≈ 0.65, n = 8, 20 instances,
  50 matches per pair): a BT fit puts organiser power at Π = 0.063 ± 0.004 against a true 0.197 ± 0.009 (3× too low) and
  K at 2.3 vs 4.2. A BC fit (paper's regulariser) recovers Π = 0.199 ± 0.009 and K = 4.5, and has lower held-out log-loss
  in 20/20 instances (by 0.081 ± 0.006 nats/match). The same holds with a ridge regulariser (Π = 0.184).
  (`outputs/fig/F3_rigging_bt_vs_bc.pdf`, `outputs/csv/e2_archetype.csv`, `..._ridge.csv`)
- **Real tennis looks like a ladder; apparent cycles are noise.** ATP 2015–2019, the 16 players with most mutual matches
  (614 matches): held-out log-loss BT 0.6416 vs BC 0.6415 (λ chosen on validation shrinks BC to BT; κ = 0). An
  under-regularised BC "finds" κ ≈ 0.7–0.8 and fits training data better (0.495 vs 0.589) but is far worse on later matches
  (1.13–1.81). Organiser power is moderate (Π ≥ 0.092, K ≥ 4: Djokovic, Federer, Nadal, Murray, a top block, consistent with P6).
  Lesson: **κ must be estimated out of sample**, or organiser power is overstated. (`outputs/csv/e2_tennis.csv`,
  `outputs/csv/e2_tennis_lambda_path.csv`, `outputs/fig/F3_rigging_bt_vs_bc.pdf` right panel)

**Surprises:**
1. **P6 (new conjecture): under BT the kingmakeable set is always a top segment {1, …, K} of the strength order.** True in all
   1,200 BT matrices at n = 8. It fails with cycles (top-segment share 0.987 at κ = 0.1, 0.878 at κ = 0.6). See `theory/P6.md`.
2. **P3 is not new:** it is exactly the main theorem of Chung & Hwang (1978), which we found only after proving it
   ourselves. Our proof route (factorise, then a "Ladder Lemma") matches theirs (ladder trees, their Lemma 2). What we add
   on top: under BT the weakest player is never favourite (one line from their theorem), K ≤ n − 1 is attained, and P6
   (top-segment structure, still a conjecture). Side observation: our ladder certificate has (h+2)^h monomials (Cayley numbers).
3. **An 8-player, 3-round Swiss with "most wins" crowns exactly the same distribution as a random knockout.** Round 2 pairs the four
   1–0 players at random, and round 3 forces the two 2–0 players to meet, so the champion's path *is* a random bracket. The 5
   extra matches only sort out the lower places. Confirmed: E4 metrics agree to 3 decimals, and 200k-run Swiss matches exact
   KO-random within 3 s.e. on 40/40 entries.
4. BT is more riggable than our hypothesis said: K = 1 in only 642/1,200 BT matrices, and one matrix had K = 6 of 8.
   The "small kingmakeable set under BT" claim should be "a top segment, typically 1–3 players".

## 2. Theory items

| Item | Status | Statement | File |
|---|---|---|---|
| P1 | not attempted | deterministic outcomes: transitive ⇒ K = 1; cyclic ⇒ tournament-fixing literature | — |
| P2 | example re-verified exactly (sympy, 30 digits); characterisation not attempted | BT is not organiser-proof; the example has K = 3 (A, B, C each favourite of one bracket) | `theory/P2.md` |
| P3 | **known theorem: Chung & Hwang (1978, JASA), all n, any tree**. Our independent computer-assisted proof covers n ≤ 32. 0 violations in 999,480 random + 2.4 M adversarial tests | BT: stronger player in the weaker one's slot does strictly better | `theory/P3.md` |
| P3(i) | **proved, all n** (one line from Chung & Hwang's theorem) | weakest never favourite; more strongly, a player is always beaten in W by a stronger first-round opponent | `theory/P3.md` |
| P3(ii) | **proved, all n** (known: Adler et al. 2017) | W_i increasing in g_i | `theory/P3.md` |
| P3(iii) | **proved, all n; tight** (K = 7 found at n = 8) | under BT, K ≤ n − 1 | `theory/P3.md`, `outputs/csv/p3_max_K_bt.csv` |
| P4 | example re-verified exactly (Fraction): W_B = 293/1000 is the unique max | cycles break P3; lowest-Borda B is crowned by {A,C}\|{B,D} | `theory/P4.md` |
| P5 | not attempted; E1 data: mean K increases in κ in 59 of 60 adjacent steps (n = 8, 6 cells; the exception is within noise) | E[K] monotone in κ? threshold κ* for the weakest player | — |
| P6 (new) | conjecture: 0 violations in 1,200 (E1) + 230,000 random + 615,000 adversarial tests (n = 4, 8); not proved | under BT the kingmakeable set is a top segment | `theory/P6.md` |

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

### P3 search and proof (done)

- `python theory/search_counterexamples.py --full`; seed 20261122; 35 s. Strength families: normal (scale 0.05–8), clustered
  (P2-like), heavy-tailed, near-ties. Results in `outputs/csv/p3_search.csv`. P3: n = 4 / 8 / 16, 399,798 / 399,777 /
  199,905 random tests, min slack ≥ 4e-40 (never negative); adversarial (2,000 × 400 per n) min slack ≥ 3e-34. P3(ii): 10⁶
  tests, 0 violations. P3(i) and P6: n = 4: 200,000 random + 600,000 adversarial; n = 8: 30,000 random + 15,000 adversarial;
  0 violations.
- Detector validation: the same code applied to cyclic matrices (κ = 0.6) flags 42/300 P3 violations and 21/300 P6
  violations, so a zero count under BT is meaningful.
- `python theory/ladder_lemma.py`: symbolic certificate for ladder depths 0–4 (< 3 s).
- `python theory/max_K_bt.py`: K = n − 1 attained at n = 4 and 8.
- Literature: **Chung & Hwang (1978) prove P3 itself** (their Theorem, any knockout tree, all n), plus the random-draw
  average as a corollary, and they show both fail under strong stochastic transitivity alone. We read the original
  (supplied by the humans on 22 Nov). P3 is cited, not claimed.

### E2 — BT vs BC on (synthetic) real-style data (archetype game done; tennis blocked)

- Command: `python experiments/e2_real.py --full`; seed 20261124; git commit a5817b9; runtime 41 s.
- **Archetype game** (`km.data.make_archetype_game`): 3 archetypes in an R→P→S→R counter loop (blade/chest directions 120°
  apart), σ_g = 0.5, cycle strength s = 0.8, vector noise σ_v = 0.3. These were tuned **before** any E2 metric was looked at, on
  a 400-draw grid, to hit the spec's κ target: mean κ = 0.62 (sd 0.15), mean |P − ½| = 0.21. Grid over σ_g ∈ {0.5, 1, 1.5} ×
  s ∈ {0.6, 0.8, 1, 1.2}. The 20 instances used have true κ = 0.634 ± 0.034.
- Per instance and N ∈ {10, 50} matches per pair: independent train / validation / test samples from the true P. BT = MLE;
  BC = d = 2 MLE, 3 random restarts, λ chosen on validation log-loss from {0.01, 0.1, 1, 3, 10, 30, 100} (chosen: mostly 1 at N = 10,
  3 at N = 50).
- **Regulariser (main analysis = the paper's).** Chen & Joachims regularise with λΣ‖bᵢ − cᵢ‖². This restrains vector
  *scale* only weakly: as λ goes 0.01 → 1000, fitted blades lengthen (mean norm 2 → 36) with κ unchanged, and the fit
  collapses to BT only near λ = 10⁵. Useful λ values are therefore large. With a first grid capped at 1000, selection
  kept picking the cap, and **we wrongly concluded the penalty "doesn't work" and briefly switched to a ridge penalty
  λΣ(‖bᵢ‖² + ‖cᵢ‖²). On the humans' challenge we ran both on identical data** (separate random stream for games and
  samples): with a wide grid {0.01, …, 10⁶} the paper's penalty selects interior λ (mostly 10³) and matches ridge on held-out
  log-loss (n = 8, N = 50: 0.5755 vs 0.5758, difference −0.0004 ± 0.0003), while estimating organiser power closer to the
  truth (Π 0.199 vs ridge 0.184; true 0.197). So the main analysis uses the paper's penalty, and ridge is a sensitivity
  check (`--reg ridge`, files `*_ridge.csv`). **Every E2 conclusion holds under both.**
- Command: `python experiments/e2_real.py --full` (and `--reg ridge`); seed 20261124; git commit 4aa72e5; ~60 s each.

Results (mean over instances, ± s.e. where shown; n = 8: 20 instances, exhaustive; n = 16: 3 instances, local search):

| n | N/pair | model | test log-loss | κ of P | K | Π | Jaccard vs true |
|---|---|---|---|---|---|---|---|
| 8 | – | true P | 0.563 / 0.568 | 0.649 | 4.20 ± 0.37 | 0.197 ± 0.009 | 1 |
| 8 | 10 | BT | 0.665 ± 0.005 | 0 | 2.15 ± 0.27 | 0.066 ± 0.004 | 0.47 |
| 8 | 10 | BC (paper) | 0.607 ± 0.010 | 0.59 | 4.10 ± 0.35 | 0.199 ± 0.013 | 0.64 |
| 8 | 10 | BC (ridge) | 0.601 | 0.52 | 3.50 | 0.157 | 0.63 |
| 8 | 50 | BT | 0.656 ± 0.004 | 0 | 2.30 ± 0.26 | 0.063 ± 0.004 | 0.56 |
| 8 | 50 | BC (paper) | 0.575 ± 0.005 | 0.65 | 4.50 ± 0.27 | 0.199 ± 0.009 | 0.79 |
| 8 | 50 | BC (ridge) | 0.576 | 0.62 | 4.10 | 0.184 | 0.82 |
| 16 | – | true P | 0.558 | 0.584 | ≥ 8.3 | ≥ 0.184 | 1 |
| 16 | 50 | BT | 0.642 | 0 | ≥ 1.7 | ≥ 0.062 | 0.47 |
| 16 | 50 | BC (paper) | 0.562 | 0.59 | ≥ 8.3 | ≥ 0.182 | 1.00 |

Held-out log-loss, BC (paper) better than BT: 19/20 instances at N = 10 (by 0.058 ± 0.008), 20/20 at N = 50 (0.081 ± 0.006).

Interpretation: with a cyclic ground truth, BT fits (κ = 0 by construction) underestimate organiser power about 3× and
miss about half the kingmakeable players. BC recovers both, and held-out log-loss correctly prefers it. With only 10
matches per pair the kingmakeable *set* is recovered less well (Jaccard 0.64), even though average power is right.
The weakest player was kingmakeable in only 1 of 20 true matrices, in line with E1 at κ ≈ 0.6.

**Tennis (done, 22 Nov).**
- Data: Jeff Sackmann's `atp_matches_2015…2019.csv`. The original `JeffSackmann/tennis_atp` repository was not found on
  GitHub on 22 Nov 2026. The humans pointed to `jasonmauss/tennis_atp`, but that copy is from March 2015 and has no match
  files. We used `zvonimir-rezo/tennis_atp`, a copy carrying Sackmann's full commit history, **pinned to commit
  2c40e40c0f3a (authored by Jeff Sackmann, 6 May 2026)**, so it contains no changes by the mirror's owner; each 2015–2019
  file was last modified by Sackmann (30 Dec 2024). Checksums and provenance: `data/raw/tennis_atp/` (not committed).
- Players: the 16 with the most matches among themselves (greedy removal from the top 60 by match count): 614 matches.
  Time-ordered split: 491 train / 123 test; BC λ chosen on the last 20% of the training period (chosen λ = 10³, paper's
  penalty; ridge chooses λ = 3).
- Held-out log-loss: BT 0.6416, BC 0.6415, coin flip 0.6931. Fitted κ = 0 (BC reduces to BT; ridge gives κ = 0.02). On the full data BT and BC
  give the same metrics: K ≥ 4 (Djokovic, Federer, Nadal, Murray), Π ≥ 0.092 (local search, 10 restarts).
- λ path (`experiments/e2_tennis_lambda_path.py`, `outputs/csv/e2_tennis_lambda_path.csv`). Paper's penalty: λ = 0.01 →
  κ = 0.72, train 0.495, test 1.813; λ = 1 → κ = 0.78, test 1.132; λ = 100 → κ = 0.55, test 0.757; λ ≥ 10³ → κ = 0, test
  0.6415. Ridge: λ = 0.01 → κ = 0.79, test 1.355; λ ≥ 3 → κ = 0, test 0.6416. In-sample cyclicity in a 614-match dataset is
  over-fitting.

## 4. Limitations and threats to validity

- Only one real dataset (ATP, 16 players, 614 matches), and it is ~transitive out of sample. With this little data, BC
  could not detect weak cycles even if present, so "κ ≈ 0" means "no cycles detectable", not "proved transitive".
- BC fits depend on λ selection. The paper's penalty needs a very wide grid (useful λ ~10³); the conclusions hold under
  ridge as well (sensitivity check in E2).
- n = 16 results are local-search lower bounds with 10 restarts.
- "Weakest" is defined by the Hodge/BT potential; under cycles there is no canonical weakest player (Borda alternative recorded).
- E4 uses one scale (medium) and n = 8; the size of format differences will depend on decisiveness.
- The scales are calibrated at κ = 0; at higher κ the same scale gives slightly less decisive matches
  (medium: mean |P − ½| 0.179 at κ = 0, 0.176 at 0.5, 0.172 at 1; recorded per matrix in `e1_n8_raw.csv`), so the rise
  in Π with κ is not an artefact of matches becoming more decisive.

## 5. Draft of report Section 1

_To be written after E1._
