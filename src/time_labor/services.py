"""Time & Labor services (Specs/02): capture, OT calculation, accruals,
period close with the retro reconciliation identity.
"""
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from rules_workflow.rules import evaluate, load_ruleset
from time_labor.models import AccrualLot, TimeEntry, TimeResult

_ot_rules = None
_minor_rules = None


def _ot_ruleset():
    global _ot_rules
    if _ot_rules is None:
        _ot_rules = load_ruleset("overtime-thresholds")
    return _ot_rules


def _minor_ruleset():
    global _minor_rules
    if _minor_rules is None:
        _minor_rules = load_ruleset("minor-hour-caps")
    return _minor_rules


class PeriodLockedError(ValueError):
    pass


class NegativeBalanceError(ValueError):
    pass


class MinorHourCapError(ValueError):
    pass


# ---------- Capture ----------

def record_entry(
    session: Session, *, worker_id, person_id, in_utc: datetime, out_utc: datetime,
    timezone_name: str, pay_group: str, country: str, state: str | None = None,
) -> TimeEntry:
    """Attribution: the LOCAL date of shift start (midnight-spanning rule);
    elapsed time always derives from UTC (DST-proof)."""
    local_start = in_utc.astimezone(ZoneInfo(timezone_name))
    entry = TimeEntry(
        worker_id=worker_id, person_id=person_id, in_utc=in_utc, out_utc=out_utc,
        timezone_name=timezone_name, work_date=local_start.date(),
        pay_group=pay_group, country=country, state=state,
    )
    session.add(entry)
    session.flush()
    return entry


def entry_hours(entry: TimeEntry) -> float:
    return (entry.out_utc - entry.in_utc).total_seconds() / 3600.0


# ---------- Calculation ----------

@dataclass
class CalcLine:
    earnings_code: str
    hours: float
    explanation: str


def calculate_period(
    session: Session, *, person_id, period_start: date, period_end: date,
    transaction_date: date | None = None,
) -> dict[uuid.UUID, list[CalcLine]]:
    """OT calculation per worker for a period. Multi-job FLSA aggregation:
    when the jurisdiction combines hours, OT is computed on the PERSON's
    combined weekly hours and attributed to the worker whose hours crossed
    the threshold (register row)."""
    transaction_date = transaction_date or period_end
    entries = list(session.scalars(
        select(TimeEntry).where(
            TimeEntry.person_id == person_id,
            TimeEntry.work_date >= period_start,
            TimeEntry.work_date <= period_end,
        ).order_by(TimeEntry.in_utc)
    ))
    if not entries:
        return {}

    rule_eval = evaluate(
        _ot_ruleset(),
        {"country": entries[0].country, "state": entries[0].state},
        transaction_date,
    )
    params = rule_eval.output
    rule_tag = f"overtime-thresholds v{rule_eval.version}"

    daily_ot = params.get("daily_ot")
    daily_dt = params.get("daily_dt")
    weekly_ot = params.get("weekly_ot")
    combine = params.get("combine_multi_job", False)

    per_worker: dict[uuid.UUID, dict[str, float]] = defaultdict(lambda: {"REG": 0.0, "OT15": 0.0, "OT20": 0.0})

    # Daily buckets first (e.g., CA 8/12), per worker per local day.
    daily: dict[tuple, float] = defaultdict(float)
    for entry in entries:
        daily[(entry.worker_id, entry.work_date)] += entry_hours(entry)

    for (worker_id, _day), hours in daily.items():
        dt_hours = max(0.0, hours - daily_dt) if daily_dt else 0.0
        ot_hours = (max(0.0, min(hours, daily_dt or hours) - daily_ot) if daily_ot else 0.0)
        reg = hours - ot_hours - dt_hours
        per_worker[worker_id]["OT20"] += dt_hours
        per_worker[worker_id]["OT15"] += ot_hours
        per_worker[worker_id]["REG"] += reg

    # Weekly threshold on remaining straight time. Combined across the person's
    # jobs when the rule says so (FLSA joint-employment aggregation).
    if weekly_ot:
        if combine:
            total_reg = sum(buckets["REG"] for buckets in per_worker.values())
            overflow = max(0.0, total_reg - weekly_ot)
            # Attribute overflow to workers in reverse chronological order of hours
            for worker_id in sorted(per_worker, key=lambda w: per_worker[w]["REG"]):
                if overflow <= 0:
                    break
                take = min(overflow, per_worker[worker_id]["REG"])
                per_worker[worker_id]["REG"] -= take
                per_worker[worker_id]["OT15"] += take
                overflow -= take
        else:
            for worker_id, buckets in per_worker.items():
                overflow = max(0.0, buckets["REG"] - weekly_ot)
                buckets["REG"] -= overflow
                buckets["OT15"] += overflow

    results: dict[uuid.UUID, list[CalcLine]] = {}
    for worker_id, buckets in per_worker.items():
        lines = [
            CalcLine(code, round(hours, 2),
                     f"{rule_tag}; combined={combine}; period {period_start}..{period_end}")
            for code, hours in buckets.items() if hours > 0
        ]
        results[worker_id] = lines
    return results


