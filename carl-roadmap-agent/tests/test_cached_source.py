"""The cache door must produce the same epics the REST door would."""

import json

import pytest

from carl_roadmap.model import Buckets
from carl_roadmap.sources.cached import CacheError, load

BUCKETS = {
    "done": ["Done"],
    "build": ["In Progress", "Blocked"],
    "requirements": ["To Do", "In Triage"],
    "excluded": ["Archive"],
}


def write(tmp_path, blob):
    p = tmp_path / "cache.json"
    p.write_text(json.dumps(blob), encoding="utf-8")
    return p


def test_rolls_children_into_buckets(tmp_path):
    p = write(tmp_path, {
        "epics": [{"key": "CARL-9", "summary": "E", "status": "In Progress",
                   "assignee": "A", "ticket_count": 10}],
        "children": [
            ["CARL-10", "CARL-9", "Done", 5],
            ["CARL-11", "CARL-9", "In Progress", 3],
            ["CARL-12", "CARL-9", "In Triage", 2],
            ["CARL-13", "CARL-9", "Archive", 8],
        ],
    })
    (epic,) = load(p, Buckets(BUCKETS))
    # The archived child leaves both numerator and denominator.
    assert epic.sp_array() == [10, 5, 3, 2]
    assert epic.num == "9"


def test_declared_ticket_count_wins_over_pointed_children(tmp_path):
    """Only pointed children are cached, so the rolled-up count undercounts."""
    p = write(tmp_path, {
        "epics": [{"key": "CARL-9", "summary": "E", "status": "To Do",
                   "ticket_count": 43}],
        "children": [["CARL-10", "CARL-9", "Done", 5]],
    })
    (epic,) = load(p, Buckets(BUCKETS))
    assert epic.ticket_count == 43
    assert epic.points_total == 5


def test_epic_with_no_cached_children_is_unsized_not_missing(tmp_path):
    p = write(tmp_path, {
        "epics": [{"key": "CARL-9", "summary": "E", "status": "To Do",
                   "ticket_count": 0}],
        "children": [],
    })
    (epic,) = load(p, Buckets(BUCKETS))
    assert epic.sp_array() == [0, 0, 0, 0]
    assert epic.sized is False


def test_missing_cache_says_how_to_fix_it(tmp_path):
    with pytest.raises(CacheError, match="no Jira cache"):
        load(tmp_path / "nope.json", Buckets(BUCKETS))


def test_children_of_unknown_parents_are_ignored(tmp_path):
    """Sub-tasks hang off stories, not epics; they must not invent an epic."""
    p = write(tmp_path, {
        "epics": [{"key": "CARL-9", "summary": "E", "status": "To Do",
                   "ticket_count": 1}],
        "children": [
            ["CARL-10", "CARL-9", "Done", 5],
            ["CARL-20", "CARL-316", "Done", 99],
        ],
    })
    epics = load(p, Buckets(BUCKETS))
    assert len(epics) == 1
    assert epics[0].points_total == 5
