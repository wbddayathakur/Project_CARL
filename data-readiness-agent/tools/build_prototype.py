"""Build prototype/readiness_prototype.html: one self-contained file with a snapshot of the real
data embedded. Open it by double-click; no server, no network.

Usage: python3 tools/build_prototype.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from readiness.engine import Engine  # noqa: E402
from readiness.inputs import in_scope  # noqa: E402

FRESH = [7, 14, 30, 60, 90]
REC = [1, 2, 3]
MARK = '<script>\n"use strict";'


def build() -> Path:
    e = Engine(ROOT)
    base = e.baseline
    assert base[0] in FRESH and base[1] in REC, "saved thresholds must be on the precomputed grid"

    variants = {}
    for f in FRESH:
        for r in REC:
            e.set_thresholds(f, r)
            s = e.state()
            variants[f"{f}_{r}"] = {"totals": s["totals"], "findings": s["findings"], "rows": s["rows"]}
    e.set_thresholds(*base)
    s = e.state()

    stories_by_table = {}
    for rc in e.recon["recons"]:
        for t in rc.tables:
            stories_by_table.setdefault(t, []).append(rc.key)

    tables = []
    for t in e.inp.tables:  # same order the engine iterates, so ties break identically
        if not in_scope(t):
            continue
        h = t.history
        tables.append({
            "fqn": t.fqn, "name": t.name, "source": t.source, "layer": t.layer,
            "in_dev": t.in_dev, "in_prod": t.in_prod,
            "dev_updated": t.dev_updated.isoformat() if t.dev_updated else None,
            "prod_updated": t.prod_updated.isoformat() if t.prod_updated else None,
            "versions": h.get("versions") if h else None,
            "commit_days": h.get("days_with_commits_30d") if h else None,
            "stories": stories_by_table.get(t.fqn, []),
        })

    data = {
        "site": s["jira_site"],
        "glue_as_of": e.inp.glue_as_of.isoformat(),
        "inputs": [{"name": i["name"], "as_of": i["as_of"], "detail": i["detail"]} for i in s["inputs"]],
        "rubric_status": s["rubric_status"], "rubric_note": s["rubric_note"],
        "default": {"fresh": base[0], "rec": base[1]},
        "options": {"fresh": FRESH, "rec": REC},
        "variants": variants,
        "excluded": s["excluded"], "criteria": s["criteria"], "gaps": s["gaps"],
        "golden": s["golden_name_matches"], "dq": s["dq_metrics_tables"],
        "jira": s["jira"], "sources": s["sources"],
        "tables": tables,
        "recon": e.recon_rows(limit=10**6)["rows"],
        "stories": [{"key": k, "summary": v["summary"], "status": v["status"], "resolved": (v.get("resolved") or "")[:10] or None}
                    for k, v in e.stories.items()],
        "blocked": [{"key": b["key"], "summary": b["summary"]} for b in e.inp.jira["blocked"]],
    }
    blob = json.dumps(data, separators=(",", ":"), default=str).replace("</", "<\\/")

    shim = (ROOT / "ui" / "static_shim.js").read_text().replace("__DATA__", blob, 1)
    page = (ROOT / "ui" / "index.html").read_text()
    assert page.count(MARK) == 1, "main script marker not found exactly once"
    page = page.replace(MARK, "<script>\n" + shim + "\n</script>\n" + MARK, 1)
    page = page.replace("<title>CARL Data Readiness</title>", "<title>CARL Data Readiness (prototype)</title>", 1)

    out = ROOT / "prototype" / "readiness_prototype.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    return out


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({p.stat().st_size / 1024:.0f} KB)")
