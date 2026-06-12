"""Review cycles (PERF-2): templates (ratings-philosophy gate isolated in
config), launch with eligibility snapshot, leave extensions."""
from datetime import date, timedelta
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from performance.models import ReviewCycle, ReviewDoc

CONFIG_DIR = Path(__file__).resolve().parent / "config"

MIN_TENURE_DAYS = 90  # spec §3: auto-exclusion under 90 days


class TemplateError(ValueError):
    pass


def load_template(key: str, path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "templates.yaml"
    template = yaml.safe_load(path.read_text(encoding="utf-8"))["templates"][key]
    weights = template.get("participant_weights")
    if weights is not None and sum(weights.values()) != 100:
        # Register row: matrix-manager weighting conflicts are rejected at
        # template validation, not discovered at calibration.
        raise TemplateError(
            f"participant weights must sum to 100, got {sum(weights.values())} "
            f"({weights}) — resolve the matrix-manager conflict in config"
        )
    return template


def launch_cycle(
    session: Session, *, name: str, template_key: str, launched_on: date,
    window_end: date, population: list[dict],
) -> tuple[ReviewCycle, list[ReviewDoc]]:
    """Population snapshot at launch; late hires (<90d tenure) auto-excluded;
    mid-window hires beyond cutoff are prorated (§3 late-hire rules)."""
    template = load_template(template_key)
    cycle = ReviewCycle(name=name, template_key=template_key,
                        launched_on=launched_on, window_end=window_end)
    session.add(cycle)
    session.flush()
    docs = []
    for member in population:
        tenure_days = (launched_on - member["hire_date"]).days
        if tenure_days < template.get("min_tenure_days", MIN_TENURE_DAYS):
            continue  # auto-excluded
        doc = ReviewDoc(
            cycle_id=cycle.cycle_id, worker_id=member["worker_id"],
            manager_id=member["manager_id"],
            prorated=tenure_days < 365,
            restricted=template.get("restricted", False),
        )
        session.add(doc)
        docs.append(doc)
    session.flush()
    return cycle, docs


def extend_for_leave(doc: ReviewDoc, *, leave_type: str, window_end: date,
                     template: dict) -> ReviewDoc:
    """Register row: worker on leave during the window gets an auto-extension
    per leave type (country packs refine the days in config)."""
    days = template.get("leave_extension_days", {}).get(leave_type)
    if days is None:
        raise TemplateError(f"no extension policy for leave type '{leave_type}'")
    doc.extension_until = window_end + timedelta(days=days)
    return doc
