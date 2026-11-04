"""Score each (source, layer) against the proposed rubric using only evidence we hold.

Statuses: pass | partial | fail | na | unverified.
There are deliberately no percentages or composite scores: a criterion either has evidence
(shown as exact counts) or it is 'unverified'. The stage label is derived only from evidence.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from typing import Dict, List

from .inputs import Inputs, Table, in_scope

GOLDEN_RE = re.compile(r"(golden|gold_set|eval(?:uation)?_|_eval\b|ground_truth|expected_output|benchmark)", re.I)


def _count_status(n: int, total: int) -> str:
    if total == 0:
        return "na"
    return "pass" if n == total else ("partial" if n > 0 else "fail")


def _evaluate(inp: Inputs, layer: str, tables: List[Table]) -> Dict[str, object]:
    cfg = inp.cfg
    window = cfg["fresh_window_days"]
    min_days = cfg["recurring_min_commit_days_30d"]
    total = len(tables)
    dev = [t for t in tables if t.in_dev]
    prod = [t for t in tables if t.in_prod]
    fresh = [t for t in prod if t.prod_updated and (inp.glue_as_of - t.prod_updated).days <= window]

    with_hist = [t for t in prod if t.history]
    recurring = [t for t in with_hist if (t.history.get("days_with_commits_30d") or 0) >= min_days]
    single = [t for t in with_hist if t.history.get("versions") == 1]

    counts = {
        "tables": total, "in_dev": len(dev), "in_prod": len(prod), "fresh_in_prod": len(fresh),
        "prod_with_history": len(with_hist), "prod_recurring": len(recurring), "prod_single_snapshot": len(single),
    }

    results = []
    for c in cfg["criteria"]:
        if c["layer"] != layer:
            continue
        cid, ev = c["id"], c["evidence"]
        r = {"id": cid, "title": c["title"], "evidence": ev}
        n = cid[1:]
        if ev == "glue" and n == "1":
            r.update(status=_count_status(len(dev), total), detail=f"{len(dev)} of {total} tables in dev")
        elif ev == "glue" and n == "2":
            r.update(status=_count_status(len(prod), total), detail=f"{len(prod)} of {total} tables in prod")
        elif ev == "glue" and n == "3":
            r.update(
                status=_count_status(len(fresh), len(prod)),
                detail=f"{len(fresh)} of {len(prod)} prod tables updated within {window}d of the catalog snapshot",
            )
        elif ev == "load_history":
            if not prod:
                r.update(status="na", detail="nothing in prod")
            elif not with_hist:
                r.update(status="unverified", detail=f"no load history for any of the {len(prod)} prod tables")
            else:
                # No recurring loads in the retained snapshots is "not evidenced", not "fail":
                # snapshot expiry could hide a real cadence, and this input cannot tell the two apart.
                st = "pass" if len(recurring) == len(prod) else ("unverified" if not recurring else "partial")
                r.update(
                    status=st,
                    detail=(
                        f"{len(recurring)} recurring, {len(single)} with a single retained snapshot, "
                        f"history covers {len(with_hist)} of {len(prod)} prod tables"
                    ),
                )
        else:
            r.update(status="unverified", detail="no evidence source", needs=c.get("needs", ""))
        results.append(r)

    if total == 0:
        stage = "not present"
    elif not prod:
        stage = "dev only"
    elif len(prod) < total:
        stage = "partly in prod"
    else:
        stage = "in prod"
    flags = []
    if prod and len(fresh) < len(prod):
        flags.append(f"{len(prod) - len(fresh)} stale in prod")
    if with_hist and len(recurring) < len(with_hist):
        flags.append(f"{len(with_hist) - len(recurring)} with no recurring-load evidence")
    return {"counts": counts, "criteria": results, "stage": stage, "flags": flags}


def score(inp: Inputs, recon: dict) -> Dict[str, object]:
    groups: Dict[tuple, List[Table]] = defaultdict(list)
    excluded = defaultdict(int)
    for t in inp.tables:
        if in_scope(t):
            groups[(t.source, t.layer)].append(t)
        elif t.sandbox_db:
            excluded["sandbox database"] += 1
        elif t.noise:
            excluded["test/tmp-looking table name"] += 1
        else:
            excluded["no medallion layer (raw/audit/unknown)"] += 1

    # Jira overlay: unique requested table names per (source, layer) and what the catalog shows
    jira: Dict[tuple, dict] = defaultdict(lambda: {"requested": set(), "in_dev": set(), "in_prod": set(), "classes": defaultdict(int)})
    for r in recon["recons"]:
        j = jira[(r.source, r.layer)]
        j["requested"].add(r.candidate)
        if r.in_dev:
            j["in_dev"].add(r.candidate)
        if r.in_prod:
            j["in_prod"].add(r.candidate)
        j["classes"][r.classification] += 1

    keys = set(groups) | set(jira)
    rows = []
    for source, layer in sorted(keys, key=lambda k: (k[0], ["bronze", "silver", "gold"].index(k[1]))):
        tables = groups.get((source, layer), [])
        ev = _evaluate(inp, layer, tables)
        j = jira.get((source, layer))
        rows.append({
            "source": source, "layer": layer, **ev,
            "jira": None if j is None else {
                "requested_tables": len(j["requested"]),
                "found_in_dev": len(j["in_dev"]),
                "found_in_prod": len(j["in_prod"]),
                "story_classes": dict(j["classes"]),
            },
        })

    # real, directly observed evidence about the evidence gaps
    golden = [t.fqn for t in inp.tables if GOLDEN_RE.search(t.name) or GOLDEN_RE.search(t.db)]
    dq = [(t.fqn, t.in_dev, t.in_prod) for t in inp.tables if "dq" in t.db.lower() and "metrics" in t.db.lower()]
    old_single = []
    for t in inp.tables:
        if in_scope(t) and t.in_prod and t.history and t.history.get("versions") == 1:
            age = (inp.history_as_of - date_of(t.history.get("first_version"))).days
            if age > inp.cfg["fresh_window_days"]:
                old_single.append((t.source, t.fqn, age))

    return {
        "rows": rows,
        "excluded": dict(excluded),
        "golden_name_matches": golden,
        "dq_metrics_tables": dq,
        "one_time_loads": old_single,
    }


def date_of(s: str) -> date:
    return date.fromisoformat(s[:10])
