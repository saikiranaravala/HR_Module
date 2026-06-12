"""Learning tests (Specs/08): compliance engine, versioned content/evidence,
SCORM resilience, certs, and the §8 edge-case register."""
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from learning import catalog, certs, compliance, scorm

PACKS = compliance.load_packs()


# --- Compliance engine (LEARN-2, P0) ----------------------------------------------

def test_population_rules_from_packs():
    ca_supervisor = {"worker_id": "w-1", "location": "US-CA", "supervisor": True,
                     "worker_type": "employee"}
    ny_worker = {"worker_id": "w-2", "location": "US-NY", "supervisor": False,
                 "worker_type": "employee"}
    de_worker = {"worker_id": "w-3", "location": "DE", "worker_type": "employee"}
    energy_tech = {"worker_id": "w-4", "location": "US-TX",
                   "role_flags": ["energy-control"], "worker_type": "employee"}

    assert compliance.applicable_requirements(ca_supervisor, PACKS) == ["us-ca-harassment-supervisor"]
    assert compliance.applicable_requirements(ny_worker, PACKS) == ["us-ny-harassment"]
    assert compliance.applicable_requirements(de_worker, PACKS) == []
    assert compliance.applicable_requirements(energy_tech, PACKS) == ["osha-lockout-tagout"]


def test_deadline_recurrence_and_escalation(session):
    worker = {"worker_id": "w-1", "location": "US-CA", "supervisor": True}
    assignment = compliance.assign_requirement(
        session, worker=worker, requirement_key="us-ca-harassment-supervisor",
        trigger_date=date(2026, 1, 1), packs=PACKS,
    )
    assert assignment.due_on == date(2026, 6, 30)  # +180 days

    req = PACKS["us-ca-harassment-supervisor"]
    # rolling anniversary: 24 calendar months, not 720 days
    assert compliance.next_due(req, completed_on=date(2026, 5, 1)) == date(2028, 5, 1)
    # NY fixed-date annual
    assert compliance.next_due(PACKS["us-ny-harassment"],
                               completed_on=date(2026, 5, 1)) == date(2026, 12, 31)

    assert compliance.escalation_level(assignment, today=date(2026, 6, 1)) is None
    assert compliance.escalation_level(assignment, today=date(2026, 6, 17)) == "worker"
    assert compliance.escalation_level(assignment, today=date(2026, 6, 25)) == "manager"
    assert compliance.escalation_level(assignment, today=date(2026, 7, 5)) == "compliance-officer"


def test_consequence_flag_policy_gated(session):
    worker = {"worker_id": "w-4", "location": "US-TX", "role_flags": ["energy-control"]}
    compliance.assign_requirement(session, worker=worker,
                                  requirement_key="osha-lockout-tagout",
                                  trigger_date=date(2026, 1, 1), packs=PACKS)
    flags = compliance.consequence_flags(session, worker_id="w-4",
                                         today=date(2026, 3, 1), packs=PACKS)
    assert flags == [{"worker_id": "w-4", "flag": "safety-training-lapsed",
                      "requirement": "osha-lockout-tagout"}]


# --- Register rows ------------------------------------------------------------------

def test_LEARN_leave_pauses_compliance_clock(session):
    """Register row: leave pauses the clock; due date shifts by exactly the
    paused days, with the pause window logged."""
    worker = {"worker_id": "w-1", "location": "US-NY"}
    assignment = compliance.assign_requirement(
        session, worker=worker, requirement_key="us-ny-harassment",
        trigger_date=date(2026, 1, 1), packs=PACKS)
    original_due = assignment.due_on

    compliance.pause_for_leave(session, assignment, start=date(2026, 2, 1))
    assert compliance.consequence_flags(session, worker_id="w-1",
                                        today=date(2026, 12, 1), packs=PACKS) == []
    compliance.resume_from_leave(session, assignment, end=date(2026, 3, 15))
    assert assignment.due_on == original_due.replace(month=original_due.month) + (date(2026, 3, 15) - date(2026, 2, 1))
    assert assignment.pause_log[0]["days_credited"] == 42


def test_LEARN_vendor_outage_batch_extension(session):
    """Register row: outage in deadline week — batch extension with mandatory
    evidence note on every assignment."""
    for i in range(3):
        compliance.assign_requirement(
            session, worker={"worker_id": f"w-{i}", "location": "US-NY"},
            requirement_key="us-ny-harassment", trigger_date=date(2026, 1, 1),
            packs=PACKS)
    with pytest.raises(ValueError, match="evidence note"):
        compliance.batch_extend(session, requirement_key="us-ny-harassment",
                                days=7, evidence_note="  ", due_before=date(2026, 4, 15))
    touched = compliance.batch_extend(
        session, requirement_key="us-ny-harassment", days=7,
        evidence_note="vendor outage 2026-03-28..30, ticket VND-112",
        due_before=date(2026, 4, 15),
    )
    assert touched == 3


