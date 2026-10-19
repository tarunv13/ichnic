"""Public-media video: enforcement reports on YouTube (seizures, arrests, court outcomes).

Many seizures in South and Southeast Asia, Africa and Latin America are reported first, or only, as
short videos by newsrooms and agencies. This collector finds them with free, open tools and feeds
them through the same event gate as news:

* yt-dlp (github.com/yt-dlp/yt-dlp, Unlicense): newest-first search results, metadata only, no download.
* youtube-transcript-api (github.com/jdepoix/youtube-transcript-api, MIT): the caption text, when the
  uploader or YouTube provides it, so the gate reads what is said and not only the title.
* YouTube channel RSS (`/feeds/videos.xml?channel_id=`): no key, works in CI, for channels listed in
  resources/sources.yaml under `video_channels`.

Records have kind "news_video" and outlet "youtube.com". The channel name stays in data/raw (private)
and is never published, the same rule as seller handles; case pages link to the video URL only.
"""
from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import quote_plus

from .. import lexicon
from ..schema import Record
from .base import get
from .social import youtube_search

# Enforcement queries per language: a species word and an event word, short enough for YouTube search.
EVENT_WORDS = {
    "en": ["seized", "arrested", "smuggling"], "hi": ["तस्कर गिरफ्तार", "बरामद"], "pt": ["apreensão", "tráfico"],
    "es": ["decomiso", "tráfico"], "fr": ["saisie", "trafic"], "vi": ["bắt giữ", "buôn lậu"],
    "id_ms": ["disita", "penyelundupan"], "th": ["จับกุม", "ตรวจยึด"],
}
# Video formats that are not reports of one event: documentaries, series episodes, explainers, compilations.
# Found in the first blind audit of video cases (2026-10-20, 41 of 50 real events).
GENRE = re.compile(r"\bepisode\b|\bep\.? ?\d|documentar|\bexplain|\bwhy (?:is|are|do|does)\b|\binside the\b|\bthe story of\b|"
                   r"\btop \d+\b|compilation|\bfaces extinction\b|\bwe(?:'|’)ve covered\b|\bfull (?:film|movie)\b", re.I)
_ID = re.compile(r"(?:v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})")


def video_id(url: str) -> str:
    m = _ID.search(url or "")
    return m.group(1) if m else ""


def queries(groups: list[str] | None = None, per_group: int = 1) -> list[tuple[str, str]]:
    """(language, query) pairs: the group's first terms in each language with an event word."""
    out = []
    for gid, g in lexicon.load()["groups"].items():
        if groups and gid not in groups:
            continue
        for lang, words in EVENT_WORDS.items():
            terms = [t for t in (g.get("terms") or {}).get(lang, []) if len(t) > 3][:per_group]
            for t in terms:
                out.append((lang, f"{t} {words[0]}"))
    return out


def transcript(vid: str, langs: tuple[str, ...] = ("en", "hi", "pt", "es", "fr", "vi", "id", "th")) -> str:
    """Caption text (first 1,500 characters), or "" when none is available or the tool is missing."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return ""
    try:
        api = YouTubeTranscriptApi()
        listing = api.list(vid)
        try:
            tr = listing.find_transcript(list(langs))
        except Exception:
            tr = next(iter(listing))
        return " ".join(s.text for s in tr.fetch())[:1500]
    except Exception:
        return ""


_DATE = re.compile(r'itemprop="(?:uploadDate|datePublished)" content="(\d{4}-\d{2}-\d{2})|"(?:uploadDate|publishDate)":"(\d{4}-\d{2}-\d{2})')


def upload_date(url: str) -> str:
    """ISO upload date from the video's public watch page (its schema.org uploadDate); yt-dlp as a fallback,
    which YouTube's bot check refuses after many requests (we never pass cookies). "" on failure."""
    import shutil, subprocess
    import requests, time
    try:      # not through base.get: watch pages are ~1 MB each and must not fill the HTTP cache
        time.sleep(1.5)
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (WildTrace research; +https://tarunv13.github.io/wildtrace/)",
                                       "Accept-Language": "en"}, timeout=40)
        m = _DATE.search(r.text) if r.ok else None
    except requests.RequestException:
        m = None
    if m:
        return m.group(1) or m.group(2)
    exe = shutil.which("yt-dlp")
    if not exe:
        return ""
    try:
        out = subprocess.run([exe, url, "--skip-download", "--no-warnings", "--print", "upload_date"], capture_output=True,
                             text=True, timeout=60, encoding="utf-8", errors="replace").stdout.strip()
        return f"{out[:4]}-{out[4:6]}-{out[6:8]}" if re.fullmatch(r"\d{8}", out) else ""
    except Exception:
        return ""


