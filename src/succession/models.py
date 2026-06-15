"""Succession data model (Specs/09). Schema: succession. The most sensitive
non-payroll domain: slates, 9-box, and key positions are T3 (read-audited)."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Identity, Integer, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_SUCC_TAG = tag(category="succession", purpose="talent-management",
                lawful_basis="legitimate-interest", retention_class="succession-active+2y", tier=Tier.T3)
_PROFILE_TAG = tag(category="succession-profile", purpose="talent-management",
                   lawful_basis="legitimate-interest", retention_class="succession-active+2y", tier=Tier.T2)


@register_model
class KeyPosition(Base):
    __tablename__ = "key_position"
    __table_args__ = {"schema": "succession"}

    position_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    title: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))
    incumbent_id: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_SUCC_TAG))
    division_path: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))  # org subtree
    criticality = mapped_column(JSONB, info=dict(_SUCC_TAG))  # {impact, scarcity, ramp, total}
    retirement_band: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_SUCC_TAG))  # band, never a date


@register_model
class SlateEntry(Base):
    __tablename__ = "slate_entry"
    __table_args__ = {"schema": "succession"}

    entry_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    position_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_SUCC_TAG))
    successor_id: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))
    readiness: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))  # now|1-2y|3y+
    rationale: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))  # mandatory
    emergency: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_SUCC_TAG))
    development_plan_ref: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_SUCC_TAG))
    last_validated: Mapped[date] = mapped_column(Date, info=dict(_SUCC_TAG))
    status: Mapped[str] = mapped_column(Text, default="active", info=dict(_SUCC_TAG))  # active|gap


@register_model
class TalentProfile(Base):
    __tablename__ = "talent_profile"
    __table_args__ = {"schema": "succession"}

    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_PROFILE_TAG))
    aspirations: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PROFILE_TAG))
    aspirations_consent: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_PROFILE_TAG))  # manager visibility opt-in
    mobility_prefs = mapped_column(JSONB, nullable=True, info=dict(_PROFILE_TAG))
    experiences = mapped_column(JSONB, nullable=True, info=dict(_PROFILE_TAG))  # tags: P&L size, international…
    interim: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_PROFILE_TAG))  # acquisition cohort
    history_note: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PROFILE_TAG))


@register_model
class NineBoxPlacement(Base):
    """Append-only placement lineage — immutable at the database level."""
    __tablename__ = "ninebox_placement"
    __table_args__ = {"schema": "succession"}

    placement_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    seq: Mapped[int] = mapped_column(Integer, Identity(always=True), nullable=False, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))
    session_id: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))
    performance: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))  # opaque PERF rating
    potential: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))    # rubric input
    rationale: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))    # mandatory
    actor: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    placed_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))


@register_model
class DiscoveryHold(Base):
    """Legal-discovery privilege workflow over talent decisions."""
    __tablename__ = "discovery_hold"
    __table_args__ = {"schema": "succession"}

    hold_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    scope: Mapped[str] = mapped_column(Text, info=dict(_SUCC_TAG))  # e.g. worker or division
    requested_by: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    counsel: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    privileged: Mapped[bool] = mapped_column(Boolean, default=True, info=dict(_SUCC_TAG))
    counsel_approved: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(RECORD_KEEPING_TAG))
    released: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(RECORD_KEEPING_TAG))
    artifact_refs = mapped_column(JSONB, nullable=True, info=dict(_SUCC_TAG))
