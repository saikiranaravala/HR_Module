"""Benefits data model (Specs/04). Schema: benefits."""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_BEN_TAG = tag(category="benefits", purpose="benefits-administration",
               lawful_basis="contract", retention_class="benefits-7y", tier=Tier.T1)
# Health-plan election detail is HIPAA-adjacent → T3.
_BEN_HEALTH_TAG = tag(category="benefits-health", purpose="benefits-administration",
                      lawful_basis="contract", retention_class="benefits-7y", tier=Tier.T3)


@register_model
class BenefitPlan(Base):
    __tablename__ = "benefit_plan"
    __table_args__ = {"schema": "benefits"}

    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    plan_type: Mapped[str] = mapped_column(Text, info=dict(_BEN_TAG))  # medical|dental|life|retirement
    name: Mapped[str] = mapped_column(Text, info=dict(_BEN_TAG))
    country: Mapped[str] = mapped_column(Text, info=dict(_BEN_TAG))
    requires_eoi_above_multiple: Mapped[int | None] = mapped_column(Integer, nullable=True, info=dict(_BEN_TAG))  # life: EOI above N× salary
    default_option: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_BEN_TAG))  # window-expiry default


@register_model
class BenefitRate(Base):
    """Effective-dated rate rows: (plan, option tier, age band) → annual premium."""
    __tablename__ = "benefit_rate"
    __table_args__ = {"schema": "benefits"}

    rate_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_BEN_TAG))
    option: Mapped[str] = mapped_column(Text, info=dict(_BEN_TAG))  # EE|EE+SP|EE+FAM
    age_min: Mapped[int] = mapped_column(Integer, default=0, info=dict(_BEN_TAG))
    age_max: Mapped[int] = mapped_column(Integer, default=120, info=dict(_BEN_TAG))
    effective_date: Mapped[date] = mapped_column(Date, info=dict(RECORD_KEEPING_TAG))
    annual_premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), info=dict(_BEN_TAG))
    employer_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), info=dict(_BEN_TAG))


@register_model
class Enrollment(Base):
    __tablename__ = "enrollment"
    __table_args__ = {"schema": "benefits"}

    enrollment_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_BEN_TAG))
    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_BEN_TAG))
    option: Mapped[str] = mapped_column(Text, info=dict(_BEN_HEALTH_TAG))
    status: Mapped[str] = mapped_column(Text, info=dict(_BEN_TAG))  # pending-eoi|active|terminated|waived|defaulted
    coverage_start: Mapped[date] = mapped_column(Date, info=dict(_BEN_TAG))
    coverage_end: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(_BEN_TAG))
    dependents = mapped_column(JSONB, nullable=True, info=dict(_BEN_HEALTH_TAG))  # [{dependent_key, relation}]
    source: Mapped[str] = mapped_column(Text, info=dict(_BEN_TAG))  # new-hire|life-event|oe|default
