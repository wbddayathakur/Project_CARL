"""Distil raw Jira MCP dumps into a slim, reviewable snapshot.

The raw dumps carry comments, watchers, worklogs and people. The scorer needs
none of that, so this keeps only: key, summary, status, type, parent, labels,
dates and issue links. Nothing is inferred or filled in; a field that is absent
in the raw file is absent here.

    python3 tools/distill_jira.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "jira_snapshot.json"

# Provenance. These are the exact queries that produced the raw files, run via
# the Atlassian MCP on 2026-10-22 against wbdprod.atlassian.net.
CHILDREN_JQL = (
    "parent in (CARL-1756, CARL-1380, CARL-2887, CARL-1477, CARL-3638, "
    "CARL-3639, CARL-4086, CARL-4087, CARL-4153, CARL-3779, CARL-3500, "
    "CARL-3499, CARL-3497, CARL-2888, CARL-3501, CARL-3750, CARL-1480, "
    "CARL-749, CARL-312, CARL-313, CARL-4035, CARL-3505, CARL-3504, "
    "CARL-3503, CARL-631, CARL-4050, CARL-1479) ORDER BY key ASC"
)
BLOCKED_JQL = "project = CARL AND status = Blocked ORDER BY updated DESC"


def _slim(issue: dict) -> dict:
    f = issue["fields"]
    parent = f.get("parent")
    links = []
    for ln in f.get("issuelinks") or []:
        other = ln.get("outwardIssue") or ln.get("inwardIssue")
        if not other:
            continue
        direction = "outward" if "outwardIssue" in ln else "inward"
        t = ln["type"]
        links.append(
            {
                "type": t["name"],
                "relation": t[direction],  # e.g. "blocks" / "is blocked by"
                "key": other["key"],
                "summary": other["fields"].get("summary"),
                "status": other["fields"]["status"]["name"],
            }
        )
    return {
        "key": issue["key"],
        "summary": (f.get("summary") or "").strip(),
        "status": f["status"]["name"],
        "status_category": (f.get("statusCategory") or {}).get("key")
        or f["status"].get("statusCategory", {}).get("key"),
        "issuetype": f["issuetype"]["name"],
        "parent": (
            {"key": parent["key"], "summary": parent["fields"].get("summary")}
            if parent
            else None
        ),
        "labels": f.get("labels") or [],
        "priority": (f.get("priority") or {}).get("name"),
        "created": f.get("created"),
        "updated": f.get("updated"),
        "resolved": f.get("resolutiondate"),
        "links": links,
    }


def _load(name: str) -> list[dict]:
    return json.loads((RAW / name).read_text())["data"]["issues"]


def main() -> None:
    children = []
    for p in (1, 2, 3):
        children += [_slim(i) for i in _load(f"jira_children_p{p}.json")]
    blocked = [_slim(i) for i in _load("jira_blocked.json")]

    snap = {
        "retrieved": "2026-10-22",
        "site": "wbdprod.atlassian.net",
        "queries": {"children_of_ingestion_epics": CHILDREN_JQL, "blocked": BLOCKED_JQL},
        "children_of_ingestion_epics": children,
        "blocked": blocked,
    }
    OUT.write_text(json.dumps(snap, indent=1))
    print(f"children={len(children)} blocked={len(blocked)} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
