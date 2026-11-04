"""Engine behind the UI: holds the loaded evidence, recomputes on rubric changes, and exposes
the operations (state, drill-down, triage) the UI and the question-answering agent call."""
from __future__ import annotations

import difflib
import json
import re
import threading
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from .inputs import Inputs, Table, in_scope, load
from .match import CLASS_LABELS, reconcile
from .report import SHORT, findings
from .score import score

LAYERS = ["bronze", "silver", "gold"]
TESTING = {"Ready for Testing", "In Testing", "Ready For UAT", "In Review"}


def _iso(d):
    return d.isoformat() if d else None


def gate(row: dict) -> dict:
    """Derived 'may an agent act on this?' verdict. It can only reach CLEARED when every
    criterion in the rubric has passing evidence, which today none do."""
    stage = row["stage"]
    crit = row["criteria"]
    unverified = [c["id"] for c in crit if c["status"] == "unverified"]
    failed = [c["id"] for c in crit if c["status"] in ("fail", "partial")]
    if stage in ("not present", "dev only"):
        return {"verdict": "BLOCK", "reason": "Not in prod." if stage == "dev only" else "No tables for this source in this layer."}
    reasons = []
    if stage == "partly in prod":
        c = row["counts"]
        reasons.append(f"only {c['in_prod']} of {c['tables']} tables are in prod")
    if any(f.endswith("3") for f in failed):
        reasons.append("some prod tables are stale")
    if unverified:
        reasons.append(f"{len(unverified)} criteria unverified ({', '.join(unverified)})")
    if not reasons and not failed:
        return {"verdict": "CLEARED", "reason": "All rubric criteria have passing evidence."}
    return {"verdict": "CAUTION", "reason": "; ".join(reasons) or "criteria not fully passing"}


