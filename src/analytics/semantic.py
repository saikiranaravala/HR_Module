"""Semantic layer (Specs/11 §3): the governed metric registry is the ONLY
place metrics are defined; this module evaluates exactly the formulas the
registry names. "Headcount" is defined once, enterprise-wide."""
from datetime import date
from pathlib import Path

import yaml

from analytics.models import DimWorker
from analytics.orgmap import map_path
from platform_core.orgpath import within

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "metrics.yaml"


class UnknownMetricError(LookupError):
    pass


def load_registry(path: Path = CONFIG_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["metrics"]


def _population(rows: list[DimWorker], spec: dict) -> list[DimWorker]:
    """Contractor inclusion is a per-metric registry toggle (register row)."""
    if spec.get("include_contingent", False):
        return rows
    return [r for r in rows if r.worker_type == "employee"]


def evaluate(registry: dict, metric: str, rows: list[DimWorker], *,
             as_of: date, bridges: list | None = None,
             org_filter: str | None = None) -> float:
    if metric not in registry:
        raise UnknownMetricError(f"metric '{metric}' is not in the governed registry")
    spec = registry[metric]
    pop = _population(rows, spec)
    if org_filter is not None:
        # Bridge-translate each row's org so pre-reorg history trends
        # like-for-like under the new structure (register row).
        pop = [r for r in pop
               if within(map_path(r.org_path, bridges or [], as_of=as_of), org_filter)]

    formula = spec["formula"]
    if formula == "headcount-point-in-time":
        return float(len([r for r in pop if not r.exited]))
    if formula == "headcount-fte-weighted":
        return float(sum(float(r.fte) for r in pop if not r.exited))
    if formula == "turnover-annualized":
        exits = len([r for r in pop if r.exited])
        active = len([r for r in pop if not r.exited])
        if active == 0:
            return 0.0
        months = spec.get("window_months", 12)
        return round(exits / active * (12 / months), 4)
    if formula == "turnover-regrettable":
        exits = [r for r in pop if r.exited]
        if not exits:
            return 0.0
        return round(len([r for r in exits if r.regrettable_exit]) / len(exits), 4)
    if formula == "span-of-control":
        managers = {r.org_path for r in pop}
        if not managers:
            return 0.0
        return round(len(pop) / len(managers), 2)
    raise UnknownMetricError(f"formula '{formula}' is not implemented")
