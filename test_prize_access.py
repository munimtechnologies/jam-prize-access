"""Tests for prize_access.py (Apache-2.0). By MV2 of Munim, Inc., made with AI agents (Anthropic Claude).

Most sentences below are copied from real itch.io jam pages saved on 2026-10-31 by MV2's agent-clauses run
(one host's Discord handle is replaced by "the host"). Run: python -m unittest -v
"""
import unittest

import prize_access as pa


class Amounts(unittest.TestCase):
    def test_currencies_and_separators(self):
        self.assertEqual(pa.amounts("Prizes: $1,000 / €250 / 100 USD / $10.50 / $5k"), [1000, 250, 100, 10, 5000])

    def test_dot_thousands_and_suffix(self):
        self.assertEqual(pa.amounts("€1.000 for the winner, 10$ for second"), [1000, 10])

    def test_no_money(self):
        self.assertEqual(pa.amounts("The jam takes place in 2026 with 3 themes"), [])


class Cash(unittest.TestCase):
    def test_real_gdevelop_line(self):
        self.assertTrue(pa.is_cash("1st: €400 cash from CrazyGames, a 1-on-1 consultation with CrazyGames "
                                   "Developer Relations, and a $50 Fanatical voucher"))

    def test_real_gift_card(self):
        self.assertTrue(pa.is_cash("Winning Prize: 10$ Steam Gift Card* + Your game featured on Untitled Games Of Fame!!"))

    def test_real_cash_phrase(self):
        self.assertTrue(pa.is_cash("Their prize includes both awards (for example, a Discord role and a CraftPix key, "
                                   "plus 2 certificates) and the cash prize."))

    def test_inkind_value_is_not_cash(self):
        self.assertFalse(pa.is_cash("Prizes include Easel+ subscriptions (worth $60), a discord role, CraftPix "
                                    "memberships and Steam keys."))

    def test_real_negation(self):
        self.assertFalse(pa.is_cash("There are no cash prizes for game submissions in the Mini Jam, but the winning "
                                    "game earns a place in our Discord"))

    def test_bullets_and_pools(self):
        self.assertTrue(pa.is_cash("1st place: $500"))
        self.assertTrue(pa.is_cash("$200"))
        self.assertTrue(pa.is_cash("Total prize pool: $1,000"))

    def test_not_cash(self):
        self.assertFalse(pa.is_cash("Are there any prizes?"))
        self.assertFalse(pa.is_cash("Budget: $0 needed"))
        self.assertFalse(pa.is_cash("Use any engine you like, the asset store is fine"))

    def test_unrelated_no_does_not_negate(self):
        self.assertTrue(pa.is_cash("There is no theme restriction and the winner gets $50."))


class DiscordCodes(unittest.TestCase):
    def codes(self, s):
        return {k for k, v in pa.discord_codes(s).items() if v}

    def test_real_eligibility_gate(self):
        self.assertEqual(self.codes("You must be a part of the discord community to be eligible to win a prize."),
                         {"any", "claim"})
        self.assertEqual(self.codes("All team members MUST be a part of the discord to be eligible."), {"any", "claim"})

    def test_real_claim_message(self):
        self.assertEqual(self.codes("*Must be in the UGJ Discord to receive message with prize."), {"any", "claim"})

    def test_real_announce(self):
        self.assertEqual(self.codes("The prizes are announced on the discord server close to the start of the jam."),
                         {"any", "announce"})

    def test_real_entry_gate(self):
        self.assertEqual(self.codes("Submitters must be Level 1 or higher on our Discord server."), {"any", "entry"})

    def test_real_role_prize(self):
        self.assertEqual(self.codes('(The winners will receive the "WINNER" role on our discord server.)'),
                         {"any", "role"})
        self.assertEqual(self.codes("Their prize includes both awards (for example, a Discord role and a CraftPix key, "
                                    "plus 2 certificates) and the cash prize."), {"any", "role"})

    def test_real_not_prize_related(self):
        self.assertEqual(self.codes("Support tickets must be submitted in our Discord,"), {"any"})
        self.assertEqual(self.codes("(if you'd like to sponsor or donate prizes dm: the host on Discord)"), {"any"})
        self.assertEqual(self.codes("Claim an online ticket and you will be invited to our Discord, where you and your "
                                    "team will be able to watch our keynote"), {"any"})
        self.assertEqual(self.codes("There are no cash prizes for game submissions in the Mini Jam, but the winning "
                                    "game earns a place in our Discord"), {"any"})

    def test_no_discord(self):
        self.assertEqual(self.codes("Winners must email us to claim the prize."), set())


