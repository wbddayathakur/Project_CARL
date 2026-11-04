"""Reconcile Jira stories against the Glue catalog.

A story is only reconciled when a table name can be parsed from its title. The parse is a
naming heuristic, so the result always reports how many stories could not be parsed and how
many parsed names matched nothing. Those counts are the honest match rate.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from .inputs import Inputs, Table, in_scope

# Ordered: first pattern that matches wins. Each yields candidate table names, strictest first.
_PATTERNS = [
    (re.compile(r"\b(?:BRONZE|SILVER|GOLD)\.([A-Za-z][A-Za-z0-9_]+)"), lambda m: [m.group(1)]),
    (re.compile(r"\b([A-Z][A-Z0-9]+)\.([A-Z][A-Z0-9_]+)\b"), lambda m: [f"{m.group(1)}_{m.group(2)}", m.group(2)]),
    (re.compile(r"Ingest\s+Freewheel\s+([A-Za-z][A-Za-z0-9_]+)", re.I), lambda m: [m.group(1)]),
    (re.compile(r"Bronze Ingestion\s*[—-]\s*([a-z][a-z0-9_]+)"), lambda m: [m.group(1)]),
    (re.compile(r"Ingest\s+([A-Z][A-Z0-9_]{3,})\s+to\b"), lambda m: [m.group(1)]),
    (re.compile(r"Get\s+([A-Z][A-Z0-9_]{3,})\s+table"), lambda m: [m.group(1)]),
    (re.compile(r"(?:Silver|Gold)\s+Table:\s*([a-z][a-z0-9_]+)"), lambda m: [m.group(1)]),
    (re.compile(r"Develop\s+FreeWheel\s+([a-z][a-z0-9_]+)\s+in\s+(?:Silver|Gold)", re.I), lambda m: [m.group(1)]),
]


def expected_layer(summary: str) -> Optional[str]:
    s = summary.lower()
    found = [l for l in ("bronze", "silver", "gold") if l in s]
    return found[0] if len(found) == 1 else None


def candidates(summary: str) -> List[str]:
    for pat, fn in _PATTERNS:
        m = pat.search(summary)
        if m:
            return [c.lower() for c in fn(m)]
    return []


def _name_matches(table: str, cand: str) -> bool:
    return table == cand or table.endswith("_" + cand)


@dataclass
class Recon:
    key: str
    summary: str
    status: str
    resolved: Optional[date]
    epic: str
    source: str
    layer: str
    candidate: str
    confidence: str  # exact | loose | ambiguous | none
    tables: List[str]
    in_dev: bool
    in_prod: bool
    classification: str
    note: str = ""
    updated: Optional[date] = None
    cross_source: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)  # closest catalog names; never counted as a match


TESTING_STATUSES = {"Ready for Testing", "In Testing", "Ready For UAT", "In Review"}

CLASS_LABELS = {
    "done_and_in_prod": "Done in Jira and the table is in prod (consistent)",
    "done_but_dev_only": "Done in Jira, but the table is only in dev (promotion gap)",
    "done_no_table_found": "Done in Jira before the catalog snapshot, but no matching table (gap or naming mismatch)",
    "done_after_snapshot": "Done in Jira after the catalog snapshot (cannot judge: refresh the catalog)",
    "live_but_open": "Table is in prod but the story is still open (stale ticket or unfinished validation)",
    "in_dev_open": "Table is in dev; story open (consistent)",
    "testing_no_table": "Story is in testing/UAT but no matching table in the catalog (gap, or created after the snapshot)",
    "open_no_table": "Story open and no table yet (consistent: not started)",
}


def _classify(status_cat: str, status: str, hit: List[Table], resolved: Optional[date], glue_as_of: date):
    in_dev = any(t.in_dev for t in hit)
    in_prod = any(t.in_prod for t in hit)
    done = status_cat == "done"
    if done and in_prod:
        return "done_and_in_prod"
    if done and in_dev:
        return "done_but_dev_only"
    if done and not hit:
        if resolved is not None and resolved > glue_as_of:
            return "done_after_snapshot"
        return "done_no_table_found"
    if in_prod:
        return "live_but_open"
    if in_dev:
        return "in_dev_open"
    return "testing_no_table" if status in TESTING_STATUSES else "open_no_table"


def reconcile(inp: Inputs) -> Dict[str, object]:
    cfg = inp.cfg
    stories = {}
    for i in inp.jira["children_of_ingestion_epics"]:
        stories[i["key"]] = i
    for i in inp.jira["blocked"]:
        stories.setdefault(i["key"], i)

    by_layer: Dict[str, List[Table]] = {"bronze": [], "silver": [], "gold": []}
    for t in inp.tables:
        if in_scope(t):
            by_layer[t.layer].append(t)

    recons: List[Recon] = []
    unparsed, no_layer, unmatched = [], [], []
    for key, s in sorted(stories.items(), key=lambda kv: int(kv[0].split("-")[1])):
        summ = s["summary"]
        cands = candidates(summ)
        if not cands:
            unparsed.append(key)
            continue
        layer = expected_layer(summ) or expected_layer((s.get("parent") or {}).get("summary", ""))
        if layer is None:  # a table is named but the layer is absent or ambiguous: skip, and say so
            no_layer.append(key)
            continue
        epic = (s.get("parent") or {}).get("key", "")
        source = cfg["epic_sources"].get(epic, "unmapped")
        hit, used, conf = [], cands[0], "none"
        for idx, c in enumerate(cands):
            hit = [t for t in by_layer[layer] if _name_matches(t.name, c)]
            if hit:
                used, conf = c, ("exact" if idx == 0 else "loose")
                break
        cross: List[str] = []
        if source != "unmapped" and hit:
            same = [t for t in hit if t.source == source]
            cross = [t.fqn for t in hit if t.source != source]
            hit = same
            if not hit:
                conf = "none"  # name exists only in another source group: do not claim a match
        elif source == "unmapped" and hit:
            srcs = {t.source for t in hit}
            if len(srcs) == 1:
                source = srcs.pop()
        if len(hit) > 1:
            conf = "ambiguous"
        resolved = None
        if s.get("resolved"):
            resolved = date.fromisoformat(s["resolved"][:10])
        updated = date.fromisoformat(s["updated"][:10]) if s.get("updated") else None
        cls = _classify(s["status_category"], s["status"], hit, resolved, inp.glue_as_of)
        r = Recon(
            key=key, summary=summ, status=s["status"], resolved=resolved, epic=epic,
            source=source, layer=layer, candidate=used, confidence=conf,
            tables=[t.fqn for t in hit],
            in_dev=any(t.in_dev for t in hit), in_prod=any(t.in_prod for t in hit),
            classification=cls, note=CLASS_LABELS[cls], updated=updated, cross_source=cross,
        )
        if conf == "none":
            unmatched.append(key)
            if cls == "done_no_table_found":
                pool = {t.name: t.fqn for t in by_layer[layer]}
                close = difflib.get_close_matches(used, list(pool), n=2, cutoff=0.8)
                r.hints = sorted({pool[n] for n in close})
        recons.append(r)

    return {
        "stories_total": len(stories),
        "reconciled": len(recons),
        "matched": len([r for r in recons if r.confidence != "none"]),
        "unmatched_parsed": unmatched,
        "unparsed": unparsed,
        "no_layer": no_layer,
        "recons": recons,
    }
