"""Joiner-Mover-Leaver identity lifecycle (Specs/13 §4).

Meridian is the single source of truth for workforce identity. Provisioning
actions are computed from lifecycle facts and executed through a SCIM-shaped
client. Guarantees:
- idempotent: an action's identity is (worker, action_type, effective_ts);
  duplicate delivery has exactly one effect (register row)
- never dropped: IdP failures queue the action with an alert flag (register
  row: IdP outage during termination window) for replay
- leaver disable is the priority path (SLA ≤ 15 min from effective time)
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from sqlalchemy import Boolean, DateTime, Text, Uuid, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_JML_TAG = tag(
    category="identity-lifecycle", purpose="access-provisioning",
    lawful_basis="legitimate-interest", retention_class="ops-2y", tier=Tier.T1,
)

PRESTAGE_LEAD = timedelta(days=3)  # account pre-staged T-3 days before start


class ScimClient(Protocol):
    def create_account(self, worker_id: str, attributes: dict) -> None: ...
    def update_attributes(self, worker_id: str, attributes: dict) -> None: ...
    def disable_account(self, worker_id: str) -> None: ...


@register_model
class ProvisioningAction(Base):
    __tablename__ = "provisioning_action"
    __table_args__ = {"schema": "integration"}

    action_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_JML_TAG))
    action_type: Mapped[str] = mapped_column(Text, info=dict(_JML_TAG))  # prestage|enable|update|disable
    effective_ts = mapped_column(DateTime(timezone=True), info=dict(_JML_TAG))
    attributes = mapped_column(JSONB, nullable=True, info=dict(_JML_TAG))
    status: Mapped[str] = mapped_column(Text, info=dict(_JML_TAG))  # applied|queued
    alert_raised: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_JML_TAG))
    applied_at = mapped_column(DateTime(timezone=True), nullable=True, info=dict(RECORD_KEEPING_TAG))


@dataclass
class JmlResult:
    applied: bool
    duplicate: bool = False
    queued: bool = False


def _find_existing(session: Session, worker_id: str, action_type: str, effective_ts) -> ProvisioningAction | None:
    return session.scalars(
        select(ProvisioningAction).where(
            ProvisioningAction.worker_id == worker_id,
            ProvisioningAction.action_type == action_type,
            ProvisioningAction.effective_ts == effective_ts,
        )
    ).first()


def process_action(
    session: Session,
    scim: ScimClient,
    *,
    worker_id: str,
    action_type: str,
    effective_ts: datetime,
    attributes: dict | None = None,
) -> JmlResult:
    existing = _find_existing(session, worker_id, action_type, effective_ts)
    if existing is not None and existing.status == "applied":
        return JmlResult(applied=False, duplicate=True)  # idempotent: no second effect

    action = existing or ProvisioningAction(
        worker_id=worker_id, action_type=action_type,
        effective_ts=effective_ts, attributes=attributes, status="queued",
    )
    if existing is None:
        session.add(action)
        session.flush()

    try:
        if action_type in ("prestage", "enable"):
            scim.create_account(worker_id, attributes or {})
        elif action_type == "update":
            scim.update_attributes(worker_id, attributes or {})
        elif action_type == "disable":
            scim.disable_account(worker_id)
        else:
            raise ValueError(f"unknown action type: {action_type}")
    except ValueError:
        raise
    except Exception:  # noqa: BLE001 — IdP outage: queue with alert, never drop
        action.status = "queued"
        action.alert_raised = True  # disable actions page someone (15-min SLA)
        session.flush()
        return JmlResult(applied=False, queued=True)

    action.status = "applied"
    action.applied_at = datetime.now(timezone.utc)
    session.flush()
    return JmlResult(applied=True)


def replay_queued(session: Session, scim: ScimClient) -> int:
    """Recovery path after an IdP outage: re-attempt queued actions, oldest first,
    disables before everything else (the SLA path)."""
    queued = list(session.scalars(
        select(ProvisioningAction)
        .where(ProvisioningAction.status == "queued")
        .order_by(
            ProvisioningAction.action_type != "disable",  # false sorts first ⇒ disables lead
            ProvisioningAction.effective_ts,
        )
    ))
    applied = 0
    for action in queued:
        result = process_action(
            session, scim,
            worker_id=action.worker_id, action_type=action.action_type,
            effective_ts=action.effective_ts, attributes=action.attributes,
        )
        if result.applied:
            applied += 1
    return applied


def prestage_due(start_date: datetime, now: datetime) -> bool:
    """Accounts are pre-staged T-3 days before the worker's start."""
    return now >= start_date - PRESTAGE_LEAD
