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
> (Kevin, 23 Nov) Expected *more* decisive matches to mean *less* organiser power ("you can't dethrone someone that
> good"). Interesting that close matches are what kill rigging: with near coin-flips you can't steer much.
>
> (Claude's reply) Both intuitions show up in F2, and which one wins depends on κ (`e1_n8_summary.csv`, skew):
> - κ = 0 (ladder): your effect is real. Decisive has the *fewest* crownable players (K 1.45 [1.34, 1.57] vs
>   ≈ 2.0 for close/medium), and Π stops growing (medium 0.092, decisive 0.091). The top player is too good to dethrone.
> - κ = 1 (cycles): no one is undethronable, since everyone has a counter. Decisiveness then only *amplifies* the
>   organiser's choice of who meets whom: Π is 0.072 (close), 0.197 (medium), 0.490 (decisive).
> - Takeaway for the report: rigging needs **both** ingredients. Decisive matches make bracket choices matter, and
>   cycles mean no single player is safe from them. Close matches kill the first; a ladder kills the second.

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
2. **Explain how seeding works before E3 (Kevin, 24 Nov).** One short paragraph: rank players by Elo/BT, then 1v8, 4v5,
   2v7, 3v6 with #1 and #2 in opposite halves. Say plainly that this ranking *is* a ladder (BT) model, then describe
   "promised vs actual" and read F4 (diagonal = promise kept, above = luckier).
3. **Rigging needs two ingredients: decisive matches + cycles (Kevin, 23 Nov).** At κ = 0, more decisive matches *reduce*
   crownable players (K 1.45 vs ≈ 2.0) since the top player can't be dethroned; at κ = 1 decisiveness amplifies power
   (Π 0.07 → 0.20 → 0.49). Close matches or a ladder each kill rigging. Good Discussion sentence (F2, `e1_n8_summary.csv`).
4. **Spell out how a model "estimates the swing" before E2 (Kevin, 24 Nov).** Fit model → fitted P → same DP over all 315
   brackets → best minus worst per player → average = Π. BT is low because it irons out the cycles ("correct answer for the
   wrong world"); held-out log-loss tells you which fitted P to believe.

---

## Step 3: P3, can we *prove* that a pure ladder protects the bottom player? (done ✅, mostly)

**The claim (P3):** in a pure-ladder (BT) world, take any bracket and swap a stronger player into a weaker player's slot.
The stronger player then does *better* there than the weaker one did.

**What we did:**
1. **Tried hard to break it first.** About 1 million random tests plus 2.4 million steps of a search actively trying to
   find a counterexample, with 4, 8 and 16 players. Zero failures. We checked that the same search *does* find failures
   when there are cycles, so "zero" means something.
2. **Proved it our own way.** The proof boils the claim down to a tiny "ladder" game: someone waits at the top while a
   challenger climbs past a few fixed opponents. Computer algebra shows that for ladders of up to 4 steps the difference is
   always (strength gap) × (positive terms).
3. **Then found it's already known (thanks to your PDF).** Chung & Hwang (1978) proved exactly this, for any number of
   players and any bracket shape, and their proof also goes through "ladder trees". So in the report we **cite** P3 as their
   theorem and don't claim it as ours. Our versions of the consequences below are still useful, and P6 is still open.

**Consequences, in words:**
- **The bottom player can never be the favourite, under any bracket, for any number of players.** The proof is short:
  your first-round opponent is stronger than you, and that alone means they beat your title chance.
- But under BT the organiser *can* crown up to everyone except the bottom player. We found an 8-player world where 7
  different players can be made favourite: seven nearly equal players plus one hopeless one, where whoever is drawn
  against the hopeless player gets a free round.
- So the honest BT story is: **the bottom is protected, the top is not.** With cycles, the bottom is no longer protected (P4, E1).

💬 **Your thoughts:**
> Well fair this si rigours test of the inbuilt strucutre in all of these; but the foact the topc is not proetect is of signifcance iguess as that highlihgts our furhter experimentationz

---

## Step 4: E2, what if we only see match results, not the true odds? (archetype half done ✅, tennis blocked ⚠️)

**Set-up:** we invented a small strategy game (not based on any real game) with three play styles in a
rock-paper-scissors loop, plus individual skill. About 60% of what decides a match is the style matchup (κ ≈ 0.6).
We *played* 10 or 50 matches between every pair, then "forgot" the true odds and estimated them with BT
(one strength number per player) and with BC (strength plus style).

**What we found:**
- **BT hides the organiser's power.** Because BT can't represent cycles, it says the organiser can swing a player's
  chances by about 6 points, when the truth is about 20 points. That's 3× too low. It also misses most of the players
  who could be crowned.
- **BC sees it.** With 50 matches per pair, BC estimates about 20 points of swing (spot on) and finds most of the right crownable players.
- **The data can tell which model to believe.** On fresh matches BC predicted better than BT in all 20 game instances.
- **With little data (10 matches per pair) BC still gets the *amount* of power right, but is less sure *who* the
  crownable players are.**

**Correction about the anti-over-fitting penalty (you were right to question it):** I first claimed the Blade–Chest paper's
penalty "didn't work" and switched to a different one (ridge). When you pushed back, I tested both on *identical* data. The
paper's penalty works fine; it just needs a much larger dial setting (λ ≈ 1000) than I had tried. It predicts as well as
ridge and gets the organiser's power *closer* to the truth. So we now use **the paper's penalty**, with ridge as a backup
check. All conclusions are the same either way.

**Tennis (done, using a copy of Sackmann's data pinned to his own last commit):** among the 16 top players of
2015–2019, there's **no detectable rock-paper-scissors**. BC predicts fresh matches exactly as well as BT, because the
fit chooses to shrink BC back to BT. A sloppily fitted BC *claims* tennis is very cyclic (κ ≈ 0.8) but then predicts later
matches far worse than a coin flip. 👉 **Lesson for the report: you have to measure cyclicity on held-out matches, or you'll
"find" cycles that are just noise and overstate the organiser's power.** In tennis the crownable players are the Big
Four (Djokovic, Federer, Nadal, Murray), a top block exactly as P6 predicts for a ladder world.

💬 **Your thoughts:**
> this nice analysis i suppose; and for the tennis we can alwasy argue that - its the top tournament so we have technically preselected people; also that sstyle kinda averages out in sports due to rules and regulations the the specific sports or smthg like this

---

## Step 5: E3, does "seed by ranking" still work when there are cycles? (done ✅)

**Set-up:** organisers usually seed with an Elo-style ranking: best vs worst in round 1, top two in opposite halves.
That ranking assumes a ladder. We checked how wrong its predictions get when the world has cycles.

**Found:** with no cycles the predictions are exact. With cycles they drift: some player's title chance is off by about
5 points at κ = 0.3 and 7 points at κ = 0.6 (up to 10 in the strategy game). The "protected" top seed tends to do *worse*
than promised. Their seeded bracket goes from a good draw for them (87th percentile of all brackets) to a mediocre one
(65th). Who gains or loses depends on matchups, e.g. a seed whose path avoids its counter-style gains 7 points.

Picture: `outputs/fig/F4_elo_pred_vs_actual.pdf` (dots above the diagonal = luckier than predicted).

💬 **Your thoughts:**
> (Kevin, 24 Nov) The seeding explanation was needed: what Elo seeding *is* (1v8, top two in opposite halves) and that
> the ranking behind it is a BT ladder. Without that, E3 doesn't make sense. Explain it that way in the report.
>
> Key points to keep (from the chat walk-through):
> - The question is about an **honest** organiser, not a rigging one: seed by ranking, then see how wrong the ranking's
>   promises are when the world has cycles.
> - "Promised" = title chances computed with the ladder (BT) model; "actual" = the same bracket under the true cyclic P.
>   κ = 0 is the control (they match to 1e-17).
> - Why the top seed loses protection: seeding hands #1 the *overall* weakest opponents, but "weakest overall" is not
>   "easy for me". #8 may be exactly #1's counter-style.
> - Gains and losses follow **styles, not rank**: a one-number ranking can't see who counters whom.
> - Message: even with no rigging intent, ladder seeding in a cyclic world hands out hidden advantages. Measuring κ
>   first tells the organiser whether to trust the seeding (feeds Discussion, "should organisers measure κ?").

---

## Step 6: E4, which format picks a sensible winner when there are cycles? (done ✅)

**Set-up:** five formats for 8 players: knockout with a random draw (7 matches), knockout seeded by ranking (7), Swiss
(12), groups then knockout (15), everyone-plays-everyone round robin (28). For each we measured how often the champion is a
"deserving" winner: (a) beats the most opponents (Copeland), (b) best average win rate (Borda), (c) favoured by the
game-theory "Nash" mix.

**Found:**
1. **More matches help only when there are few cycles.** In a ladder world round robin picks a deserving winner about 7
   points more often than a random knockout (45% vs 38%). The gap shrinks as cycles grow and is **zero** in pure
   rock-paper-scissors: 28 matches buy nothing over 7. (On one measure round robin is even a hair worse there, by 0.2
   points: real, but too small to matter.)
2. **Surprise: our 8-player 3-round Swiss is secretly a random knockout.** The person who goes 3–0 had to win a random
   round-1 match, then beat another 1–0 player, then beat the other 2–0 player. That is exactly a random bracket. The other
   5 matches only decide the lower places. So in our simulations its winner statistics are identical to the knockout's.
3. **Seeding by ranking helps a bit with no cycles (+5 points) and stops helping in pure cycles,** because the ranking itself
   stops meaning much.

Picture: `outputs/fig/F5_formats_vs_kappa.pdf`.

**Question for you:** is the Swiss result worth a short paragraph in the report? It's simple to explain and a bit surprising.

💬 **Your thoughts:**
> Can epxlain the swiss result but thats not the main result/outcome from this; should discuss more on in hihgly-transitive (but with little intransvitiy) which method is better which should be used and stuff; and the same case arugment for the case when its highly intrasnitive with very little trsivitity

---

## Step 7: P4 tidy-up + pictures F0 and F1 (done ✅)

- **Cleaner example (for the report):** A is strongest, D weakest on average (43% average win rate). In the bracket
  {A vs C} | {B vs D}, C (A's nemesis) knocks A out 70% of the time, and D beats both B and C 60% of the time. So **D, the
  weakest, is the favourite at exactly 27%**. Picture: `outputs/fig/F1_p4_example.pdf`.
- **How much cycling does that take?** A lot. Even with 4 players we found nothing below κ ≈ 0.56 without resorting to
  near-certain matches. That fits E1, so the bottom player is protected unless cycles dominate.
- **F0** (`outputs/fig/F0_setup.pdf`) is the one-picture overview of the whole pipeline the professor asked for.

💬 **Your thoughts:**
> Okay this is pretty nice F1 image is good; I dont like your overview F)  - i feel it isnt very human appealing while an overview though faithful to the porject must also generaete interest and a better outlook fo things so work on F0


## Step 8: E5, does "best-of-3" make things fairer? (done ✅)

Surprisingly, **no, it makes the organiser more powerful when there are cycles.** Best-of-3 removes luck, so matchups
decide more. In a pure ladder that barely matters (+1.6 points of swing). In a rock-paper-scissors world it adds about
12 points (20 → 31). Picture: `outputs/fig/F6_bo3.pdf`.

💬 **Your thoughts:**
> I think this is nice research idea; kudos to u; and the plot is pretty good; Like i like this to be a bonus seciton right before or right after the conclusion ro results seciotn just sos th it would be like -  we present our exploration, observation and solidfy the problem throughout the report and this is an honest tried improvement in teh free time kinda thing

## Step 9: Section 1 draft

A first draft of report Section 1 (question, why it matters, key idea, findings, approach) is at the end of
`RESULTS.md`. Read it and tell me what doesn't sound like *your* project. That section carries the most marks, so it
should match how you'd explain the idea.

💬 **Your thoughts:**
> I've gone through the section 1 but i dont think very well intrducdes the motivation in human student to teach eprot matter; i think i shall give you more context below

> this is the final report for my course Learnign from Human Preferences; Where i was asked to take a paper presetn on it and work one xpriementations and submit a report later on; I had chosen this Blade_Chest Respresentation paper and had presented this; And this is my work to the report; I shall allos now quote the guidelines ive received: "Dear students, I want to clearly articulate the policy for the last 20 marks of this course, namely your project report.

Scope and effort. I expect about 15 hours of work per student. As a rough guide, spend a third of that time thinking and planning, a third doing the work, and a third writing and reflecting. You may go through that cycle a couple of times. Your project should revolve around one key idea. One well-chosen experiment or one carefully investigated theorem can make a great project. Spend a couple of days exploring ideas, then pick one and do it well.

On committing to a plan. Continuing on the above point. Please try to agree on a plan by 10 November if you haven’t already. I am purposely not putting a separate project proposal deadline, as you have endsems/placements coming up. In the first section of the report, explain what question you are exploring, why it is worth asking, and how you approach it. This first section will carry a substantial share of the 20 marks.

What you can do. You can do experimental or theoretical work, and either route can earn full marks. Feel free to go beyond your assigned paper when it helps you answer your question.

    Experiments. You might reproduce one result and then vary a key assumption, test a simpler baseline, or try a different dataset. Explain why you chose the experiment, what happened, and what you learned, even if the result was inconclusive.
    Theory. You might focus on one theorem and work through the proof step that makes it work. You could trace an idea to earlier papers and explain what the authors had to change, or examine why an assumption matters. For instance, can you construct a small example where the theorem fails when you drop that assumption? A theory project can earn full marks without code.
    Experiments inspired by theory. If your assigned paper is theoretical, you can still do an empirical project. If the theory explains something observed in practice, you could design a small experiment to see when that explanation holds up. If later work keeps the paper’s main idea but shows that a much simpler method works in practice, you could compare the two and investigate when the simpler method is enough.

Feel free to critique the paper. If you suspect a result is sensitive to a particular choice, or that a method is computationally expensive for what it delivers, investigate that. Show where the issue arises and explain what your evidence tells you.

You’re welcome to use AI creatively, for example to brainstorm experiments, generate synthetic data with specific properties, or help test an algorithm on different kinds of data. Check the outputs yourself and use what helps you answer your central question.

Report format. Use 11-point font. LaTeX is strongly preferred. Treat 15 pages of main text as a rough upper guideline. A shorter report is fine if it gives me enough detail to follow what you did and assess what you learned. For experimental work, include a figure or schematic that explains the setup. Make plots legible at the size they appear in the PDF, with readable labels and legends. Avoid grids of tiny plots and oversized tables. You may include GitHub links in the PDF, but there’s a good chance I won’t open them.

Convince me from the write-up itself that you did something cool."

See what i felt was laking was the transition from the blade cehst apper to this research lacking of human-like (we are 21yr old btech students) motvaiotn - section

## Step 10: the report (draft v1, 24 Nov)

- `report/main.tex` (+ `refs.bib`, `figures/`), compiled to `report/main.pdf`: 16 pages, of which 13 are main text,
  then references and a 2-page appendix.
- **Overleaf:** upload `report/report_overleaf.zip` (Overleaf → New Project → Upload Project). It compiles on its own.
  If figures change, run `report/make_overleaf_zip.sh` to refresh them and rebuild the zip.
- What your 💬 notes changed:
  - Section 1 now starts from *presenting the BC paper* and asks "so what?": pairwise models are used to make decisions
    (brackets, Chatbot Arena, RLHF reward models), and the paper's own StarCraft data come from knockout events.
  - E4 now gives format advice by regime: mostly-ladder (seeded KO gets ~70% of round robin's gain with 7 matches
    instead of 28) vs mostly-cycle (extra matches buy nothing; use a random draw). Swiss is a short side note.
  - Best-of-3 is a "Bonus" section just before the Conclusion.
  - F0 has been redrawn as a 4-step story with real mini-graphics.
  - Tennis: your "pre-selected elite players / rules average styles out" points are included, labelled as untested
    explanations.
  - Seeding is explained before E3; "rigging needs two ingredients" is in E1.
- **Please check or personalise:**
  - (a) Section 1.1 wording. It's written as "we presented the paper, then asked so what?"; add your own detail if
    you like.
  - (b) The red `[GitHub link to be added]` placeholder (`\repourl` at the top of main.tex).
  - (c) The "Use of AI tools" paragraph before the references. Edit it to say what you're comfortable with.
  - (d) The date on the title page (27 Nov).

💬 **Your thoughts:**
>
