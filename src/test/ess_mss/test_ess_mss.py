"""ESS/MSS + HR Service Delivery tests (Specs/10): inbox/delegation, cases with
ER segregation, help copilot handoff, KB legal gate, notifications, access
modes, and the §7 edge-case register."""
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from ai_layer.gateway import AiGateway, MockProvider
from ai_layer.retrieval import load_corpus
from ess_mss import access, cases, help as help_center, inbox, knowledge, notifications, team
from ess_mss.models import NotificationPref
from platform_core.audit import AuditEvent
from platform_core.policy.engine import PolicyEngine, Subject
from rules_workflow.workflow import load_definition, start_instance

POLICY = PolicyEngine()


# --- MSS inbox & delegation -------------------------------------------------

def test_inbox_aggregates_pending_for_assignee(session, org):
    definition = load_definition("job-change-approval", version=1)
    start_instance(session, definition, subject_worker="emp-1", initiator="emp-1", org=org)
    items = inbox.inbox(session, "mgr-1")
    assert len(items) == 1
    step, instance = items[0]
    assert step.resolved_assignee == "mgr-1" and instance.subject_ref == "emp-1"


def test_inbox_includes_role_queue_items(session, org):
    """Steps fallback-routed to 'role:hr-admin' must reach role members'
    inboxes — act_on_step already lets them approve."""
    definition = load_definition("job-change-approval", version=1)
    # 'solo' has no manager chain -> approver resolution exhausts -> fallback role
    start_instance(session, definition, subject_worker="solo", initiator="solo", org=org)
    assert inbox.inbox(session, "hr-alice") == []
    items = inbox.inbox(session, "hr-alice", roles=("hr-admin",))
    assert len(items) == 1
    assert items[0][0].resolved_assignee == "role:hr-admin"


def test_delegation_duration_limit(session):
    with pytest.raises(inbox.DelegationLimitError):
        inbox.create_delegation(
            session, delegator="mgr-1", delegate="mgr-2", scope_types=["time"],
            starts_on=date(2026, 6, 1), ends_on=date(2026, 8, 1),
        )


def test_MSS_delegate_self_approval_blocked(session, org):
    """Register row: a delegated approver acting on an item about THEMSELVES
    is blocked, and the attempt is audit-logged."""
    definition = load_definition("job-change-approval", version=1)
    # mgr-1 delegates to emp-1's peer... here: the item's subject IS the delegate.
    delegations = {"mgr-1": "emp-1"}
    instance = start_instance(session, definition, subject_worker="emp-1",
                              initiator="hr-init", org=org, delegations=delegations)
    with pytest.raises(inbox.SelfApprovalError):
        inbox.act_via_inbox(session, instance, definition,
                            actor="emp-1", approve=True, org=org)
    logged = session.scalars(select(AuditEvent).where(AuditEvent.action == "deny")).all()
    assert any("self-approval" in (e.after or {}).get("detail", "") for e in logged)


def test_bulk_approve_barred_for_comp(session, org):
    comp_def = load_definition("comp-change-approval", version=1)
    instance = start_instance(session, comp_def, subject_worker="emp-1",
                              initiator="emp-1", org=org)
    with pytest.raises(inbox.BulkNotAllowedError):
        inbox.bulk_approve(session, [(instance, comp_def)], actor="mgr-1", org=org)


# --- Team analytics (register row) -------------------------------------------

def test_MSS_team_analytics_scope_and_suppression():
    """Register row: manager-of-manager sees only their subtree; n<5 suppressed."""
    roster = [
        {"worker_id": f"w{i}", "org_path": "/corp/eng/platform/",
         "tenure_years": 2.0, "terminated_in_period": i == 0}
        for i in range(6)
    ] + [
        {"worker_id": "x1", "org_path": "/corp/sales/", "tenure_years": 10.0,
         "terminated_in_period": True},
    ]
    metrics = team.team_metrics(roster, requestor_org_path="/corp/eng/")
    assert not metrics.suppressed
    assert metrics.headcount == 6              # sales row excluded structurally
    assert metrics.turnover_rate == round(1 / 6, 4)

    small = team.team_metrics(roster[:3], requestor_org_path="/corp/eng/")
    assert small.suppressed and small.headcount is None

    # '/corp/eng' must not match '/corp/engineering-services' (path boundary)
    lookalike = [{"worker_id": f"l{i}", "org_path": "/corp/engineering-services/",
                  "tenure_years": 1.0, "terminated_in_period": False} for i in range(6)]
    boundary = team.team_metrics(roster + lookalike, requestor_org_path="/corp/eng")
    assert boundary.headcount == 6  # lookalike org excluded


