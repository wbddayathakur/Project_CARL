"""Render the readiness report (markdown), a machine-readable JSON, and a reconciliation CSV."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import List

from .inputs import Inputs
from .match import CLASS_LABELS

SHORT = {
    "open_no_table": "open with no table yet (not started)",
    "testing_no_table": "in testing/UAT with no table in the catalog",
    "done_after_snapshot": "Done after the catalog snapshot",
    "done_no_table_found": "Done before the snapshot with no table",
    "done_but_dev_only": "Done but dev-only",
    "live_but_open": "open although the table is in prod",
    "in_dev_open": "open with the table in dev",
    "done_and_in_prod": "Done and in prod",
}
SYMBOL = {"pass": "PASS", "partial": "PARTIAL", "fail": "FAIL", "na": "n/a", "unverified": "UNVERIFIED"}


def _age(d: date, today: date) -> str:
    return f"{(today - d).days} days old"


def _findings(inp: Inputs, recon: dict, sc: dict) -> List[dict]:
    f: List[dict] = []
    cls = Counter(r.classification for r in recon["recons"])
    by_cls = defaultdict(list)
    for r in recon["recons"]:
        by_cls[r.classification].append(r)

    # dev-only layers, rolled up
    dev_only = [r for r in sc["rows"] if r["counts"]["tables"] and r["counts"]["in_prod"] == 0]
    if dev_only:
        total = sum(r["counts"]["tables"] for r in dev_only)
        top = sorted(dev_only, key=lambda r: -r["counts"]["tables"])[:5]
        f.append({
            "id": "dev-only-layers", "count": total,
            "text": f"{total} tables across {len(dev_only)} source/layer groups exist only in dev, with nothing in prod. Largest: "
                    + "; ".join(f"{r['source']} {r['layer']} ({r['counts']['tables']})" for r in top) + ".",
        })

    if cls["testing_no_table"]:
        ex = ", ".join(r.key for r in by_cls["testing_no_table"][:6])
        pre = [r for r in by_cls["testing_no_table"] if r.updated and r.updated <= inp.glue_as_of]
        f.append({
            "id": "testing_no_table", "count": cls["testing_no_table"],
            "text": f"{cls['testing_no_table']} stories are in Ready for Testing / In Testing / UAT / In Review with no matching table in the catalog "
                    f"(e.g. {ex}). "
                    + (f"{len(pre)} of them were last touched on or before the {inp.glue_as_of} snapshot, so their tables should already have been visible. " if pre else
                       f"All were touched after the {inp.glue_as_of} snapshot, so the tables may simply post-date the catalog export. ")
                    + "Refresh the catalog before treating these as gaps.",
        })
    if cls["done_no_table_found"]:
        ex = ", ".join(r.key for r in by_cls["done_no_table_found"])
        f.append({
            "id": "done_no_table_found", "count": cls["done_no_table_found"],
            "text": f"{cls['done_no_table_found']} stories were Done before the catalog snapshot but no matching table exists: {ex}. "
                    f"{sum(1 for r in by_cls['done_no_table_found'] if r.hints)} of them have a near-identical table name in the catalog (likely a rename), "
                    "so they are naming drift rather than missing data; the rest need an owner to confirm.",
        })
    if cls["done_but_dev_only"]:
        f.append({
            "id": "done_but_dev_only", "count": cls["done_but_dev_only"],
            "text": f"{cls['done_but_dev_only']} stories are Done but the table is only in dev: "
                    + ", ".join(r.key for r in by_cls["done_but_dev_only"]),
        })
    if cls["live_but_open"]:
        blocked = [r for r in by_cls["live_but_open"] if r.status == "Blocked"]
        f.append({
            "id": "live_but_open", "count": cls["live_but_open"],
            "text": f"{cls['live_but_open']} stories are still open although a matching table is already in prod "
                    f"({len(blocked)} of them Blocked: {', '.join(r.key for r in blocked)}). "
                    "The ticket status is stale, or the table is live but unaccepted. Either way reporting on Jira status misstates the lake.",
        })
    if cls["done_after_snapshot"]:
        f.append({
            "id": "done_after_snapshot", "count": cls["done_after_snapshot"],
            "text": f"{cls['done_after_snapshot']} Done stories were resolved after the catalog snapshot, so they cannot be judged until the catalog is refreshed.",
        })

    one = sc["one_time_loads"]
    if one:
        per = Counter(s for s, _, _ in one)
        top = ", ".join(f"{k} ({v})" for k, v in per.most_common(4))
        f.append({
            "id": "one_time_loads", "count": len(one),
            "text": f"{len(one)} prod tables have exactly one retained snapshot older than {inp.cfg['fresh_window_days']} days, "
                    f"so no recurring load is evidenced. By source: {top}.",
        })
    return sorted(f, key=lambda x: -x["count"])


findings = _findings


def render_markdown(inp: Inputs, recon: dict, sc: dict, today: date) -> str:
    L: List[str] = []
    w = L.append
    w("# CARL data-readiness report (PoC)\n")
    w("Every number below is computed from real inputs. Nothing is simulated. "
      "Where the inputs cannot answer a question, the report says **UNVERIFIED**.\n")

    w("## 1. Inputs and how fresh they are\n")
    w("| Input | As of | Age today | What it is |")
    w("|---|---|---|---|")
    w(f"| Glue catalog inventory (dev + prod) | {inp.glue_as_of} | {_age(inp.glue_as_of, today)} | {len(inp.tables)} tables, live Glue export |")
    w(f"| Prod load history | {inp.history_as_of} | {_age(inp.history_as_of, today)} | Iceberg snapshot history for {inp.history_tables} prod tables ({inp.history_unmatched} not in the inventory) |")
    w(f"| Jira (CARL project) | {inp.jira_as_of} | {_age(inp.jira_as_of, today)} | {recon['stories_total']} stories: children of the ingestion epics plus all Blocked |")
    w("")
    w("QA and stage accounts are **not** in the catalog export, so readiness here is dev-versus-prod only.\n")

    findings = _findings(inp, recon, sc)
    w("## 2. What the evidence says (ranked by count)\n")
    for i, x in enumerate(findings, 1):
        w(f"{i}. {x['text']}")
    w("")

    w("## 3. Readiness by source and layer\n")
    w("`Stage` is derived only from the catalog. Quality is **unverified** for every row because no data-quality, "
      "schema-contract or parity results exist in any input (see section 6).\n")
    w("| Source | Layer | Tables | In dev | In prod | Stage | Flags | Jira-requested tables found in dev / prod |")
    w("|---|---|---:|---:|---:|---|---|---|")
    for r in sc["rows"]:
        c, j = r["counts"], r["jira"]
        jtxt = "-" if j is None else f"{j['found_in_dev']} / {j['found_in_prod']} of {j['requested_tables']}"
        w(f"| {r['source']} | {r['layer']} | {c['tables']} | {c['in_dev']} | {c['in_prod']} | {r['stage']} | {'; '.join(r['flags']) or '-'} | {jtxt} |")
    w("")
    ex = "; ".join(f"{v} {k}" for k, v in sc["excluded"].items())
    w(f"Excluded from scoring: {ex}. Rules are in `config/rubric.json`.\n")

    w("### Criterion detail\n")
    for r in sc["rows"]:
        if r["counts"]["tables"] == 0:
            continue
        w(f"**{r['source']} / {r['layer']}**: {r['stage']}\n")
        for c in r["criteria"]:
            w(f"- {c['id']} {c['title']}: **{SYMBOL[c['status']]}** ({c['detail']})")
        w("")

    w("## 4. Jira versus the catalog\n")
    m = recon
    w(f"Of {m['stories_total']} stories, {m['reconciled']} name a table and a layer that this PoC could parse; "
      f"{len(m['unparsed'])} are design, discovery or access tasks with no table name. "
      f"Of the {m['reconciled']} parsed, **{m['matched']} matched a catalog table** and "
      f"{len(m['unmatched_parsed'])} did not. The matcher is a naming heuristic, so treat a no-match as a lead to check, not a verdict. "
      "Breakdown of the stories with no catalog match: "
      + ", ".join(f"{n} {SHORT[k]}" for k, n in Counter(
          r.classification for r in m["recons"] if r.confidence == "none").most_common()) + ".\n")
    cls = Counter(r.classification for r in m["recons"])
    w("| Reconciliation | Stories |")
    w("|---|---:|")
    for k, label in CLASS_LABELS.items():
        w(f"| {label} | {cls.get(k, 0)} |")
    w("")
    amb = [r for r in m["recons"] if r.confidence == "ambiguous"]
    if amb:
        w(f"{len(amb)} stories matched more than one table (suffix match); they are flagged `ambiguous` in the CSV.\n")

    for k in ("done_no_table_found", "done_but_dev_only", "live_but_open"):
        rows = [r for r in m["recons"] if r.classification == k]
        if not rows:
            continue
        w(f"### {CLASS_LABELS[k]}\n")
        for r in rows:
            tb = ", ".join(r.tables[:2]) if r.tables else "no exact match"
            hint = f" (closest names, hint only: {', '.join(r.hints)})" if r.hints else ""
            w(f"- {r.key} ({r.status}) {r.summary.strip()} -> {tb}{hint}")
        w("")

    w("## 5. Blocked work, mapped to the lake\n")
    blocked = inp.jira["blocked"]
    by_key = {r.key: r for r in m["recons"]}
    w(f"{len(blocked)} CARL stories are Blocked. For the {sum(1 for b in blocked if b['key'] in by_key)} that name a table:\n")
    for b in blocked:
        r = by_key.get(b["key"])
        if r:
            w(f"- {b['key']} {b['summary'].strip()}: {CLASS_LABELS[r.classification]}")
    w("")

    w("## 6. Evidence gaps: criteria nobody can currently measure\n")
    w("These rubric criteria have no data source. They are the real blockers to scoring readiness without guesswork.\n")
    seen = set()
    for c in inp.cfg["criteria"]:
        if c["evidence"] == "none" and c["id"] not in seen:
            seen.add(c["id"])
            w(f"- {c['id']} ({c['layer']}) {c['title']}. Needs: {c['needs']}.")
    w("")
    g = sc["golden_name_matches"]
    w(f"- Golden / eval datasets: a name search across all {len(inp.tables)} catalog tables for golden / eval / ground-truth / benchmark found **{len(g)}**"
      + (f": {', '.join(g[:5])}" if g else ".") + "")
    dq = sc["dq_metrics_tables"]
    if dq:
        w("- DQ results store: " + "; ".join(f"`{n}` (dev={'Y' if d else 'N'}, prod={'Y' if p else 'N'})" for n, d, p in dq) + ".")
    w("- Environment isolation (non-prod DMS pointing at prod Oracle, CARL-4112): evidenced only by Jira/ARB notes. No input shows DMS endpoints, so it cannot be scored here.")
    w("- Layer definitions: the rubric in `config/rubric.json` is a proposal. Until owners agree it, the stage labels are this PoC's reading, not a company standard.\n")

    w("## 7. Limits of this run\n")
    w("- Glue `UpdateTime` is when metadata or data last changed, not when data was last read or reconciled.")
    w("- Load history comes from retained Iceberg snapshots. If snapshots were expired, 'single snapshot' can understate real load frequency.")
    w("- The `Done` judgement in section 4 uses a catalog that is older than Jira; stories resolved after the snapshot are separated out rather than counted as gaps.")
    w("- Table-name matching is heuristic (exact, then suffix). The match rate above is reported as is.")
    return "\n".join(L) + "\n"


def write_outputs(out_dir: Path, inp: Inputs, recon: dict, sc: dict, today: date) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "readiness_report.md").write_text(render_markdown(inp, recon, sc, today))

    payload = {
        "generated_for": str(today),
        "inputs": {
            "glue_as_of": str(inp.glue_as_of), "history_as_of": str(inp.history_as_of), "jira_as_of": str(inp.jira_as_of),
        },
        "rubric_status": inp.cfg["status"],
        "rows": sc["rows"],
        "excluded": sc["excluded"],
        "jira_match": {
            "stories_total": recon["stories_total"], "reconciled": recon["reconciled"], "matched": recon["matched"],
            "unparsed": len(recon["unparsed"]), "unmatched_parsed": len(recon["unmatched_parsed"]),
        },
        "findings": _findings(inp, recon, sc),
    }
    (out_dir / "readiness.json").write_text(json.dumps(payload, indent=2, default=str))

    with (out_dir / "jira_glue_reconciliation.csv").open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["key", "status", "resolved", "epic", "source", "layer", "candidate_table", "match", "tables", "in_dev", "in_prod", "classification", "summary"])
        for r in recon["recons"]:
            wr.writerow([r.key, r.status, r.resolved or "", r.epic, r.source, r.layer, r.candidate, r.confidence,
                         "|".join(r.tables), r.in_dev, r.in_prod, r.classification, r.summary.strip()])
