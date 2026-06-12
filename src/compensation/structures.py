"""Comp foundation (COMP-1): ranges, derived metrics, geo differentials,
range refresh with remediation."""
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from compensation.models import CompRecord, GradeRange, comp_key
from platform_core import temporal

CONFIG_DIR = Path(__file__).resolve().parent / "config"


def load_geo_zones(path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "geo_zones.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["zones"]


def load_components(path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "components.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["components"]


def set_range(session: Session, *, grade: str, country: str, currency: str,
              range_min: Decimal, range_mid: Decimal, range_max: Decimal,
              effective_date: date, actor: str, reason: str = "range-refresh") -> GradeRange:
    row = GradeRange(
        range_key=f"{grade}:{country}", grade=grade, country=country,
        currency=currency, range_min=range_min, range_mid=range_mid,
        range_max=range_max, effective_date=effective_date,
        action_code="insert", action_reason=reason,
    )
    temporal.insert_temporal(session, row, actor=actor, source_channel="comp-admin")
    return row


def range_as_of(session: Session, *, grade: str, country: str, as_of: date) -> GradeRange | None:
    return temporal.as_of(session, GradeRange, f"{grade}:{country}", as_of)


def zone_adjusted(range_value: Decimal, *, zone: str, zones: dict) -> Decimal:
    return (range_value * Decimal(str(zones[zone])) / 100).quantize(Decimal("0.01"))


def compa_ratio(salary: Decimal, rng: GradeRange) -> Decimal:
    return (salary / rng.range_mid).quantize(Decimal("0.0001"))


def range_penetration(salary: Decimal, rng: GradeRange) -> Decimal:
    span = rng.range_max - rng.range_min
    return ((salary - rng.range_min) / span).quantize(Decimal("0.0001"))


def compa_quartile(salary: Decimal, rng: GradeRange) -> int:
    """1..4 by range penetration; clamped for below-min/above-max."""
    pen = range_penetration(salary, rng)
    if pen < Decimal("0.25"):
        return 1
    if pen < Decimal("0.5"):
        return 2
    if pen < Decimal("0.75"):
        return 3
    return 4


def current_comp(session: Session, worker_id: str, *, as_of: date,
                 record_role: str = "home") -> CompRecord | None:
    return temporal.as_of(session, CompRecord, comp_key(worker_id, record_role), as_of)


def refresh_with_remediation(
    session: Session, *, grade: str, country: str, currency: str,
    range_min: Decimal, range_mid: Decimal, range_max: Decimal,
    effective_date: date, actor: str, workers: list[str],
) -> list[dict]:
    """Range refresh (§2): apply the new range and return the remediation list —
    every worker now below the new min, with the proposed bring-to-min amount.
    Proposals are returned, not auto-applied (human commits comp money)."""
    set_range(session, grade=grade, country=country, currency=currency,
              range_min=range_min, range_mid=range_mid, range_max=range_max,
              effective_date=effective_date, actor=actor)
    remediation = []
    for worker_id in workers:
        record = current_comp(session, worker_id, as_of=effective_date)
        if record is None or record.grade != grade or record.country != country:
            continue
        if record.base_annual < range_min:
            remediation.append({
                "worker_id": worker_id,
                "current": record.base_annual,
                "new_min": range_min,
                "proposed_increase": range_min - record.base_annual,
            })
    return remediation
