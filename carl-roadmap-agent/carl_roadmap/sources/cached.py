"""Build epics from a flat on-disk cache instead of a live REST call.

The scheduled run talks to Jira over REST with an API token. An interactive
run may not have a token to hand but may have an authenticated Atlassian
connector, which returns the same issues through a different door. Rather than
duplicate the rollup and render logic for that case, both doors write the same
cache shape and everything downstream stays identical.

Cache layout (`out/jira-cache.json`)::

    {"asof": "2026-10-15",
     "epics":    [{"key","summary","status","assignee","labels","due",
                   "created","updated","parent_key","parent_summary",
                   "ticket_count"}],
     "children": [["CARL-123", "CARL-2", "Done", 3.0]]}

`children` is a list of positional rows rather than objects purely to keep the
file legible when it holds a couple of thousand of them.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..model import Buckets, Epic, Story

log = logging.getLogger(__name__)


class CacheError(RuntimeError):
    pass


def load(path: Path, buckets: Buckets) -> list[Epic]:
    if not path.exists():
        raise CacheError(
            f"no Jira cache at {path}. Either set JIRA_USER/JIRA_TOKEN for a "
            f"live pull, or write a cache first."
        )
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CacheError(f"{path} is not valid JSON: {e}") from e

    by_parent: dict[str, list[Story]] = {}
    for row in blob.get("children", []):
        key, parent, status, points = row[0], row[1], row[2], row[3]
        by_parent.setdefault(parent, []).append(
            Story(
                key=key,
                summary="",
                status=status,
                bucket=buckets.of(status),
                points=float(points or 0),
                assignee="",
                issue_type="",
            )
        )

    epics = []
    for e in blob.get("epics", []):
        epic = Epic(
            key=e["key"],
            num=e["key"].split("-")[-1],
            summary=(e.get("summary") or "").strip(),
            status=e.get("status") or "",
            assignee=e.get("assignee") or "",
            issue_type="Epic",
            labels=e.get("labels") or [],
            due=e.get("due"),
            created=e.get("created"),
            updated=e.get("updated"),
            parent_key=e.get("parent_key"),
            parent_summary=e.get("parent_summary"),
            stories=by_parent.get(e["key"], []),
        )
        epic.roll_up(buckets)

        # Only issues carrying story points are cached, so the rolled-up ticket
        # count undercounts. Jira's own "Children of Epic count" is the honest
        # figure; prefer it and fall back to what we actually hold.
        declared = e.get("ticket_count")
        if declared is not None:
            epic.ticket_count = int(declared)
        epics.append(epic)

    log.info(
        "loaded %s epics and %s pointed children from %s",
        len(epics), sum(len(v) for v in by_parent.values()), path,
    )
    return epics
