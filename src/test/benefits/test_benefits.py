"""Benefits tests (Specs/04): eligibility, windows, life events, EOI,
deduction derivation, and the §9 edge-case register."""
from datetime import date
from decimal import Decimal

import pytest

from benefits import services
from benefits.models import Enrollment


def test_eligibility_rules():
    assert services.eligible(worker_type="employee", fte=0.8, country="US",
                             as_of=date(2026, 6, 1))
    assert not services.eligible(worker_type="contingent", fte=1.0, country="US",
                                 as_of=date(2026, 6, 1))
    assert not services.eligible(worker_type="employee", fte=0.4, country="US",
                                 as_of=date(2026, 6, 1))


def test_waiting_period_date_math():
    assert services.first_of_month_after(date(2026, 3, 15), 30) == date(2026, 5, 1)
    assert services.first_of_month_after(date(2026, 12, 5), 30) == date(2027, 2, 1)
    assert services.first_of_month_after(date(2026, 6, 1), 30) == date(2026, 8, 1)


def test_new_hire_window_and_default(session, medical_plan):
    enrolled = services.enroll_new_hire(
        session, worker_id="w-1", plan=medical_plan, option="EE+FAM",
        hire_date=date(2026, 5, 1), enrolled_on=date(2026, 5, 20),
    )
    assert enrolled.status == "active"
    # hire 5/1 + 30d waiting ends 5/31 -> first of following month
    assert enrolled.coverage_start == date(2026, 6, 1)

    with pytest.raises(services.WindowExpiredError):
        services.enroll_new_hire(
            session, worker_id="w-2", plan=medical_plan, option="EE",
            hire_date=date(2026, 5, 1), enrolled_on=date(2026, 6, 15),
        )
    defaulted = services.default_on_window_expiry(
        session, worker_id="w-2", plan=medical_plan, hire_date=date(2026, 5, 1))
    assert defaulted.status == "defaulted" and defaulted.option == "EE"


def test_BEN_dual_covered_dependent_conflict(session, medical_plan):
    """Register row: both spouses work here — a dependent child may be covered
    under only one medical enrollment."""
    services.enroll_new_hire(
        session, worker_id="spouse-a", plan=medical_plan, option="EE+FAM",
        hire_date=date(2026, 5, 1), enrolled_on=date(2026, 5, 10),
        dependents=[{"dependent_key": "child-1", "relation": "child"}],
    )
    with pytest.raises(services.DependentConflictError, match="child-1"):
        services.enroll_new_hire(
            session, worker_id="spouse-b", plan=medical_plan, option="EE+FAM",
            hire_date=date(2026, 5, 1), enrolled_on=date(2026, 5, 12),
            dependents=[{"dependent_key": "child-1", "relation": "child"}],
        )


def test_section_125_consistency_matrix(session, medical_plan):
    enrollment = services.enroll_new_hire(
        session, worker_id="w-1", plan=medical_plan, option="EE",
        hire_date=date(2026, 5, 1), enrolled_on=date(2026, 5, 10),
    )
    with pytest.raises(services.ChangeNotAllowedError, match="Section 125"):
        services.apply_life_event(session, enrollment, event_type="marriage",
                                  change="remove-dependent",
                                  reported_on=date(2026, 6, 1), occurred_on=date(2026, 5, 25))


def test_BEN_retro_divorce_clawback_window(session, medical_plan):
    """Register row: divorce reported 90 days late — spouse removed, but the
    retroactive coverage end is capped at the carrier retro-term limit."""
    enrollment = services.enroll_new_hire(
        session, worker_id="w-1", plan=medical_plan, option="EE+FAM",
        hire_date=date(2026, 1, 5), enrolled_on=date(2026, 1, 10),
        dependents=[{"dependent_key": "sp-1", "relation": "spouse"}],
    )
    outcome = services.apply_life_event(
        session, enrollment, event_type="divorce", change="remove-spouse",
        reported_on=date(2026, 6, 1), occurred_on=date(2026, 3, 3),  # 90 days late
    )
    assert outcome["clawback_capped"]
    assert outcome["coverage_change_effective"] == date(2026, 4, 2)  # reported - 60d
    assert enrollment.dependents == []


def test_BEN_mid_oe_termination_cancels_pending(session, medical_plan):
    """Register row: termination during OE — future OE elections cancelled,
    active coverage ends at month end."""
    active = services.enroll_new_hire(
        session, worker_id="w-1", plan=medical_plan, option="EE",
        hire_date=date(2026, 1, 5), enrolled_on=date(2026, 1, 10),
    )
    pending_oe = Enrollment(worker_id="w-1", plan_id=medical_plan.plan_id,
                            option="EE+FAM", status="active",
                            coverage_start=date(2027, 1, 1), source="oe")
    session.add(pending_oe)
    session.flush()

    outcome = services.terminate_mid_oe(session, worker_id="w-1",
                                        termination_date=date(2026, 11, 15))
    assert outcome == {"pending_cancelled": 1, "active_ended": 1}
    assert pending_oe.coverage_end == date(2026, 11, 15)
    assert active.coverage_end == date(2026, 11, 30)  # end of month


def test_BEN_eoi_denied_reverts_to_default(session, life_plan):
    """Register row: EOI denied after default coverage started — elected 5×
    coverage terminates and the guaranteed-issue default takes its place."""
    elected = services.enroll_new_hire(
        session, worker_id="w-1", plan=life_plan, option="5x",
        hire_date=date(2026, 5, 1), enrolled_on=date(2026, 5, 10),
        salary_multiple=5,
    )
    assert elected.status == "pending-eoi"

    replacement = services.resolve_eoi(session, elected, approved=False,
                                       fallback_plan=life_plan)
    assert elected.status == "terminated"
    assert replacement.status == "defaulted" and replacement.option == "1x"


def test_eoi_approval_activates(session, life_plan):
    elected = services.enroll_new_hire(
        session, worker_id="w-2", plan=life_plan, option="5x",
        hire_date=date(2026, 5, 1), enrolled_on=date(2026, 5, 10), salary_multiple=5,
    )
    services.resolve_eoi(session, elected, approved=True)
    assert elected.status == "active"


def test_deduction_derivation_24_vs_26(session, medical_plan):
    rate = services.rate_for(session, plan_id=medical_plan.plan_id, option="EE",
                             age=40, as_of=date(2026, 6, 1))
    semi_monthly = services.per_period_deduction(rate, periods_per_year=24)
    biweekly = services.per_period_deduction(rate, periods_per_year=26)
    assert semi_monthly["employee_per_period"] == Decimal("62.50")   # 1500/24
    assert biweekly["employee_per_period"] == Decimal("57.69")       # 1500/26
    assert semi_monthly["employer_per_period"] == Decimal("187.50")  # 4500/24


def test_gtl_imputed_income():
    assert services.gtl_imputed_income_monthly(
        coverage=Decimal("50000"), age=40) == Decimal("0.00")
    assert services.gtl_imputed_income_monthly(
        coverage=Decimal("150000"), age=40) == Decimal("10.00")   # 100 × 0.10
    assert services.gtl_imputed_income_monthly(
        coverage=Decimal("150000"), age=58) == Decimal("43.00")   # 100 × 0.43
