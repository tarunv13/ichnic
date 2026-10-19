"""Recall against an independent, hand-validated case list: how many of its events WildTrace also found.

    wildtrace recall data/raw/reference/wcs_observatory/cases.json

Precision (accuracy.py) says how many published cases are real. Recall needs a list made by someone
else. A reference case counts as found when a WildTrace case shares a species group, falls within
DAYS of it, and has a place within KM (or carries the same source URL). Only reference cases that
WildTrace could have found are scored: inside its date window and naming a species group it tracks.

The reference rows stay private (data/raw/reference, data/interim); only the aggregate is reported,
with attribution, because reference lists rarely carry an open licence.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from datetime import date
from pathlib import Path

from . import lexicon
from .accuracy import wilson
from .config import INTERIM, WEB_DATA

DAYS, KM = 14, 300
# Country names in the WCS Global Observatory (Portuguese) -> the ISO codes WildTrace uses.
PT_ISO = dict(p.split("=") for p in (
    "Brasil=BR;Brazil=BR;Hong Kong=HK;Índia=IN;México=MX;Argentina=AR;Indonésia=ID;China=CN;Sri Lanka=LK;Peru=PE;"
    "Rússia=RU;Estados Unidos=US;África do Sul=ZA;Colômbia=CO;Paquistão=PK;Nigéria=NG;Austrália=AU;Malásia=MY;"
    "Itália=IT;Equador=EC;Quênia=KE;Bolívia=BO;Bolivia=BO;Paraguai=PY;Filipinas=PH;Tailândia=TH;Zâmbia=ZM;Espanha=ES;"
    "República Democrática do Congo=CD;Chile=CL;Egito=EG;Uganda=UG;Costa Rica=CR;Países Baixos=NL;Armênia=AM;"
    "França=FR;Vietnã=VN;Madagascar=MG;Taiwan=TW;Bangladesh=BD;Uzbequistão=UZ;Suriname=SR;Panamá=PA;Polônia=PL;"
    "Arábia Saudita=SA;Omã=OM;Gabão=GA;Namíbia=NA;Camarões=CM;Costa do Marfim=CI;Reino Unido=GB;Eslováquia=SK;"
    "Canadá=CA;Laos=LA;Marrocos=MA;Guiné=GN;Singapura=SG;Moçambique=MZ;Togo=TG;Malawi=MW;Hungria=HU;Romênia=RO;"
    "Croácia=HR;Emirados Árabes Unidos=AE;Turquia=TR;Líbano=LB;Iraque=IQ;Sudão do Sul=SS;Palestina=PS;Japão=JP;"
    "Cazaquistão=KZ;Guiana Francesa=GF;República Dominicana=DO;Alemanha=DE;Honduras=HN;Guatemala=GT;"
    "República do Congo=CG;Libéria=LR;Ucrânia=UA;Tchéquia=CZ;República Tcheca=CZ;Nicarágua=NI;Israel=IL;Fiji=FJ;"
    "Kuwait=KW;Qatar=QA;Comores=KM;Argélia=DZ;Sudão=SD;Chipre=CY;Mongólia=MN;Irã=IR;Polinésia Francesa=PF;"
    "Quirguistão=KG;Geórgia=GE;Portugal=PT;Suíça=CH;Áustria=AT;Malta=MT;Macedônia do Norte=MK;Bulgária=BG;"
    "França (Reunião)=RE;Belize=BZ;Gana=GH;Uruguai=UY"
).split(";"))


def _km(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def _day(s) -> date | None:
    try:
        return date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


def load_reference(path: str | Path) -> list[dict]:
    """Normalise a reference file to {id, date, lat, lon, text, url}. Understands the WCS Global
    Observatory layout (cases.json with a `cases` list) and plain lists with the same keys."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = d.get("cases", d) if isinstance(d, dict) else d
    out = []
    for r in rows:
        if r.get("exclude_from_totals"):
            continue                           # aggregates and duplicates, flagged by the curators
        c = r.get("coordinates") or {}
        out.append({"id": r.get("id"), "date": _day(r.get("event_date") or r.get("publication_date") or r.get("date")),
                    "lat": c.get("lat", r.get("lat")), "lon": c.get("lon", r.get("lon")),
                    "cc": PT_ISO.get(r.get("country") or "", r.get("country") or "?"), "url": r.get("source_url") or r.get("url") or "",
                    "text": " ".join(str(r.get(k) or "") for k in ("title_en", "taxon_text", "card_text_en", "title"))})
    return out


def score(path: str | Path, label: str = "") -> dict:
    cases = json.loads((WEB_DATA / "cases.json").read_text(encoding="utf-8"))
    ours = []
    for c in cases:
        pts = [(p["lat"], p["lon"]) for p in c.get("places") or [] if isinstance(p, dict) and p.get("lat") is not None]
        if not pts and isinstance(c.get("place"), dict) and c["place"].get("lat") is not None:
            pts = [(c["place"]["lat"], c["place"]["lon"])]
        ours.append({"date": _day(c.get("date")), "groups": set(c.get("species") or []), "pts": pts,
                     "urls": {s.get("url") for s in c.get("sources") or []}, "countries": c.get("countries") or []})
    start = min(o["date"] for o in ours if o["date"])
    end = max(o["date"] for o in ours if o["date"])
    eligible, found, out_window, untracked, missed = [], [], 0, 0, []
    for r in load_reference(path):
        if not r["date"] or not (start <= r["date"] <= end):
            out_window += 1
            continue
        groups = {g for g in lexicon.species_groups(r["text"]) if g != lexicon.GENERAL}
        if not groups:
            untracked += 1
            continue
        eligible.append(r)
        hit = None
        for o in ours:
            if r["url"] and r["url"] in o["urls"]:
                hit = o
                break
            if not (o["date"] and abs((o["date"] - r["date"]).days) <= DAYS and groups & o["groups"]):
                continue
            if r["lat"] is not None and any(_km((r["lat"], r["lon"]), p) <= KM for p in o["pts"]):
                hit = o
                break
            if not o["pts"] and r["cc"] in o["countries"]:     # a country-level case: the same country is enough
                hit = o
                break
        r["groups"] = sorted(groups)
        (found if hit else missed).append(r)
    n, k = len(eligible), len(found)
    lo, hi = wilson(k, n) if n else (0, 0)
    by_cc = Counter(r["cc"] for r in eligible)
    hit_cc = Counter(r["cc"] for r in found)
    res = {"reference": label or str(path), "date": date.today().isoformat(), "window": [start.isoformat(), end.isoformat()],
           "eligible": n, "found": k, "recall": k / n if n else None, "ci": [lo, hi],
           "skipped": {"outside_window": out_window, "species_not_tracked": untracked},
           "by_country": {cc: [hit_cc[cc], m] for cc, m in by_cc.most_common()},
           "match": f"same species group, within {DAYS} days and {KM} km, or the same source URL"}
    INTERIM.mkdir(parents=True, exist_ok=True)
    (INTERIM / "recall_missed.jsonl").write_text(
        "\n".join(json.dumps({k2: (str(v) if k2 == "date" else v) for k2, v in r.items() if k2 != "text"}, ensure_ascii=False)
                  for r in missed), encoding="utf-8")
    return res
