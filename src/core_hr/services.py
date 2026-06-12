"""Core HR lifecycle services (Specs/01 §3). The only write paths for
employment data — everything goes through insert_temporal (Invariant #1).
"""
import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core_hr.models import (
    Assignment,
    Department,
    NationalId,
    Person,
    PersonName,
    Position,
    WorkEligibility,
    Worker,
)
from platform_core import temporal
from platform_core.audit import record_audit
from platform_core.crypto import encrypt_field
from rules_workflow.rules import evaluate, load_ruleset

ADULT_AGE_YEARS = 18

_transfer_rules = None
_fmla_rules = None


def _transfer_ruleset():
    global _transfer_rules
    if _transfer_rules is None:
        _transfer_rules = load_ruleset("transfer-pattern")
    return _transfer_rules


def _fmla_ruleset():
    global _fmla_rules
    if _fmla_rules is None:
        _fmla_rules = load_ruleset("fmla-eligibility")
    return _fmla_rules


class DuplicatePersonError(ValueError):
    pass


class PermitExpiryError(ValueError):
    pass


class DepartmentHasIncumbentsError(ValueError):
    pass


@dataclass
class HireResult:
    person: Person
    worker: Worker
    rehire: bool


def find_duplicate(session: Session, *, given_name: str, family_name: str,
                   date_of_birth: date, national_id_value: str | None = None) -> Person | None:
    """Duplicate check: national-ID last-four+type exact would be checked in a
    fuller build; locally we match fuzzy name+DOB (lowercased) per §3.1."""
    candidates = session.scalars(select(Person).where(Person.date_of_birth == date_of_birth)).all()
    for person in candidates:
        name = temporal.current_max(session, PersonName, person.person_id)
        if name is not None and (
            name.given_name.lower() == given_name.lower()
            and name.family_name.lower() == family_name.lower()
        ):
            return person
    return None


def hire(
    session: Session,
    *,
    given_name: str,
    family_name: str,
    date_of_birth: date,
    legal_entity: str,
    entity_country: str,
    hire_date: date,
    job_code: str,
    department_id: uuid.UUID | None = None,
    national_id: tuple[str, str] | None = None,  # (type, value) — synthetic only in tests
    worker_type: str = "employee",
    actor: str = "hr",
    source_channel: str = "ui",
    carried_flags: str | None = None,
) -> HireResult:
    existing = find_duplicate(session, given_name=given_name, family_name=family_name,
                              date_of_birth=date_of_birth)
    rehire = False
    if existing is not None:
        # Rehire path (§3.1): same human, new employment relationship,
        # original_hire_date bridged from the earliest prior worker.
        person = existing
        earliest = session.scalar(
            select(func.min(Worker.original_hire_date)).where(Worker.person_id == person.person_id)
        )
        original_hire_date = earliest or hire_date
        rehire = earliest is not None
    else:
        person = Person(date_of_birth=date_of_birth, primary_nationality=entity_country)
        session.add(person)
        session.flush()
        temporal.insert_temporal(
            session,
            PersonName(person_id=person.person_id, effective_date=hire_date,
                       action_code="HIR", given_name=given_name, family_name=family_name,
                       formatted_name=f"{given_name} {family_name}"),
            actor=actor, source_channel=source_channel,
        )
        original_hire_date = hire_date

    if national_id is not None:
        id_type, value = national_id
        session.add(NationalId(
            person_id=person.person_id, id_type=id_type,
            value_encrypted=encrypt_field(value), last_four=value[-4:],
        ))

    worker = Worker(
        person_id=person.person_id, legal_entity=legal_entity,
        entity_country=entity_country, worker_type=worker_type,
        hire_date=hire_date, original_hire_date=original_hire_date,
        carried_flags=carried_flags,
    )
    session.add(worker)
    session.flush()

    temporal.insert_temporal(
        session,
        Assignment(worker_id=worker.worker_id, effective_date=hire_date,
                   action_code="HIR", action_reason="new-hire" if not rehire else "rehire",
                   worker_status="active", job_code=job_code,
                   department_id=department_id, location_country=entity_country),
        actor=actor, source_channel=source_channel,
    )
    return HireResult(person=person, worker=worker, rehire=rehire)


