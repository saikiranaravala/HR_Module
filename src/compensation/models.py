"""Compensation data model (Specs/05). Schema: comp.

Comp is Invariant-#1 territory: ranges and comp records are temporal
(EFFDT/EFFSEQ via TemporalMixin, written only through insert_temporal) and
T2-sensitive (read-logged, the most-audited domain).
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag
from platform_core.temporal import TemporalMixin

_COMP_TAG = tag(category="compensation", purpose="comp-administration",
                lawful_basis="contract", retention_class="comp-7y", tier=Tier.T2)
_COMP_STRUCT_TAG = tag(category="compensation-structure", purpose="comp-administration",
                       lawful_basis="legitimate-interest", retention_class="comp-7y", tier=Tier.T1)


def comp_key(worker_id: str, record_role: str = "home") -> uuid.UUID:
    """Deterministic temporal identity per (worker, role) comp series."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"meridian:comp:{worker_id}:{record_role}")


@register_model
class GradeRange(TemporalMixin, Base):
    """Effective-dated salary range per grade × country."""
    __tablename__ = "grade_range"
    __table_args__ = {"schema": "comp"}
    __temporal_identity__ = "range_key"

    range_key: Mapped[str] = mapped_column(Text, primary_key=True, info=dict(RECORD_KEEPING_TAG))  # "G7:US"
    grade: Mapped[str] = mapped_column(Text, info=dict(_COMP_STRUCT_TAG))
    country: Mapped[str] = mapped_column(Text, info=dict(_COMP_STRUCT_TAG))
    currency: Mapped[str] = mapped_column(Text, info=dict(_COMP_STRUCT_TAG))
    range_min: Mapped[Decimal] = mapped_column(Numeric(12, 2), info=dict(_COMP_STRUCT_TAG))
    range_mid: Mapped[Decimal] = mapped_column(Numeric(12, 2), info=dict(_COMP_STRUCT_TAG))
    range_max: Mapped[Decimal] = mapped_column(Numeric(12, 2), info=dict(_COMP_STRUCT_TAG))


@register_model
class CompRecord(TemporalMixin, Base):
    """The temporal comp series per worker (and per expat role)."""
    __tablename__ = "comp_record"
    __table_args__ = {"schema": "comp"}
    __temporal_identity__ = "comp_key"

    comp_key: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_COMP_TAG))
    record_role: Mapped[str] = mapped_column(Text, default="home", info=dict(_COMP_TAG))  # home|host-shadow
    base_annual: Mapped[Decimal] = mapped_column(Numeric(12, 2), info=dict(_COMP_TAG))
    currency: Mapped[str] = mapped_column(Text, info=dict(_COMP_TAG))
    grade: Mapped[str] = mapped_column(Text, info=dict(_COMP_TAG))
    country: Mapped[str] = mapped_column(Text, info=dict(_COMP_TAG))
    fte: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1"), info=dict(_COMP_TAG))


@register_model
class CompCycle(Base):
    __tablename__ = "comp_cycle"
    __table_args__ = {"schema": "comp"}

    cycle_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    name: Mapped[str] = mapped_column(Text, info=dict(_COMP_STRUCT_TAG))
    status: Mapped[str] = mapped_column(Text, info=dict(_COMP_STRUCT_TAG))  # open|submitted|released
    corporate_currency: Mapped[str] = mapped_column(Text, info=dict(_COMP_STRUCT_TAG))
    fx_rates = mapped_column(JSONB, info=dict(_COMP_STRUCT_TAG))  # locked at open
    budget_pool: Mapped[Decimal] = mapped_column(Numeric(14, 2), info=dict(_COMP_TAG))
    opened_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))


@register_model
class CycleLine(Base):
    """Frozen worksheet row — population snapshot taken at cycle open."""
    __tablename__ = "cycle_line"
    __table_args__ = {"schema": "comp"}

    line_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    cycle_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_COMP_TAG))
    worker_id: Mapped[str] = mapped_column(Text, info=dict(_COMP_TAG))
    manager_id: Mapped[str] = mapped_column(Text, info=dict(_COMP_TAG))
    snapshot = mapped_column(JSONB, info=dict(_COMP_TAG))  # {salary, currency, rating, compa_ratio}
    merit_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True, info=dict(_COMP_TAG))
    justification: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_COMP_TAG))
    out_of_guideline: Mapped[bool] = mapped_column(default=False, info=dict(_COMP_TAG))
    status: Mapped[str] = mapped_column(Text, default="draft", info=dict(_COMP_TAG))  # draft|submitted|routed-skip-level
