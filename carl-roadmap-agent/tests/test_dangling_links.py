"""A carried-over link pointing at a deleted item must never reach the page.

The page does `byK[z].dep` with no guard, so one dangling key throws during
init and every tab renders blank. The failure is total and silent — the file
still opens, it is just empty — so this is worth a test of its own.
"""

from carl_roadmap.agent import _prune_dangling

ITEMS = [{"k": "744"}, {"k": "2888"}, {"k": "2778"}]


def test_drops_rel_whose_endpoint_is_gone():
    rels = [["744", "2888"], ["744", "3959"]]
    kept, _, dropped = _prune_dangling(rels, [], ITEMS)
    assert kept == [["744", "2888"]]
    assert len(dropped) == 1 and "3959" in dropped[0]


def test_keeps_rel_when_both_ends_live():
    rels = [["744", "2888"]]
    kept, _, dropped = _prune_dangling(rels, [], ITEMS)
    assert kept == rels and dropped == []


def test_prunes_missing_keys_from_a_dependency_without_losing_the_gate():
    """The external ask is still real even if one blocked epic vanished."""
    deps = [{"id": "X-SF", "n": "Salesforce source team", "b": ["2778", "3959"]}]
    _, kept, dropped = _prune_dangling([], deps, ITEMS)
    assert kept[0]["b"] == ["2778"]
    assert kept[0]["n"] == "Salesforce source team"
    assert len(dropped) == 1 and "X-SF" in dropped[0]


def test_dependency_blocking_nothing_is_still_kept():
    deps = [{"id": "X-GONE", "b": ["3959"]}]
    _, kept, dropped = _prune_dangling([], deps, ITEMS)
    assert len(kept) == 1 and kept[0]["b"] == []
    assert dropped


def test_original_dependency_is_not_mutated():
    deps = [{"id": "X-SF", "b": ["2778", "3959"]}]
    _prune_dangling([], deps, ITEMS)
    assert deps[0]["b"] == ["2778", "3959"]


def test_no_links_at_all_is_not_an_error():
    assert _prune_dangling([], [], ITEMS) == ([], [], [])
