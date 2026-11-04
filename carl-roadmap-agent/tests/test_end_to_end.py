"""Runs the whole agent against a copy of the real published page, with Jira
stubbed.

This is the test that would have caught every bug worth catching: it proves the
real file can be read, rewritten and re-read, that human-owned fields survive,
and that a brand-new epic lands somewhere visible instead of vanishing.
"""

import json
import shutil
from pathlib import Path

import pytest
import yaml

from carl_roadmap import agent
from carl_roadmap.config import Config
from carl_roadmap.model import Buckets, Epic, Story
from carl_roadmap.registry import extract_data_blob

REPO = Path(__file__).resolve().parent.parent
REAL_PAGE = Path(Config.load(REPO / "config.yaml").get("output", "html_path"))

pytestmark = pytest.mark.skipif(
    not REAL_PAGE.exists(), reason="published page not available on this machine"
)


def _story(key, status, pts, buckets):
    return Story(key=key, summary=key, status=status, bucket=buckets.of(status),
                 points=pts, assignee="Someone", issue_type="Story")


def _fake_epics(buckets):
    """Three epics: one known and finished, one known and mid-flight, one new."""
    known_done = Epic(key="CARL-744", num="744", summary="Ingest Operative Data (Bronze)",
                      status="Done", assignee="Diana Saafi", issue_type="Epic",
                      parent_summary="Unified Ads Data")
    known_done.stories = [_story("s1", "Done", 193, buckets)]

    mid = Epic(key="CARL-1756", num="1756", summary="Ingest Freewheel Data (Bronze Phase 2)",
               status="In Progress", assignee="Hong Zhang", issue_type="Epic",
               due="2026-09-01")
    mid.stories = [
        _story("s2", "Done", 5, buckets),
        _story("s3", "In Progress", 20, buckets),
        _story("s4", "To Do", 150, buckets),
        _story("s5", "In Triage", 6, buckets),
        _story("s6", "Archive", 999, buckets),
    ]

    brand_new = Epic(key="CARL-9999", num="9999", summary="Something opened this morning",
                     status="To Do", assignee="Nobody", issue_type="Epic")
    brand_new.stories = [_story("s7", "To Do", 3, buckets)]

    for e in (known_done, mid, brand_new):
        e.roll_up(buckets)
    return [known_done, mid, brand_new]


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """A full copy of the agent's inputs, pointed at a throwaway page."""
    page = tmp_path / "page.html"
    shutil.copy2(REAL_PAGE, page)

    cfg_doc = yaml.safe_load((REPO / "config.yaml").read_text(encoding="utf-8"))
    cfg_doc["output"]["html_path"] = str(page)
    cfg_doc["output"]["json_path"] = str(tmp_path / "out.json")
    cfg_doc["output"]["snapshot_dir"] = str(tmp_path / "history")
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg_doc), encoding="utf-8")

    shutil.copytree(REPO / "registry", tmp_path / "registry")

    cfg = Config.load(cfg_path)
    monkeypatch.setattr(
        agent, "_load_jira", lambda c, b: _fake_epics(b)
    )
    monkeypatch.setattr(agent, "_load_confluence", lambda c, skip: ({}, {}))
    return cfg, page


def test_full_run_rewrites_the_page(sandbox):
    cfg, page = sandbox
    report = agent.run(cfg, asof="2026-10-15")

    assert report["epics"] == 3
    assert report["html"]["changed"] is True

    blob = extract_data_blob(page)
    by_key = {i["k"]: i for i in blob["items"]}
    assert "744" in by_key and "1756" in by_key and "9999" in by_key


def test_human_owned_fields_survive_the_refresh(sandbox):
    """The programme structure must not be regenerated from Jira."""
    cfg, page = sandbox
    agent.run(cfg, asof="2026-10-15")
    item = {i["k"]: i for i in extract_data_blob(page)["items"]}["744"]
    assert item["p"] == "DF"                       # from the registry
    assert item["sub"].startswith("Iceberg")       # from the registry
    assert item["st"] == "Done"                    # from Jira
    assert item["o"] == "Diana Saafi"              # from Jira


