"""Recruiting tests (Specs/06): requisitions, pipeline guardrails, offers and
the zero-re-keying hire contract, GDPR, and the §9 edge-case register."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from ai_layer.gateway import AiGateway, MockProvider
from platform_core.policy.engine import PolicyEngine, Subject
from recruiting import gdpr, offers, pipeline, requisitions
from recruiting.models import Application, CandidateProfile, Offer, Requisition

POLICY = PolicyEngine()


def _apply(session, candidate, req, **kw):
    session.add(req)
    session.flush()
    return pipeline.apply_to_requisition(session, candidate=candidate, req=req,
                                         applied_on=date(2026, 6, 1), **kw)


# --- Requisitions (REC-1) -------------------------------------------------------

def test_posting_salary_disclosure_by_jurisdiction(session):
    position = {"position_id": "pos-1", "title": "Engineer", "grade": "G7",
                "country": "US", "range_min": 80000, "range_max": 120000}
    co = requisitions.create_requisition(session, position=position,
                                         headcount_type="net-new", jurisdiction="US-CO")
    tx = requisitions.create_requisition(session, position=position,
                                         headcount_type="backfill", jurisdiction="US-TX")
    assert "Salary range" in co.posting_text
    assert "Salary range" not in tx.posting_text
    assert requisitions.approval_chain(co) == ["hiring-manager", "finance", "hr-leadership"]
    assert requisitions.approval_chain(tx) == ["hiring-manager"]


# --- Pipeline guardrails (REC-3) ---------------------------------------------------

def test_knockout_is_deterministic():
    passed, _ = pipeline.knockout_check({"work_authorization": True,
                                         "has_required_license": True})
    assert passed
    failed, q = pipeline.knockout_check({"work_authorization": False,
                                         "has_required_license": True})
    assert not failed and q == "work_authorization"


def test_rejection_requires_human_and_ofccp_code(session, candidate, req):
    app = _apply(session, candidate, req)
    with pytest.raises(pipeline.DispositionRequiredError):
        pipeline.reject(session, app, actor="recruiter-1", disposition_code=None)
    with pytest.raises(pipeline.AiCannotRejectError):
        pipeline.reject(session, app, actor="ai:screener", disposition_code="withdrew")
    pipeline.reject(session, app, actor="recruiter-1",
                    disposition_code="not-qualified-min")
    assert app.status == "rejected"


def test_ai_rank_is_advisory_only(session, candidate, req):
    """REC-3 / Invariant #6: ranking writes advisory columns; status, stage,
    and disposition are untouched."""
    app = _apply(session, candidate, req)
    gateway = AiGateway(MockProvider(canned={"10y platform experience": "strong skills match"}))
    pipeline.ai_rank(session, gateway, req=req,
                     applications=[(app, "10y platform experience")],
                     recruiter_id="recruiter-1")
    assert app.ai_rank == 1 and app.ai_explanation == "strong skills match"
    assert app.status == "active" and app.stage == "new" and app.disposition_code is None


def test_stage_flow_from_config(session, candidate, req):
    app = _apply(session, candidate, req)
    flow = pipeline.load_stage_flow("standard")
    pipeline.advance_stage(session, app, flow=flow)
    assert app.stage == "screen"


# --- Register rows -----------------------------------------------------------------

def test_REC_do_not_rehire_policy_gated(session):
    """Register row: the do-not-rehire flag is visible only with the
    `candidate.read-dnr` capability — others get None, not False."""
    former = CandidateProfile(full_name="Re Hire", email="r@example.test",
                              country="US", internal_worker_id="w-old",
                              do_not_rehire=True)
    session.add(former)
    session.flush()
    lead = Subject("lead-1", ("recruiter-lead",))
    base = Subject("rec-1", ("recruiter",))
    assert pipeline.visible_do_not_rehire(POLICY, lead, former) is True
    assert pipeline.visible_do_not_rehire(POLICY, base, former) is None


def test_REC_internal_candidate_manager_data_wall(session, candidate, req):
    """Register row: confidential internal application is invisible to the
    candidate's manager; rejection uses sensitive handling."""
    app = _apply(session, candidate, req, internal=True, confidential=True)
    assert not pipeline.visible_to_manager(app, manager_of_candidate=True)
    assert pipeline.visible_to_manager(app, manager_of_candidate=False)
    note = pipeline.rejection_notification(app)
    assert note == {"channel": "personal-private", "copy_manager": False,
                    "template": "internal-candidate-rejection"}


def test_REC_accepted_offer_rescind_flow(session, candidate, req):
    """Register row: accepted offer rescinded (counter-offer) — explicit state
    chain, reason recorded, requisition reopens."""
    app = _apply(session, candidate, req)
    offer = offers.build_offer(session, app=app, req=req,
                               base_annual=Decimal("100000"), currency="USD",
                               start_date=date(2026, 8, 1))
    offers.extend(session, offer)
    offers.accept(session, offer, app=app, candidate=candidate, req=req,
                  on=date(2026, 6, 15))
    assert req.status == "filled"

    offers.rescind_accepted(session, offer, app=app, req=req, actor="recruiter-1",
                            reason="candidate accepted counter-offer")
    assert offer.status == "rescinded" and "counter-offer" in offer.rescind_reason
    assert app.status == "withdrawn" and req.status == "open"


