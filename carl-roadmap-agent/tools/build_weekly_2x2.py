#!/usr/bin/env python3
"""Fill the CALS Weekly 2x2 template for CARL.

Fills the supplied template in place rather than rebuilding it, so the
landscape setup, table styles, cell merges and column widths all survive —
rebuilding by hand drifts from whatever Nage's team actually circulated.

    python3 tools/build_weekly_2x2.py

Scorecard values are read from the agent's own weekly snapshots in
out/history, so "last week" is a real prior reading rather than a blank.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = Path("/Users/dthakur/Downloads/CALS Weekly 2x2 Template.docx")
OUT = Path("/Users/dthakur/Library/CloudStorage/OneDrive-WarnerBros.Discovery/"
           "Documents/Copilot/Created/CARL_Weekly_2x2_2026-10-23.docx")

WEEK_ENDING = "10/23/2026"


# --------------------------------------------------------------- scorecard

def snapshots() -> dict:
    out = {}
    for f in sorted((REPO / "out" / "history").glob("roadmap-*.json")):
        out[f.stem.replace("roadmap-", "")] = json.loads(
            f.read_text(encoding="utf-8"))["items"]
    return out


def scorecard() -> list[tuple[str, str, str, str, str]]:
    """Metric, target, this week, last week, trend — sourced where possible."""
    snaps = snapshots()
    weeks = list(snaps)
    now, prev = (snaps[weeks[-1]], snaps[weeks[-2]]) if len(weeks) > 1 else (snaps[weeks[-1]], {})

    def sp(items, key):
        it = items.get(key) or {}
        return it.get("sp") or [0, 0, 0, 0]

    sox_now, sox_prev = sp(now, "4134")[1], sp(prev, "4134")[1]
    return [
        ("MicroStrategy SOX & Accounting delivered (story points, CARL-4134)",
         "74", f"{sox_now:g}", f"{sox_prev:g}",
         "\u25b2" if sox_now > sox_prev else "\u25ba"),
        ("Ad Sales Batch 2.3 reports accepted into intake (CARL-3790)",
         "26", "26", "0", "\u25b2"),
        ("Venus bronze tables cleared for production (CARL-4035)",
         "9", "0 \u2014 epic Blocked", "0 \u2014 Ready for Testing", "\u25bc"),
    ]


# ------------------------------------------------------------------ content

ROLLUP = [
    ("Headline:", "Legacy WBD advanced the CARL revenue foundation, BI modernization "
                  "and governed data access (Daya Thakur)."),
    ("What we did:", "Delivered the Ad Sales Total Revenue gold view in development, "
                     "completed 4 SOX dashboards, opened the 26-report Batch 2.3 intake, "
                     "and operationalized Salesforce Phase 1 ingestion."),
    ("Proof:", "4 SOX dashboards completed (story points delivered 9 \u2192 14); "
               "26 Ad Sales reports accepted into intake; Salesforce Phase 1 closed "
               "at 38 of 39 tickets."),
    ("Status / next:", "On track. Close Ad Sales sign-off with Jason Chalmers and "
                       "Adam Christensen by 10/31, and unblock 8 Venus bronze tables "
                       "with Venus / UMP stakeholders by 10/31."),
    ("Why it matters:", "Improves revenue reporting trust, lowers migration risk and "
                        "accelerates Sales and Finance decisioning."),
]

HIGHLIGHTS = [
    "Ad Sales Total Revenue: gold view delivered in development for stakeholder "
    "review; 2 silver layers moved to review, with Athena dataset views supporting "
    "faster query verification.",
    "MicroStrategy modernization: 4 SOX dashboards completed; Batches 2.1 and 2.2 "
    "advanced through QA/UAT; Batch 2.3 intake opened for 26 planned reports.",
    "Governed enablement: Salesforce Phase 1 operationalized at 38 of 39 tickets "
    "closed; Lake Formation role-policy alignment and catalog federation completed.",
]

RISKS = [
    "Ad Sales production deployment \u2014 Impact: production date pending stakeholder "
    "review; the gold epic (CARL-3639) remains at 0 of 19 story points. "
    "Fix: Jason Chalmers / Adam Christensen close feedback and sign-off path by 10/31.",
    "Finance forecasting and MicroStrategy validation \u2014 Impact: Finance Batch 1 "
    "(CARL-2727) sits at 17 of 180 story points and is unchanged week on week. "
    "Fix: Finance and Data Engineering re-baseline production timing once discrepancy "
    "triage closes.",
    "iDeal / Venus production dependency \u2014 Impact: CARL-4035 moved from Ready for "
    "Testing to Blocked this week; 8 production bronze tables are held on external "
    "source access and schema. Fix: Venus / UMP stakeholders close dependencies by 10/31.",
]

NEXT = [
    "Next week: close Ad Sales Total Revenue review, business acceptance criteria and "
    "target production date by 10/31.",
    "Next week: complete business validation of the 9 Venus tables and agree an unblock "
    "plan for the 8 production bronze tables by 10/31.",
    "Asks / decisions needed: Ad Sales stakeholders to confirm the sign-off path; Finance "
    "to close validation gaps and revised timing; Venus / UMP leads to escalate source "
    "access and schema closure.",
    "Transparency: record scope expansion from dataset migration into report authoring, "
    "custom fields and new business logic, so date movement is attributable to demand "
    "rather than execution.",
]


# -------------------------------------------------------------------- docx

def set_cell(cell, text: str, *, bold_prefix: str | None = None, size: float = 8.5):
    """Replace a cell's text, keeping its paragraph style and shading."""
    p = cell.paragraphs[0]
    for extra in cell.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    if bold_prefix:
        run = p.add_run(bold_prefix + " ")
        run.bold = True
        run.font.size = Pt(size)
    run = p.add_run(text)
    run.font.size = Pt(size)
    return p


