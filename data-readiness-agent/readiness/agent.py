"""Question answering over the evidence.

This is a deterministic router, not an LLM: it maps a question to tool calls over the real
evidence and returns a structured answer plus the tools it called. It can only say what the
data supports, and it says "I can't tell" when it can't. An LLM can later sit on top of the
same tools (see README); the tool layer is the part that keeps answers grounded.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Optional

from .engine import Engine
from .match import CLASS_LABELS
from .report import SHORT

STOP = {"carl", "gold", "silver", "bronze", "legacy", "oracle", "modelled", "other", "usage", "insights",
        "global", "channel", "dim", "fact", "ldr", "via", "the", "unmapped"}
SHORT_OK = {"neo", "dwh", "nrld", "mit"}
SUGGESTED = [
    "Give me an overview",
    "Which sources are safe for an agent to use?",
    "What is blocked?",
    "Is FreeWheel ready?",
    "Where does Jira disagree with the lake?",
    "What can't you measure?",
    "How fresh is the data?",
    "Look up DCI_RATECARD_HEADER",
]


def _tool(name: str, args: dict, result: str) -> dict:
    return {"tool": name, "args": args, "result": result}


class Agent:
    def __init__(self, eng: Engine):
        self.e = eng

    # ---- helpers ---------------------------------------------------------
    def _sources_in(self, q: str) -> List[str]:
        rows = self.e.sc["rows"]
        names = sorted({r["source"] for r in rows if r["source"] != "unmapped"})
        found = []
        ql = q.lower()
        for n in names:
            nl = n.lower()
            words = [w for w in re.findall(r"[a-z0-9]+", nl) if w not in STOP and (len(w) >= 4 or w in SHORT_OK)]
            if nl in ql or any(re.search(rf"\b{re.escape(w)}\b", ql) for w in words):
                found.append(n)
        return found[:3]

    def _layer_in(self, q: str) -> Optional[str]:
        for l in ("bronze", "silver", "gold"):
            if re.search(rf"\b{l}\b", q.lower()):
                return l
        return None

    # ---- answer builders -------------------------------------------------
    def overview(self) -> dict:
        st = self.e.state()
        t, j = st["totals"], st["jira"]
        gates = Counter(r["gate"]["verdict"] for r in st["rows"] if r["counts"]["tables"])
        stale_inputs = [i for i in st["inputs"] if i["age_days"] > 7]
        return {
            "headline": f"{t['in_prod']} of {t['tables']} scored tables are in prod. {t['dev_only']} sit only in dev.",
            "bullets": [
                f"Agent-use gate across {sum(gates.values())} populated source/layer groups: "
                f"{gates.get('BLOCK', 0)} BLOCK, {gates.get('CAUTION', 0)} CAUTION, {gates.get('CLEARED', 0)} CLEARED. "
                "Nothing is CLEARED because no data-quality, schema or parity evidence exists.",
                f"No prod table shows a recurring load in the retained history ({t['prod_recurring']} of {t['prod_with_history']} with history). This is 'not evidenced', not proof of no schedule.",
                f"{j['blocked_with_prod_table']} of {j['blocked_total']} Blocked Jira stories already have their table in prod.",
                f"Only {j['matched']} of {j['reconciled']} table-named stories matched a catalog table; the rest are not started, post-date the catalog, or are naming drift.",
                *( [f"Staleness: " + ", ".join(f"{i['name']} is {i['age_days']} days old" for i in stale_inputs) + "."] if stale_inputs else []),
            ],
            "tools": [_tool("get_state", {}, f"{len(st['rows'])} source/layer rows, {len(st['findings'])} findings")],
            "followups": ["Which sources are safe for an agent to use?", "What is blocked?", "What can't you measure?"],
        }

    def gate_overview(self) -> dict:
        rows = [r for r in self.e.sc["rows"] if r["counts"]["tables"]]
        by = Counter(r["gate"]["verdict"] for r in rows)
        caution = [r for r in rows if r["gate"]["verdict"] == "CAUTION"]
        return {
            "headline": f"No source is cleared for unsupervised agent use. {by.get('CAUTION', 0)} groups are usable with caution, {by.get('BLOCK', 0)} are blocked.",
            "table": {"cols": ["Source", "Layer", "In prod", "Verdict", "Why"],
                      "rows": [[r["source"], r["layer"], f"{r['counts']['in_prod']}/{r['counts']['tables']}", r["gate"]["verdict"], r["gate"]["reason"]] for r in caution]},
            "bullets": ["CAUTION means the tables are in prod, so an agent can read them, but quality is unverified. The agent should cite the data as unverified and avoid irreversible actions on it."],
            "tools": [_tool("gate_by_source_layer", {}, f"{len(rows)} groups evaluated")],
            "followups": ["Is iDeal ready?", "What can't you measure?"],
            "caveat": "The gate is derived from the proposed rubric, not an approved standard.",
        }

    def source_readiness(self, sources: List[str], layer: Optional[str]) -> dict:
        rows = [r for r in self.e.sc["rows"] if r["source"] in sources and (not layer or r["layer"] == layer)]
        tools = [_tool("readiness_by_source", {"sources": sources, "layer": layer}, f"{len(rows)} rows")]
        if not rows:
            return {"headline": f"No rows for {', '.join(sources)}{' / ' + layer if layer else ''}.", "tools": tools}
        recs = [r for r in self.e.recon["recons"] if r.source in sources and (not layer or r.layer == layer)]
        tools.append(_tool("jira_for_source", {"sources": sources}, f"{len(recs)} table stories"))
        cls = Counter(r.classification for r in recs)
        bullets = []
        for r in rows:
            c = r["counts"]
            if not c["tables"]:
                bullets.append(f"{r['source']} {r['layer']}: no tables in the catalog.")
                continue
            bullets.append(f"{r['source']} {r['layer']}: {c['in_dev']} in dev, {c['in_prod']} in prod of {c['tables']}. "
                           f"Verdict {r['gate']['verdict']}: {r['gate']['reason']}")
        if recs:
            bullets.append("Jira: " + ", ".join(f"{n} {SHORT.get(k, k)}" for k, n in cls.most_common()) + ".")
        blocked = [r for r in recs if r.status == "Blocked"]
        if blocked:
            bullets.append("Blocked: " + ", ".join(r.key for r in blocked) + ".")
        worst = "BLOCK" if all(r["gate"]["verdict"] == "BLOCK" for r in rows) else ("CAUTION" if any(r["gate"]["verdict"] in ("CAUTION", "CLEARED") for r in rows) else "BLOCK")
        head = {"BLOCK": "Not ready for an agent to act on.", "CAUTION": "Partly usable, with caution."}[worst]
        return {
            "headline": f"{', '.join(sources)}: {head}",
            "bullets": bullets,
            "tools": tools,
            "followups": [f"What is blocked for {sources[0]}?", "What can't you measure?"],
            "caveat": f"Catalog is {self.e.state()['inputs'][0]['age_days']} days old. Quality criteria are unverified for every layer.",
        }

    def blocked(self) -> dict:
        st = self.e.state()
        by_key = {r.key: r for r in self.e.recon["recons"]}
        rows, named = [], 0
        for b in self.e.inp.jira["blocked"]:
            r = by_key.get(b["key"])
            if r:
                named += 1
            rows.append([b["key"], b["summary"].strip()[:80], SHORT.get(r.classification, r.classification) if r else "no table named"])
        rows.sort(key=lambda x: (x[2] == "no table named", x[0]))
        live = st["jira"]["blocked_with_prod_table"]
        return {
            "headline": f"{st['jira']['blocked_total']} stories are Blocked. {live} of them already have a table in prod.",
            "bullets": [f"{named} of the blocked stories name a table; for the other {len(rows) - named} the lake cannot say anything.",
                        "A Blocked story whose table is already in prod is either a stale ticket or live-but-unaccepted data. Ask the owner which."],
            "table": {"cols": ["Story", "Summary", "Lake says"], "rows": rows},
            "tools": [_tool("list_blocked", {}, f"{len(rows)} stories"), _tool("jira_vs_catalog", {}, f"{named} matched to table names")],
            "followups": ["Where does Jira disagree with the lake?"],
        }

    def jira(self) -> dict:
        st = self.e.state()["jira"]
        return {
            "headline": f"{st['matched']} of {st['reconciled']} table-named stories match a catalog table.",
            "table": {"cols": ["Reconciliation", "Stories"], "rows": [[c["label"], c["count"]] for c in st["classes"]]},
            "bullets": ["Open the 'Jira vs lake' tab to filter these and see the tables behind each."],
            "tools": [_tool("jira_vs_catalog", {}, f"{st['reconciled']} reconciled, {st['unparsed']} without a table name")],
            "followups": ["What is blocked?"],
            "caveat": "Matching is a naming heuristic; a no-match is a lead, not a verdict.",
        }

    def gaps(self) -> dict:
        st = self.e.state()
        g = st["golden_name_matches"]
        return {
            "headline": f"{len(st['gaps'])} rubric criteria cannot be measured from any data we hold.",
            "table": {"cols": ["Criterion", "Layer", "What is needed"], "rows": [[f"{x['id']} {x['title']}", x["layer"], x["needs"]] for x in st["gaps"]]},
            "bullets": [
                f"Golden / eval datasets: a name search over {st['totals']['tables']} tables found {len(g)}.",
                *[f"DQ results store: {n} (dev={'Y' if d else 'N'}, prod={'Y' if p else 'N'})." for n, d, p in st["dq_metrics_tables"]],
                "Environment isolation (non-prod DMS pointing at prod Oracle, CARL-4112) is only in Jira/ARB notes: not scorable here.",
            ],
            "tools": [_tool("evidence_gaps", {}, f"{len(st['gaps'])} criteria without evidence"), _tool("name_search", {"pattern": "golden|eval|ground_truth|benchmark"}, f"{len(g)} hits")],
            "followups": ["Which sources are safe for an agent to use?"],
        }

    def freshness(self) -> dict:
        st = self.e.state()
        t = st["totals"]
        w = st["thresholds"]["fresh_window_days"]
        return {
            "headline": f"{t['stale_in_prod']} of {t['in_prod']} prod tables were not updated within {w} days of the catalog snapshot.",
            "table": {"cols": ["Input", "As of", "Age (days)", "Detail"], "rows": [[i["name"], i["as_of"], i["age_days"], i["detail"]] for i in st["inputs"]]},
            "bullets": ["The catalog is the oldest input, so findings that depend on it (Done-but-no-table, testing-but-no-table) may be overtaken by events.",
                        "Change the freshness window in the Rubric tab to see how this moves."],
            "tools": [_tool("input_freshness", {}, "3 inputs"), _tool("count_stale_prod", {"window_days": w}, f"{t['stale_in_prod']} stale")],
            "followups": ["What can't you measure?"],
        }

    def recurrence(self) -> dict:
        t = self.e.totals()
        rows = [r for r in self.e.sc["rows"] if r["counts"]["prod_with_history"]]
        return {
            "headline": f"{t['prod_recurring']} of {t['prod_with_history']} prod tables with history show a recurring load.",
            "table": {"cols": ["Source", "Layer", "With history", "Recurring", "Single snapshot"],
                      "rows": [[r["source"], r["layer"], r["counts"]["prod_with_history"], r["counts"]["prod_recurring"], r["counts"]["prod_single_snapshot"]] for r in rows]},
            "bullets": ["'Recurring' means commits on at least the configured number of distinct days in the last 30. A single retained snapshot may just mean snapshots were expired, so treat this as not evidenced rather than proof of no schedule."],
            "tools": [_tool("load_cadence", {"min_days": self.e.inp.cfg["recurring_min_commit_days_30d"]}, f"{len(rows)} groups with history")],
            "followups": ["How fresh is the data?"],
        }

    def dev_only(self) -> dict:
        rows = [r for r in self.e.sc["rows"] if r["counts"]["tables"] and r["counts"]["in_prod"] == 0]
        rows.sort(key=lambda r: -r["counts"]["tables"])
        return {
            "headline": f"{sum(r['counts']['tables'] for r in rows)} tables across {len(rows)} source/layer groups exist only in dev.",
            "table": {"cols": ["Source", "Layer", "Tables in dev only"], "rows": [[r["source"], r["layer"], r["counts"]["tables"]] for r in rows]},
            "tools": [_tool("dev_only_groups", {}, f"{len(rows)} groups")],
            "followups": ["Which sources are safe for an agent to use?"],
        }

    def table_lookup(self, names: List[str]) -> dict:
        res = [self.e.triage_one(n) for n in names[:3]]
        bullets = []
        for r in res:
            bullets.append(f"{r['input']}: {r['title']}. {r['next']}")
            for h in r.get("tables", [])[:3]:
                bullets.append(f"   {h['fqn']}: dev={'Y' if h['in_dev'] else 'N'}, prod={'Y' if h['in_prod'] else 'N'}")
            for s in r.get("stories", [])[:2]:
                bullets.append(f"   {s['key']} ({s['status']}): {s['summary'][:70]}")
        return {
            "headline": f"Looked up {len(res)} table name{'s' if len(res) != 1 else ''}.",
            "bullets": bullets,
            "tools": [_tool("triage_table", {"name": r["input"]}, r.get("code", "")) for r in res],
            "followups": ["Open the Triage tab to check many table names at once"],
        }

    # ---- router ----------------------------------------------------------
    def ask(self, question: str) -> dict:
        q = (question or "").strip()[:500]
        if not q:
            return {"headline": "Ask me something about readiness.", "suggestions": SUGGESTED, "tools": []}
        ql = q.lower()

        toks = [t for t in re.findall(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)?", q) if "_" in t or "." in t]
        toks = [t for t in toks if not t.lower().startswith(("e.g", "i.e"))]
        if toks:
            return self.table_lookup(toks)

        srcs = self._sources_in(q)
        if srcs and not re.search(r"\b(all|every|overall)\b", ql):
            return self.source_readiness(srcs, self._layer_in(q))
        if re.search(r"\bblock(ed|ers?)?\b", ql):
            return self.blocked()
        if re.search(r"\b(overview|summary|summari[sz]e|big picture|where are we|what'?s going on)\b", ql):
            return self.overview()
        if re.search(r"\b(jira|tickets?|stor(y|ies)|disagree|mismatch(es)?)\b", ql):
            return self.jira()
        if re.search(r"\b(gaps?|unverified|evidence|golden|eval|dq|quality|measure|missing|can'?t|cannot)\b", ql):
            return self.gaps()
        if re.search(r"\b(fresh|freshness|stale|old|up to date|age|ages|recent|snapshot)\b", ql):
            return self.freshness()
        if re.search(r"\b(recur\w*|cadence|schedul\w*|one.time|reload\w*)\b", ql):
            return self.recurrence()
        if re.search(r"\b(dev.only|only in dev|promot\w*|not in prod)\b", ql):
            return self.dev_only()
        if re.search(r"\b(safe|trust\w*|agents?|use|act|clear\w*|gate|ready|reliable)\b", ql):
            return self.gate_overview()
        out = self.overview()
        out["headline"] = "I'm not sure what you meant, so here is the overview. " + out["headline"]
        out["suggestions"] = SUGGESTED
        return out
