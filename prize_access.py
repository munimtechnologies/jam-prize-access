"""Prize access on itch.io game jams: how many open and upcoming jams offer cash prizes, and how many of those tie
the prize (eligibility, claiming or the winners' announcement) to the host's Discord server (Apache-2.0).
By MV2 of Munim, Inc. (mv2@munimtech.com), made with AI agents (Anthropic Claude).

    python prize_access.py --out /out [--delay 5.0] [--max-pages 20] [--raw-dir DIR]
    python prize_access.py --grade /out/summary.json

Reads only public pages that itch.io's robots.txt allows (/jams/in-progress, /jams/upcoming and each /jam/<slug>
main page), one request every --delay seconds, waiting and retrying on "429 Too Many Requests", with a User-Agent
that names MV2 and his email. Saves every page under out/raw/ so the coding can be redone offline (--raw-dir).
Only jam pages are read; no entry, author or user data is collected.

The page reader (to_text, sentences, jam_slugs, page_total, chrome_sentences) is copied unchanged from MV2's
agent_clauses.py reader 0.2 (munimtechnologies/game-jam-ai-rules), which read 590 jam pages on 2026-10-31.
The codes are defined in PREREGISTRATION-prize-access.md and frozen there (version 0.1).
"""
import argparse
import csv
import html
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request

VERSION = "0.1"
BASE = "https://itch.io"
UA = "MV2-Munim-prize-access/%s (MV2 of Munim, Inc.; mv2@munimtech.com)" % VERSION
LISTINGS = ["in-progress", "upcoming"]
NOT_JAMS = {"new", "created", "joined", "ending", "starting", "upcoming", "in-progress", "past", "featured"}
BLOCK_END = re.compile(r"(?i)<br\s*/?>|</(?:p|div|tr|li|h\d|table|section|dt|dd|td|th|title|nav|header|footer"
                       r"|aside|article|main|ul|ol|form|blockquote|pre)>")

# ---------- codes (frozen in the pre-registration, version 0.1) ----------
NUM = r"(\d{1,3}(?:[,.]\d{3})+|\d+)(?:[.,]\d{1,2})?\s*(k\b)?"
MONEY = re.compile(r"(?i)(?:US|CA|AU)?[$€£]\s?" + NUM
                   + r"|" + NUM + r"\s?(?:[$€£]|usd\b|eur\b|euros?\b|dollars?\b|gbp\b|pounds?\b|cad\b|aud\b)")
PRIZE_WORD = re.compile(r"(?i)\b(?:prizes?|win|wins|winners?|winning|awards?|place|placed|1st|2nd|3rd|first|second|"
                        r"third|rewards?|pool|gift ?cards?|cash|paypal|bount(?:y|ies)|grand)\b")
CASH_PHRASE = re.compile(r"(?i)\b(?:cash (?:prizes?|awards?|rewards?)|prize money|monetary (?:prizes?|awards?))\b")
CASH_NEG = re.compile(r"(?i)\b(?:no|not|without|zero)\b[^.!?]{0,25}\b(?:cash|money|monetary)\b"
                      r"|\bno (?:real )?prizes?\b|\bthere (?:are|is|will be) no (?:real )?(?:cash|money|monetary|prizes?)\b")
# Amounts that only describe the value of an in-kind prize (a subscription, voucher, key...) are not cash,
# unless the same sentence also says cash, PayPal, gift card or prize money.
INKIND = re.compile(r"(?i)\b(?:worth|value|valued|retail|subscriptions?|memberships?|vouchers?|coupons?|discounts?|"
                    r"credits?|licen[cs]es?|keys?|assets?|bundles?)\b")
MONEY_WORD = re.compile(r"(?i)\b(?:cash|paypal|gift ?cards?|prize money)\b")
DISCORD = re.compile(r"(?i)\bdiscord\b")
ROLE = re.compile(r"(?i)\broles?\b")
PRIZE_STRICT = re.compile(r"(?i)\b(?:prizes?|winners?|winning|rewards?|payouts?|eligib\w*|awards?|gift ?cards?|cash|"
                          r"money)\b")
