"""Shared helpers for the UC1 field-mapping build."""
import os, re, sys, json
from collections import OrderedDict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "work"))
from lkml_parse import parse as _lkml_parse   # noqa: E402

LEG = os.path.join(HERE, "work", "legacy", "carl-legacy-source-master")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

_pcache = {}
_tcache = {}


def lkml(rel):
    if rel not in _pcache:
        _pcache[rel] = _lkml_parse(os.path.join(LEG, rel))
    return _pcache[rel]


def text_lines(rel):
    if rel not in _tcache:
        _tcache[rel] = open(os.path.join(LEG, rel), encoding="utf-8", errors="replace").read().split("\n")
    return _tcache[rel]


def resolve(ref):
    """ref = (relpath, name). name 'L:needle' -> first line containing needle; else LookML field name.
    Returns (citation, snippet)."""
    rel, name = ref
    if name.startswith("L:"):
        needle = name[2:]
        for i, l in enumerate(text_lines(rel), 1):
            if needle in l:
                return f"{rel}:L{i}", l.strip()[:400]
        for i, l in enumerate(text_lines(rel), 1):
            if needle.lower() in l.lower():
                return f"{rel}:L{i}", l.strip()[:400]
        return f"{rel}:(needle not found: {needle})", ""
    v = lkml(rel)
    for f in v["fields"]:
        if f["name"] == name:
            sql = re.sub(r"\s+", " ", (f["sql"] or "")).strip()
            lab = f["label"]
            return f"{rel}:L{f['line_start']}-{f['line_end']} [{f['kind']} {name}" + (f" '{lab}'" if lab else "") + "]", sql[:900]
    return f"{rel}:(field {name} not found)", ""


# ------------------------------------------------------------------ xlsx styling
HDR = PatternFill("solid", fgColor="1F3864")
SUB = PatternFill("solid", fgColor="D9E1F2")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
STATUS_FILLS = [("MISMATCH", "F8CBAD"), ("NOT FOUND", "D9D9D9"), ("NOT RE-DERIVABLE", "D9D9D9"), ("NOT TESTABLE", "D9D9D9"), ("UNVERIFIABLE", "FFE699"), ("CHAT-ONLY", "FFE699"), ("VERIFIED-DATA", "C6E0B4"), ("LEGACY-SOURCE", "DDEBF7")]


def status_fill(text):
    t = str(text or "")
    for k, c in STATUS_FILLS:
        if k in t:
            return PatternFill("solid", fgColor=c)
    return None


def write_sheet(wb, name, headers, rows, widths=None, status_cols=(), title=None, note=None, freeze_col=1):
    ws = wb.create_sheet(name[:31])
    hr = 1
    if title:
        ws.cell(1, 1, title).font = Font(bold=True, size=13)
        hr = 2
        if note:
            ws.cell(2, 1, note).alignment = Alignment(wrap_text=True, vertical="top")
            ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max(2, min(len(headers), 8)))
            ws.row_dimensions[2].height = 75
            hr = 3
    for j, h in enumerate(headers, 1):
        c = ws.cell(hr, j, h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HDR
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = BORDER
    for i, row in enumerate(rows, hr + 1):
        for j, v in enumerate(row, 1):
            if isinstance(v, (list, tuple, dict, set)):
                v = json.dumps(v, default=str) if isinstance(v, dict) else "; ".join(map(str, v))
            if isinstance(v, str) and len(v) > 32000:
                v = v[:32000] + " ...[truncated]"
            c = ws.cell(i, j, v)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = BORDER
            if (j - 1) in status_cols:
                f = status_fill(v)
                if f:
                    c.fill = f
    widths = widths or [18] * len(headers)
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = ws.cell(hr + 1, freeze_col + 1)
    ws.auto_filter.ref = f"A{hr}:{get_column_letter(len(headers))}{hr + max(1, len(rows))}"
    return ws


def new_wb():
    wb = Workbook()
    wb.remove(wb.active)
    return wb


def profile_summary(p, k=6):
    if not p:
        return ""
    s = f"non-null {p['non_null']:,} / null {p['null']:,} ({p['null_pct']}%) / distinct {p['distinct']:,}"
    if p.get("min") is not None:
        s += f"; min {p['min']:,.2f} max {p['max']:,.2f}"
        if p.get("sum") is not None:
            s += f"; sum {p['sum']:,.2f}"
    vals = p.get("values") or []
    if vals and p["distinct"] <= 60:
        s += "; values: " + ", ".join(f"{v} ({n:,})" for v, n in vals[:k]) + (" ..." if len(vals) > k else "")
    elif vals:
        s += "; top: " + ", ".join(f"{v} ({n:,})" for v, n in vals[:3])
    return s