def test_to_do_and_triage_land_in_the_in_progress_segment(sandbox):
    cfg, page = sandbox
    agent.run(cfg, asof="2026-10-15")
    item = {i["k"]: i for i in extract_data_blob(page)["items"]}["1756"]
    total, done, build, requirements = item["sp"]
    assert total == 181          # 999 archived points excluded
    assert done == 5
    assert build == 20           # In Progress
    assert requirements == 156   # To Do 150 + In Triage 6
    assert build + requirements == 176


def test_a_brand_new_epic_is_visible_not_dropped(sandbox):
    """An unmapped epic goes into a holding programme rather than disappearing."""
    cfg, page = sandbox
    report = agent.run(cfg, asof="2026-10-15")
    item = {i["k"]: i for i in extract_data_blob(page)["items"]}["9999"]
    assert item["p"] == "XP"
    assert "Unmapped" in item["sub"]
    assert report["findings"].get("blocker", 0) >= 1


def test_roadmap_only_rows_are_carried_through(sandbox):
    cfg, page = sandbox
    agent.run(cfg, asof="2026-10-15")
    items = extract_data_blob(page)["items"]
    rm = {i["k"] for i in items if i.get("rm")}
    assert "CDC" in rm and "IDS" in rm
    assert all(i["sp"] is None for i in items if i.get("rm"))


def test_hand_maintained_dependencies_are_preserved(sandbox):
    """`deps` and `rels` are judgement, not data — they must come back intact.

    Intact means: every gate survives, and every link whose endpoints still
    exist survives. Links to epics this run no longer has are pruned, because
    the page cannot render them — see the dangling-link test below.
    """
    cfg, page = sandbox
    before = extract_data_blob(page)
    agent.run(cfg, asof="2026-10-15")
    after = extract_data_blob(page)

    # The page carries 15 gates, not the 16 quoted in the v3 summary. Every one
    # is an external ask and must survive even if nothing it blocks is left.
    assert len(before["deps"]) == 15
    assert len(after["deps"]) == 15
    assert [d["id"] for d in after["deps"]] == [d["id"] for d in before["deps"]]
    assert [d.get("ask") for d in after["deps"]] == [d.get("ask") for d in before["deps"]]

    # Not a fixed count: the fixture copies the published page, which the agent
    # itself rewrites, so any constant here rots the first time it runs for real.
    # The property is what matters — every still-valid link comes back.
    assert before["rels"], "fixture page has no relationships to preserve"
    live = {i["k"] for i in after["items"]}
    expected = [r for r in before["rels"] if all(z in live for z in r)]
    assert after["rels"] == expected


def test_no_dangling_reference_ever_reaches_the_page(sandbox):
    """One bad key blanks all nine tabs, so this is the load-bearing invariant.

    The page does `byK[z].dep` with no guard. A link to a deleted epic throws
    during init, every section stays empty, and the file still opens — so the
    damage is invisible until someone scrolls.
    """
    cfg, page = sandbox
    agent.run(cfg, asof="2026-10-15")
    after = extract_data_blob(page)
    live = {i["k"] for i in after["items"]}

    for r in after["rels"]:
        assert all(z in live for z in r), f"rel {r} points at a missing item"
    for d in after["deps"]:
        for z in d.get("b", []):
            assert z in live, f"dep {d.get('id')} blocks missing item {z}"


def test_second_run_is_stable(sandbox):
    cfg, page = sandbox
    agent.run(cfg, asof="2026-10-15")
    once = page.read_text(encoding="utf-8")
    agent.run(cfg, asof="2026-10-15")
    twice = page.read_text(encoding="utf-8")
    # Only the refresh stamp's clock may differ.
    import re
    strip = lambda t: re.sub(r'<div id="refresh-stamp".*?</div>', "", t, flags=re.S)
    assert strip(once) == strip(twice)


def test_week_on_week_delta_is_computed(sandbox):
    cfg, page = sandbox
    agent.run(cfg, asof="2026-10-08")          # lays down a snapshot
    agent.run(cfg, asof="2026-10-15")
    blob = extract_data_blob(page)
    assert "delta" in blob


def test_dry_run_leaves_the_page_alone(sandbox):
    cfg, page = sandbox
    before = page.read_text(encoding="utf-8")
    report = agent.run(cfg, dry_run=True, asof="2026-10-15")
    assert page.read_text(encoding="utf-8") == before
    assert report["html"]["dry_run"] is True
