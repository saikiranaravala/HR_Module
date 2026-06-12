"""Time & Labor data model (Specs/02). Schema: time_labor.

TimeEntry stores BOTH the UTC instants and the IANA timezone — elapsed time is
computed from UTC (DST-proof); attribution date is the LOCAL date of shift
start (midnight-spanning rule). TimeResult rows are immutable snapshots;
retro deltas are new rows with lineage, never edits.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_TIME_TAG = tag(category="time-attendance", purpose="payroll-input",
                lawful_basis="contract", retention_class="payroll-statutory", tier=Tier.T1)


@register_model
class TimeEntry(Base):
    __tablename__ = "time_entry"
    __table_args__ = {"schema": "time_labor"}

    entry_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_TIME_TAG))
    person_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_TIME_TAG))  # multi-job aggregation key
    in_utc = mapped_column(DateTime(timezone=True), info=dict(_TIME_TAG))
    out_utc = mapped_column(DateTime(timezone=True), info=dict(_TIME_TAG))
    timezone_name: Mapped[str] = mapped_column(Text, info=dict(_TIME_TAG))  # IANA
    work_date: Mapped[date] = mapped_column(Date, info=dict(_TIME_TAG))  # local shift-start date
    pay_group: Mapped[str] = mapped_column(Text, info=dict(_TIME_TAG))
    country: Mapped[str] = mapped_column(Text, info=dict(_TIME_TAG))
    state: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_TIME_TAG))


@register_model
class TimeResult(Base):
    """Canonical payroll elements per worker × period: earnings code × hours ×
    rate context. Immutable snapshot; retro deltas are separate rows."""
    __tablename__ = "time_result"
    __table_args__ = {"schema": "time_labor"}

    result_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_TIME_TAG))
    period_key: Mapped[str] = mapped_column(Text, info=dict(_TIME_TAG))  # e.g. 2026-W23|biweekly-A
    pay_group: Mapped[str] = mapped_column(Text, info=dict(_TIME_TAG))
    earnings_code: Mapped[str] = mapped_column(Text, info=dict(_TIME_TAG))  # REG|OT15|OT20|RETRO_*
    hours: Mapped[float] = mapped_column(Numeric(7, 2), info=dict(_TIME_TAG))
    rate: Mapped[float] = mapped_column(Numeric(12, 4), info=tag(
        category="compensation", purpose="payroll-input",
        lawful_basis="contract", retention_class="payroll-statutory", tier=Tier.T2))
    is_retro_delta: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_TIME_TAG))
    origin_result_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, info=dict(_TIME_TAG))  # lineage
    explanation: Mapped[str] = mapped_column(Text, info=dict(_TIME_TAG))  # rule version + inputs
    locked: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_TIME_TAG))


@register_model
class AccrualLot(Base):
    """Carryover-aware accrual lots; consumption is FIFO by expiry."""
    __tablename__ = "accrual_lot"
    __table_args__ = {"schema": "time_labor"}

    lot_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_TIME_TAG))
    absence_type: Mapped[str] = mapped_column(Text, info=dict(_TIME_TAG))  # pto|sick
    granted_on: Mapped[date] = mapped_column(Date, info=dict(_TIME_TAG))
    hours_granted: Mapped[float] = mapped_column(Numeric(7, 2), info=dict(_TIME_TAG))
    hours_consumed: Mapped[float] = mapped_column(Numeric(7, 2), default=0, info=dict(_TIME_TAG))
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(_TIME_TAG))
