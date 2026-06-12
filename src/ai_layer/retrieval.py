"""Knowledge & retrieval service (Specs/14 §3) — hierarchical, vectorless-first.

The corpus is a tree: country → population → topic. Scoping is STRUCTURAL:
retrieval for a DE worker never traverses the US branch, so a US FMLA answer
to a DE worker is impossible by construction, not by similarity threshold.

Documents carry version + effective dates; tombstoned docs are excluded
immediately; contradictions (CBA vs handbook) return BOTH with a precedence
note and a case-routing flag — never silently resolved.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml

CORPUS_DIR = Path(__file__).resolve().parent / "config" / "corpus"

CHANGE_BANNER_WINDOW = timedelta(days=14)

# Source-kind precedence: a CBA outranks the handbook, statute outranks both.
PRECEDENCE = {"statute": 0, "cba": 1, "handbook": 2, "kb-article": 3}


@dataclass
class CorpusDoc:
    doc_id: str
    country: str
    population: str  # e.g. 'all', 'union-metal', 'salaried'
    topic: str
    kind: str        # statute|cba|handbook|kb-article
    version: int
    effective_date: date
    body: str
    tombstoned: bool = False


@dataclass
class RetrievalResult:
    docs: list[CorpusDoc] = field(default_factory=list)
    contradiction: bool = False
    precedence_note: str | None = None
    route_to_case: bool = False
    change_banner: str | None = None


def load_corpus(base_dir: Path = CORPUS_DIR) -> list[CorpusDoc]:
    docs = []
    for path in sorted(base_dir.glob("*.yaml")):
        for raw in yaml.safe_load(path.read_text(encoding="utf-8"))["documents"]:
            raw["effective_date"] = (
                raw["effective_date"] if isinstance(raw["effective_date"], date)
                else date.fromisoformat(str(raw["effective_date"]))
            )
            docs.append(CorpusDoc(**raw))
    return docs


def retrieve(
    corpus: list[CorpusDoc],
    *,
    country: str,
    population: str,
    topic: str,
    as_of: date,
) -> RetrievalResult:
    """Tree traversal: country and population filters are applied FIRST and are
    absolute — nothing outside the worker's branch is ever a candidate."""
    branch = [
        d for d in corpus
        if not d.tombstoned
        and d.country == country                       # structural scope
        and d.population in (population, "all")        # structural scope
        and d.topic == topic
        and d.effective_date <= as_of
    ]
    if not branch:
        return RetrievalResult()

    # Latest version per (kind, population) wins; pinned version is cited.
    latest: dict[tuple, CorpusDoc] = {}
    for doc in branch:
        key = (doc.kind, doc.population)
        if key not in latest or (doc.effective_date, doc.version) > (
            latest[key].effective_date, latest[key].version
        ):
            latest[key] = doc
    docs = sorted(latest.values(), key=lambda d: PRECEDENCE.get(d.kind, 9))

    result = RetrievalResult(docs=docs)

    kinds = {d.kind for d in docs}
    if "cba" in kinds and "handbook" in kinds:
        result.contradiction = True
        result.precedence_note = (
            "A collective agreement and the handbook both govern this topic; the "
            "collective agreement takes precedence where they differ. Both are shown."
        )
        result.route_to_case = True  # never resolved silently (register row)

    newest = max(docs, key=lambda d: d.effective_date)
    if as_of - newest.effective_date <= CHANGE_BANNER_WINDOW:
        result.change_banner = (
            f"This policy changed on {newest.effective_date.isoformat()} "
            f"(doc {newest.doc_id} v{newest.version}). Answers before that date may differ."
        )
    return result
