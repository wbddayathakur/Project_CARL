#!/usr/bin/env python3
"""Add inferred initiative placement for new epics to a v4 page's INIT_MAP.

    python3 tools/place_new_epics.py <page.html> [--dry-run]

The v4 page keeps initiative / domain / project in an `INIT_MAP` block that is
separate from the Jira data, so the weekly refresh never touches it. An epic
created after the workbook was exported would otherwise sit under "Not yet
mapped". This reads registry/initiative-placement.yaml, copies each epic's
placement from its stated sibling, and sets `inf: 1` so the page labels it
"mapping inferred". It never overwrites an entry that already exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
PLACE = REPO / "registry" / "initiative-placement.yaml"


def span(text: str, name: str) -> tuple[int, int]:
    i = text.index("const %s=" % name)
    j = text.index("{", i)
    depth, k, quote = 0, j, None
    while True:
        ch = text[k]
        if quote:
            if ch == "\\":
                k += 2
                continue
            if ch == quote:
                quote = None
        elif ch == '"':
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return j, k + 1
        k += 1


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    page = Path(sys.argv[1])
    dry = "--dry-run" in sys.argv
    text = page.read_text(encoding="utf-8")
    a, b = span(text, "INIT_MAP")
    imap = json.loads(text[a:b])
    want = yaml.safe_load(PLACE.read_text(encoding="utf-8"))["epics"]

    added, kept, missing = [], [], []
    for key, spec in want.items():
        key = str(key)
        if key in imap:
            kept.append(key)
            continue
        sib = imap.get(str(spec["like"]))
        if not sib:
            missing.append((key, spec["like"]))
            continue
        imap[key] = {
            "i": sib["i"],
            "d": spec["d"] if "d" in spec else sib.get("d", ""),
            "j": sib["j"],
            "l": [],
            "inf": 1,
        }
        added.append(key)

    print("%s: %d placed, %d already mapped (left alone), %d sibling not found"
          % (page.name, len(added), len(kept), len(missing)))
    for k in added:
        m = imap[k]
        print("  CARL-%-5s %s | %-22s | %s" % (k, m["i"], m["d"], m["j"]))
    for k, s in missing:
        print("  CARL-%s: sibling CARL-%s is not in INIT_MAP" % (k, s))

    if added and not dry:
        blob = json.dumps(imap, ensure_ascii=True, separators=(",", ":"))
        tmp = page.with_suffix(".html.tmp")
        tmp.write_text(text[:a] + blob + text[b:], encoding="utf-8")
        tmp.replace(page)
        print("written")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
