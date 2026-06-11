"""Temporal data platform service (TECH-4, Invariant #1).

Effective-dated pattern: effective_date + effective_sequence + action/reason +
audit columns. Rows are immutable — corrections are new rows with a higher
sequence; retroactive changes are new rows with a past effective date and an
emitted retro record (locally an audit event; CloudEvents when the event layer
lands).

The database clock is the single time authority: created_at is set by
``now()`` server-side, never by callers.
"""
import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import Date, SmallInteger, Text, DateTime, Uuid, func, select, text
from sqlalchemy.orm import Mapped, Session, mapped_column

from platform_core.catalog import RECORD_KEEPING_TAG

# Actions a temporal insert can resolve to.
ACTION_INSERT = "insert"
ACTION_CORRECTION = "update-correction"
ACTION_RETRO = "insert-retro"


class TemporalMixin:
    """Add to any effective-dated model. Subclass must set __temporal_identity__
    to the name of its stable entity-id column."""

    __temporal_identity__: str

    effective_date: Mapped[date] = mapped_column(
        Date, primary_key=True, info=dict(RECORD_KEEPING_TAG)
    )
    effective_sequence: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, default=0, info=dict(RECORD_KEEPING_TAG)
    )
    action_code: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    action_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True, info=dict(RECORD_KEEPING_TAG)
    )
    created_by: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # single time authority: the database clock
        info=dict(RECORD_KEEPING_TAG),
    )
    source_channel: Mapped[str] = mapped_column(Text, info=dict(RECORD_KEEPING_TAG))
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(RECORD_KEEPING_TAG))


@dataclass
class TemporalWriteResult:
    action: str  # insert | update-correction | insert-retro
    effective_sequence: int


def _entity_filter(model, entity_id):
    return getattr(model, model.__temporal_identity__) == entity_id


def current_max(session: Session, model, entity_id):
    """Latest row for the entity by (effective_date, effective_sequence), or None."""
    stmt = (
        select(model)
        .where(_entity_filter(model, entity_id))
        .order_by(model.effective_date.desc(), model.effective_sequence.desc())
        .limit(1)
    )
    return session.scalars(stmt).first()


def as_of(session: Session, model, entity_id, as_of_date: date):
    """The row in force on ``as_of_date`` — max (effective_date, sequence) ≤ date."""
    stmt = (
        select(model)
        .where(
            _entity_filter(model, entity_id),
            model.effective_date <= as_of_date,
        )
        .order_by(model.effective_date.desc(), model.effective_sequence.desc())
        .limit(1)
    )
    return session.scalars(stmt).first()


def next_sequence(session: Session, model, entity_id, effective_date: date) -> int:
    stmt = select(func.max(model.effective_sequence)).where(
        _entity_filter(model, entity_id),
        model.effective_date == effective_date,
    )
    max_seq = session.scalar(stmt)
    return 0 if max_seq is None else max_seq + 1


def insert_temporal(
    session: Session,
    obj,
    *,
    actor: str,
    source_channel: str,
    correlation_id: uuid.UUID | None = None,
    on_behalf_of: str | None = None,
    actor_type: str = "user",
) -> TemporalWriteResult:
    """The only sanctioned write path for temporal rows.

    Resolves correction vs retro vs plain insert, assigns the sequence, writes
    the row, and records the audit event (with before/after snapshots). Never
    updates an existing row.
    """
    from platform_core.audit import record_audit  # local import: avoid cycle
    from platform_core.catalog import max_model_tier

    model = type(obj)
    entity_id = getattr(obj, model.__temporal_identity__)
    if entity_id is None:
        raise ValueError("temporal insert requires the entity id to be set")
    if obj.effective_date is None:
        raise ValueError("temporal insert requires effective_date")

    correlation_id = correlation_id or uuid.uuid4()
    latest = current_max(session, model, entity_id)
    predecessor = as_of(session, model, entity_id, obj.effective_date)

    seq = next_sequence(session, model, entity_id, obj.effective_date)
    if seq > 0:
        action = ACTION_CORRECTION
    elif latest is not None and obj.effective_date < latest.effective_date:
        action = ACTION_RETRO
    else:
        action = ACTION_INSERT

    obj.effective_sequence = seq
    obj.created_by = actor
    obj.source_channel = source_channel
    obj.correlation_id = correlation_id
    session.add(obj)
    session.flush()
    session.refresh(obj)  # load server-side created_at (single time authority)

    record_audit(
        session,
        actor=actor,
        on_behalf_of=on_behalf_of,
        actor_type=actor_type,
        action=action,
        entity_ref=f"{model.__table__.fullname}:{entity_id}",
        before=snapshot(predecessor),
        after=snapshot(obj),
        sensitivity_tier=max_model_tier(model).value,
        source_channel=source_channel,
        correlation_id=correlation_id,
    )
    return TemporalWriteResult(action=action, effective_sequence=seq)


def snapshot(obj) -> dict | None:
    """JSON-safe dict of a row's mapped columns (audit before/after payloads)."""
    if obj is None:
        return None
    result = {}
    for column in type(obj).__table__.columns:
        value = getattr(obj, column.name)
        result[column.name] = value if isinstance(value, (str, int, float, bool, type(None))) else str(value)
    return result


IMMUTABILITY_FUNCTION_DDL = text(
    """
    CREATE SCHEMA IF NOT EXISTS platform;
    CREATE OR REPLACE FUNCTION platform.forbid_mutation() RETURNS trigger AS $$
    BEGIN
        RAISE EXCEPTION 'rows in %.% are immutable (temporal/audit pattern): % denied',
            TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP;
    END;
    $$ LANGUAGE plpgsql;
    """
)


def install_immutability_guard(connection, table_fullname: str) -> None:
    """Block UPDATE and DELETE on a temporal or audit table at the database level."""
    trigger_name = f"immutable_{table_fullname.replace('.', '_')}"
    connection.execute(IMMUTABILITY_FUNCTION_DDL)
    connection.execute(
        text(
            f"""
            DROP TRIGGER IF EXISTS {trigger_name} ON {table_fullname};
            CREATE TRIGGER {trigger_name}
                BEFORE UPDATE OR DELETE ON {table_fullname}
                FOR EACH ROW EXECUTE FUNCTION platform.forbid_mutation();
            """
        )
    )
