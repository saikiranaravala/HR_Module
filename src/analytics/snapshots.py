"""Certified snapshots (Specs/11 §2/§8): immutable once written (DB-level
guard); retro corrections produce a NEW version row annotated with why, the
original remains forever readable."""
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from analytics.models import CertifiedSnapshot


def certify(session: Session, *, as_of: date, metric: str, value: float) -> CertifiedSnapshot:
    snap = CertifiedSnapshot(as_of=as_of, metric=metric, value=value, version=1)
    session.add(snap)
    session.flush()
    return snap


def restate_snapshot(session: Session, original: CertifiedSnapshot, *,
                     value: float, annotation: str) -> CertifiedSnapshot:
    """Restatement: never mutates — writes version n+1 pointing at the original."""
    snap = CertifiedSnapshot(
        as_of=original.as_of, metric=original.metric, value=value,
        version=original.version + 1, restatement_of=original.snapshot_id,
        annotation=annotation,
    )
    session.add(snap)
    session.flush()
    return snap


def current_certified(session: Session, *, as_of: date, metric: str) -> CertifiedSnapshot | None:
    return session.scalars(
        select(CertifiedSnapshot)
        .where(CertifiedSnapshot.as_of == as_of, CertifiedSnapshot.metric == metric)
        .order_by(CertifiedSnapshot.version.desc())
    ).first()
