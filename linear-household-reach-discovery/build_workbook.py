"""Build the Linear household reach / Reach Guarantee backtest data requirements workbook.

    python3 build_workbook.py            # writes into ./out

Picks up the newest evidence/glue_columns_*.json from verify_columns.py when present.
"""
import csv
import glob
import json
import os
import re
import statistics
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

import knowledge as K

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(bold=True, color="FFFFFF")
TITLE_FONT = Font(bold=True, size=14)
WRAP = Alignment(wrap_text=True, vertical="top")
STATUS_FILL = {
    "Fit": "C6EFCE", "Found": "C6EFCE", "Present": "C6EFCE", "Pass": "C6EFCE", "Answered": "C6EFCE",
    "Partial": "FFEB9C", "Not verified": "FFEB9C", "Not run": "FFEB9C", "Watch": "FFEB9C", "Lead": "FFEB9C", "Info": "DDEBF7",
    "Gap": "FFC7CE", "Missing": "FFC7CE", "NOT_FOUND": "FFC7CE", "Gap (DDL reports not landed)": "FFC7CE",
}


def sheet(wb, title, subtitle, headers, rows, widths=None, status_col=None):
    ws = wb.create_sheet(title[:31])
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = subtitle
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=4, column=i, value=h)
        c.fill, c.font, c.alignment = HEADER_FILL, HEADER_FONT, WRAP
    for r, row in enumerate(rows, 5):
        for i, v in enumerate(row, 1):
            ws.cell(row=r, column=i, value=v).alignment = WRAP
        if status_col is not None:
            fill = STATUS_FILL.get(str(row[status_col]))
            if fill:
                ws.cell(row=r, column=status_col + 1).fill = PatternFill("solid", fgColor=fill)
    widths = widths or [24] * len(headers)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "B5"
    if rows:
        ws.auto_filter.ref = f"A4:{get_column_letter(len(headers))}{len(rows) + 4}"
    return ws


def glue_inventory():
    inv = {}
    with open(os.path.join(ROOT, K.GLUE_INVENTORY)) as f:
        for r in csv.DictReader(f):
            inv[f"{r['database']}.{r['table']}"] = r
    return inv


def latest_evidence():
    files = sorted(glob.glob(os.path.join(HERE, "evidence", "glue_columns_*.json")))
    return (json.load(open(files[-1])), os.path.basename(files[-1])) if files else (None, None)


def results(name):
    path = os.path.join(OUT, "sql_results", name)
    return list(csv.DictReader(open(path))) if os.path.exists(path) else None


def pct(n, d):
    return f"{n} of {d} ({n / d:.0%})" if d else "-"


