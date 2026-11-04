#!/usr/bin/env python3
"""Refresh the Strategic Roadmap swimlane from the same live Jira pull.

    python3 tools/refresh_swimlane.py [--dry-run]

The swimlane is a second published page built on the same item model as the
roadmap — every row carries a `k` of Jira keys — but its numbers were last set
from a 30 September export. Rather than hand-editing 77 rows, this reuses
out/carl-roadmap.json so both pages always agree about what Jira says.

Two things it deliberately does beyond copying numbers across:

* Drops Jira keys that do not exist. The page cites CARL-3959 and CARL-3962,
  neither of which is a real issue — the author assumed the Cross-Project epics
  occupied a contiguous block. Those links would 404 for every reader.
* Gives the status colour map a fallback. `background:${STC[i.st]}` has no
  guard, so the first live status missing from the map paints a bar
  `background:undefined`.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LIVE = REPO / "out" / "carl-roadmap.json"
PAGE = Path(
    "/Users/dthakur/Library/CloudStorage/OneDrive-WarnerBros.Discovery/Documents/"
    "Copilot/Created/CARL_Strategic_Roadmap_Swimlane_v3.html"
)

# Statuses the swimlane has never seen but live Jira returns, mapped onto the
# page's existing palette rather than new colours nobody has a legend for.
EXTRA_STATUS = {
    "In QA Testing": "#bef264",
    "Ready For UAT": "#bef264",
    "Ready for review": "#fde68a",
    "In Review": "#fde68a",
    "Ready to Deploy": "#bef264",
    "In Testing": "#bef264",
    "Blocked": "#fecaca",
    "Closed": "#86efac",
    "Resolved": "#86efac",
    "Backlog": "#e2e8f0",
    "Open": "#e2e8f0",
    "Archive": "#e5e7eb",
    "Cancelled": "#e5e7eb",
}

BUILD = {"In Progress", "In UAT", "In QA Testing", "In Testing", "Ready for Testing",
         "Ready For UAT", "In Review", "Ready for review", "Ready to Deploy", "Blocked"}
DONE = {"Done", "Closed", "Resolved"}


# ------------------------------------------------------------------ parsing

def block(text: str, name: str) -> tuple[int, int]:
    """Byte range of a top-level `const NAME = [...]` / `{...}` literal."""
    m = re.search(r"(?:const|let|var)\s+%s\s*=\s*" % name, text)
    if not m:
        sys.exit("no `%s` in the page" % name)
    i = m.end()
    opener = text[i]
    closer = {"[": "]", "{": "}"}[opener]
    depth = 0
    j = i
    quote = None
    while j < len(text):
        ch = text[j]
        if quote:
            if ch == "\\":
                j += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return i, j + 1
        j += 1
    sys.exit("unterminated `%s`" % name)


def loads_js(raw: str):
    """Parse a JS object literal with bare keys."""
    return json.loads(re.sub(r"([{,]\s*)([A-Za-z_$][\w$]*)\s*:", r'\1"\2":', raw))


def dumps_js(items: list[dict]) -> str:
    """Re-emit in the page's own style: bare keys, one row per line."""
    out = []
    for it in items:
        parts = []
        for k, v in it.items():
            parts.append("%s:%s" % (k, json.dumps(v, ensure_ascii=False)))
        out.append("{" + ",".join(parts) + "}")
    return "[\n" + ",\n".join(out) + "\n]"


# ------------------------------------------------------------------- refresh

def keys_of(raw: str) -> list[str]:
    """"CARL-3789 / 3790" -> ["3789", "3790"]; "—" -> []."""
    return re.findall(r"\d+", raw or "")


# Rows whose cited epics no longer describe the work. P-VEN's only surviving
# key is CARL-1160, a closed cross-board tracker; left alone the row would read
# "Done" while the actual Venus support epic has not started.
REMAP = {"P-VEN": ["4137"]}

# Statuses that mean "nobody has started", so a row carrying delivered or
# in-flight points contradicts itself by claiming one. Epic status is the least
# maintained field in the project — teams transition stories and leave the epic
# at To Do — so where the points disagree with the epic, the points win.
NOT_STARTED = {"To Do", "In Triage", "Backlog", "Open", "Pending Scope"}


def rag_of(total, done, target, blocked, asof: str, status: str) -> str:
    # A delivered row is not "at risk" for having been delivered late.
    if status in DONE:
        return "G"
    if not total:
        return "N"
    pct = done / total
    overdue = bool(target) and target < asof and pct < 1
    if overdue and pct < 0.25:
        return "R"
    if blocked and total and blocked / total > 0.4:
        return "R"
    if overdue:
        return "A"
    return "G"


