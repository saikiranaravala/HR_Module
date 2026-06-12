"""SCD2 dimension maintenance (Specs/11 §2) and the restatement policy (§8):
retro changes RESTATE facts (history rows are corrected) while certified
snapshots stay immutable and get annotated restatement versions."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from analytics.models import HIGH_DATE, DimWorker


def current_row(session: Session, worker_key: str) -> DimWorker | None:
    return session.scalars(select(DimWorker).where(
        DimWorker.worker_key == worker_key,
        DimWorker.valid_to == HIGH_DATE,
    )).first()


def apply_change(session: Session, *, worker_key: str, effective_from: date, **attrs) -> DimWorker:
    """Standard SCD2: close the open row the day before, open a new one."""
    open_row = current_row(session, worker_key)
    if open_row is not None:
        base = {c: getattr(open_row, c) for c in
                ("org_path", "country", "worker_type", "fte", "exited", "regrettable_exit")}
        open_row.valid_to = effective_from - timedelta(days=1)
    else:
        base = {"exited": False, "regrettable_exit": False}
    base.update(attrs)
    row = DimWorker(worker_key=worker_key, valid_from=effective_from,
                    valid_to=HIGH_DATE, **base)
    session.add(row)
    session.flush()
    return row


def restate(session: Session, *, worker_key: str, on: date, **corrections) -> list[DimWorker]:
    """Retro restatement: correct the dimension rows covering `on` and later.

    Facts restate (this is the documented SCD2 restatement policy) — but
    nothing here touches certified snapshots; those are immutable and get a
    restatement VERSION via `snapshots.restate_snapshot`.
    """
    rows = session.scalars(select(DimWorker).where(
        DimWorker.worker_key == worker_key,
        DimWorker.valid_to >= on,
    ).order_by(DimWorker.valid_from)).all()
    for row in rows:
        for field, value in corrections.items():
            setattr(row, field, value)
    session.flush()
    return rows


def rows_as_of(session: Session, as_of: date) -> list[DimWorker]:
    return session.scalars(select(DimWorker).where(
        DimWorker.valid_from <= as_of,
        DimWorker.valid_to >= as_of,
    )).all()
