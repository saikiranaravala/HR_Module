"""Append-only, hash-chained audit pipeline (TECH-6).

Every mutation (and every T2/T3 read) becomes an AuditEvent row. Rows form a
single hash chain: row_hash = sha256(prev_hash || canonical_json(payload)).
Appends are serialized with a Postgres advisory lock; UPDATE/DELETE are blocked
by trigger. WORM object-lock storage is a cloud-phase concern — locally the
trigger + revoked grants are the append-only enforcement.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Text, Uuid, func, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, register_model, tag, Tier

GENESIS_HASH = "GENESIS"
_CHAIN_LOCK_KEY = 815001  # advisory lock id for platform.audit_event appends


@register_model
class AuditEvent(Base):
    __tablename__ = "audit_event"
    __table_args__ = {"schema": "platform"}

    audit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG)
    )
    seq: Mapped[int] = mapped_column(BigInteger, unique=True, info=dict(RECORD_KEEPING_TAG))
    occurred_at = mapped_column(DateTime(timezone=True), info=dict(RECORD_KEEPING_TAG))
    actor: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    on_behalf_of: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(RECORD_KEEPING_TAG))
    actor_type: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))  # user|system|agent
    action: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))  # insert|update-correction|insert-retro|read
    entity_ref: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    before = mapped_column(
        JSONB,
        nullable=True,
        info=tag(category="audit-snapshot", purpose="audit-and-integrity",
                 lawful_basis="legal-obligation", retention_class="audit-7y", tier=Tier.T2),
    )
    after = mapped_column(
        JSONB,
        nullable=True,
        info=tag(category="audit-snapshot", purpose="audit-and-integrity",
                 lawful_basis="legal-obligation", retention_class="audit-7y", tier=Tier.T2),
    )
    sensitivity_tier: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    source_channel: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(RECORD_KEEPING_TAG))
    prev_hash: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    row_hash: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _hash_payload(event: AuditEvent) -> dict:
    return {
        "seq": event.seq,
        # Canonicalize to UTC: Postgres returns timestamptz in the session
        # timezone, which must not change the hash.
        "occurred_at": event.occurred_at.astimezone(timezone.utc).isoformat(),
        "actor": event.actor,
        "on_behalf_of": event.on_behalf_of,
        "actor_type": event.actor_type,
        "action": event.action,
        "entity_ref": event.entity_ref,
        "before": event.before,
        "after": event.after,
        "sensitivity_tier": event.sensitivity_tier,
        "source_channel": event.source_channel,
        "correlation_id": str(event.correlation_id),
    }


def compute_row_hash(prev_hash: str, payload: dict) -> str:
    return hashlib.sha256((prev_hash + canonical_json(payload)).encode()).hexdigest()


def record_audit(
    session: Session,
    *,
    actor: str,
    action: str,
    entity_ref: str,
    sensitivity_tier: str,
    source_channel: str,
    correlation_id: uuid.UUID,
    before: dict | None = None,
    after: dict | None = None,
    on_behalf_of: str | None = None,
    actor_type: str = "user",
) -> AuditEvent:
    # Serialize appends so seq/prev_hash are race-free within the transaction.
    session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _CHAIN_LOCK_KEY})

    last = session.scalars(
        select(AuditEvent).order_by(AuditEvent.seq.desc()).limit(1)
    ).first()
    seq = 1 if last is None else last.seq + 1
    prev_hash = GENESIS_HASH if last is None else last.row_hash

    event = AuditEvent(
        seq=seq,
        occurred_at=datetime.now(timezone.utc),
        actor=actor,
        on_behalf_of=on_behalf_of,
        actor_type=actor_type,
        action=action,
        entity_ref=entity_ref,
        before=before,
        after=after,
        sensitivity_tier=sensitivity_tier,
        source_channel=source_channel,
        correlation_id=correlation_id,
        prev_hash=prev_hash,
    )
    event.row_hash = compute_row_hash(prev_hash, _hash_payload(event))
    session.add(event)
    session.flush()
    return event


def verify_chain(session: Session, start_seq: int = 1) -> int | None:
    """Walk the chain from start_seq; return the first broken seq, or None if intact."""
    events = session.scalars(
        select(AuditEvent).where(AuditEvent.seq >= start_seq).order_by(AuditEvent.seq)
    ).all()
    prev_hash = GENESIS_HASH
    if start_seq > 1:
        anchor = session.scalar(select(AuditEvent).where(AuditEvent.seq == start_seq - 1))
        if anchor is None:
            return start_seq
        prev_hash = anchor.row_hash
    expected_seq = start_seq
    for event in events:
        if event.seq != expected_seq:
            return expected_seq  # gap in the chain
        if event.prev_hash != prev_hash:
            return event.seq
        if compute_row_hash(prev_hash, _hash_payload(event)) != event.row_hash:
            return event.seq
        prev_hash = event.row_hash
        expected_seq += 1
    return None