def change_assignment(
    session: Session,
    worker: Worker,
    *,
    effective_date: date,
    action_code: str,
    actor: str,
    source_channel: str = "ui",
    action_reason: str | None = None,
    **changes,
) -> temporal.TemporalWriteResult:
    """New assignment row carrying forward unchanged fields (correction/retro
    semantics resolved by the temporal library). Blocks assignments extending
    past work-permit expiry (§2.1 blocking rule)."""
    current = temporal.current_max(session, Assignment, worker.worker_id)
    if current is None:
        raise ValueError("worker has no assignment history")

    new_country = changes.get("location_country", current.location_country)
    permit = session.scalars(select(WorkEligibility).where(
        WorkEligibility.person_id == worker.person_id,
        WorkEligibility.country == new_country,
    )).first()
    if permit is not None and permit.expiry_date is not None and effective_date > permit.expiry_date:
        raise PermitExpiryError(
            f"assignment effective {effective_date} exceeds work-permit expiry {permit.expiry_date}"
        )

    row = Assignment(
        worker_id=worker.worker_id, effective_date=effective_date,
        action_code=action_code, action_reason=action_reason,
        worker_status=changes.get("worker_status", current.worker_status),
        job_code=changes.get("job_code", current.job_code),
        department_id=changes.get("department_id", current.department_id),
        position_id=changes.get("position_id", current.position_id),
        manager_worker_id=changes.get("manager_worker_id", current.manager_worker_id),
        location_country=new_country,
        fte=changes.get("fte", current.fte),
        pay_group=changes.get("pay_group", current.pay_group),
    )
    return temporal.insert_temporal(session, row, actor=actor, source_channel=source_channel)


def correct_hire_date(
    session: Session, worker: Worker, *, corrected_hire_date: date,
    first_payroll_ran: bool, actor: str,
) -> dict:
    """Retro hire-date correction (register row). The original row is never
    rewritten; a retro/correction row is inserted and, when payroll already
    ran, the result is flagged for payroll recalculation (Module 03 consumes)."""
    result = change_assignment(
        session, worker,
        effective_date=corrected_hire_date,
        action_code="HIR", action_reason="hire-date-correction",
        actor=actor, source_channel="ui",
    )
    worker.hire_date = corrected_hire_date
    session.flush()
    needs_recalc = first_payroll_ran
    if needs_recalc:
        record_audit(
            session, actor=actor, action="insert",
            entity_ref=f"core.worker:{worker.worker_id}",
            after={"flag": "payroll-recalc-required", "corrected_hire_date": str(corrected_hire_date)},
            sensitivity_tier="T1", source_channel="ui", correlation_id=uuid.uuid4(),
        )
    return {"temporal_action": result.action, "payroll_recalc_required": needs_recalc}


