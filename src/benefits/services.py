"""Benefits services (Specs/04): eligibility, enrollment windows + life events,
EOI, dependent-conflict rules, deduction derivation for the payroll interlock.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from benefits.models import BenefitPlan, BenefitRate, Enrollment
from rules_workflow.rules import evaluate, load_ruleset

NEW_HIRE_WINDOW_DAYS = 30
LIFE_EVENT_WINDOW_DAYS = {"marriage": 30, "birth": 60, "divorce": 30, "aging-out": 30}
RETRO_DIVORCE_CLAWBACK_LIMIT_DAYS = 60  # carrier retro-term limit

# Section 125 consistency: which changes each life event permits.
ALLOWED_CHANGES = {
    "marriage":  {"add-spouse", "change-option"},
    "birth":     {"add-dependent", "change-option"},
    "divorce":   {"remove-spouse"},
    "aging-out": {"remove-dependent"},
}

_eligibility_rules = None


def _ruleset():
    global _eligibility_rules
    if _eligibility_rules is None:
        _eligibility_rules = load_ruleset("benefits-eligibility")
    return _eligibility_rules


class WindowExpiredError(ValueError):
    pass


class ChangeNotAllowedError(ValueError):
    pass


class DependentConflictError(ValueError):
    pass


def eligible(*, worker_type: str, fte: float, country: str, as_of: date) -> bool:
    outcome = evaluate(_ruleset(), {"worker_type": worker_type, "fte": fte,
                                    "country": country}, as_of).output
    return outcome != "not-eligible"


def first_of_month_after(start: date, days: int) -> date:
    """'First of month after N days' waiting-period date math (§3).

    Coverage begins on the first of the month strictly after the waiting
    period completes (start + days): a threshold landing exactly on the 1st
    rolls to the next month ("following", not "coinciding with").
    """
    threshold = start + timedelta(days=days)
    if threshold.month == 12:
        return date(threshold.year + 1, 1, 1)
    return date(threshold.year, threshold.month + 1, 1)


def _dependent_conflict(session: Session, plan_type_plans: list[uuid.UUID],
                        dependents: list[dict], exclude_worker: str) -> str | None:
    """Dual-covered couples (register row): the same dependent may be covered
    under only ONE active enrollment per plan type across the company."""
    if not dependents:
        return None
    keys = {d["dependent_key"] for d in dependents}
    others = session.scalars(select(Enrollment).where(
        Enrollment.status.in_(["active", "pending-eoi", "defaulted"]),
        Enrollment.worker_id != exclude_worker,
        Enrollment.plan_id.in_(plan_type_plans),
    )).all()
    for other in others:
        for dep in (other.dependents or []):
            if dep["dependent_key"] in keys:
                return dep["dependent_key"]
    return None


def enroll_new_hire(
    session: Session, *, worker_id: str, plan: BenefitPlan, option: str,
    hire_date: date, enrolled_on: date, dependents: list[dict] | None = None,
    salary_multiple: int | None = None,
) -> Enrollment:
    if enrolled_on > hire_date + timedelta(days=NEW_HIRE_WINDOW_DAYS):
        raise WindowExpiredError(
            f"new-hire window ({NEW_HIRE_WINDOW_DAYS}d) closed; defaulting policy applies"
        )
    plans_same_type = session.scalars(select(BenefitPlan.plan_id).where(
        BenefitPlan.plan_type == plan.plan_type)).all()
    conflict = _dependent_conflict(session, plans_same_type, dependents or [], worker_id)
    if conflict:
        raise DependentConflictError(
            f"dependent {conflict} already covered under another worker's {plan.plan_type} plan"
        )

    needs_eoi = (plan.requires_eoi_above_multiple is not None
                 and salary_multiple is not None
                 and salary_multiple > plan.requires_eoi_above_multiple)
    enrollment = Enrollment(
        worker_id=worker_id, plan_id=plan.plan_id, option=option,
        status="pending-eoi" if needs_eoi else "active",
        coverage_start=first_of_month_after(hire_date, 30),
        dependents=dependents, source="new-hire",
    )
    session.add(enrollment)
    session.flush()
    return enrollment


def default_on_window_expiry(session: Session, *, worker_id: str, plan: BenefitPlan,
                             hire_date: date) -> Enrollment | None:
    """Window expired without an election: apply the plan's defaulting policy."""
    if plan.default_option is None:
        return None  # waive policy
    enrollment = Enrollment(
        worker_id=worker_id, plan_id=plan.plan_id, option=plan.default_option,
        status="defaulted", coverage_start=first_of_month_after(hire_date, 30),
        source="default",
    )
    session.add(enrollment)
    session.flush()
    return enrollment