def test_REC_multi_req_shared_profile(session, candidate):
    """Register row: one candidate, many reqs — shared profile, independent
    per-req dispositions."""
    req_a = Requisition(position_id="p1", title="Eng A", grade="G7", country="US",
                        headcount_type="backfill", status="open")
    req_b = Requisition(position_id="p2", title="Eng B", grade="G8", country="US",
                        headcount_type="net-new", status="open")
    app_a = _apply(session, candidate, req_a)
    app_b = _apply(session, candidate, req_b)
    assert app_a.candidate_id == app_b.candidate_id

    pipeline.reject(session, app_a, actor="rec-1",
                    disposition_code="less-qualified-than-selected")
    assert app_a.status == "rejected" and app_b.status == "active"


def test_REC_req_cancelled_with_offers_out(session, candidate, req):
    """Register row: cancelling a req with an extended offer rescinds it with
    care (reason + audit) and dispositions remaining applications."""
    app = _apply(session, candidate, req)
    offer = offers.build_offer(session, app=app, req=req,
                               base_annual=Decimal("95000"), currency="USD",
                               start_date=date(2026, 8, 1))
    offers.extend(session, offer)
    outcome = requisitions.cancel_requisition(session, req, actor="hr-lead",
                                              reason="budget pulled")
    assert outcome == {"offers_rescinded": 1, "applications_dispositioned": 1}
    assert req.status == "cancelled"
    session.refresh(offer)
    assert offer.status == "rescinded" and "budget pulled" in offer.rescind_reason


def test_REC_adverse_finding_post_start_escalation(session):
    """Register row: post-start adverse finding routes to the ER-segregated
    case queue (T3), never an automatic employment action."""
    case = offers.adverse_finding_post_start(
        session, worker_id="w-9", finding="license verification failed",
        actor="background-vendor-callback",
    )
    assert case.queue == "er" and case.priority == "critical"


def test_REC_gdpr_erasure_mid_pipeline(session, candidate, req):
    """Register row: erasure mid-pipeline anonymizes PII, keeps identity-free
    flow statistics; accepted-offer candidates are refused (contract basis)."""
    app = _apply(session, candidate, req)
    outcome = gdpr.erase_candidate(session, candidate, actor="privacy-office")
    assert outcome == {"erased": True, "applications_closed": 1}
    assert candidate.full_name is None and candidate.email is None and candidate.erased
    assert app.status == "withdrawn"  # flow stats retained, identity-free

    # accepted offer ⇒ refusal with the legal basis stated
    other = CandidateProfile(full_name="Held", email="h@example.test", country="US")
    session.add(other)
    session.flush()
    req2 = Requisition(position_id="p9", title="X", grade="G7", country="US",
                       headcount_type="backfill", status="open",
                       range_min=80000, range_max=120000)
    app2 = _apply(session, other, req2)
    offer = offers.build_offer(session, app=app2, req=req2,
                               base_annual=Decimal("90000"), currency="USD",
                               start_date=date(2026, 9, 1))
    offers.extend(session, offer)
    offers.accept(session, offer, app=app2, candidate=other, req=req2, on=date(2026, 6, 20))
    with pytest.raises(gdpr.ErasureRefusedError, match="contract"):
        gdpr.erase_candidate(session, other, actor="privacy-office")


# --- Offer → hire contract (REC-4) -----------------------------------------------

def test_offer_out_of_range_routes_to_comp(session, candidate, req):
    app = _apply(session, candidate, req)
    offer = offers.build_offer(session, app=app, req=req,
                               base_annual=Decimal("130000"), currency="USD",
                               start_date=date(2026, 8, 1))
    assert offer.requires_comp_approval


def test_offer_negotiation_versioning(session, candidate, req):
    app = _apply(session, candidate, req)
    v1 = offers.build_offer(session, app=app, req=req, base_annual=Decimal("95000"),
                            currency="USD", start_date=date(2026, 8, 1))
    v2 = offers.build_offer(session, app=app, req=req, base_annual=Decimal("100000"),
                            currency="USD", start_date=date(2026, 8, 1), supersedes=v1)
    assert (v2.version, v2.supersedes) == (2, v1.offer_id)
    assert v1.status == "rescinded"


def test_zero_rekeying_hire_contract(session, candidate, req):
    """REC-4 acceptance: the pre-hire payload is assembled entirely from
    existing records — every field present, nothing re-keyed."""
    app = _apply(session, candidate, req)
    offer = offers.build_offer(
        session, app=app, req=req, base_annual=Decimal("100000"), currency="USD",
        start_date=date(2026, 8, 1),
        components={"sign-on": {"amount": 10000, "clawback_months": 12}},
    )
    offers.extend(session, offer)
    payload = offers.accept(session, offer, app=app, candidate=candidate,
                            req=req, on=date(2026, 6, 15))
    assert payload == {
        "candidate_id": str(candidate.candidate_id),
        "full_name": "Avery Quinn",
        "email": "avery@example.test",
        "country": "US",
        "position_id": "pos-1",
        "grade": "G7",
        "base_annual": "100000",
        "currency": "USD",
        "components": {"sign-on": {"amount": 10000, "clawback_months": 12}},
        "start_date": "2026-08-01",
        "requisition_id": str(req.requisition_id),
        "offer_id": str(offer.offer_id),
        "rehire": False,
    }
