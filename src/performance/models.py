"""Performance data model (Specs/07). Schema: performance."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_PERF_TAG = tag(category="performance", purpose="performance-management",
                lawful_basis="legitimate-interest", retention_class="perf-per-country", tier=Tier.T1)
# PIP / restricted docs are tier-3 (read-audited).
_PERF_RESTRICTED_TAG = tag(category="performance-restricted", purpose="performance-management",
                           lawful_basis="legitimate-interest", retention_class="perf-per-country", tier=Tier.T3)


@register_model
class Goal(Base):
    """Goals with cascade alignment; revisions are a version chain — the
    original is preserved, never edited (PERF-1)."""
    __tablename__ = "goal"
    __table_args__ = {"schema": "performance"}

    goal_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    title: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    goal_type: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))  # okr|mbo|development
    weight: Mapped[int] = mapped_column(Integer, default=0, info=dict(_PERF_TAG))
    parent_goal_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, info=dict(_PERF_TAG))  # cascade
    visibility: Mapped[str] = mapped_column(Text, default="manager", info=dict(_PERF_TAG))  # private|manager|public
    status: Mapped[str] = mapped_column(Text, default="active", info=dict(_PERF_TAG))  # active|superseded|done
    version: Mapped[int] = mapped_column(Integer, default=1, info=dict(RECORD_KEEPING_TAG))
    supersedes: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, info=dict(RECORD_KEEPING_TAG))


@register_model
class ReviewCycle(Base):
    __tablename__ = "review_cycle"
    __table_args__ = {"schema": "performance"}

    cycle_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    name: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    template_key: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    status: Mapped[str] = mapped_column(Text, default="open", info=dict(_PERF_TAG))
    launched_on: Mapped[date] = mapped_column(Date, info=dict(RECORD_KEEPING_TAG))
    window_end: Mapped[date] = mapped_column(Date, info=dict(_PERF_TAG))


@register_model
class ReviewDoc(Base):
    __tablename__ = "review_doc"
    __table_args__ = {"schema": "performance"}

    doc_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    cycle_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_PERF_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    manager_id: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    state: Mapped[str] = mapped_column(Text, default="draft", info=dict(_PERF_TAG))
    # draft|self-done|manager-done|calibrated|released|acknowledged|amended|closed-out
    rating: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))  # nullable: ratingless mode
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))
    self_assessment: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))
    ai_drafted: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(RECORD_KEEPING_TAG))
    ai_draft_edited: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(RECORD_KEEPING_TAG))
    prorated: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_PERF_TAG))
    extension_until: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(_PERF_TAG))
    restricted: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_PERF_RESTRICTED_TAG))  # PIP tier
    amends: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, info=dict(RECORD_KEEPING_TAG))  # dual record
    amendment_reason: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))
    skip_level_disagreement: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))
    acknowledged_comment: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))
    closeout_reason: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))
    handoff_log = mapped_column(JSONB, nullable=True, info=dict(RECORD_KEEPING_TAG))  # manager-change lineage


@register_model
class CalibrationAdjustment(Base):
    """Append-only rating lineage: every adjustment carries actor + rationale."""
    __tablename__ = "calibration_adjustment"
    __table_args__ = {"schema": "performance"}

    adjustment_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    doc_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_PERF_TAG))
    session_id: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    before_rating: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))
    after_rating: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))
    rationale: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))  # mandatory
    actor: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    adjusted_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))


@register_model
class Checkin(Base):
    __tablename__ = "checkin"
    __table_args__ = {"schema": "performance"}

    checkin_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    manager_id: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    occurred_on: Mapped[date] = mapped_column(Date, info=dict(_PERF_TAG))
    shared_notes: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))
    private_notes: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))  # author-only
    private_notes_author: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(RECORD_KEEPING_TAG))


@register_model
class Feedback(Base):
    """Feedback with EXPLICIT per-item visibility — no silent manager copy."""
    __tablename__ = "feedback"
    __table_args__ = {"schema": "performance"}

    feedback_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    author_id: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    subject_id: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    visibility: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))  # to-subject|to-manager
    body: Mapped[str] = mapped_column(Text, info=dict(_PERF_TAG))
    competency: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))
    campaign_id: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERF_TAG))  # 360
    given_on: Mapped[date] = mapped_column(Date, info=dict(RECORD_KEEPING_TAG))
