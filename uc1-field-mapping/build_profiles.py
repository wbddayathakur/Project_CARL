"""Workbook 5 - value profiles of the two data exports + every validation computed from them."""
import os, json
from common import *


def flat(prefix, v, out):
    if isinstance(v, dict):
        for k, x in v.items():
            flat(f"{prefix} / {k}" if prefix else str(k), x, out)
    elif isinstance(v, (list, tuple)):
        if v and all(not isinstance(x, (dict, list, tuple)) for x in v):
            out.append((prefix, json.dumps(v, default=str)[:1500]))
        else:
            for i, x in enumerate(v):
                flat(f"{prefix}[{i}]", x, out)
    else:
        out.append((prefix, v))


AB = {
    "sf_stage_to_rank": ("Salesforce Opportunity Stage", "Salesforce Projection Rank"),
    "sf_stage_to_status": ("Salesforce Opportunity Stage", "Status Group"),
    "sf_workflow_to_status": ("Salesforce Workflow Status", "Status Group"),
    "sf_class_to_market": ("Salesforce Classification", "Market Type"),
    "sf_class_to_ufyear": ("Salesforce Classification", "UF Year"),
    "sf_platform_vs_recordtype": ("Platform", "Salesforce Record Type"),
    "sf_division_vs_platform": ("sales_division", "Platform"),
    "op1_salesstage_vs_sfstage": ("Op1 Contracted Data Sales Stage", "Salesforce Opportunity Stage"),
    "op1_workflow_vs_salesstage": ("Op1 Contracted Data Workflow Status", "Op1 Contracted Data Sales Stage"),
    "op1_ssp_by_dealtype": ("Op1 Contracted Data SSP", "Op1 Contracted Data Deal Type"),
}


def build(A):
    wb = new_wb()
    srcs = [("Look 26238 (PIPELINE export, Salesforce)", A["profile_pipe"], A["n_pipe"]),
            ("Look 26239 (DIG_ORDER export, Op1 digital)", A["profile_dig"], A["n_dig"])]
    rows = []
    for name, prof, n in srcs:
        for col, p in prof.items():
            rows.append([name, col, n, p["non_null"], p["null"], p["null_pct"], p["distinct"], ", ".join(f"{k}:{v}" for k, v in (p.get("python_types") or {}).items()), p.get("min"), p.get("max"), p.get("sum"), "yes" if p.get("all_values_listed") else "top values only"])
    write_sheet(wb, "01_Column_Summary", ["export", "column label", "rows", "non-null", "null", "null %", "distinct", "python types", "min", "max", "sum", "all values listed in 02?"], rows, [40, 40, 9, 10, 8, 8, 9, 20, 20, 20, 22, 18],
                title="Every column of both exports (rows exclude the Looker totals row in the pipeline export)",
                note=f"PIPELINE rows = {A['n_pipe']} (raw sheet {A['n_pipe_raw']}, 1 totals row excluded); DIG_ORDER rows = {A['n_dig']}.", freeze_col=2)
    rows = []
    for name, prof, n in srcs:
        for col, p in prof.items():
            for val, cnt in p.get("values", []):
                rows.append([name, col, "(null)" if val is None else val, cnt, round(100.0 * cnt / n, 3)])
    write_sheet(wb, "02_Value_Profiles", ["export", "column label", "value", "count", "% of rows"], rows, [40, 40, 60, 10, 10],
                title=f"Value distribution per column ({len(rows)} rows). For high-cardinality columns only the top values stored by analysis.py appear (see 01 col L).", freeze_col=2)
    # validation: tables vs scalars
    V = A["verify"]
    toc = []
    scal = []
    for k, v in V.items():
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            heads = list(dict.fromkeys(h for x in v for h in x.keys()))
            ren = {}
            if k in AB:
                ren = {"a": AB[k][0], "b": AB[k][1], "n": "rows"}
            sheet = ("V_" + k)[:31]
            write_sheet(wb, sheet, [ren.get(h, h) for h in heads], [[x.get(h) for h in heads] for x in v], [max(14, min(50, len(h) + 4)) for h in heads], title=k, note="Computed by analysis.py from the two export files; see 00_Index.")
            toc.append([k, sheet, len(v), "table"])
        else:
            out = []
            flat("", v, out)
            for p, x in out:
                scal.append([k, p, x])
            toc.append([k, "03_Scalar_Checks", len(out), "key/value"])
    write_sheet(wb, "03_Scalar_Checks", ["check", "path", "value"], scal, [40, 90, 60], title="Scalar / nested validation results", freeze_col=1)
    fl = []
    flat("", A["verify"].get("fl_checks", {}), fl)
    toc.sort(key=lambda r: r[0])
    write_sheet(wb, "00_Index", ["check key", "sheet", "rows", "shape"], toc, [44, 40, 8, 12], title="Index of validation results",
                note="Every number here is recomputed from the two export files on each build. Rule re-implementations (market_type, upfront_year, lifecycle, uf_group, UDF_OP_VERTICAL, Discovery+) follow the text in 'UC1_Fields_for_CARL_working (2).xlsx' / legacy LookML and are named in each check.")
    wb.move_sheet("00_Index", offset=-(len(wb.sheetnames) - 1))
    p = os.path.join(OUT, "UC1_Value_Profiles_and_Validation.xlsx")
    wb.save(p)
    return p
