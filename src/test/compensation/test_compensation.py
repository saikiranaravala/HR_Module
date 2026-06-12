"""Compensation tests (Specs/05): foundation math, change transactions, cycle
mechanics, and the §8 edge-case register."""
from datetime import date
from decimal import Decimal

import pytest

from compensation import changes, cycles, structures
from compensation.models import CompRecord, comp_key
from platform_core import temporal

GUIDELINES = cycles.load_guidelines()


def seed_worker(session, worker_id="w-1", salary="100000", grade="G7",
                country="US", on=date(2026, 1, 1)):
    row = CompRecord(
        comp_key=comp_key(worker_id), worker_id=worker_id, record_role="home",
        base_annual=Decimal(salary), currency="USD", grade=grade, country=country,
        fte=Decimal("1"), effective_date=on, action_code="insert", action_reason="hire",
    )
    temporal.insert_temporal(session, row, actor="seed", source_channel="test")
    return row


def seed_range(session, grade="G7", country="US", lo="80000", mid="100000",
               hi="120000", on=date(2026, 1, 1)):
    return structures.set_range(
        session, grade=grade, country=country, currency="USD",
        range_min=Decimal(lo), range_mid=Decimal(mid), range_max=Decimal(hi),
        effective_date=on, actor="seed",
    )


# --- Foundation (COMP-1) -------------------------------------------------------

def test_derived_metrics(session):
    rng = seed_range(session)
    assert structures.compa_ratio(Decimal("90000"), rng) == Decimal("0.9000")
    assert structures.range_penetration(Decimal("90000"), rng) == Decimal("0.2500")
    assert structures.compa_quartile(Decimal("85000"), rng) == 1
    assert structures.compa_quartile(Decimal("119000"), rng) == 4


def test_geo_zone_differential():
    zones = structures.load_geo_zones()
    assert structures.zone_adjusted(Decimal("100000"), zone="us-metro-tier2",
                                    zones=zones) == Decimal("95000.00")


def test_change_reason_taxonomy_and_approval_matrix(session):
    seed_range(session)
    seed_worker(session)
    with pytest.raises(changes.InvalidReasonError):
        changes.apply_change(session, worker_id="w-1", new_salary=Decimal("105000"),
                             reason="because", effective_date=date(2026, 6, 1), actor="mgr")
    ok = changes.apply_change(session, worker_id="w-1", new_salary=Decimal("105000"),
                              reason="merit", effective_date=date(2026, 6, 1), actor="mgr")
    assert not ok.requires_comp_team_approval

    big = changes.apply_change(session, worker_id="w-1", new_salary=Decimal("125000"),
                               reason="market", effective_date=date(2026, 7, 1), actor="mgr")
    assert big.requires_comp_team_approval
    assert any("exceeds" in r for r in big.approval_reasons)
    assert any("out of range" in r for r in big.approval_reasons)


# --- Register rows ---------------------------------------------------------------

def test_COMP_promo_plus_merit_sequencing(session):
    """Register row: merit on pre-promotion salary, promotion on top, range
    validated against the NEW grade."""
    seed_range(session, grade="G7")
    seed_range(session, grade="G8", lo="100000", mid="125000", hi="150000")
    seed_worker(session, salary="100000", grade="G7")

    result = changes.promote_with_merit(
        session, worker_id="w-1", new_grade="G8", merit_pct=Decimal("4"),
        promotion_pct=Decimal("10"), effective_date=date(2026, 6, 1), actor="mgr",
    )
    # 100000 * 1.04 = 104000; * 1.10 = 114400 — inside G8 range
    assert result.record.base_annual == Decimal("114400.00")
    assert result.record.grade == "G8"
    assert not result.requires_comp_team_approval

    current = structures.current_comp(session, "w-1", as_of=date(2026, 6, 1))
    assert current.base_annual == Decimal("114400.00")


def test_COMP_retro_merit_after_termination_supplement(session):
    """Register row: merit landing retroactively after termination becomes a
    retro temporal row + a final-pay supplement element, not ongoing pay."""
    seed_range(session)
    seed_worker(session)
    # later record exists (e.g. a market adjustment in May)
    changes.apply_change(session, worker_id="w-1", new_salary=Decimal("102000"),
                         reason="market", effective_date=date(2026, 5, 1), actor="mgr")
    # retro merit effective April, after the worker terminated April 30
    result = changes.apply_change(
        session, worker_id="w-1", new_salary=Decimal("104000"), reason="merit",
        effective_date=date(2026, 4, 1), actor="comp-admin",
        worker_terminated_on=date(2026, 4, 30),
    )
    assert result.record.action_code == "insert"
    assert result.payroll_elements[0]["element"] == "final-pay-supplement"
    assert result.payroll_elements[0]["off_cycle"] is True
    # the retro write is sequenced under the May record, not over it
    assert structures.current_comp(session, "w-1", as_of=date(2026, 5, 1)).base_annual == Decimal("102000")
    assert structures.current_comp(session, "w-1", as_of=date(2026, 4, 15)).base_annual == Decimal("104000")


