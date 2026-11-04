#!/usr/bin/env python3
"""Take committed dates from the Q4 planning CSV into the epic registry.

    python3 tools/apply_csv_dates.py <csv> [--write]

Dates are human-owned (see registry/epic-map.yaml), so this edits the registry
and the weekly refresh then carries them onto the page. Mapping, matching how
the registry was first bootstrapped from the same sheet:

    Development Start Date        -> s   committed start
    Development End Date          -> t   committed target
    Dev- Actual Production Date   -> a   actual completion, but ONLY when Jira
                                          says the epic is Done. The column is
                                          also used for planned prod dates, and
                                          stamping "completed" on an open epic
                                          is worse than leaving it blank.

Things it refuses to import silently, and reports instead:
    * an end date before the start date
    * an end date more than 12 months after the start (typo-shaped)
    * a year that is not 2025-2027
Where the CSV is silent for a field the existing registry value is kept.
A revised forecast (fc) is cleared whenever the CSV supplies a new target,
since fc overrides t on the page and would otherwise hide the CSV date.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "registry" / "epic-map.yaml"
LIVE = REPO / "out" / "carl-roadmap.json"

C_START, C_END, C_PROD, C_EPIC, C_NAME = 11, 12, 15, 17, 2


def parse(x: str):
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", (x or "").strip())
    if not m:
        return None
    mo, d, y = map(int, m.groups())
    y += 2000 if y < 100 else 0
    if not 2025 <= y <= 2027:
        return ("bad-year", "%s" % x.strip())
    try:
        return dt.date(y, mo, d)
    except ValueError:
        return ("bad-date", x.strip())


def read_csv(path: Path):
    rows = list(csv.reader(path.open(encoding="utf-8", errors="replace")))
    per: dict[str, dict] = {}
    for r in rows[3:]:
        if len(r) <= C_EPIC:
            continue
        for k in re.findall(r"CARL-?\s*(\d+)", r[C_EPIC]):
            e = per.setdefault(k, {"s": [], "t": [], "a": [], "rows": [], "bad": []})
            e["rows"].append(r[C_NAME].strip())
            for col, slot in ((C_START, "s"), (C_END, "t"), (C_PROD, "a")):
                v = parse(r[col])
                if isinstance(v, tuple):
                    e["bad"].append("%s %r (%s)" % (slot, v[1], v[0]))
                elif v:
                    e[slot].append(v)
    return per


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    write = "--write" in sys.argv
    per = read_csv(Path(sys.argv[1]))
    live = {i["k"]: i for i in json.loads(LIVE.read_text(encoding="utf-8"))["data"]["items"]}
    text = REG.read_text(encoding="utf-8")

    applied, held, skipped, fc_cleared, a_ignored = [], [], [], [], []

    def block_span(key: str):
        m = re.search(r"^  '?%s'?:\n((?:    .*\n|      .*\n)+)" % re.escape(key), text, re.M)
        return m

    for key, e in sorted(per.items(), key=lambda kv: int(kv[0])):
        item = live.get(key)
        if not item or item.get("rm"):
            skipped.append((key, e["rows"][0]))
            continue
        m = block_span(key)
        if not m:
            skipped.append((key, e["rows"][0] + "  [live epic with no registry entry]"))
            continue
        s = min(e["s"]) if e["s"] else None
        t = max(e["t"]) if e["t"] else None
        problems = list(e["bad"])
        if s and t and t < s:
            problems.append("end %s is before start %s" % (t, s))
            t = None
        if s and t and (t - s).days > 366:
            problems.append("end %s is %d days after start" % (t, (t - s).days))
            t = None
        a = None
        if e["a"] and item.get("st") in ("Done", "Closed", "Resolved"):
            a = max(e["a"])
        elif e["a"]:
            a_ignored.append((key, item.get("st"), max(e["a"])))
        if problems:
            held.append((key, e["rows"][0], problems))

        body = m.group(1)
        old = {f: (re.search(r"^    %s: '?([^'\n]*)'?\s*$" % f, body, re.M) or [None, ""])[1]
               for f in ("s", "t", "fc", "a")}
        new = dict(old)
        if s:
            new["s"] = s.isoformat()
        if t:
            new["t"] = t.isoformat()
            if old["fc"]:
                fc_cleared.append((key, old["fc"], t.isoformat()))
            new["fc"] = ""
        if a:
            new["a"] = a.isoformat()
        if new == old:
            continue
        applied.append((key, item["n"][:40], old, new))
        if write:
            kept = [ln for ln in body.splitlines(True)
                    if not re.match(r"    (s|t|fc|a): ", ln)]
            add = "".join("    %s: '%s'\n" % (f, new[f]) for f in ("s", "t", "fc", "a") if new[f])
            # Keep continuation lines of folded notes attached to their field.
            text = text[:m.start(1)] + "".join(kept) + add + text[m.end(1):]

    print("CSV epics: %d | changed: %d | held back: %d | not applicable: %d"
          % (len(per), len(applied), len(held), len(skipped)))
    print("\nchanged:")
    for k, n, o, nw in applied:
        diff = ", ".join("%s %s->%s" % (f, o[f] or "-", nw[f] or "-")
                         for f in ("s", "t", "fc", "a") if o[f] != nw[f])
        print("  CARL-%-5s %-40s %s" % (k, n, diff))
    if held:
        print("\nHELD BACK (looks like a data-entry error, not imported):")
        for k, n, p in held:
            print("  CARL-%-5s %-30s %s" % (k, n[:30], "; ".join(p)))
    if a_ignored:
        print("\nProd date in CSV but Jira says not Done, so no actual recorded:")
        for k, st, d in a_ignored:
            print("  CARL-%-5s Jira=%-14s CSV prod date %s" % (k, st, d))
    if skipped:
        print("\nnot applied (not a live CARL epic, or roadmap-only):")
        for k, n in skipped:
            print("  CARL-%-5s %s" % (k, n[:60]))

    if write:
        REG.write_text(text, encoding="utf-8")
        print("\nregistry updated: %s" % REG)
    else:
        print("\n(dry run — registry untouched; pass --write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
