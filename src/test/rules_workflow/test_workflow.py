"""Workflow engine tests (Specs/12 §2) including register rows:
chain exhaustion, circular delegation, finish-on-old version migration."""
import pytest
from sqlalchemy import select

from platform_core.audit import AuditEvent
from rules_workflow.workflow import (
    CircularDelegationError,
    act_on_step,
    load_definition,
    pending_step,
    resolve_approver,
    resolve_delegate,
    start_instance,
)

V1 = load_definition("job-change-approval", version=1)
V2 = load_definition("job-change-approval", version=2)


def test_happy_path_single_approval(session, org):
    instance = start_instance(
        session, V1, subject_worker="w1", initiator="hr-user-1", org=org
    )
    step = pending_step(session, instance)
    assert step.resolved_assignee == "mgr1"
    assert "levels-up:1" in step.resolution_reason  # explain-routing populated

    act_on_step(session, instance, V1, actor="mgr1", approve=True, org=org)
    session.commit()
    assert instance.status == "completed"  # notification auto-completes


def test_rejection_halts_instance(session, org):
    instance = start_instance(session, V1, subject_worker="w1", initiator="hr-user-1", org=org)
    act_on_step(session, instance, V1, actor="mgr1", approve=False, org=org)
    assert instance.status == "rejected"


def test_self_approval_blocked_at_engine_level(session, org):
    # Initiator IS the manager: routing must skip them, landing on dir1.
    instance = start_instance(session, V1, subject_worker="w1", initiator="mgr1", org=org)
    step = pending_step(session, instance)
    assert step.resolved_assignee == "dir1"
    assert "self-approval blocked" in step.resolution_reason

    # And even a correctly-assigned actor who is the initiator is refused.
    with pytest.raises(PermissionError, match="self-approval"):
        act_on_step(session, instance, V1, actor="mgr1", approve=True, org=org)


def test_PLAT_approver_chain_exhaustion_fallback(session, org):
    """Register row: top-of-tree transactions route to the designated fallback role."""
    instance = start_instance(session, V1, subject_worker="ceo", initiator="hr-user-1", org=org)
    step = pending_step(session, instance)
    assert step.resolved_assignee == "role:hr-admin"
    assert "fallback" in step.resolution_reason


def test_PLAT_circular_delegation_detected(org):
    """Register row: circular delegation must be rejected, not looped."""
    with pytest.raises(CircularDelegationError):
        resolve_delegate("a", {"a": "b", "b": "c", "c": "a"})

    # And through full routing:
    with pytest.raises(CircularDelegationError):
        resolve_approver(
            {"approver": "levels-up:1"},
            subject_worker="w1", initiator="hr-user-1", org=org,
            delegations={"mgr1": "x", "x": "mgr1"},
        )


def test_PLAT_inflight_instance_finishes_on_old_version(session, org):
    """Register row: an instance started on v1 completes on v1 even after v2
    deploys; the engine refuses to advance it with the wrong version."""
    instance = start_instance(session, V1, subject_worker="w1", initiator="hr-user-1", org=org)
    assert instance.definition_version == 1

    # v2 (with an extra hr-approval step) is now the latest — engine refuses it.
    with pytest.raises(ValueError, match="finish-on-old"):
        act_on_step(session, instance, V2, actor="mgr1", approve=True, org=org)

    # Completing with the pinned v1 works and never executes v2's extra step.
    act_on_step(session, instance, V1, actor="mgr1", approve=True, org=org)
    assert instance.status == "completed"


def test_every_transition_is_audited(session, org):
    instance = start_instance(session, V1, subject_worker="w1", initiator="hr-user-1", org=org)
    act_on_step(session, instance, V1, actor="mgr1", approve=True, org=org)
    session.commit()

    events = session.scalars(
        select(AuditEvent).where(
            AuditEvent.entity_ref == f"workflow.workflow_instance:{instance.instance_id}"
        )
    ).all()
    details = [e.after["detail"] for e in events]
    assert any("started" in d for d in details)
    assert any("approved" in d for d in details)
    assert any(d == "completed" for d in details)


def test_delegation_is_resolved_and_explained(session, org):
    instance = start_instance(
        session, V1, subject_worker="w1", initiator="hr-user-1", org=org,
        delegations={"mgr1": "mgr1-backup"},
    )
    step = pending_step(session, instance)
    assert step.resolved_assignee == "mgr1-backup"
    assert "delegation" in step.resolution_reason