class JamLevel(unittest.TestCase):
    def test_code_jam(self):
        sents = ["Retro Summer", "Discord", "1st place: $100",
                 "You must be a part of the discord community to be eligible to win a prize.",
                 "Questions? E-mail the host."]
        r = pa.code_jam(sents, chrome={"Discord"})
        self.assertTrue(r["cash"])
        self.assertEqual(r["max_amount"], 100)
        self.assertTrue(r["discord_any"])  # counted even though the bare link line is chrome
        self.assertTrue(r["discord_claim"])
        self.assertTrue(r["discord_dependent"])
        self.assertFalse(r["discord_role"])
        self.assertTrue(r["mentions_email"])

    def test_code_jam_plain(self):
        r = pa.code_jam(["A cozy jam", "Have fun!"], chrome=set())
        self.assertFalse(r["cash"] or r["discord_any"] or r["discord_dependent"])
        self.assertIsNone(r["max_amount"])


def row(slug, cash, dep=False, any_=False, role=False, email=False, listing="upcoming"):
    return {"slug": slug, "listing": listing, "cash": cash, "discord_any": any_ or dep, "discord_dependent": dep,
            "discord_claim": dep, "discord_announce": False, "discord_entry": False, "discord_role": role,
            "mentions_email": email}


class SummaryAndGrade(unittest.TestCase):
    def test_summary(self):
        rows = [row("a", True, dep=True, email=True), row("b", True, any_=True), row("c", False, role=True, any_=True),
                row("d", False), row("e", False, dep=True, listing="in-progress")]
        s = pa.summarize(rows)
        self.assertEqual(s["jams_read"], 5)
        self.assertEqual(s["cash"], 2)
        self.assertEqual(s["cash_share"], 0.4)
        self.assertEqual(s["cash_dependent"], 1)
        self.assertEqual(s["cash_dependent_share"], 0.5)
        self.assertEqual(s["cash_discord_any_share"], 1.0)
        self.assertEqual(s["cash_dependent_with_email"], 1)
        self.assertEqual(s["noncash_dependent"], 1)
        self.assertEqual(s["role_prize_jams"], 1)
        self.assertEqual(s["dependent_cash_slugs"], ["a"])
        self.assertEqual(s["by_listing"], {"in-progress": 1, "upcoming": 4})

    def test_grade_thresholds(self):
        s = {"discord_any_share": 0.40, "cash_share": 0.20, "cash_dependent_share": 0.35,
             "cash_discord_any_share": 0.60, "role_prize_jams": 9, "cash_dependent": 8, "jams_read": 300, "cash": 20}
        self.assertEqual(pa.grade(s), {"D1": True, "D2": True, "D3": True, "D4": True, "D5": True,
                                       "core_gradable": True})
        s.update({"discord_any_share": 0.66, "cash_share": 0.05, "cash_dependent_share": 0.09,
                  "cash_discord_any_share": 0.59, "role_prize_jams": 8, "jams_read": 299})
        self.assertEqual(pa.grade(s), {"D1": False, "D2": False, "D3": False, "D4": False, "D5": False,
                                       "core_gradable": False})


class Reader(unittest.TestCase):
    def test_to_text_and_sentences(self):
        t = pa.to_text("<title>X - itch.io</title><div><p>Rule one. Rule two!</p><p>Join our <a>Discord</a></p></div>")
        self.assertEqual(pa.sentences(t), ["X - itch.io", "Rule one.", "Rule two!", "Join our Discord"])

    def test_jam_slugs(self):
        h = '<a href="/jam/abc-1">a</a><a href="https://itch.io/jam/abc-1">b</a><a href="/jam/upcoming">c</a>' \
            '<a href="/jam/zz_2">d</a>'
        self.assertEqual(pa.jam_slugs(h), ["abc-1", "zz_2"])

    def test_chrome(self):
        pages = [["Discord", "x%d" % i] for i in range(10)]
        self.assertEqual(pa.chrome_sentences(pages, 0.2), {"Discord"})


if __name__ == "__main__":
    unittest.main()
