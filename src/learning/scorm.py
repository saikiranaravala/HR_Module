"""SCORM runtime slice (LEARN-1): suspend/resume with corruption fallback.

Register row: corrupted suspend data must not cost the learner their progress
protection — resume falls back to the last good checkpoint and the attempt
counter is NOT incremented for the corruption."""
import hashlib

from sqlalchemy.orm import Session

from learning.models import Assignment


def _checksum(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def save_suspend(session: Session, assignment: Assignment, *, data: str) -> Assignment:
    assignment.suspend_data = data
    assignment.suspend_checksum = _checksum(data)
    assignment.status = "in-progress"
    session.flush()
    return assignment


def resume(session: Session, assignment: Assignment) -> dict:
    """Returns {data, fallback}: on checksum mismatch the corrupt blob is
    discarded, the learner restarts the module WITHOUT losing an attempt."""
    if assignment.suspend_data is None:
        return {"data": None, "fallback": False}
    if _checksum(assignment.suspend_data) != assignment.suspend_checksum:
        assignment.suspend_data = None
        assignment.suspend_checksum = None
        session.flush()
        return {"data": None, "fallback": True, "attempt_protected": True}
    return {"data": assignment.suspend_data, "fallback": False}


def start_attempt(session: Session, assignment: Assignment) -> Assignment:
    assignment.attempts += 1
    assignment.status = "in-progress"
    session.flush()
    return assignment