def test_COMP_fx_locked_variance_reported(session):
    """Register row: mid-cycle FX swing — locked rate stands, variance reported."""
    cycle = cycles.open_cycle(
        session, name="FY26 merit", corporate_currency="USD",
        fx_rates={"EUR": 1.10}, budget_pool=Decimal("100000"),
        population=[{"worker_id": "de-1", "manager_id": "mgr-1",
                     "snapshot": {"salary": 80000, "currency": "EUR",
                                  "rating": "meets", "compa_quartile": 2}}],
    )
    line = cycles.lines_for_manager(session, cycle, "mgr-1")[0]
    cycles.recommend(session, cycle, line, actor="mgr-1",
                     merit_pct=Decimal("3"), guidelines=GUIDELINES)
    # committed at locked 1.10, regardless of the market moving to 1.25
    assert cycles.committed_spend(session, cycle) == Decimal("2640.00")  # 2400 EUR * 1.10
    variance = cycles.fx_variance(cycle, {"EUR": 1.25})
    assert variance["EUR"] == Decimal("0.1500")
    assert cycles.committed_spend(session, cycle) == Decimal("2640.00")  # unchanged


def test_COMP_range_refresh_remediation_list(session):
    """Register row: post-refresh below-min workers land on the remediation
    list with a proposed bring-to-min (proposal only — humans commit money)."""
    seed_range(session)
    seed_worker(session, worker_id="low", salary="82000")
    seed_worker(session, worker_id="fine", salary="110000")
    remediation = structures.refresh_with_remediation(
        session, grade="G7", country="US", currency="USD",
        range_min=Decimal("90000"), range_mid=Decimal("110000"),
        range_max=Decimal("130000"), effective_date=date(2026, 7, 1),
        actor="comp-admin", workers=["low", "fine"],
    )
    assert len(remediation) == 1
    assert remediation[0]["worker_id"] == "low"
    assert remediation[0]["proposed_increase"] == Decimal("8000")


def test_COMP_manager_self_recommendation_skip_level(session):
    """Register row: a manager's own record routes to the skip-level."""
    cycle = cycles.open_cycle(
        session, name="FY26", corporate_currency="USD", fx_rates={},
        budget_pool=Decimal("50000"),
        population=[{"worker_id": "mgr-1", "manager_id": "mgr-1",
                     "snapshot": {"salary": 150000, "currency": "USD",
                                  "rating": "meets", "compa_quartile": 3}}],
    )
    line = cycles.lines_for_manager(session, cycle, "mgr-1")[0]
    with pytest.raises(cycles.SelfRecommendationError):
        cycles.recommend(session, cycle, line, actor="mgr-1",
                         merit_pct=Decimal("3"), guidelines=GUIDELINES)
    assert line.status == "routed-skip-level"
    assert line.merit_pct is None  # untouched by the self-attempt


def test_COMP_dual_currency_expat_shadow(session):
    """Register row: expat split — home record of record + host shadow."""
    home, host = changes.create_expat_split(
        session, worker_id="x-1", effective_date=date(2026, 6, 1), actor="comp-admin",
        home={"base_annual": Decimal("100000"), "currency": "USD", "grade": "G7", "country": "US"},
        host={"base_annual": Decimal("92000"), "currency": "EUR", "grade": "G7", "country": "DE"},
    )
    assert (home.record_role, host.record_role) == ("home", "host-shadow")
    assert structures.current_comp(session, "x-1", as_of=date(2026, 6, 1)).currency == "USD"
    shadow = structures.current_comp(session, "x-1", as_of=date(2026, 6, 1),
                                     record_role="host-shadow")
    assert shadow.currency == "EUR" and shadow.country == "DE"


# --- Cycle mechanics --------------------------------------------------------------

def test_out_of_guideline_requires_justification_and_budget_enforced(session):
    cycle = cycles.open_cycle(
        session, name="FY26", corporate_currency="USD", fx_rates={},
        budget_pool=Decimal("10000"),
        population=[
            {"worker_id": "w-1", "manager_id": "mgr-1",
             "snapshot": {"salary": 100000, "currency": "USD", "rating": "meets",
                          "compa_quartile": 2}},
            {"worker_id": "w-2", "manager_id": "mgr-1",
             "snapshot": {"salary": 100000, "currency": "USD", "rating": "meets",
                          "compa_quartile": 2}},
        ],
    )
    l1, l2 = cycles.lines_for_manager(session, cycle, "mgr-1")
    with pytest.raises(cycles.JustificationRequiredError):
        cycles.recommend(session, cycle, l1, actor="mgr-1",
                         merit_pct=Decimal("9"), guidelines=GUIDELINES)
    cycles.recommend(session, cycle, l1, actor="mgr-1", merit_pct=Decimal("9"),
                     guidelines=GUIDELINES, justification="retention risk, key skill")
    assert l1.out_of_guideline

    with pytest.raises(cycles.BudgetExceededError):
        cycles.recommend(session, cycle, l2, actor="mgr-1",
                         merit_pct=Decimal("4"), guidelines=GUIDELINES)
    assert l2.merit_pct is None  # rejected entry rolled back


# --- Temporal conformance (Invariant #1) -------------------------------------------

from platform_core.conformance import TemporalConformanceSuite  # noqa: E402
from compensation.models import CompRecord  # noqa: E402
from decimal import Decimal as D  # noqa: E402


class TestCompRecordTemporalConformance(TemporalConformanceSuite):
    @pytest.fixture
    def temporal_model(self):
        return CompRecord

    @pytest.fixture
    def make_row(self):
        def _make(entity_id, effective_date, **overrides):
            defaults = dict(
                comp_key=entity_id, worker_id="w-conf", record_role="home",
                base_annual=D("100000"), currency="USD", grade="G7", country="US",
                fte=D("1"), effective_date=effective_date,
                action_code="insert", action_reason="conformance",
            )
            defaults.update(overrides)
            return CompRecord(**defaults)
        return _make
