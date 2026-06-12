"""Goal management (PERF-1): cascade, revision chains, orphan report, transfer."""
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from performance.models import Goal


def create_goal(session: Session, *, worker_id: str, title: str, goal_type: str,
                weight: int = 0, parent: Goal | None = None,
                visibility: str = "manager") -> Goal:
    goal = Goal(worker_id=worker_id, title=title, goal_type=goal_type, weight=weight,
                parent_goal_id=parent.goal_id if parent else None, visibility=visibility)
    session.add(goal)
    session.flush()
    return goal


def revise_goal(session: Session, goal: Goal, **changes) -> Goal:
    """Mid-cycle revision: version chain — the original row is preserved
    (status superseded), never edited in place."""
    goal.status = "superseded"
    revised = Goal(
        worker_id=goal.worker_id,
        title=changes.get("title", goal.title),
        goal_type=goal.goal_type,
        weight=changes.get("weight", goal.weight),
        parent_goal_id=goal.parent_goal_id,
        visibility=changes.get("visibility", goal.visibility),
        version=goal.version + 1,
        supersedes=goal.goal_id,
    )
    session.add(revised)
    session.flush()
    return revised


def orphan_report(session: Session, *, exclude_types: tuple = ("development",)) -> list[Goal]:
    """Leaders' view: active goals with no alignment parent (§2)."""
    return session.scalars(select(Goal).where(
        Goal.status == "active",
        Goal.parent_goal_id.is_(None),
        Goal.goal_type.notin_(exclude_types),
    )).all()


def transfer_goals(session: Session, *, worker_id: str, policy: str) -> list[Goal]:
    """Manager/worker move: 'travel-with-worker' keeps goals active;
    're-baseline' supersedes them for re-negotiation under the new manager."""
    goals = session.scalars(select(Goal).where(
        Goal.worker_id == worker_id, Goal.status == "active")).all()
    if policy == "travel-with-worker":
        return goals
    if policy == "re-baseline":
        return [revise_goal(session, g) for g in goals]
    raise ValueError(f"unknown transfer policy '{policy}'")
