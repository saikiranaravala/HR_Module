"""Key positions & slates (SUCC-1): criticality rubric, readiness, staleness,
concentration risk, termination gap alerts, reorg re-homing."""
import uuid
from datetime import date, timedelta
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.audit import record_audit
from succession.models import KeyPosition, SlateEntry

CONFIG_DIR = Path(__file__).resolve().parent / "config"

READINESS = {"now", "1-2y", "3y+"}
STALENESS_MONTHS = 12
CONCENTRATION_THRESHOLD = 3


def load_rubric(path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "criticality.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["weights"]


def retirement_band(*, age: int, service_years: int) -> str:
    """Eligibility surfaces as a BAND, never a date (§2)."""
    score = age + service_years
    if score >= 85:
        return "<3y"
    if score >= 75:
        return "3-5y"
    return ">5y"


def designate_key_position(
    session: Session, *, title: str, incumbent_id: str | None, division_path: str,
    impact: int, scarcity: int, ramp: int, incumbent_age: int | None = None,
    incumbent_service: int | None = None, rubric: dict | None = None,
) -> KeyPosition:
    rubric = rubric or load_rubric()
    total = (impact * rubric["impact"] + scarcity * rubric["scarcity"]
             + ramp * rubric["ramp"])
    band = None
    if incumbent_age is not None and incumbent_service is not None:
        band = retirement_band(age=incumbent_age, service_years=incumbent_service)
    position = KeyPosition(
        title=title, incumbent_id=incumbent_id, division_path=division_path,
        criticality={"impact": impact, "scarcity": scarcity, "ramp": ramp, "total": total},
        retirement_band=band,
    )
    session.add(position)
    session.flush()
    return position


def add_successor(
    session: Session, position: KeyPosition, *, successor_id: str, readiness: str,
    rationale: str, on: date, emergency: bool = False,
) -> SlateEntry:
    if readiness not in READINESS:
        raise ValueError(f"readiness must be one of {sorted(READINESS)}")
    if not rationale.strip():
        raise ValueError("readiness rationale is mandatory")
    entry = SlateEntry(position_id=position.position_id, successor_id=successor_id,
                       readiness=readiness, rationale=rationale,
                       emergency=emergency, last_validated=on)
    session.add(entry)
    session.flush()
    return entry


def stale_entries(session: Session, *, as_of: date) -> list[SlateEntry]:
    cutoff = as_of - timedelta(days=STALENESS_MONTHS * 30)
    return session.scalars(select(SlateEntry).where(
        SlateEntry.status == "active",
        SlateEntry.last_validated <= cutoff,
    )).all()


def concentration_risks(session: Session) -> list[dict]:
    """One person on many slates = single point of failure (§2)."""
    entries = session.scalars(select(SlateEntry).where(
        SlateEntry.status == "active")).all()
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.successor_id] = counts.get(entry.successor_id, 0) + 1
    return [{"worker_id": worker, "slate_count": count, "flag": "concentration-risk"}
            for worker, count in sorted(counts.items()) if count >= CONCENTRATION_THRESHOLD]


def successor_terminated(session: Session, *, worker_id: str, actor: str) -> list[dict]:
    """Register row: terminated successor → entries flip to gap, a review task
    is raised per affected slate, and the event is audited."""
    entries = session.scalars(select(SlateEntry).where(
        SlateEntry.successor_id == worker_id,
        SlateEntry.status == "active",
    )).all()
    tasks = []
    for entry in entries:
        entry.status = "gap"
        tasks.append({"task": "slate-review", "position_id": str(entry.position_id),
                      "reason": f"successor {worker_id} terminated"})
        record_audit(
            session, actor=actor, action="update",
            entity_ref=f"succession.slate_entry:{entry.entry_id}",
            after={"status": "gap", "reason": "successor-terminated"},
            sensitivity_tier="T3", source_channel="succession",
            correlation_id=uuid.uuid4(),
        )
    session.flush()
    return tasks


def rehome_division(session: Session, *, old_path: str, new_paths: dict[str, str],
                    actor: str) -> list[dict]:
    """Register row: divisional reorg — positions re-home to mapped divisions,
    slates stay intact, and each move raises a review task (continuity is a
    human validation, not an assumption)."""
    from platform_core.orgpath import normalize, within
    positions = [p for p in session.scalars(select(KeyPosition)).all()
                 if within(p.division_path, old_path)]
    old_norm = normalize(old_path)
    tasks = []
    for position in positions:
        suffix = normalize(position.division_path)[len(old_norm):]
        target = new_paths.get(position.title) or next(iter(new_paths.values()))
        position.division_path = target + suffix
        tasks.append({"task": "post-reorg-slate-review",
                      "position_id": str(position.position_id),
                      "new_division": position.division_path})
    session.flush()
    if positions:
        record_audit(
            session, actor=actor, action="update",
            entity_ref=f"succession.key_position:reorg:{old_path}",
            after={"moved": len(positions), "targets": sorted(set(new_paths.values()))},
            sensitivity_tier="T3", source_channel="succession",
            correlation_id=uuid.uuid4(),
        )
    return tasks
