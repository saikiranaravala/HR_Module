"""9-box placements (SUCC-2): performance (opaque PERF rating) × potential
(rubric input), mandatory rationale, append-only immutable lineage, session
decision log."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from succession.models import NineBoxPlacement


class RationaleRequiredError(ValueError):
    pass


def place(session: Session, *, worker_id: str, session_id: str, performance: str,
          potential: str, rationale: str | None, actor: str) -> NineBoxPlacement:
    if not rationale or not rationale.strip():
        raise RationaleRequiredError("9-box placements require a rationale")
    placement = NineBoxPlacement(
        worker_id=worker_id, session_id=session_id, performance=performance,
        potential=potential, rationale=rationale, actor=actor,
        placed_at=datetime.now(timezone.utc),
    )
    session.add(placement)
    session.flush()
    return placement


def session_minutes(session: Session, *, session_id: str) -> list[dict]:
    """Auto-minuted decision log: the full placement lineage of a session."""
    placements = session.scalars(select(NineBoxPlacement).where(
        NineBoxPlacement.session_id == session_id,
    ).order_by(NineBoxPlacement.placed_at)).all()
    return [{"worker_id": p.worker_id, "box": f"{p.performance}×{p.potential}",
             "rationale": p.rationale, "actor": p.actor,
             "at": p.placed_at.isoformat()} for p in placements]


def current_box(session: Session, *, worker_id: str) -> NineBoxPlacement | None:
    return session.scalars(select(NineBoxPlacement).where(
        NineBoxPlacement.worker_id == worker_id,
    ).order_by(NineBoxPlacement.placed_at.desc())).first()
