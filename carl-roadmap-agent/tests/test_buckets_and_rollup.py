"""The bucketing rule is the thing most likely to be wrong and least likely to
be noticed, so it gets the most tests.

The rule under test: To Do and In Triage are in progress, because the PM is
holding those stories to gather requirements with stakeholders. They are a
separate bucket from build work, not a separate category from active work.
"""

import datetime as dt

import pytest

from carl_roadmap.model import BUILD, DONE, EXCLUDED, REQUIREMENTS, Buckets, Epic, Story, rag_for

CFG = {
    "done": ["Done", "Closed"],
    "build": ["In Progress", "In UAT", "Ready for Testing", "Blocked"],
    "requirements": ["To Do", "In Triage", "Pending Scope"],
    "excluded": ["Archive", "Cancelled"],
    "in_progress_buckets": ["build", "requirements"],
}


def buckets():
    return Buckets(CFG)


def story(key, status, points, **kw):
    b = buckets()
    return Story(
        key=key,
        summary=kw.get("summary", key),
        status=status,
        bucket=b.of(status),
        points=points,
        assignee=kw.get("assignee", "Someone"),
        issue_type="Story",
    )


def epic(key="CARL-1", stories=(), **kw):
    e = Epic(
        key=key,
        num=key.split("-")[1],
        summary=kw.get("summary", "An epic"),
        status=kw.get("status", "In Progress"),
        assignee=kw.get("assignee", "Someone"),
        issue_type="Epic",
        due=kw.get("due"),
        updated=kw.get("updated"),
    )
    e.stories = list(stories)
    e.roll_up(buckets())
    return e


# ------------------------------------------------------------------ bucketing


@pytest.mark.parametrize(
    "status,expected",
    [
        ("Done", DONE),
        ("Closed", DONE),
        ("In Progress", BUILD),
        ("Blocked", BUILD),
        ("To Do", REQUIREMENTS),
        ("In Triage", REQUIREMENTS),
        ("Pending Scope", REQUIREMENTS),
        ("Archive", EXCLUDED),
    ],
)
def test_status_maps_to_bucket(status, expected):
    assert buckets().of(status) == expected


def test_to_do_and_triage_count_as_in_progress():
    b = buckets()
    assert b.counts_as_in_progress(b.of("To Do"))
    assert b.counts_as_in_progress(b.of("In Triage"))
    assert not b.counts_as_in_progress(b.of("Done"))


def test_status_matching_is_case_and_space_insensitive():
    b = buckets()
    assert b.of("  in   progress ") == BUILD
    assert b.of("READY FOR TESTING") == BUILD


def test_unknown_status_is_requirements_not_done():
    """Guessing `done` would inflate the headline; this only understates it."""
    b = buckets()
    assert b.of("Awaiting Vendor") == REQUIREMENTS
    assert "Awaiting Vendor" in b.unmapped


# -------------------------------------------------------------------- rollups


def test_epic_sums_children_into_three_buckets():
    e = epic(
        stories=[
            story("S1", "Done", 5),
            story("S2", "Done", 3),
            story("S3", "In Progress", 8),
            story("S4", "To Do", 13),
            story("S5", "In Triage", 2),
        ]
    )
    assert e.points_total == 31
    assert e.points_done == 8
    assert e.points_build == 8
    assert e.points_requirements == 15
    assert e.points_in_progress == 23
    assert e.ticket_count == 5


def test_archived_children_leave_the_denominator_entirely():
    """A tidied-up backlog must not read as a regression."""
    e = epic(stories=[story("S1", "Done", 5), story("S2", "Archive", 100)])
    assert e.points_total == 5
    assert e.pct_done == 100
    assert e.ticket_count == 1


def test_blocked_points_are_tracked_inside_build():
    e = epic(stories=[story("S1", "Blocked", 8), story("S2", "In Progress", 2)])
    assert e.points_build == 10
    assert e.blocked_points == 8


def test_sp_array_is_total_done_build_requirements():
    e = epic(stories=[story("S1", "Done", 5), story("S2", "In Progress", 3), story("S3", "To Do", 2)])
    assert e.sp_array() == [10, 5, 3, 2]


def test_unsized_epic_reports_zeroes_not_none():
    e = epic(stories=[story("S1", "To Do", 0)])
    assert e.sp_array() == [0, 0, 0, 0]
    assert not e.sized
    assert e.ticket_count == 1


def test_points_stay_readable_when_halved():
    e = epic(stories=[story("S1", "Done", 2.5), story("S2", "To Do", 0.5)])
    assert e.sp_array() == [3, 2.5, 0, 0.5]


def test_empty_epic_does_not_divide_by_zero():
    e = epic()
    assert e.pct_done == 0
    assert e.sp_array() == [0, 0, 0, 0]


# ------------------------------------------------------------------------ rag

RAG = {
    "red": [{"overdue_and_under": 25}, {"blocked_share_over": 40}],
    "amber": [{"overdue": True}, {"due_within_days_and_under": [30, 50]}, {"unsized": True}],
}
TODAY = dt.date(2026, 10, 15)


def test_overdue_and_barely_started_is_red():
    e = epic(due="2026-09-01", stories=[story("S1", "To Do", 100)])
    assert rag_for(e, RAG, TODAY) == "R"


def test_overdue_but_mostly_done_is_amber_not_red():
    e = epic(due="2026-09-01", stories=[story("S1", "Done", 90), story("S2", "To Do", 10)])
    assert rag_for(e, RAG, TODAY) == "A"


def test_mostly_blocked_is_red_even_when_not_overdue():
    e = epic(due="2027-06-01", stories=[story("S1", "Blocked", 9), story("S2", "In Progress", 1)])
    assert rag_for(e, RAG, TODAY) == "R"


def test_due_soon_and_half_done_is_amber():
    e = epic(due="2026-10-30", stories=[story("S1", "Done", 4), story("S2", "To Do", 6)])
    assert rag_for(e, RAG, TODAY) == "A"


def test_epic_with_tickets_but_no_estimate_is_amber():
    e = epic(stories=[story("S1", "To Do", 0)])
    assert rag_for(e, RAG, TODAY) == "A"


def test_on_track_is_green():
    e = epic(due="2027-01-31", stories=[story("S1", "Done", 8), story("S2", "To Do", 2)])
    assert rag_for(e, RAG, TODAY) == "G"


def test_completed_epic_past_its_date_is_not_overdue():
    e = epic(due="2026-09-01", stories=[story("S1", "Done", 10)])
    assert rag_for(e, RAG, TODAY) == "G"
