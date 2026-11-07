# Pre-registration: who can collect an itch.io jam's cash prize without Discord?

By MV2 of Munim, Inc. (mv2@munimtech.com). The study, code and this text were made with AI agents (Anthropic
Claude) working in his name. Text CC BY 4.0, code Apache-2.0.
Written and committed on 2026-11-07, **before** the data run reads any page. Marker: PREDICTIONS-FROZEN-2026-11-07.

## Why

Many itch.io game jams run their community on a Discord server. For most entrants that is just a convenience.
But when a jam ties its prizes to Discord (you must be on the server to be eligible, winners are announced or
paid there, or prizes are claimed through a Discord ticket), an entrant without a Discord account can win and
still not be able to collect. MV2 has no Discord account, and in October-November 2026 he met this in practice
(one jam's judged winners were announced only on Discord; two jam series take prize claims through Discord
tickets). We found no published count of how common this is: searches on 2026-11-07 turned up individual jam
pages only, no survey or dataset.

## What is read

- itch.io's public lists of in-progress and upcoming jams (up to 20 pages each) and the main page of every jam
  listed, once, on the day of the run. Nothing else: no entries, no user pages, no Discord.
- One request every 5 seconds; on "429 Too Many Requests" it waits (Retry-After, or 30 s x attempt) and retries.
- The page reader is MV2's agent_clauses.py reader 0.2 (game-jam-ai-rules), copied unchanged; sentences that
  appear on more than 20% of jam pages are treated as site furniture for the cash and prize codes.

## Codes (prize_access.py version 0.1, frozen with this file)

Per sentence, then per jam (a jam has a code if any of its sentences has it):
- **cash**: the sentence offers money: an amount of at least 1 in any currency next to a prize word (or on a
  short line of at most 6 words, as in "1st place: $100" lists), or a phrase such as "cash prize". Gift cards and
  PayPal count as cash. Not cash: a sentence that says there is no cash or no prize, and an amount that only gives
  the value of an in-kind prize (subscription, voucher, key, credits, licence) unless the sentence also says cash,
  PayPal, gift card or prize money.
- **discord_any**: any line of the page names Discord (a bare "Discord" link counts).
- **discord_claim**: a sentence names Discord, a prize word (prize, winner, reward, payout, eligible, award, gift
  card, cash, money) and a gate (must, required, need to, have to, ticket, contact, DM, message, reach out,
  "Level N", "members only", "member of", "to claim / receive / redeem / collect / be eligible", "be part of / in /
  on"), and is not about sponsoring or donating prizes.
- **discord_announce**: a sentence names Discord, winners/results/prizes/placements/rankings/awards, and
  announce/reveal/posted/stream/declared.
- **discord_entry**: a sentence names Discord and a requirement (must, required, need to, have to) to submit,
  participate, enter, join or be eligible (not support or question channels), and is not already a claim.
- **discord_role**: a sentence names Discord, a role, and winners/prizes/awards/rewards (a Discord role as prize).
- **Discord-dependent**: discord_claim or discord_announce or discord_entry.
The unit tests (test_prize_access.py) pin these codes on sentences copied from real jam pages.

## Predictions

Shares are of the jams actually read. **Core: D1, D2, D3.**

| | Prediction |
|---|---|
| D1 (core) | Between 40% and 65% of jams name Discord somewhere on their page. |
| D2 (core) | Between 6% and 20% of jams offer cash. |
| D3 (core) | Between 10% and 35% of cash jams are Discord-dependent. |
| D4 | At least 60% of cash jams name Discord somewhere on their page. |
| D5 | More jams offer a Discord role as a prize than there are Discord-dependent cash jams. |
| D6 (method) | A hand check of every Discord-dependent cash jam's coded sentences finds at least 80% of them correctly coded (the sentence really ties eligibility, the announcement or the claim to Discord). |

The core predictions are gradable only if at least 300 jams and at least 20 cash jams are read; otherwise we
report the counts and grade nothing. D1-D5 are graded by `prize_access.py --grade` exactly as written. For D6 we
also read the 20 cash jams the script samples (seed 11) among those that name Discord but are not coded
dependent, and report how many are missed (a recall check, not graded).

## What we already looked at (disclosed)

While designing the codes we searched the 590 jam pages MV2's agent-clauses run saved on 2026-10-31 for
sentences that name Discord with prize words, and read about 40 of them (the test sentences come from there).
A plain text search of those saved pages found the word "Discord" in 332 of 590 (56%), counting link
addresses; D1 is set around that. We did not count cash jams or Discord-dependent cash jams in that snapshot.

## Reporting

RESULTS-prize-access.md: every prediction with its verdict, the counts, the hand-check result, and what a
miss means. Published data: one row per jam (slug, listing, joined, entries and the codes). Not published: the
saved pages and the coded sentences, which can name hosts' Discord handles. Limits we expect: the codes are
keyword rules on English text (non-English pages will mostly code as no cash); a jam page can change after the
run; "dependent" does not mean exclusive (a page may also offer email), so we also count dependent cash jams
whose page mentions email.
