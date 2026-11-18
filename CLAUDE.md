# CLAUDE.md — Kingmakers & Formats

Course project for **DA5453 "Learning from Human Preferences"** (team: Kevin Kinsey S EP23B027, Aditri Jain ED23B060).
Base paper: Chen & Joachims, *Modeling Intransitivity in Matchup and Comparison Data* (Blade-Chest), WSDM 2016.
Hard deadline: **report PDF due Fri 27 Nov 2026, end of day (IST)**. Results must be frozen by **Tue 24 Nov**.

You (Claude Code) are the research engineer and the first-pass mathematician. The humans will proofread, adjust and write the
final report later. Your job: build the simulation code, run the experiments, try to prove or refute the theory claims, and leave
behind results that hold up and can be checked, with an honest log of what you found. Read this whole file before writing code.

---

## 1. The research question (do not drift from it)

**When pairwise matchups are cyclic (intransitive), how much of *who wins* is decided by the tournament (its bracket and its
format) rather than by the players?** We measure this as a function of how cyclic the matchups are, with Bradley–Terry (BT) and
Blade-Chest (BC) as the two models of the world.

The refined hypothesis (already partly checked, see §4):
- Even under BT, an organiser can make a player who isn't the strongest into the favourite. So "the bracket matters" isn't the finding.
- The finding we are after: **cycles change *which* players can be crowned.** Under BT the weakest player (we conjecture) can
  never be made favourite, and the set of kingmakeable players is small. With cycles, low-ranked players become kingmakeable and
  the organiser's power grows with the cyclic share κ.
- Second half: under cycles, **which tournament format crowns a sensible winner**, and at what cost in matches?

The professor values, in order: a clearly stated question and why it matters, one key idea done well, honest results
(inconclusive is fine if explained), legible figures. Everything you produce should serve that.

---

## 2. Definitions (use exactly these; put them in `src/km/` docstrings)

**Players and matchups.** n players, n a power of 2 (n = 4, 8 for exact work; n = 16 for search). `P[i, j]` = probability i beats
j; `P[i, j] + P[j, i] = 1`; diagonal 0.5. Logits `L = logit(P)` form a skew-symmetric matrix.

- BT: `L[i, j] = g[i] - g[j]`
- BC (inner-product form): `L[i, j] = g[i] - g[j] + b[i]·c[j] - b[j]·c[i]` with blade `b[i]` and chest `c[i]` in R^d.

**Hodge split on the complete graph.** For any skew-symmetric L: `s = L.mean(axis=1)`, `T[i, j] = s[i] - s[j]` (ranking part),
`C = L - T` (cyclic part; every row of C sums to 0). Check numerically that `T` and `C` are orthogonal in the Frobenius inner
product. **Cyclic share** `κ = ||C||_F² / ||L||_F²` ∈ [0, 1].

**Synthetic generator `make_P(n, kappa, scale, rng)`.**
1. `T̂`: draw `g ~ N(0, 1)`, build `T`, normalise to `||T̂||_F = 1`.
2. `Ĉ`: draw a random skew-symmetric matrix A (upper triangle N(0,1)), subtract its ranking part, normalise to `||Ĉ||_F = 1`.
   Also provide a variant where Ĉ comes from random BC vectors with d = 1 and d = 2 (structured cycles), and say which variant each result used.
3. `L = scale · (sqrt(1-κ)·T̂ + sqrt(κ)·Ĉ)`, `P = sigmoid(L)`.
4. Assert that the realised κ of L equals the target κ to 1e-9, since T̂ ⟂ Ĉ by construction.
`scale` controls how decisive matches are. Pick three scales so that, at κ = 0, the mean |P − 0.5| is about 0.08 ("close"),
0.18 ("medium") and 0.32 ("decisive"). Calibrate numerically for each n and record the values used.

