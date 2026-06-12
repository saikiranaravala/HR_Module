"""Case management (ESS-2, Specs/10 §5): smart routing, SLA, ER segregation,
note visibility, CSAT, and the honest deflection metric.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ess_mss.models import Case, CaseNote
from platform_core.catalog import Tier
from platform_core.policy.engine import PolicyEngine, Resource, Subject, read_with_audit
from rules_workflow.rules import evaluate, load_ruleset

DEFLECTION_WINDOW = timedelta(hours=72)

_routing_rules = None


def _ruleset():
    global _routing_rules
    if _routing_rules is None:
        _routing_rules = load_ruleset("case-routing")
    return _routing_rules


class ErCaseAccessError(PermissionError):
    pass


def open_case(
    session: Session, *, worker_id: str, topic: str, description: str,
    opened_at: datetime | None = None, transcript: list | None = None,
) -> Case:
    opened_at = opened_at or datetime.now(timezone.utc)
    routing = evaluate(_ruleset(), {"topic": topic}, opened_at.date()).output
    queue, priority, sla_hours = routing.split("|")  # e.g. "payroll|high|8"
    case = Case(
        worker_id=worker_id, topic=topic, queue=queue, priority=priority,
        status="open", description=description, transcript=transcript,
        opened_at=opened_at, sla_due_at=opened_at + timedelta(hours=int(sla_hours)),
    )
    session.add(case)
    session.flush()
    return case


def read_case(
    session: Session, policy: PolicyEngine, case: Case, *,
    subject: Subject, correlation_id: uuid.UUID | None = None,
) -> dict:
    """ER cases sit in a segregated tier: the central policy engine decides
    (capability `case.read-er`); allowed T3 reads are audit-logged. The same
    path serves API, reports, and AI — no local bypass (Invariant #3)."""
    capability = "case.read-er" if case.queue == "er" else "case.read"
    decision = policy.decide(subject, capability, Resource(owner_id=case.worker_id))
    if not decision.allow:
        raise ErCaseAccessError(f"denied: {'; '.join(decision.reasons)}")
    data = {c.name: getattr(case, c.name) for c in Case.__table__.columns}
    return read_with_audit(
        session, Case, data, decision, subject=subject,
        entity_ref=f"service_delivery.case:{case.case_id}",
        source_channel="ess-mss", correlation_id=correlation_id or uuid.uuid4(),
    )


def add_note(session: Session, case: Case, *, author: str, visibility: str, body: str) -> CaseNote:
    if visibility not in ("internal", "employee"):
        raise ValueError("visibility must be internal|employee")
    note = CaseNote(case_id=case.case_id, author=author, visibility=visibility,
                    body=body, created_at=datetime.now(timezone.utc))
    session.add(note)
    session.flush()
    return note


def notes_for_viewer(session: Session, case: Case, *, viewer: str) -> list[CaseNote]:
    """The worker on the case sees employee-visible notes only."""
    notes = session.scalars(select(CaseNote).where(CaseNote.case_id == case.case_id)
                            .order_by(CaseNote.created_at)).all()
    if viewer == case.worker_id:
        return [n for n in notes if n.visibility == "employee"]
    return notes


def close_case(session: Session, case: Case, *, satisfaction: int | None = None) -> Case:
    case.status = "closed"
    case.closed_at = datetime.now(timezone.utc)
    case.satisfaction = satisfaction
    session.flush()
    return case


def was_deflected(session: Session, *, worker_id: str, topic: str, answered_at: datetime) -> bool:
    """Honest deflection (§5 acceptance): answered AND no case on the same
    topic from the same worker within 72 hours."""
    follow_up = session.scalars(select(Case).where(
        Case.worker_id == worker_id,
        Case.topic == topic,
        Case.opened_at >= answered_at,
        Case.opened_at <= answered_at + DEFLECTION_WINDOW,
    )).first()
    return follow_up is None
