"""Time & Labor tests (Specs/02): OT rules, accrual lots, period close,
and the §8 edge-case register."""
import uuid
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from time_labor import services
from time_labor.models import TimeEntry

LA = ZoneInfo("America/Los_Angeles")
DEN = ZoneInfo("America/Denver")


def _entry(session, worker, person, day_local, start_h, hours, tz=LA,
           country="US", state="CA", pay_group="us-biweekly"):
    start_local = datetime(day_local.year, day_local.month, day_local.day,
                           start_h, 0, tzinfo=tz)
    in_utc = start_local.astimezone(timezone.utc)
    out_utc = in_utc + __import__("datetime").timedelta(hours=hours)
    return services.record_entry(
        session, worker_id=worker, person_id=person, in_utc=in_utc, out_utc=out_utc,
        timezone_name=str(tz.key), pay_group=pay_group, country=country, state=state,
    )


def test_ca_daily_overtime_and_doubletime(session):
    worker, person = uuid.uuid4(), uuid.uuid4()
    _entry(session, worker, person, date(2026, 6, 1), 8, 14)  # 8 REG, 4 OT15, 2 OT20
    session.commit()

    calc = services.calculate_period(session, person_id=person,
                                     period_start=date(2026, 6, 1),
                                     period_end=date(2026, 6, 7))
    buckets = {line.earnings_code: line.hours for line in calc[worker]}
    assert buckets == {"REG": 8.0, "OT15": 4.0, "OT20": 2.0}
    assert "overtime-thresholds v1" in calc[worker][0].explanation  # explainability


def test_flsa_weekly_40(session):
    worker, person = uuid.uuid4(), uuid.uuid4()
    for offset in range(6):  # 6 × 8h = 48h, US default (no daily OT)
        _entry(session, worker, person, date(2026, 6, 1 + offset), 9, 8,
               tz=ZoneInfo("America/New_York"), state="NY")
    session.commit()
    calc = services.calculate_period(session, person_id=person,
                                     period_start=date(2026, 6, 1),
                                     period_end=date(2026, 6, 7))
    buckets = {line.earnings_code: line.hours for line in calc[worker]}
    assert buckets == {"REG": 40.0, "OT15": 8.0}


def test_TIME_multi_job_combined_hours_ot(session):
    """Register row: FLSA joint employment — combined hours across a person's
    concurrent jobs drive the weekly threshold."""
    person = uuid.uuid4()
    job_a, job_b = uuid.uuid4(), uuid.uuid4()
    for offset in range(5):  # job A: 5×6h = 30h
        _entry(session, job_a, person, date(2026, 6, 1 + offset), 8, 6,
               tz=ZoneInfo("America/New_York"), state="NY", pay_group="grp-a")
    for offset in range(5):  # job B: 5×4h = 20h → combined 50h ⇒ 10h OT
        _entry(session, job_b, person, date(2026, 6, 1 + offset), 16, 4,
               tz=ZoneInfo("America/New_York"), state="NY", pay_group="grp-b")
    session.commit()

    calc = services.calculate_period(session, person_id=person,
                                     period_start=date(2026, 6, 1),
                                     period_end=date(2026, 6, 7))
    total_ot = sum(line.hours for lines in calc.values()
                   for line in lines if line.earnings_code == "OT15")
    total_all = sum(line.hours for lines in calc.values() for line in lines)
    assert total_ot == 10.0
    assert total_all == 50.0


def test_TIME_midnight_spanning_shift_attribution(session):
    """Register row: a 20:00→04:00 shift attributes fully to the shift-START
    local date."""
    worker, person = uuid.uuid4(), uuid.uuid4()
    entry = _entry(session, worker, person, date(2026, 6, 1), 20, 8)
    session.commit()
    assert entry.work_date == date(2026, 6, 1)
    assert services.entry_hours(entry) == 8.0


def test_TIME_dst_transition_hours_from_utc(session):
    """Register row: spring-forward night (2026-03-08 US) — a 22:00→06:00
    local shift is only 7 elapsed hours; elapsed derives from UTC, never from
    local wall-clock subtraction."""
    worker, person = uuid.uuid4(), uuid.uuid4()
    start_local = datetime(2026, 3, 7, 22, 0, tzinfo=DEN)
    end_local = datetime(2026, 3, 8, 6, 0, tzinfo=DEN)  # wall clock says 8h
    entry = services.record_entry(
        session, worker_id=worker, person_id=person,
        in_utc=start_local.astimezone(timezone.utc),
        out_utc=end_local.astimezone(timezone.utc),
        timezone_name="America/Denver", pay_group="us-biweekly",
        country="US", state="CO",
    )
    session.commit()
    assert services.entry_hours(entry) == 7.0  # 23-hour day handled
    assert entry.work_date == date(2026, 3, 7)


def test_TIME_mid_period_transfer_split_results(session):
    """Register row: pay-group change mid-period → results split per worker/
    pay group, no blending."""
    person = uuid.uuid4()
    old_job, new_job = uuid.uuid4(), uuid.uuid4()
    _entry(session, old_job, person, date(2026, 6, 1), 9, 8, pay_group="grp-old",
           state="NY", tz=ZoneInfo("America/New_York"))
    _entry(session, new_job, person, date(2026, 6, 4), 9, 8, pay_group="grp-new",
           state="NY", tz=ZoneInfo("America/New_York"))
    session.commit()

    rows = services.compile_period(
        session, person_id=person, period_key="2026-P12",
        period_start=date(2026, 6, 1), period_end=date(2026, 6, 7),
        rates={"default": 30},
    )
    by_group = {(r.worker_id, r.pay_group) for r in rows}
    assert (old_job, "grp-old") in by_group and (new_job, "grp-new") in by_group


