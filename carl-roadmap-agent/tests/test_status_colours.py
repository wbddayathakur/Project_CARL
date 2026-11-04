"""Every Jira status must resolve to a colour.

The page indexes `STC` by raw status name and, at one site, without a
fallback. An epic in a status the 30 Sep export never contained rendered
`background:undefined` and came out unstyled.
"""

from carl_roadmap.model import Buckets
from carl_roadmap.render import _patch_status_colours

PAGE = (
    'const STC={"Done":"#86efac","In Progress":"#fde68a","To Do":"#e2e8f0"};\n'
    'bars.map(i=>`<div style="background:${STC[i.st]};left:0"></div>`)\n'
    'other.map(s=>`<i style="background:${STC[s]||\'#e2e8f0\'}"></i>`)\n'
)


def test_adds_a_colour_for_an_unseen_status():
    out = _patch_status_colours(PAGE, {"In Testing": "#fde68a"})
    assert '"In Testing": "#fde68a"' in out or '"In Testing":"#fde68a"' in out


def test_keeps_the_designers_existing_colours():
    out = _patch_status_colours(PAGE, {"Done": "#000000", "In Testing": "#fde68a"})
    assert "#86efac" in out, "existing Done colour was overwritten"
    assert "#000000" not in out


def test_adds_the_missing_fallback():
    out = _patch_status_colours(PAGE, {})
    assert "background:${STC[i.st]||'#e2e8f0'}" in out
    assert "background:${STC[i.st]}" not in out


def test_fallback_already_present_is_left_alone():
    out = _patch_status_colours(PAGE, {})
    assert out.count("STC[s]||'#e2e8f0'") == 1


def test_is_idempotent():
    once = _patch_status_colours(PAGE, {"In Testing": "#fde68a"})
    assert _patch_status_colours(once, {"In Testing": "#fde68a"}) == once


def test_missing_stc_is_a_warning_not_a_crash():
    assert _patch_status_colours("<html>no map</html>", {"X": "#fff"}) == "<html>no map</html>"


def test_agent_derives_a_colour_for_every_live_status():
    from carl_roadmap.agent import _status_colours
    from carl_roadmap.model import Epic

    buckets = Buckets({"done": ["Done"], "build": ["In Testing"],
                       "requirements": ["To Do"], "excluded": ["Archive"]})
    epics = [Epic(key="C-1", num="1", summary="a", status="In Testing",
                  assignee="", issue_type="Epic"),
             Epic(key="C-2", num="2", summary="b", status="Done",
                  assignee="", issue_type="Epic"),
             # A status in no bucket at all still gets a colour, not None.
             Epic(key="C-3", num="3", summary="c", status="Invented Yesterday",
                  assignee="", issue_type="Epic")]
    colours = _status_colours(epics, buckets)
    assert set(colours) == {"In Testing", "Done", "Invented Yesterday"}
    assert all(v.startswith("#") for v in colours.values())
