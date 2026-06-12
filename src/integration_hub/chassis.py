"""Shared adapter chassis (Specs/13 §6) — the pattern payroll adapters reuse.

A Connector = transform (canonical → provider format) + transport + ack
handling, with normalized errors and a run log that doubles as the heartbeat
feed. Vendor formats never escape the connector (Invariant #4).
"""
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, Text, Uuid, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag

_INT_TAG = tag(
    category="integration-ops", purpose="interface-operations",
    lawful_basis="legitimate-interest", retention_class="ops-2y", tier=Tier.T0,
)


@register_model
class ConnectorRun(Base):
    __tablename__ = "connector_run"
    __table_args__ = {"schema": "integration"}

    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    connector_key: Mapped[str] = mapped_column(Text, info=dict(_INT_TAG))
    started_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))
    finished_at = mapped_column(DateTime(timezone=True), nullable=True, info=dict(RECORD_KEEPING_TAG))
    status: Mapped[str] = mapped_column(Text, info=dict(_INT_TAG))  # success|failed
    record_count: Mapped[int] = mapped_column(Integer, default=0, info=dict(_INT_TAG))
    error_normalized: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_INT_TAG))
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(RECORD_KEEPING_TAG))


@register_model
class ConnectorCredential(Base):
    __tablename__ = "connector_credential"
    __table_args__ = {"schema": "integration"}

    credential_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    connector_key: Mapped[str] = mapped_column(Text, info=dict(_INT_TAG))
    credential_kind: Mapped[str] = mapped_column(Text, info=dict(_INT_TAG))  # cert|api-key|pgp-key
    reference: Mapped[str] = mapped_column(Text, info=dict(_INT_TAG))  # vault pointer, never the secret
    expires_on: Mapped[date] = mapped_column(Date, info=dict(_INT_TAG))


@dataclass
class TransportResult:
    accepted: bool
    ack_reference: str | None = None
    error: str | None = None


@dataclass
class ConnectorOutcome:
    status: str
    record_count: int
    ack_reference: str | None = None
    error_normalized: str | None = None
    run_id: uuid.UUID | None = None


class Connector:
    """Subclass per provider/carrier. Override transform() and transport()."""

    key: str = "abstract"

    def transform(self, canonical_records: list[dict]) -> object:
        raise NotImplementedError

    def transport(self, payload: object) -> TransportResult:
        raise NotImplementedError

    def normalize_error(self, exc_or_msg) -> str:
        return f"{self.key}: {exc_or_msg}"

    def run(self, session: Session, canonical_records: list[dict],
            correlation_id: uuid.UUID | None = None) -> ConnectorOutcome:
        run = ConnectorRun(
            connector_key=self.key,
            started_at=datetime.now(timezone.utc),
            status="failed",
            record_count=len(canonical_records),
            correlation_id=correlation_id or uuid.uuid4(),
        )
        session.add(run)
        session.flush()
        try:
            payload = self.transform(canonical_records)
            result = self.transport(payload)
            if result.accepted:
                run.status = "success"
                outcome = ConnectorOutcome("success", len(canonical_records),
                                           ack_reference=result.ack_reference, run_id=run.run_id)
            else:
                run.error_normalized = self.normalize_error(result.error)
                outcome = ConnectorOutcome("failed", len(canonical_records),
                                           error_normalized=run.error_normalized, run_id=run.run_id)
        except Exception as exc:  # noqa: BLE001 — interfaces fail loudly, never silently
            run.error_normalized = self.normalize_error(exc)
            outcome = ConnectorOutcome("failed", len(canonical_records),
                                       error_normalized=run.error_normalized, run_id=run.run_id)
        run.finished_at = datetime.now(timezone.utc)
        session.flush()
        return outcome


def last_success(session: Session, connector_key: str) -> datetime | None:
    """Heartbeat feed: expected-cadence alerting compares this to the schedule."""
    return session.scalar(
        select(ConnectorRun.finished_at)
        .where(ConnectorRun.connector_key == connector_key, ConnectorRun.status == "success")
        .order_by(ConnectorRun.finished_at.desc())
        .limit(1)
    )


def expiring_credentials(session: Session, today: date, within_days: int = 30) -> list[ConnectorCredential]:
    """The cert-lapse alert feed (Specs/13 §6 'classic silent killer')."""
    from datetime import timedelta
    horizon = today + timedelta(days=within_days)
    return list(session.scalars(
        select(ConnectorCredential)
        .where(ConnectorCredential.expires_on <= horizon)
        .order_by(ConnectorCredential.expires_on)
    ))
