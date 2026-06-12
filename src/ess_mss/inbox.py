"""Unified MSS approval inbox (MSS-1, Specs/10 §4).

Aggregates pending workflow steps through rules_workflow's own query surface
(never the workflow schema directly), adds delegation records with scope and
duration limits, the no-bulk-on-comp guardrail, and the delegate self-approval
block (register row: blocked AND logged).
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ess_mss.models import Delegation
from platform_core.audit import record_audit
from rules_workflow.workflow import (
    OrgResolver,
    WorkflowInstance,
    act_on_step,
    pending_for_assignee,
)

MAX_DELEGATION_DAYS = 30
BULK_BARRED_DEFINITIONS = {"comp-change-approval"}  # no bulk approve on comp


class DelegationLimitError(ValueError):
    pass


class BulkNotAllowedError(PermissionError):
    pass


class SelfApprovalError(PermissionError):
    pass


def create_delegation(
    session: Session, *, delegator: str, delegate: str, scope_types: list[str],
    starts_on: date, ends_on: date,
) -> Delegation:
    if delegate == delegator:
        raise DelegationLimitError("cannot delegate to self")
    if (ends_on - starts_on).days > MAX_DELEGATION_DAYS:
        raise DelegationLimitError(f"delegation exceeds {MAX_DELEGATION_DAYS}-day limit")
    record = Delegation(delegator=delegator, delegate=delegate,
                        scope_types=scope_types, starts_on=starts_on, ends_on=ends_on)
    session.add(record)
    session.flush()
    record_audit(
        session, actor=delegator, action="insert",
        entity_ref=f"service_delivery.delegation:{record.delegation_id}",
        after={"delegate": delegate, "scope": scope_types,
               "starts_on": starts_on.isoformat(), "ends_on": ends_on.isoformat()},
        sensitivity_tier="T1", source_channel="ess-mss",
        correlation_id=uuid.uuid4(),
    )
    return record


def active_delegation_map(session: Session, on: date, *, approval_type: str | None = None) -> dict[str, str]:
    """delegator → delegate map for `rules_workflow.resolve_delegate`."""
    rows = session.scalars(select(Delegation).where(
        Delegation.revoked.is_(False),
        Delegation.starts_on <= on,
        Delegation.ends_on >= on,
    )).all()
    return {
        r.delegator: r.delegate
        for r in rows
        if approval_type is None or approval_type in (r.scope_types or [])
    }


def inbox(session: Session, approver: str, *, roles: tuple[str, ...] = (),
          definition_key: str | None = None):
    """All pending approvals for this approver (including their roles' queues,
    e.g. fallback-routed `role:hr-admin` items), oldest first, with context."""
    return pending_for_assignee(session, approver, roles=roles,
                                definition_key=definition_key)


def act_via_inbox(
    session: Session, instance: WorkflowInstance, definition: dict, *,
    actor: str, approve: bool, org: OrgResolver,
    delegations: dict[str, str] | None = None,
) -> WorkflowInstance:
    """Single-item action with the delegate self-approval block.

    The engine already blocks initiator == actor; this adds the register row:
    a delegated approver acting on an item whose SUBJECT is themselves is
    blocked and the attempt is audit-logged.
    """
    if actor == instance.subject_ref:
        record_audit(
            session, actor=actor, action="deny",
            entity_ref=f"workflow.workflow_instance:{instance.instance_id}",
            after={"detail": "delegate self-approval attempt blocked"},
            sensitivity_tier="T1", source_channel="ess-mss",
            correlation_id=instance.correlation_id,
        )
        raise SelfApprovalError("you are the subject of this item; routed to fallback approver")
    return act_on_step(session, instance, definition,
                       actor=actor, approve=approve, org=org, delegations=delegations)


def bulk_approve(
    session: Session, items: list[tuple[WorkflowInstance, dict]], *,
    actor: str, org: OrgResolver,
) -> list[uuid.UUID]:
    """Bulk approve with guardrails: comp items are never bulk-approvable."""
    barred = [inst for inst, _ in items if inst.definition_key in BULK_BARRED_DEFINITIONS]
    if barred:
        raise BulkNotAllowedError(
            "compensation approvals require individual review; bulk action refused"
        )
    done = []
    for instance, definition in items:
        act_via_inbox(session, instance, definition, actor=actor, approve=True, org=org)
        done.append(instance.instance_id)
    return done
