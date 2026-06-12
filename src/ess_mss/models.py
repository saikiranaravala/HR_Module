"""ESS/MSS + HR Service Delivery data model (Specs/10). Schema: service_delivery."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_SVC_TAG = tag(category="service-delivery", purpose="hr-service",
               lawful_basis="legitimate-interest", retention_class="cases-5y", tier=Tier.T1)
# Employee-relations case content is segregated (whistleblower directive) → T3.
_ER_TAG = tag(category="service-delivery-er", purpose="hr-service",
              lawful_basis="legal-obligation", retention_class="cases-5y", tier=Tier.T3)
_CONTENT_TAG = tag(category="knowledge-content", purpose="hr-service",
                   lawful_basis="legitimate-interest", retention_class="content-current", tier=Tier.T0)


@register_model
class Case(Base):
    __tablename__ = "case"
    __table_args__ = {"schema": "service_delivery"}

    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))
    topic: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))
    queue: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))  # payroll|benefits|er|general
    priority: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))
    status: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))  # open|closed
    description: Mapped[str] = mapped_column(Text, info=dict(_ER_TAG))  # may hold ER detail
    transcript = mapped_column(JSONB, nullable=True, info=dict(_ER_TAG))  # copilot handoff
    opened_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))
    sla_due_at = mapped_column(DateTime(timezone=True), info=dict(_SVC_TAG))
    closed_at = mapped_column(DateTime(timezone=True), nullable=True, info=dict(RECORD_KEEPING_TAG))
    satisfaction: Mapped[int | None] = mapped_column(Integer, nullable=True, info=dict(_SVC_TAG))


@register_model
class CaseNote(Base):
    __tablename__ = "case_note"
    __table_args__ = {"schema": "service_delivery"}

    note_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_SVC_TAG))
    author: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))
    visibility: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))  # internal|employee
    body: Mapped[str] = mapped_column(Text, info=dict(_ER_TAG))
    created_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))


@register_model
class KbArticle(Base):
    __tablename__ = "kb_article"
    __table_args__ = {"schema": "service_delivery"}

    article_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    title: Mapped[str] = mapped_column(Text, info=dict(_CONTENT_TAG))
    body: Mapped[str] = mapped_column(Text, info=dict(_CONTENT_TAG))
    country: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))  # population targeting
    population: Mapped[str] = mapped_column(Text, default="all", info=dict(_SVC_TAG))
    version: Mapped[int] = mapped_column(Integer, default=1, info=dict(RECORD_KEEPING_TAG))
    status: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))  # draft|in-legal-review|published
    is_policy: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_SVC_TAG))  # legal gate
    published_on: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(RECORD_KEEPING_TAG))
    review_due: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(_SVC_TAG))


@register_model
class Delegation(Base):
    __tablename__ = "delegation"
    __table_args__ = {"schema": "service_delivery"}

    delegation_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    delegator: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))
    delegate: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))
    scope_types = mapped_column(JSONB, info=dict(_SVC_TAG))  # ["time","absence",...]
    starts_on: Mapped[date] = mapped_column(Date, info=dict(_SVC_TAG))
    ends_on: Mapped[date] = mapped_column(Date, info=dict(_SVC_TAG))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_SVC_TAG))


@register_model
class NotificationPref(Base):
    __tablename__ = "notification_pref"
    __table_args__ = {"schema": "service_delivery"}

    pref_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))
    notif_type: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_SVC_TAG))  # None = account-level
    channels = mapped_column(JSONB, nullable=True, info=dict(_SVC_TAG))  # override list
    quiet_start: Mapped[int | None] = mapped_column(Integer, nullable=True, info=dict(_SVC_TAG))  # local hour
    quiet_end: Mapped[int | None] = mapped_column(Integer, nullable=True, info=dict(_SVC_TAG))
    personal_channel_consent: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_SVC_TAG))


@register_model
class AccessGrant(Base):
    """Alumni limited-scope access and legal-hold freeze flags."""
    __tablename__ = "access_grant"
    __table_args__ = {"schema": "service_delivery"}

    grant_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))
    kind: Mapped[str] = mapped_column(Text, info=dict(_SVC_TAG))  # alumni|legal-hold
    scope = mapped_column(JSONB, nullable=True, info=dict(_SVC_TAG))  # alumni: ["payslip","tax-doc"]
    reason: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_SVC_TAG))
    starts_on: Mapped[date] = mapped_column(Date, info=dict(_SVC_TAG))
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(_SVC_TAG))  # None = until released
    released: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_SVC_TAG))
