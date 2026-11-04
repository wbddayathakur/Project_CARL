"""The shapes the rest of the agent passes around, and the bucketing rules.

The only genuinely opinionated thing in here is `Buckets`. Everything else is
plumbing.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Iterable, Optional

# The four buckets, in the order they are drawn in the progress bar.
DONE = "done"
BUILD = "build"
REQUIREMENTS = "requirements"
EXCLUDED = "excluded"


class Buckets:
    """Maps a Jira status name to a progress bucket.

    Status names are compared case-insensitively and with surrounding
    whitespace stripped, because Jira workflows accumulate near-duplicates
    ("Ready For UAT" vs "Ready for UAT") and a silent miss here would show up
    as work vanishing from the totals rather than as an error.
    """

    def __init__(self, cfg: dict):
        self._map: dict[str, str] = {}
        for bucket in (DONE, BUILD, REQUIREMENTS, EXCLUDED):
            for status in cfg.get(bucket, []) or []:
                self._map[self._norm(status)] = bucket
        self.in_progress = tuple(cfg.get("in_progress_buckets") or [BUILD, REQUIREMENTS])
        # Statuses seen in the wild that matched nothing, so the run can report
        # them instead of quietly dropping the points.
        self.unmapped: set[str] = set()

    @staticmethod
    def _norm(s: str) -> str:
        return " ".join(str(s or "").split()).casefold()

    def of(self, status: str) -> str:
        bucket = self._map.get(self._norm(status))
        if bucket is None:
            self.unmapped.add(status)
            # An unknown status is unstarted work, not finished work. Guessing
            # `done` would inflate the headline; guessing `requirements` only
            # understates it.
            return REQUIREMENTS
        return bucket

    def counts_as_in_progress(self, bucket: str) -> bool:
        return bucket in self.in_progress


@dataclass
class Story:
    key: str
    summary: str
    status: str
    bucket: str
    points: float
    assignee: str
    issue_type: str
    updated: Optional[str] = None


@dataclass
class Epic:
    key: str                      # "CARL-744"
    num: str                      # "744" — the HTML keys items by the bare number
    summary: str
    status: str
    assignee: str
    issue_type: str
    labels: list[str] = field(default_factory=list)
    due: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    parent_key: Optional[str] = None      # Tech Capability above the epic
    parent_summary: Optional[str] = None
    stories: list[Story] = field(default_factory=list)

    # Filled by roll_up()
    points_total: float = 0.0
    points_done: float = 0.0
    points_build: float = 0.0
    points_requirements: float = 0.0
    ticket_count: int = 0
    blocked_points: float = 0.0

    def roll_up(self, buckets: Buckets) -> None:
        """Sum child story points into the epic.

        Children in an excluded status (Archive, Cancelled) are dropped from
        both the numerator and the denominator. Counting them in the
        denominator would make a tidied-up backlog look like a regression.
        """
        self.points_total = 0.0
        self.points_done = 0.0
        self.points_build = 0.0
        self.points_requirements = 0.0
        self.ticket_count = 0
        self.blocked_points = 0.0

        for s in self.stories:
            if s.bucket == EXCLUDED:
                continue
            self.ticket_count += 1
            self.points_total += s.points
            if s.bucket == DONE:
                self.points_done += s.points
            elif s.bucket == BUILD:
                self.points_build += s.points
            else:
                self.points_requirements += s.points
            if s.status.strip().casefold() == "blocked":
                self.blocked_points += s.points

    @property
    def points_in_progress(self) -> float:
        return self.points_build + self.points_requirements

    @property
    def pct_done(self) -> float:
        return (self.points_done / self.points_total * 100) if self.points_total else 0.0

    @property
    def sized(self) -> bool:
        return self.points_total > 0

    def sp_array(self) -> list:
        """The [total, done, build, requirements] array the HTML renders.

        Returns [0, 0, 0, 0] for an unsized epic rather than None, so the page
        can distinguish "no points" from "no data" — the v3 file used both and
        the two rendered identically.
        """
        return [
            _round(self.points_total),
            _round(self.points_done),
            _round(self.points_build),
            _round(self.points_requirements),
        ]


@dataclass
class Rollup:
    """Aggregate over a set of epics — used for programs and sub-projects."""

    epics: int = 0
    tickets: int = 0
    total: float = 0.0
    done: float = 0.0
    build: float = 0.0
    requirements: float = 0.0
    blocked: float = 0.0
    done_epics: int = 0
    red: int = 0
    amber: int = 0
    green: int = 0

    @classmethod
    def over(cls, epics: Iterable[Epic], rag_of) -> "Rollup":
        r = cls()
        for e in epics:
            r.epics += 1
            r.tickets += e.ticket_count
            r.total += e.points_total
            r.done += e.points_done
            r.build += e.points_build
            r.requirements += e.points_requirements
            r.blocked += e.blocked_points
            if rag_of(e) == "R":
                r.red += 1
            elif rag_of(e) == "A":
                r.amber += 1
            else:
                r.green += 1
            if e.points_total and e.points_done >= e.points_total:
                r.done_epics += 1
        return r

    @property
    def pct_done(self) -> float:
        return (self.done / self.total * 100) if self.total else 0.0

    @property
    def in_progress(self) -> float:
        return self.build + self.requirements


def _round(x: float) -> float:
    """Story points are halves at worst; keep them readable in the JSON blob."""
    return int(x) if float(x).is_integer() else round(x, 1)


def rag_for(epic: Epic, rules: dict, today: Optional[dt.date] = None) -> str:
    """Red / Amber / Green for one epic.

    Deliberately boring and explainable: an exec asking "why is this red?"
    should get an answer that fits in a sentence.
    """
    today = today or dt.date.today()
    due = _as_date(epic.due)
    overdue = bool(due and due < today and epic.pct_done < 100)

    red = rules.get("red") or []
    for rule in red:
        if "overdue_and_under" in rule and overdue:
            if epic.pct_done < rule["overdue_and_under"]:
                return "R"
        if "blocked_share_over" in rule and epic.points_in_progress:
            share = epic.blocked_points / epic.points_in_progress * 100
            if share > rule["blocked_share_over"]:
                return "R"

    amber = rules.get("amber") or []
    for rule in amber:
        if rule.get("overdue") and overdue:
            return "A"
        if "due_within_days_and_under" in rule and due:
            days, pct = rule["due_within_days_and_under"]
            if 0 <= (due - today).days <= days and epic.pct_done < pct:
                return "A"
        if rule.get("unsized") and epic.stories and not epic.sized:
            return "A"

    return "G"


def _as_date(value) -> Optional[dt.date]:
    if not value:
        return None
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
