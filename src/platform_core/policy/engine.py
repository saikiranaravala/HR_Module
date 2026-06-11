"""Central policy decision point (TECH-5, Invariant #3).

One implementation serves every surface: the FastAPI endpoint, in-process
calls from other services, and the serialization filter all use the same
``PolicyEngine.decide`` and ``serialize_filtered``. Policy is versioned YAML
config — changing access rules is a config change, not a code change.

Fail-closed: any error during evaluation yields DENY, never ALLOW.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml
from sqlalchemy import DateTime, Text, Uuid, Boolean
from sqlalchemy.orm import Mapped, Session, mapped_column

from platform_core.base import Base
from platform_core.catalog import (
    RECORD_KEEPING_TAG,
    TIER_ORDER,
    Tier,
    register_model,
)

DEFAULT_POLICY_PATH = Path(__file__).resolve().parent.parent / "config" / "policy" / "roles.yaml"

# Tiers whose reads must be audit-logged (TECH-6).
READ_LOGGED_TIERS = {Tier.T2, Tier.T3}


@dataclass(frozen=True)
class Subject:
    subject_id: str
    roles: tuple[str, ...]
    country: str | None = None
    org_path: str | None = None


@dataclass(frozen=True)
class Resource:
    """Attributes of the data being accessed (ABAC side of the decision)."""
    country: str | None = None
    org_path: str | None = None
    population: str | None = None
    owner_id: str | None = None  # for *.self capabilities


@dataclass
class Decision:
    allow: bool
    clearance: Tier = Tier.T0
    redact_above: Tier = Tier.T0
    policy_version: str = "unknown"
    reasons: list[str] = field(default_factory=list)
    log_read_tiers: tuple[Tier, ...] = ()


@register_model
class PolicyDecisionLog(Base):
    __tablename__ = "policy_decision_log"
    __table_args__ = {"schema": "platform"}

    decision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG)
    )
    decided_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))
    subject_id: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    capability: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    resource_ref: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(RECORD_KEEPING_TAG))
    allow: Mapped[bool] = mapped_column(Boolean, info=dict(RECORD_KEEPING_TAG))
    reasons: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    policy_version: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(RECORD_KEEPING_TAG))


class PolicyEngine:
    def __init__(self, policy_path: Path = DEFAULT_POLICY_PATH):
        self._policy_path = policy_path
        self._policy: dict | None = None

    def _load(self) -> dict:
        if self._policy is None:
            raw = yaml.safe_load(self._policy_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or "version" not in raw or "roles" not in raw:
                raise ValueError(f"malformed policy file: {self._policy_path}")
            self._policy = raw
        return self._policy

    @property
    def version(self) -> str:
        return str(self._load()["version"])

    def decide(self, subject: Subject, capability: str, resource: Resource) -> Decision:
        """Fail-closed evaluation: errors become DENY with a policy-error reason."""
        try:
            return self._decide(subject, capability, resource)
        except Exception as exc:  # noqa: BLE001 — fail closed by design
            return Decision(
                allow=False,
                reasons=[f"policy-error (fail closed): {type(exc).__name__}"],
            )

    def _decide(self, subject: Subject, capability: str, resource: Resource) -> Decision:
        policy = self._load()
        version = str(policy["version"])
        reasons: list[str] = []
        best_clearance: Tier | None = None

        for role_name in subject.roles:
            role = policy["roles"].get(role_name)
            if role is None:
                reasons.append(f"role '{role_name}' unknown")
                continue
            if not self._capability_granted(role, capability, subject, resource, reasons):
                continue
            if not self._scope_matches(role, subject, resource, reasons):
                continue
            clearance = Tier(role.get("max_tier", "T1"))
            if best_clearance is None or TIER_ORDER[clearance] > TIER_ORDER[best_clearance]:
                best_clearance = clearance

        if best_clearance is None:
            reasons.append(f"no role grants '{capability}' in scope")
            return Decision(allow=False, policy_version=version, reasons=reasons)

        return Decision(
            allow=True,
            clearance=best_clearance,
            redact_above=best_clearance,
            policy_version=version,
            reasons=[f"granted '{capability}' at clearance {best_clearance.value}"],
            log_read_tiers=tuple(t for t in READ_LOGGED_TIERS if TIER_ORDER[t] <= TIER_ORDER[best_clearance]),
        )

    @staticmethod
    def _capability_granted(role, capability, subject, resource, reasons) -> bool:
        caps = role.get("capabilities", [])
        if capability in caps:
            return True
        # `.self` grants apply only when the subject owns the resource.
        self_cap = f"{capability}.self"
        if self_cap in caps:
            if resource.owner_id is not None and resource.owner_id == subject.subject_id:
                return True
            reasons.append(f"'{self_cap}' granted but subject is not the owner")
        return False

    @staticmethod
    def _scope_matches(role, subject, resource, reasons) -> bool:
        scope = role.get("scope", {})
        countries = scope.get("countries", ["*"])
        if resource.country and "*" not in countries and resource.country not in countries:
            reasons.append(f"country '{resource.country}' outside scope {countries}")
            return False
        subtrees = scope.get("org_subtrees", ["/"])
        if resource.org_path and not any(resource.org_path.startswith(p) for p in subtrees):
            reasons.append(f"org path '{resource.org_path}' outside subtrees {subtrees}")
            return False
        populations = scope.get("populations", ["*"])
        if resource.population and "*" not in populations and resource.population not in populations:
            reasons.append(f"population '{resource.population}' outside scope {populations}")
            return False
        return True


def serialize_filtered(model: type, data: dict, decision: Decision) -> dict:
    """Strip fields above the decision's clearance — the one filter used by API
    responses and report-style output alike (cross-surface consistency)."""
    if not decision.allow:
        return {}
    clearance_rank = TIER_ORDER[decision.clearance]
    columns = model.__table__.columns
    filtered = {}
    for key, value in data.items():
        if key in columns:
            field_tag = (columns[key].info or {}).get("catalog")
            tier = field_tag.tier if field_tag else Tier.T3  # untagged ⇒ most restrictive
            if TIER_ORDER[tier] > clearance_rank:
                continue
        filtered[key] = value
    return filtered


def log_decision(
    session: Session,
    decision: Decision,
    *,
    subject: Subject,
    capability: str,
    resource_ref: str | None,
    correlation_id: uuid.UUID,
) -> None:
    session.add(
        PolicyDecisionLog(
            decided_at=datetime.now(timezone.utc),
            subject_id=subject.subject_id,
            capability=capability,
            resource_ref=resource_ref,
            allow=decision.allow,
            reasons="; ".join(decision.reasons),
            policy_version=decision.policy_version,
            correlation_id=correlation_id,
        )
    )
    session.flush()


def read_with_audit(
    session: Session,
    model: type,
    data: dict,
    decision: Decision,
    *,
    subject: Subject,
    entity_ref: str,
    source_channel: str,
    correlation_id: uuid.UUID,
) -> dict:
    """Filter a row for output and audit-log the read if T2/T3 fields are returned."""
    from platform_core.audit import record_audit
    from platform_core.catalog import field_tier

    filtered = serialize_filtered(model, data, decision)
    returned_tiers = {
        field_tier(model, key)
        for key in filtered
        if key in model.__table__.columns
    }
    sensitive = returned_tiers & READ_LOGGED_TIERS
    if sensitive and decision.allow:
        record_audit(
            session,
            actor=subject.subject_id,
            action="read",
            entity_ref=entity_ref,
            sensitivity_tier=max(sensitive, key=lambda t: TIER_ORDER[t]).value,
            source_channel=source_channel,
            correlation_id=correlation_id,
        )
    return filtered
