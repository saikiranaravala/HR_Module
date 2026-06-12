"""Learning data model (Specs/08). Schema: learning."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_LEARN_TAG = tag(category="learning", purpose="learning-compliance",
                 lawful_basis="legal-obligation", retention_class="learning-audit-7y", tier=Tier.T1)
_CONTENT_TAG = tag(category="learning-content", purpose="learning-compliance",
                   lawful_basis="legitimate-interest", retention_class="content-current", tier=Tier.T0)


@register_model
class ContentItem(Base):
    __tablename__ = "content_item"
    __table_args__ = {"schema": "learning"}

    content_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    content_key: Mapped[str] = mapped_column(Text, info=dict(_CONTENT_TAG))  # stable across versions
    title: Mapped[str] = mapped_column(Text, info=dict(_CONTENT_TAG))
    version: Mapped[int] = mapped_column(Integer, default=1, info=dict(RECORD_KEEPING_TAG))
    supersede_policy: Mapped[str] = mapped_column(Text, default="finish-old", info=dict(_CONTENT_TAG))  # finish-old|restart
    active: Mapped[bool] = mapped_column(Boolean, default=True, info=dict(_CONTENT_TAG))


@register_model
class Assignment(Base):
    __tablename__ = "assignment"
    __table_args__ = {"schema": "learning"}

    assignment_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_LEARN_TAG))
    requirement_key: Mapped[str] = mapped_column(Text, info=dict(_LEARN_TAG))
    content_key: Mapped[str] = mapped_column(Text, info=dict(_LEARN_TAG))
    content_version: Mapped[int] = mapped_column(Integer, info=dict(_LEARN_TAG))  # version in progress
    status: Mapped[str] = mapped_column(Text, default="assigned", info=dict(_LEARN_TAG))  # assigned|in-progress|completed|waived
    due_on: Mapped[date] = mapped_column(Date, info=dict(_LEARN_TAG))
    paused_on: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(_LEARN_TAG))
    pause_log = mapped_column(JSONB, nullable=True, info=dict(RECORD_KEEPING_TAG))
    extension_note: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_LEARN_TAG))  # evidence
    attempts: Mapped[int] = mapped_column(Integer, default=0, info=dict(_LEARN_TAG))
    suspend_data: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_LEARN_TAG))
    suspend_checksum: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(RECORD_KEEPING_TAG))
    lightweight: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_LEARN_TAG))  # contractor scope


@register_model
class CompletionRecord(Base):
    """Audit evidence — immutable; corrections are new records."""
    __tablename__ = "completion_record"
    __table_args__ = {"schema": "learning"}

    completion_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_LEARN_TAG))
    requirement_key: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_LEARN_TAG))
    content_key: Mapped[str] = mapped_column(Text, info=dict(_LEARN_TAG))
    content_version: Mapped[int] = mapped_column(Integer, info=dict(_LEARN_TAG))  # pinned forever
    score: Mapped[int | None] = mapped_column(Integer, nullable=True, info=dict(_LEARN_TAG))
    completed_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))
    source: Mapped[str] = mapped_column(Text, default="native", info=dict(RECORD_KEEPING_TAG))  # native|import|equivalency
    evidence_ref: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_LEARN_TAG))
    approved_by: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(RECORD_KEEPING_TAG))  # equivalency approver


@register_model
class Certification(Base):
    __tablename__ = "certification"
    __table_args__ = {"schema": "learning"}

    certification_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_LEARN_TAG))
    cert_type: Mapped[str] = mapped_column(Text, info=dict(_LEARN_TAG))
    issuer: Mapped[str] = mapped_column(Text, info=dict(_LEARN_TAG))
    issued_on: Mapped[date] = mapped_column(Date, info=dict(_LEARN_TAG))
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(_LEARN_TAG))
    evidence_ref: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_LEARN_TAG))
    job_required: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_LEARN_TAG))