# --- Cases: routing, ER segregation, notes, deflection ------------------------

def test_case_routing_and_sla(session):
    case = cases.open_case(session, worker_id="w-1", topic="bank-change",
                           description="my deposit went elsewhere",
                           opened_at=datetime(2026, 6, 11, 9, 0, tzinfo=timezone.utc))
    assert case.queue == "payroll" and case.priority == "high"
    assert case.sla_due_at == datetime(2026, 6, 11, 13, 0, tzinfo=timezone.utc)


def test_er_case_segregation_policy_gated(session):
    er_case = cases.open_case(session, worker_id="w-1", topic="harassment",
                              description="ER detail")
    agent = Subject("agent-1", ("case-agent",))
    investigator = Subject("er-1", ("er-investigator",))

    with pytest.raises(cases.ErCaseAccessError):
        cases.read_case(session, POLICY, er_case, subject=agent)

    data = cases.read_case(session, POLICY, er_case, subject=investigator)
    assert data["description"] == "ER detail"
    # T3 read is audit-logged (read-logging invariant)
    reads = session.scalars(select(AuditEvent).where(AuditEvent.action == "read")).all()
    assert any(e.sensitivity_tier == "T3" for e in reads)


def test_case_note_visibility(session):
    case = cases.open_case(session, worker_id="w-1", topic="payslip", description="q")
    cases.add_note(session, case, author="agent-1", visibility="internal", body="escalating")
    cases.add_note(session, case, author="agent-1", visibility="employee", body="we are on it")
    assert [n.body for n in cases.notes_for_viewer(session, case, viewer="w-1")] == ["we are on it"]
    assert len(cases.notes_for_viewer(session, case, viewer="agent-1")) == 2


def test_deflection_honest_measurement(session):
    answered_at = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    assert cases.was_deflected(session, worker_id="w-1", topic="leave", answered_at=answered_at)
    cases.open_case(session, worker_id="w-1", topic="leave", description="still confused",
                    opened_at=datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc))
    assert not cases.was_deflected(session, worker_id="w-1", topic="leave", answered_at=answered_at)


# --- Help copilot -------------------------------------------------------------

def test_help_answers_with_citations(session):
    gateway = AiGateway(MockProvider(canned={"policy-answer": "12 weeks, per handbook."}))
    outcome = help_center.ask(
        session, gateway, load_corpus(), worker_id="w-1", country="US",
        population="all", topic="family-medical-leave",
        question="How long is family leave?", as_of=date(2026, 6, 1),
    )
    assert outcome.kind == "answered"
    assert "us-fmla-handbook v3" in outcome.citations


def test_help_contradiction_hands_off_to_case_with_transcript(session):
    gateway = AiGateway(MockProvider())
    outcome = help_center.ask(
        session, gateway, load_corpus(), worker_id="w-2", country="DE",
        population="union-metal", topic="family-medical-leave",
        question="Wie lange Elternzeit?", as_of=date(2026, 6, 1),
    )
    # CBA vs handbook contradiction routes to a case, transcript attached.
    assert outcome.kind == "case-created"
    assert outcome.case.transcript[0]["text"] == "Wie lange Elternzeit?"


# --- Knowledge base -----------------------------------------------------------

def test_kb_policy_article_legal_gate(session):
    article = knowledge.draft_article(session, title="DE Leave Policy", body="...",
                                      country="DE", is_policy=True)
    with pytest.raises(knowledge.LegalReviewRequiredError):
        knowledge.publish(session, article, on=date(2026, 6, 1))
    knowledge.submit_for_legal_review(session, article)
    knowledge.publish(session, article, on=date(2026, 6, 1), legal_approved=True)
    assert article.status == "published"
    assert article.review_due == date(2027, 6, 1)
    assert knowledge.stale_articles(session, as_of=date(2027, 6, 2)) == [article]


