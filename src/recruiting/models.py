"""Recruiting data model (Specs/06). Schema: recruiting."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_REC_TAG = tag(category="recruiting", purpose="talent-acquisition",
               lawful_basis="consent", retention_class="recruiting-per-country", tier=Tier.T1)
_REC_OPS_TAG = tag(category="recruiting", purpose="talent-acquisition",
                   lawful_basis="legitimate-interest", retention_class="recruiting-7y", tier=Tier.T1)
_DNR_TAG = tag(category="recruiting-flags", purpose="talent-acquisition",
               lawful_basis="legitimate-interest", retention_class="recruiting-7y", tier=Tier.T2)
_OFFER_TAG = tag(category="recruiting-offer", purpose="talent-acquisition",
                 lawful_basis="contract", retention_class="comp-7y", tier=Tier.T2)


@register_model
class CandidateProfile(Base):
    """One profile per person, shared across requisitions (register row)."""
    __tablename__ = "candidate_profile"
    __table_args__ = {"schema": "recruiting"}

    candidate_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_REC_TAG))
    email: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_REC_TAG))
    country: Mapped[str] = mapped_column(Text, info=dict(_REC_OPS_TAG))
    internal_worker_id: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_REC_OPS_TAG))
    do_not_rehire: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_DNR_TAG))
    consent_captured_on: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(RECORD_KEEPING_TAG))
    erased: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(RECORD_KEEPING_TAG))


@register_model
class Requisition(Base):
    __tablename__ = "requisition"
    __table_args__ = {"schema": "recruiting"}

    requisition_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    position_id: Mapped[str] = mapped_column(Text, info=dict(_REC_OPS_TAG))
    title: Mapped[str] = mapped_column(Text, info=dict(_REC_OPS_TAG))
    grade: Mapped[str] = mapped_column(Text, info=dict(_REC_OPS_TAG))
    country: Mapped[str] = mapped_column(Text, info=dict(_REC_OPS_TAG))
    jurisdiction: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_REC_OPS_TAG))  # e.g. US-CO
    headcount_type: Mapped[str] = mapped_column(Text, info=dict(_REC_OPS_TAG))  # backfill|net-new
    status: Mapped[str] = mapped_column(Text, default="open", info=dict(_REC_OPS_TAG))  # open|hold|filled|cancelled
    range_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True, info=dict(_OFFER_TAG))
    range_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True, info=dict(_OFFER_TAG))
    posting_text: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_REC_OPS_TAG))


@register_model
class Application(Base):
    """Per-requisition application; dispositions are per-req (register row)."""
    __tablename__ = "application"
    __table_args__ = {"schema": "recruiting"}

    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    candidate_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_REC_OPS_TAG))
    requisition_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_REC_OPS_TAG))
    stage: Mapped[str] = mapped_column(Text, default="new", info=dict(_REC_OPS_TAG))
    status: Mapped[str] = mapped_column(Text, default="active", info=dict(_REC_OPS_TAG))  # active|rejected|hired|withdrawn
    disposition_code: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_REC_OPS_TAG))  # OFCCP taxonomy
    internal: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_REC_OPS_TAG))
    confidential: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_REC_OPS_TAG))  # internal-mobility policy
    ai_rank: Mapped[int | None] = mapped_column(Integer, nullable=True, info=dict(_REC_OPS_TAG))  # advisory ONLY
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_REC_OPS_TAG))
    applied_on: Mapped[date] = mapped_column(Date, info=dict(RECORD_KEEPING_TAG))


@register_model
class Offer(Base):
    """Versioned offers — negotiation history is a chain, never an edit."""
    __tablename__ = "offer"
    __table_args__ = {"schema": "recruiting"}

    offer_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_REC_OPS_TAG))
    version: Mapped[int] = mapped_column(Integer, default=1, info=dict(RECORD_KEEPING_TAG))
    supersedes: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, info=dict(RECORD_KEEPING_TAG))
    base_annual: Mapped[Decimal] = mapped_column(Numeric(12, 2), info=dict(_OFFER_TAG))
    currency: Mapped[str] = mapped_column(Text, info=dict(_OFFER_TAG))
    components = mapped_column(JSONB, nullable=True, info=dict(_OFFER_TAG))  # sign-on w/ clawback, equity, relo
    status: Mapped[str] = mapped_column(Text, default="draft", info=dict(_REC_OPS_TAG))  # draft|extended|accepted|declined|rescinded
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(_REC_OPS_TAG))
    requires_comp_approval: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_REC_OPS_TAG))
    rescind_reason: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_REC_OPS_TAG))
    decided_at = mapped_column(DateTime(timezone=True), nullable=True, info=dict(RECORD_KEEPING_TAG))
