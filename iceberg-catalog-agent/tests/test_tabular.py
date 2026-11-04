"""The tabular layout must carry the sectioned layout's information, exactly.

This is the test that makes overwriting the source snapshot safe. If the flat
inventory loses a timestamp, a consumer edge or a stale count, the agent would
happily keep republishing the smaller estate and every adoption denominator
would quietly shrink.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from iceberg_catalog.render import tabular  # noqa: E402
from iceberg_catalog.sources.snapshot import parse_markdown  # noqa: E402

ORIGINAL = Path("/Users/dthakur/Downloads/iceberg-regular-refresh-and-consumers.md")
GENERATED = ROOT / "out" / "iceberg-catalog-tabular.md"


def _fingerprint(catalog):
    """Everything the two layouts are both supposed to carry."""
    return {
        t.fqn: (
            {env: copy.last_updated for env, copy in sorted(t.copies.items())},
            t.source_system,
            tuple(t.producers),
            tuple(t.consumers),
        )
        for t in catalog.tables
    }


def _require(path: Path) -> Path:
    if not path.exists():
        raise SystemExit(f"{path} is missing. Run the agent first.")
    return path


def test_flat_layout_round_trips_the_sectioned_one():
    sectioned = parse_markdown(_require(ORIGINAL))
    flat = parse_markdown(_require(GENERATED))

    assert len(flat.tables) == len(sectioned.tables), (
        f"flat layout has {len(flat.tables)} tables, sectioned has "
        f"{len(sectioned.tables)}"
    )

    left, right = _fingerprint(sectioned), _fingerprint(flat)
    assert set(left) == set(right), "the two layouts disagree on which tables exist"

    differing = {fqn: (left[fqn], right[fqn]) for fqn in left if left[fqn] != right[fqn]}
    assert not differing, f"{len(differing)} tables differ, e.g. {list(differing)[:3]}"


def test_stale_counts_survive():
    sectioned = parse_markdown(_require(ORIGINAL))
    flat = parse_markdown(_require(GENERATED))

    assert sectioned.stale_counts, "the original's stale section did not parse"
    assert flat.stale_counts == sectioned.stale_counts


def test_accounts_survive():
    sectioned = parse_markdown(_require(ORIGINAL))
    flat = parse_markdown(_require(GENERATED))

    assert len(flat.accounts) == 4
    assert [(a.environment, a.account_id, a.tables_in_catalog) for a in flat.accounts] == [
        (a.environment, a.account_id, a.tables_in_catalog) for a in sectioned.accounts
    ]


def test_csv_matches_the_inventory():
    flat = parse_markdown(_require(GENERATED))
    rows = list(tabular.csv_rows(flat))

    header, body = rows[0], rows[1:]
    assert header[:2] == ["database", "table"]
    assert len(body) == len(flat.tables)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
