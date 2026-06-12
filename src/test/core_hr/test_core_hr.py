"""Core HR tests (Specs/01): lifecycle services + §6 edge-case register."""
import uuid
from datetime import date

import pytest

from core_hr import services
from core_hr.models import Assignment, Department, Person, PersonName, Position
from platform_core import temporal
from platform_core.conformance import TemporalConformanceSuite
from platform_core.crypto import decrypt_field


def _hire(session, given="Aiko", family="Tanaka", dob=date(1990, 4, 1),
          entity="meridian-us", country="US", hire_date=date(2026, 3, 1), **kw):
    return services.hire(
        session, given_name=given, family_name=family, date_of_birth=dob,
        legal_entity=entity, entity_country=country, hire_date=hire_date,
        job_code="ENG-2", **kw,
    )


# ---------- Temporal conformance for Core HR's effective-dated entities ----------

class TestAssignmentConformance(TemporalConformanceSuite):
    @pytest.fixture
    def temporal_model(self):
        return Assignment

    @pytest.fixture
    def make_row(self):
        def _make(entity_id, effective_date, **overrides):
            defaults = dict(worker_id=entity_id, effective_date=effective_date,
                            action_code="DTA", worker_status="active",
                            job_code="ENG-2", location_country="US")
            defaults.update(overrides)
            return Assignment(**defaults)
        return _make


class TestPersonNameConformance(TemporalConformanceSuite):
    @pytest.fixture
    def temporal_model(self):
        return PersonName

    @pytest.fixture
    def make_row(self):
        def _make(entity_id, effective_date, **overrides):
            defaults = dict(person_id=entity_id, effective_date=effective_date,
                            action_code="NAM", given_name="Synthetic",
                            family_name="Person", formatted_name="Synthetic Person")
            defaults.update(overrides)
            return PersonName(**defaults)
        return _make


# ---------- Lifecycle ----------

def test_hire_creates_person_name_worker_assignment(session):
    result = _hire(session, national_id=("SSN", "078-05-1120"))
    session.commit()
    assert not result.rehire
    row = temporal.as_of(session, Assignment, result.worker.worker_id, date(2026, 3, 1))
    assert row.action_code == "HIR" and row.worker_status == "active"


def test_national_id_encrypted_and_masked(session):
    result = _hire(session, national_id=("SSN", "078-05-1120"))
    session.commit()
    from sqlalchemy import select
    from core_hr.models import NationalId
    nid = session.scalars(select(NationalId).where(
        NationalId.person_id == result.person.person_id)).one()
    assert nid.last_four == "1120"
    assert "078" not in nid.value_encrypted          # ciphertext only at rest
    assert decrypt_field(nid.value_encrypted) == "078-05-1120"


def test_CORE_concurrent_multi_country_jobs(session):
    """Register row / CORE-3: one person, two concurrent employment
    relationships in different countries — one Person record, two Workers."""
    first = _hire(session)
    second = _hire(session, entity="meridian-de", country="DE",
                   hire_date=date(2026, 5, 1))
    session.commit()

    assert first.person.person_id == second.person.person_id  # deduped human
    assert first.worker.worker_id != second.worker.worker_id
    a1 = temporal.as_of(session, Assignment, first.worker.worker_id, date(2026, 6, 1))
    a2 = temporal.as_of(session, Assignment, second.worker.worker_id, date(2026, 6, 1))
    assert a1.worker_status == a2.worker_status == "active"
    assert {a1.location_country, a2.location_country} == {"US", "DE"}


def test_CORE_rehire_bridges_original_hire_date(session, scim):
    """Register row: rehire bridges original_hire_date and carries prior flags
    (e.g., negative PTO balance) onto the new relationship."""
    first = _hire(session)
    services.terminate(session, first.worker, effective_date=date(2026, 4, 30),
                       reason="resignation", actor="hr", scim=scim)
    rehired = _hire(session, hire_date=date(2026, 9, 1),
                    carried_flags="negative-pto-balance")
    session.commit()

    assert rehired.rehire
    assert rehired.worker.original_hire_date == date(2026, 3, 1)  # bridged
    assert rehired.worker.hire_date == date(2026, 9, 1)
    assert rehired.worker.carried_flags == "negative-pto-balance"


def test_CORE_retro_hire_date_correction_after_payroll(session):
    """Register row: retro hire-date correction after first payroll — history
    is appended (retro action), never rewritten, and payroll recalc is flagged."""
    result = _hire(session)
    outcome = services.correct_hire_date(
        session, result.worker, corrected_hire_date=date(2026, 2, 15),
        first_payroll_ran=True, actor="hr",
    )
    session.commit()

    assert outcome["temporal_action"] == temporal.ACTION_RETRO
    assert outcome["payroll_recalc_required"]
    original = temporal.as_of(session, Assignment, result.worker.worker_id, date(2026, 3, 1))
    assert original is not None  # original row still in history


