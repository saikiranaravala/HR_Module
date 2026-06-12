"""Analytics tests (Specs/11): semantic layer, SCD2 + restatement policy,
certified snapshot immutability, suppression, inherited report security, and
the §8 edge-case register."""
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from analytics import orgmap, reports, scd2, semantic, snapshots, suppression
from analytics.models import HIGH_DATE, OrgBridge
from platform_core.policy.engine import PolicyEngine, Subject

REGISTRY = semantic.load_registry()
POLICY = PolicyEngine()


def _seed(session, n_employees=6, n_contingent=2, org="/corp/eng/"):
    for i in range(n_employees):
        scd2.apply_change(session, worker_key=f"e{i}", effective_from=date(2026, 1, 1),
                          org_path=org, country="US", worker_type="employee", fte=1.0)
    for i in range(n_contingent):
        scd2.apply_change(session, worker_key=f"c{i}", effective_from=date(2026, 1, 1),
                          org_path=org, country="US", worker_type="contingent", fte=0.5)


# --- Semantic layer -----------------------------------------------------------

def test_metric_must_be_registered(session):
    with pytest.raises(semantic.UnknownMetricError):
        semantic.evaluate(REGISTRY, "shadow-headcount", [], as_of=date(2026, 6, 1))


def test_ANLT_contractor_inclusion_toggle(session):
    """Register row: contractor inclusion is a per-metric registry toggle —
    'headcount' excludes contingent, the total-workforce variant includes them."""
    _seed(session)
    rows = scd2.rows_as_of(session, date(2026, 6, 1))
    assert semantic.evaluate(REGISTRY, "headcount", rows, as_of=date(2026, 6, 1)) == 6.0
    assert semantic.evaluate(REGISTRY, "headcount-total-workforce", rows,
                             as_of=date(2026, 6, 1)) == 8.0
    assert semantic.evaluate(REGISTRY, "headcount-fte", rows, as_of=date(2026, 6, 1)) == 6.0


def test_scd2_point_in_time_headcount(session):
    _seed(session, n_employees=3, n_contingent=0)
    # one worker exits effective 2026-04-01
    scd2.apply_change(session, worker_key="e0", effective_from=date(2026, 4, 1),
                      org_path="/corp/eng/", country="US", worker_type="employee",
                      fte=1.0, exited=True)
    march = scd2.rows_as_of(session, date(2026, 3, 31))
    june = scd2.rows_as_of(session, date(2026, 6, 1))
    assert semantic.evaluate(REGISTRY, "headcount", march, as_of=date(2026, 3, 31)) == 3.0
    assert semantic.evaluate(REGISTRY, "headcount", june, as_of=date(2026, 6, 1)) == 2.0


# --- Register: retro restatement vs snapshot immutability ---------------------

def test_ANLT_retro_restates_facts_snapshots_immutable(session):
    """Register row: retro transactions restate SCD2 facts; certified snapshots
    are immutable — corrections are new annotated versions, originals remain."""
    _seed(session, n_employees=5, n_contingent=0)
    rows = scd2.rows_as_of(session, date(2026, 6, 1))
    original = snapshots.certify(
        session, as_of=date(2026, 6, 1), metric="headcount",
        value=semantic.evaluate(REGISTRY, "headcount", rows, as_of=date(2026, 6, 1)),
    )
    # Retro: e4 actually exited back in May — facts restate…
    scd2.restate(session, worker_key="e4", on=date(2026, 5, 15), exited=True)
    restated_rows = scd2.rows_as_of(session, date(2026, 6, 1))
    new_value = semantic.evaluate(REGISTRY, "headcount", restated_rows, as_of=date(2026, 6, 1))
    assert new_value == 4.0

    # …the certified snapshot does NOT mutate (DB guard), it gains a version.
    with pytest.raises(ProgrammingError, match="immutable"):
        with session.begin_nested():  # savepoint: only the UPDATE rolls back
            session.execute(text(
                "UPDATE analytics.certified_snapshot SET value = 4 WHERE snapshot_id = :sid"
            ), {"sid": original.snapshot_id})

    restated = snapshots.restate_snapshot(
        session, snapshots.current_certified(session, as_of=date(2026, 6, 1), metric="headcount"),
        value=new_value, annotation="retro exit e4 effective 2026-05-15",
    )
    assert restated.version == 2 and restated.restatement_of is not None
    current = snapshots.current_certified(session, as_of=date(2026, 6, 1), metric="headcount")
    assert float(current.value) == 4.0 and current.annotation.startswith("retro exit")


