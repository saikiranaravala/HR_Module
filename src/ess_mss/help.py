"""AI-first help center (ESS-2, Specs/10 §5).

Copilot answers come from population-scoped retrieval through the AI Gateway
(the calling worker's own scope — Invariant #6). Low confidence, contradiction
flags, or gateway refusal degrade seamlessly into a case with the transcript
attached, so the employee never repeats themselves.
"""
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from ai_layer.gateway import AiGateway
from ai_layer.retrieval import CorpusDoc, retrieve
from ess_mss.cases import open_case
from ess_mss.models import Case


@dataclass
class HelpOutcome:
    kind: str                  # answered | case-created
    answer: str | None = None
    citations: list[str] | None = None
    as_of: date | None = None
    case: Case | None = None


def ask(
    session: Session, gateway: AiGateway, corpus: list[CorpusDoc], *,
    worker_id: str, country: str, population: str, topic: str, question: str,
    as_of: date,
) -> HelpOutcome:
    transcript = [{"role": "user", "text": question}]

    result = retrieve(corpus, country=country, population=population,
                      topic=topic, as_of=as_of)
    if not result.docs or result.route_to_case:
        case = open_case(session, worker_id=worker_id, topic=topic,
                         description=question, transcript=transcript)
        return HelpOutcome(kind="case-created", case=case)

    grounding = "\n---\n".join(d.body for d in result.docs)
    completion = gateway.complete(
        session, use_case="policy-qa-copilot", subject_id=worker_id,
        user_text=question, prompt_key="policy-answer",
        prompt_vars={"country": country, "population": population, "sources": grounding},
    )
    if completion.status != "ok":
        transcript.append({"role": "system", "text": f"gateway: {completion.refusal_reason}"})
        case = open_case(session, worker_id=worker_id, topic=topic,
                         description=question, transcript=transcript)
        return HelpOutcome(kind="case-created", case=case)

    return HelpOutcome(
        kind="answered",
        answer=completion.text,
        citations=[f"{d.doc_id} v{d.version}" for d in result.docs],
        as_of=as_of,
    )
