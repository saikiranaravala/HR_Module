"""Constrained workflow engine (Specs/12 §2).

Step types: approval, notification, condition. No code nodes. Definitions are
versioned YAML; an instance pins the version it started on and finishes on it
(finish-on-old). Every routing decision records WHY (explain-routing) and every
transition writes a platform audit event.

Engine-level guarantees implemented here:
- initiator ≠ approver (self-approval escalates one level instead)
- delegation resolved at evaluation time, circular delegation rejected
- approver chain exhaustion falls back to the step's fallback role
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import yaml
from sqlalchemy import DateTime, Integer, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from platform_core.audit import record_audit
from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

CONFIG_DIR = Path(__file__).resolve().parent / "config" / "workflows"

_WORKFLOW_TAG = tag(
    category="workflow-state", purpose="process-orchestration",
    lawful_basis="legitimate-interest", retention_class="workflow-3y", tier=Tier.T1,
)


class CircularDelegationError(RuntimeError):
    pass


class RoutingExhaustedError(RuntimeError):
    pass


class OrgResolver(Protocol):
    """Supplies supervisory chains; Core HR provides the real one later."""

    def manager_of(self, worker_id: str) -> str | None: ...


@register_model
class WorkflowInstance(Base):
    __tablename__ = "workflow_instance"
    __table_args__ = {"schema": "workflow"}

    instance_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    definition_key: Mapped[str] = mapped_column(Text, info=dict(_WORKFLOW_TAG))
    definition_version: Mapped[int] = mapped_column(Integer, info=dict(_WORKFLOW_TAG))
    subject_ref: Mapped[str] = mapped_column(Text, info=dict(_WORKFLOW_TAG))
    initiator: Mapped[str] = mapped_column(Text, info=dict(_WORKFLOW_TAG))
    status: Mapped[str] = mapped_column(Text, info=dict(_WORKFLOW_TAG))  # running|completed|rejected
    current_step_index: Mapped[int] = mapped_column(Integer, info=dict(_WORKFLOW_TAG))
    payload = mapped_column(JSONB, nullable=True, info=dict(_WORKFLOW_TAG))
    created_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(RECORD_KEEPING_TAG))


@register_model
class StepExecution(Base):
    __tablename__ = "step_execution"
    __table_args__ = {"schema": "workflow"}

    execution_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    instance_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_WORKFLOW_TAG))
    step_id: Mapped[str] = mapped_column(Text, info=dict(_WORKFLOW_TAG))
    step_type: Mapped[str] = mapped_column(Text, info=dict(_WORKFLOW_TAG))
    resolved_assignee: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_WORKFLOW_TAG))
    resolution_reason: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_WORKFLOW_TAG))  # explain-routing
    status: Mapped[str] = mapped_column(Text, info=dict(_WORKFLOW_TAG))  # pending|approved|rejected|done
    acted_by: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_WORKFLOW_TAG))
    acted_at = mapped_column(DateTime(timezone=True), nullable=True, info=dict(RECORD_KEEPING_TAG))


def load_definition(key: str, version: int | None = None, base_dir: Path = CONFIG_DIR) -> dict:
    """Load a workflow definition; latest version unless one is pinned."""
    raw = yaml.safe_load((base_dir / f"{key}.yaml").read_text(encoding="utf-8"))
    versions = {v["version"]: v for v in raw["versions"]}
    chosen = versions[version] if version is not None else versions[max(versions)]
    return {"key": raw["workflow"], "version": chosen["version"], "steps": chosen["steps"]}


def resolve_delegate(assignee: str, delegations: dict[str, str]) -> tuple[str, list[str]]:
    """Follow the delegation map; raise on cycles. Returns (final, hop path)."""
    path = [assignee]
    current = assignee
    while current in delegations:
        current = delegations[current]
        if current in path:
            raise CircularDelegationError(" -> ".join(path + [current]))
        path.append(current)
    return current, path


def resolve_approver(
    step: dict,
    *,
    subject_worker: str,
    initiator: str,
    org: OrgResolver,
    delegations: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Resolve an approval step to a concrete approver with an explanation."""
    delegations = delegations or {}
    rule = step["approver"]
    notes: list[str] = []

    if rule.startswith("levels-up:"):
        levels = int(rule.split(":", 1)[1])
        candidate = subject_worker
        for _ in range(levels):
            parent = org.manager_of(candidate)
            if parent is None:
                candidate = None
                break
            candidate = parent
        # Self-approval prevention: escalate past the initiator.
        while candidate is not None and candidate == initiator:
            notes.append(f"skipped {candidate} (initiator; self-approval blocked)")
            candidate = org.manager_of(candidate)
        if candidate is None:
            fallback = step.get("on_exhausted", "")
            if fallback.startswith("fallback-role:"):
                role = fallback.split(":", 1)[1]
                notes.append("chain exhausted; designated fallback role applied")
                return f"role:{role}", f"{rule} exhausted → {fallback}. " + "; ".join(notes)
            raise RoutingExhaustedError(f"{rule} exhausted for {subject_worker} and no fallback")
        final, hops = resolve_delegate(candidate, delegations)
        if final == initiator:
            raise RoutingExhaustedError("delegation resolves to initiator; self-approval blocked")
        if len(hops) > 1:
            notes.append(f"delegation {' -> '.join(hops)}")
        reason = f"{rule} from {subject_worker} → {final}" + (f" ({'; '.join(notes)})" if notes else "")
        return final, reason

    if rule.startswith("role:"):
        return rule, f"static role assignment {rule}"
    raise ValueError(f"unknown approver rule: {rule}")


