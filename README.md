# jam-prize-access

Who can collect an itch.io game jam's cash prize without a Discord account? An open, pre-registered count by
MV2 of Munim, Inc. (mv2@munimtech.com). The study and code were made with AI agents (Anthropic Claude) working
in his name. Code Apache-2.0; text and data CC BY 4.0.

**Result (7 November 2026, 565 jams):** 55% of jams name Discord, but few tie prizes to it. Graded on the
frozen code, 3 of 6 predictions held (core 2 of 3). A hand check found that half of the jams coded "cash" were
false positives: prices of submitted games shown on the jam page. Corrected by hand, 42 jams offer real cash,
and 6 of them (14%, from 4 organizers) tie prize eligibility or collection to Discord on the page itself. See
[RESULTS-prize-access.md](RESULTS-prize-access.md).

- [PREREGISTRATION-prize-access.md](PREREGISTRATION-prize-access.md): the question, the codes and six
  predictions, committed on 2026-11-07 before any page was read.
- [RESULTS-prize-access.md](RESULTS-prize-access.md): every verdict, the hand check and its limits.
- `data/jams.csv`: one row per jam, with the codes as the frozen script assigned them.
- `data/hand-check-cash.csv`: hand verdicts for the 89 jams coded cash.
- `prize_access.py`: reads itch.io's in-progress and upcoming jam lists and each jam's main page (one request
  every 5 seconds, a User-Agent naming MV2 and his email), codes each jam for cash prizes and for prizes tied
  to Discord, and writes `jams.csv` and `summary.json`. `python prize_access.py --grade summary.json` prints the
  verdicts.
- `test_prize_access.py`: unit tests on sentences copied from real jam pages. Run `python -m unittest -v`.

No saved pages and no quoted sentences that could name people are published.

Licence: Apache-2.0 (see LICENSE).
