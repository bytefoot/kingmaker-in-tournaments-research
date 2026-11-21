# Plain-language notebook (follow-along)

`RESULTS.md` is the technical lab log. This file explains the same work in plain words, one step at a time.
Each step ends with a **💬 Your thoughts** box. Write anything there (questions, doubts, ideas, "this seems wrong")
and I'll pick it up next time we talk.

---

## The idea in one paragraph

In a knockout tournament, *who you face* matters as much as *how good you are*. The organiser chooses the bracket.
How much can that choice change who wins? We suspect the answer depends on whether matchups are **"ladder-like"**
(a clear ranking: if A beats B and B beats C, then A beats C) or **"rock-paper-scissors-like"** (cycles: A beats B,
B beats C, but C beats A). Our dial for this is **κ (kappa)**: 0 = a pure ladder, 1 = pure cycles.
The bet: with more cycles, the organiser can crown more people, including players who look weak overall.

Two models of the world:
- **Bradley–Terry (BT):** every player has one strength number. Always ladder-like (κ = 0).
- **Blade–Chest (BC):** every player also has an "attack style" (blade) and a "weak spot" (chest), so rock-paper-scissors is possible.

## Words we use

| Term | Meaning |
|---|---|
| `P[i, j]` | chance that i beats j in one match |
| bracket | who is placed where in the knockout tree. With 8 players there are exactly 315 genuinely different ones |
| W_i | chance player i wins the whole tournament, for a given bracket (computed exactly, not simulated) |
| kingmakeable | there is *some* bracket where this player is the single most likely winner |
| K | how many players are kingmakeable (1 = the organiser can't change the favourite; 8 = they can crown anyone) |
| rigging range R_i | best bracket for i minus worst bracket for i |
| Π (organiser power) | the average rigging range over all players |
| scale | how decisive matches are: "close" (≈ coin flips, typical P ≈ 0.58), "medium" (≈ 0.68), "decisive" (≈ 0.82) |

---

## Step 0: E0, checking the machinery (done ✅)

**What:** before trusting any result, we checked that the code computes what it claims, for example:
- the exact win-probability formula agrees with simply simulating 100,000 tournaments;
- there are really 315 distinct 8-player brackets;
- the "how cyclic is it" dial (κ) comes out exactly as requested;
- with coin-flip matches every format picks a uniformly random winner; with near-certain matches the best player always wins;
- the game-theory "Nash" calculation gives ⅓-⅓-⅓ for rock-paper-scissors.

**Result:** 26/26 checks pass.
**Why so fast (2 s)?** Small problems. 8 players means 315 brackets, and each bracket is a few dozen multiplications.
The 100,000 simulations run as one big array operation, not one at a time.

💬 **Your thoughts:**
>

---

## Step 1: re-checking the two starting examples (done ✅)

**Example 1 (P2): even a pure ladder can be rigged.** Strengths A = 1.0, B = 0.95, C = 0.8, D = −3.0 (D is hopeless).
If the organiser pairs **A vs B** and **C vs D** in the semis, C gets a near-free pass to the final and becomes the
favourite: **C wins 44.6% of the time vs A's 28.7%.** In fact A, B and C can each be made favourite by choosing who
gets to play D. Only D can never be made favourite.
→ So "the bracket matters" alone isn't our finding; it's true even without cycles.

**Example 2 (P4): with cycles, the *weakest* player can be crowned.** In this 4-player table, B has the lowest average
win rate (42.3%). But B's only bad matchup is A, and A's nemesis C is likely to knock A out first. Bracket
{A vs C} | {B vs D} makes **B the favourite at exactly 29.3%**. With a pure ladder that's impossible (we'll try to prove this in P3).

Both checked with exact fractions, not rounded decimals. Files: `theory/P2.md`, `theory/P4.md`.

💬 **Your thoughts:**
>

---

## Step 2: E1, does organiser power grow with cycles? (done ✅)

**What we did:** made 13,200 random 8-player worlds with the cycle dial κ set from 0 to 1 and three levels of
decisiveness. For each world we checked **all 315 brackets** exactly and counted how many players the organiser could
make the favourite (K), and how much a player's title chance can be pushed up or down (Π).
Then a smaller run with 16 players, where there are too many brackets to check, so we search for good ones.

**Picture:** `outputs/fig/F2_power_vs_kappa_skew.pdf` (left: K, right: Π; x-axis: how cyclic).

**What we found, in words:**
1. **More cycles mean more power for the organiser.** Medium decisiveness: about **2** of 8 players can be made favourite
   in a pure ladder, about **3.5** at κ = 0.6, and essentially **all 8** in pure rock-paper-scissors. Same story at 16 players
   (about 5 → 9.5 → 16).
2. **Decisive matches plus cycles give the most power.** When matches are near coin flips, the bracket barely matters
   whatever κ is. When matches are lopsided, cycles let the organiser swing a player's title chance by about 0.49 on
   average, versus 0.09 with no cycles.
3. **The bottom player is hard to crown.** Mid-table players become crownable gradually, but the very weakest player is
   *never* crownable unless the world is very cyclic (κ ≥ 0.6 at the earliest, mostly κ ≥ 0.8).
