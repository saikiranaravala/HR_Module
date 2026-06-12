"""Performance tests (Specs/07): goals, cycles, review flow, AI guardrails,
continuous feedback, and the §8 edge-case register."""
from datetime import date

import pytest
import yaml

from ai_layer.gateway import AiGateway, MockProvider
from performance import cycles, feedback, goals, reviews
from performance.models import ReviewDoc


# --- Goals (PERF-1) ---------------------------------------------------------------

def test_goal_revision_preserves_original(session):
    g1 = goals.create_goal(session, worker_id="w-1", title="Ship v1",
                           goal_type="okr", weight=40)
    g2 = goals.revise_goal(session, g1, title="Ship v1 + hardening", weight=50)
    assert g1.status == "superseded" and g1.title == "Ship v1"   # original intact
    assert (g2.version, g2.supersedes) == (2, g1.goal_id)


def test_orphan_goal_report(session):
    parent = goals.create_goal(session, worker_id="ceo", title="Grow ARR",
                               goal_type="okr")
    goals.create_goal(session, worker_id="w-1", title="Aligned", goal_type="okr",
                      parent=parent)
    orphan = goals.create_goal(session, worker_id="w-2", title="Unaligned",
                               goal_type="okr")
    goals.create_goal(session, worker_id="w-3", title="Learn Rust",
                      goal_type="development")  # dev goals exempt
    report = goals.orphan_report(session)
    titles = {g.title for g in report}
    assert "Unaligned" in titles and "Aligned" not in titles
    assert "Learn Rust" not in titles and "Grow ARR" in titles


# --- Cycle launch (PERF-2) ----------------------------------------------------------

def test_launch_excludes_short_tenure_and_prorates(session):
    _, docs = cycles.launch_cycle(
        session, name="FY26", template_key="annual-standard",
        launched_on=date(2026, 1, 15), window_end=date(2026, 3, 31),
        population=[
            {"worker_id": "vet", "manager_id": "m", "hire_date": date(2020, 1, 1)},
            {"worker_id": "mid", "manager_id": "m", "hire_date": date(2025, 6, 1)},
            {"worker_id": "new", "manager_id": "m", "hire_date": date(2025, 12, 1)},
        ],
    )
    by_worker = {d.worker_id: d for d in docs}
    assert "new" not in by_worker            # <90 days: auto-excluded
    assert by_worker["vet"].prorated is False
    assert by_worker["mid"].prorated is True


def test_ratingless_template_supported(session):
    template = cycles.load_template("annual-ratingless")
    assert template["ratingless"] is True
    _, docs = cycles.launch_cycle(
        session, name="FY26-NR", template_key="annual-ratingless",
        launched_on=date(2026, 1, 15), window_end=date(2026, 3, 31),
        population=[{"worker_id": "w-1", "manager_id": "m",
                     "hire_date": date(2020, 1, 1)}],
    )
    doc = docs[0]
    doc.narrative = "Narrative only."
    reviews.submit_manager_assessment(session, doc, rating=None)  # no rating
    assert doc.state == "manager-done" and doc.rating is None


# --- AI guardrails (PERF-4 / §5 hard rule) --------------------------------------------

def test_ai_draft_labeled_and_edit_required(session, doc):
    gateway = AiGateway(MockProvider(canned={"Goals:": "Delivered platform milestones."}))
    doc.state = "draft"
    doc.rating = None
    reviews.ai_draft_narrative(session, gateway, doc, author_id="mgr-1",
                               goal_summary="3/3 OKRs", checkin_summary="positive")
    assert doc.narrative.startswith("[AI draft — review and edit]")
    assert doc.ai_drafted and not doc.ai_draft_edited
    assert doc.rating is None  # AI path has no rating surface

    with pytest.raises(reviews.EditRequiredError):
        reviews.submit_manager_assessment(session, doc, rating="meets")
    reviews.edit_narrative(session, doc, narrative="Delivered all platform milestones on time.")
    reviews.submit_manager_assessment(session, doc, rating="meets")
    assert doc.state == "manager-done"
    assert doc.rating == "meets"  # rating came from the human submit, not the draft


def test_bias_lint_flags_coded_language():
    findings = reviews.bias_lint("She can be abrasive but is a digital native.")
    categories = {f["category"] for f in findings}
    assert categories == {"gender-coded", "age-coded"}
    assert reviews.bias_lint("Consistently delivered measurable results.") == []


# --- Calibration lineage ---------------------------------------------------------------

def test_calibration_requires_rationale_and_keeps_lineage(session, doc):
    with pytest.raises(reviews.RationaleRequiredError):
        reviews.calibrate(session, doc, session_id="cal-1", actor="hrbp-1",
                          new_rating="exceeds", rationale=None)
    adjustment = reviews.calibrate(session, doc, session_id="cal-1", actor="hrbp-1",
                                   new_rating="exceeds",
                                   rationale="cross-team comparison: top quartile impact")
    assert (adjustment.before_rating, adjustment.after_rating) == ("meets", "exceeds")
    assert doc.rating == "exceeds" and doc.state == "calibrated"


# --- Register rows -----------------------------------------------------------------------

