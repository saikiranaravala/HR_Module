"""Cycle management (COMP-2): frozen population snapshot, locked FX, budget
enforcement, guideline matrix, self-recommendation skip-level routing."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from compensation.models import CompCycle, CycleLine

CONFIG_DIR = Path(__file__).resolve().parent / "config"


class BudgetExceededError(ValueError):
    pass


class JustificationRequiredError(ValueError):
    pass


class SelfRecommendationError(PermissionError):
    pass


def load_guidelines(path: Path | None = None) -> dict:
    """Merit matrix: rating × compa-quartile → {min, max, cap}. Rating keys are
    opaque config strings — the ratings-philosophy gate (00-INDEX) is isolated
    here; a ratingless cycle ships a matrix with the single key 'default'."""
    path = path or CONFIG_DIR / "guidelines.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["matrix"]


def open_cycle(
    session: Session, *, name: str, corporate_currency: str, fx_rates: dict,
    budget_pool: Decimal, population: list[dict],
) -> CompCycle:
    """Population is FROZEN at open (snapshot policy, §3 acceptance): later org
    moves do not add/remove lines; exceptions are admin-managed."""
    cycle = CompCycle(name=name, status="open", corporate_currency=corporate_currency,
                      fx_rates=fx_rates, budget_pool=budget_pool,
                      opened_at=datetime.now(timezone.utc))
    session.add(cycle)
    session.flush()
    for member in population:
        session.add(CycleLine(cycle_id=cycle.cycle_id, worker_id=member["worker_id"],
                              manager_id=member["manager_id"], snapshot=member["snapshot"]))
    session.flush()
    return cycle


def lines_for_manager(session: Session, cycle: CompCycle, manager_id: str) -> list[CycleLine]:
    return session.scalars(select(CycleLine).where(
        CycleLine.cycle_id == cycle.cycle_id,
        CycleLine.manager_id == manager_id,
    )).all()


def to_corporate(cycle: CompCycle, amount: Decimal, currency: str) -> Decimal:
    """Convert at the rate LOCKED at cycle open — never the market rate."""
    if currency == cycle.corporate_currency:
        return amount
    return (amount * Decimal(str(cycle.fx_rates[currency]))).quantize(Decimal("0.01"))


def committed_spend(session: Session, cycle: CompCycle) -> Decimal:
    lines = session.scalars(select(CycleLine).where(
        CycleLine.cycle_id == cycle.cycle_id, CycleLine.merit_pct.isnot(None))).all()
    total = Decimal("0")
    for line in lines:
        increase = (Decimal(str(line.snapshot["salary"]))
                    * Decimal(str(line.merit_pct)) / 100)
        total += to_corporate(cycle, increase, line.snapshot["currency"])
    return total.quantize(Decimal("0.01"))


def recommend(
    session: Session, cycle: CompCycle, line: CycleLine, *, actor: str,
    merit_pct: Decimal, guidelines: dict, justification: str | None = None,
) -> CycleLine:
    # Register row: a manager never recommends on their own record — it routes
    # to the skip-level untouched.
    if actor == line.worker_id:
        line.status = "routed-skip-level"
        session.flush()
        raise SelfRecommendationError(
            "your own record is routed to your manager for recommendation"
        )

    rating = line.snapshot.get("rating", "default")
    quartile = str(line.snapshot.get("compa_quartile", 2))
    cell = guidelines.get(rating, guidelines.get("default", {})).get(
        quartile, {"min": 0, "max": 100})
    in_guideline = Decimal(str(cell["min"])) <= merit_pct <= Decimal(str(cell["max"]))
    if not in_guideline and not justification:
        raise JustificationRequiredError(
            f"{merit_pct}% is outside guideline {cell['min']}–{cell['max']}% "
            "for this rating/quartile; justification is mandatory"
        )

    previous = line.merit_pct
    line.merit_pct = merit_pct
    line.justification = justification
    line.out_of_guideline = not in_guideline
    session.flush()

    spend = committed_spend(session, cycle)
    if spend > cycle.budget_pool:
        line.merit_pct = previous  # reject the over-budget entry
        session.flush()
        raise BudgetExceededError(
            f"committed {spend} {cycle.corporate_currency} exceeds pool {cycle.budget_pool}"
        )
    return line


def fx_variance(cycle: CompCycle, market_rates: dict) -> dict[str, Decimal]:
    """Register row: FX swings mid-cycle never recalc committed lines — the
    locked rate stands; this reports the variance per currency for finance."""
    variance = {}
    for currency, locked in cycle.fx_rates.items():
        market = market_rates.get(currency)
        if market is None:
            continue
        variance[currency] = (Decimal(str(market)) - Decimal(str(locked))).quantize(Decimal("0.0001"))
    return variance