def as_news(rec: Record, with_transcript: bool = False) -> Record:
    rec.kind, rec.source, rec.outlet = "news_video", "youtube_news", "youtube.com"
    if with_transcript:
        rec.published = rec.published or upload_date(rec.url)
        cap = transcript(video_id(rec.url))
        if cap:
            rec.text = f"{rec.text} {cap}".strip()
            rec.extra = {**(rec.extra or {}), "transcript": True}
    return rec


def collect_videos(groups: list[str] | None = None, per_query: int = 15, transcripts: bool = True,
                   max_transcripts: int = 150) -> list[Record]:
    """Search YouTube for enforcement videos. Transcripts are fetched only for videos whose title or
    description already names a species group (to stay polite and fast)."""
    recs, seen, n_tr = [], set(), 0
    for lang, q in queries(groups):
        try:
            got = youtube_search(q, per_query)
        except RuntimeError as e:
            print(" ", e)
            return recs
        for r in got:
            vid = video_id(r.url)
            if not vid or vid in seen:
                continue
            seen.add(vid)
            wants = transcripts and n_tr < max_transcripts and bool(lexicon.species_groups(f"{r.title} {r.text}"))
            recs.append(as_news(r, with_transcript=wants))
            n_tr += wants
        print(f"  video {lang} '{q}': {len(got)}")
    return recs


def channel_feed(channel_id: str) -> list[Record]:
    """Latest videos of one channel from its public RSS feed (no key; CI-safe)."""
    r = get(f"https://www.youtube.com/feeds/videos.xml?channel_id={quote_plus(channel_id)}", delay=2, check_robots=False)
    if r is None or not r.ok:
        return []
    xml = r.text
    out = []
    for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        vid = re.search(r"<yt:videoId>(.*?)</yt:videoId>", entry)
        title = re.search(r"<title>(.*?)</title>", entry, re.S)
        pub = re.search(r"<published>(\d{4}-\d{2}-\d{2})", entry)
        desc = re.search(r"<media:description>(.*?)</media:description>", entry, re.S)
        if not vid:
            continue
        out.append(Record(url=f"https://www.youtube.com/watch?v={vid.group(1)}", title=(title.group(1) if title else "").strip(),
                          text=(desc.group(1) if desc else "").strip()[:1500], source="youtube_news", outlet="youtube.com",
                          published=pub.group(1) if pub else "", kind="news_video",
                          extra={"channel_id": channel_id, "seen": datetime.now().strftime("%Y-%m-%d")}))
    return out


def fill_dates(path, workers: int = 2) -> int:
    """Add upload dates to the undated videos in a raw file whose title or description names a species
    group. Search results carry no date, and the build counts a video only when it has one (an undated
    video could be years old). Returns the number of records dated."""
    import json
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path
    p = Path(path)
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    todo = [r for r in rows if not r.get("published") and lexicon.species_groups(f"{r.get('title', '')} {r.get('text', '')}")]
    with ThreadPoolExecutor(workers) as ex:
        for r, d in zip(todo, ex.map(lambda r: upload_date(r["url"]), todo)):
            r["published"] = d
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return sum(1 for r in todo if r["published"])
