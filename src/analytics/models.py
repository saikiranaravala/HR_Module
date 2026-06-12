"""Analytics data model (Specs/11). Schema: analytics.

PII-vault pattern: the dimension carries a tokenized worker key and analytic
attributes only — no names, no identifiers re-traceable without the governed
re-identification service (cloud phase).
"""
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Integer, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_ANLT_TAG = tag(category="analytics", purpose="workforce-analytics",
                lawful_basis="legitimate-interest", retention_class="analytics-3y", tier=Tier.T1)
_ANLT_PUBLIC = tag(category="analytics", purpose="workforce-analytics",
                   lawful_basis="legitimate-interest", retention_class="analytics-3y", tier=Tier.T0)

HIGH_DATE = date(9999, 12, 31)


@register_model
class DimWorker(Base):
    """SCD2 worker dimension mirroring operational effective dating."""
    __tablename__ = "dim_worker"
    __table_args__ = {"schema": "analytics"}

    row_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_key: Mapped[str] = mapped_column(Text, info=dict(_ANLT_TAG))  # tokenized
    valid_from: Mapped[date] = mapped_column(Date, info=dict(RECORD_KEEPING_TAG))
    valid_to: Mapped[date] = mapped_column(Date, default=HIGH_DATE, info=dict(RECORD_KEEPING_TAG))
    org_path: Mapped[str] = mapped_column(Text, info=dict(_ANLT_TAG))
    country: Mapped[str] = mapped_column(Text, info=dict(_ANLT_TAG))
    worker_type: Mapped[str] = mapped_column(Text, info=dict(_ANLT_TAG))  # employee|contingent
    fte: Mapped[float] = mapped_column(Numeric(4, 2), info=dict(_ANLT_TAG))
    exited: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_ANLT_TAG))
    regrettable_exit: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_ANLT_TAG))


@register_model
class CertifiedSnapshot(Base):
    """Immutable certified metric snapshots; restatement = new version row."""
    __tablename__ = "certified_snapshot"
    __table_args__ = {"schema": "analytics"}

    snapshot_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    as_of: Mapped[date] = mapped_column(Date, info=dict(RECORD_KEEPING_TAG))
    metric: Mapped[str] = mapped_column(Text, info=dict(_ANLT_PUBLIC))
    value: Mapped[float] = mapped_column(Numeric(18, 4), info=dict(_ANLT_TAG))
    version: Mapped[int] = mapped_column(Integer, default=1, info=dict(RECORD_KEEPING_TAG))
    restatement_of: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, info=dict(RECORD_KEEPING_TAG))
    annotation: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_ANLT_PUBLIC))


@register_model
class OrgBridge(Base):
    """Reorg mapping for like-for-like trending across org changes."""
    __tablename__ = "org_bridge"
    __table_args__ = {"schema": "analytics"}

    bridge_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    old_org_path: Mapped[str] = mapped_column(Text, info=dict(_ANLT_PUBLIC))
    new_org_path: Mapped[str] = mapped_column(Text, info=dict(_ANLT_PUBLIC))
    effective_date: Mapped[date] = mapped_column(Date, info=dict(RECORD_KEEPING_TAG))