4. **Surprise (new conjecture, P6):** in a pure ladder world the crownable players are **always the top few**: if the 3rd
   best can be crowned, so can the 1st and 2nd. That held in all 1,200 ladder worlds we tried. With cycles it starts to break.
5. **Correction to our starting hypothesis:** a pure ladder is *more* riggable than we assumed. Only about half the time
   is the best player the only possible favourite, and once 6 of 8 were crownable.

**How sure are we?** Every point is an average over 200 worlds, with a 95% confidence band (the shaded strip). A second
program written from scratch gave identical answers on 96 test worlds. The 16-player numbers are lower bounds, because
the search can miss the best bracket.

**Questions for you:**
- Is "weakest = lowest overall strength score" the right meaning of "weakest" under cycles? The alternative is "lowest
  average win rate"; it gives similar but slightly lower rates.
- Finding 3 cuts against "a little cyclicity is enough". Do we want to lean into "crownability spreads gradually down the
  table" as the story?
- P6 could be a nice clean theorem for the report. Should we prioritise proving it alongside P3?

💬 **Your thoughts:**
>

---

## 📝 Notes for the report (things to make sure we write about)

1. **Explain K and Π with the 4-player P2 example (Kevin liked this, 22 Nov).** Use one small table where each row is a
   bracket and the columns show each player's title chance. K and Π can then be read straight off it:
   - Favourite per bracket: C, B, A, so **K = 3** (D never). The favourite is always whoever is drawn against hopeless D,
     because that player gets a near-free pass to the final. (C beats D 98%, then wins the final ~46%, giving 44.6%; A must
     win two close matches, 51% × 56% giving 28.7%.)
   - Best minus worst bracket per player: A, B, C each ≈ 23.4 points, D ≈ 0, so **Π ≈ 0.175**.
   - Then: "Row 1 of our results = how many *different* players can be made favourite; row 2 = how far the bracket moves a
     typical player's title chance (fair share with 8 players is 12.5%)."
   - Length: probably a compact version in Section 1 or 2 (one table + 3–4 sentences), maybe the full walk-through as a boxed
     example. Decide when drafting.

---

## Step 3: P3, can we *prove* that a pure ladder protects the bottom player? (done ✅, mostly)

**The claim (P3):** in a pure-ladder (BT) world, take any bracket and swap a stronger player into a weaker player's slot.
The stronger player then does *better* there than the weaker one did.

**What we did:**
1. **Tried hard to break it first.** About 1 million random tests plus 2.4 million steps of a search actively trying to
   find a counterexample, with 4, 8 and 16 players. Zero failures. We checked that the same search *does* find failures
   when there are cycles, so "zero" means something.
2. **Checked the literature.** Chung & Hwang (1978) proved a related averaged version ("stronger players win more
   *random-draw* knockouts under BT"). We couldn't find our exact "same bracket, swapped slot" version stated anywhere, but we
   couldn't read their original paper. 👉 *Could you check it on JSTOR through the IITM library?*
3. **Proved it.** The proof boils the claim down to a tiny "ladder" game: someone waits at the top while a challenger
   climbs past a few fixed opponents. Proving "the stronger waiting player does better" in that ladder is enough. For
   ladders of up to 4 steps, which covers every bracket up to 32 players, the computer algebra shows the difference is
   (strength gap) × (a sum of positive terms), so it can never be negative. For 4 players the whole proof fits on paper.

**Consequences, in words:**
- **The bottom player can never be the favourite, under any bracket, for any number of players.** The proof is short:
  your first-round opponent is stronger than you, and that alone means they beat your title chance.
- But under BT the organiser *can* crown up to everyone except the bottom player. We found an 8-player world where 7
  different players can be made favourite: seven nearly equal players plus one hopeless one, where whoever is drawn
  against the hopeless player gets a free round.
- So the honest BT story is: **the bottom is protected, the top is not.** With cycles, the bottom is no longer protected (P4, E1).

💬 **Your thoughts:**
>

---

## Step 4: E2, what if we only see match results, not the true odds? (archetype half done ✅, tennis blocked ⚠️)

**Set-up:** we invented a small strategy game (not based on any real game) with three play styles in a
rock-paper-scissors loop, plus individual skill. About 60% of what decides a match is the style matchup (κ ≈ 0.6).
We *played* 10 or 50 matches between every pair, then "forgot" the true odds and estimated them with BT
(one strength number per player) and with BC (strength plus style).

**What we found:**
- **BT hides the organiser's power.** Because BT can't represent cycles, it says the organiser can swing a player's
  chances by about 6 points, when the truth is about 19 points. That's 3× too low. It also misses most of the players
  who could be crowned.
- **BC sees it.** With 50 matches per pair, BC estimates about 17 points of swing and finds most of the right crownable players.
- **The data can tell which model to believe.** On fresh matches BC predicted better than BT in all 20 game instances.
- **With little data (10 matches per pair) even BC underestimates a bit,** because with few matches the fit cautiously
  leans back toward the simpler model.

**A technical change I made (please sanity-check):** the Blade–Chest paper's way of preventing over-fitting turned out
not to work in our setting (the fitted vectors just grew longer instead of simpler). So I used a standard alternative
("ridge"). Both are in the code, and the reason is written up in RESULTS.md.

**Tennis is blocked:** the public ATP data repository the plan pointed to no longer exists on GitHub. See the question below.

💬 **Your thoughts:**
>
