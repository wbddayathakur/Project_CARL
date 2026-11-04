"""Checks on the two paths the agent can recover state from.

The fidelity difference between them is deliberate and easy to regress, so it
is asserted rather than left as a comment: the published markdown is allowed to
be lossy, the run JSON is not.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from iceberg_catalog.sources.previous import load_json  # noqa: E402
from iceberg_catalog.sources.snapshot import parse_markdown  # noqa: E402

OUT = ROOT / "out"

# Confluence storage format is an XML fragment using the ac: and ri: prefixes,
# which have to be declared before a parser will accept it.
_NS_WRAPPER = (
    '<root xmlns:ac="http://atlassian.com/content" '
    'xmlns:ri="http://atlassian.com/resource/identifier">{}</root>'
)


def _require(path: Path):
    if not path.exists():
        raise SystemExit(
            f"{path} is missing. Run the agent first:\n"
            f"  python -m iceberg_catalog --source snapshot --snapshot <file.md>"
        )
    return path


def test_markdown_listing_round_trips():
    """Every table the published markdown lists must parse back out of it."""
    catalog = parse_markdown(_require(OUT / "iceberg-catalog.md"))

    assert catalog.tables, "rendered markdown produced no parseable table rows"
    assert len(catalog.accounts) == 4

    # Consumer lists survive the semicolon join and split.
    with_consumers = [t for t in catalog.tables if t.consumers]
    assert with_consumers, "consumer column did not survive the round trip"


def test_run_json_is_full_fidelity():
    """The JSON keeps what the markdown drops: stale and sandbox tables."""
    restored = load_json(_require(OUT / "iceberg-catalog.json"))
    from_markdown = parse_markdown(_require(OUT / "iceberg-catalog.md"))

    assert len(restored.tables) > len(from_markdown.tables), (
        "the JSON should carry more tables than the published markdown, because "
        "the markdown strips stale and sandbox rows"
    )

    tiers = {t.tier for t in restored.tables}
    assert "sandbox" in tiers or "stale" in tiers, (
        "no stale or sandbox tables survived into the JSON, so the fallback would "
        "shrink every adoption denominator"
    )
    assert all(t.tier != "unclassified" for t in restored.tables)


def test_confluence_body_is_well_formed():
    """A malformed body is rejected by Confluence with an opaque 400."""
    body = _require(OUT / "iceberg-catalog.confluence.xhtml").read_text(encoding="utf-8")
    ET.fromstring(_NS_WRAPPER.format(body))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