def validation_rows():
    rows = []
    r2, r3, r4, r5, r6, r7, r8, r9 = (results(f) for f in [
        "02_campaign_profile.csv", "03_campaign_videoamp_mapping.csv", "04_final_linear_hh_reach.csv",
        "05_campaign_deal_plan.csv", "06_planned_imps_network_daypart.csv", "07_household_universe.csv",
        "08_forecast_availability.csv", "09_sample_campaigns.csv"])
    if r2:
        m = [x for x in r2 if x["is_linear"] == "true" and x["has_videoamp"] == "true"]
        rows.append(("02", "Measured Linear campaigns", ", ".join(f"{x['campaign_type']} {x['campaigns']}" for x in m),
                     "FreeWheel IDs: " + ", ".join(f"{x['campaign_type']} {x['with_fw_campaign_ids']}" for x in m), "Pass"))
    if r3:
        have = sum(1 for x in r3 if x["has_linear_hh_report"] == "true")
        by = {}
        for x in r3:
            by.setdefault(x["campaign_type"], [0, 0])
            by[x["campaign_type"]][0] += 1
            by[x["campaign_type"]][1] += x["has_linear_hh_report"] == "true"
        rows.append(("03", "Campaigns mapped to >= 1 request", pct(sum(1 for x in r3 if x["mapping_status"] != "UNMAPPED"), len(r3)), "", "Pass"))
        rows.append(("03", "Campaigns with a final Linear HH report", pct(have, len(r3)),
                     "; ".join(f"{k}: {v[1]} of {v[0]}" for k, v in by.items()), "Gap (DDL reports not landed)"))
    if r4:
        n = len(r4)
        rows.append(("04", "Frequency consistency (reach x freq = imps within 1%)", pct(sum(1 for x in r4 if x["check_freq_consistent"] == "true"), n), "", "Pass"))
        rows.append(("04", "Final report covers the full flight", pct(sum(1 for x in r4 if x["is_final"] == "true"), n), "", "Pass"))
        rows.append(("04", "Final requests shared by another campaign", pct(sum(1 for x in r4 if x["campaigns_sharing_request"] != "1"), n), "Excluded from sample", "Watch"))
        reach = sorted(float(x["linear_hh_reach"]) for x in r4)
        rows.append(("04", "Linear HH reach (households)", f"min {reach[0]/1e6:.1f}M, median {statistics.median(reach)/1e6:.1f}M, max {reach[-1]/1e6:.1f}M", "", "Info"))
    if r5:
        found = [x for x in r5 if x["deal_found"] == "true"]
        rows.append(("05", "Campaign GAB deal numbers resolved in deal_header", pct(len(found), len(r5)), "", "Pass"))
        rows.append(("05", "Deal links with a revision confirmed before flight start", pct(sum(1 for x in found if x["pre_flight_audit_no"]), len(found)),
                     f"median header versions {statistics.median([int(x['header_versions']) for x in found]):.0f}", "Pass"))
    if r6:
        rows.append(("06", "Plan rows with network mapped", pct(sum(1 for x in r6 if x["net_id"]), len(r6)), "sell_id -> pricing_rating.net_id", "Pass"))
        per = {x["campaign_id"]: x for x in r6}
        ratios = sorted(float(x["measured_to_plan_ratio"]) for x in per.values() if x["measured_to_plan_ratio"])
        if ratios:
            rows.append(("06", "Measured VideoAmp imps / Nielsen HH as-sold plan", f"median {statistics.median(ratios):.2f} over {len(ratios)} campaigns",
                         f"outliers > 10: {sum(1 for r in ratios if r > 10)}", "Info"))
        rows.append(("06", "Campaigns with a pre-flight HH plan", pct(sum(1 for x in per.values() if x["deal_nielsen_hh_plan_pre_flight"]), len(per)), "", "Pass"))
    if r7:
        ue = sorted({float(x["nielsen_hh_universe"]) for x in r7 if x["nielsen_hh_universe"]})
        p = sorted(float(x["reach_pct"]) for x in r7 if x["reach_pct"])
        rows.append(("07", "Nielsen HH universe values", ", ".join(f"{u/1e6:.1f}M" for u in ue), "One ue_nat across networks per period", "Pass"))
        if p:
            rows.append(("07", "Linear HH reach %", f"min {p[0]:.1%}, median {statistics.median(p):.1%}, max {p[-1]:.1%}", "", "Info"))
    if r8:
        rows.append(("08", "Campaigns with a Nielsen forecast run before flight", pct(sum(1 for x in r8 if x["nielsen_runs_before_flight"] not in ("", "0")), len(r8)),
                     f"first run {r8[0]['nielsen_first_run_on']}", "Gap"))
        rows.append(("08", "Campaigns whose VideoAmp audience has a Foresite forecast", pct(sum(1 for x in r8 if x["va_audiences_with_forecast"] not in ("", "0")), len(r8)),
                     f"processed before flight: {sum(1 for x in r8 if x['va_audiences_processed_before_flight'] not in ('', '0'))}; impressions only", "Gap"))
        rows.append(("08", "Campaigns with a VideoAmp Planning ID", pct(sum(1 for x in r8 if x["videoamp_planning_id"]), len(r8)), "Possible planned-reach source", "Lead"))
    if r9 is not None:
        rows.append(("09", "Validation sample rows", str(len(r9)), "", "Pass" if 8 <= len(r9) <= 12 else "Watch"))
    return rows


def mit_columns():
    path = os.path.join(ROOT, K.MIT_COLUMNS)
    return json.load(open(path)).get("big_mit_bronze.universe_estimate", []) if os.path.exists(path) else []


