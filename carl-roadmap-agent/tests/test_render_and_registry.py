"""The render step edits a file people have already shared, so the thing worth
proving is that it changes the data and nothing else — and that running it
twice is identical to running it once.
"""

import json

import pytest

from carl_roadmap.registry import Registry, bootstrap_from_html, extract_data_blob
from carl_roadmap.render import mark, write

PAGE = """<!doctype html><html><head><title>CARL</title>
<style>.bar{height:8px}</style></head><body>
<header><h1>CARL Program Roadmap</h1>
<div class="tabs" id="tabs"></div></header>
<section id="exec"></section>
<script>const DATA={"items": [{"k": "744", "n": "Ingest Operative", "p": "DF", "sub": "Bronze",
 "st": "Done", "sp": [193, 193, 0, 0], "note": "a \\"quoted\\" note with {braces}", "rm": false}],
 "rels": [["744", "2888"]], "deps": [{"id": "X-OP1", "b": ["2888"]}]};
const ASOF="2026-10-05",ITEMS=DATA.items,RELS=DATA.rels,DEPS=DATA.deps;
function spbar(sp){if(!sp||!sp[0])return'old';const[t,d,p,o]=sp;return 'old-bar'}
function roll(arr){return arr.length}
<div class="kpis"><div class="kpi"><b>87</b><span>Epics</span></div></div>
<div class="g5">cards</div>
</script></body></html>
"""

NEW_DATA = {
    "items": [
        {"k": "744", "n": "Ingest Operative One", "p": "DF", "sub": "Bronze",
         "st": "Done", "sp": [193, 193, 0, 0], "rm": False},
        {"k": "4175", "n": "Engineering Architecture", "p": "XP", "sub": "Unmapped",
         "st": "To Do", "sp": [0, 0, 0, 0], "rm": False},
    ],
    "rels": [["744", "2888"]],
    "deps": [{"id": "X-OP1", "b": ["2888"]}],
}


@pytest.fixture
def page(tmp_path):
    p = tmp_path / "CARL_Program_Roadmap_v3.html"
    p.write_text(PAGE, encoding="utf-8")
    return p


# ------------------------------------------------------------------ extraction


def test_data_blob_survives_braces_and_quotes_inside_strings(page):
    blob = extract_data_blob(page)
    assert blob["items"][0]["note"] == 'a "quoted" note with {braces}'
    assert blob["rels"] == [["744", "2888"]]


def test_missing_marker_is_a_clear_error(tmp_path):
    p = tmp_path / "x.html"
    p.write_text("<html>no data here</html>", encoding="utf-8")
    with pytest.raises(ValueError, match="no `const DATA=`"):
        extract_data_blob(p)


# ---------------------------------------------------------------------- write


def test_write_replaces_the_data_and_the_asof(page):
    write(page, data=NEW_DATA, asof="2026-10-15")
    text = page.read_text(encoding="utf-8")
    assert 'const ASOF="2026-10-15"' in text
    blob = extract_data_blob(page)
    assert [i["k"] for i in blob["items"]] == ["744", "4175"]


def test_write_keeps_the_narrative_untouched(page):
    before = page.read_text(encoding="utf-8")
    write(page, data=NEW_DATA, asof="2026-10-15")
    after = page.read_text(encoding="utf-8")
    for fragment in ("<title>CARL</title>", "CARL Program Roadmap", "function roll(arr)"):
        assert fragment in before and fragment in after


def test_write_is_idempotent(page):
    write(page, data=NEW_DATA, asof="2026-10-15", generated_at="2026-10-15 09:00")
    once = page.read_text(encoding="utf-8")
    write(page, data=NEW_DATA, asof="2026-10-15", generated_at="2026-10-15 09:00")
    assert page.read_text(encoding="utf-8") == once
    assert once.count(mark("kpis")) == 1
    assert once.count(mark("spbar")) == 1


def test_header_date_and_provenance_follow_the_data(tmp_path):
    """The prose date must not contradict the refresh stamp."""
    from carl_roadmap.render import _replace_subtitle

    src = ('<div class="sub">Status as of 5 Oct 2026 \u00b7 Sources: '
           'CARL_Epic_Mapping_Initiative_15Oct 2.xlsx (Jira export 30 Sep, Sprint 19) '
           '\u00b7 CARL_Q1_2027_BigRoom_Planning.xlsx</div>')
    out = _replace_subtitle(src, "2026-10-15")

    assert "Status as of 15 Oct 2026" in out
    assert "Status as of 5 Oct" not in out
    assert "live Jira (CARL)" in out
    assert "Jira export 30 Sep" not in out
    # The workbooks still back the usage, intake and planning tabs.
    assert "CARL_Q1_2027_BigRoom_Planning.xlsx" in out