GATE = re.compile(r"(?i)\b(?:must|required|requires?|needs? to|have to|has to|ticket|contact|dm|message\w*|"
                  r"reach out|level \d+|members only)\b|\bmembers? (?:of|on|in)\b"
                  r"|\bto (?:claim|receive|redeem|collect|be eligible)\b"
                  r"|\b(?:be|being) (?:a )?(?:part of|in|on|member of)\b")
SPONSOR = re.compile(r"(?i)\b(?:sponsor\w*|donat\w*)\b")
ANNOUNCE_WHAT = re.compile(r"(?i)\b(?:winners?|results?|prizes?|placements?|rankings?|awards?)\b")
ANNOUNCE = re.compile(r"(?i)\b(?:announc\w*|reveal\w*|posted|stream\w*|livestream\w*|declared)\b")
ENTRY_REQ = re.compile(r"(?i)\b(?:must|required|requires?|needs? to|have to|has to)\b")
ENTRY_OBJ = re.compile(r"(?i)\b(?:submit\w*|participa\w*|entrants?|eligib\w*|enter|join\w*|members?)\b")
ENTRY_NOT = re.compile(r"(?i)\bsupport\b|\bquestions?\b|\bbug reports?\b")
WIN_WORD = re.compile(r"(?i)\b(?:winners?|prizes?|awards?|rewards?)\b")


def amounts(s):
    """Money amounts (numbers only, any currency) named in a sentence."""
    out = []
    for m in MONEY.finditer(s):
        num, k = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        v = float(re.sub(r"[,.](?=\d{3}\b)", "", num).replace(",", "."))
        out.append(v * 1000 if k else v)
    return out


def is_cash(s):
    """A sentence that offers money: an amount of at least 1 next to a prize word (or on a short line, as in
    "1st place: $100" bullet lists), or a phrase such as "cash prizes"; not when it says there is no cash."""
    if CASH_NEG.search(s):
        return False
    if CASH_PHRASE.search(s):
        return True
    if any(v >= 1 for v in amounts(s)):
        if INKIND.search(s) and not MONEY_WORD.search(s):
            return False
        return bool(PRIZE_WORD.search(s)) or len(s.split()) <= 6
    return False


def discord_codes(s):
    """Codes for one sentence: any, claim, announce, entry, role (see the pre-registration)."""
    if not DISCORD.search(s):
        return {"any": False, "claim": False, "announce": False, "entry": False, "role": False}
    claim = bool(PRIZE_STRICT.search(s) and GATE.search(s) and not SPONSOR.search(s))
    announce = bool(ANNOUNCE_WHAT.search(s) and ANNOUNCE.search(s))
    entry = bool(ENTRY_REQ.search(s) and ENTRY_OBJ.search(s) and not ENTRY_NOT.search(s)) and not claim
    role = bool(ROLE.search(s) and WIN_WORD.search(s))
    return {"any": True, "claim": claim, "announce": announce, "entry": entry, "role": role}


def code_jam(sents, chrome):
    own = [s for s in sents if s not in chrome]
    cash = [s for s in own if is_cash(s)]
    codes = {k: [] for k in ("any", "claim", "announce", "entry", "role")}
    for s in own:
        for k, v in discord_codes(s).items():
            if v:
                codes[k].append(s)
    amts = [v for s in cash for v in amounts(s)]
    # "any" counts every line, chrome included: a bare "Discord" link line can repeat on many jam pages
    # (itch.io's own page furniture never names Discord).
    any_discord = any(DISCORD.search(s) for s in sents)
    return {"cash": bool(cash), "max_amount": max(amts) if amts else None,
            "discord_any": any_discord, "discord_claim": bool(codes["claim"]),
            "discord_announce": bool(codes["announce"]), "discord_entry": bool(codes["entry"]),
            "discord_role": bool(codes["role"]),
            "discord_dependent": bool(codes["claim"] or codes["announce"] or codes["entry"]),
            "mentions_email": any(re.search(r"(?i)\be-?mail\b|@[a-z0-9-]+\.[a-z]{2,}", s) for s in own),
            "cash_sentences": [s[:300] for s in cash][:6],
            "dependent_sentences": [s[:300] for k in ("claim", "announce", "entry") for s in codes[k]][:6]}