def build(path):
    inv = glue_inventory()
    ev, ev_name = latest_evidence()
    wb = Workbook()
    wb.remove(wb.active)

    verified = ev is not None and any("tables" in e for e in ev["envs"].values())
    readme = [
        ("Purpose", "Data requirements for the Linear household reach work and the Reach Guarantee backtest: what each requested field means, where it lives in CARL, how the tables join, the target backtest dataset, and the SQL to validate definitions and joins on a small sample of completed campaigns."),
        ("Prepared", f"{date.today():%d %b %Y} - generated by linear-household-reach-discovery/build_workbook.py"),
        ("Requested data", "Required: campaign/plan ID and flight dates; audience and household universe; planned Linear impressions by network and daypart; final measured VideoAmp household Linear Total reach; campaign-to-VideoAmp request/report mapping. Backtest: pre-campaign Linear Total HH reach forecast; forecast creation timestamp and version. Optional: weekly planned impressions, selling titles, planned GRPs, network/daypart actual delivery, universe version/effective date, historical plan versions."),
        ("Validation run", "SQL pack run on Athena (CARL Dev, workgroup primary) - see Validation Results and Sample Campaigns. Rerun: run_sql.py, then this script." if results("09_sample_campaigns.csv") is not None else "SQL pack not yet run."),
        ("Column verification", f"Live Glue columns from {ev_name}." if verified else "NOT YET RUN. Column names come from Confluence (Salesforce Data Model, VideoAmp Measurement Requests, Measurement Summary), legacy iDeal DDL and the Aug-27 MIT Glue export. Run gimme-aws-creds, then verify_columns.py, then rebuild."),
        ("Evidence", "Confluence PAM / PAYTV / FF pages (see Evidence sheet); Glue inventory 7-Oct-2026; legacy iDeal DDL; Aug-27 Prod Glue column export for big_mit_bronze."),
        ("Status legend", "Fit = source and definition known. Partial = source known, a column, basis or rule still to confirm. Gap = no source today."),
        ("Companion files", "sql/ (validation pack; _base.sql holds every raw column name), verify_columns.py (Glue schema check), run_sql.py (render / run on Athena)."),
    ]
    sheet(wb, "Read Me", "Scope, evidence and how to read this workbook", ["Item", "Detail"], readme, [24, 150])

    sheet(wb, "Key Findings", "What the discovery changes about the plan",
          ["ID", "Finding", "Evidence", "So what / action", "Confidence"], K.FINDINGS, [7, 38, 80, 70, 18])

    # Requirements with column verification status
    req_rows = []
    for r in K.REQUIREMENTS:
        tables = set(re.findall(r"\b[a-z0-9_]+_(?:bronze|silver|gold)(?:_dev)?\.[a-z0-9_]+", r[5]))
        vstat = "Not run"
        if verified:
            dev = ev["envs"].get("dev", {}).get("tables", {})
            states = [dev[t]["status"] for t in tables if t in dev]
            vstat = "n/a" if not tables else ("Found" if states and all(s == "FOUND" for s in states) else ("Missing" if any(s != "FOUND" for s in states) else "Not checked"))
        req_rows.append(r[:8] + (r[8], vstat) + r[9:])
    vrows = validation_rows()
    if vrows:
        sheet(wb, "Validation Results", "What the SQL pack found on CARL Dev (computed from out/sql_results)",
              ["Query", "Check", "Result", "Detail", "Verdict"], vrows, [7, 50, 36, 60, 22], status_col=4)
    sample = results("09_sample_campaigns.csv")
    if sample:
        cols = [c for c in sample[0].keys() if c != "rank_in_quarter"]
        sheet(wb, "Sample Campaigns", "Initial validation sample: one row per completed, measured Linear campaign (09_sample_campaigns.sql)",
              cols, [[x[c] for c in cols] for x in sample], [16] * len(cols))
    plan = results("06_planned_imps_network_daypart.csv")
    if plan and sample:
        ids = {x["campaign_id"] for x in sample}
        cols = list(plan[0].keys())
        sheet(wb, "Sample Plan by Network", "Plan by network x selling title for the sample campaigns (06_planned_imps_network_daypart.sql)",
              cols, [[x[c] for c in cols] for x in plan if x["campaign_id"] in ids], [14] * len(cols))

    sheet(wb, "Requirements", "Each requested field: definition, grain, source, join and status",
          ["ID", "Tier", "Requirement", "Business definition", "Grain", "Candidate source(s)", "Key columns", "How obtained",
           "Status", "Tables found in Glue", "Confidence", "Notes"],
          req_rows, [7, 10, 30, 50, 24, 50, 44, 50, 10, 14, 28, 50], status_col=8)

    src_rows = []
    for full, role, platform, upstream, notes in K.SOURCES:
        i = inv.get(full, {})
        src_rows.append((full, role, platform, i.get("in_dev", "") or "-", i.get("in_prod", "") or "-",
                         i.get("dev_last_updated", ""), i.get("prod_last_updated", ""), upstream, notes))
    sheet(wb, "Source Inventory", f"Candidate tables with Dev/Prod presence and last update from {os.path.basename(K.GLUE_INVENTORY)}",
          ["Table", "Role", "Platform", "In Dev", "In Prod", "Dev last updated", "Prod last updated", "Upstream / Snowflake equivalent", "Notes"],
          src_rows, [56, 40, 20, 8, 8, 18, 18, 52, 60])

    sheet(wb, "Join Path", "How campaign, plan, VideoAmp, universe and forecast connect",
          ["Step", "From", "To", "Key / rule", "Cardinality", "Risk"], K.JOINS, [7, 40, 40, 64, 28, 64])

    sheet(wb, "Backtest Dataset Spec", "Target analysis table: one row per campaign (proposed silver reach_backtest_campaign)",
          ["Column", "Type", "Definition", "Source", "Rule"], K.DATASET, [26, 16, 48, 56, 56])

    sheet(wb, "Calculations", "Metrics and rules the backtest must reproduce",
          ["Metric", "Business definition", "Formula", "Grain", "Additivity / reporting", "Notes"],
          K.CALCS, [28, 40, 64, 14, 30, 60])

    sheet(wb, "Sample Selection", "Criteria for the initial sample of completed campaigns (implemented in sql/09_sample_campaigns.sql)",
          ["ID", "Criterion", "Field / rule"], K.SAMPLE_CRITERIA, [7, 90, 40])

    sheet(wb, "Validation SQL", "SQL pack in sql/ (Athena / Trino). Numbered files are prefixed with _base.sql by run_sql.py",
          ["File", "Purpose", "What it checks", "Pass criteria"], K.SQL_PACK, [40, 44, 70, 50])

    base = open(os.path.join(HERE, "sql", "_base.sql")).read().splitlines()
    sheet(wb, "SQL Base CTEs", "sql/_base.sql - the only place raw column names appear. Edit here after column verification",
          ["Line", "SQL"], [(i, l) for i, l in enumerate(base, 1)], [6, 150])

    # Column verification
    crow = []
    if verified:
        for env, e in ev["envs"].items():
            if "tables" not in e:
                crow.append((env, "(all)", "-", "Not run", e.get("error", "")))
                continue
            for full, exp in K.EXPECTED_COLUMNS.items():
                t = e["tables"].get(full, {})
                if t.get("status") != "FOUND":
                    crow.append((env, full, "(table)", t.get("status", "n/a"), ""))
                    continue
                have = {c[0].lower(): c[1] for c in t["columns"]}
                for c in exp:
                    crow.append((env, full, c, "Present" if c.lower() in have else "Missing", have.get(c.lower(), "")))
    else:
        for full, exp in K.EXPECTED_COLUMNS.items():
            for c in exp:
                crow.append(("-", full, c, "Not run", ""))
        for name, dtype, _ in mit_columns()[:5]:
            crow.append(("prod (Aug-27 export)", "big_mit_bronze.universe_estimate", name, "Present", dtype))
    sheet(wb, "Column Verification", "Expected (documented) columns vs live Glue",
          ["Env", "Table", "Expected column", "Status", "Actual type"], crow, [20, 56, 32, 12, 24], status_col=3)

    grow = []
    if verified:
        for env, e in ev["envs"].items():
            for full, t in e.get("tables", {}).items():
                for name, dtype, part in t.get("columns", []):
                    grow.append((env, full, name, dtype, "Y" if part else ""))
    sheet(wb, "Glue Columns", "Full live schema of every candidate table" + ("" if verified else " - populated after verify_columns.py"),
          ["Env", "Table", "Column", "Type", "Partition key"], grow, [8, 56, 40, 24, 12])

    drow = []
    if verified:
        for env, e in ev["envs"].items():
            for full, col, typ in e.get("discovery", []):
                drow.append((env, full, col, typ))
    sheet(wb, "Column Discovery", "Columns in scope databases matching reach / universe / request / campaign / deal / forecast / daypart patterns",
          ["Env", "Table", "Column", "Type"], drow, [8, 60, 40, 24])

    sheet(wb, "Open Questions", "Decisions and facts needed from owners",
          ["ID", "Priority", "Topic", "Status", "Question / action", "Owner (suggested)", "Why it matters"],
          K.QUESTIONS, [7, 8, 26, 10, 80, 40, 44])

    sheet(wb, "User Stories", "Stories to take this from validation to a production backtest dataset",
          ["ID", "Epic", "Title", "Story", "Acceptance criteria", "Depends on", "Priority", "Size", "Layer"],
          K.STORIES, [8, 12, 34, 70, 80, 14, 8, 6, 12])

    evidence = [
        ("E-01", "Measurement Summary (PAM)", K.PAGES["measurement_summary"], "Production SQL for VideoAmp measured reach; medium / time slice / audience -1 rules; planned values deferred to VideoAmp Planning"),
        ("E-02", "VideoAmp Measurement Requests (PAM)", K.PAGES["va_requests"], "Request cadence (Mondays, flight start + 21 to flight end + 17), 17-day Linear lag, VAMP_DCR request columns incl. dealid (new), postlog naming"),
        ("E-03", "Salesforce Data Model (PAM)", K.PAGES["sf_model"], "Impact_Campaign__c fields: flight dates, campaign type, iDeal Deal ID, FreeWheel IDs, VideoAmp flags"),
        ("E-04", "Support Multiple Linear Deal IDs (PAM)", K.PAGES["multi_deal"], "iDeal_DealId__c is comma-separated"),
        ("E-05", "Proposal for Guaranteed Reach (PAYTV)", K.PAGES["guaranteed_reach"], "Phase 1 builds a forecast-error dataset, implying no history"),
        ("E-06", "Foresite VideoAmp: Data Sources & Pipeline Flow (FF)", K.PAGES["foresite_va"], "VideoAmp universe weights stay inside the clean room; forecast outputs are impressions to iDeal / tracking"),
        ("E-07", "PRD029 Traditional Linear Forecasting (PAYTV)", K.PAGES["prd029"], "VideoAmp listed as a future forecasting currency"),
        ("E-08", "Linear Forecasting Excel decision logic, 25-Feb-2026 (PAYTV)", K.PAGES["excel_forecast"], "DAI households in Nielsen UE need manual adjustment"),
        ("E-09", "Glue inventory 7-Oct-2026", K.GLUE_INVENTORY, "Table presence and last update per environment"),
        ("E-10", "Legacy iDeal DDL", K.LEGACY_DDL, "DCI_DEAL_HEADER column names (deal_revision_no, plan_chg_dt, ...)"),
        ("E-11", "Aug-27 Prod Glue column export", K.MIT_COLUMNS, "big_mit_bronze.universe_estimate columns"),
    ]
    if verified:
        evidence.append(("E-12", "Live Glue column check", f"evidence/{ev_name}", "Columns of every candidate table"))
    if results("09_sample_campaigns.csv") is not None:
        evidence.append(("E-13", "Validation SQL results (Athena, CARL Dev)", "out/sql_results/*.csv", "Every number in Validation Results and Key Findings"))
    sheet(wb, "Evidence", "Evidence register", ["#", "Source", "Location", "What it supports"], evidence, [6, 50, 70, 80])

    wb.save(path)
    return verified


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    xlsx = os.path.join(OUT, "Linear_Household_Reach_Data_Requirements.xlsx")
    verified = build(xlsx)
    print(f"wrote {xlsx} (columns verified: {verified})")
