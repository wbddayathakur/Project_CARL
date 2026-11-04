"""Parity check: the static prototype's JavaScript logic must give the same answers as the Python
engine on the same inputs. Runs the shim headlessly in macOS JavaScriptCore (`jsc`).

Usage: python3 tests/check_prototype_parity.py     (skips cleanly if jsc is unavailable)
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from readiness.agent import Agent  # noqa: E402
from readiness.engine import Engine  # noqa: E402

JSC = Path("/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc")
TRIAGE = ["DCI_RATECARD_HEADER", "DEALBLDR.DCI_RATECLASS", "D_BREAK", "SALESFORCE.SF_CASECOMMENT", "DEALBLDR.BRAND_NEW_THING",
          "FACT_PACING_REVENUE_BUDGET_MO", "dim_month", "zzz_nothing_like_this", "  ", "d_ad_unit", "bronze.ideal_dci_acct"]
QUESTIONS = ["Give me an overview", "Which sources are safe for an agent to use?", "What is blocked?", "Is FreeWheel ready?",
             "Where does Jira disagree with the lake?", "What can't you measure?", "How fresh is the data?",
             "Look up DCI_RATECARD_HEADER", "is ideal silver ready", "how are loads scheduled", "Which tables are dev only?", "blah blah",
             "Is Salesforce ready?", "NEO bronze status"]


def main() -> int:
    if not JSC.exists():
        print("jsc not available: skipped")
        return 0
    html = (ROOT / "prototype" / "readiness_prototype.html").read_text()
    shim = re.search(r"<script>\n(// Static data layer.*?)\n</script>", html, re.S).group(1)
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "shim.js").write_text(shim)
        (Path(d) / "run.js").write_text(
            f'load("{d}/shim.js");\n'
            f"var T = __STATIC_TEST, out = {{triage: {{}}, ask: {{}}}};\n"
            f"{json.dumps(TRIAGE)}.forEach(function (n) {{ var r = T.triageOne(n); out.triage[n] = [r.code, r.title, r.next, (r.close_names||[]).join('|'), (r.tables||[]).map(function(t){{return t.fqn}}).join('|'), (r.stories||[]).map(function(s){{return s.key}}).join('|')]; }});\n"
            f"{json.dumps(QUESTIONS)}.forEach(function (q) {{ var r = T.ask(q); out.ask[q] = [r.headline, (r.tools||[]).map(function(t){{return t.tool}}).join('|'), (r.bullets||[]).length, r.table ? r.table.rows.length : -1]; }});\n"
            f"var st = T.state(); out.totals = st.totals; out.nrows = st.rows.length;\n"
            f"var tb = T.tables({{source: 'FreeWheel', layer: 'bronze'}}); out.tb = [tb.total, tb.rows[0].name];\n"
            f"var rc = T.recon({{classification: 'live_but_open'}}); out.rc = rc.total;\n"
            f"T.setThresholds(30, 2); out.totals30 = T.state().totals;\n"
            f"print(JSON.stringify(out));\n")
        res = subprocess.run([str(JSC), str(Path(d) / "run.js")], capture_output=True, text=True, timeout=120)
    if res.returncode != 0 or not res.stdout.strip():
        print("jsc failed:", res.stderr or res.stdout)
        return 1
    js = json.loads(res.stdout.strip().splitlines()[-1])

    e = Engine(ROOT)
    a = Agent(e)
    bad = []
    for n in TRIAGE:
        r = e.triage_one(n)
        py = [r["code"], r["title"], r["next"], "|".join(r.get("close_names") or []),
              "|".join(t["fqn"] for t in r.get("tables") or []), "|".join(s["key"] for s in r.get("stories") or [])]
        if py != js["triage"][n]:
            bad.append(("triage", n, py, js["triage"][n]))
    for q in QUESTIONS:
        r = a.ask(q)
        py = [r["headline"], "|".join(t["tool"] for t in r["tools"]), len(r.get("bullets", [])), len(r["table"]["rows"]) if r.get("table") else -1]
        if py != js["ask"][q]:
            bad.append(("ask", q, py, js["ask"][q]))
    if e.state()["totals"] != js["totals"]:
        bad.append(("totals", "", e.state()["totals"], js["totals"]))
    tb = e.tables(source="FreeWheel", layer="bronze")
    if [tb["total"], tb["rows"][0]["name"]] != js["tb"]:
        bad.append(("tables", "", [tb["total"], tb["rows"][0]["name"]], js["tb"]))
    if e.recon_rows(classification="live_but_open")["total"] != js["rc"]:
        bad.append(("recon", "", None, js["rc"]))
    e.set_thresholds(30, 2)
    if e.totals() != js["totals30"]:
        bad.append(("totals30", "", e.totals(), js["totals30"]))

    checks = len(TRIAGE) + len(QUESTIONS) + 4
    if bad:
        for b in bad:
            print("MISMATCH", b)
        print(f"{len(bad)} of {checks} checks differ")
        return 1
    print(f"parity OK: {checks} checks identical between Python engine and in-browser JS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
