"""Succession tests (Specs/09): slates, 9-box lineage, the confidentiality
model, and the §7 edge-case register."""
from datetime import date

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError

from platform_core.audit import AuditEvent
from platform_core.policy.engine import PolicyEngine, Subject
from succession import access, ninebox, slates
from succession.models import TalentProfile

POLICY = PolicyEngine()


def _position(session, incumbent="inc-1", division="/corp/emea/finance/"):
    return slates.designate_key_position(
        session, title="VP Finance EMEA", incumbent_id=incumbent,
        division_path=division, impact=5, scarcity=4, ramp=3,
        incumbent_age=58, incumbent_service=20,
    )


# --- Key positions & slates (SUCC-1) ------------------------------------------------

def test_criticality_rubric_and_retirement_band(session):
    position = _position(session)
    assert position.criticality["total"] == 5 * 3 + 4 * 2 + 3 * 1
    assert position.retirement_band == "3-5y"  # rule-of-85: 58+20=78
    assert slates.retirement_band(age=62, service_years=25) == "<3y"
    assert slates.retirement_band(age=40, service_years=10) == ">5y"
    assert slates.retirement_band(age=55, service_years=22) == "3-5y"


def test_slate_readiness_rationale_and_staleness(session):
    position = _position(session)
    with pytest.raises(ValueError, match="rationale"):
        slates.add_successor(session, position, successor_id="s-1",
                             readiness="now", rationale="  ", on=date(2026, 6, 1))
    entry = slates.add_successor(session, position, successor_id="s-1",
                                 readiness="now", rationale="ran region during gap",
                                 on=date(2025, 1, 1))
    assert slates.stale_entries(session, as_of=date(2026, 6, 1)) == [entry]


def test_concentration_risk_flag(session):
    for i in range(3):
        position = _position(session, incumbent=f"inc-{i}")
        slates.add_successor(session, position, successor_id="star-1",
                             readiness="1-2y", rationale="strong bench",
                             on=date(2026, 6, 1))
    risks = slates.concentration_risks(session)
    assert risks == [{"worker_id": "star-1", "slate_count": 3,
                      "flag": "concentration-risk"}]


# --- Register rows -------------------------------------------------------------------

def test_SUCC_successor_termination_gap_alert(session):
    """Register row: terminated successor → gap status + review task + audit."""
    p1, p2 = _position(session), _position(session, incumbent="inc-2")
    slates.add_successor(session, p1, successor_id="s-9", readiness="now",
                         rationale="r", on=date(2026, 6, 1))
    slates.add_successor(session, p2, successor_id="s-9", readiness="1-2y",
                         rationale="r", on=date(2026, 6, 1))
    tasks = slates.successor_terminated(session, worker_id="s-9", actor="core-hr-feed")
    assert len(tasks) == 2 and all(t["task"] == "slate-review" for t in tasks)


def test_SUCC_incumbent_never_sees_own_slate(session):
    """Register row: the incumbent cannot read their own slate even with the
    highest talent role — checked against CURRENT incumbent at read time, so
    inherited role changes can never leak it. The attempt is audit-logged."""
    position = _position(session, incumbent="exec-9")
    slates.add_successor(session, position, successor_id="s-1", readiness="now",
                         rationale="r", on=date(2026, 6, 1))

    incumbent_with_top_role = Subject("exec-9", ("exec-talent",))
    with pytest.raises(access.SlateAccessError, match="own position"):
        access.read_slate(session, POLICY, position, subject=incumbent_with_top_role)
    denies = session.scalars(select(AuditEvent).where(AuditEvent.action == "deny")).all()
    assert any("own slate" in (e.after or {}).get("detail", "") for e in denies)

    # …and a different exec-talent reader is fine (read-audited at T3)
    other = Subject("talent-1", ("exec-talent",))
    rows = access.read_slate(session, POLICY, position, subject=other)
    assert len(rows) == 1
    reads = session.scalars(select(AuditEvent).where(AuditEvent.action == "read")).all()
    assert any(e.sensitivity_tier == "T3" for e in reads)


