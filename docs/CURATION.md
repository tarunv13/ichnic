# Curation log: every change to what Ichnic counts, and why

Ichnic decides what counts as a wildlife-trade report through its vocabulary (lexicon), its
screens and its sources. Those decisions shape every number on the site, so they are recorded
here, like code changes: what changed, the evidence for it, and what it did to the data. The idea
follows *Scrub Data* (Kay, Bar & Beery 2026, bioRxiv doi:10.64898/2026.09.19.752880): curation
steps should be explicit, provenance-tracked and re-runnable, not silent edits.

## Rule: no word is deleted for having a second meaning

A word that names a traded species or an enforcement act can also mean something else ("monitor",
"horn", "python", Thai "เหี้ย", "crackdown"). Deleting it loses real reports; matching it bare adds
noise. Such words go to the `ambiguous` section of `pipeline/wildtrace/resources/lexicon.yaml`
with the context they need nearby (another species, an enforcement or sale word, a wildlife phrase,
or a number). Every hit, accepted or held, is written to `data/labels/ambiguous_review.csv`
(private: it carries headlines) with a `verdict` column for review, and image evidence can confirm
a held hit (`wildtrace vision`: OCR plus BioCLIP species recognition). Rules change only from that
evidence.

Precedence: a word listed as ambiguous is always context-checked, even if a strong list also has it.
Plural terms match their singular ("parakeets" finds "parakeet") unless the singular is ambiguous.

## Log