def transfer(
    session: Session, worker: Worker, *,
    effective_date: date, to_entity: str, to_entity_country: str,
    job_code: str | None = None, actor: str = "hr",
) -> dict:
    """Cross-entity transfer (§3.2). The country rule decides the pattern
    (DE: terminate+rehire; default: continuous) — the caller sees ONE transfer."""
    pattern = evaluate(
        _transfer_ruleset(),
        {"from_country": worker.entity_country, "to_country": to_entity_country,
         "cross_entity": to_entity != worker.legal_entity},
        effective_date,
    ).output

    if pattern == "continuous":
        change_assignment(session, worker, effective_date=effective_date,
                          action_code="XFR", action_reason="transfer",
                          location_country=to_entity_country, actor=actor,
                          **({"job_code": job_code} if job_code else {}))
        worker.legal_entity = to_entity
        worker.entity_country = to_entity_country
        session.flush()
        return {"pattern": "continuous", "worker_id": worker.worker_id}

    # terminate + rehire pattern: old relationship ends, a new Worker begins,
    # original_hire_date bridges.
    change_assignment(session, worker, effective_date=effective_date,
                      action_code="TER", action_reason="transfer-out",
                      worker_status="terminated", actor=actor)
    current = temporal.current_max(session, Assignment, worker.worker_id)
    new_worker = Worker(
        person_id=worker.person_id, legal_entity=to_entity,
        entity_country=to_entity_country, worker_type=worker.worker_type,
        hire_date=effective_date, original_hire_date=worker.original_hire_date,
    )
    session.add(new_worker)
    session.flush()
    temporal.insert_temporal(
        session,
        Assignment(worker_id=new_worker.worker_id, effective_date=effective_date,
                   action_code="HIR", action_reason="transfer-in",
                   worker_status="active", job_code=job_code or current.job_code,
                   location_country=to_entity_country),
        actor=actor, source_channel="ui",
    )
    return {"pattern": "terminate-rehire", "worker_id": new_worker.worker_id,
            "prior_worker_id": worker.worker_id}


def terminate(
    session: Session, worker: Worker, *, effective_date: date, reason: str,
    actor: str, scim=None,
) -> dict:
    change_assignment(session, worker, effective_date=effective_date,
                      action_code="TER", action_reason=reason,
                      worker_status="terminated", actor=actor)
    jml_result = None
    if scim is not None:
        from datetime import datetime, time, timezone
        from integration_hub.jml import process_action
        jml_result = process_action(
            session, scim, worker_id=str(worker.worker_id), action_type="disable",
            effective_ts=datetime.combine(effective_date, time(0, 0), tzinfo=timezone.utc),
        )
    return {"terminated": True, "jml": jml_result}


def fmla_eligible(*, tenure_months: int, hours_last_12mo: int, as_of: date) -> bool:
    """FMLA eligibility auto-check (§3.3): 12 months tenure AND 1,250 hours."""
    return evaluate(
        _fmla_ruleset(),
        {"tenure_months": tenure_months, "hours_last_12mo": hours_last_12mo},
        as_of,
    ).output == "eligible"


def active_incumbents(session: Session, department_id: uuid.UUID, as_of: date) -> int:
    """Workers whose as-of assignment sits in this department and is active."""
    worker_ids = session.scalars(
        select(Assignment.worker_id).where(Assignment.department_id == department_id).distinct()
    ).all()
    count = 0
    for worker_id in worker_ids:
        row = temporal.as_of(session, Assignment, worker_id, as_of)
        if row is not None and row.department_id == department_id and row.worker_status == "active":
            count += 1
    return count


def inactivate_department(session: Session, department: Department, *, as_of: date) -> None:
    """Blocked while incumbents remain (register row) — guided re-home first."""
    incumbents = active_incumbents(session, department.department_id, as_of)
    if incumbents > 0:
        raise DepartmentHasIncumbentsError(
            f"department has {incumbents} active incumbent(s); re-home them first"
        )
    department.status = "inactive"
    session.flush()


def position_openings(session: Session, position: Position, as_of: date) -> int:
    """Vacancy logic (§2.3): headcount budget minus active incumbents."""
    worker_ids = session.scalars(
        select(Assignment.worker_id).where(Assignment.position_id == position.position_id).distinct()
    ).all()
    incumbents = 0
    for worker_id in worker_ids:
        row = temporal.as_of(session, Assignment, worker_id, as_of)
        if row is not None and row.position_id == position.position_id and row.worker_status == "active":
            incumbents += 1
    return position.headcount_budget - incumbents


def is_minor(person: Person, as_of: date) -> bool:
    """Feeds Module 02 hour-restriction rules (register row, partial here)."""
    years = as_of.year - person.date_of_birth.year - (
        (as_of.month, as_of.day) < (person.date_of_birth.month, person.date_of_birth.day)
    )
    return years < ADULT_AGE_YEARS
