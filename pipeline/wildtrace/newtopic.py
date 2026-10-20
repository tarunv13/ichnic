"""Start a Ichnic-style evidence project on another topic, reusing the tested engine.

    wildtrace new-topic D:/GitHub/sandtrace --title "SandTrace" --group sand_mining="illegal sand mining,sand mafia"

The new project inherits every rule Ichnic learned from its blind audits (event verbs, topic words,
genre, statistics and rescue filters, masks, the ambiguous-word machinery, platforms, agencies) and
replaces only the species groups with the new topic's groups. Its data, labels and public output live
in the new folder; the engine is the installed `wildtrace` package, so a fix in one project reaches all.

Run it with two environment variables:

    WILDTRACE_ROOT=<project>  WILDTRACE_LEXICON=<project>/lexicon.yaml  python -m wildtrace.cli collect ...

`run.ps1` and `run.sh` in the new folder set them for you.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

from .config import RESOURCES

README = """# {title}

An evidence project built on the Ichnic engine ({engine}).

Topic groups: {groups}.

Run (sets WILDTRACE_ROOT and WILDTRACE_LEXICON for this folder):

    ./run.sh collect --gnews --countries ALL --gnews-window 30d --no-gdelt
    ./run.sh collect --video --no-gdelt         # YouTube enforcement videos, local only
    ./run.sh build
    ./run.sh accuracy sample --n 200 --seed <new>   # then label and score

Every public number must come from `web/data/`, every rule change goes in CURATION.md, and accuracy is
measured with a blind audit before anything is claimed.
"""


def parse_group(spec: str) -> tuple[str, dict]:
    """'sand_mining=illegal sand mining,sand mafia' or with languages 'id=en:a,b;hi:c'."""
    gid, _, rest = spec.partition("=")
    terms: dict[str, list[str]] = {}
    for part in rest.split(";"):
        lang, _, words = part.rpartition(":") if ":" in part else ("en", "", part)
        terms.setdefault(lang or "en", []).extend(w.strip() for w in words.split(",") if w.strip())
    return gid.strip(), {"label": gid.strip().replace("_", " ").capitalize(), "taxa": [], "cites": None,
                         "products": [], "terms": terms}


def create(folder: str | Path, title: str, groups: list[str]) -> Path:
    out = Path(folder)
    for d in ("data/raw", "data/interim", "data/labels", "data/private", "web/data", "models"):
        (out / d).mkdir(parents=True, exist_ok=True)
    base = yaml.safe_load((RESOURCES / "lexicon.yaml").read_text(encoding="utf-8"))
    new_groups = dict(parse_group(g) for g in groups)
    if not new_groups:
        raise SystemExit("give at least one --group id=term,term")
    # Keep the general catch-all so unspecified reports still have a home.
    new_groups["wildlife_general"] = {"label": f"{title} (unspecified)", "taxa": [], "cites": None, "products": [],
                                     "terms": {"en": [f"illegal {title.lower()}"]}}
    base["groups"] = new_groups
    # Ambiguous entries tied to wildlife groups do not apply; cue-level ones (crackdown, denuncia) do.
    base["ambiguous"] = [a for a in base.get("ambiguous", []) if not a.get("group")]
    (out / "lexicon.yaml").write_text(yaml.safe_dump(base, allow_unicode=True, sort_keys=False), encoding="utf-8")
    import wildtrace
    engine = Path(wildtrace.__file__).resolve().parent
    (out / "README.md").write_text(README.format(title=title, engine=engine, groups=", ".join(new_groups)), encoding="utf-8")
    (out / "CURATION.md").write_text(f"# {title} curation log\n\n| Date | Change | Evidence | Effect |\n| --- | --- | --- | --- |\n",
                                     encoding="utf-8")
    root = out.resolve().as_posix()
    (out / "run.sh").write_text(f'#!/usr/bin/env bash\nWILDTRACE_ROOT="{root}" WILDTRACE_LEXICON="{root}/lexicon.yaml" '
                                f'PYTHONIOENCODING=utf-8 python -m wildtrace.cli "$@"\n', encoding="utf-8")
    (out / "run.ps1").write_text(f'$env:WILDTRACE_ROOT="{root}"; $env:WILDTRACE_LEXICON="{root}/lexicon.yaml"; '
                                 f'$env:PYTHONIOENCODING="utf-8"; python -m wildtrace.cli @args\n', encoding="utf-8")
    os.chmod(out / "run.sh", 0o755)
    (out / ".gitignore").write_text("data/raw/\ndata/private/\ndata/interim/\ndata/labels/*.csv\nmodels/\n", encoding="utf-8")
    return out
