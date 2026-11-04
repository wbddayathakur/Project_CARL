"""RAG must be scored against the dates the page displays, not Jira's due field.

CARL does not fill Jira's due date. Committed dates live in the registry, so
scoring on `epic.due` alone made every epic green regardless of how late it was.
"""

import datetime as dt
from types import SimpleNamespace

from carl_roadmap.agent import _apply_committed_dates
from carl_roadmap.model import Epic, rag_for

RAG = {"red": [{"overdue_and_under": 25}], "amber": [{"overdue": True}]}
TODAY = dt.date(2026, 11, 4)


class FakeRegistry:
    def __init__(self, entries):
        self._e = entries

    def entry(self, num):
        return self._e.get(num, {})


def epic(num, **kw):
    e = Epic.__new__(Epic)
    e.__dict__.update(num=num, due=None, **kw)
    return e


def test_committed_target_makes_a_late_epic_visible(monkeypatch):
    e = epic("3639")
    reg = FakeRegistry({"3639": {"t": "2026-10-30"}})
    _apply_committed_dates([e], reg)
    assert e.due == "2026-10-30"


def test_revised_forecast_wins_over_original_target():
    e = epic("1")
    _apply_committed_dates([e], FakeRegistry({"1": {"t": "2026-09-01", "fc": "2026-12-01"}}))
    assert e.due == "2026-12-01"


def test_epic_with_no_committed_date_keeps_jira_due():
    e = epic("2")
    e.due = "2026-11-30"
    _apply_committed_dates([e], FakeRegistry({}))
    assert e.due == "2026-11-30"
