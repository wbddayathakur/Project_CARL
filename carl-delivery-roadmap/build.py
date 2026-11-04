#!/usr/bin/env python3
"""Build CARL_Delivery_Roadmap.html.

    python build.py            # writes out/CARL_Delivery_Roadmap.html
    python build.py --check    # structure checks only, writes nothing

Numbers (status, story points, tickets, owners, epic dates) come from the
carl-roadmap-agent snapshot, overlaid with the live-Jira status corrections in
LIVE_STATUS below. Structure, ladders and non-Jira items come from subprojects.py.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import subprojects as sp_def

HERE = Path(__file__).parent
SNAPSHOT = HERE.parent / "carl-roadmap-agent" / "out" / "carl-roadmap.json"
OUT = HERE / "out" / "CARL_Delivery_Roadmap.html"
JIRA = "https://wbdprod.atlassian.net/browse/CARL-"
WIKI = "https://wbdprod.atlassian.net/wiki/spaces/PAYTV/pages/"

# Live Jira (epic search, 21 Oct) differs from the 14:56 snapshot on these epics only.
LIVE_STATUS = {"2778": "Done"}

DONE = {"done"}
TODAY = date.fromisoformat(sp_def.TODAY)

STATUS_BUCKET = {
    "Done": "done", "Closed": "done", "Resolved": "done", "Released": "done",
    "Blocked": "block",
    "In Progress": "build", "In UAT": "build", "In QA Testing": "build", "In Testing": "build",
    "Ready for Testing": "build", "Ready For UAT": "build", "In Review": "build",
    "Ready for review": "build", "Ready to Deploy": "build",
    "To Do": "req", "In Triage": "req", "Pending Scope": "req", "Open": "req", "Backlog": "req",
}


def d(x):
    return date.fromisoformat(x) if x else None


def registry_dated():
    """Epic keys whose dates came from the hand-maintained roadmap registry (Q4 Planning).

    Parsed with a regex rather than PyYAML so the build has no dependencies.
    """
    path = HERE.parent / "carl-roadmap-agent" / "registry" / "epic-map.yaml"
    if not path.exists():
        return set()
    keys, cur, in_epics = set(), None, False
    for line in path.read_text().splitlines():
        if line.startswith("epics:"):
            in_epics = True
        elif in_epics and re.match(r"^  ['\"]?([\w-]+)['\"]?:\s*$", line):
            cur = re.match(r"^  ['\"]?([\w-]+)['\"]?:\s*$", line).group(1)
        elif in_epics and cur and re.match(r"^    (s|t|fc|a):\s*\S", line):
            keys.add(cur)
    return keys


REG_DATED = registry_dated()


def load_snapshot():
    data = json.loads(SNAPSHOT.read_text())
    return data["report"], {i["k"]: i for i in data["data"]["items"]}


def resolve(it, J):
    """Turn a curated item into the flat record the page renders."""
    kind = it["kind"]
    r = dict(kind=kind, key=None, n=it.get("n"), st=it.get("st"), bucket=it.get("bucket"),
             o=it.get("o", ""), note=it.get("note", ""), src=it.get("src", ""),
             s=it.get("s"), t=it.get("t"), fc=it.get("fc"), a=it.get("a"), approx=it.get("approx", False),
             sp=None, tk=None, jrag=None, ev=bool(it.get("ev")))
    if kind == "epic":
        j = J[it["key"]]
        r["key"] = "CARL-" + it["key"]
        r["n"] = it.get("n") or j["n"].strip()
        r["st"] = it.get("st") or LIVE_STATUS.get(it["key"]) or j["st"]
        r["o"] = j["o"] if j["o"] != "—" else ""
        r["bucket"] = STATUS_BUCKET.get(r["st"], "req")
        for f in ("s", "t", "fc", "a"):
            r[f] = it[f] if f in it else (j[f] or None)
        r["note"] = it["note"] if "note" in it else (j["note"] or "")
        r["sp"], r["tk"], r["jrag"] = (j["sp"] or [0, 0, 0, 0]), j["tk"], j["rag"]
        if not r["src"]:
            r["src"] = ("PLAN" if it["key"] in REG_DATED else "JIRA due date") if (r["s"] or r["t"] or r["fc"]) else ""
    elif kind == "story":
        r["key"] = it["key"]
    return r


def state_of(r):
    """Date confidence for one item."""
    if r["bucket"] in DONE:
        return "delivered"
    eff = r["fc"] or r["t"]
    if r["kind"] == "ext":
        return "external" if eff else "nodate"
    if not eff:
        return "ongoing" if r.get("ev") else "nodate"
    if r["fc"]:
        return "fcpassed" if d(r["fc"]) < TODAY else "slipped"
    return "overdue" if d(r["t"]) < TODAY else "onplan"


def build():
    report, J = load_snapshot()
    subs, seen = [], {}
    for sp in sp_def.SUBPROJECTS:
        items = [resolve(i, J) for i in sp["items"]]
        for r in items:
            r["eff"] = r["fc"] or r["t"]
            r["state"] = state_of(r)
            if r["kind"] == "epic":
                if r["key"] in seen:
                    raise SystemExit(f"{r['key']} assigned twice: {seen[r['key']]} and {sp['id']}")
                seen[r["key"]] = sp["id"]
        carl = [r for r in items if r["kind"] != "ext"]
        open_c = [r for r in carl if r["bucket"] not in DONE]
        dated = [r for r in open_c if r["eff"]]
        epics = [r for r in carl if r["kind"] == "epic" and r["sp"] and r["bucket"] != "excluded"]
        tot = sum(r["sp"][0] for r in epics)
        done, build_, req = (sum(r["sp"][i] for r in epics) for i in (1, 2, 3))
        nxt = min(dated, key=lambda r: r["eff"]) if dated else None
        ext_open = sorted([r for r in items if r["kind"] == "ext" and r["bucket"] not in DONE and r["eff"]], key=lambda r: r["eff"])
        last_done = max([r["a"] for r in carl if r["a"]], default=None)
        subs.append(dict(
            id=sp["id"], g=sp["g"], name=sp["name"], outcome=sp["outcome"], owner=sp["owner"], rag=sp["rag"],
            why=sp["why"], phase=sp["phase"], ladder=sp["ladder"], blocker=sp["blocker"], ask=sp.get("ask", ""),
            docs=[dict(t=t, u=WIKI + p) for t, p in sp.get("docs", [])],
            items=items,
            sp=dict(total=tot, done=done, build=build_, req=req, sized=len(epics),
                    unsized=len([r for r in carl if r["kind"] == "epic" and not r["sp"][0]]),
                    pct=round(100 * done / tot) if tot else None),
            n_open=len(open_c), n_done=len(carl) - len(open_c),
            end=max(r["eff"] for r in dated) if dated else None,
            end_past=bool(dated) and d(max(r["eff"] for r in dated)) < TODAY,
            end_who=max(dated, key=lambda r: r["eff"])["n"] if dated else None,
            undated=len([r for r in open_c if not r["eff"] and not r["ev"]]),
            overdue=len([r for r in open_c if r["state"] in ("overdue", "fcpassed")]),
            delivered=(not open_c), last_done=last_done,
            nxt=dict(n=nxt["n"], eff=nxt["eff"], state=nxt["state"], key=nxt["key"]) if nxt else None,
            ext_next=dict(n=ext_open[0]["n"], eff=ext_open[0]["eff"], approx=ext_open[0]["approx"]) if ext_open else None,
        ))

    # coverage: every Jira epic in the snapshot should sit in exactly one sub-project
    snap_keys = {"CARL-" + k for k, v in J.items() if v["st"] != "Archive" and not v["rm"] and not k.startswith("3932-")}
    missing = sorted(snap_keys - set(seen), key=lambda k: int(k.split("-")[1]) if k.split("-")[1].isdigit() else 0)

    by_id = {s["id"]: s for s in subs}
    sources = []
    for s in sp_def.SOURCES:
        keys = ["CARL-" + k for k in s["keys"]]
        recs = [r for sub in subs for r in sub["items"] if r["key"] in keys]
        open_r = [r for r in recs if r["bucket"] not in DONE and r["eff"]]
        nxt = min(open_r, key=lambda r: r["eff"]) if open_r else None
        sources.append(dict(src=s["src"], b=s["b"], s=s["s"], g=s["g"], use=s["use"], sub=s["sub"],
                            sub_name=by_id[s["sub"]]["name"] if s["sub"] else "—",
                            keys=keys, next=dict(eff=nxt["eff"], state=nxt["state"]) if nxt else None,
                            undated=len([r for r in recs if r["bucket"] not in DONE and not r["eff"] and not r["ev"]])))

    payload = dict(
        today=sp_def.TODAY, report=dict(asof=report["asof"], epics=report["epics"], tickets=report["tickets"], points=report["points"]),
        groups=[dict(id=i, n=n, d=dsc, c=c) for i, n, dsc, c in sp_def.GROUPS],
        subs=subs, sources=sources, conflicts=sp_def.CONFLICTS, decisions=sp_def.DECISIONS,
        jira=JIRA, wiki=WIKI,
    )
    return payload, missing


def summarize(p):
    print(f"{len(p['subs'])} sub-projects · {sum(len(s['items']) for s in p['subs'])} items")
    for s in p["subs"]:
        sp = s["sp"]
        print(f"[{s['rag']}] {s['name'][:52]:52} open {s['n_open']:>2} done {s['n_done']:>2} "
              f"SP {sp['done']}/{sp['total']} ({sp['pct']}%) end={s['end']} undated={s['undated']} overdue={s['overdue']}")


def main():
    payload, missing = build()
    summarize(payload)
    if missing:
        print("\nEpics in the Jira snapshot not placed in any sub-project:", ", ".join(missing))
    if "--check" in sys.argv:
        return 1 if missing else 0
    tpl = (HERE / "template.html").read_text()
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(tpl.replace("/*__DATA__*/null", blob))
    print(f"\nwrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
