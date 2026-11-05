"""Pull live status and child-ticket progress for every roadmap epic.

Epic keys come from the roadmap inputs (v3 relationship items and the Q4 CSV).
Credentials are the carl-roadmap-agent ones: JIRA_USER / JIRA_TOKEN from the
environment or carl-roadmap-agent/.env.

Writes inputs/jira-live-<date>.json.

Run:  .venv/bin/python lakehouse-layer-dashboard-v2/pull_jira.py
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
AGENT = ROOT / "carl-roadmap-agent"
sys.path.insert(0, str(AGENT))

from carl_roadmap.sources.jira import Jira, _chunks  # noqa: E402

POINTS = "customfield_10004"
KEY = re.compile(r"CARL-?\s?(\d+)")


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def epic_keys() -> list[str]:
    keys = set()
    v3 = json.loads((HERE / "inputs" / "roadmap_v3_relationships.json").read_text())
    for item in v3["ITEMS"]:
        for part in re.split(r"[/,\s]+", str(item.get("k") or "")):
            if re.search(r"\d", part):
                keys.add("CARL-" + re.sub(r"\D", "", part))
    with (HERE / "inputs" / "CARL_2026Q4_QuarterlyPlanning_Status_Roadmap.csv").open(encoding="cp1252") as fh:
        for row in csv.reader(fh):
            for cell in row:
                for num in KEY.findall(cell):
                    keys.add(f"CARL-{num}")
    return sorted(keys, key=lambda k: int(k.split("-")[1]))


def main() -> None:
    load_env(AGENT / ".env")
    jira = Jira("https://wbdprod.atlassian.net", os.environ.get("JIRA_USER", ""), os.environ.get("JIRA_TOKEN", ""))
    keys = epic_keys()

    epics = {}
    for chunk in _chunks(keys, 100):
        for issue in jira._search(f"key IN ({', '.join(chunk)})", ["summary", "status", "assignee", "duedate", "updated"]):
            f = issue["fields"]
            epics[issue["key"]] = {
                "summary": (f.get("summary") or "").strip(),
                "status": f["status"]["name"],
                "category": f["status"]["statusCategory"]["key"],
                "assignee": (f.get("assignee") or {}).get("displayName", ""),
                "due": f.get("duedate"),
                "updated": (f.get("updated") or "")[:10],
                "tickets": 0, "done": 0, "inprog": 0, "sp": 0.0, "spDone": 0.0, "byStatus": {},
            }

    by_status = {k: Counter() for k in epics}
    for chunk in _chunks(list(epics), 100):
        for issue in jira._search(f"parent IN ({', '.join(chunk)})", ["status", "parent", POINTS]):
            f = issue["fields"]
            parent = (f.get("parent") or {}).get("key")
            if parent not in epics:
                continue
            e = epics[parent]
            cat = f["status"]["statusCategory"]["key"]
            pts = float(f.get(POINTS) or 0)
            e["tickets"] += 1
            e["sp"] += pts
            if cat == "done":
                e["done"] += 1
                e["spDone"] += pts
            elif cat == "indeterminate":
                e["inprog"] += 1
            by_status[parent][f["status"]["name"]] += 1
    for k, c in by_status.items():
        epics[k]["byStatus"] = dict(c)

    out = HERE / "inputs" / f"jira-live-{dt.date.today().isoformat()}.json"
    out.write_text(json.dumps({"pulled": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "epics": epics}, indent=1))
    missing = sorted(set(keys) - set(epics))
    print(f"Wrote {out}: {len(epics)} epics, {sum(e['tickets'] for e in epics.values())} child tickets")
    if missing:
        print("  not found in Jira:", ", ".join(missing))


if __name__ == "__main__":
    main()