| Date | Change | Evidence | Effect |
| --- | --- | --- | --- |
| 2026-09-29 | Trade context words for ambiguous terms (trade, smugglers, traffickers, poachers, sold, luggage, exports, heist, theft, seizures ...); masks (Tiger Reserve, leopard tortoise, Al-Monitor, Sandalwood film industry, Kasturi Kepala Hitam); चंदन needs wood or customs words | review of 1,820 ambiguous-word hits: 162 real trade stories held, person names and place names accepted | decisions right 86.5% -> 92.1% on the reviewed labels; audit 5 precision 96.5% |
| 2026-10-20 | PROFEPA extractor reads only the release body (`article-body`); headline rule `headline_release_cues` (release, relocation, animal loose in a town) unless the headline names a seizure, arrest or charge | the gob.mx sidebar placed every PROFEPA case in Zacatecas; 14 of 40 tuning cases were releases or conflict | PROFEPA events 183 -> 163 |
| 2026-10-20 | PROFEPA-only cases held back; PROFEPA corroborates news cases | fresh blind audit, 30 of 50 real (60%; ACCURACY.md) | see build log "PROFEPA-only cases held back" |
| 2026-10-20 | Spanish official verbs: "asegura" as an ambiguous seizure cue (needs a count, specimens, kilos or timber nearby; vetoed by "asegura que/la/el"); "rescata", "rescató"; "vinculan/vinculado a proceso" (charged) | PROFEPA (Mexico) releases: 0 of 339 passed the screen (218 "no event") | 138 of 339 pass; on 1,028 Spanish-language news records the new cues add 8 events, all real (SERFOR Peru and Profepa rescues of trafficked animals, one prosecution) |
| 2026-10-20 | Spanish datelines ("19 de octubre de 2026") removed from agency text before the statistics rule | "de 20" in every dated release triggered the statistics rule (95 of 339) | 3 left as statistics |
| 2026-10-20 | "psitácidos", "psitácido", "cotorras" added to parrots (es) | PROFEPA titles name parrots by family | parrot seizures in Mexico found |
| 2026-10-20 | Codebook common words "black", "cardinal", "canary" (birds), "vanilla" (orchids), "sheng" (medicinal plants), "mamba" (reptiles) moved from strong to ambiguous (need context) | Hong Kong "Black Rainstorm Warning" notices tagged as bird seizures (audit of Hong Kong cases, 7 of 30 non-events) | see the fresh audit in docs/ACCURACY.md |
| 2026-10-20 | Penalty boilerplate removed from agency releases ("liable to a maximum fine ... imprisonment") | Hong Kong Customs seizures labelled convictions | seizures keep their kind |
| 2026-10-20 | Video titles in documentary, episode, explainer or compilation formats are not counted (`video.GENRE`) | first audit of video-only cases: 41 of 50 real events | see the fresh audit |
| 2026-10-20 | Videos count only with an upload date | 241 of 258 video-only cases had no date | undated videos ignored |
| 2026-09-29 | Event gate: a case needs an event verb; topic words ("trafficking", "tráfico", "तस्करी") are context only | blind audit 1: 37 of 200 published cases were not events | precision 81.5% -> 94.5% (fresh audit 2) |
| 2026-09-29 | Genre, statistics and rescue rules; masks for non-species phrases (Tiger Strike Force, Costa do Marfim, arrêtés préfectoraux, Araras, human trafficking) | audits 1-3 error classes | precision 96.0% (audit 3), 95.5% (audit 4); see ACCURACY.md |
| 2026-09-29 | Leftmost-longest species matching; "चंदन" (also a first name), "denuncia", "बाघ", "बंदर", Thai "กบ" context-checked; codebook generic names never map to a narrower group | "Chandan Yadav arrested" stories; "red sandalwood" tagged sandalwood; "deer antlers" tagged musk deer | species right in 99.0% of genuine cases |
| 2026-09-29 | Daily run: English editions rotate over three days; job limit 180 min; unbuffered logs | daily run cancelled at 120 min (collection outgrew the limit) | every edition still covered every 3 days |
| 2026-09-29 | Google News `when:` months converted (12m -> 1y) | `when:12m` returned 0 results for Portuguese; `when:1y` returned 78 | one-year backfill re-run: +3,997 reports |
| 2026-09-29 | Online-crime searches in 8 languages | ECO-SOLVE comparison: online trade reaches enforcement in news | +582 reports, platforms per case |
| 2026-09-29 | Enforcement verbs added (busts, foils, raid, charged, दबोचा, बरामद, khởi tố, thu giữ, diringkus, diamankan, autuado, aseguran, démantelé) | real missed reports in the online backfill, e.g. "Indonesia busts online trade in wildlife skulls" (TRAFFIC) | cases 1,999 -> 2,133 |
| 2026-09-29 | "crackdown" moved to `ambiguous` (needs a number or a species) | it had pulled in policy announcements ("GIS mapping, CCTVs to boost wildlife crime crackdown") | announcements held, real operations with counts kept |
| 2026-09-29 | Thai: species and enforcement words, Thai news edition, Thai place matching without word spaces | 10,313 of ECO-SOLVE's 30,934 adverts are in Thai; Ichnic searched only English Thai news | Thailand cases 25 -> 48 |
| 2026-09-29 | Thai "เหี้ย" (water monitor; also a swear word) moved to `ambiguous` instead of deleted | owner review: deleting polysemous words loses real reports | counted with trade, enforcement, wildlife or number context |
| 2026-09-29 | Codebook common words (monitor, coral, turtle, deer, parrot ...) kept as `ambiguous` instead of dropped | same principle; PMC8579131 names | 17 groups gain context-checked terms |
| 2026-09-29 | Amphibians group (axolotls, dart frogs, salamanders, frog legs; "frog", "toad", Thai "กบ" ambiguous) | Vora et al. 2026, *Nature* (40% of traded amphibians wild-caught); ECO-SOLVE axolotl adverts; LEMIS amphibian imports | new group in cases, CITES, LEMIS, captive-bred claims |
| 2026-09-29 | Plural terms match singular | "parakeets" missed "parakeet species" (3 real cases lost when the codebook grew) | 0 reports lost against the previous build |
| 2026-09-28 | Trade-only taxon widening (`EXTRA_HIGHER`: Testudines, Varanus, Ursidae ...) | group labels were broader than their Indian taxa lists | CITES seizures 15,512 -> 24,719 |
