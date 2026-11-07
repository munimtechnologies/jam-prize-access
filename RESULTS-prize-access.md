# Results: who can collect an itch.io jam's cash prize without Discord?

By MV2 of Munim, Inc. (mv2@munimtech.com). The study, code and this text were made with AI agents (Anthropic
Claude) working in his name. Text and data CC BY 4.0, code Apache-2.0.

The pre-registration ([PREREGISTRATION-prize-access.md](PREREGISTRATION-prize-access.md), marker
PREDICTIONS-FROZEN-2026-11-07) was public on GitHub before the data run started: the run's first step waited
for it and found it at 09:19 UTC on 2026-11-07. The run then read itch.io's in-progress and upcoming jam lists
(12 pages) and the main page of each of the **565 jams** listed (318 in progress, 247 upcoming), one request
every 5 seconds, from 09:19 to 10:37 UTC. `prize_access.py` 0.1 ran unchanged, and its unit tests passed.

## Verdicts (graded exactly as written)

| | Prediction | Result | Verdict |
|---|---|---|---|
| D1 (core) | 40-65% of jams name Discord | 311 of 565 = **55.0%** | **held** |
| D2 (core) | 6-20% of jams offer cash | 89 of 565 = **15.8%** | **held** |
| D3 (core) | 10-35% of cash jams are Discord-dependent | 8 of 89 = **9.0%** | **missed** (just below) |
| D4 | at least 60% of cash jams name Discord | 45 of 89 = **50.6%** | **missed** |
| D5 | more jams give a Discord role as a prize than there are Discord-dependent cash jams | 18 vs 8 | **held** |
| D6 (method) | at least 80% of the dependent cash jams correctly coded, by hand | 6 of 8 jams (75%); 7 of 10 distinct sentences (70%) | **missed** |

Core: 2 of 3 held. All six: 3 of 6 held. The core was gradable (565 jams read, 89 coded cash; the minimums
were 300 and 20).

## The hand check found a bigger problem: half the "cash" jams are price tags

D6 asked us to read the coded sentences of every jam coded Discord-dependent. While doing that we read the cash
sentences of **all 89** cash jams, and the cash code is much worse than the dependence code:

- **42 of the 89 are false positives caused by game prices.** While a jam runs, its main page shows a grid of
  submitted games, and a paid game shows its price ("$3", "$7.99"). The reader keeps these short lines, and the
  cash rule accepts an amount on a line of at most 6 words (meant for "1st place: $100" lists). All 42 are
  in-progress jams. MV2's earlier agent-clause census met the same entry grid and planned for its next reader to
  skip it. This study's reader did not skip it.
- 3 more are not prizes: payment for an anthology contribution, travel funding (in kind), and a mini jam whose
  cash prizes belong to a different, annual jam.
- 2 are unclear: an amount from another challenge that the page mentions, and a worked example of a fundraiser
  split.
- **42 jams really offer cash** (counting PayPal and gift cards, as pre-registered).

Read by hand, 6 of the 8 jams coded Discord-dependent really are:

- 3 rounds of one biweekly series: you must be a member of its Discord to be eligible for prizes.
- 1 jam where submitters need a Discord server level.
- 1 jam where the winner must be in the Discord to receive the gift-card prize.
- 1 jam where every team member must register on its Discord.

The other two are wrong. One page offers email as an alternative way to claim. The other jam has no cash
prize of its own, and its Discord sentence is about voice-acting requests. The recall check covered the 20
sampled cash jams that name Discord but were not coded dependent. Eight of them are price-tag false positives.
Of the other 12, 11 are correctly not dependent. One is a partial miss: GMT Jam #1's devlog prize track can
only be entered through a Discord support ticket, but its game track does not need Discord.

**Corrected by hand (exploratory, after the run; not graded):** 42 of 565 jams (7.4%) offer real cash. 27 of
those 42 (64%) name Discord somewhere on the page. **6 of the 42 (14%), from 4 organizers, tie prize
eligibility or collection to Discord on the jam page itself**, plus 1 more on one of its tracks. 15 of the
42 never mention Discord. With these corrections D3 and D4 would both fall inside their predicted ranges, but
they were graded on the frozen code, and that code missed them.

## What this means for an entrant without Discord

On 7 November 2026, most itch.io jams with a cash prize did not tie it to Discord on their own page: about 6
in 7 could, as far as their page says, be entered and collected by email or through itch.io. Discord is very
common (55% of all jams name it) but is mostly a place for chat and announcements, not a gate. Two limits
point the same way, so 14% is a floor:

- We read only each jam's main page. Rules in linked documents, the community tab or Discord itself were not
  read.
- MV2 met two off-page cases himself in October-November 2026: winners announced only on Discord, and prize
  claims through a Discord ticket. One of those two jams shows nothing of it on its page.

The codes are English keyword rules, so non-English pages mostly code as "no cash". A page can change after it
was read.

## Data

- `data/jams.csv`: one row per jam (slug, listing, joined, entries, and the codes as the frozen script assigned
  them).
- `data/hand-check-cash.csv`: the 89 jams coded cash, with our hand verdicts on cash (yes / no-price-tags /
  no-other / unclear) and on Discord dependence (yes / no / partial), and a short note. The notes paraphrase
  the pages and name no people.
- Not published: the saved pages and the coded sentences, which can name hosts' Discord handles.

## Prior art

A web search on 7 November 2026, before writing this up, again found only individual jam pages and forum threads
(several offer email as a fallback to Discord) and no count or survey. As far as we know, this is the first
measured count of how often itch.io jam prizes depend on Discord.

## Next version

The reader for a re-run (`prize_access.py` 0.2) must drop the entry grid (`game_grid` cells and their
`price_tag`) before coding cash. A re-run would be pre-registered separately; this result stays graded as above.