class Engine:
    def __init__(self, root: Path, today: Optional[date] = None):
        self.root = root
        self.today = today or date.today()
        self.lock = threading.RLock()
        self.reload()

    # ---- lifecycle -------------------------------------------------------
    def reload(self) -> None:
        with self.lock:
            self.cfg_path = self.root / "config" / "rubric.json"
            self.inp: Inputs = load(self.root / "data", self.cfg_path)
            self.baseline = (self.inp.cfg["fresh_window_days"], self.inp.cfg["recurring_min_commit_days_30d"])
            self._compute()

    def _compute(self) -> None:
        self.recon = reconcile(self.inp)
        self.sc = score(self.inp, self.recon)
        for r in self.sc["rows"]:
            r["gate"] = gate(r)
        self.findings = findings(self.inp, self.recon, self.sc)
        self.stories = {}
        for i in self.inp.jira["children_of_ingestion_epics"] + self.inp.jira["blocked"]:
            self.stories.setdefault(i["key"], i)

    def set_thresholds(self, fresh: int, recurring: int) -> dict:
        if not (1 <= fresh <= 365) or not (1 <= recurring <= 30):
            raise ValueError("fresh_window_days must be 1-365 and recurring_min_commit_days_30d 1-30")
        with self.lock:
            before = self.totals()
            self.inp.cfg["fresh_window_days"] = fresh
            self.inp.cfg["recurring_min_commit_days_30d"] = recurring
            self._compute()
            return {"before": before, "after": self.totals()}

    def save_thresholds(self) -> None:
        with self.lock:
            raw = json.loads(self.cfg_path.read_text())
            raw["fresh_window_days"] = self.inp.cfg["fresh_window_days"]
            raw["recurring_min_commit_days_30d"] = self.inp.cfg["recurring_min_commit_days_30d"]
            self.cfg_path.write_text(json.dumps(raw, indent=2) + "\n")
            self.baseline = (raw["fresh_window_days"], raw["recurring_min_commit_days_30d"])

    # ---- views -----------------------------------------------------------
    def totals(self) -> dict:
        rows = self.sc["rows"]
        s = lambda k: sum(r["counts"][k] for r in rows)
        return {
            "tables": s("tables"), "in_dev": s("in_dev"), "in_prod": s("in_prod"),
            "fresh_in_prod": s("fresh_in_prod"), "stale_in_prod": s("in_prod") - s("fresh_in_prod"),
            "prod_recurring": s("prod_recurring"), "prod_with_history": s("prod_with_history"),
            "dev_only": sum(r["counts"]["tables"] for r in rows if r["counts"]["tables"] and r["counts"]["in_prod"] == 0),
        }

    def state(self) -> dict:
        with self.lock:
            inp, recon = self.inp, self.recon
            cls = Counter(r.classification for r in recon["recons"])
            blocked = inp.jira["blocked"]
            by_key = {r.key: r for r in recon["recons"]}
            blocked_live = [b["key"] for b in blocked if b["key"] in by_key and by_key[b["key"]].classification == "live_but_open"]
            gaps = [
                {"id": c["id"], "layer": c["layer"], "title": c["title"], "needs": c.get("needs", "")}
                for c in inp.cfg["criteria"] if c["evidence"] == "none"
            ]
            return {
                "today": _iso(self.today),
                "rubric_status": inp.cfg["status"],
                "rubric_note": inp.cfg["note"],
                "thresholds": {
                    "fresh_window_days": inp.cfg["fresh_window_days"],
                    "recurring_min_commit_days_30d": inp.cfg["recurring_min_commit_days_30d"],
                    "baseline": {"fresh_window_days": self.baseline[0], "recurring_min_commit_days_30d": self.baseline[1]},
                },
                "inputs": [
                    {"name": "Glue catalog (dev + prod)", "as_of": _iso(inp.glue_as_of), "age_days": (self.today - inp.glue_as_of).days,
                     "detail": f"{len(inp.tables)} tables"},
                    {"name": "Prod load history", "as_of": _iso(inp.history_as_of), "age_days": (self.today - inp.history_as_of).days,
                     "detail": f"{inp.history_tables} prod tables"},
                    {"name": "Jira (CARL)", "as_of": _iso(inp.jira_as_of), "age_days": (self.today - inp.jira_as_of).days,
                     "detail": f"{recon['stories_total']} stories"},
                ],
                "jira_site": inp.jira.get("site", ""),
                "totals": self.totals(),
                "findings": self.findings,
                "rows": self.sc["rows"],
                "excluded": self.sc["excluded"],
                "criteria": inp.cfg["criteria"],
                "gaps": gaps,
                "golden_name_matches": self.sc["golden_name_matches"],
                "dq_metrics_tables": self.sc["dq_metrics_tables"],
                "jira": {
                    "stories_total": recon["stories_total"], "reconciled": recon["reconciled"], "matched": recon["matched"],
                    "unparsed": len(recon["unparsed"]), "unmatched_parsed": len(recon["unmatched_parsed"]),
                    "classes": [{"id": k, "label": CLASS_LABELS[k], "short": SHORT.get(k, k), "count": cls.get(k, 0)} for k in CLASS_LABELS],
                    "blocked_total": len(blocked), "blocked_with_prod_table": len(blocked_live),
                },
                "sources": sorted({r["source"] for r in self.sc["rows"]}),
            }

    def tables(self, source: str = "", layer: str = "", q: str = "", prod: str = "", limit: int = 300) -> dict:
        with self.lock:
            story_by_table = defaultdict(list)
            for r in self.recon["recons"]:
                for t in r.tables:
                    story_by_table[t].append(r.key)
            q = q.lower().strip()
            out = []
            window = self.inp.cfg["fresh_window_days"]
            min_days = self.inp.cfg["recurring_min_commit_days_30d"]
            for t in self.inp.tables:
                if not in_scope(t):
                    continue
                if source and t.source != source:
                    continue
                if layer and t.layer != layer:
                    continue
                if q and q not in t.name.lower():
                    continue
                if prod == "yes" and not t.in_prod:
                    continue
                if prod == "no" and t.in_prod:
                    continue
                h = t.history
                out.append({
                    "fqn": t.fqn, "name": t.name, "source": t.source, "layer": t.layer,
                    "in_dev": t.in_dev, "in_prod": t.in_prod,
                    "dev_updated": _iso(t.dev_updated), "prod_updated": _iso(t.prod_updated),
                    "fresh": bool(t.in_prod and t.prod_updated and (self.inp.glue_as_of - t.prod_updated).days <= window),
                    "versions": h.get("versions") if h else None,
                    "commit_days_30d": h.get("days_with_commits_30d") if h else None,
                    "recurring": bool(h and (h.get("days_with_commits_30d") or 0) >= min_days) if h else None,
                    "stories": story_by_table.get(t.fqn, []),
                })
            out.sort(key=lambda x: (not x["in_prod"], x["name"]))
            return {"total": len(out), "rows": out[:limit], "truncated": len(out) > limit}

    def recon_rows(self, classification: str = "", source: str = "", q: str = "", limit: int = 400) -> dict:
        with self.lock:
            q = q.lower().strip()
            rows = []
            for r in self.recon["recons"]:
                if classification and r.classification != classification:
                    continue
                if source and r.source != source:
                    continue
                if q and q not in r.summary.lower() and q not in r.key.lower() and not any(q in t for t in r.tables):
                    continue
                d = asdict(r)
                d["resolved"] = _iso(r.resolved)
                d["updated"] = _iso(r.updated)
                rows.append(d)
            return {"total": len(rows), "rows": rows[:limit], "truncated": len(rows) > limit}

    # ---- triage: "should this requested table go on the bronze backlog?" ------
    def triage_one(self, raw: str) -> dict:
        name = (raw or "").strip()
        res = {"input": name}
        if not name or len(name) > 200:
            return {**res, "code": "invalid", "title": "Invalid or empty name", "next": "Enter a table name such as DCI_RATECARD_HEADER or DEALBLDR.DCI_RATECLASS."}
        s = re.sub(r"^(bronze|silver|gold)\.", "", name.lower())
        schema = None
        if "." in s:
            schema, tbl = s.split(".", 1)
            cands = [f"{schema}_{tbl}", tbl]
        else:
            cands = [s]
        cands = [re.sub(r"[^a-z0-9_]", "_", c) for c in cands]

        pool = [t for t in self.inp.tables if not t.sandbox_db and not t.noise and t.layer in LAYERS]
        hits: List[Table] = []
        used = cands[0]
        for c in cands:
            hits = [t for t in pool if t.name == c or t.name.endswith("_" + c)]
            if hits:
                used = c
                break
        hit_rows = [{
            "fqn": t.fqn, "layer": t.layer, "source": t.source, "in_dev": t.in_dev, "in_prod": t.in_prod,
            "prod_updated": _iso(t.prod_updated),
        } for t in sorted(hits, key=lambda t: (not t.in_prod, t.layer, t.name))[:8]]

        story_hits = []
        pats = [re.compile(r"(?<![a-z0-9_])" + re.escape(c) + r"(?![a-z0-9_])") for c in cands]
        for k, st in self.stories.items():
            low = st["summary"].lower()
            texts = (low.replace(".", "_"), low.replace(".", " "))
            if any(p.search(t) for p in pats for t in texts):
                story_hits.append({"key": k, "status": st["status"], "summary": st["summary"].strip(),
                                   "resolved": (st.get("resolved") or "")[:10] or None})
        story_hits.sort(key=lambda x: int(x["key"].split("-")[1]))

        related = []
        if schema:
            cnt = Counter(t.source for t in pool if t.name.startswith(schema + "_") or f"_{schema}_" in t.name)
            related = [{"source": s_, "tables": n} for s_, n in cnt.most_common(3)]

        close = []
        if not hits:
            names = {t.name: t.fqn for t in pool}
            close = sorted({names[n] for n in difflib.get_close_matches(used, list(names), n=3, cutoff=0.85)})

        prod_b = [h for h in hits if h.in_prod and h.layer == "bronze"]
        prod_any = [h for h in hits if h.in_prod]
        dev_any = [h for h in hits if h.in_dev]
        open_story = next((x for x in story_hits if x["status"] not in ("Done", "Archive")), None)
        if prod_b or prod_any:
            code = "in_prod"
            hh = (prod_b or prod_any)[0]
            title = f"Already in prod ({hh.layer}): no new ingestion needed"
            nxt = "Check recurrence and freshness below before relying on it."
            if open_story:
                nxt += f" Jira {open_story['key']} is still '{open_story['status']}': likely a stale ticket or unfinished acceptance."
        elif dev_any:
            code = "dev_only"
            title = "Exists in dev only: needs promotion, not a new ingestion"
            nxt = "Put promotion to prod on the backlog."
        elif story_hits:
            st = story_hits[0]
            if st["status"] == "Done":
                after = bool(st["resolved"] and st["resolved"] > self.inp.glue_as_of.isoformat())
                code = "done_no_table"
                title = f"Jira {st['key']} is Done but the catalog has no such table"
                nxt = ("It was resolved after the catalog snapshot, so refresh the catalog first." if after
                       else "Resolved before the snapshot, so this is a real gap or a rename: confirm with the story owner.")
            else:
                code = "requested_no_table"
                title = f"Requested in Jira ({st['key']}, {st['status']}) but not in the catalog"
                nxt = ("Status says testing/UAT, so check whether the catalog export is stale before treating this as a gap."
                       if st["status"] in TESTING else "Already on the backlog: no duplicate request needed.")
            if close:
                nxt += " Near-identical table names exist: this may be a rename."
        elif close:
            code = "possible_rename"
            title = "Not found, but near-identical table names exist"
            nxt = "Likely a rename or variant of an existing table. Confirm before creating a new backlog item."
        else:
            code = "new_request"
            title = "Not in the catalog and no Jira story: new bronze backlog item"
            nxt = "Create a bronze ingestion story."
            if related:
                nxt += f" Related tables already live under {related[0]['source']} ({related[0]['tables']} tables), so reuse that pipeline and DAG."
            else:
                nxt += " No related tables found, so the source group is unknown: an owner must assign one."
        return {**res, "code": code, "title": title, "next": nxt, "candidate": used,
                "tables": hit_rows, "stories": story_hits[:6], "close_names": close, "related_sources": related,
                "data_age_days": (self.today - self.inp.glue_as_of).days}

    def triage(self, names: List[str]) -> dict:
        names = [n for n in names if n.strip()][:100]
        with self.lock:
            return {"results": [self.triage_one(n) for n in names]}