def apply_life_event(
    session: Session, enrollment: Enrollment, *, event_type: str, change: str,
    reported_on: date, occurred_on: date, dependents: list[dict] | None = None,
) -> dict:
    """Life-event change under the allowed-change matrix and reporting window.
    Retro divorce reported late (register row): coverage ends retroactively but
    the clawback reaches back at most the carrier retro-term limit."""
    if change not in ALLOWED_CHANGES.get(event_type, set()):
        raise ChangeNotAllowedError(
            f"'{change}' not permitted for life event '{event_type}' (Section 125)"
        )
    window = LIFE_EVENT_WINDOW_DAYS[event_type]
    clawback_capped = False
    effective_end = None

    if event_type == "divorce":
        days_late = (reported_on - occurred_on).days
        effective_end = occurred_on
        if days_late > RETRO_DIVORCE_CLAWBACK_LIMIT_DAYS:
            effective_end = reported_on - timedelta(days=RETRO_DIVORCE_CLAWBACK_LIMIT_DAYS)
            clawback_capped = True
        enrollment.dependents = [
            d for d in (enrollment.dependents or []) if d.get("relation") != "spouse"
        ]
    elif (reported_on - occurred_on).days > window:
        raise WindowExpiredError(f"{event_type} window ({window}d) closed")
    elif change in ("add-spouse", "add-dependent"):
        enrollment.dependents = (enrollment.dependents or []) + (dependents or [])

    session.flush()
    return {"applied": change, "coverage_change_effective": effective_end,
            "clawback_capped": clawback_capped}


def terminate_mid_oe(session: Session, *, worker_id: str, termination_date: date) -> dict:
    """Mid-OE termination (register row): pending OE elections are cancelled;
    active coverage ends per plan rule (end of month here)."""
    enrollments = session.scalars(select(Enrollment).where(
        Enrollment.worker_id == worker_id)).all()
    cancelled, ended = 0, 0
    for enrollment in enrollments:
        if enrollment.source == "oe" and enrollment.coverage_start > termination_date:
            enrollment.status = "terminated"
            enrollment.coverage_end = termination_date
            cancelled += 1
        elif enrollment.status in ("active", "defaulted", "pending-eoi"):
            enrollment.status = "terminated"
            month_end = (date(termination_date.year + (termination_date.month == 12),
                              (termination_date.month % 12) + 1, 1) - timedelta(days=1))
            enrollment.coverage_end = month_end
            ended += 1
    session.flush()
    return {"pending_cancelled": cancelled, "active_ended": ended}


def resolve_eoi(session: Session, enrollment: Enrollment, *, approved: bool,
                fallback_plan: BenefitPlan | None = None) -> Enrollment:
    """EOI denied after default coverage started (register row): the elected
    coverage reverts to the guaranteed-issue default, never silently lapses."""
    if enrollment.status != "pending-eoi":
        raise ValueError("enrollment is not awaiting EOI")
    if approved:
        enrollment.status = "active"
        session.flush()
        return enrollment
    enrollment.status = "terminated"
    enrollment.coverage_end = enrollment.coverage_start
    replacement = None
    if fallback_plan is not None and fallback_plan.default_option:
        replacement = Enrollment(
            worker_id=enrollment.worker_id, plan_id=fallback_plan.plan_id,
            option=fallback_plan.default_option, status="defaulted",
            coverage_start=enrollment.coverage_start, source="default",
        )
        session.add(replacement)
    session.flush()
    return replacement


# ---------- Payroll interlock (§6) ----------

def rate_for(session: Session, *, plan_id, option: str, age: int, as_of: date) -> BenefitRate:
    rates = session.scalars(select(BenefitRate).where(
        BenefitRate.plan_id == plan_id, BenefitRate.option == option,
        BenefitRate.age_min <= age, BenefitRate.age_max >= age,
        BenefitRate.effective_date <= as_of,
    ).order_by(BenefitRate.effective_date.desc())).first()
    if rates is None:
        raise LookupError("no rate row in force")
    return rates


def per_period_deduction(rate: BenefitRate, *, periods_per_year: int) -> dict:
    """Annual premium → per-period employee/employer split (24/26 logic)."""
    annual = Decimal(rate.annual_premium)
    employer = (annual * Decimal(rate.employer_pct) / Decimal("100"))
    employee = annual - employer
    quant = Decimal("0.01")
    return {
        "employee_per_period": (employee / periods_per_year).quantize(quant),
        "employer_per_period": (employer / periods_per_year).quantize(quant),
    }


GTL_TABLE_I_PER_1000_MONTH = {  # IRS Table I, simplified bands
    (0, 34): Decimal("0.08"), (35, 44): Decimal("0.10"),
    (45, 54): Decimal("0.23"), (55, 64): Decimal("0.43"), (65, 120): Decimal("1.27"),
}


def gtl_imputed_income_monthly(*, coverage: Decimal, age: int) -> Decimal:
    """Group-term life imputed income: Table I rate on coverage above $50K."""
    excess = max(Decimal("0"), coverage - Decimal("50000"))
    rate = next(v for (lo, hi), v in GTL_TABLE_I_PER_1000_MONTH.items() if lo <= age <= hi)
    return (excess / Decimal("1000") * rate).quantize(Decimal("0.01"))
