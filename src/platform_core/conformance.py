"""Temporal conformance suite (TECH-4) — the shared tests every effective-dated
entity must pass. A module's test file subclasses TemporalConformanceSuite and
provides two fixtures:

    temporal_model  — the mapped class under test
    make_row        — make_row(entity_id, effective_date, **domain_overrides)
                      returning an UNSAVED instance with domain fields set

plus the standard ``session`` fixture. Inherited tests then enforce as-of
correctness, sequence ordering, retro semantics, audit coverage, and
database-level immutability for that entity.
"""
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import select, text

from platform_core import temporal
from platform_core.audit import AuditEvent

ACTOR = "conformance-suite"
CHANNEL = "test"


def _insert(session, row):
    return temporal.insert_temporal(
        session, row, actor=ACTOR, source_channel=CHANNEL, correlation_id=uuid.uuid4()
    )


class TemporalConformanceSuite:
    def test_as_of_straddles_change_boundary(self, session, temporal_model, make_row):
        entity_id = uuid.uuid4()
        _insert(session, make_row(entity_id, date(2026, 1, 1)))
        _insert(session, make_row(entity_id, date(2026, 3, 1)))
        session.commit()

        before = temporal.as_of(session, temporal_model, entity_id, date(2026, 2, 28))
        on = temporal.as_of(session, temporal_model, entity_id, date(2026, 3, 1))
        prior = temporal.as_of(session, temporal_model, entity_id, date(2025, 12, 31))

        assert before.effective_date == date(2026, 1, 1)
        assert on.effective_date == date(2026, 3, 1)
        assert prior is None

    def test_same_day_double_change_orders_by_sequence(self, session, temporal_model, make_row):
        entity_id = uuid.uuid4()
        day = date(2026, 5, 1)
        first = _insert(session, make_row(entity_id, day))
        second = _insert(session, make_row(entity_id, day))
        session.commit()

        assert (first.action, first.effective_sequence) == (temporal.ACTION_INSERT, 0)
        assert (second.action, second.effective_sequence) == (temporal.ACTION_CORRECTION, 1)
        winner = temporal.as_of(session, temporal_model, entity_id, day)
        assert winner.effective_sequence == 1  # highest sequence wins same-day

    def test_retro_insert_is_flagged_and_audited(self, session, temporal_model, make_row):
        entity_id = uuid.uuid4()
        _insert(session, make_row(entity_id, date(2026, 6, 1)))
        retro = _insert(session, make_row(entity_id, date(2026, 2, 1)))
        session.commit()

        assert retro.action == temporal.ACTION_RETRO
        retro_events = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == temporal.ACTION_RETRO,
                AuditEvent.entity_ref == f"{temporal_model.__table__.fullname}:{entity_id}",
            )
        ).all()
        assert len(retro_events) == 1  # retro record emitted, never a silent rewrite

    def test_audit_columns_populated_on_every_write(self, session, temporal_model, make_row):
        entity_id = uuid.uuid4()
        _insert(session, make_row(entity_id, date(2026, 4, 1)))
        session.commit()

        row = temporal.as_of(session, temporal_model, entity_id, date(2026, 4, 1))
        assert row.created_by == ACTOR
        assert row.source_channel == CHANNEL
        assert row.correlation_id is not None
        assert row.created_at is not None  # set by the database clock, not the caller
        assert row.action_code

    def test_update_is_blocked_by_database(self, session, temporal_model, make_row):
        entity_id = uuid.uuid4()
        _insert(session, make_row(entity_id, date(2026, 1, 15)))
        session.commit()

        with pytest.raises(Exception, match="immutable"):
            session.execute(
                text(
                    f"UPDATE {temporal_model.__table__.fullname} "
                    f"SET action_code = 'HACK' "
                    f"WHERE {temporal_model.__temporal_identity__} = :eid"
                ),
                {"eid": str(entity_id)},
            )
        session.rollback()

    def test_delete_is_blocked_by_database(self, session, temporal_model, make_row):
        entity_id = uuid.uuid4()
        _insert(session, make_row(entity_id, date(2026, 1, 15)))
        session.commit()

        with pytest.raises(Exception, match="immutable"):
            session.execute(
                text(
                    f"DELETE FROM {temporal_model.__table__.fullname} "
                    f"WHERE {temporal_model.__temporal_identity__} = :eid"
                ),
                {"eid": str(entity_id)},
            )
        session.rollback()
