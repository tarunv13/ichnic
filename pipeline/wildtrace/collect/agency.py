"""Official press releases read straight from the agencies, not through Google News.

The first recall check (`wildtrace recall`, against the WCS Global Observatory's validated cases,
2026-10-19) found that 35% of the events WildTrace missed were government press releases: Hong Kong
Customs, PROFEPA, Brazilian state governments, US FWS, Australian Border Force, French customs. Google
News indexes these sites poorly, so the `site:` queries in feeds.collect_official rarely find them.

* AGENCY_FEEDS: the agencies' own RSS (no key; CI-safe), read every day. Found and health-checked with
  Agent Reach's rss channel (github.com/Panniantong/Agent-Reach, MIT). Entries are kept only when the
  lexicon finds a species group or the title names protected species, then pass the same event gate.
* collect_hk_archive: Hong Kong GovNews keeps 100 items in its feed (about a day), so history comes from
  its public daily index pages (robots.txt allows them), opening a release only when its title is a
  candidate. Two seconds between requests.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from html import unescape

from .. import lexicon
from ..schema import Record
from .base import get
from .feeds import parse

# (feed URL, country, outlet). Feeds that do not exist (checked 2026-10-19): customs.gov.hk, fws.gov,
# gob.mx/profepa, abf.gov.au, news.navy.lk. Their releases are still searched via collect_official.
AGENCY_FEEDS = [
    ("https://www.info.gov.hk/gia/rss/general_en.xml", "HK", "info.gov.hk"),
    ("https://www.douane.gouv.fr/rss.xml", "FR", "douane.gouv.fr"),
    ("https://www.justice.gov/news/rss?type=press_release", "US", "justice.gov"),
]
# Titles that announce a wildlife case without naming the species ("suspected scheduled endangered species").
PROTECTED = re.compile(r"endangered species|protected species|wildlife|espèces? protégées?|cites|"
                       r"especies? (?:protegidas?|en riesgo|silvestres?)|vida silvestre", re.I)


def _candidate(text: str) -> bool:
    return bool(lexicon.species_groups(text)) or bool(PROTECTED.search(text))


def collect_agency_feeds() -> list[Record]:
    recs = []
    for url, cc, outlet in AGENCY_FEEDS:
        r = get(url, delay=2, check_robots=False, cache_hours=6)
        got = parse(r.content, "agency_rss", cc, "official") if r is not None and r.ok else []
        keep = [g for g in got if _candidate(g.title) or PROTECTED.search(g.text[:400])]
        for g in keep:
            g.outlet = outlet
        print(f"  agency {outlet}: {len(keep)} of {len(got)}")
        recs += keep
    return recs


_LINK = re.compile(r'href="(/gia/general/(\d{6})/(\d{2})/P\d+\.htm)"[^>]*>(.*?)</a>', re.S)


# The penalty paragraph every Customs release ends with ("liable to a maximum fine ... and imprisonment") reads as
# a conviction to the event gate; it describes the law, not this case, so it is removed.
_BOILER = re.compile(r"[^.]*(?:liable to|maximum (?:fine|penalty)|24-hour hotline|hotline 182 8080|report any suspected)[^.]*\.", re.I)


# A release's dateline ("19 de octubre de 2026") is not a period summary: drop it before the statistics rule reads "de 20".
_DATELINE = re.compile(r"\b\d{1,2} de (?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre) de 20\d\d\b", re.I)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", _DATELINE.sub(" ", _BOILER.sub(" ", text or ""))).strip()


def _text(html: str) -> str:
    body = re.search(r'<span id="pressrelease"[^>]*>(.*?)</span>', html, re.S) or re.search(r"<body.*?>(.*)</body>", html, re.S)
    t = re.sub(r"<[^>]+>", " ", body.group(1) if body else html)
    return clean(unescape(t))[:1500]


def collect_hk_archive(since: str = "2024-01-01", until: str | None = None) -> list[Record]:
    """Hong Kong Government press releases from `since`, day by day; a release is opened only when its
    title names a species group or protected species."""
    d, end, recs = date.fromisoformat(since), date.fromisoformat(until) if until else date.today(), []
    while d <= end:
        idx = get(f"https://www.info.gov.hk/gia/general/{d:%Y%m}/{d:%d}.htm", delay=2, cache_hours=24 * 365)
        if idx is not None and idx.ok:
            for path, _, _, title in _LINK.findall(idx.text):
                title = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", title))).strip()
                if not _candidate(title):
                    continue
                url = "https://www.info.gov.hk" + path
                page = get(url, delay=2, cache_hours=24 * 365)
                recs.append(Record(url=url, title=title, text=_text(page.text) if page is not None and page.ok else "",
                                   source="agency_hk_archive", outlet="info.gov.hk", published=d.isoformat(), lang="en",
                                   country_hint="HK", kind="official"))
        if d.day == 1:
            print(f"  HK GovNews {d:%Y-%m}: {len(recs)} so far")
        d += timedelta(days=1)
    return recs


# PROFEPA (Mexico's environmental enforcement agency) publishes no feed; its press archive is a paged list.
_PROFEPA = re.compile(r'<time datetime=\\"(\d{4}-\d{2}-\d{2}).*?<h2>(.*?)<\\/h2>.*?href=\\"(/profepa/prensa/[^"\\]+)', re.S)


def _profepa_text(html: str) -> str:
    """The release itself: gob.mx pages carry a long sidebar (other states' offices, campaigns) that would
    otherwise place every case in Zacatecas and lend it trade words it does not have."""
    i = html.find('class="article-body"')
    if i < 0:
        return ""
    body = html[i:html.find("</div>", i)]
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", body.split(">", 1)[-1]))).strip()[:3000]


def collect_profepa(since: str = "2024-01-01", max_pages: int = 400) -> list[Record]:
    """PROFEPA press releases back to `since`, page by page; a release is opened only when its title names a
    species group or protected species."""
    recs, stop = [], date.fromisoformat(since)
    for n in range(1, max_pages + 1):
        idx = get(f"https://www.gob.mx/profepa/archivo/prensa?idiom=es&page={n}", delay=2, cache_hours=24)
        rows = _PROFEPA.findall(idx.text) if idx is not None and idx.ok else []
        if not rows:
            break
        for day, title, path in rows:
            title = re.sub(r"\s+", " ", unescape(title)).strip()
            if day < since or not _candidate(title):
                continue
            url = "https://www.gob.mx" + path.split("?")[0]
            page = get(url, delay=2, cache_hours=24 * 365)
            recs.append(Record(url=url, title=title, text=_profepa_text(page.text) if page is not None and page.ok else "",
                               source="agency_profepa", outlet="gob.mx/profepa", published=day, lang="es",
                               country_hint="MX", kind="official"))
        if min(r[0] for r in rows) < since:
            break
        if n % 10 == 0:
            print(f"  PROFEPA page {n} ({rows[-1][0]}): {len(recs)} so far")
    return recs
