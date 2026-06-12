"""Confidentiality model (SUCC-4, the defining feature).

Tiered access rides the central policy engine (capability `succession.read`,
division scoping via role org_subtrees). Two absolutes layered on top:
- the incumbent NEVER sees their own slate, whatever roles they inherit —
  checked against the position's CURRENT incumbent at read time, so role/
  assignment changes can never stale the rule (register row);
- every allowed view is read-audited at T3.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.audit import record_audit
from platform_core.policy.engine import (
    PolicyEngine,
    Resource,
    Subject,
    read_with_audit,
)
from succession.models import DiscoveryHold, KeyPosition, SlateEntry, TalentProfile


class SlateAccessError(PermissionError):
    pass


class PrivilegeError(PermissionError):
    pass


def read_slate(
    session: Session, policy: PolicyEngine, position: KeyPosition, *,
    subject: Subject, correlation_id: uuid.UUID | None = None,
) -> list[dict]:
    correlation_id = correlation_id or uuid.uuid4()

    # Absolute: own-slate self-block, evaluated against the CURRENT incumbent.
    if position.incumbent_id is not None and subject.subject_id == position.incumbent_id:
        record_audit(
            session, actor=subject.subject_id, action="deny",
            entity_ref=f"succession.key_position:{position.position_id}",
            after={"detail": "incumbent attempted to read own slate"},
            sensitivity_tier="T3", source_channel="succession",
            correlation_id=correlation_id,
        )
        raise SlateAccessError("succession records about your own position are not accessible")

    decision = policy.decide(
        subject, "succession.read",
        Resource(org_path=position.division_path),
    )
    if not decision.allow:
        raise SlateAccessError(f"denied: {'; '.join(decision.reasons)}")

    entries = session.scalars(select(SlateEntry).where(
        SlateEntry.position_id == position.position_id)).all()
    output = []
    for entry in entries:
        data = {c.name: getattr(entry, c.name) for c in SlateEntry.__table__.columns}
        filtered = read_with_audit(
            session, SlateEntry, data, decision, subject=subject,
            entity_ref=f"succession.slate_entry:{entry.entry_id}",
            source_channel="succession", correlation_id=correlation_id,
        )
        if filtered:
            output.append(filtered)
    return output


def aspirations_view(profile: TalentProfile, *, viewer_is_manager: bool) -> str | None:
    """Aspirations never reach the current manager without explicit consent."""
    if viewer_is_manager and not profile.aspirations_consent:
        return None
    return profile.aspirations


def open_discovery(session: Session, *, scope: str, requested_by: str,
                   counsel: str, artifact_refs: list[str]) -> DiscoveryHold:
    """Register row: legal discovery on talent decisions — artifacts gather
    under privilege; nothing releases without counsel approval."""
    hold = DiscoveryHold(scope=scope, requested_by=requested_by, counsel=counsel,
                         artifact_refs=artifact_refs)
    session.add(hold)
    session.flush()
    record_audit(
        session, actor=requested_by, action="insert",
        entity_ref=f"succession.discovery_hold:{hold.hold_id}",
        after={"scope": scope, "privileged": True},
        sensitivity_tier="T3", source_channel="succession",
        correlation_id=uuid.uuid4(),
    )
    return hold


def release_discovery(session: Session, hold: DiscoveryHold, *, actor: str,
                      counsel_approved: bool) -> DiscoveryHold:
    if not counsel_approved or actor != hold.counsel:
        raise PrivilegeError("release requires the named counsel's approval")
    hold.counsel_approved = True
    hold.released = True
    session.flush()
    record_audit(
        session, actor=actor, action="update",
        entity_ref=f"succession.discovery_hold:{hold.hold_id}",
        after={"released": True},
        sensitivity_tier="T3", source_channel="succession",
        correlation_id=uuid.uuid4(),
    )
    return hold