**Brackets.** A bracket is a seeding of n players into the leaves of a balanced binary tree; leaves (0,1) meet in round 1, the
winners of (0,1) and (2,3) meet in round 2, and so on. Two seedings are the same bracket if one can be turned into the other by
swapping the two subtrees under any node. Number of distinct brackets = `n! / 2^(n-1)` (n = 4: 3; n = 8: 315;
n = 16: 638,512,875). Write `enumerate_brackets(n)` giving canonical representatives and **assert the count** for n = 4 and 8.

**Exact win probability (DP).** For node v with children A, B and i in A: `q_v(i) = q_A(i) · Σ_{j∈B} q_B(j) · P[i, j]`; leaves
q = 1; `W_i(σ) = q_root(i)`. O(n²) per bracket. Vectorise over brackets for n = 8.

**Bracket metrics.**
- `Wmax_i = max_σ W_i(σ)`, `Wmin_i = min_σ W_i(σ)`, rigging range `R_i = Wmax_i − Wmin_i`.
- Kingmakeable: there is a bracket σ where i is the unique argmax of W(σ) (ties within 1e-12 don't count). `K(P)` = count.
- Organiser power `Π(P) = mean_i R_i`.
- Also store, for each player, the arg-max bracket, so examples can be shown in the report.

**Formats** (n = 8; 10,000 Monte Carlo runs per (P, format) unless the exact computation is cheap):

| Format | Rules | Matches |
|---|---|---|
| KO-random | uniform random bracket (exact: average W over all 315 brackets) | 7 |
| KO-elo | seed by a BT fit to P (`g` = least-squares fit to L), standard seeding 1v8, 4v5, 2v7, 3v6 | 7 |
| Swiss | 3 rounds, round 1 random, then pair within score groups, no rematches (backtracking pairing), winner = most wins, ties broken uniformly at random | 12 |
| Groups+KO | random split into two round-robin groups of 4, top 2 by wins (ties random), semis A1vB2 and B1vA2, final | 15 |
| Round robin | everyone plays everyone once, most wins, ties random | 28 |

**Reference "who should win"** (there may be no best player under cycles):
- Copeland winner(s): maximise #{j : P[i, j] > 0.5}. If tied, split credit equally.
- Borda winner: maximise the mean of `P[i, :]` excluding the diagonal.
- Nash mass: the maximin strategy x of the symmetric zero-sum game with payoff `A = P − 0.5`, found by `scipy.optimize.linprog`
  (maximise v subject to `Aᵀx ≥ v`, `Σx = 1`, `x ≥ 0`). If the solution isn't unique, also report the max-entropy Nash
  (Balduzzi et al. 2018, Nash averaging) via a second LP or a small convex solve, and say which one you used.

**Format metrics.** `P(winner ∈ Copeland set)`, expected Nash mass of the winner `Σ_i P(i wins)·x_i`, P(winner = Borda winner),
entropy of the winner distribution (bits), matches played.

---

## 3. Repository layout (create it)

```
kingmakers/
  CLAUDE.md
  RESULTS.md            # running lab notebook; see §7
  pyproject.toml        # numpy, scipy, pandas, matplotlib, pytest (+ torch only if BC fitting needs it)
  src/km/
    models.py           # sigmoid/logit, hodge_split, kappa, make_P, fit_bt, fit_bc
    bracket.py          # enumerate_brackets, win_probs (DP), win_probs_mc, exhaustive_metrics, local_search
    formats.py          # simulators for the five formats
    refs.py             # copeland, borda, nash (LP), maxent nash
    data.py             # synthetic archetype game + tennis loader (§5 E2)
    plotting.py         # one shared style (see §6)
  tests/                # pytest; must all pass before any experiment is reported
  experiments/
    e0_sanity.py  e1_power_vs_kappa.py  e2_real.py  e3_misspec.py  e4_formats.py  e5_bo3.py
  theory/
    search_counterexamples.py
    P1.md P2.md P3.md P4.md P5.md   # statements, proofs or refutations, in Markdown + LaTeX math
  outputs/{csv,fig}/    # every number in the report comes from a file here
```

Conventions: Python ≥ 3.10, type hints, NumPy vectorisation, `numpy.random.default_rng(seed)` passed explicitly (never global
seeding). Every experiment script takes `--quick` (seconds, for smoke tests) and `--full`, writes a CSV plus a figure, and logs
its seed, parameters, git commit hash and runtime at the top of the CSV (as comment lines) and in RESULTS.md.

---

## 4. Theory: what to prove, refute or test

Rule: **numerical falsification first, proof second.** For each claim, run an aggressive search for counterexamples
(random + adversarial: hill-climb on P to break the claim) before attempting a proof. If a counterexample exists, the claim is
refuted; record the smallest one you can find, with exact rational or round numbers if possible, and verify it by hand in the `.md`.
Use exact arithmetic (`fractions.Fraction` or `sympy`) to double-check every published example. Never write "proved" in
RESULTS.md unless the `.md` contains a complete argument that you have re-read step by step; otherwise say "conjecture,
supported by N tests".

**P1 (baseline).** (a) Deterministic transitive outcomes (P ∈ {0,1}, acyclic): the top player wins every bracket, K = 1. Easy
proof. (b) Deterministic cyclic outcomes: relate to known tournament-fixing results (Vassilevska Williams 2010: a king who
beats ≥ n/2 players can win some bracket; Kim & Williams; Manurangsi & Suksompong IJCAI 2022). Cite, don't reprove; give one
small example where every player can win some bracket.

**P2 (BT is not organiser-proof).** Already found: γ = (1.0, 0.95, 0.8, −3.0) for A, B, C, D; bracket {A,B} | {C,D} gives
W_C ≈ 0.446 > W_A ≈ 0.287. Re-verify exactly. Then characterise: under BT with n = 4, for which γ can the k-th strongest be made
favourite? Aim for a clean closed-form condition or a clear picture of the region (a 2D slice plot is fine).

**P3 (BT swap-monotonicity, the main theorem attempt).** Claim: under BT, if g[i] > g[j], then swapping i into j's slot gives
`W_i(σ') ≥ W_j(σ)`. Already: 0 violations in 3,000 random 8-player tests; run ≥ 10⁶ including adversarial search, n = 4, 8, 16.
Corollaries to test and prove: (i) the weakest player is never the unique favourite; (ii) `W_i(σ)` is non-decreasing in g[i]
with everything else fixed; (iii) what bound on K(P) under BT follows. **Check the literature** before claiming novelty:
knockout-tournament monotonicity under strong stochastic transitivity (search: Hwang 1982 "New concepts in seeding knockout
tournaments", Chung & Hwang 1978, Israel 1981, Horen & Riezman 1985 "Comparing draws for single elimination tournaments",
Schwenk 2000 "What is the correct way to seed a knockout tournament?"). If it's known, cite it and give our own short proof for n = 4
with a sketch for general n (induction on rounds is the natural route: the DP is a composition of maps that preserve "stronger
at the same slot ⇒ at least as likely to come out").

**P4 (cycles break P3).** Already found (row beats column):

```
      A     B     C     D
A     -   0.95  0.20  0.62
B   0.05    -   0.72  0.50
C   0.80  0.28    -   0.39
D   0.38  0.50  0.61    -
```
B has the lowest average win rate (0.42), yet bracket {A,C} | {B,D} makes B the favourite at ≈ 0.293. Re-verify exactly, then
find a **cleaner** example with round numbers (e.g. probabilities in {0.1, 0.3, 0.5, 0.7, 0.9}) and the smallest κ that still
does it. Also find the 4-player instance that maximises "Borda rank of the crowned player" with the lowest κ: this shows how little
cyclicity is needed.

**P5 (stretch).** Is E[K(P)] monotone in κ at fixed scale? Look for a threshold κ* (as a function of scale) where the weakest
player first becomes kingmakeable with non-trivial probability. For n = 4 an analytic or semi-analytic answer may be possible.

If, while working, you find a *better* or *more surprising* theorem-shaped statement, write it down as a new P-item, test
it the same way and flag it at the top of RESULTS.md. Surprises are the most valuable output.

---

## 5. Experiments (in this order; each has a definition of done)

**E0: sanity (must pass before anything else).**
- DP vs Monte Carlo (10⁵ runs) on 5 random P for n = 8: max |difference| within 4 standard errors.
- Bracket count assertions; Hodge orthogonality; κ of `make_P` equals the target.
- Format simulators: at scale → ∞ and κ = 0, round robin picks the top player with probability → 1; at scale = 0 every
  format's winner distribution is uniform.
- Nash LP: on rock-paper-scissors it returns (1/3, 1/3, 1/3); on a BT matrix it returns the top player.
- **Done when:** `pytest` is green and `outputs/csv/e0.csv` records each check.

**E1: organiser power vs κ (the headline).** n = 8, exhaustive over 315 brackets. κ ∈ {0, 0.1, …, 1.0} × 3 scales × 200
matrices per cell, both Ĉ variants (random-skew, BC-d2). Output K(P), Π(P), and "weakest player kingmakeable" rate with 95%
bootstrap CIs. Repeat a reduced version at n = 16 with local search (below) to check the trend holds.
- **Figure F2:** K(P) vs κ, one line per scale, shaded CI; second panel Π(P) vs κ. At most 2 panels.
- **Done when:** the CSV and the figure exist, and RESULTS.md states the trend in one sentence with numbers (e.g. "K rises from
  1.3 at κ=0 to 4.1 at κ=0.6, medium scale").

**Local search for n = 16** (`bracket.local_search`): start from a random bracket; moves = swap any two leaves; accept if the
objective W_i improves (first-improvement), plus 50 random restarts; optionally simulated annealing. **Validate at n = 8**:
report how often local search hits the exhaustive optimum and the mean gap. Report n = 16 numbers as lower bounds on Wmax (and
upper bounds on Wmin).

**E2: real matchups, BT vs BC.**
- *Archetype game (synthetic, high κ).* **Do not use Pokémon or any real game's rules for this; it is a purely synthetic
  game.** It stands in for a strategy game with a few play styles that counter each other. Construction (`data.make_archetype_game`):
  3 archetypes with a rock-paper-scissors counter loop, each a direction in a d = 2 BC embedding (blade/chest vectors at 120°
  apart); every player = one archetype + individual noise on its vectors + its own skill g ~ N(0, σ_g). Tune σ_g and the cycle
  strength so that κ of the true P is about 0.5–0.7, and record the values. Use n = 8 players for exhaustive work and n = 16 for
  local search. Then pretend it's real data: sample N matches per pair (N ∈ {10, 50}), fit BT and BC (d = 2, λ by held-out
  log-loss) to the *sampled outcomes*, and compute every metric on both the fitted P and the true P. This shows how much of the
  organiser-power signal survives estimation from finite data.
- *ATP tennis (low κ, transitive control).* Data: Jeff Sackmann's `tennis_atp` GitHub repo (`atp_matches_YYYY.csv`).
  Clone/download it **only if network access works**; if not, stop and ask the humans to place the CSVs in `data/raw/`. Take a
  multi-year window (e.g. 2015–2019), pick the 16 players with the most matches against each other, fit BT and BC on all matches
  among them (time-ordered 80/20 split for log-loss), compute κ and the metrics.
- Report held-out log-loss for BT vs BC on both (this decides which P is "believable").
- **Figure F3:** per-player rigging range R_i, BT vs BC side by side, archetype game and tennis (2 panels max).
- **Done when:** both are processed, or the archetype game is, with an explicit note on why tennis failed.

**E3: Elo seeding in a cyclic world (misspecification).** For the archetype-game BC fit (and `make_P` with κ ∈ {0.3, 0.6}): seed by the BT
fit (standard seeding), compute each player's predicted W (under BT) and actual W (under BC). Report the largest gainers and losers,
and where the Elo-seeded bracket ranks among all 315 brackets for each player's W (percentile).
- **Figure F4:** predicted vs actual W scatter with the y = x line, labelled points.

**E4: formats.** For each format in §2 and κ ∈ {0, 0.2, …, 1.0}, medium scale, 200 matrices: all format metrics.
- **Figure F5:** P(winner ∈ Copeland set) vs κ, one line per format; second panel expected Nash mass of the winner. Put the
  number of matches in the legend (e.g. "Round robin (28)").
- Interpretation to test: round robin's advantage shrinks as κ grows. Check whether it does, and whether it ever reverses.

**E5 (optional, only if E1–E4 are done by 23 Nov).** Best-of-3 series: `p ↦ p²(3 − 2p)`. Re-run E1 at one scale. Does a
longer series amplify or damp organiser power?

**F0 (required by the professor):** a setup schematic, data → BT/BC fit → P → {bracket DP + search, format simulator} → metrics.
Produce `outputs/fig/F0_setup.pdf` with matplotlib or TikZ (`.tex` file), clean and simple. **F1:** the P4 example drawn as a
4-player bracket with win probabilities.

---

## 6. Figures and numbers

- matplotlib, vector PDF plus PNG, sized for the report: single column 3.4 × 2.6 in or full width 6.8 × 3.0 in; font ≥ 9 pt
  at final size; colour-blind-safe palette; same colour for the same format or model in every figure.
- No grids of tiny subplots (max 2 panels per figure). Axis labels with units or definitions (e.g. "cyclic share κ").
- Every number quoted in RESULTS.md must be traceable to a CSV in `outputs/csv/`. Report uncertainty (CI or ± s.e.) for
  every Monte Carlo quantity. Use enough samples that the CI half-width is < 10% of the effect you claim.

---

## 7. RESULTS.md (the lab notebook; the humans write the report from it)

Keep it current after every experiment. Structure:
1. **Top: headline findings** (3–6 bullets with numbers and the figure file each one comes from), plus a "Surprises" list.
2. Per P-item: status (proved / refuted / conjecture with N tests / not attempted), the one-line statement and the file.
3. Per experiment: parameters, seed, runtime, key numbers, figure path, a one-paragraph interpretation, caveats.
4. **Limitations and threats to validity** (model choice, the archetype game being synthetic, local-search lower bounds, etc.).
5. A short draft of report Section 1 ("question, why it matters, approach") updated to reflect what was actually found.

Be honest: if a hypothesis failed, say so plainly and explain what the evidence shows instead. A clean negative result
written up well is worth full marks; a hidden one is worth nothing.

---

## 8. Working rules

- **Order:** E0 → P2/P4 re-verification → E1 → P3 search + proof attempt → E2 → E3 → E4 → (E5) → F0/F1 → RESULTS.md polish.
  Commit after each step with a descriptive message.
- **Checkpoints:** stop and summarise for the humans (in chat) after E0, after E1, and before any change to the definitions in §2.
  If a definition turns out to be wrong or unworkable, propose the fix and wait for approval.
- **Compute budget:** everything should run on a laptop in < 30 minutes total at `--full`. If a run would take longer,
  reduce samples, vectorise, or ask.
- **Never fabricate data or results.** If a dataset can't be obtained, say so. Don't hand-type match results. Don't tune
  parameters until a hypothesis "works" without reporting that you did.
- **Independent check:** before declaring E1 and P3 done, re-derive the key numbers a second way (e.g. Monte Carlo vs DP; a
  fresh script written from the definitions, not from the existing code) and record the agreement.
- Keep the code small and readable; the humans need to explain it in the report. Prefer 50 clear lines to 200 clever ones.

## 9. Report (later, only when asked)

When the humans ask, produce `report/main.tex` (11 pt, LaTeX article, about 10–12 pages) following this outline:
1. Question, why it matters, approach (~2 pages; carries the most marks). 2. Background: BT, BC, Hodge split, knockout DP.
3. Theory: P1–P4 (+P5). 4. Setup with F0. 5. Organiser power: E1–E3. 6. Formats: E4. 7. Discussion: is "best" defined
under cycles; is rigging power a flaw or unavoidable; does the BT-vs-BC choice change the verdict; sensitivity to d and λ;
practical advice (should organisers measure κ?). 8. Conclusion + references. Names and roll numbers on page 1.
