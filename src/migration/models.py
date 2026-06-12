"""Migration program data model (Specs/16). Schema: migration."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_MIG_TAG = tag(category="migration", purpose="migration-program",
               lawful_basis="legitimate-interest", retention_class="program-life+7y", tier=Tier.T1)


@register_model
class StagedRecord(Base):
    """Canonical output of transform; (batch_id, source_key) is the idempotency key."""
    __tablename__ = "staged_record"
    __table_args__ = {"schema": "migration"}

    staged_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    batch_id: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    source_key: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    domain: Mapped[str] = mapped_column(Text, info=dict(_MIG_TAG))
    payload = mapped_column(JSONB, info=dict(_MIG_TAG))  # canonical row (refs, no raw PS codes)
    loaded: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_MIG_TAG))


@register_model
class DqException(Base):
    """Steward queue: fix at the SOURCE while PS is authoritative."""
    __tablename__ = "dq_exception"
    __table_args__ = {"schema": "migration"}

    exception_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    batch_id: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    domain: Mapped[str] = mapped_column(Text, info=dict(_MIG_TAG))
    rule: Mapped[str] = mapped_column(Text, info=dict(_MIG_TAG))  # completeness|validity|referential|uniqueness
    source_ref: Mapped[str] = mapped_column(Text, info=dict(_MIG_TAG))  # ref only, no PII payload
    guidance: Mapped[str] = mapped_column(Text, info=dict(_MIG_TAG))
    status: Mapped[str] = mapped_column(Text, default="open", info=dict(_MIG_TAG))  # open|fixed-at-source|waived


@register_model
class GateArtifact(Base):
    """Signed, immutable wave gate reports — the program's audit trail."""
    __tablename__ = "gate_artifact"
    __table_args__ = {"schema": "migration"}

    artifact_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    wave: Mapped[str] = mapped_column(Text, info=dict(_MIG_TAG))
    gate: Mapped[str] = mapped_column(Text, info=dict(_MIG_TAG))  # entry|exit
    passed: Mapped[bool] = mapped_column(Boolean, info=dict(_MIG_TAG))
    report = mapped_column(JSONB, info=dict(_MIG_TAG))
    content_hash: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    signed_by: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    signed_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))


@register_model
class SyncConflict(Base):
    __tablename__ = "sync_conflict"
    __table_args__ = {"schema": "migration"}

    conflict_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_ref: Mapped[str] = mapped_column(Text, info=dict(_MIG_TAG))
    field: Mapped[str] = mapped_column(Text, info=dict(_MIG_TAG))
    ps_value: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_MIG_TAG))
    meridian_value: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_MIG_TAG))
    detected_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))
    sla_due_at = mapped_column(DateTime(timezone=True), info=dict(_MIG_TAG))  # 4h
    status: Mapped[str] = mapped_column(Text, default="open", info=dict(_MIG_TAG))  # open|resolved|parked
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_MIG_TAG))
