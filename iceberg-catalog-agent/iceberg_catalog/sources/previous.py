"""Restore a `Catalog` from the JSON a previous run wrote.

This is the preferred fallback when live collection fails, ahead of parsing
markdown. The published markdown is deliberately lossy — it drops stale and
sandbox tables, because nobody circulating a catalog wants 700 rows of
`vg_test` in it — so re-parsing it would quietly shrink every denominator in
the adoption report and make the estate look better than it is.

The JSON keeps everything. Falling back to it means last week's numbers are
reported as last week's numbers, rather than as a new and mysteriously
improved set.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Optional

from ..model import Account, Catalog, Table, TableCopy


def load_json(path: str | Path) -> Catalog:
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    catalog = Catalog(
        generated_at=_stamp(data.get("generated_at")) or dt.datetime.now(),
        source=data.get("source", "snapshot"),
        window_days=int(data.get("window_days", 14)),
        notes=list(data.get("notes", [])),
    )

    catalog.accounts = [
        Account(
            environment=a["environment"],
            account_id=a.get("account_id", ""),
            databases_with_tables=a.get("databases_with_tables", 0),
            tables_in_catalog=a.get("tables_in_catalog", 0),
            tables_refreshed=a.get("tables_refreshed", 0),
        )
        for a in data.get("accounts", [])
    ]

    for raw in data.get("tables", []):
        table = Table(database=raw["database"], name=raw["name"])
        table.source_system = raw.get("source_system")
        table.cadence = raw.get("cadence")
        table.producers = list(raw.get("producers", []))
        table.consumers = list(raw.get("consumers", []))
        table.layer = raw.get("layer", "unknown")
        table.domain = raw.get("domain", "unassigned")
        table.tier = raw.get("tier", "unclassified")

        for env, copy in (raw.get("environments") or {}).items():
            table.copies[env] = TableCopy(
                environment=env,
                account=copy.get("account", ""),
                last_updated=_stamp(copy.get("last_updated")),
                location=copy.get("location"),
            )

        catalog.tables.append(table)

    return catalog


def _stamp(value) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
