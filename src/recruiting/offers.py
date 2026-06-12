"""Offer → hire (REC-4): comp-validated offers, negotiation versioning,
the zero-re-keying pre-hire contract, rescind and post-start escalation."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.audit import record_audit
from recruiting.models import Application, CandidateProfile, Offer, Requisition


class OfferStateError(ValueError):
    pass


def build_offer(
    session: Session, *, app: Application, req: Requisition,
    base_annual: Decimal, currency: str, start_date: date,
    components: dict | None = None, supersedes: Offer | None = None,
) -> Offer:
    """Comp validation against the req's inherited range — out-of-range routes
    to the comp team, it does not block drafting (§5)."""
    out_of_range = (
        req.range_min is not None and req.range_max is not None
        and not (req.range_min <= base_annual <= req.range_max)
    )
    offer = Offer(
        application_id=app.application_id,
        version=1 if supersedes is None else supersedes.version + 1,
        supersedes=supersedes.offer_id if supersedes else None,
        base_annual=base_annual, currency=currency, components=components,
        start_date=start_date, requires_comp_approval=out_of_range,
    )
    if supersedes is not None:
        supersedes.status = "rescinded"
        supersedes.rescind_reason = "superseded by negotiation version"
    session.add(offer)
    session.flush()
    return offer


def extend(session: Session, offer: Offer) -> Offer:
    if offer.status != "draft":
        raise OfferStateError(f"cannot extend from '{offer.status}'")
    offer.status = "extended"
    session.flush()
    return offer


def accept(session: Session, offer: Offer, *, app: Application,
           candidate: CandidateProfile, req: Requisition, on: date) -> dict:
    """Accept → the POST /hires contract (the most-tested interface in the
    suite): every field assembled from existing records, zero re-keying."""
    if offer.status != "extended":
        raise OfferStateError(f"cannot accept from '{offer.status}'")
    offer.status = "accepted"
    offer.decided_at = datetime.now(timezone.utc)
    app.status = "hired"
    req.status = "filled"
    session.flush()
    return {
        "candidate_id": str(candidate.candidate_id),
        "full_name": candidate.full_name,
        "email": candidate.email,
        "country": req.country,
        "position_id": req.position_id,
        "grade": req.grade,
        "base_annual": str(offer.base_annual),
        "currency": offer.currency,
        "components": offer.components or {},
        "start_date": offer.start_date.isoformat(),
        "requisition_id": str(req.requisition_id),
        "offer_id": str(offer.offer_id),
        "rehire": candidate.internal_worker_id is not None,
    }


def rescind_accepted(session: Session, offer: Offer, *, app: Application,
                     req: Requisition, actor: str, reason: str) -> Offer:
    """Register row: accepted-then-rescinded (counter-offer) — explicit state,
    reason, audit; the requisition reopens."""
    if offer.status != "accepted":
        raise OfferStateError(f"cannot rescind-accepted from '{offer.status}'")
    offer.status = "rescinded"
    offer.rescind_reason = reason
    offer.decided_at = datetime.now(timezone.utc)
    app.status = "withdrawn"
    app.disposition_code = "withdrew"
    req.status = "open"  # position reverts to open (failure-to-start pattern)
    session.flush()
    record_audit(
        session, actor=actor, action="update",
        entity_ref=f"recruiting.offer:{offer.offer_id}",
        after={"status": "rescinded", "reason": reason},
        sensitivity_tier="T2", source_channel="recruiting",
        correlation_id=uuid.uuid4(),
    )
    return offer


def adverse_finding_post_start(session: Session, *, worker_id: str,
                               finding: str, actor: str):
    """Register row: background adverse finding AFTER start — escalation
    runbook, not a recruiting disposition: ER-segregated case (T3 queue) via
    the one case system + audit. Employment decisions stay with humans."""
    from ess_mss.cases import open_case
    case = open_case(
        session, worker_id=worker_id, topic="investigation",
        description=f"post-start background adverse finding: {finding}",
    )
    record_audit(
        session, actor=actor, action="insert",
        entity_ref=f"service_delivery.case:{case.case_id}",
        after={"detail": "adverse-finding escalation runbook initiated"},
        sensitivity_tier="T3", source_channel="recruiting",
        correlation_id=uuid.uuid4(),
    )
    return case