def _audit(session: Session, instance: WorkflowInstance, action_detail: str, actor: str):
    record_audit(
        session,
        actor=actor,
        actor_type="system",
        action="insert",
        entity_ref=f"workflow.workflow_instance:{instance.instance_id}",
        after={"detail": action_detail, "status": instance.status,
               "step_index": instance.current_step_index},
        sensitivity_tier="T1",
        source_channel="workflow-engine",
        correlation_id=instance.correlation_id,
    )


def start_instance(
    session: Session,
    definition: dict,
    *,
    subject_worker: str,
    initiator: str,
    org: OrgResolver,
    payload: dict | None = None,
    delegations: dict[str, str] | None = None,
) -> WorkflowInstance:
    instance = WorkflowInstance(
        definition_key=definition["key"],
        definition_version=definition["version"],  # pinned: finish-on-old
        subject_ref=subject_worker,
        initiator=initiator,
        status="running",
        current_step_index=0,
        payload=payload,
        created_at=datetime.now(timezone.utc),
        correlation_id=uuid.uuid4(),
    )
    session.add(instance)
    session.flush()
    _audit(session, instance, f"started {definition['key']} v{definition['version']}", initiator)
    _activate_step(session, instance, definition, org, delegations or {})
    return instance


def _activate_step(session, instance, definition, org, delegations):
    while instance.current_step_index < len(definition["steps"]):
        step = definition["steps"][instance.current_step_index]
        if step["type"] == "approval":
            assignee, reason = resolve_approver(
                step,
                subject_worker=instance.subject_ref,
                initiator=instance.initiator,
                org=org,
                delegations=delegations,
            )
            session.add(StepExecution(
                instance_id=instance.instance_id, step_id=step["id"], step_type="approval",
                resolved_assignee=assignee, resolution_reason=reason, status="pending",
            ))
            session.flush()
            return  # wait for human action
        # notification/condition steps complete immediately at local scope
        session.add(StepExecution(
            instance_id=instance.instance_id, step_id=step["id"], step_type=step["type"],
            resolution_reason="auto-completed (non-approval step)", status="done",
            acted_by="engine", acted_at=datetime.now(timezone.utc),
        ))
        instance.current_step_index += 1
        session.flush()
    instance.status = "completed"
    session.flush()
    _audit(session, instance, "completed", "engine")


def pending_step(session: Session, instance: WorkflowInstance) -> StepExecution | None:
    from sqlalchemy import select
    return session.scalars(
        select(StepExecution).where(
            StepExecution.instance_id == instance.instance_id,
            StepExecution.status == "pending",
        )
    ).first()


def pending_for_assignee(
    session: Session, assignee: str, *, roles: tuple[str, ...] = (),
    definition_key: str | None = None,
) -> list[tuple[StepExecution, WorkflowInstance]]:
    """Inbox query: all pending approval steps resolved to this assignee —
    including steps resolved to any of the caller's roles ("role:X"), which
    `act_on_step` already permits role members to action.

    Owned here (workflow schema) so consumers like ESS/MSS never query the
    schema directly (Invariant #2).
    """
    from sqlalchemy import select
    assignees = [assignee] + [f"role:{role}" for role in roles]
    query = (
        select(StepExecution, WorkflowInstance)
        .join(WorkflowInstance, WorkflowInstance.instance_id == StepExecution.instance_id)
        .where(StepExecution.status == "pending",
               StepExecution.resolved_assignee.in_(assignees))
        .order_by(WorkflowInstance.created_at)
    )
    if definition_key is not None:
        query = query.where(WorkflowInstance.definition_key == definition_key)
    return [tuple(row) for row in session.execute(query)]


def act_on_step(
    session: Session,
    instance: WorkflowInstance,
    definition: dict,
    *,
    actor: str,
    approve: bool,
    org: OrgResolver,
    delegations: dict[str, str] | None = None,
) -> WorkflowInstance:
    if definition["version"] != instance.definition_version:
        raise ValueError(
            f"instance pinned to v{instance.definition_version}; "
            f"got definition v{definition['version']} (finish-on-old policy)"
        )
    step = pending_step(session, instance)
    if step is None:
        raise ValueError("no pending step")
    if actor == instance.initiator:
        raise PermissionError("self-approval blocked at engine level")
    if step.resolved_assignee not in (actor, f"role:{actor}") and not (
        step.resolved_assignee.startswith("role:") and actor.startswith("role-member:")
    ):
        if step.resolved_assignee != actor:
            raise PermissionError(f"step assigned to {step.resolved_assignee}, not {actor}")

    step.status = "approved" if approve else "rejected"
    step.acted_by = actor
    step.acted_at = datetime.now(timezone.utc)
    if not approve:
        instance.status = "rejected"
        session.flush()
        _audit(session, instance, f"step {step.step_id} rejected by {actor}", actor)
        return instance
    instance.current_step_index += 1
    session.flush()
    _audit(session, instance, f"step {step.step_id} approved by {actor}", actor)
    _activate_step(session, instance, definition, org, delegations or {})
    return instance
