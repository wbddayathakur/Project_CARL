"""Workbook 1 - master field-to-field mapping."""
import re, json
from collections import OrderedDict
import analysis, knowledge as K
from common import *

MVP_TO_LOOKER = {
    3: (["Salesforce Record Type", "Platform"], []),
    4: (["Market Type"], ["Op1 Contracted Data Market Type"]),
    5: (["Salesforce Deal Type"], ["Op1 Contracted Data Deal Type"]),
    6: (["Salesforce Advertiser Name"], ["Op1 Contracted Data Advertiser"]),
    7: (["Salesforce Agency"], ["Op1 Contracted Data Agency"]),
    8: (["Salesforce Mega Agency"], ["Op1 Contracted Data Mega Agency"]),
    9: ([], ["Op1 Contracted Data Calendar Quarter"]),
    11: (["sales_division"], []),
    13: (["Salesforce Opportunity Stage"], ["Salesforce Opportunity Stage"]),
    14: ([], ["Op1 Contracted Data Sales Stage"]),
    16: (["Salesforce Workflow Status"], ["Op1 Contracted Data Workflow Status"]),
    19: (["Salesforce Classification"], ["Op1 Contracted Data Classification"]),
    20: (["Buyer_AE"], ["Op1 Contracted Data Primary AE"]),
    21: (["Client_AE"], []),
    22: (["Planning_AE"], []),
    24: (["UF Year"], []),
    25: (["Salesforce iDeal ID"], []),
    28: (["Salesforce Opportunity ID"], ["Op1 Contracted Data Opportunity ID"]),
    29: (["Salesforce Opportunity Name"], ["Op1 Contracted Data Order Name"]),
    31: (["Salesforce Activity Quarter"], []),
    34: (["Salesforce Order ID"], []),
    35: (["Salesforce Sales Order ID"], ["Op1 Contracted Data Sales Order ID"]),
    36: (["Salesforce Placeholder Operative Order ID"], []),
    39: ([], ["Op1 Contracted Data Sales Order Start Date"]),
    40: ([], ["Op1 Contracted Data Sales Order End Date"]),
    42: (["UF Year"], []),
    43: (["Status Group"], []),
    44: (["Property Detail"], []),
    45: (["Property"], []),
    46: (["uf_group"], []),
    48: (["Salesforce Projection Rank"], []),
    49: (["Salesforce Ad Type"], []),
    50: (["Salesforce  Historical Snapshot Filter"], []),
    51: ([], ["Op1 Contracted Data Site"]),
    52: ([], ["Op1 Contracted Data Package Name"]),
    53: ([], ["Op1 Contracted Data Product Name"]),
    54: ([], ["Op1 Contracted Data SSP"]),
    55: ([], ["Op1 Contracted Data Net Revenue"]),
    56: ([], ["Op1 Contracted Data Gross Revenue"]),
    57: (["Salesforce Net Projections"], []),
    58: (["Salesforce Net Weighted Projections"], []),
    59: (["Salesforce Linear Total Amount"], []),
    60: (["Salesforce Total Amount"], []),
    61: ([], ["Op1 Contracted Data Contracted Quantity"]),
    62: ([], ["Op1 Contracted Data Contracted Production Quantity"]),
}