def check_minor_daily_cap(*, country: str, hours: float, work_date: date) -> None:
    """Register row: minors' hour caps. Raises when a minor's day exceeds the cap."""
    cap = evaluate(_minor_ruleset(), {"country": country}, work_date).output
    if hours > cap:
        raise MinorHourCapError(f"minor daily cap {cap}h exceeded ({hours}h) on {work_date}")


# ---------- Period close & retro ----------

def compile_period(
    session: Session, *, person_id, period_key: str, period_start: date,
    period_end: date, rates: dict, default_pay_group: str = "default",
) -> list[TimeResult]:
    """Compile calculation lines into canonical TimeResult rows (earnings code ×
    hours × rate). Split by the worker's pay group (mid-period transfer rows
    land separately per worker — register row)."""
    calc = calculate_period(session, person_id=person_id,
                            period_start=period_start, period_end=period_end)
    rows: list[TimeResult] = []
    for worker_id, lines in calc.items():
        pay_group = session.scalar(
            select(TimeEntry.pay_group).where(
                TimeEntry.worker_id == worker_id,
                TimeEntry.work_date >= period_start,
                TimeEntry.work_date <= period_end,
            ).order_by(TimeEntry.work_date.desc()).limit(1)
        ) or default_pay_group
        for line in lines:
            row = TimeResult(
                worker_id=worker_id, period_key=period_key, pay_group=pay_group,
                earnings_code=line.earnings_code, hours=line.hours,
                rate=rates.get(worker_id, rates.get("default", 0)),
                explanation=line.explanation,
            )
            session.add(row)
            rows.append(row)
    session.flush()
    return rows


def lock_period(session: Session, *, period_key: str) -> int:
    results = session.scalars(
        select(TimeResult).where(TimeResult.period_key == period_key,
                                 TimeResult.locked == False)  # noqa: E712
    ).all()
    for row in results:
        row.locked = True
    session.flush()
    return len(results)


def reprice_locked_period(
    session: Session, *, period_key: str, worker_id, new_rate,
) -> dict:
    """Retro engine (§6): a rate change against a locked period produces DELTA
    rows — original rows are untouched. Identity guaranteed:
    original + delta = recalculated."""
    originals = session.scalars(
        select(TimeResult).where(
            TimeResult.period_key == period_key,
            TimeResult.worker_id == worker_id,
            TimeResult.is_retro_delta == False,  # noqa: E712
        )
    ).all()
    if not originals:
        raise ValueError("nothing compiled for that period/worker")
    if not all(row.locked for row in originals):
        raise PeriodLockedError("retro repricing only applies to locked periods")

    deltas = []
    for original in originals:
        original_amount = Decimal(original.hours) * Decimal(original.rate)
        recalculated_amount = Decimal(original.hours) * Decimal(str(new_rate))
        delta_amount = recalculated_amount - original_amount
        if delta_amount == 0:
            continue
        # Delta expressed in the rate dimension: same hours, rate difference.
        delta = TimeResult(
            worker_id=worker_id, period_key=period_key, pay_group=original.pay_group,
            earnings_code=f"RETRO_{original.earnings_code}", hours=original.hours,
            rate=Decimal(str(new_rate)) - Decimal(original.rate),
            is_retro_delta=True, origin_result_id=original.result_id,
            explanation=f"retro reprice {original.rate}->{new_rate} of {original.result_id}",
            locked=True,
        )
        session.add(delta)
        deltas.append(delta)
    session.flush()
    return {"originals": originals, "deltas": deltas}