def test_CORE_overlapping_changes_resolve_by_sequence(session):
    """Register row: future-dated promotion overlapping a pending transfer on
    the same effective date — sequence resolves; latest sequence wins."""
    result = _hire(session)
    day = date(2026, 8, 1)
    services.change_assignment(session, result.worker, effective_date=day,
                               action_code="XFR", department_id=uuid.uuid4(), actor="hr")
    services.change_assignment(session, result.worker, effective_date=day,
                               action_code="PRO", job_code="ENG-3", actor="hr")
    session.commit()

    winner = temporal.as_of(session, Assignment, result.worker.worker_id, day)
    assert winner.effective_sequence == 1
    assert winner.action_code == "PRO" and winner.job_code == "ENG-3"


def test_CORE_department_inactivation_blocked(session):
    """Register row: inactivation blocked while active incumbents remain."""
    dept = Department(name="Assembly")
    session.add(dept)
    session.flush()
    result = _hire(session, department_id=dept.department_id)
    session.commit()

    with pytest.raises(services.DepartmentHasIncumbentsError, match="re-home"):
        services.inactivate_department(session, dept, as_of=date(2026, 6, 1))

    services.terminate(session, result.worker, effective_date=date(2026, 6, 15),
                       reason="resignation", actor="hr")
    services.inactivate_department(session, dept, as_of=date(2026, 7, 1))
    assert dept.status == "inactive"


def test_CORE_assignment_blocked_past_permit_expiry(session):
    """§2.1 blocking rule: cannot extend an assignment past work-permit expiry."""
    from core_hr.models import WorkEligibility
    result = _hire(session)
    session.add(WorkEligibility(person_id=result.person.person_id, country="US",
                                document_type="work-permit",
                                expiry_date=date(2026, 12, 31)))
    session.flush()

    with pytest.raises(services.PermitExpiryError, match="expiry"):
        services.change_assignment(session, result.worker,
                                   effective_date=date(2027, 1, 15),
                                   action_code="EXT", actor="hr")


def test_transfer_continuous_vs_terminate_rehire(session):
    """§3.2: country rule decides the pattern; the caller sees one transfer."""
    us = _hire(session)
    moved = services.transfer(session, us.worker, effective_date=date(2026, 6, 1),
                              to_entity="meridian-us-2", to_entity_country="US")
    assert moved["pattern"] == "continuous"

    de = _hire(session, given="Jonas", family="Weber", dob=date(1988, 2, 2),
               entity="meridian-de", country="DE")
    moved_de = services.transfer(session, de.worker, effective_date=date(2026, 7, 1),
                                 to_entity="meridian-de-2", to_entity_country="DE")
    session.commit()
    assert moved_de["pattern"] == "terminate-rehire"
    old = temporal.current_max(session, Assignment, de.worker.worker_id)
    assert old.worker_status == "terminated"
    new = temporal.current_max(session, Assignment, moved_de["worker_id"])
    assert new.worker_status == "active"
    from sqlalchemy import select
    from core_hr.models import Worker
    new_worker = session.get(Worker, moved_de["worker_id"])
    assert new_worker.original_hire_date == de.worker.original_hire_date  # bridged


def test_termination_triggers_jml_disable(session, scim):
    result = _hire(session)
    outcome = services.terminate(session, result.worker, effective_date=date(2026, 6, 30),
                                 reason="involuntary", actor="hr", scim=scim)
    session.commit()
    assert outcome["jml"].applied
    assert scim.calls == [("disable", str(result.worker.worker_id))]


def test_fmla_eligibility_rule():
    assert services.fmla_eligible(tenure_months=14, hours_last_12mo=1300, as_of=date(2026, 6, 1))
    assert not services.fmla_eligible(tenure_months=14, hours_last_12mo=1200, as_of=date(2026, 6, 1))
    assert not services.fmla_eligible(tenure_months=11, hours_last_12mo=1300, as_of=date(2026, 6, 1))


def test_position_vacancy_logic(session):
    dept = Department(name="Eng")
    session.add(dept)
    session.flush()
    position = Position(job_code="ENG-2", department_id=dept.department_id, headcount_budget=2)
    session.add(position)
    session.flush()

    result = _hire(session)
    services.change_assignment(session, result.worker, effective_date=date(2026, 4, 1),
                               action_code="POS", position_id=position.position_id, actor="hr")
    session.commit()
    assert services.position_openings(session, position, date(2026, 5, 1)) == 1


def test_minor_flag():
    minor = Person(date_of_birth=date(2010, 7, 1))
    adult = Person(date_of_birth=date(2000, 7, 1))
    assert services.is_minor(minor, date(2026, 6, 10))
    assert not services.is_minor(adult, date(2026, 6, 10))