def main() -> int:
    dry = "--dry-run" in sys.argv
    live_blob = json.loads(LIVE.read_text(encoding="utf-8"))
    asof = live_blob["report"]["asof"]
    live = {i["k"]: i for i in live_blob["data"]["items"]}

    text = PAGE.read_text(encoding="utf-8")
    i, j = block(text, "ITEMS")
    items = loads_js(text[i:j])

    changed, dangling, unresolved = [], [], []

    for it in items:
        comps = REMAP.get(it["id"]) or keys_of(it.get("k", ""))
        if not comps:
            continue
        good = [c for c in comps if c in live]
        gone = [c for c in comps if c not in live]
        if not good:
            # Nothing to rewrite the citation from, so leave it exactly as it
            # was rather than blanking a link that may still resolve.
            unresolved.append((it["id"], it["k"], it["n"]))
            continue
        if gone:
            dangling.append((it["id"], it["k"], gone))

        # Keep the citation honest about which issues actually exist.
        it["k"] = " / ".join(("CARL-" + c) if n == 0 else c
                             for n, c in enumerate(good))

        tot = dn = bd = rq = 0
        for c in good:
            sp = live[c].get("sp") or [0, 0, 0, 0]
            tot += sp[0] or 0
            dn += sp[1] or 0
            bd += sp[2] or 0
            rq += sp[3] or 0
        before = (it.get("st"), tuple(it.get("sp") or []), it.get("rag"), it.get("o"))

        # Let the component carrying the most points speak for the row. A
        # composite often pairs a real delivery epic with a zero-point tracking
        # epic nobody transitions, and taking the first key lets the tracker
        # report "To Do" over work that is finished.
        sts = [live[c].get("st") for c in good if live[c].get("st")]
        if sts and all(s in DONE for s in sts):
            status = "Done"
        else:
            dominant = max(good, key=lambda c: (live[c].get("sp") or [0])[0] or 0)
            status = live[dominant].get("st") or it.get("st")
            if status in NOT_STARTED and (dn or bd):
                status = "In Progress"

        owners = [live[c].get("o") for c in good if live[c].get("o")]
        blocked = sum(1 for c in good if live[c].get("st") == "Blocked")

        it["st"] = status
        it["sp"] = [tot, dn, bd, rq]
        if owners:
            it["o"] = owners[0] if len(set(owners)) == 1 else owners[0] + " +"
        it["rag"] = rag_of(tot, dn, it.get("t"), bd if blocked else 0, asof, status)
        if status == "Done" and not it.get("a"):
            it["a"] = max((live[c].get("upd") or "") for c in good) or it.get("t")

        after = (it["st"], tuple(it["sp"]), it["rag"], it.get("o"))
        if before != after:
            changed.append((it["id"], it["n"], before, after))

    # --- splice ITEMS back -------------------------------------------------
    text = text[:i] + dumps_js(items) + text[j:]

    # --- colour map: merge missing statuses and add the fallback -----------
    si, sj = block(text, "STC")
    stc = json.loads(text[si:sj])
    present = {it.get("st") for it in items if it.get("st")}
    added = {s: EXTRA_STATUS.get(s, "#e2e8f0") for s in present if s not in stc}
    stc.update(added)
    text = text[:si] + json.dumps(stc, ensure_ascii=False, separators=(",", ":")) + text[sj:]
    text = text.replace("STC[i.st]}", "STC[i.st]||'#e2e8f0'}")
    text = text.replace("STC[i.st]+'55'", "(STC[i.st]||'#e2e8f0')+'55'")

    # --- headline numbers ---------------------------------------------------
    # The KPI strip and the bottom line carried literals from the 30 Sep export
    # ("87 Epics", "43.3% ... unchanged since v2", "717 SP"). Sitting above
    # category bars that *are* computed, they contradicted the page itself.
    # Derive them so the next refresh cannot leave them behind.
    if "const SPT=" not in text:
        _, sj2 = block(text, "STC")
        text = (text[:sj2] + ";const SPT=ITEMS.reduce((a,i)=>a+((i.sp&&i.sp[0])||0),0),"
                "SPD=ITEMS.reduce((a,i)=>a+((i.sp&&i.sp[1])||0),0),"
                "SPP=SPT?Math.round(SPD/SPT*1000)/10:0" + text[sj2:])

    for pat, rep in [
        # Matches the original literal and any count this tool wrote before, so
        # the figure is corrected rather than frozen on the first run. Counts
        # real Jira epics only — `live` also holds roadmap-only placeholders.
        (r"<b>\d+</b><span>Epics in CARL Jira \([^)]*\)</span>",
         "<b>%d</b><span>Epics in CARL Jira (live)</span>"
         % sum(1 for i in live.values() if not i.get("rm"))),
        (r'<b style="color:var\(--G\)">43\.3%</b><span>SP done \(1,730 / 3,992\)'
         r" \u2014 unchanged since v2</span>",
         '<b style="color:var(--G)">${SPP}%</b><span>SP done (${SPD.toLocaleString()}'
         " / ${SPT.toLocaleString()}) \u2014 live from Jira</span>"),
        (r'<b style="color:var\(--R\)">717</b>',
         '<b style="color:var(--R)">${((ITEMS.find(i=>i.id=="D-MINT")||{sp:[0]})'
         ".sp[0]||0).toLocaleString()}</b>"),
        (r"43% of sized work \(1,730 of 3,992 SP\) is done",
         "${SPP}% of sized work (${SPD.toLocaleString()} of "
         "${SPT.toLocaleString()} SP) is done"),
    ]:
        text, n = re.subn(pat, lambda _m, r=rep: r, text)
        if not n:
            print("note: headline not found, left alone: %s" % pat[:58])

    # --- dates and provenance ----------------------------------------------
    pretty = date.fromisoformat(asof).strftime("%-d %b %Y")
    text = re.sub(r'ASOF="\d{4}-\d{2}-\d{2}"', 'ASOF="%s"' % asof, text, count=1)
    text = text.replace("as of 6 Oct 2026", "as of %s" % pretty)
    text = text.replace(
        "Jira workstream roll-up (export 30 Sep 2026, Sprint 19)",
        "Jira workstream roll-up (live Jira, %s)" % pretty,
    )
    text = text.replace("export 30 Sep 2026, Sprint 19)", "live Jira, %s)" % pretty)

    # The page states its own provenance in several places. Leaving these at
    # "still the 30 Sep export" while the numbers underneath are live is worse
    # than either state on its own — a reader discounts figures that are right.
    for pat, rep in [
        (r"Jira data is the 30 Sep Sprint 19 export",
         "Jira story points and status pulled live from CARL on %s" % pretty),
        (r"Jira story points: <b>no change</b> \u2014 the epic workbook is still the "
         r"30 Sep \(Sprint 19\) export;",
         "Jira story points: <b>live</b> \u2014 refreshed from the CARL project on "
         "%s by carl-roadmap-agent;" % pretty),
        (r"No story-point changes \(still the 9/30 Sprint 19 export\)\.",
         "Story points and status now refreshed from live Jira (%s), replacing the "
         "30 Sep Sprint 19 export." % pretty),
        # Matches both the original sentence and a half-rewritten one, so a
        # re-run cannot leave "unchanged from v2 - ... has been replaced".
        ("unchanged from v2 \u2014 the epic workbook (?:is still the 30 Sep 2026 "
         r"export|has been replaced by a live Jira pull) \([^)]*\)\.",
         "refreshed %s \u2014 the epic workbook has been replaced by a live pull "
         "from the CARL project." % pretty),
    ]:
        text, n = re.subn(pat, lambda _m, r=rep: r, text)
        if not n:
            print("note: provenance string not found, left alone: %s" % pat[:60])

    # --- report -------------------------------------------------------------
    print("as of %s  ·  %d items, %d refreshed" % (asof, len(items), len(changed)))
    for iid, name, b, a in changed:
        print("  %-10s %-44s %-16s -> %-16s  sp %s -> %s  rag %s->%s"
              % (iid, name[:44], b[0], a[0], list(b[1]), a[1], b[2], a[2]))
    if added:
        print("\nstatus colours added: %s" % ", ".join(sorted(added)))
    if dangling:
        print("\nJira keys dropped (no such issue):")
        for iid, raw, gone in dangling:
            print("  %-10s %-24s dropped %s" % (iid, raw, ", ".join("CARL-" + g for g in gone)))
    if unresolved:
        print("\nno live epic behind these rows — left as they were:")
        for iid, raw, name in unresolved:
            print("  %-10s %-24s %s" % (iid, raw, name[:50]))

    if dry:
        print("\n--dry-run: page not written")
        return 0

    snap = REPO / "out" / "history" / ("%s-%s.html" % (PAGE.stem, date.today().isoformat()))
    snap.parent.mkdir(parents=True, exist_ok=True)
    if not snap.exists():
        shutil.copy2(PAGE, snap)
        print("\nkept the previous page at %s" % snap)
    tmp = PAGE.with_suffix(".html.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(PAGE)
    print("wrote %s (%d bytes)" % (PAGE, len(text)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
