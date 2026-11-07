# jam-prize-access

Who can collect an itch.io game jam's cash prize without a Discord account? An open, pre-registered count by
MV2 of Munim, Inc. (mv2@munimtech.com). The study and code were made with AI agents (Anthropic Claude) working
in his name. Code Apache-2.0; text and data CC BY 4.0.

- [PREREGISTRATION-prize-access.md](PREREGISTRATION-prize-access.md): the question, the codes and six
  predictions, committed on 2026-11-07 before any page was read.
- `prize_access.py`: reads itch.io's in-progress and upcoming jam lists and each jam's main page (one request
  every 5 seconds, a User-Agent naming MV2 and his email), codes each jam for cash prizes and for prizes tied
  to Discord, and writes `jams.csv` and `summary.json`. `python prize_access.py --grade summary.json` prints the
  verdicts.
- `test_prize_access.py`: unit tests on sentences copied from real jam pages. Run `python -m unittest -v`.

Results will be added as RESULTS-prize-access.md, with one row per jam (no saved pages, no quoted sentences
that could name people).

Licence: Apache-2.0 (see LICENSE).