GAPS = [
 ("G-01", "Pasted Looker SQL (Salesforce explore, Op1 explore incl. CTEs oper_targeting_count and dt_oper_hbo_targeting) and Slack history are NOT on disk.", "All 'CHAT-ONLY' tags (record-type IDs, Mike's SQL changes, PR numbers, Aishwarya's availability lists, measure formulas) cannot be re-verified.", "Save the two Looker SQLs, Ping's uf_group SQL and the Slack export into uc1-field-mapping/evidence/ and re-run build.py for a verification pass.", "Daya"),
 ("G-02", "Live Looker custom dimensions with no LookML on disk: Platform, uf_group, sales_division, Property, Property Detail, UF Year, Status Group, SF Market Type, Buyer_AE/Client_AE/Planning_AE.", "Only behavioural equivalence is proven (see Validation workbook), not the Looker expressions.", "Export the live LookML for salesforce_reporting (current version) into evidence/.", "Looker owner"),
 ("G-03", "CARL silver/gold column lists for fact_pipeline_sf, fact_digital_op1, fact_linear_working_ms, fact_linear_revenue_ms are not on disk (only chat-quoted partial names and the Northstar silver sample header).", "The 'CARL column' of most rows is 'not found in provided evidence'. No column names were invented.", "Provide DESCRIBE/DDL for the four gold tables and silver.fact_linear_ms_revenue / SF / Op1 silver tables.", "Mike / Aishwarya"),
 ("G-04", "oper_etl_orders_activity_order_status_mappping_V (SF Workflow Status source) definition.", "Workflow Status mapping cannot be reproduced from evidence.", "DDL of the view.", "Looker/Snowflake owner"),
 ("G-05", "PI_SITE_MAPPING, PI_HOLDCO_MAPPING, PI_AGENCY_MAPPING, SF_MEGA_AGENCY table contents; INSIGHT_DIMAGENCY (EMERALDDW_PROD).", "holdco_conformed / Mega Agency cascade not reproducible (Field Logic!D20).", "Table extracts.", "Data steward"),
 ("G-06", "oper_dimdate_v (broadcast calendar) and OPER_PRODUCT_SITE contents.", "Calendar Quarter / Site fallback cannot be reproduced.", "Table extracts.", "Data Engineering"),
 ("G-07", "Legacy repo is an older snapshot (no date in the zip).", "Live fields renamed since (e.g. BROADWAY_IO_ID_C -> IDEAL_DEAL_ID; agency fields; record_type) are known only from the secondary workbook.", "Confirm snapshot date or provide the current repo.", "Daya"),
 ("G-08", "Both Look exports are label-keyed samples at the Look's own grain (not row-level source tables).", "Raw inputs (sports_property, forecast_category, network, payment_type, ad_type for Op1, etc.) are not in the exports, so some Field Logic columns are 'NOT RE-DERIVABLE'.", "Export the sample_sf / sample_op1 raw inputs at the same grain.", "Daya"),
 ("G-09", "MVP lists fields as green for fact_digital_op1 (sales_division, UF Year, business_source) that Look 26239 does not contain.", "MVP parity cannot be tested for these on the Looker side.", "Confirm whether Jason's Op1 look should include them.", "Jason"),
 ("G-10", "Northstar sample has Excel date-formatted integers (calendar_year -> 1905-07-18, calendar_qtr_num -> 1900-01-01).", "Sample file defect, not necessarily a silver defect.", "Re-export the sample with numeric formats.", "Daya"),
]


