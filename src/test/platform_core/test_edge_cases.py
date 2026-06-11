"""Named edge-case tests from the Specs/15 §9 register (local-scope rows).
Cloud-only register rows (region failover, Kafka lag, KMS drill) are deferred —
see TechDesignDoc/15-foundation-design.md §5."""
import uuid
from datetime import date

from platform_core import temporal
from sample_entity import WorkerProfile


def test_TECH_clock_skew_effective_ordering(session, make_row):
    """Single time authority: ordering comes from the DB-assigned sequence and
    DB clock, never from caller-supplied timestamps. Same-day writes are
    strictly ordered even if callers' clocks disagree."""
    worker_id = uuid.uuid4()
    day = date(2026, 7, 1)

    results = []
    for _ in range(4):  # four same-day writes from "different machines"
        results.append(
            temporal.insert_temporal(
                session, make_row(worker_id, day),
                actor="node-with-skewed-clock", source_channel="test",
                correlation_id=uuid.uuid4(),
            )
        )
    session.commit()

    sequences = [r.effective_sequence for r in results]
    assert sequences == [0, 1, 2, 3]  # strictly monotonic, DB-assigned

    rows = [
        temporal.as_of(session, WorkerProfile, worker_id, day)
    ]
    assert rows[0].effective_sequence == 3  # latest sequence wins

    # created_at values come from the database clock: non-decreasing.
    from sqlalchemy import select
    all_rows = session.scalars(
        select(WorkerProfile)
        .where(WorkerProfile.worker_id == worker_id)
        .order_by(WorkerProfile.effective_sequence)
    ).all()
    stamps = [r.created_at for r in all_rows]
    assert stamps == sorted(stamps)