def test_division_scoping_enforced(session):
    """SUCC-4: division HR sees own-division slates only — central policy scope."""
    emea = _position(session, division="/corp/emea/finance/")
    amer = _position(session, incumbent="inc-3", division="/corp/amer/finance/")
    division_hr = Subject("dhr-1", ("division-hr-talent-emea",))
    assert access.read_slate(session, POLICY, emea, subject=division_hr) == []  # empty slate, allowed
    with pytest.raises(access.SlateAccessError):
        access.read_slate(session, POLICY, amer, subject=division_hr)
    # managers/employees: no slate access at all
    with pytest.raises(access.SlateAccessError):
        access.read_slate(session, POLICY, emea, subject=Subject("mgr-1", ("manager",)))


def test_SUCC_reorg_rehomes_slates_with_review(session):
    """Register row: divisional reorg re-homes positions and raises review
    tasks — continuity is validated by humans, not assumed."""
    position = _position(session, division="/corp/emea/finance/")
    entry = slates.add_successor(session, position, successor_id="s-1",
                                 readiness="now", rationale="r", on=date(2026, 6, 1))
    tasks = slates.rehome_division(
        session, old_path="/corp/emea/",
        new_paths={"VP Finance EMEA": "/corp/europe/"}, actor="reorg-admin")
    assert position.division_path == "/corp/europe/finance/"
    assert tasks[0]["task"] == "post-reorg-slate-review"
    assert entry.status == "active"  # slate intact, review pending


def test_SUCC_acquisition_interim_profiles(session):
    """Register row: acquired executives get interim profiles with the limited
    history explicitly noted."""
    profile = TalentProfile(worker_id="acq-exec-1", interim=True,
                            history_note="acquired via Northwind close 2026-05; "
                                         "pre-close history not migrated")
    session.add(profile)
    session.flush()
    assert profile.interim and "pre-close" in profile.history_note


def test_SUCC_legal_discovery_privilege_workflow(session):
    """Register row: discovery gathers artifacts under privilege; release
    requires the named counsel."""
    hold = access.open_discovery(
        session, scope="worker:s-1", requested_by="legal-ops",
        counsel="counsel-jane", artifact_refs=["ninebox:sess-1", "slate:p-1"])
    assert hold.privileged and not hold.released
    with pytest.raises(access.PrivilegeError):
        access.release_discovery(session, hold, actor="legal-ops", counsel_approved=True)
    with pytest.raises(access.PrivilegeError):
        access.release_discovery(session, hold, actor="counsel-jane", counsel_approved=False)
    access.release_discovery(session, hold, actor="counsel-jane", counsel_approved=True)
    assert hold.released and hold.counsel_approved


# --- 9-box (SUCC-2) -------------------------------------------------------------------

def test_ninebox_rationale_and_immutable_lineage(session):
    with pytest.raises(ninebox.RationaleRequiredError):
        ninebox.place(session, worker_id="w-1", session_id="tr-1",
                      performance="exceeds", potential="high", rationale=None,
                      actor="facilitator")
    placement = ninebox.place(session, worker_id="w-1", session_id="tr-1",
                              performance="exceeds", potential="high",
                              rationale="scaled team through reorg",
                              actor="facilitator")
    with pytest.raises(ProgrammingError, match="immutable"):
        with session.begin_nested():
            session.execute(text(
                "UPDATE succession.ninebox_placement SET potential = 'medium' "
                "WHERE placement_id = :pid"), {"pid": placement.placement_id})

    # re-placement is a NEW row; minutes show the full lineage
    ninebox.place(session, worker_id="w-1", session_id="tr-1",
                  performance="exceeds", potential="medium",
                  rationale="calibrated against peer cohort", actor="facilitator")
    minutes = ninebox.session_minutes(session, session_id="tr-1")
    assert [m["box"] for m in minutes] == ["exceeds×high", "exceeds×medium"]
    assert ninebox.current_box(session, worker_id="w-1").potential == "medium"


# --- Aspirations privacy (SUCC-3 slice) ---------------------------------------------------

def test_aspirations_consent_wall(session):
    profile = TalentProfile(worker_id="w-1", aspirations="wants intl assignment",
                            aspirations_consent=False)
    session.add(profile)
    session.flush()
    assert access.aspirations_view(profile, viewer_is_manager=True) is None
    assert access.aspirations_view(profile, viewer_is_manager=False) == "wants intl assignment"
    profile.aspirations_consent = True
    assert access.aspirations_view(profile, viewer_is_manager=True) == "wants intl assignment"
