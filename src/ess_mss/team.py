"""Team analytics lite (MSS-1, Specs/10 §4): hierarchy-scoped metrics with
small-population suppression. Register row: a manager-of-managers sees only
their own subtree, and any cut below n=5 is suppressed entirely."""
from dataclasses import dataclass

from platform_core.orgpath import within

SUPPRESSION_THRESHOLD = 5


@dataclass
class TeamMetrics:
    suppressed: bool
    headcount: int | None = None
    turnover_rate: float | None = None
    average_tenure_years: float | None = None


def team_metrics(roster: list[dict], *, requestor_org_path: str) -> TeamMetrics:
    """`roster` rows: {worker_id, org_path, tenure_years, terminated_in_period}.

    Scope is structural: rows outside the requestor's subtree are excluded
    BEFORE any computation, so out-of-scope workers can never influence (or
    leak through) an aggregate.
    """
    scoped = [r for r in roster if within(r["org_path"], requestor_org_path)]
    if len(scoped) < SUPPRESSION_THRESHOLD:
        return TeamMetrics(suppressed=True)
    terminated = sum(1 for r in scoped if r.get("terminated_in_period"))
    return TeamMetrics(
        suppressed=False,
        headcount=len(scoped),
        turnover_rate=round(terminated / len(scoped), 4),
        average_tenure_years=round(sum(r["tenure_years"] for r in scoped) / len(scoped), 2),
    )
