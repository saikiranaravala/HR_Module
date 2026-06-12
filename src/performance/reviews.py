"""Review document flow (PERF-2/PERF-4): AI-labeled drafts with edit-required,
deterministic bias lint, calibration lineage, release/acknowledge, amendments,
manager handoff, close-out. Hard rule (§5): AI never assigns or recommends a
rating — no rating surface exists anywhere in the AI path."""
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from ai_layer.gateway import AiGateway
from performance.models import CalibrationAdjustment, ReviewDoc

CONFIG_DIR = Path(__file__).resolve().parent / "config"


class EditRequiredError(ValueError):
    pass


class RationaleRequiredError(ValueError):
    pass


class StateError(ValueError):
    pass


def load_bias_terms(path: Path | None = None) -> list[dict]:
    path = path or CONFIG_DIR / "bias_lint.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["terms"]


def bias_lint(text: str, terms: list[dict] | None = None) -> list[dict]:
    """Deterministic pre-submit lint: gendered/age-coded/personality-vs-behavior
    language. Flags, never blocks — the manager decides (and owns) the words."""
    terms = terms if terms is not None else load_bias_terms()
    findings = []
    for term in terms:
        if re.search(rf"\b{re.escape(term['term'])}\b", text, re.IGNORECASE):
            findings.append({"term": term["term"], "category": term["category"]})
    return findings


def ai_draft_narrative(
    session: Session, gateway: AiGateway, doc: ReviewDoc, *,
    author_id: str, goal_summary: str, checkin_summary: str,
) -> ReviewDoc:
    """Draft assist: clearly labeled, fully editable, NEVER touches the rating
    (the function has no rating parameter; the prompt receives none)."""
    completion = gateway.complete(
        session, use_case="review-draft-assist", subject_id=author_id,
        user_text=f"Goals: {goal_summary}\nCheck-ins: {checkin_summary}",
        prompt_key="review-draft",
    )
    if completion.status == "ok":
        doc.narrative = f"[AI draft — review and edit]\n{completion.text}"
        doc.ai_drafted = True
        doc.ai_draft_edited = False
        session.flush()
    return doc


def edit_narrative(session: Session, doc: ReviewDoc, *, narrative: str) -> ReviewDoc:
    doc.narrative = narrative
    if doc.ai_drafted:
        doc.ai_draft_edited = True
    session.flush()
    return doc


def submit_manager_assessment(session: Session, doc: ReviewDoc, *,
                              rating: str | None) -> ReviewDoc:
    """Rating is a HUMAN entry (nullable for ratingless templates). An unedited
    AI draft cannot be submitted (edit-required-before-submit policy)."""
    if doc.ai_drafted and not doc.ai_draft_edited:
        raise EditRequiredError("AI-drafted narrative must be edited before submit")
    doc.rating = rating
    doc.state = "manager-done"
    session.flush()
    return doc


def calibrate(session: Session, doc: ReviewDoc, *, session_id: str, actor: str,
              new_rating: str | None, rationale: str | None) -> CalibrationAdjustment:
    """Every adjustment carries actor + mandatory rationale; pre/post live in
    an append-only lineage row (100%-audited metric, §1)."""
    if not rationale:
        raise RationaleRequiredError("calibration adjustments require a rationale")
    adjustment = CalibrationAdjustment(
        doc_id=doc.doc_id, session_id=session_id, before_rating=doc.rating,
        after_rating=new_rating, rationale=rationale, actor=actor,
        adjusted_at=datetime.now(timezone.utc),
    )
    session.add(adjustment)
    doc.rating = new_rating
    doc.state = "calibrated"
    session.flush()
    return adjustment


def record_skip_level_disagreement(session: Session, doc: ReviewDoc, *,
                                   skip_level_id: str, position: str) -> ReviewDoc:
    """Register row: skip-level disagreement is recorded on the document and
    must be resolved in calibration — it never silently overwrites the rating."""
    doc.skip_level_disagreement = f"{skip_level_id}: {position}"
    session.flush()
    return doc


def release(session: Session, doc: ReviewDoc) -> ReviewDoc:
    if doc.state != "calibrated":
        raise StateError(f"release requires calibrated state, got '{doc.state}'")
    if doc.skip_level_disagreement is not None:
        raise StateError("skip-level disagreement unresolved — calibration must "
                         "disposition it before release")
    doc.state = "released"
    session.flush()
    return doc


def resolve_skip_level(session: Session, doc: ReviewDoc, *, resolution: str,
                       session_id: str, actor: str) -> ReviewDoc:
    calibrate(session, doc, session_id=session_id, actor=actor,
              new_rating=doc.rating, rationale=f"skip-level resolution: {resolution}")
    doc.skip_level_disagreement = None
    session.flush()
    return doc


def acknowledge(session: Session, doc: ReviewDoc, *, comment: str | None = None) -> ReviewDoc:
    if doc.state != "released":
        raise StateError("only released docs can be acknowledged")
    doc.state = "acknowledged"
    doc.acknowledged_comment = comment
    session.flush()
    return doc


def amend_released(session: Session, doc: ReviewDoc, *, reason: str,
                   new_rating: str | None, new_narrative: str | None) -> ReviewDoc:
    """Register row: factual error found after release → DUAL RECORD. The
    released original is preserved (state 'amended'), a new doc references it."""
    if doc.state not in ("released", "acknowledged"):
        raise StateError("amendment applies to released documents only")
    amendment = ReviewDoc(
        cycle_id=doc.cycle_id, worker_id=doc.worker_id, manager_id=doc.manager_id,
        state="released", rating=new_rating if new_rating is not None else doc.rating,
        narrative=new_narrative if new_narrative is not None else doc.narrative,
        amends=doc.doc_id, amendment_reason=reason, restricted=doc.restricted,
    )
    doc.state = "amended"
    session.add(amendment)
    session.flush()
    return amendment


def handoff_manager(session: Session, doc: ReviewDoc, *, outgoing: str,
                    incoming: str) -> ReviewDoc:
    """Register row: manager change mid-cycle — outgoing's draft content stays,
    the incoming manager finalizes; both are logged on the document."""
    entry = {"outgoing": outgoing, "incoming": incoming,
             "at": datetime.now(timezone.utc).isoformat(),
             "draft_state_at_handoff": doc.state}
    doc.handoff_log = (doc.handoff_log or []) + [entry]
    doc.manager_id = incoming
    session.flush()
    return doc


def closeout_terminated(session: Session, doc: ReviewDoc, *, reason: str) -> ReviewDoc:
    """Register row: terminated before release — the document closes out
    explicitly (retained per schedule), it is neither released nor deleted."""
    if doc.state in ("released", "acknowledged"):
        raise StateError("released docs follow the released retention path")
    doc.state = "closed-out"
    doc.closeout_reason = reason
    session.flush()
    return doc