def test_LEARN_scorm_suspend_corruption_fallback(session):
    """Register row: corrupted suspend data → fallback resume, attempt protected."""
    worker = {"worker_id": "w-1", "location": "US-NY"}
    assignment = compliance.assign_requirement(
        session, worker=worker, requirement_key="us-ny-harassment",
        trigger_date=date(2026, 1, 1), packs=PACKS)
    scorm.start_attempt(session, assignment)
    scorm.save_suspend(session, assignment, data="lesson=3;score=80")
    assert scorm.resume(session, assignment)["data"] == "lesson=3;score=80"

    assignment.suspend_data = "lesson=3;sc"  # corruption
    outcome = scorm.resume(session, assignment)
    assert outcome["fallback"] and outcome["attempt_protected"]
    assert assignment.attempts == 1  # not incremented by the corruption


def test_LEARN_acquired_transcript_import(session):
    """Register row: acquisition import — compliance-relevant history is the
    guaranteed minimum; the rest is reported, not silently dropped."""
    outcome = catalog.import_transcripts(
        session,
        rows=[
            {"worker_id": "acq-1", "requirement_key": "us-ny-harassment",
             "completed_at": datetime(2025, 11, 1, tzinfo=timezone.utc), "score": 95},
            {"worker_id": "acq-1", "requirement_key": "leadership-101",
             "completed_at": datetime(2025, 5, 1, tzinfo=timezone.utc)},
        ],
        compliance_keys={"us-ny-harassment", "osha-lockout-tagout"},
    )
    assert outcome["imported_compliance_records"] == 1
    assert outcome["skipped_non_compliance"] == ["leadership-101"]
    records = catalog.transcript(session, "acq-1")
    assert len(records) == 1 and records[0].source == "import"


def test_LEARN_contractor_lightweight_scope(session):
    """Register row: contractors get only requirements whose pack includes
    contingent workers, on lightweight records."""
    contractor = {"worker_id": "c-1", "location": "US-CA", "supervisor": False,
                  "worker_type": "contingent"}
    applicable = compliance.applicable_requirements(contractor, PACKS)
    assert applicable == ["us-ca-harassment-nonsupervisor"]  # supervisor course N/A

    assignment = compliance.assign_requirement(
        session, worker=contractor, requirement_key=applicable[0],
        trigger_date=date(2026, 1, 1), packs=PACKS)
    assert assignment.lightweight is True


# --- Catalog & evidence (LEARN-1) -----------------------------------------------------

def test_version_pinning_and_supersede_policies(session):
    catalog.publish_version(session, content_key="harassment-prevention-ny",
                            title="NY Harassment v1", supersede_policy="finish-old")
    worker = {"worker_id": "w-1", "location": "US-NY"}
    assignment = compliance.assign_requirement(
        session, worker=worker, requirement_key="us-ny-harassment",
        trigger_date=date(2026, 1, 1), packs=PACKS, content_version=1)
    scorm.start_attempt(session, assignment)

    # finish-old: the in-progress learner keeps v1
    catalog.publish_version(session, content_key="harassment-prevention-ny",
                            title="NY Harassment v2", supersede_policy="finish-old")
    assert assignment.content_version == 1
    record = catalog.record_completion(session, assignment, score=92)
    assert record.content_version == 1  # pinned: "which version did they take"

    # restart: in-progress learners re-baseline to the new version
    a2 = compliance.assign_requirement(
        session, worker={"worker_id": "w-2", "location": "US-NY"},
        requirement_key="us-ny-harassment", trigger_date=date(2026, 1, 1),
        packs=PACKS, content_version=2)
    scorm.start_attempt(session, a2)
    catalog.publish_version(session, content_key="harassment-prevention-ny",
                            title="NY Harassment v3", supersede_policy="restart")
    session.refresh(a2)
    assert (a2.status, a2.content_version) == ("assigned", 3)


def test_completion_records_immutable(session):
    worker = {"worker_id": "w-1", "location": "US-NY"}
    assignment = compliance.assign_requirement(
        session, worker=worker, requirement_key="us-ny-harassment",
        trigger_date=date(2026, 1, 1), packs=PACKS)
    record = catalog.record_completion(session, assignment, score=90)
    with pytest.raises(ProgrammingError, match="immutable"):
        with session.begin_nested():
            session.execute(text(
                "UPDATE learning.completion_record SET score = 100 "
                "WHERE completion_id = :cid"), {"cid": record.completion_id})


def test_equivalency_requires_evidence_and_approver(session):
    record = catalog.record_equivalency(
        session, worker_id="w-1", requirement_key="osha-lockout-tagout",
        content_key="external-osha-cert", evidence_ref="doc://cert-123",
        approved_by="compliance-officer-1",
    )
    assert record.source == "equivalency" and record.approved_by


# --- Certifications (LEARN-3) -----------------------------------------------------------

def test_cert_expiry_pipeline_and_lapse_flag(session):
    certs.register_certification(
        session, worker_id="w-1", cert_type="forklift-license", issuer="state",
        issued_on=date(2025, 7, 1), expires_on=date(2026, 7, 1), job_required=True)
    alerts = certs.expiry_alerts(session, today=date(2026, 4, 2))  # 90 days out
    assert alerts[0]["days_left"] == 90 and alerts[0]["recipients"] == ["worker", "manager"]

    flags = certs.lapsed_required_certs(session, today=date(2026, 7, 2))
    assert flags[0]["flag"] == "required-cert-lapsed"
    assert flags[0]["assignment_block_candidate"] is True
