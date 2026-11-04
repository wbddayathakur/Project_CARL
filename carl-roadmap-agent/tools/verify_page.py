#!/usr/bin/env python3
"""Open the published page in a real headless browser and prove it works.

The agent can write a page that is valid HTML, parses as valid JSON, and still
renders nine blank tabs — that is exactly what a dangling `rels` key did. The
only check that catches it is running the JavaScript.

    python3 tools/verify_page.py [path-to-html]

Exit 0 if every tab rendered and no script threw; 1 otherwise.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

BROWSERS = [
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]

TABS = ["exec", "struct", "road", "dep", "rel", "use", "intake", "q1", "epics", "meth"]

# The swimlane page is a sibling artefact with its own tab set. Pass the ids as a
# comma-separated second argument to check that one instead.
if len(sys.argv) > 2:
    TABS = [t.strip() for t in sys.argv[2].split(",") if t.strip()]

ERROR_TRAP = """<script>
window.addEventListener('error', function (e) {
  if (document.getElementById('JSERR')) return;
  var d = document.createElement('pre');
  d.id = 'JSERR';
  d.textContent = (e.message || '?') + ' @' + (e.lineno || '?') + ':' + (e.colno || '?');
  document.documentElement.appendChild(d);
}, true);
</script>"""


def browser() -> str:
    for b in BROWSERS:
        if Path(b).exists():
            return b
    sys.exit("no Chromium-based browser found; cannot verify rendering")


def render(path: Path) -> str:
    out = subprocess.run(
        [browser(), "--headless", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=9000", "--dump-dom", path.as_uri()],
        capture_output=True, text=True, timeout=180,
    )
    return out.stdout


def section(dom: str, sid: str) -> str | None:
    m = re.search(r'<section id="%s"[^>]*>' % re.escape(sid), dom)
    if not m:
        return None
    i, depth = m.end(), 1
    for t in re.finditer(r"</?section\b", dom[i:]):
        depth += 1 if t.group(0) == "<section" else -1
        if depth == 0:
            return dom[i:i + t.start()]
    return dom[i:]


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out = []; self.skip = 0
    def handle_starttag(self, t, a):
        if t in ("script", "style"): self.skip += 1
    def handle_endtag(self, t):
        if t in ("script", "style"): self.skip = max(0, self.skip - 1)
    def handle_data(self, d):
        if not self.skip: self.out.append(d)


def text_of(html: str) -> str:
    p = _Text(); p.feed(html)
    return re.sub(r"\s+", " ", " ".join(p.out)).strip()


def main() -> int:
    page = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        json.loads(Path(__file__).parent.joinpath("..", "out", "carl-roadmap.json")
                   .resolve().read_text(encoding="utf-8"))["report"]["html"]["path"])
    if not page.exists():
        sys.exit(f"no page at {page}")

    src = page.read_text(encoding="utf-8")
    problems: list[str] = []

    # 1. Did anything throw?
    with tempfile.TemporaryDirectory() as td:
        trap = Path(td) / "trap.html"
        trap.write_text(src.replace("<head>", "<head>" + ERROR_TRAP, 1), encoding="utf-8")
        err = re.search(r'<pre id="JSERR">(.*?)</pre>', render(trap), re.S)
    if err:
        problems.append("JavaScript error: " + err.group(1).strip()[:200])

    # 2. Did every tab produce content?
    dom = render(page)
    print("%-8s %7s %6s %5s %s" % ("tab", "chars", "nodes", "jira", "opens with"))
    print("-" * 88)
    for sid in TABS:
        html = section(dom, sid)
        if html is None:
            problems.append(f"{sid}: section missing"); continue
        txt = text_of(html)
        if len(txt) < 200:
            problems.append(f"{sid}: rendered {len(txt)} chars — effectively blank")
        print("%-8s %7d %6d %5d %s" % (
            sid, len(txt), len(re.findall(r"<[a-zA-Z]", html)),
            len(re.findall(r"atlassian\.net/browse", html)), txt[:46]))

    # 3. Did any placeholder leak into what a reader sees, or into an attribute?
    #    Attributes matter as much as text: `background:undefined` renders an
    #    unstyled bar, which looks like a design choice rather than a fault.
    visible = re.sub(r"<(script|style)\b.*?</\1>", " ", dom, flags=re.S | re.I)
    vt = text_of(visible)
    for bad in ("undefined", "NaN", "[object Object]", "Infinity"):
        if re.search(r"\b%s\b" % re.escape(bad), vt):
            problems.append(f"{bad!r} is visible in the page text")
        for attr in re.findall(r'\b(?:style|href|src|title)="([^"]*)"', visible):
            if bad in attr:
                problems.append(f"{bad!r} leaked into an attribute: {attr[:70]!r}")
                break

    print()
    if problems:
        for p in problems:
            print("FAIL  " + p)
        return 1
    print("OK  all %d tabs rendered, no script errors, no placeholders visible" % len(TABS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
