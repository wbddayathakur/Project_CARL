"""UI smoke test for the static prototype using a minimal fake DOM in macOS JavaScriptCore.
It drives the real page script: loads, visits every tab, opens a source, asks the agent,
runs a triage and applies a rubric change, failing on any runtime error or missing content.
It does not test layout or styling; open the file in a browser for that.

Usage: python3 tests/check_prototype_ui.py     (skips cleanly if jsc is unavailable)
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSC = Path("/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc")

STUB = r"""
var window = this; window.innerWidth = 1400;
function El(tag){ this.nodeType = 1; this.tag = tag; this.children = []; this.attrs = {}; this.listeners = {}; this.className = ""; this.value = ""; this.style = {}; this.scrollTop = 0; this.scrollHeight = 0; this.parent = null;
  var self = this; this.classList = { add: function(){}, toggle: function(){}, remove: function(){} }; }
El.prototype.append = function(){ for (var i = 0; i < arguments.length; i++) { var c = arguments[i]; if (c && typeof c === "object") c.parent = this; this.children.push(c); } };
El.prototype.replaceChildren = function(){ this.children = []; this.append.apply(this, arguments); };
El.prototype.setAttribute = function(k, v){ this.attrs[k] = v; };
El.prototype.addEventListener = function(t, f){ this.listeners[t] = f; };
El.prototype.replaceWith = function(n){ var p = this.parent, i = p.children.indexOf(this); n.parent = p; p.children[i] = n; };
El.prototype.remove = function(){}; El.prototype.click = function(){}; El.prototype.focus = function(){}; El.prototype.setSelectionRange = function(){};
var _sel = {};
var document = { createElement: function(t){ return new El(t); }, createTextNode: function(s){ return { nodeType: 3, text: String(s) }; },
  querySelector: function(s){ return _sel[s] || (_sel[s] = new El("sel")); }, body: new El("body") };
function URLSearchParams(o){ this.o = o; }
URLSearchParams.prototype.toString = function(){ var o = this.o; return Object.keys(o).map(function(k){ return encodeURIComponent(k) + "=" + encodeURIComponent(o[k]); }).join("&"); };
var URL = { createObjectURL: function(){ return "blob:x"; } }; function Blob(){}
function text(n){ if (!n) return ""; if (n.nodeType === 3) return n.text; return n.children.map(text).join(" "); }
function find(n, pred, out){ out = out || []; if (!n || n.nodeType === 3) return out; if (pred(n)) out.push(n); n.children.forEach(function(c){ find(c, pred, out); }); return out; }
var ticks = async function(){ for (var i = 0; i < 40; i++) await null; };
var failures = [], passes = 0;
function check(name, cond){ if (cond) passes++; else failures.push(name); }
"""

DRIVER = r"""
(async function () {
  await ticks();
  var view = document.querySelector("#view");
  check("init: no load error", text(view).indexOf("Could not load data") < 0);
  check("overview: findings", text(view).indexOf("What the evidence says") >= 0);
  check("overview: kpis", /scored tables in prod/.test(text(view)));
  check("header: static pill", text(document.querySelector("#pills")).indexOf("Static prototype") >= 0);
  check("header: no reload button in static mode", text(document.querySelector("#pills")).indexOf("Reload data") < 0);
  check("chat: welcome", text(document.querySelector("#msgs")).indexOf("Ask me about data readiness") >= 0);

  tab = "sources"; await renderView(); await ticks();
  check("sources: gate column", text(view).indexOf("Agent-use gate") >= 0);
  check("sources: FreeWheel row", text(view).indexOf("FreeWheel") >= 0);
  openRow = "FreeWheel|bronze"; await renderView(); await ticks();
  check("sources: criteria detail", text(view).indexOf("Promoted to prod") >= 0);
  check("sources: table drill-down", text(view).indexOf("d_ad_unit") >= 0);

  tab = "jira"; await renderView(); await ticks();
  check("jira: summary", text(view).indexOf("matched a catalog table") >= 0);
  check("jira: story rows", text(view).indexOf("CARL-698") >= 0);
  jf.classification = "live_but_open"; await renderView();
  check("jira: filter", text(view).indexOf("CARL-284") >= 0 && text(view).indexOf("CARL-4073") < 0);
  jf.classification = "";

  tab = "triage"; triText = "DCI_RATECARD_HEADER\nDEALBLDR.BRAND_NEW_THING"; await renderView();
  var btn = find(view, function (n) { return n.tag === "button" && text(n) === "Triage"; })[0];
  check("triage: button present", !!btn);
  btn.listeners.click(); await ticks();
  check("triage: in prod verdict", text(view).indexOf("IN PROD") >= 0);
  check("triage: new request verdict", text(view).indexOf("NEW REQUEST") >= 0);
  var before = document.body.children.length; exportTri();
  check("triage: export runs", true);

  tab = "rubric"; draft = null; await renderView();
  check("rubric: proposed banner", text(view).indexOf("PROPOSED") >= 0);
  check("rubric: no save button", find(view, function (n) { return n.tag === "button" && text(n) === "Save to config"; }).length === 0);
  check("rubric: selects not number inputs", find(view, function (n) { return n.tag === "input" && n.attrs.type === "number"; }).length === 0);
  draft = { fresh: 30, rec: 2 };
  var apply = find(view, function (n) { return n.tag === "button" && text(n) === "Apply"; })[0];
  apply.listeners.click(); await ticks();
  check("rubric: threshold applied", S.thresholds.fresh_window_days === 30);
  check("rubric: delta shown", text(view).indexOf("Stale prod tables:") >= 0);

  var msgs = document.querySelector("#msgs");
  await ask("Is FreeWheel ready?"); await ticks();
  check("ask: source answer", text(msgs).indexOf("FreeWheel: Not ready") >= 0);
  check("ask: evidence trail", text(msgs).indexOf("Evidence trail") >= 0);
  await ask("What is blocked?"); await ticks();
  check("ask: blocked table", text(msgs).indexOf("stories are Blocked") >= 0);
  await ask("Look up D_BREAK"); await ticks();
  check("ask: lookup", text(msgs).indexOf("CARL-2816") >= 0);

  print(failures.length ? "FAIL: " + failures.join("; ") : "OK");
  print("passes=" + passes);
})().catch(function (e) { print("EXCEPTION: " + e + (e.stack ? "\n" + e.stack : "")); });
"""


def main() -> int:
    if not JSC.exists():
        print("jsc not available: skipped")
        return 0
    html = (ROOT / "prototype" / "readiness_prototype.html").read_text()
    scripts = re.findall(r"<script>\n(.*?)\n</script>", html, re.S)
    if len(scripts) != 2:
        print(f"expected 2 inline scripts, found {len(scripts)}")
        return 1
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "stub.js").write_text(STUB)
        (d / "shim.js").write_text(scripts[0])
        (d / "page.js").write_text(scripts[1])
        (d / "driver.js").write_text(DRIVER)
        # one concatenated script so top-level let/const from the page are visible to the driver
        (d / "all.js").write_text("\n".join((d / n).read_text() for n in ("stub.js", "shim.js", "page.js", "driver.js")))
        res = subprocess.run([str(JSC), str(d / "all.js")], capture_output=True, text=True, timeout=180)
    out = (res.stdout + res.stderr).strip()
    print(out)
    return 0 if res.returncode == 0 and out.splitlines()[0] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
