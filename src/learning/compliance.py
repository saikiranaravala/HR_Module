"""Compliance training engine (LEARN-2, P0): jurisdiction packs, population
rules, deadlines/recurrence, escalation ladder, clock pause, batch extension,
policy-gated consequence flags."""
from datetime import date, timedelta
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from learning.models import Assignment, CompletionRecord
from platform_core.dates import add_months

CONFIG_DIR = Path(__file__).resolve().parent / "config"


def load_packs(path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "jurisdiction_packs.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["requirements"]


def applicable_requirements(worker: dict, packs: dict | None = None) -> list[str]:
    """Population rule evaluation: location / role flags / worker type — all
    pack attributes, no code branches per country."""
    packs = packs or load_packs()
    keys = []
    for key, req in packs.items():
        rule = req["population"]
        if rule.get("locations") and worker["location"] not in rule["locations"]:
            continue
        if rule.get("supervisor") is not None and worker.get("supervisor", False) != rule["supervisor"]:
            continue
        if rule.get("role_flags") and not set(rule["role_flags"]) & set(worker.get("role_flags", [])):
            continue
        if worker.get("worker_type", "employee") not in req.get("applies_to", ["employee"]):
            continue
        keys.append(key)
    return keys


def assign_requirement(
    session: Session, *, worker: dict, requirement_key: str, trigger_date: date,
    packs: dict | None = None, content_version: int = 1,
) -> Assignment:
    packs = packs or load_packs()
    req = packs[requirement_key]
    lightweight = worker.get("worker_type") == "contingent"
    assignment = Assignment(
        worker_id=worker["worker_id"], requirement_key=requirement_key,
        content_key=req["content_key"], content_version=content_version,
        due_on=trigger_date + timedelta(days=req["initial_deadline_days"]),
        lightweight=lightweight,
    )
    session.add(assignment)
    session.flush()
    return assignment


def next_due(req: dict, *, completed_on: date) -> date:
    """Recurrence: rolling anniversary from completion, or pack fixed date."""
    recurrence = req["recurrence"]
    if recurrence["type"] == "rolling-anniversary":
        return add_months(completed_on, recurrence["months"])
    if recurrence["type"] == "fixed-date":
        month, day = (int(x) for x in recurrence["date"].split("-"))
        candidate = date(completed_on.year, month, day)
        return candidate if candidate > completed_on else date(completed_on.year + 1, month, day)
    raise ValueError(f"unknown recurrence type {recurrence['type']}")


def escalation_level(assignment: Assignment, *, today: date,
                     ladder: dict | None = None) -> str | None:
    """T-14 worker → T-7 manager → overdue HR/compliance (pack-configurable)."""
    ladder = ladder or {"worker": 14, "manager": 7, "compliance": 0}
    days_left = (assignment.due_on - today).days
    if assignment.status == "completed":
        return None
    if days_left < ladder["compliance"]:
        return "compliance-officer"
    if days_left <= ladder["manager"]:
        return "manager"
    if days_left <= ladder["worker"]:
        return "worker"
    return None


def pause_for_leave(session: Session, assignment: Assignment, *, start: date) -> Assignment:
    """Register row: leave pauses the compliance clock — explicit pause window,
    never a silent due-date edit."""
    assignment.paused_on = start
    session.flush()
    return assignment


def resume_from_leave(session: Session, assignment: Assignment, *, end: date) -> Assignment:
    if assignment.paused_on is None:
        raise ValueError("assignment is not paused")
    paused_days = (end - assignment.paused_on).days
    assignment.due_on = assignment.due_on + timedelta(days=paused_days)
    assignment.pause_log = (assignment.pause_log or []) + [{
        "paused_on": assignment.paused_on.isoformat(), "resumed_on": end.isoformat(),
        "days_credited": paused_days,
    }]
    assignment.paused_on = None
    session.flush()
    return assignment


def batch_extend(session: Session, *, requirement_key: str, days: int,
                 evidence_note: str, due_before: date) -> int:
    """Register row: vendor outage in deadline week — batch extension with a
    mandatory regulator-facing evidence note on every touched assignment."""
    if not evidence_note.strip():
        raise ValueError("evidence note is mandatory for batch extensions")
    assignments = session.scalars(select(Assignment).where(
        Assignment.requirement_key == requirement_key,
        Assignment.status.in_(["assigned", "in-progress"]),
        Assignment.due_on <= due_before,
    )).all()
    for assignment in assignments:
        assignment.due_on = assignment.due_on + timedelta(days=days)
        assignment.extension_note = evidence_note
    session.flush()
    return len(assignments)


def consequence_flags(session: Session, *, worker_id: str, today: date,
                      packs: dict | None = None) -> list[dict]:
    """Policy-gated consequence hooks: Learning EMITS flags (safety
    assignment-block candidates); the policy layer decides — never blocked here."""
    packs = packs or load_packs()
    flags = []
    overdue = session.scalars(select(Assignment).where(
        Assignment.worker_id == worker_id,
        Assignment.status.in_(["assigned", "in-progress"]),
        Assignment.due_on < today,
        Assignment.paused_on.is_(None),
    )).all()
    for assignment in overdue:
        req = packs.get(assignment.requirement_key, {})
        if req.get("consequence") == "assignment-block":
            flags.append({"worker_id": worker_id, "flag": "safety-training-lapsed",
                          "requirement": assignment.requirement_key})
    return flags