def test_subtitle_rewrite_is_idempotent(tmp_path):
    from carl_roadmap.render import _replace_subtitle

    src = ('<div class="sub">Status as of 5 Oct 2026 \u00b7 Sources: '
           'CARL_Epic_Mapping_Initiative_15Oct 2.xlsx (Jira export 30 Sep, Sprint 19)</div>')
    once = _replace_subtitle(src, "2026-10-15")
    assert _replace_subtitle(once, "2026-10-15") == once


def test_patch_markers_are_complete_comments(tmp_path):
    """A marker must be inert. `/*agent*/kpis` is not — it is an identifier.

    With a `(` on the next line that parses as a call, and `<div id="kpis">`
    publishes `window.kpis`, so it throws "kpis is not a function" from a line
    that looks innocent.
    """
    for label in ("kpis", "spbar"):
        m = mark(label)
        assert m.startswith("/*") and m.endswith("*/"), m
        assert "*/" not in m[2:-2], f"{m} closes early, leaking {label} into code"
        assert label in m


def test_progress_bar_gains_a_requirements_segment(page):
    write(page, data=NEW_DATA, asof="2026-10-15")
    text = page.read_text(encoding="utf-8")
    assert "Requirements with PM" in text
    assert "#60a5fa" in text          # the requirements colour
    assert "in progress</span>" in text


def test_literal_headline_numbers_are_replaced_by_derived_ones(page):
    write(page, data=NEW_DATA, asof="2026-10-15")
    text = page.read_text(encoding="utf-8")
    assert "<b>87</b>" not in text
    assert '<div class="kpis" id="kpis"></div>' in text
    assert "Epics with tickets but no estimate" in text


def test_refresh_stamp_is_added_once_and_then_updated(page):
    write(page, data=NEW_DATA, asof="2026-10-15", generated_at="2026-10-15 09:00")
    write(page, data=NEW_DATA, asof="2026-10-16", generated_at="2026-10-16 09:00")
    text = page.read_text(encoding="utf-8")
    assert text.count('id="refresh-stamp"') == 1
    assert "2026-10-16 09:00" in text
    assert "2026-10-15 09:00" not in text


def test_previous_version_is_kept_before_overwriting(page, tmp_path):
    history = tmp_path / "history"
    write(page, data=NEW_DATA, asof="2026-10-15", history_dir=history)
    kept = list(history.glob("*.html"))
    assert len(kept) == 1
    assert "<b>87</b>" in kept[0].read_text(encoding="utf-8")


def test_missing_page_fails_loudly_rather_than_creating_one(tmp_path):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        write(tmp_path / "nope.html", data=NEW_DATA, asof="2026-10-15")


def test_output_is_ascii_so_it_survives_being_mailed_around(page):
    data = dict(NEW_DATA)
    data["items"] = [{**NEW_DATA["items"][0], "n": "Ingest \u2014 Op\u00e9rative"}]
    write(page, data=data, asof="2026-10-15")
    raw = page.read_bytes()
    marker = raw.index(b"const DATA=")
    assert all(b < 128 for b in raw[marker : marker + 2000])
    assert extract_data_blob(page)["items"][0]["n"] == "Ingest \u2014 Op\u00e9rative"


# ------------------------------------------------------------------- registry


def test_bootstrap_keeps_human_fields_and_drops_jira_ones(page, tmp_path):
    reg = bootstrap_from_html(page, tmp_path / "epic-map.yaml")
    entry = reg.entry("744")
    assert entry["p"] == "DF"
    assert entry["sub"] == "Bronze"
    assert entry["note"].startswith("a \"quoted\"")
    # Status and points belong to Jira and must not be frozen into the registry.
    assert "st" not in entry and "sp" not in entry


def test_registry_round_trips_through_yaml(page, tmp_path):
    path = tmp_path / "epic-map.yaml"
    bootstrap_from_html(page, path).save()
    assert Registry(path).entry("744")["p"] == "DF"


def test_registry_refuses_to_write_jira_owned_fields(tmp_path):
    reg = Registry(tmp_path / "r.yaml")
    with pytest.raises(ValueError, match="not human-owned"):
        reg.upsert("744", st="Done")


def test_non_numeric_keys_are_roadmap_only_by_definition(tmp_path):
    p = tmp_path / "p.html"
    p.write_text(
        PAGE.replace('"k": "744"', '"k": "CDC"'), encoding="utf-8"
    )
    reg = bootstrap_from_html(p, tmp_path / "m.yaml")
    assert reg.entry("CDC")["rm"] is True
    assert "CDC" in reg.roadmap_only()