def test_TIME_retro_rate_change_delta_reconciles(session):
    """Register row + §6 acceptance: retro pay-rate change against a locked
    period produces deltas where original + delta = recalculated, exactly."""
    worker, person = uuid.uuid4(), uuid.uuid4()
    _entry(session, worker, person, date(2026, 6, 1), 8, 10)  # 8 REG + 2 OT15
    session.commit()

    originals = services.compile_period(
        session, person_id=person, period_key="2026-P12",
        period_start=date(2026, 6, 1), period_end=date(2026, 6, 7),
        rates={worker: 20},
    )
    services.lock_period(session, period_key="2026-P12")

    outcome = services.reprice_locked_period(
        session, period_key="2026-P12", worker_id=worker, new_rate=22,
    )
    session.commit()

    assert outcome["deltas"], "rate change must produce deltas"
    assert all(d.is_retro_delta and d.origin_result_id for d in outcome["deltas"])
    assert services.reconciliation_identity_holds(
        outcome["originals"], outcome["deltas"], recalculated_rate=22,
    )
    # originals untouched
    assert all(float(r.rate) == 20 for r in originals)


def test_retro_requires_lock(session):
    worker, person = uuid.uuid4(), uuid.uuid4()
    _entry(session, worker, person, date(2026, 6, 1), 9, 8)
    services.compile_period(session, person_id=person, period_key="2026-P13",
                            period_start=date(2026, 6, 1), period_end=date(2026, 6, 7),
                            rates={"default": 20})
    with pytest.raises(services.PeriodLockedError):
        services.reprice_locked_period(session, period_key="2026-P13",
                                       worker_id=worker, new_rate=25)


def test_TIME_minor_hour_cap_violation_detected():
    """Register row: minors' hour caps — exceeding the daily cap raises."""
    services.check_minor_daily_cap(country="US", hours=8, work_date=date(2026, 6, 1))
    with pytest.raises(services.MinorHourCapError, match="cap 8"):
        services.check_minor_daily_cap(country="US", hours=9.5, work_date=date(2026, 6, 1))


# ---------- Accruals ----------

def test_accrual_lots_fifo_with_expiry(session):
    worker = uuid.uuid4()
    services.grant_accrual(session, worker_id=worker, absence_type="pto",
                           granted_on=date(2026, 1, 1), hours=40,
                           expires_on=date(2026, 6, 30))  # carryover lot
    services.grant_accrual(session, worker_id=worker, absence_type="pto",
                           granted_on=date(2026, 1, 1), hours=80)  # current-year lot
    services.consume(session, worker_id=worker, absence_type="pto",
                     hours=50, on_date=date(2026, 5, 1))
    session.commit()

    # Expiring lot consumed first (FIFO by expiry): 40 from carryover, 10 from current.
    assert services.balance(session, worker_id=worker, absence_type="pto",
                            as_of=date(2026, 5, 2)) == 70.0
    # After the carryover lot expires nothing more is forfeited (it was used first).
    assert services.balance(session, worker_id=worker, absence_type="pto",
                            as_of=date(2026, 7, 1)) == 70.0


def test_carryover_expiry_forfeits_unused(session):
    worker = uuid.uuid4()
    services.grant_accrual(session, worker_id=worker, absence_type="pto",
                           granted_on=date(2026, 1, 1), hours=40,
                           expires_on=date(2026, 6, 30))
    assert services.balance(session, worker_id=worker, absence_type="pto",
                            as_of=date(2026, 6, 1)) == 40.0
    assert services.balance(session, worker_id=worker, absence_type="pto",
                            as_of=date(2026, 7, 1)) == 0.0  # forfeited


def test_negative_balance_limit(session):
    worker = uuid.uuid4()
    services.grant_accrual(session, worker_id=worker, absence_type="pto",
                           granted_on=date(2026, 1, 1), hours=8)
    with pytest.raises(services.NegativeBalanceError):
        services.consume(session, worker_id=worker, absence_type="pto",
                         hours=20, on_date=date(2026, 5, 1), negative_limit=8)
    services.consume(session, worker_id=worker, absence_type="pto",
                     hours=16, on_date=date(2026, 5, 1), negative_limit=8)
    assert services.balance(session, worker_id=worker, absence_type="pto",
                            as_of=date(2026, 5, 2)) == -8.0


def test_balance_projection(session):
    worker = uuid.uuid4()
    services.grant_accrual(session, worker_id=worker, absence_type="pto",
                           granted_on=date(2026, 1, 1), hours=80)
    projected = services.projected_balance(
        session, worker_id=worker, absence_type="pto",
        as_of=date(2026, 8, 1), pending_request_hours=24,
    )
    assert projected == 56.0


def test_accrual_cap_limits_grant(session):
    worker = uuid.uuid4()
    services.grant_accrual(session, worker_id=worker, absence_type="pto",
                           granted_on=date(2026, 1, 1), hours=150)
    lot = services.grant_accrual(session, worker_id=worker, absence_type="pto",
                                 granted_on=date(2026, 2, 1), hours=50, balance_cap=160)
    assert float(lot.hours_granted) == 10.0  # capped at 160 total