# --- Register: reorg bridge ----------------------------------------------------

def test_ANLT_reorg_bridge_like_for_like_trend(session):
    """Register row: after /corp/eng/platform → /corp/product/platform, the
    bridge keeps pre-reorg history trending under the new org."""
    for i in range(5):
        scd2.apply_change(session, worker_key=f"e{i}", effective_from=date(2026, 1, 1),
                          org_path="/corp/eng/platform/", country="US",
                          worker_type="employee", fte=1.0)
    bridge = OrgBridge(old_org_path="/corp/eng/platform/",
                       new_org_path="/corp/product/platform/",
                       effective_date=date(2026, 6, 1))
    session.add(bridge)
    session.flush()

    rows = scd2.rows_as_of(session, date(2026, 3, 1))  # pre-reorg history
    # Without the bridge the new org shows no history; with it, like-for-like.
    assert semantic.evaluate(REGISTRY, "headcount", rows, as_of=date(2026, 3, 1),
                             org_filter="/corp/product/platform/") == 0.0
    assert semantic.evaluate(REGISTRY, "headcount", rows, as_of=date(2026, 6, 2),
                             bridges=[bridge], org_filter="/corp/product/platform/") == 5.0
    assert orgmap.map_path("/corp/eng/platform/team-a/", [bridge],
                           as_of=date(2026, 7, 1)) == "/corp/product/platform/team-a/"


# --- Register: complementary suppression ----------------------------------------

def test_ANLT_complementary_suppression_no_subtraction():
    """Register row: a single suppressed cell must not be recoverable by
    subtracting visible cells from the total — the next-smallest cell is
    suppressed too."""
    breakdown = {"US": 40, "DE": 12, "FR": 3}
    result = suppression.suppress(breakdown)
    assert result["FR"] is None          # n<5
    assert result["DE"] is None          # complementary partner
    assert result["US"] == 40

    # two cells already below threshold: no extra partner needed
    result2 = suppression.suppress({"US": 40, "DE": 4, "FR": 3})
    assert result2 == {"US": 40, "DE": None, "FR": None}

    # nothing suppressed: untouched
    assert suppression.suppress({"US": 40, "DE": 12}) == {"US": 40, "DE": 12}


# --- Inherited report security ---------------------------------------------------

def test_report_inherits_policy_rows_and_fields(session):
    """ANLT-1: the report path uses the same policy decision as the UI/API —
    a US-scoped admin's report shows no DE rows, ever."""
    scd2.apply_change(session, worker_key="us-1", effective_from=date(2026, 1, 1),
                      org_path="/corp/", country="US", worker_type="employee", fte=1.0)
    scd2.apply_change(session, worker_key="de-1", effective_from=date(2026, 1, 1),
                      org_path="/corp/", country="DE", worker_type="employee", fte=1.0)
    rows = scd2.rows_as_of(session, date(2026, 6, 1))

    us_admin = Subject("u-hr-us", ("hr-admin-us",))
    out = reports.run_report(session, POLICY, subject=us_admin, rows=rows,
                             columns=["worker_key", "country", "org_path"])
    assert [r["country"] for r in out] == ["US"]

    nobody = Subject("intern", ("unknown-role",))
    assert reports.run_report(session, POLICY, subject=nobody, rows=rows,
                              columns=["worker_key"]) == []