# ---------- page reader (copied unchanged from agent_clauses.py reader 0.2) ----------
def to_text(h):
    h = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", h)
    h = re.sub(r"\s+", " ", h)
    h = BLOCK_END.sub("\n", h)
    h = re.sub(r"<[^>]+>", " ", h)
    h = html.unescape(h)
    lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in h.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def sentences(text):
    out = []
    for ln in text.split("\n"):
        out += [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", ln) if s.strip()]
    return out


def jam_slugs(page_html):
    slugs = re.findall(r'href="(?:https://itch\.io)?/jam/([A-Za-z0-9_-]+)"', page_html)
    return [s for s in dict.fromkeys(slugs) if s not in NOT_JAMS]


def page_total(page_html):
    m = re.search(r"Page\s+\d+\s+of\s+(\d+)", to_text(page_html))
    if m:
        return int(m.group(1))
    nums = [int(n) for n in re.findall(r"[?&]page=(\d+)", page_html)]
    return max(nums) if nums else 1


def count_before(text, label):
    m = re.search(r"([\d,]+)\s+%s\b" % label, " ".join(text.split()))
    return int(m.group(1).replace(",", "")) if m else None


def parse_jam(page_html):
    text = to_text(page_html)
    m = re.search(r"(?is)<title>(.*?)</title>", page_html)
    title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else ""
    title = re.sub(r"\s*-\s*itch\.io$", "", title)
    return {"title": title, "joined": count_before(text, "Joined"),
            "entries": count_before(text, "(?:Entries|Submissions)"), "sentences": sentences(text)}


def chrome_sentences(all_sents, share):
    n = len(all_sents)
    seen = {}
    for sents in all_sents:
        for s in set(sents):
            seen[s] = seen.get(s, 0) + 1
    return {s for s, c in seen.items() if c >= 3 and c > share * n}


def fetch(url, tries=6):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 404:
                break
            wait = 5 * (i + 1)
            if e.code == 429:
                ra = e.headers.get("Retry-After") if e.headers else None
                wait = int(ra) if ra and ra.isdigit() else 30 * (i + 1)
            time.sleep(min(wait, 300))
        except Exception as e:
            last = e
            time.sleep(5 * (i + 1))
    raise last


# ---------- summary and grading ----------
def share(a, b):
    return round(a / b, 4) if b else None


def summarize(rows):
    n = len(rows)
    cash = [r for r in rows if r["cash"]]
    dep = [r for r in cash if r["discord_dependent"]]
    noncash = [r for r in rows if not r["cash"]]
    s = {"jams_read": n,
         "by_listing": {l: sum(1 for r in rows if r["listing"] == l) for l in LISTINGS},
         "discord_any": sum(r["discord_any"] for r in rows),
         "discord_any_share": share(sum(r["discord_any"] for r in rows), n),
         "cash": len(cash), "cash_share": share(len(cash), n),
         "cash_discord_any": sum(r["discord_any"] for r in cash),
         "cash_discord_any_share": share(sum(r["discord_any"] for r in cash), len(cash)),
         "cash_dependent": len(dep), "cash_dependent_share": share(len(dep), len(cash)),
         "cash_dependent_by_code": {k: sum(r["discord_" + k] for r in cash) for k in ("claim", "announce", "entry")},
         "cash_dependent_with_email": sum(r["mentions_email"] for r in dep),
         "noncash_dependent": sum(r["discord_dependent"] for r in noncash),
         "noncash_dependent_share": share(sum(r["discord_dependent"] for r in noncash), len(noncash)),
         "role_prize_jams": sum(r["discord_role"] for r in rows),
         "dependent_cash_slugs": [r["slug"] for r in dep]}
    return s


def grade(s):
    """Verdicts for D1-D5 exactly as pre-registered (D6 is graded by hand)."""
    g = {}
    g["D1"] = s["discord_any_share"] is not None and 0.40 <= s["discord_any_share"] <= 0.65
    g["D2"] = s["cash_share"] is not None and 0.06 <= s["cash_share"] <= 0.20
    g["D3"] = s["cash_dependent_share"] is not None and 0.10 <= s["cash_dependent_share"] <= 0.35
    g["D4"] = s["cash_discord_any_share"] is not None and s["cash_discord_any_share"] >= 0.60
    g["D5"] = s["role_prize_jams"] > s["cash_dependent"]
    g["core_gradable"] = s["jams_read"] >= 300 and s["cash"] >= 20
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--delay", type=float, default=5.0)
    ap.add_argument("--max-pages", type=int, default=20)
    ap.add_argument("--chrome-share", type=float, default=0.2)
    ap.add_argument("--raw-dir", default="", help="reuse pages saved by an earlier run (no network)")
    ap.add_argument("--grade", default="", help="print the verdicts for a summary.json")
    a = ap.parse_args()
    if a.grade:
        with open(a.grade, encoding="utf-8") as f:
            print(json.dumps(grade(json.load(f)), indent=1))
        return
    if not a.out:
        ap.error("--out is required")
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    problems = []

    def page(name, url):
        if a.raw_dir:
            p = os.path.join(a.raw_dir, name)
            if not os.path.exists(p):
                return ""
            with open(p, encoding="utf-8") as f:
                return f.read()
        h = fetch(url)
        with open(os.path.join(raw, name), "w", encoding="utf-8") as f:
            f.write(h)
        time.sleep(a.delay)
        return h

    listed = {}
    for listing in LISTINGS:
        first = page("list-%s-1.html" % listing, "%s/jams/%s" % (BASE, listing))
        total = min(page_total(first), a.max_pages)
        found = jam_slugs(first)
        for k in range(2, total + 1):
            try:
                found += jam_slugs(page("list-%s-%d.html" % (listing, k), "%s/jams/%s?page=%d" % (BASE, listing, k)))
            except Exception as e:
                problems.append("list %s %d: %r" % (listing, k, e))
        for s in found:
            listed.setdefault(s, listing)
        print("%s: %d pages, %d jams" % (listing, total, len(found)), flush=True)

    parsed = []
    for k, (slug, listing) in enumerate(listed.items()):
        try:
            h = page("jam-%s.html" % slug, "%s/jam/%s" % (BASE, slug))
        except Exception as e:
            problems.append("jam %s: %r" % (slug, e))
            continue
        if not h:
            problems.append("jam %s: empty" % slug)
            continue
        row = parse_jam(h)
        row.update({"slug": slug, "listing": listing})
        parsed.append(row)
        if k % 50 == 0:
            print("read %d/%d" % (k + 1, len(listed)), flush=True)

    chrome = chrome_sentences([r["sentences"] for r in parsed], a.chrome_share)
    rows = [{**{k: r[k] for k in ("slug", "title", "listing", "joined", "entries")}, **code_jam(r["sentences"], chrome)}
            for r in parsed]

    cols = ["slug", "listing", "joined", "entries", "cash", "max_amount", "discord_any", "discord_claim",
            "discord_announce", "discord_entry", "discord_role", "discord_dependent", "mentions_email"]
    with open(os.path.join(a.out, "jams.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])
    # Sentences for the hand check (D6). Not for publication: they can name hosts' Discord handles.
    with open(os.path.join(a.out, "check-sentences.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            if r["cash"]:
                f.write(json.dumps({"slug": r["slug"], "dependent": r["discord_dependent"],
                                    "cash_sentences": r["cash_sentences"],
                                    "dependent_sentences": r["dependent_sentences"]}, ensure_ascii=False) + "\n")
    cash_not_dep = sorted(r["slug"] for r in rows if r["cash"] and not r["discord_dependent"] and r["discord_any"])
    sample = random.Random(11).sample(cash_not_dep, min(20, len(cash_not_dep)))
    summary = summarize(rows)
    summary.update({"reader_version": VERSION, "listed": len(listed), "problems": problems,
                    "parsed_ok": len(rows) >= 0.95 * len(listed) > 0, "chrome_sentences": len(chrome),
                    "check_sample_not_dependent": sample})
    summary["grades"] = grade(summary)
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    sys.exit(0 if summary["parsed_ok"] else 1)


if __name__ == "__main__":
    main()
