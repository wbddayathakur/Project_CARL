#!/usr/bin/env python3
"""Run the built page in headless Chromium: did any script throw, did every tab render,
did a placeholder (undefined / NaN) leak into what a reader sees?

    python verify.py [--shots]      # --shots also writes PNGs of each tab to out/shots/
"""
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).parent
PAGE = HERE / "out" / "CARL_Delivery_Roadmap.html"
TABS = ["plan", "timeline", "when", "sources", "reconfirm", "method"]
BROWSERS = ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium"]
TRAP = """<script>window.addEventListener('error',function(e){if(document.getElementById('JSERR'))return;
var d=document.createElement('pre');d.id='JSERR';d.textContent=(e.message||'?')+' @'+(e.lineno||'?')+':'+(e.colno||'?');
document.documentElement.appendChild(d);},true);</script>"""


def browser():
    for b in BROWSERS:
        if Path(b).exists():
            return b
    sys.exit("no Chromium-based browser found")


def dom_of(uri):
    return subprocess.run([browser(), "--headless", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=6000",
                           "--dump-dom", uri], capture_output=True, text=True, timeout=120).stdout


class T(HTMLParser):
    def __init__(self):
        super().__init__(); self.o = []; self.k = 0
    def handle_starttag(self, t, a):
        self.k += t in ("script", "style")
    def handle_endtag(self, t):
        self.k = max(0, self.k - (t in ("script", "style")))
    def handle_data(self, d):
        if not self.k: self.o.append(d)


def text(h):
    p = T(); p.feed(h)
    return re.sub(r"\s+", " ", " ".join(p.o)).strip()


def section(dom, sid):
    m = re.search(r'<section id="%s"[^>]*>' % sid, dom)
    if not m: return None
    i, depth = m.end(), 1
    for t in re.finditer(r"</?section\b", dom[i:]):
        depth += 1 if t.group(0) == "<section" else -1
        if depth == 0: return dom[i:i + t.start()]
    return dom[i:]


def main():
    src = PAGE.read_text()
    problems = []
    with tempfile.TemporaryDirectory() as td:
        trap = Path(td) / "t.html"
        trap.write_text(src.replace("<head>", "<head>" + TRAP, 1))
        e = re.search(r'<pre id="JSERR">(.*?)</pre>', dom_of(trap.as_uri()), re.S)
        if e: problems.append("JavaScript error: " + e.group(1)[:200])
    dom = dom_of(PAGE.as_uri())
    print("%-10s %7s %6s" % ("tab", "chars", "nodes")); print("-" * 28)
    for sid in TABS:
        h = section(dom, sid)
        if h is None: problems.append(f"{sid}: missing"); continue
        t = text(h)
        if len(t) < 200: problems.append(f"{sid}: only {len(t)} chars")
        print("%-10s %7d %6d" % (sid, len(t), len(re.findall(r"<[a-zA-Z]", h))))
    vis = re.sub(r"<(script|style)\b.*?</\1>", " ", dom, flags=re.S | re.I)
    vt = text(vis)
    for bad in ("undefined", "NaN", "[object Object]", "Infinity", "null"):
        if re.search(r"\b%s\b" % re.escape(bad), vt): problems.append(f"{bad!r} visible in text")
        for a in re.findall(r'\b(?:style|href|title)="([^"]*)"', vis):
            if bad in a: problems.append(f"{bad!r} in attribute: {a[:70]!r}"); break
    if "--shots" in sys.argv:
        out = HERE / "out" / "shots"; out.mkdir(exist_ok=True)
        for sid in TABS:
            subprocess.run([browser(), "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                            "--window-size=1600,1500", "--virtual-time-budget=6000",
                            f"--screenshot={out / (sid + '.png')}", PAGE.as_uri() + "#" + sid],
                           capture_output=True, timeout=120)
        print("screenshots →", out)
    print()
    for p in problems: print("FAIL ", p)
    if not problems: print("OK  all tabs rendered, no script errors, no placeholders")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