def reconciliation_identity_holds(originals, deltas, recalculated_rate) -> bool:
    """original + delta = recalculated, to the penny (Decimal arithmetic)."""
    original_total = sum(Decimal(r.hours) * Decimal(r.rate) for r in originals)
    delta_total = sum(Decimal(d.hours) * Decimal(d.rate) for d in deltas)
    recalculated_total = sum(
        Decimal(r.hours) * Decimal(str(recalculated_rate)) for r in originals
    )
    return original_total + delta_total == recalculated_total


# ---------- Accruals ----------

def grant_accrual(
    session: Session, *, worker_id, absence_type: str, granted_on: date,
    hours: float, expires_on: date | None = None, balance_cap: float | None = None,
) -> AccrualLot:
    if balance_cap is not None:
        current = balance(session, worker_id=worker_id, absence_type=absence_type, as_of=granted_on)
        hours = min(hours, max(0.0, balance_cap - current))  # cap-aware grant
    lot = AccrualLot(worker_id=worker_id, absence_type=absence_type,
                     granted_on=granted_on, hours_granted=hours, expires_on=expires_on)
    session.add(lot)
    session.flush()
    return lot


def balance(session: Session, *, worker_id, absence_type: str, as_of: date) -> float:
    lots = session.scalars(select(AccrualLot).where(
        AccrualLot.worker_id == worker_id, AccrualLot.absence_type == absence_type,
        AccrualLot.granted_on <= as_of,
    )).all()
    total = 0.0
    for lot in lots:
        if lot.expires_on is not None and lot.expires_on < as_of:
            continue  # expired lot: unconsumed remainder is forfeited
        total += float(lot.hours_granted) - float(lot.hours_consumed)
    return round(total, 2)


def consume(
    session: Session, *, worker_id, absence_type: str, hours: float, on_date: date,
    negative_limit: float = 0.0,
) -> None:
    """FIFO by expiry (expiring lots first), then by grant date. Negative
    balances allowed only within the configured limit."""
    available = balance(session, worker_id=worker_id, absence_type=absence_type, as_of=on_date)
    if available - hours < -negative_limit:
        raise NegativeBalanceError(
            f"request {hours}h exceeds balance {available}h + negative limit {negative_limit}h"
        )
    lots = sorted(
        session.scalars(select(AccrualLot).where(
            AccrualLot.worker_id == worker_id, AccrualLot.absence_type == absence_type,
        )).all(),
        key=lambda lot: (lot.expires_on or date.max, lot.granted_on),
    )
    remaining = hours
    for lot in lots:
        if remaining <= 0:
            break
        if lot.expires_on is not None and lot.expires_on < on_date:
            continue
        lot_available = float(lot.hours_granted) - float(lot.hours_consumed)
        take = min(lot_available, remaining)
        lot.hours_consumed = float(lot.hours_consumed) + take
        remaining -= take
    if remaining > 0:  # negative balance within limit: tracked on newest lot
        lots[-1].hours_consumed = float(lots[-1].hours_consumed) + remaining
    session.flush()


def projected_balance(
    session: Session, *, worker_id, absence_type: str, as_of: date,
    pending_request_hours: float = 0.0,
) -> float:
    """'Balance as of future date X given pending requests' (§4) — the #1 HR question."""
    return round(
        balance(session, worker_id=worker_id, absence_type=absence_type, as_of=as_of)
        - pending_request_hours, 2,
    )
