# How accurate is Ichnic?

Accuracy is measured, not asserted. A reviewer draws a random sample of published cases
(`wildtrace accuracy sample`), reads each case's source headlines blind to how the pipeline scored it,
and records whether it is a genuine wildlife-trade enforcement event (a seizure, arrest, prosecution,
conviction, or a rescue linked to trade), whether its species are right, and why when it is not.
`wildtrace accuracy score` computes precision with a 95% Wilson interval and publishes it on the site
(`web/data/accuracy.json`, the "How accurate is Ichnic?" answer). Label files stay private because
they contain headlines; the counts and error classes are public.

## Current figure

**96.5% of published cases are genuine wildlife-trade enforcement events** (193 of 200; 95% interval
93.0% to 98.3%; audit 5, 29 September 2026). Species were right in 98.4% of the genuine cases. The previous
audit measured 95.5% (91.7% to 97.6%); the intervals overlap, so precision is holding steady rather than
proven higher.

The target is 98%. It is not reached yet, and Ichnic does not claim it. Precision by evidence grade in
the same audit, with 95% Wilson intervals: corroborated 97.6% (40/41; 87.4% to 99.6%), single report 95.1%
(135/142; 90.2% to 97.6%), official 94.1% (16/17; 73.0% to 99.0%). The intervals overlap widely, so the audit does
not show that one grade is more precise than another; 17 official cases are too few to say.

## History

| Audit | Pipeline | Sample | Genuine events | Main error classes found |
| --- | --- | --- | --- | --- |
| 1 | v1.10.0 | 200 | 163 (81.5%) | features and commentary, programmes and launches, statistics, topic words ("trafficking") taken as events, place and person names read as species |
| 2 | event-verb gate, genre and statistics rules, masks | 200, fresh | 189 (94.5%) | statistics in Portuguese and Spanish, reports, "arrêtés" (orders), a town named Araras (macaws) |
| 3 | second round of rules | 200, fresh | 192 (96.0%) | football ("Costa do Marfim"), bycatch rescues, tender notices, political statements, NGO complaints |
| 4 | third round of rules, leftmost-longest species matching | 200, fresh | 191 (95.5%) | a suburb named Rosewood, the Sandalwood film industry, legal decrees, opinion, research features |
| 5 | ambiguous-word rules tuned from 1,820 reviewed hits (below) | 200, fresh | 193 (96.5%) | meeting remarks, a research feature, administrative and fines policy, an awareness warning, a python-skin manuscript, one non-wildlife story |

Each fix is recorded with its evidence in [CURATION.md](CURATION.md). Every audit uses a new random seed,
so no figure is measured on cases the rules were tuned on.

## What the figure does not cover

- **Recall** (events Ichnic misses) is not measured by these audits. After the first round of rules,
  148 of the 163 genuine events in audit 1 were still published (90.8%); later verb additions recovered
  some of the rest. Recall against an independent list is measured separately (next section).
- **Coverage** follows the sources searched: newsrooms, government sites and the languages Ichnic reads.
- **Place** accuracy is not yet audited systematically; known errors come from towns that share a name with
  a place elsewhere.

## Recall against an independent list (19 October 2026)

Precision says how many published cases are real; it cannot say how many real events are missing. For
that we need a list made by someone else. The Illegal Wildlife Trafficking Global Observatory
(github.com/acarvalho-wcs/wildlife-trafficking-data) publishes 1,080 hand-validated cases with dates,
coordinates and source links. Its files carry no licence, so we use them only to measure, keep the rows
private, and report the aggregate here with attribution.

`wildtrace recall <cases.json>` counts a reference case as found when a Ichnic case names the same
species group, falls within 14 days of it, and lies within 300 km (or, for a case located only to a
country, in the same country), or carries the same source link. Only cases Ichnic could have found are
scored: 576 fell inside Ichnic's dates and named a species group it tracks.

**Ichnic found 150 of the 576 (26%; 95% interval 22.6% to 29.8%).** Recall is highest where the Google
News editions and languages are strongest (Brazil 58 of 118, India 31 of 51) and lowest where the cases come
from government press releases or from languages Ichnic does not read (Hong Kong 5 of 37, mainland China
0 of 30, Mexico 3 of 26). Of the 426 missed cases, 150 (35%) came from government sites such as Hong Kong
GovNews and Customs, PROFEPA, Brazilian state governments, US FWS, the Australian Border Force and French
customs. Google News indexes these sites poorly, so Ichnic now reads agency feeds directly
(`collect --agency`, daily) and has backfilled Hong Kong Government press releases from January 2024
(`collect --hk-archive`). The next gaps are Chinese-language sources and the Mexican, Peruvian and
Brazilian agency sites, which publish no feed.

**After the Hong Kong backfill (20 October 2026): 180 of 576 (31.2%; 95% interval 27.6% to 35.1%) on the
matching rule above. Corrected for chance matches (next paragraphs), recall is about 20% to 25%.** Hong Kong rose from
5 to 31 of 38. Two blind audits checked the new sources before publication. Hong Kong press releases: 23 of 30 real
events at first (weather notices matched the codebook word "black"); after the fixes in CURATION.md, 29 of 30 on a fresh
sample. Video-only cases: 41 of 50 and then 33 of 40 (82%), because video titles include documentaries, explainers,
series and toys. So a video now corroborates a case but cannot make one on its own; 95 video-only cases are held back.