def test_PERF_manager_change_midcycle_handoff(session, doc):
    """Register row: outgoing manager's draft survives; incoming finalizes;
    both are logged on the document."""
    reviews.handoff_manager(session, doc, outgoing="mgr-1", incoming="mgr-2")
    assert doc.manager_id == "mgr-2"
    assert doc.narrative == "Solid delivery on platform goals."  # draft kept
    log = doc.handoff_log[0]
    assert (log["outgoing"], log["incoming"]) == ("mgr-1", "mgr-2")


def test_PERF_leave_auto_extension(session, doc):
    """Register row: leave during the window → auto-extension per leave type."""
    template = cycles.load_template("annual-standard")
    cycles.extend_for_leave(doc, leave_type="parental",
                            window_end=date(2026, 3, 31), template=template)
    assert doc.extension_until == date(2026, 5, 30)  # +60 days
    with pytest.raises(cycles.TemplateError):
        cycles.extend_for_leave(doc, leave_type="sabbatical",
                                window_end=date(2026, 3, 31), template=template)


def test_PERF_released_amendment_dual_record(session, doc):
    """Register row: factual error after release → amendment as a NEW doc;
    the original is preserved with state 'amended'."""
    reviews.calibrate(session, doc, session_id="cal-1", actor="hrbp-1",
                      new_rating="meets", rationale="confirmed")
    reviews.release(session, doc)
    amendment = reviews.amend_released(
        session, doc, reason="goal attainment miscounted (3/3 not 2/3)",
        new_rating="exceeds", new_narrative=None,
    )
    assert doc.state == "amended" and doc.rating == "meets"      # original intact
    assert amendment.amends == doc.doc_id
    assert amendment.rating == "exceeds" and amendment.state == "released"


def test_PERF_skip_level_disagreement_recorded(session, doc):
    """Register row: skip-level disagreement blocks release until calibration
    dispositions it — never a silent overwrite."""
    reviews.calibrate(session, doc, session_id="cal-1", actor="hrbp-1",
                      new_rating="meets", rationale="initial")
    reviews.record_skip_level_disagreement(session, doc, skip_level_id="dir-1",
                                           position="rating understates scope growth")
    with pytest.raises(reviews.StateError, match="skip-level"):
        reviews.release(session, doc)
    reviews.resolve_skip_level(session, doc, resolution="panel reviewed; rating stands",
                               session_id="cal-1", actor="hrbp-1")
    reviews.release(session, doc)
    assert doc.state == "released"


def test_PERF_matrix_weight_conflict_rejected(tmp_path):
    """Register row: matrix-manager weighting conflicts fail at template
    validation, not at calibration time."""
    bad = {"templates": {"conflicted": {
        "sections": ["overall"], "ratingless": False,
        "participant_weights": {"manager": 70, "matrix_manager": 50},
    }}}
    path = tmp_path / "templates.yaml"
    path.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(cycles.TemplateError, match="sum to 100"):
        cycles.load_template("conflicted", path=path)


def test_PERF_terminated_before_release_closeout(session, doc):
    """Register row: terminated before release → explicit close-out, retained,
    neither released nor deleted."""
    reviews.closeout_terminated(session, doc, reason="terminated 2026-03-15")
    assert doc.state == "closed-out"
    with pytest.raises(reviews.StateError):
        reviews.release(session, doc)


# --- Continuous performance (PERF-3) ------------------------------------------------------

def test_checkin_private_notes_author_only(session):
    checkin = feedback.record_checkin(
        session, worker_id="w-1", manager_id="mgr-1", occurred_on=date(2026, 6, 1),
        shared_notes="Discussed growth plan.",
        private_notes="Watch workload — burnout risk.", private_author="mgr-1",
    )
    manager_view = feedback.checkin_view(checkin, viewer="mgr-1")
    worker_view = feedback.checkin_view(checkin, viewer="w-1")
    assert "private_notes" in manager_view
    assert "private_notes" not in worker_view


def test_feedback_visibility_explicit(session):
    with pytest.raises(ValueError):
        feedback.give_feedback(session, author_id="a", subject_id="s",
                               visibility="everyone", body="x", on=date(2026, 6, 1))
    item = feedback.give_feedback(session, author_id="a", subject_id="s",
                                  visibility="to-subject", body="great work",
                                  on=date(2026, 6, 1))
    assert item.visibility == "to-subject"


def test_360_anonymity_threshold(session):
    for i, author in enumerate(["r1", "r2", "r3"]):
        feedback.give_feedback(session, author_id=author, subject_id="w-1",
                               visibility="to-manager", body=f"comm {i}",
                               competency="communication", campaign_id="c-360",
                               on=date(2026, 6, 1))
    feedback.give_feedback(session, author_id="r4", subject_id="w-1",
                           visibility="to-manager", body="needs strategy work",
                           competency="strategy", campaign_id="c-360",
                           on=date(2026, 6, 1))
    report = feedback.aggregate_360(session, campaign_id="c-360", subject_id="w-1")
    assert "communication" in report["themes"]                 # 3 raters: shown
    assert report["withheld_below_threshold"] == ["strategy"]  # 1 rater: withheld
    assert report["total_raters"] == 4
