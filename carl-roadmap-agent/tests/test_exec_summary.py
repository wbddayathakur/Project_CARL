"""The exec paragraph must be derived, not asserted.

The v3 page carried claims like "most mature" and "platform largely built"
that no reader could check and that went stale within a fortnight. These tests
pin the structure of the replacement: it is computed, it is idempotent, and it
drops the unverifiable prose.
"""

import re

from carl_roadmap.render import _patch_exec_summary, mark_html

BLOCK = (
    'document.getElementById("exec").innerHTML=`\n'
    '<div class="card" style="border-left:6px solid #312e81"><div class="big">'
    '<b>Bottom line:</b> CARL is organised as five programs. <b>Data Foundations</b> '
    'is the most mature (platform largely built). <b>MSTR Migration</b> carries the '
    'largest open load (${R.MM.t} SP, International alone 717 SP unprojected).'
    '</div></div>\n'
    '<div class="kpis" id="kpis"></div>'
)


def test_replaces_the_unverifiable_prose():
    out = _patch_exec_summary(BLOCK)
    for claim in ("most mature", "largely built", "717 SP unprojected",
                  "organised as five programs"):
        assert claim not in out, f"{claim!r} survived"


def test_keeps_the_surrounding_markup_intact():
    out = _patch_exec_summary(BLOCK)
    assert 'document.getElementById("exec").innerHTML=`' in out
    assert '<div class="kpis" id="kpis"></div>' in out
    assert out.count('border-left:6px solid #312e81') == 1


def test_is_idempotent():
    once = _patch_exec_summary(BLOCK)
    assert _patch_exec_summary(once) == once
    assert once.count(mark_html("exec")) == 1


def test_every_figure_in_the_prose_comes_from_the_data():
    """The sentences the exec reads must carry no hard-coded quantities.

    Checks the backtick-quoted copy rather than the whole block: the
    surrounding JavaScript is full of legitimate literals (0, 100, 1000) that
    say nothing to a reader.
    """
    out = _patch_exec_summary(BLOCK)
    new = out[out.index(mark_html("exec")):out.index('<div class="kpis"')]

    prose = []
    for lit in re.findall(r"`([^`]*)`", new):
        # Drop the interpolations; what is left is what gets read aloud.
        prose.append(re.sub(r"\$\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", "", lit))

    assert prose, "no template copy found to check"
    for line in prose:
        assert not re.search(r"\d", line), f"hard-coded figure in copy: {line!r}"


def test_marker_is_invisible_to_a_reader():
    """This patch lands inside a template literal, so a /*...*/ marker is text.

    It shipped once: the exec tab opened with the literal characters
    '/*carl-roadmap-agent:exec*/' above the headline.
    """
    out = _patch_exec_summary(BLOCK)
    assert "/*carl-roadmap-agent" not in out
    assert mark_html("exec") in out
    assert mark_html("exec").startswith("<!--") and mark_html("exec").endswith("-->")


def test_missing_block_is_a_warning_not_a_crash():
    text = "<html>no exec card here</html>"
    assert _patch_exec_summary(text) == text


def test_balanced_braces_and_backticks():
    """A broken template literal blanks the tab, so check it closes cleanly."""
    out = _patch_exec_summary(BLOCK)
    new = out[out.index(mark_html("exec")):out.index('<div class="kpis"')]
    assert new.count("(function(){") == 1
    assert new.count("{") == new.count("}")
    assert new.count("`") % 2 == 0