**How much the figure depends on the matching rule (20 October 2026).** We re-ran the score under stricter and
looser rules. Recall moves a long way: 21.0% at 7 days and 150 km (121/576), 25.9% at 7 days and 300 km, 31.2% at
the default 14 days and 300 km, 37.2% at 14 days and 500 km, and 45.7% at 30 days and 500 km (263/576). A looser
rule finds more real matches, but it also pairs unrelated events: a district with frequent pangolin seizures will
produce a Ichnic case within a month of almost any reference case there.

To measure those chance pairings, we ran a placebo: every reference date moved by 60 or 90 days, backwards and
forwards, with link matches switched off, so that any "match" is a coincidence. Under the default rule 8.6% to 14.0%
of the shifted cases still matched (77/561, 79/565, 37/328, 25/290; forward shifts leave fewer cases inside
Ichnic's dates). Removing that chance rate, (observed − chance) / (1 − chance), gives about 20% to 25% under
the default rule. The strict rule gives a similar 16% to 19% (chance 3.0% to 5.9%), while the loosest rule spreads
to 18% to 29% because its chance rate is so high (23.8% to 33.7%). The honest summary is that Ichnic finds
about one in five of the events on this list. The headline 31.2% is kept above only because it is the figure the
command reports; read it with this correction.

The figure is a floor in one sense and generous in another. The reference list leans to Brazil and to
cases its curators found, so it is not a random sample of all events; and a match on species, date and
distance can pair two different events in the same district.

## Mexico's PROFEPA press releases (20 October 2026)

PROFEPA, Mexico's environmental enforcement agency, publishes no feed, so `collect --profepa` reads its press archive
(339 releases since January 2024). At first none passed the screen: the gate did not know Mexican official usage
("asegura" for a seizure, "vinculan a proceso" for a charge), and every dateline ("19 de octubre de 2026") looked like
a period summary. After those fixes, and after the extractor was limited to the release itself (the page sidebar had
placed every case in Zacatecas), a first look at 40 PROFEPA-only cases found 26 real events; a headline rule for
releases, relocations and animals loose in towns followed (CURATION.md). Those 40 were used to tune, so they do not count.

**A fresh blind sample of 50 PROFEPA-only cases found 30 real enforcement events (60%; 95% interval 46.2% to 72.4%).**
The rest were public campaigns (4), fishery equipment compliance (4), follow-ups such as a necropsy (3), logging
operations with no event (3), nesting or protection operations (3), and single cases of a road named for a tiger, a
checkpoint programme and wildlife conflict. Official releases use enforcement words far more densely than news, so
the news-tuned screen lets these through. Until that gap closes, a PROFEPA release corroborates a news case but
does not make one on its own, as with videos.

## How the audits are designed, and their limits

- **Sampling frame.** Each audit draws a simple random sample, without replacement, from all cases published on the
  day of the audit (`wildtrace accuracy sample --seed <new seed>`); the Wilson interval assumes exactly that design.
  Seeds are never reused, and a figure counts as independent only when its cases were neither judged before nor
  used to tune the rules.
- **One reviewer.** Every audit so far was judged by one person, the maintainer, who also writes the rules. The
  reviewer judges from the headlines without seeing the pipeline's score, but knows how the pipeline works. No
  second reviewer has yet judged the same cases, so agreement between reviewers (for example Cohen's kappa) is not
  known. A second, independent reviewer on a share of each audit is the next step, and the figure should be read as
  one careful reviewer's judgement until then.
- **What counts as an error.** A case is "not genuine" when its headlines describe no enforcement event on wildlife
  trade; the error class is recorded for each one, so the reasons can be checked and counted across audits.
- **Software.** Python 3.11, the `wildtrace` package at the version named in each CHANGELOG entry; the interval is
  computed in `pipeline/wildtrace/accuracy.py` (`wilson`).

## Ambiguous-word review (29 September 2026)

Every hit of an ambiguous word in the screened reports (1,820 hits, 1,625 unique headlines) was read and labelled
`should_count` y/n: does the word mean the traded species or an enforcement act in that headline? Under the old
rules 86.5% of decisions were right: accepted words were 94.4% right, but half of held words (162) were real trade
stories the rule missed, because context words such as *trade*, *smugglers*, *sold*, *luggage* and *heist* were not
recognised. After the changes logged in CURATION.md, 92.1% of decisions are right on the same labels (accepted
95.6%, misses 162 -> 73). That is measured on the labels the changes came from, so audit 5 above is the
independent check. Labels are kept across rebuilds (private, `data/labels/ambiguous_review.csv`).

## Tried and not adopted: a learned relevance filter (29 September 2026)

A classifier trained on the 800 audit labels (65 non-events) was tested leave-one-audit-out: train on three
audits, score the fourth. Two feature sets, multilingual sentence embeddings (paraphrase-multilingual-MiniLM-L12-v2)
and character n-grams, gave the same result. Dropping the lowest-scoring 2% of cases removed 7 of 65 non-events
but also 9 of 735 real events (pooled precision 91.9% -> 92.6%); dropping 6% removed 16 non-events and 32 real
events. A filter that loses a real case for every false one it removes is not an improvement, so it is not used.
The remaining errors are too varied for 65 examples to teach.

## Why the last few percent are hard

The remaining errors are a long tail: each fresh sample surfaces classes the last one did not (a suburb, a
film industry, a decree). Rules close each class but not the tail. Reaching 98% needs many more labelled non-events (several hundred) before a learned model can help, or
human validation of single-report cases before they are published; both are funded work. Each quarter
brings a fresh blind audit ([FUNDING.md](FUNDING.md) lists what pays for them).
