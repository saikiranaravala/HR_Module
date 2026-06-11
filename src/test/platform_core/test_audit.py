"""Audit pipeline tests (TECH-6): hash chain integrity, tamper detection,
append-only enforcement."""
import uuid

import pytest
from sqlalchemy import text

from platform_core.audit import record_audit, verify_chain


def _event(session, n: int):
    return record_audit(
        session,
        actor=f"actor-{n}",
        action="insert",
        entity_ref=f"test.entity:{n}",
        sensitivity_tier="T1",
        source_channel="test",
        correlation_id=uuid.uuid4(),
        after={"value": n},
    )


def test_chain_is_intact_after_appends(session):
    for n in range(5):
        _event(session, n)
    session.commit()
    assert verify_chain(session) is None


def test_chain_links_prev_hash(session):
    first = _event(session, 1)
    second = _event(session, 2)
    session.commit()
    assert second.prev_hash == first.row_hash
    assert first.prev_hash == "GENESIS"


def test_tamper_detection(session, engine):
    for n in range(3):
        _event(session, n)
    session.commit()

    # Bypass the guard the way an attacker with table ownership would,
    # then prove the chain exposes it.
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE platform.audit_event DISABLE TRIGGER immutable_platform_audit_event"
        ))
        conn.execute(text("UPDATE platform.audit_event SET actor = 'tampered' WHERE seq = 2"))
        conn.execute(text(
            "ALTER TABLE platform.audit_event ENABLE TRIGGER immutable_platform_audit_event"
        ))

    assert verify_chain(session) == 2


def test_update_and_delete_blocked(session):
    _event(session, 1)
    session.commit()

    with pytest.raises(Exception, match="immutable"):
        session.execute(text("UPDATE platform.audit_event SET actor = 'x' WHERE seq = 1"))
    session.rollback()

    with pytest.raises(Exception, match="immutable"):
        session.execute(text("DELETE FROM platform.audit_event WHERE seq = 1"))
    session.rollback()


def test_TECH_audit_surge_bulk_read_logging(session):
    """Specs/15 §9: audit store surge under read-logging — chain stays valid and
    contiguous under a burst of read events."""
    for n in range(500):
        record_audit(
            session,
            actor="surge-reader",
            action="read",
            entity_ref=f"test.entity:{n % 7}",
            sensitivity_tier="T2",
            source_channel="test",
            correlation_id=uuid.uuid4(),
        )
    session.commit()
    assert verify_chain(session) is None