def test_kb_population_targeting(session):
    a = knowledge.draft_article(session, title="US 401k", body="...", country="US")
    knowledge.publish(session, a, on=date(2026, 1, 1))
    assert knowledge.visible_articles(session, country="DE", population="all") == []
    assert len(knowledge.visible_articles(session, country="US", population="salaried")) == 1


# --- Notifications ------------------------------------------------------------

def test_mandatory_channel_ignores_overrides(session):
    catalog = notifications.load_catalog()
    pref = NotificationPref(worker_id="w-1", notif_type="bank-change-alert",
                            channels=["push"], personal_channel_consent=True)
    resolved = notifications.resolve(catalog, "bank-change-alert", pref=pref)
    assert resolved.channels == ["push", "email", "sms"]  # defaults, not override


def test_quiet_hours_defer_to_digest(session):
    catalog = notifications.load_catalog()
    pref = NotificationPref(worker_id="w-1", quiet_start=22, quiet_end=7,
                            personal_channel_consent=True)
    resolved = notifications.resolve(catalog, "payslip-published", pref=pref, local_hour=23)
    assert resolved.deferred_to_digest and resolved.channels == []


def test_ESS_frontline_channel_requires_consent(session):
    """Register row: SMS/personal-email channels for workers without corporate
    devices require recorded consent; without it those channels are dropped."""
    catalog = notifications.load_catalog()
    no_consent = NotificationPref(worker_id="w-1", personal_channel_consent=False)
    resolved = notifications.resolve(catalog, "frontline-shift-notice", pref=no_consent)
    assert resolved.channels == [] and set(resolved.dropped_for_consent) == {"sms", "personal-email"}

    consented = NotificationPref(worker_id="w-1", personal_channel_consent=True)
    resolved = notifications.resolve(catalog, "frontline-shift-notice", pref=consented)
    assert resolved.channels == ["sms", "personal-email"]


# --- Access modes (register rows) ----------------------------------------------

def test_ESS_terminated_worker_alumni_scope(session):
    """Register row: post-exit access is docs-only inside the country retention
    window — payslips yes, data changes / other resources no, and it expires."""
    grant = access.grant_alumni_access(session, worker_id="w-9", country="US",
                                       terminated_on=date(2026, 1, 31))
    assert access.authorize_alumni(grant, resource_kind="payslip", on=date(2027, 1, 1))
    with pytest.raises(access.ScopeError):
        access.authorize_alumni(grant, resource_kind="directory", on=date(2027, 1, 1))
    with pytest.raises(access.AccessExpiredError):
        access.authorize_alumni(grant, resource_kind="payslip", on=date(2029, 3, 1))


def test_ESS_legal_hold_change_freeze(session):
    """Register row: legal-hold worker sees freeze messaging on change attempts;
    the attempt is audit-logged; the hold reason is never exposed."""
    access.place_legal_hold(session, worker_id="w-5", reason="litigation #4512",
                            on=date(2026, 6, 1))
    with pytest.raises(access.LegalHoldFreezeError) as exc:
        access.check_change_allowed(session, worker_id="w-5", field="address")
    assert "litigation" not in str(exc.value)  # reason not leaked
    denies = session.scalars(select(AuditEvent).where(AuditEvent.action == "deny")).all()
    assert any("legal hold" in (e.after or {}).get("detail", "") for e in denies)
    # no hold -> no error
    access.check_change_allowed(session, worker_id="w-6", field="address")


def test_bank_change_fraud_interlock():
    with pytest.raises(access.BankChangeFrozenError, match="frozen within"):
        access.validate_bank_change(change_date=date(2026, 6, 13),
                                    next_payday=date(2026, 6, 15),
                                    out_of_band_confirmed=True)
    with pytest.raises(access.BankChangeFrozenError, match="out-of-band"):
        access.validate_bank_change(change_date=date(2026, 6, 1),
                                    next_payday=date(2026, 6, 15),
                                    out_of_band_confirmed=False)
    access.validate_bank_change(change_date=date(2026, 6, 1),
                                next_payday=date(2026, 6, 15),
                                out_of_band_confirmed=True)
