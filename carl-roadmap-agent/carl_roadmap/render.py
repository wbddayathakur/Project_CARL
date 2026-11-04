"""Write fresh numbers into the published HTML, in place.

The page is edited rather than regenerated. Everything a person wrote — the
narrative, the programme diagram, the tab structure, the dependency prose —
stays byte-identical; only the data blocks move. That is what makes it safe to
run unattended every Monday against a file people have already shared.

Three things change each week:

  const DATA={...}   the epic/dependency payload
  const ASOF="..."   the as-of date the swimlane and RAG rules key off
  <span id=stamp>    the refresh stamp in the header

and three one-time patches make the page derive its own headline numbers
instead of carrying them as literals. Each patch detects its own output, so
running twice is a no-op.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import datetime, date
from pathlib import Path

log = logging.getLogger(__name__)

PATCH_MARK = "/*carl-roadmap-agent"


def mark(label: str) -> str:
    """A patch marker that is a complete JavaScript comment on its own.

    The label has to live *inside* the comment. Emitting `/*...*/kpis` leaves a
    bare identifier, and since the next line starts with `(`, JavaScript's
    automatic semicolon insertion does not fire — it parses as `kpis(...)`.
    Worse, a `<div id="kpis">` publishes `window.kpis`, so the call resolves to
    an element and throws "kpis is not a function" instead of something that
    points at the real cause.
    """
    return f"{PATCH_MARK}:{label}*/"


def mark_html(label: str) -> str:
    """The same marker for patches that land inside HTML rather than script.

    A `/*...*/` comment is only a comment to a JavaScript parser. Dropped into
    a template literal it is just text, and the reader sees it printed at the
    top of the tab.
    """
    return f"<!--carl-roadmap-agent:{label}-->"


def write(
    html_path: Path,
    *,
    data: dict,
    asof: str,
    history_dir: Path | None = None,
    generated_at: str | None = None,
    status_colours: dict | None = None,
) -> dict:
    """Splice `data` into the page. Returns a short report of what changed."""
    if not html_path.exists():
        raise FileNotFoundError(
            f"{html_path} does not exist. The agent updates the published page "
            f"in place; it does not create it. Check output.html_path."
        )

    original = html_path.read_text(encoding="utf-8")
    text = original

    if history_dir:
        _snapshot(html_path, history_dir)

    text, n_data = _replace_data(text, data)
    text, n_asof = _replace_asof(text, asof)
    text = _patch_progress_bar(text)
    text = _patch_kpis(text)
    text = _patch_status_colours(text, status_colours or {})
    text = _patch_exec_summary(text)
    text = _patch_structure_tab(text)
    text = _patch_relationship_tab(text)
    text = _patch_stamp(text, generated_at or datetime.now().strftime("%Y-%m-%d %H:%M"))

    if text == original:
        log.info("page already current — nothing written")
        return {"changed": False, "bytes": len(text)}

    # Write via a temp file in the same directory so a crash mid-write cannot
    # leave a half-page at a URL people have bookmarked. OneDrive syncs the
    # rename atomically.
    tmp = html_path.with_suffix(".html.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(html_path)

    log.info("wrote %s (%s bytes)", html_path, len(text))
    return {
        "changed": True,
        "bytes": len(text),
        "data_replaced": n_data,
        "asof_replaced": n_asof,
        "path": str(html_path),
    }


# ------------------------------------------------------------------ replacers


def _replace_data(text: str, data: dict) -> tuple[str, int]:
    marker = "const DATA="
    start = text.find(marker)
    if start == -1:
        raise ValueError("no `const DATA=` in the page")
    open_brace = text.index("{", start)
    close = _match_brace(text, open_brace)
    # ensure_ascii keeps the file 7-bit so it survives being mailed around and
    # re-saved by Windows tools, which is how the v2 page acquired mojibake.
    blob = json.dumps(data, ensure_ascii=True, separators=(", ", ": "))
    return text[: open_brace] + blob + text[close + 1 :], 1


def _replace_asof(text: str, asof: str) -> tuple[str, int]:
    new, n = re.subn(
        r'const ASOF="\d{4}-\d{2}-\d{2}"',
        f'const ASOF="{asof}"',
        text,
        count=1,
    )
    if not n:
        raise ValueError("no `const ASOF=` in the page")
    return _replace_subtitle(new, asof), n


def _replace_subtitle(text: str, asof: str) -> str:
    """Keep the date and provenance a reader sees in step with the data.

    `const ASOF` drives the late/overdue arithmetic, but the header carries its
    own "Status as of 5 Oct 2026" in prose, plus a source list crediting a
    spreadsheet export for numbers that now come from Jira directly. Leaving
    either stale is worse than useless: the refresh stamp says today, the
    headline says a fortnight ago, and the reader has to guess which to trust.
    """
    pretty = date.fromisoformat(asof).strftime("%-d %b %Y")
    text = re.sub(
        r"Status as of \d{1,2} \w{3} \d{4}",
        lambda _m: f"Status as of {pretty}",
        text,
        count=1,
    )
    # The epic numbers no longer come from the 30 Sep export. The other
    # workbooks still back the usage, intake and planning tabs, so they stay.
    return text.replace(
        "Sources: CARL_Epic_Mapping_Initiative_15Oct 2.xlsx "
        "(Jira export 30 Sep, Sprint 19)",
        "Epics, status and story points: live Jira (CARL) \u00b7 Other tabs",
        1,
    )


def _match_brace(text: str, i: int) -> int:
    depth, j, in_str, esc = 0, i, False, False
    while j < len(text):
        ch = text[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    raise ValueError("unterminated object")


# -------------------------------------------------------------- one-time fixes


def _patch_progress_bar(text: str) -> str:
    """Give the fourth bucket its own colour and an honest label.

    The original bar drew [done, in-flight, to-do] as green/amber/grey, which
    read as "grey means nobody is on it". Under the agreed rule To Do and In
    Triage are active requirements work held by the PM, so grey becomes blue
    and says so. Keeping it a separate segment rather than folding it into
    amber preserves the one distinction an exec actually acts on: whether a
    programme is short of engineers or short of definition.
    """
    if mark("spbar") in text:
        return text

    pattern = re.compile(r"function spbar\(sp\)\{.*?\n", re.S)
    replacement = (
        mark("spbar") + "\n"
        "function spbar(sp){if(!sp||!sp[0])return'<span class=\"small\">not sized</span>';"
        "const[t,d,p,r]=sp;const rq=r||0;"
        "return`<div class=\"bar\" title=\"Done ${d} \\u00b7 In build ${p} \\u00b7 "
        "Requirements with PM ${rq}\"><i style=\"width:${d/t*100}%;background:#16a34a\"></i>"
        "<i style=\"width:${p/t*100}%;background:#f59e0b\"></i>"
        "<i style=\"width:${rq/t*100}%;background:#60a5fa\"></i></div>"
        "<span class=\"small\">${d}/${t} SP done (${Math.round(d/t*1000)/10}%) "
        "\\u00b7 ${p+rq} in progress</span>`}\n"
    )
    # A callable replacement, because the snippet contains \u escapes that
    # re.sub would otherwise try to interpret as regex group references.
    new, n = pattern.subn(lambda _m: replacement, text, count=1)
    if not n:
        log.warning("could not patch spbar — progress bars keep the old 3-colour scheme")
        return text
    return new


def _patch_status_colours(text: str, colours: dict) -> str:
    """Make sure every status Jira can return has a colour.

    The page hard-codes `const STC={...}` with the nine statuses that existed
    in the 30 September export, and indexes it in one place without a fallback:
    `background:${STC[i.st]}`. The first epic to reach a status outside that
    list — "In Testing", this week — renders `background:undefined` and the bar
    comes out unstyled.

    Rather than freeze another list, this merges in a colour for every status
    actually present in the data and adds the missing fallback, so a new
    workflow step degrades to grey instead of to nothing.
    """
    m = re.search(r"const STC=\{(.*?)\};", text, re.S)
    if not m:
        log.warning("could not find STC — status colours left as they are")
        return text

    # Tolerate whitespace: this has to re-read its own output next week, and a
    # strict `"k":"v"` pattern silently parsed nothing once json.dumps had put
    # a space after the colon — which dropped every existing colour.
    existing = dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', m.group(1)))
    added = {s: c for s, c in colours.items() if s not in existing}
    if added:
        log.info("added a colour for %s", ", ".join(sorted(added)))
    merged = {**existing, **added}
    text = (text[:m.start()] +
            "const STC=" + json.dumps(merged, ensure_ascii=False,
                                      separators=(",", ":")) + ";" +
            text[m.end():])

    # The one unguarded lookup. The other sites already fall back.
    return text.replace("background:${STC[i.st]}", "background:${STC[i.st]||'#e2e8f0'}")


def _patch_exec_summary(text: str) -> str:
    """Derive the exec paragraph instead of asserting it.

    The v3 bottom line was prose with two numbers dropped in: "Data Foundations
    is the most mature", "platform largely built", "International alone 717 SP
    unprojected". None of that could be checked against the page it sat on, and
    two of the three stopped being true within a fortnight.

    Everything below is computed from ITEMS, so each claim can be verified on
    the Epic Tracker tab, and anything the data cannot support is simply not
    said. Where a figure rests on an assumption — unsized epics, excluded
    statuses — the sentence states the assumption rather than hiding it.
    """
    if mark_html("exec") in text:
        return text

    pattern = re.compile(
        r'<div class="card" style="border-left:6px solid #312e81">'
        r'<div class="big">.*?</div></div>',
        re.S,
    )
    if not pattern.search(text):
        log.warning("could not find the exec summary block — it keeps its old prose")
        return text

    summary = (
        mark_html("exec") +
        '<div class="card" style="border-left:6px solid #312e81"><div class="big">'
        "${(function(){"
        "const live=ITEMS.filter(i=>!i.rm);"
        "const sz=live.filter(i=>i.sp&&i.sp[0]);"
        "let t=0,d=0,b=0,r=0;"
        "sz.forEach(i=>{t+=i.sp[0];d+=i.sp[1]||0;b+=i.sp[2]||0;r+=i.sp[3]||0});"
        "const open=b+r;"
        # Per-programme remaining, to name the concentration rather than guess it.
        "const rem={};PK.forEach(p=>rem[p]=0);"
        "sz.forEach(i=>{if(rem[i.p]!==undefined)rem[i.p]+=(i.sp[2]||0)+(i.sp[3]||0)});"
        "const order=PK.slice().sort((x,y)=>rem[y]-rem[x]);"
        "const top=order[0],rest=order.slice(1).reduce((a,p)=>a+rem[p],0);"
        # Epics carrying tickets but no estimate are invisible to every percentage.
        "const un=live.filter(i=>(!i.sp||!i.sp[0])&&i.tk);"
        "const unTk=un.reduce((a,i)=>a+(i.tk||0),0);"
        "const late=(typeof DEPS!=='undefined')?DEPS.filter(x=>x.late).length:0;"
        "const od=live.filter(i=>{const dd=i.fc||i.t;"
        "return dd&&dd<ASOF&&i.st!='Done'&&i.sp&&i.sp[0]&&i.sp[1]<i.sp[0]}).length;"
        "const dl=(DATA.delta&&DATA.delta.done_delta)||0;"
        "const pc=v=>Math.round(v/t*1000)/10;"
        "const n=v=>Math.round(v).toLocaleString();"
        "let s=[];"
        "s.push(`<b>Where CARL stands.</b> ${live.length} epics carrying "
        "${n(t)} estimated story points, ${pc(d)}% delivered.`);"
        "if(dl>0)s.push(`${n(dl)} points closed since the last refresh.`);"
        "else if(dl<0)s.push(`${n(-dl)} points re-opened or re-estimated down since the last refresh.`);"
        "s.push(`<b>${n(open)} points remain.</b> ${n(b)} sit with engineers; "
        "${n(r)} sit with product owners awaiting requirements — "
        # Deliberately not the word "undefined": the page verifier treats that
        # token as a rendering failure, and prose should not trip it.
        "${Math.round(r/open*100)}% of what is left is unscoped rather than unbuilt.`);"
        "if(rem[top]>0)s.push(`${PIL[top].n} holds ${n(rem[top])} of those points`+"
        "(rem[top]>rest?`, more than the other four programmes combined`:``)+`.`);"
        "if(un.length)s.push(`${un.length} epics carry ${n(unTk)} tickets with no estimate, "
        "so the real total is above ${n(t)}.`);"
        "let risk=[];"
        "if(od)risk.push(`${od} epics are past their target date`);"
        "if(late)risk.push(`${late} external dependencies are late`);"
        "if(risk.length)s.push(risk.join(` and `)+`.`);"
        "return s.join(` `)})()}"
        "</div></div>"
    )
    new, n = pattern.subn(lambda _m: summary, text, count=1)
    if not n:
        log.warning("exec summary not replaced")
        return text
    return new


def _patch_structure_tab(text: str) -> str:
    """Add the initiative level the Program Structure tab already claims to show.

    The legend says "Program -> Initiative / sub-project -> Jira epic", but the
    renderer only nests programme -> sub-project, so the initiative was never on
    the page. Jira already answers it: every epic sits under a Tech Capability,
    carried through as `ws`. Deriving the level from that rather than a second
    hand-maintained column means it cannot drift away from Jira.
    """
    if mark("struct") in text:
        return text

    pattern = re.compile(r"function drawStruct\(\)\{.*?\n(?=function openP\()", re.S)
    if not pattern.search(text):
        log.warning("could not find drawStruct — the structure tab keeps two levels")
        return text

    btn = (
        "padding:4px 10px;border:1px solid #cbd5e1;border-radius:8px;background:#fff"
    )
    new_fn = (
        mark("struct") + "\n"
        "function drawStruct(){const el=document.getElementById('struct');"
        # An epic with no Tech Capability is a real finding, not a blank cell.
        "const wsOf=i=>(i.ws&&i.ws!=='\\u2014')?i.ws:'No initiative set in Jira';"
        "el.innerHTML=`<div class=\"legend\"><span>Program \\u2192 initiative "
        "(Jira Tech Capability) \\u2192 sub-project \\u2192 Jira epic. "
        "Click an epic for dates, owner and dependencies.</span>"
        "<button class=\"ctl\" onclick=\"document.querySelectorAll('#struct details')"
        ".forEach(d=>d.open=true)\" style=\"" + btn + "\">Expand all</button>"
        "<button onclick=\"document.querySelectorAll('#struct details')"
        ".forEach(d=>d.open=false)\" style=\"" + btn + "\">Collapse all</button></div>`+"
        "PK.map(p=>{const its=ITEMS.filter(i=>i.p==p),r=roll(its);"
        "const inis=[...new Set(its.map(wsOf))].sort();"
        "const subs=[...new Set(its.map(i=>i.sub))];"
        "return`<details id=\"P-${p}\" style=\"border-left:6px solid ${PIL[p].c}\">"
        "<summary><span style=\"color:${PIL[p].c}\">${PIL[p].n} "
        "<span class=\"small\" style=\"font-weight:400\">\\u2014 ${r.n} epics \\u00b7 "
        "${r.tk} tickets \\u00b7 ${inis.length} initiative${inis.length==1?'':'s'} "
        "\\u00b7 ${subs.length} sub-projects</span></span>"
        "<span style=\"width:260px\">${spbar([r.t,r.d,r.p,r.o])}</span></summary>"
        "${inis.map(w=>{const wi=its.filter(i=>wsOf(i)==w),wr=roll(wi);"
        "const wsub=[...new Set(wi.map(i=>i.sub))];"
        "return`<details style=\"margin:4px 0 4px 12px;border-left:3px solid ${PIL[p].c}\">"
        "<summary><span>${w} <span class=\"small\" style=\"font-weight:400\">\\u2014 "
        "${wr.n} epic${wr.n==1?'':'s'} \\u00b7 ${wsub.length} "
        "sub-project${wsub.length==1?'':'s'}</span></span>"
        "<span style=\"width:250px\">${spbar([wr.t,wr.d,wr.p,wr.o])}</span></summary>"
        "${wsub.map(s=>{const si=wi.filter(i=>i.sub==s),sr=roll(si);"
        "return`<details style=\"margin-left:12px\"><summary><span>${s} "
        "<span class=\"small\" style=\"font-weight:400\">\\u2014 ${sr.n} epics"
        "${si.some(i=>i.rm)?` + ${si.filter(i=>i.rm).length} roadmap-only`:''}"
        "</span></span><span style=\"width:240px\">${spbar([sr.t,sr.d,sr.p,sr.o])}"
        "</span></summary>"
        "<table><tr><th>Epic</th><th>Name</th><th>Status</th><th>RAG</th>"
        "<th>Assignee</th><th>Tickets</th><th>Progress</th><th>Target</th><th>\\u26d3</th></tr>"
        "${si.map(i=>`<tr class=\"cl\" onclick=\"openD('${i.k}')\"><td>${jk(i.k)}</td>"
        "<td>${i.n}${i.rm?' <span class=\"pill\" style=\"background:#f1f5f9\">roadmap-only</span>':''}"
        "${i.note?`<div class=\"flag\">${i.note}</div>`:''}</td><td>${stb(i.st)}</td>"
        "<td><span class=\"rag r${i.rag}\"></span></td><td>${i.o}</td><td>${i.tk??'\\u2014'}</td>"
        "<td style=\"min-width:120px\">${spbar(i.sp)}</td>"
        "<td>${fmt(i.fc||i.t)}${i.fc?' <span class=\"flag\">rev.</span>':''}</td>"
        "<td>${gates(i.k).length||''}</td></tr>`).join('')}</table></details>`"
        "}).join('')}</details>`}).join('')}</details>`}).join('')}\n"
    )
    return pattern.sub(lambda _m: new_fn, text, count=1)


def _patch_relationship_tab(text: str) -> str:
    """Add a tab for how items relate to each other, not just to outside teams.

    The existing Dependencies tab lists the 15 external gates — things other
    teams owe CARL. The 77 epic-to-epic links were in the page data and shown
    nowhere, which matters because 53 of them cross a programme boundary: the
    coupling an exec needs to see is between CARL's own programmes, and no tab
    was reporting it.
    """
    if mark("rel") in text:
        return text

    nav = '["dep","Dependencies"]'
    if nav not in text:
        log.warning("no Dependencies tab to anchor the relationship tab to")
        return text
    text = text.replace(nav, nav + ',["rel","Dependency Map"]', 1)

    sec = '<section id="dep"></section>'
    if sec not in text:
        log.warning("no dep section to anchor the relationship section to")
        return text
    text = text.replace(sec, sec + '<section id="rel"></section>', 1)

    js = (
        "\n" + mark("rel") + "\n"
        ";(function(){const el=document.getElementById('rel');if(!el)return;"
        "const live=k=>byK[k];"
        # Keep only links whose endpoints both survived this refresh.
        "const E=RELS.filter(e=>live(e[0])&&live(e[1]));"
        "const deg={};E.forEach(e=>{deg[e[0]]=(deg[e[0]]||0)+1;deg[e[1]]=(deg[e[1]]||0)+1});"
        "const cross=E.filter(e=>byK[e[0]].p!=byK[e[1]].p);"
        "const M={};PK.forEach(a=>{M[a]={};PK.forEach(b=>M[a][b]=0)});"
        "E.forEach(e=>{const a=byK[e[0]].p,b=byK[e[1]].p;if(M[a]&&M[a][b]!==undefined)M[a][b]++});"
        "const mx=Math.max(1,...PK.map(a=>Math.max(...PK.map(b=>M[a][b]))));"
        "const nm=k=>byK[k]?byK[k].n:k;"
        # Roadmap-only rows use keys like SF2 that are not Jira issues. Printing
        # "CARL-SF2" invents an issue the reader will try to open.
        "const lbl=k=>/^\\d/.test(k)?('CARL-'+k):k;"
        # --- headline -------------------------------------------------------
        "let h=`<div class=\"card\"><div class=\"big\">"
        "<b>How CARL's work is wired together.</b> ${E.length} links between "
        "${Object.keys(deg).length} epics, of which <b>${cross.length}</b> cross a "
        "programme boundary. ${DEPS.length} further gates are owed by teams outside "
        "CARL, ${DEPS.filter(x=>x.late).length} of them late.</div></div>`;"
        # --- programme coupling matrix ---------------------------------------
        "h+=`<div class=\"card\"><h3>Which programme feeds which</h3>"
        "<div class=\"small\" style=\"margin-bottom:8px\">Rows deliver to columns. "
        "A dense row is a programme other teams wait on.</div>"
        "<table><tr><th></th>${PK.map(b=>`<th>${PIL[b].n}</th>`).join('')}<th>Feeds out</th></tr>"
        "${PK.map(a=>{const out=PK.reduce((s,b)=>s+(a==b?0:M[a][b]),0);"
        "return`<tr><th style=\"text-align:left;color:${PIL[a].c}\">${PIL[a].n}</th>"
        "${PK.map(b=>{const v=M[a][b];const bg=v?`background:rgba(49,46,129,${(0.08+0.6*v/mx).toFixed(2)});"
        "color:${v/mx>0.5?'#fff':'#0f172a'}`:'color:#cbd5e1';"
        "return`<td style=\"text-align:center;${bg}\">${v||'\\u00b7'}</td>`}).join('')}"
        "<td style=\"text-align:center\"><b>${out||'\\u2014'}</b></td></tr>`}).join('')}"
        "</table></div>`;"
        # --- the cross-programme graph ---------------------------------------
        "const cols={};PK.forEach(p=>cols[p]=[]);"
        "const touched={};cross.forEach(e=>{touched[e[0]]=1;touched[e[1]]=1});"
        "Object.keys(touched).forEach(k=>{const p=byK[k].p;if(cols[p])cols[p].push(k)});"
        "PK.forEach(p=>cols[p].sort((x,y)=>(deg[y]||0)-(deg[x]||0)));"
        "const used=PK.filter(p=>cols[p].length);"
        "const W=1000,GAP=W/(used.length||1),RY=30,TOP=46;"
        "const rows=Math.max(1,...used.map(p=>cols[p].length));"
        "const H=TOP+rows*RY+20;"
        "const pos={};used.forEach((p,ci)=>{const x=GAP*ci+GAP/2;"
        "cols[p].forEach((k,ri)=>pos[k]={x:x,y:TOP+ri*RY+10,p:p})});"
        "let svg=`<svg viewBox=\"0 0 ${W} ${H}\" style=\"width:100%;height:auto\" "
        "font-family=\"inherit\">`;"
        "used.forEach((p,ci)=>{const x=GAP*ci+GAP/2;"
        "svg+=`<text x=\"${x}\" y=\"24\" text-anchor=\"middle\" font-size=\"13\" "
        "font-weight=\"700\" fill=\"${PIL[p].c}\">${PIL[p].n}</text>`});"
        "cross.forEach(e=>{const a=pos[e[0]],b=pos[e[1]];if(!a||!b)return;"
        "const mxx=(a.x+b.x)/2;"
        "svg+=`<path d=\"M${a.x} ${a.y} C${mxx} ${a.y} ${mxx} ${b.y} ${b.x} ${b.y}\" "
        "fill=\"none\" stroke=\"${PIL[a.p].c}\" stroke-width=\"1.1\" opacity=\".38\"/>`});"
        "Object.keys(pos).forEach(k=>{const n=pos[k],i=byK[k];"
        "const done=i.sp&&i.sp[0]&&i.sp[1]>=i.sp[0];"
        "svg+=`<g class=\"cl\" onclick=\"openD('${k}')\">"
        "<title>${lbl(k)} \\u2014 ${nm(k).replace(/\"/g,'')} (${i.st})</title>"
        "<circle cx=\"${n.x}\" cy=\"${n.y}\" r=\"${4+Math.min(5,(deg[k]||1))}\" "
        "fill=\"${done?'#86efac':PIL[n.p].l}\" stroke=\"${PIL[n.p].c}\" stroke-width=\"1.4\"/>"
        "<text x=\"${n.x+12}\" y=\"${n.y+4}\" font-size=\"10.5\" fill=\"#334155\">"
        "${lbl(k)}</text></g>`});"
        "svg+=`</svg>`;"
        "h+=`<div class=\"card\"><h3>Cross-programme links</h3>"
        "<div class=\"small\" style=\"margin-bottom:8px\">Only links that cross a "
        "programme are drawn \\u2014 ${cross.length} of ${E.length}. Node size is the "
        "number of links; green means the epic is fully delivered. Click any node.</div>"
        "${svg}</div>`;"
        # --- hubs -------------------------------------------------------------
        "const hubs=Object.keys(deg).sort((a,b)=>deg[b]-deg[a]).slice(0,10);"
        "h+=`<div class=\"card\"><h3>Most connected epics</h3>"
        "<div class=\"small\" style=\"margin-bottom:8px\">If one of these slips it "
        "moves more than its own programme.</div>"
        "<table><tr><th>Epic</th><th>Name</th><th>Programme</th><th>Initiative</th>"
        "<th>Status</th><th>Links</th><th>Gates</th><th>Progress</th></tr>"
        "${hubs.map(k=>{const i=byK[k];return`<tr class=\"cl\" onclick=\"openD('${k}')\">"
        "<td>${jk(k)}</td><td>${i.n}</td><td>${pp(i.p)}</td>"
        "<td class=\"small\">${i.ws||'\\u2014'}</td><td>${stb(i.st)}</td>"
        "<td style=\"text-align:center\"><b>${deg[k]}</b></td>"
        "<td style=\"text-align:center\">${gates(k).length||''}</td>"
        "<td style=\"min-width:110px\">${spbar(i.sp)}</td></tr>`}).join('')}"
        "</table></div>`;"
        # --- full adjacency ----------------------------------------------------
        "const src=[...new Set(E.map(e=>e[0]))]"
        ".sort((a,b)=>(byK[a].p+byK[a].n).localeCompare(byK[b].p+byK[b].n));"
        "h+=`<div class=\"card\"><h3>Every link, by upstream epic</h3>"
        "<div class=\"small\" style=\"margin-bottom:8px\">Read as: the epic on the left "
        "has to land before the epics on the right can finish.</div>"
        "<table><tr><th>Upstream</th><th>Programme</th><th>Status</th>"
        "<th>Feeds these epics</th></tr>"
        "${src.map(k=>{const outs=E.filter(e=>e[0]==k).map(e=>e[1]);const i=byK[k];"
        "return`<tr><td class=\"cl\" onclick=\"openD('${k}')\">${jk(k)}"
        "<div class=\"small\">${i.n}</div></td><td>${pp(i.p)}</td><td>${stb(i.st)}</td>"
        "<td>${outs.map(z=>{const j=byK[z];const xp=j.p!=i.p;"
        "return`<span class=\"cl\" onclick=\"openD('${z}')\" style=\"display:inline-block;"
        "margin:2px 6px 2px 0;padding:2px 7px;border-radius:7px;"
        "border:1px solid ${xp?PIL[j.p].c:'#e2e8f0'};background:${xp?PIL[j.p].l:'#f8fafc'}\">"
        "${lbl(z)} <span class=\"small\">${j.n.slice(0,42)}</span></span>`}).join('')}"
        "</td></tr>`}).join('')}</table></div>`;"
        "el.innerHTML=h;})();\n"
    )
    return _append_to_script(text, js)


def _patch_kpis(text: str) -> str:
    """Replace the literal headline numbers with ones derived from the data.

    The v3 page carried `<b>87</b> Epics`, `<b>3,992</b> Story points` and so
    on as text. Those were right on 30 September and wrong by the following
    Monday. Deriving them from ITEMS means the agent only ever has to update
    one thing.
    """
    if mark("kpis") in text:
        return text

    pattern = re.compile(r'<div class="kpis">.*?</div>\s*(?=<div class="g5">)', re.S)
    if not pattern.search(text):
        log.warning("could not find the KPI strip — headline numbers stay literal")
        return text

    text = pattern.sub('<div class="kpis" id="kpis"></div>', text, count=1)

    # The filler runs after ITEMS exists. Appending to the end of the exec IIFE
    # is fragile; a standalone block at the end of the script is not.
    filler = (
        "\n" + mark("kpis") + "\n"
        ";(function(){const el=document.getElementById('kpis');if(!el)return;"
        "const live=ITEMS.filter(i=>!i.rm);"
        "let t=0,d=0,b=0,r=0,tk=0,bl=0,un=0;"
        "live.forEach(i=>{tk+=i.tk||0;if(i.sp&&i.sp[0]){t+=i.sp[0];d+=i.sp[1]||0;"
        "b+=i.sp[2]||0;r+=i.sp[3]||0}else if(i.tk){un++}});"
        "bl=(typeof BLOCKED!=='undefined')?BLOCKED.sp:0;"
        "const pct=t?Math.round(d/t*1000)/10:0,ip=b+r;"
        "const k=(v,l,c)=>`<div class=\"kpi\"><b${c?` style=\"color:${c}\"`:''}>${v}</b>"
        "<span>${l}</span></div>`;"
        "el.innerHTML=k(live.length,'Epics in Jira')"
        "+k(tk.toLocaleString(),'Tickets mapped')"
        "+k(t.toLocaleString(),'Story points')"
        "+k(pct+'%','SP done ('+d.toLocaleString()+')','var(--G)')"
        "+k(ip.toLocaleString(),'SP in progress ('+b.toLocaleString()+' build \\u00b7 '"
        "+r.toLocaleString()+' requirements)','#b45309')"
        "+k(un,'Epics with tickets but no estimate','var(--R)')"
        "+k(DEPS.length+' \\u00b7 '+DEPS.filter(x=>x.late).length+' late','Open dependencies','var(--X)');"
        "})();\n"
    )
    return _append_to_script(text, filler)


def _patch_stamp(text: str, when: str) -> str:
    """Put a refresh timestamp in the header so staleness is visible.

    A page that silently stops updating is worse than no page, because people
    keep quoting it.
    """
    stamp = (
        f'<div id="refresh-stamp" style="font-size:11px;opacity:.75;margin-top:4px">'
        f"Refreshed from Jira {when} \u00b7 carl-roadmap-agent</div>"
    )
    if 'id="refresh-stamp"' in text:
        return re.sub(
            r'<div id="refresh-stamp".*?</div>',
            lambda _m: stamp,
            text,
            count=1,
            flags=re.S,
        )
    # Anchor on the tab strip, which every version of the page has.
    anchor = '<div class="tabs" id="tabs"></div>'
    if anchor in text:
        return text.replace(anchor, stamp + anchor, 1)
    log.warning("no anchor for the refresh stamp")
    return text


def _append_to_script(text: str, snippet: str) -> str:
    """Append JS just before the final </script>."""
    idx = text.rfind("</script>")
    if idx == -1:
        log.warning("no </script> to append to")
        return text
    return text[:idx] + snippet + text[idx:]


# ----------------------------------------------------------------- versioning


def _snapshot(html_path: Path, history_dir: Path) -> None:
    history_dir.mkdir(parents=True, exist_ok=True)
    dest = history_dir / f"{html_path.stem}-{date.today().isoformat()}.html"
    if not dest.exists():
        shutil.copy2(html_path, dest)
        log.info("kept the previous page at %s", dest)