def drop_row(table, idx: int):
    row = table.rows[idx]
    row._element.getparent().remove(row._element)


def main() -> int:
    if not TEMPLATE.exists():
        sys.exit(f"template not found: {TEMPLATE}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMPLATE, OUT)
    doc = Document(str(OUT))

    t_head, t_roll, t_hi, t_risk = doc.tables

    # 1. Header strip
    for cell, text in zip(t_head.rows[0].cells, [
        "Team / Workstream: CARL",
        "Owner: Ping Feng, Daya Thakur",
        f"Week ending: {WEEK_ENDING}",
        "Overall status: GREEN \u2014 On Track",
    ]):
        set_cell(cell, text, size=9)
        for r in cell.paragraphs[0].runs:
            r.bold = True

    # 2. Executive roll-up. Row 0 is the template's own instruction text.
    drop_row(t_roll, 0)
    for row, (label, body) in zip(t_roll.rows, ROLLUP):
        set_cell(row.cells[0], body, bold_prefix=label, size=9)

    # 3. Highlights (col 0) and scorecard (cols 1-5). Row 0 = section titles,
    #    row 1 = column headers, rows 2-4 = content, row 5 = instructions.
    drop_row(t_hi, 5)
    for i, text in enumerate(HIGHLIGHTS):
        set_cell(t_hi.rows[2 + i].cells[0], "\u25aa " + text)
    for i, cols in enumerate(scorecard()):
        for j, val in enumerate(cols):
            set_cell(t_hi.rows[2 + i].cells[1 + j], val)

    # 4. Risks and next week. Template gives 2 risk rows and 3 ask rows; this
    #    week needs 3 and 4, so borrow the instruction row rather than add one.
    while len(t_risk.rows) < 1 + max(len(RISKS), len(NEXT)):
        t_risk.add_row()
    for i in range(max(len(RISKS), len(NEXT))):
        row = t_risk.rows[1 + i]
        set_cell(row.cells[0], "\u25aa " + RISKS[i] if i < len(RISKS) else "")
        set_cell(row.cells[1], "\u25aa " + NEXT[i] if i < len(NEXT) else "")
    for extra in range(len(t_risk.rows) - 1, max(len(RISKS), len(NEXT))):
        drop_row(t_risk, len(t_risk.rows) - 1)

    # 5. Strip the "How to fill this in" guidance so the deliverable is one page.
    killing = False
    for p in list(doc.paragraphs):
        if p.text.strip() == "How to fill this in":
            killing = True
        if killing:
            p._element.getparent().remove(p._element)

    # 6. Provenance, so a reader knows which numbers are sourced.
    foot = doc.add_paragraph()
    run = foot.add_run(
        "Source: CARL Jira (project CARL) as at 21 Oct 2026, via carl-roadmap-agent; "
        "narrative from the CARL weekly status for 19\u201323 Oct 2026. "
        "Status scale: Green = on track; Yellow = at risk with recovery plan; "
        "Red = off track / decision needed."
    )
    run.font.size = Pt(7.5)
    run.italic = True

    doc.save(str(OUT))
    print("wrote", OUT)
    print("  tables:", len(doc.tables), "| paragraphs:", len(doc.paragraphs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
