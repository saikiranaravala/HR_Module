"""Requisition lifecycle (REC-1): position inheritance, pay-transparency
disclosure, cancellation with offers-out handling."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.audit import record_audit
from recruiting.models import Application, Offer, Requisition

CONFIG_DIR = Path(__file__).resolve().parent / "config"


def load_pay_transparency(path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "pay_transparency.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["jurisdictions"]


def create_requisition(
    session: Session, *, position: dict, headcount_type: str,
    jurisdiction: str | None = None, transparency: dict | None = None,
) -> Requisition:
    """Create from a vacant position — profile, grade, range are inherited,
    never re-keyed. Salary disclosure is auto-injected where the jurisdiction
    requires it (config, not code branches)."""
    transparency = transparency or load_pay_transparency()
    posting = position["title"]
    if jurisdiction and transparency.get(jurisdiction, {}).get("salary_disclosure"):
        posting += (f" | Salary range: {position['range_min']}–{position['range_max']} "
                    f"{position.get('currency', 'USD')} (disclosed per {jurisdiction})")
    req = Requisition(
        position_id=position["position_id"], title=position["title"],
        grade=position["grade"], country=position["country"],
        jurisdiction=jurisdiction, headcount_type=headcount_type,
        range_min=position.get("range_min"), range_max=position.get("range_max"),
        posting_text=posting,
    )
    session.add(req)
    session.flush()
    return req


def approval_chain(req: Requisition) -> list[str]:
    """Backfills approve lighter than net-new (§2 approval matrix)."""
    if req.headcount_type == "backfill":
        return ["hiring-manager"]
    return ["hiring-manager", "finance", "hr-leadership"]


def cancel_requisition(session: Session, req: Requisition, *, actor: str,
                       reason: str) -> dict:
    """Register row: cancelling a req with offers out never silently drops the
    candidates — extended offers are rescinded with care (explicit reason,
    audit), active applications are dispositioned req-cancelled."""
    apps = session.scalars(select(Application).where(
        Application.requisition_id == req.requisition_id)).all()
    offers_rescinded = 0
    apps_dispositioned = 0
    for app in apps:
        offers = session.scalars(select(Offer).where(
            Offer.application_id == app.application_id,
            Offer.status.in_(["extended", "accepted"]),
        )).all()
        for offer in offers:
            offer.status = "rescinded"
            offer.rescind_reason = f"requisition cancelled: {reason}"
            offer.decided_at = datetime.now(timezone.utc)
            offers_rescinded += 1
        if app.status == "active":
            app.status = "rejected"
            app.disposition_code = "req-cancelled"
            apps_dispositioned += 1
    req.status = "cancelled"
    session.flush()
    record_audit(
        session, actor=actor, action="update",
        entity_ref=f"recruiting.requisition:{req.requisition_id}",
        after={"status": "cancelled", "reason": reason,
               "offers_rescinded": offers_rescinded},
        sensitivity_tier="T1", source_channel="recruiting",
        correlation_id=uuid.uuid4(),
    )
    return {"offers_rescinded": offers_rescinded,
            "applications_dispositioned": apps_dispositioned}