def merge_fl(rows):
    out = []
    for r in rows:
        if r["column"] is None and out and out[-1]["system"] == r["system"]:
            out[-1]["sql"] = ((out[-1]["sql"] or "") + "\n" + (r["sql"] or "")).strip()
            out[-1]["row_end"] = r["row"]
        else:
            r = dict(r)
            r["row_end"] = r["row"]
            out.append(r)
    return out


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def build(A):
    wb = new_wb()
    P, D = A["profile_pipe"], A["profile_dig"]
    sf_by = {f["label"]: f for f in K.SF_FIELDS}
    op_by = {f["label"]: f for f in K.OP1_FIELDS}
    V = A["verify"]

    # ---- 00 README
    rows = [
        ["Purpose", "Field-to-field mapping between the Looker reports (source of truth per Jason: Look 26238 Pipeline/Salesforce, Look 26239 Digital/Op1, Linear QuickMSTR) and the CARL silver/gold tables, for UC1 Ad Sales Reporting Acceleration."],
        ["Scope", "Sheets 'MVP Fields' and 'Field Logic' of UC1_Fields_for_CARL_working (2).xlsx, cross-checked against the two Looker exports, the legacy LookML/ETL repo and prior analysis workbooks."],
        ["No-assumption rule", "Every cell carries an evidence tag (see below). Where no evidence exists the cell says 'not found in provided evidence'. No CARL column name was invented."],
        ["Headline - Salesforce (Look 26238)", f"{A['n_pipe']:,} data rows (+1 Looker grand-total row excluded), 33 labels. Field Logic reproduces Market Type, UF Year and Status Group on 23,756/23,756 rows. uf_group, Platform, Property Detail differ in the places listed in 06_Mismatches_Decisions."],
        ["Headline - Op1 (Look 26239)", f"{A['n_dig']:,} rows, 24 labels. Looker's native Market Type disagrees with the Classification-derived rule on {V['op1_marketype_summary']['disagree']:,} of {V['op1_marketype_summary']['comparable_rows (rule returns Upfront or Scatter)']:,} comparable rows (${V['op1_marketype_summary']['net_revenue_disagree_usd']/1e6:,.1f}M of ${V['op1_marketype_summary']['net_revenue_total_usd']/1e6:,.1f}M net revenue)."],
        ["Headline - MVP vs exports", "MVP marks sales_division, UF Year and business_source green for fact_digital_op1, but Look 26239 contains none of them. MVP marks Op1 Workflow Status red and SF Client/Planning AE red, yet both exports contain populated columns."],
        ["CARL column coverage", "Only the Linear Northstar silver sample (71 columns) gives real silver column names. For SF and Op1 the CARL columns are 'not found in provided evidence' except chat-quoted names (CHAT-ONLY)."],
        ["Companion files", "UC1_Custom_Fields_Catalog.xlsx, UC1_Salesforce_Lineage.xlsx, UC1_Op1_Lineage.xlsx, UC1_Value_Profiles_and_Validation.xlsx and the .md documents in out/."],
    ]
    write_sheet(wb, "00_README", ["Item", "Detail"], rows, [34, 150], title="UC1 Looker -> CARL field-to-field mapping (master)")
    ws = wb["00_README"]
    r = ws.max_row + 2
    ws.cell(r, 1, "Evidence status legend").font = Font(bold=True)
    for k, v in K.STATUS.items():
        r += 1
        ws.cell(r, 1, k).fill = status_fill(k) or PatternFill()
        ws.cell(r, 2, v).alignment = Alignment(wrap_text=True)

    # ---- 01 MVP crosswalk
    hdr = ["MVP row", "Note (col A)", "Description (col F)"]
    for t in ("Linear Pending (fact_linear_working_ms)", "Linear Booked (fact_linear_revenue_ms)", "Pipeline (fact_pipeline_sf, Look 26238)", "Digital (fact_digital_op1, Look 26239)"):
        hdr += [t + " - label", "fill", "cell comment"]
    hdr += ["Looker SF export label(s)", "Looker Op1 export label(s)", "Linear Northstar silver columns", "Linear evidence", "Export gap flag", "Decision ref(s)"]
    lin = {m[0]: m for m in K.LINEAR_MAP}
    rows = []
    for m in A["mvp"]:
        rr = m["row"]
        if rr < 3 or rr > 62:
            continue
        sf, op = MVP_TO_LOOKER.get(rr, ([], []))
        flags = []

        def real(v):
            return v and str(v).strip() not in (".", "") and not str(v).strip().startswith("null?")
        if real(m["pipeline_sf"]) and m["pipeline_sf_fill"] == "GREEN" and not sf:
            flags.append("Pipeline GREEN in MVP but no matching column in Look 26238")
        if real(m["digital_op1"]) and m["digital_op1_fill"] == "GREEN" and not op:
            flags.append("Op1 GREEN in MVP but no matching column in Look 26239")
        if m["digital_op1_fill"] == "RED" and op:
            flags.append("Op1 RED in MVP but column IS in Look 26239")
        if m["pipeline_sf_fill"] == "RED" and sf:
            flags.append("Pipeline RED in MVP but column IS in Look 26238")
        for lab in sf:
            if lab in ("Salesforce Classification", "Salesforce Ad Type", "Property Detail", "Salesforce Projection Rank") and m["pipeline_sf_fill"] == "none":
                flags.append(f"'{lab}' has no fill (not in MVP) but is an input to other MVP fields")
        decs = sorted(set(sum([[d for d in (sf_by[l]["decision"] or "").split(",") if d] for l in sf if l in sf_by], []) + sum([[d for d in (op_by[l]["decision"] or "").split(",") if d] for l in op if l in op_by], [])))
        lm = lin.get(rr)
        row = [rr, m["note"], m["description"]]
        for t in ("linear_working", "linear_revenue", "pipeline_sf", "digital_op1"):
            row += [m[t], m[t + "_fill"], m[t + "_comment"]]
        row += ["; ".join(sf), "; ".join(op), ", ".join(lm[2]) if lm else "", (lm[3] + ": " + lm[4]) if lm else "", " | ".join(flags), ", ".join(decs)]
        rows.append(row)
    write_sheet(wb, "01_MVP_Crosswalk", hdr, rows, [7, 14, 28] + [26, 9, 24] * 4 + [34, 34, 30, 40, 40, 14], status_cols=(), title="MVP Fields crosswalk (rows 3-62) - every MVP row to Looker labels and CARL columns",
                note="Fills decoded from the workbook: GREEN = in MVP / done, YELLOW = 'null?' open, RED = not available, none = not on MVP list. Linear columns map to Northstar silver names ONLY by name (NAME-MATCH). Decision refs point to 06_Mismatches_Decisions.", freeze_col=3)

    # ---- 02 SF fields
    hdr = ["#", "Looker export label (Look 26238)", "MVP row", "Looker field kind", "Looker logic / definition (evidenced)", "Legacy source citation(s)", "Legacy SQL / expression text (auto-extracted)", "Live vs legacy / notes", "Field Logic column", "In sample_sf RAW", "CARL silver/gold column", "Observed in export (auto-profile)", "Evidence status", "Decision"]
    rows = []
    for i, f in enumerate(K.SF_FIELDS, 1):
        cites, sqls = [], []
        for ref in f["legacy"]:
            c, s = resolve(ref)
            cites.append(c)
            sqls.append(s)
        rows.append([i, f["label"], f["mvp"], f["kind"], f["logic"], "\n".join(cites) or "none (no legacy equivalent)", "\n---\n".join(x for x in sqls if x), f["live_vs_legacy"], f["fl_col"], f["sample_sf_raw"], f["carl"], profile_summary(P.get(f["label"])), f["status"], f["decision"]])
    write_sheet(wb, "02_SF_Pipeline_Fields", hdr, rows, [4, 30, 16, 20, 70, 60, 70, 55, 28, 14, 34, 55, 24, 9], status_cols=(12,), title="Salesforce / Pipeline - all 33 Looker labels in Look 26238", freeze_col=2)

    # ---- 03 Op1 fields
    hdr = ["#", "Looker export label (Look 26239)", "MVP row", "Looker field kind", "Looker logic / definition (evidenced)", "Legacy source citation(s)", "Legacy SQL / expression text (auto-extracted)", "Live vs legacy / notes", "Field Logic column", "In sample_op1 RAW", "CARL silver/gold column", "Observed in export (auto-profile)", "Evidence status", "Decision"]
    rows = []
    for i, f in enumerate(K.OP1_FIELDS, 1):
        cites, sqls = [], []
        for ref in f["legacy"]:
            c, s = resolve(ref)
            cites.append(c)
            sqls.append(s)
        lab = f["label"] if f["label"] in D else f["label"]
        rows.append([i, f["label"], f["mvp"], f["kind"], f["logic"], "\n".join(cites) or "none", "\n---\n".join(x for x in sqls if x), f["live_vs_legacy"], f["fl_col"], f["sample_op1_raw"], f["carl"], profile_summary(D.get(lab)), f["status"], f["decision"]])
    write_sheet(wb, "03_Op1_Digital_Fields", hdr, rows, [4, 34, 16, 22, 70, 60, 70, 55, 28, 14, 34, 55, 24, 9], status_cols=(12,), title="Op1 / Digital - all 24 Looker labels in Look 26239",
                note="The export prefix 'Op1 Contracted Data' is the explore's view_label (legacy model eg_order_management.model.lkml:10-11), so it is not part of the field name.", freeze_col=2)

    # ---- 04 Linear
    hdr = ["MVP row", "MVP label (Linear)", "Pending fill", "Booked fill", "Northstar silver column(s) (name-match)", "Sample value(s) in Northstar row (deal 645737)", "Evidence", "Note"]
    ns = A["northstar"]
    mvp_by = {m["row"]: m for m in A["mvp"]}
    rows = []
    for rr, lab, cols, ev, note in K.LINEAR_MAP:
        m = mvp_by[rr]
        vals = "; ".join(f"{c}={ns['sample_row'].get(c)!r}" for c in cols if c in ns["sample_row"])
        rows.append([rr, lab, m["linear_working_fill"], m["linear_revenue_fill"], ", ".join(cols) or "NOT FOUND in Northstar header", vals, ev, note])
    write_sheet(wb, "04_Linear_QuickMSTR", hdr, rows, [8, 34, 10, 10, 40, 60, 18, 90], status_cols=(6,), title="Linear (QuickMSTR) - MVP rows mapped to silver.fact_linear_ms_revenue (Northstar sample)",
                note="There is NO Looker export for Linear in the evidence. The only CARL-side evidence is the 'iDeal Northstar Revenue sample' tab (silver.fact_linear_ms_revenue sample, one deal 645737, 202 rows, 71 columns). Mapping is therefore by NAME only (NAME-MATCH), plus Field Logic rows 47-160 which describe the iDeal/MicroStrategy side.")
    used = {}
    for rr, lab, cols, ev, note in K.LINEAR_MAP:
        for c in cols:
            used.setdefault(c, []).append(rr)
    ideal_rows = [r for r in A["field_logic"] if r["system"] == "iDeal" and r["column"]]
    rows = []
    for i, c in enumerate(ns["header"], 1):
        n = norm(c)
        fl = [f"row {r['row']} {r['column']}" for r in ideal_rows if norm(r["column"]) == n]
        cand = [f"row {r['row']} {r['column']}" for r in ideal_rows if norm(r["column"]) != n and len(n) >= 5 and (n in norm(r["column"]) or norm(r["column"]) in n) and len(norm(r["column"])) >= 5]
        rows.append([i, c, repr(ns["sample_row"].get(c)), ", ".join(map(str, used.get(c, []))) or "not referenced by an MVP row", "; ".join(fl) or "", "; ".join(cand) or ""])
    write_sheet(wb, "04b_Northstar_Columns", ["#", "silver column (sample header)", "sample value", "MVP row(s) mapped here", "Field Logic iDeal row (exact name match)", "Field Logic iDeal row (partial name match)"], rows, [4, 32, 40, 24, 50, 50], title="All 71 columns of the Northstar silver sample")

    # ---- 05 Field Logic register
    fl_all = merge_fl(A["field_logic"])
    ns_norm = {norm(c): c for c in ns["header"]}
    rows = []
    for r in fl_all:
        cmpv = K.FL_COMPARE.get(r["row"])
        if cmpv:
            comp, st = cmpv
        elif r["system"] == "iDeal":
            n = norm(r["column"] or "")
            hit = ns_norm.get(n)
            if hit:
                comp, st = f"Exact name match in Northstar silver sample: {hit} (sample value {ns['sample_row'].get(hit)!r}).", "NAME-MATCH"
            elif r["column"]:
                part = [c for k2, c in ns_norm.items() if len(k2) >= 5 and len(n) >= 5 and (k2 in n or n in k2)]
                comp, st = ("No exact Northstar column. Partial name candidates: " + ", ".join(part) if part else "No Northstar silver column with this name."), ("NAME-MATCH (partial)" if part else "NOT FOUND")
            else:
                comp, st = "Continuation of the previous row.", ""
        else:
            comp, st = "", ""
        rows.append([f"{r['row']}" + (f"-{r['row_end']}" if r["row_end"] != r["row"] else ""), r["system"], r["column"], r["build_order"], r["sql"], r["in_words"], r["notes"], comp, st])
    write_sheet(wb, "05_FieldLogic_Register", ["Sheet row(s)", "System", "Column", "Build order (col C)", "SQL / rule (col D)", "In words (col E)", "Notes (col F)", "Looker / legacy / data comparison", "Status"], rows, [9, 11, 28, 22, 70, 36, 60, 80, 22], status_cols=(8,),
                title="Field Logic sheet - every row (5-160) compared with Looker, legacy and export evidence",
                note="Rows 5-45 are the Salesforce and Op1 'BUILT' columns; rows 47-160 are the iDeal/MicroStrategy field list. Comparisons for rows 5-45 are computed from the exports by analysis.py; iDeal rows are compared by NAME against the Northstar silver sample only. Quoted row counts in the Field Logic notes come from a different sample than the 2026-10-16 exports.", freeze_col=3)

    # ---- 06 Mismatches / decisions
    rows = [list(d) for d in K.DECISIONS]
    write_sheet(wb, "06_Mismatches_Decisions", ["ID", "Topic", "Finding (evidence)", "Options for Jason", "Why it matters", "Evidence"], rows, [7, 30, 110, 60, 40, 24], status_cols=(5,), title="Looker vs CARL differences needing a decision (Looker = source of truth)")
    t = V["sf_fieldlogic_tests"]
    rows = []
    for k, v in t.items():
        rows.append([k, json.dumps(v, default=str)[:30000]])
    write_sheet(wb, "06b_uf_group_tests", ["Test", "Result (computed from export)"], rows, [90, 160], title="Computed tests behind D-05/D-06/D-07 (re-run analysis.py to refresh)")

    # ---- 07 gaps
    write_sheet(wb, "07_Gaps_NotFound", ["ID", "Gap", "Impact on mapping", "Needed to close", "Owner"], [list(g) for g in GAPS], [7, 80, 70, 70, 20], title="What is NOT in the evidence (nothing here was guessed)")

    # ---- 08 evidence
    write_sheet(wb, "08_Evidence_Index", ["ID", "Artifact", "Location", "What it provides", "Availability"], [list(e) for e in K.EVIDENCE], [6, 60, 36, 100, 24], title="Evidence index")

    p = os.path.join(OUT, "UC1_Field_to_Field_Mapping_Master.xlsx")
    wb.save(p)
    return p
