"""Workbook 2 - custom fields catalog (Op1 order / line / product custom fields, SF custom fields, targeting, live Looker custom dims, reference lists)."""
import re, json, glob, os
from collections import OrderedDict, defaultdict
import knowledge as K
from common import *

V = "looker-inventory-analytics/views/"
CF_ORDER = V + "base.oper_sales_order_custom_field_t.view.lkml"
CF_LINE = V + "base.oper_sales_order_line_item_custom_field_t.view.lkml"
CF_PROD = V + "base.oper_product_custom_field_t.view.lkml"
TGT = V + "base.dt_oper_hbo_targeting.view.lkml"

ID_RX = re.compile(r"custom_field_id\}?\s*(?:IN\s*\(([^)]*)\)|=\s*'?(\d+)'?)", re.I)
NM_RX = re.compile(r"custom_field_name\}?\s*(?:=\s*'([^']*)'|IN\s*\(([^)]*)\)|(?:NOT\s+)?LIKE\s*'([^']*)')", re.I)


def ids_names(sql):
    ids, names = [], []
    for m in ID_RX.finditer(sql or ""):
        ids += [x.strip().strip("'") for x in (m.group(1) or m.group(2)).split(",") if x.strip()]
    for m in NM_RX.finditer(sql or ""):
        if m.group(1):
            names.append(m.group(1))
        elif m.group(2):
            names += [x.strip().strip("'") for x in m.group(2).split(",")]
        elif m.group(3):
            names.append("LIKE '" + m.group(3) + "'")
    src = re.findall(r"source\}?\s*=\s*'(\w+)'", sql or "")
    return ids, names, sorted(set(src))


def view_catalog(rel, level, table_note):
    v = lkml(rel)
    rows = []
    for f in v["fields"]:
        sql = re.sub(r"\s+", " ", f["sql"] or "")
        ids, names, src = ids_names(sql)
        derived = bool(ids or names) or "${" in sql and f["name"] not in ("composite_key",) and any(x in sql for x in ("${custom_field", "${deal_type", "${upfront", "${classification", "${sales_split", "${wbd_", "${various", "${run_revenue", "${demo_comp", "${payment_type"))
        raw = sql.startswith("${TABLE}.")
        if raw and not (ids or names):
            continue                                         # plain pass-through column of the custom-field table
        rows.append([level, f["name"], f["label"] or "", f["kind"], ", ".join(ids), "; ".join(names), ", ".join(src), sql[:700], f"{rel}:L{f['line_start']}-{f['line_end']}", table_note])
    return rows


def raw_columns(rel):
    v = lkml(rel)
    return [[f["name"], f["type"], f["label"] or "", re.sub(r"\s+", " ", f["sql"] or "")[:200], f"{rel}:L{f['line_start']}"] for f in v["fields"] if (f["sql"] or "").strip().startswith("${TABLE}.")]


def scan_occurrences():
    rows = []
    roots = [("looker-inventory-analytics", (".lkml",)), ("looker-etl-carl", (".sql", ".hql", ".py", ".md")), ("airflow_prod_eds", (".sql",)), ("dai-digital-ads", (".sql",))]
    rx = re.compile(r"custom_field_(?:id|name)", re.I)
    for root, exts in roots:
        for dp, dn, fn in os.walk(os.path.join(LEG, root)):
            for n in fn:
                if not n.endswith(exts):
                    continue
                p = os.path.join(dp, n)
                rel = os.path.relpath(p, LEG)
                try:
                    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
                except Exception:
                    continue
                for i, l in enumerate(lines, 1):
                    if not rx.search(l):
                        continue
                    ids, names, src = ids_names(l)
                    if not ids and not names:
                        continue
                    rows.append((rel, i, ids, names, l.strip()[:260]))
    return rows


def build(A):
    wb = new_wb()
    # ---- README
    rows = [
        ["What this is", "Every Operative One (Op1) custom-field extraction and every custom dimension found in the evidence - the 'custom fields' you asked for - with the exact IDs/names, source (wbd/wm), Looker expression and file:line."],
        ["Op1 custom-field model", "Op1 stores custom fields in long tables (FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V, ..._LINE_ITEM_CUSTOM_FIELD_V, AD_TYPE_BUY_TYPE_PRODUCT_V). Looker pivots them with CASE on custom_field_id (WBD/WM ids differ) or custom_field_name, one aliased join per field in the explore. CARL silver must replicate each pivot or the field is empty/wrong."],
        ["Two keying styles", "By ID (e.g. SSP = 204 for source 'wbd'; Deal Type = 41/214) and by NAME (Classification LIKE '%classification%', Opportunity ID / Warner SF Deal ID, Order Level Target / Warner Order Level Target, Upfront / Upfront Type / Upfront Type_Old, Invoice/Affidavit, VOD/OLV Fluidity, various). The ETL (om_con_dy) uses NAMES ('Warner Payment Type', 'Warner Deal Type', 'Ad Type', 'Buy Type', 'Line Internal Notes'), the LookML mostly uses IDs - not proven identical."],
        ["Sheets", "01 order-level | 02 line-level | 03 product-level | 04 occurrence scan (every id/name hit in the legacy repo) | 05 unique key summary | 06 explore join aliases | 07 Salesforce custom fields | 08 targeting IDs | 09 targeting listagg columns | 10 live Looker custom dimensions (no LookML on disk) | 11 UDF_OP_VERTICAL | 12 reference lists | 13 other maps (projection rank, record type)"],
        ["Evidence", "LookML and ETL = LEGACY-SOURCE (older snapshot). Live custom dimensions with no LookML on disk are listed in 10 with what the data proves."],
    ]
    write_sheet(wb, "00_README", ["Item", "Detail"], rows, [26, 160], title="UC1 custom fields catalog")

    hdr = ["Level", "Looker field", "Label", "Kind", "custom_field_id(s)", "custom_field_name(s)", "source filter", "Looker expression", "Citation", "Backing table"]
    o = view_catalog(CF_ORDER, "ORDER", lkml(CF_ORDER)["sql_table_name"])
    write_sheet(wb, "01_Op1_Order_CustomFields", hdr, o, [8, 26, 26, 11, 14, 36, 10, 80, 56, 40], title=f"Operative order-level custom fields ({len(o)} derived fields from view oper_sales_order_custom_field_t)",
                note="Plain pass-through columns of the table (api_name, created_by, ...) are listed in sheet 04 raw columns below; only DERIVED custom fields appear here.", freeze_col=2)
    l = view_catalog(CF_LINE, "LINE ITEM", lkml(CF_LINE)["sql_table_name"])
    write_sheet(wb, "02_Op1_Line_CustomFields", hdr, l, [8, 26, 26, 11, 14, 36, 10, 80, 56, 40], title=f"Operative line-item-level custom fields ({len(l)} derived fields)", freeze_col=2)
    pr = view_catalog(CF_PROD, "PRODUCT", lkml(CF_PROD)["sql_table_name"])
    write_sheet(wb, "03_Op1_Product_CustomFields", hdr, pr, [8, 26, 26, 11, 14, 36, 10, 80, 56, 40], title=f"Operative product-level custom fields ({len(pr)} derived fields; Ad Type / Buy Type)",
                note="Ad Type/Buy Type is read from DAAP_RPT.AD_TYPE_BUY_TYPE_PRODUCT_V (a view whose DDL is not in the evidence). The ETL reads the product custom field names 'Ad Type' and 'Buy Type' (02_op1_contracted_w_rate.sql L95/L99).", freeze_col=2)

    # raw columns of the 3 custom-field views
    rr = []
    for rel in (CF_ORDER, CF_LINE, CF_PROD):
        for r in raw_columns(rel):
            rr.append([os.path.basename(rel)] + r)
    write_sheet(wb, "03b_CustomField_RawColumns", ["View", "Looker field", "type", "label", "SQL", "citation"], rr, [44, 28, 12, 20, 40, 60], title="Raw columns of the three custom-field tables (the long format the pivots read)")

    # ---- scan
    occ = scan_occurrences()
    rows = [[r[0], r[1], ", ".join(r[2]), "; ".join(r[3]), r[4]] for r in occ]
    write_sheet(wb, "04_Occurrence_Scan", ["File", "Line", "custom_field_id(s)", "custom_field_name(s)", "Line text"], rows, [70, 7, 22, 40, 120], title=f"Every custom_field_id / custom_field_name condition in the legacy repo ({len(rows)} hits)")
    agg = defaultdict(lambda: {"n": 0, "files": set(), "first": None})
    for rel, ln, ids, names, text in occ:
        for k in [f"ID {i}" for i in ids] + [f"NAME {n}" for n in names]:
            a = agg[k]
            a["n"] += 1
            a["files"].add(rel)
            a["first"] = a["first"] or f"{rel}:L{ln}"
    rows = [[k, v["n"], len(v["files"]), v["first"], "; ".join(sorted(v["files"]))[:600]] for k, v in sorted(agg.items(), key=lambda kv: (kv[0].split()[0], -kv[1]["n"]))]
    write_sheet(wb, "05_Unique_Keys", ["Key (ID or NAME)", "hits", "distinct files", "first location", "files"], rows, [44, 8, 10, 70, 140], title=f"Unique custom-field ids/names referenced ({len(rows)})")

    # ---- explore join aliases
    joins = json.load(open(os.path.join(HERE, "work", "explore_joins_op1.json")))
    rows = []
    for j in joins:
        frm = j["frm"] or j["join"]
        if any(x in frm for x in ("custom_field", "targeting", "cf_")) or re.search(r"custom_field", j["sql_on"] or ""):
            ids, names, src = ids_names(j["sql_on"])
            rows.append([j["join"], frm, j["type"], ", ".join(ids), "; ".join(names), j["sql_on"][:600], f"looker-inventory-analytics/models/eg_order_management.model.lkml:L{j['line']}-{j['end']}"])
    write_sheet(wb, "06_Explore_CustomField_Joins", ["Join alias", "from view", "join type", "ids", "names", "sql_on", "citation"], rows, [30, 36, 12, 14, 36, 110, 70], title=f"Aliased custom-field joins in explore oper_sales_order_line_items_t ({len(rows)})",
                note="Each alias pivots ONE custom field. LEFT OUTER joins keep the base row when the field is absent; INNER joins (see lineage workbook) drop rows. Duplicate active values would fan out measures (risk J-02 in the Op1 analysis workbook).")

    # ---- SF custom fields
    sf_rows = [
        ["Links_to_Placeholder", "SF_CUSTOM_FIELD_NAME_PIVOT_MAP_V", "ETL: custom.Links_to_Placeholder", "salesforce_reporting.links_to_placeholder (label 'Links to Placeholder')", "looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql", "LEGACY-SOURCE"],
        ["Placeholder_Operative_Order_ID", "SF_CUSTOM_FIELD_NAME_PIVOT_MAP_V", "ETL: custom.Placeholder_Operative_Order_ID", "salesforce_reporting.placeholder_operative_order_id", "same", "LEGACY-SOURCE (100% null in 2026-10-16 export)"],
    ]
    for lab, col in [("WARNER_DEAL_TYPE_C", "DEAL_TYPE"), ("WARNER_PAYMENT_TYPE_C", "PAYMENT_TYPE"), ("WARNER_SF_OPPORTUNITY_ID_C", "OPP_ID"), ("WARNER_OPPORTUNITY_C", "OPP"), ("BROADWAY_IO_ID_C", "BROADWAY_IO_ID_C (iDeal ID)"), ("CLASSIFICATION_C", "UPF_VS_SCAT"), ("UPFRONT_TYPE_C", "UPF_TYPE"), ("PAYMENT_TYPE_C", "INVOICE_TYPE"),
                     ("PROJECTION_CHANGE_REASON_C", "PROJECTION_CHANGE_REASON"), ("CLOSED_LOST_CATEGORY_C", "CLOSED_LOST_CATEGORY"), ("COORDINATOR_C", "VAR1 (Client Success Coordinator)"), ("ACCOUNT_SPECIALIST_C -> user.name", "VAR2 (Account Specialist)"), ("DIGITAL_STRATEGIST_DSSI_C -> user.name", "DSSI"),
                     ("TOTAL_LI_TRAFFICKED_C / TOTAL_LI_DELIVERY_C / ACTIVE_LI_TRAFFICKED_C / ACTIVE_LI_DELIVERY_C", "TOTAL_LINE_TRAFF / TOTAL_LINE_DEL / ACTIVE_LINE_TRAFF / ACTIVE_LINE_DEL"), ("total_proposed_revenue_sm_c", "TOTAL_OP_PROP_REV"), ("TOTAL_PUBLISHED_REVENUE_SM_C", "TOTAL_TOTAL_PUBLISHED_REVENUE_SM_C"),
                     ("warner_sf_report_team_c", "TEAM"), ("warner_sf_vp_c", "VP"), ("warner_sf_division_c / user.division", "DIVISION"), ("PRIMARY_AE_OFFICE_REGION_C / PRIMARY_AE_OFFICE_C / SECONDARY_AE_OFFICE_C / TERTIARY_AE_OFFICE_C", "REGION / OFFICE / SECOND_OFFICE / THIRD_OFFICE")]:
        sf_rows.append([lab, "OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom)", f"-> {col}", "see Salesforce lineage workbook", "looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql", "LEGACY-SOURCE"])
    write_sheet(wb, "07_Salesforce_CustomFields", ["Salesforce custom field (_C)", "Source object", "ETL mapping", "Looker field", "Citation", "Status"], sf_rows, [48, 60, 44, 56, 70, 30], title="Salesforce custom (_C) fields and pivoted custom fields used by the reporting view",
                note="The pivot SF_CUSTOM_FIELD_NAME_PIVOT_MAP_V definition is not in the repo. All _C columns are as written in the ETL SELECT (02_salesforce_stg_insert.sql). Current (renamed) columns RECORD_TYPE_ID, BUYING_AGENCY_NAME, PLANNING_AGENCY_NAME, UPFRONT_AGENCY_NAME, ORDER_ID, BRAND_NAME, ORDER_CPM, IDEAL_DEAL_ID, LINEAR_TOTAL_AMOUNT, TOTAL_ESTIMATED_AMOUNT are known only from the secondary workbook.")

    # ---- targeting IDs
    txt = "\n".join(text_lines(TGT))
    lag = []
    for m in re.finditer(r"listagg\(CASE WHEN targeting_id IN \(([^)]*)\)\s*THEN targeting_option_name end, ', '\) WITHIN GROUP \(ORDER BY TARGETING_OPTION_ID\) AS (\w+)", txt, re.I):
        ids = [x.strip().strip("'") for x in m.group(1).split(",")]
        ln = txt[:m.start()].count("\n") + 1
        lag.append((m.group(2), ids, ln))
    v = lkml(TGT)
    labs = {f["name"]: f for f in v["fields"]}
    rows = []
    for i, (col, ids, ln) in enumerate(lag, 1):
        f = labs.get(col) or labs.get(col.lower())
        rows.append([i, col, ", ".join(ids), (f or {}).get("label") or "", (f or {}).get("group_label") or "", re.sub(r"\s+", " ", (f or {}).get("description") or ""), f"{TGT}:L{ln}", "FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id)"])
    write_sheet(wb, "09_Targeting_Listagg", ["#", "column", "targeting_id(s)", "Looker label", "group", "description", "citation", "source"], rows, [4, 40, 16, 40, 14, 60, 70, 60], title=f"dt_oper_hbo_targeting: {len(rows)} LISTAGG columns (one string per line item)",
                note="Legacy view has 26 columns. The pasted live Op1 SQL (CHAT-ONLY) also had hbo_max_series_include_by_season_fw, which is NOT in the legacy view - the live view is newer. Site (export label) depends on discovery_inventory_package (ID 1774).")
    aud_view = text_lines(V + "base.dt_oper_targeting_count.view.lkml")
    etl = text_lines("looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql")
    rows = [
        ["Looker audience divisor (oper_targeting_count)", "wbd", "1494, 1551, 1550, 1556, 1501, 1499, 1500, 1635, 1231, 815, 721, 1625, 1682, 1674, 1697", V + "base.dt_oper_targeting_count.view.lkml:L%d" % next(i for i,l in enumerate(aud_view,1) if "1494," in l), "target_count = avg over line of COUNT(DISTINCT targeting_option_name); applied to Net Revenue ONLY when audience_targeting is in the query"],
        ["Looker audience divisor (oper_targeting_count)", "wm", "1049, 1238, 1237, 1239, 1388, 1389, 1422", V + "base.dt_oper_targeting_count.view.lkml:L%d" % next(i for i,l in enumerate(aud_view,1) if "1049," in l), "same"],
        ["ETL audience_counts (om_con_dy)", "wbd", "1494, 1551, 1550, 1556, 1501, 1499, 1500, 1635, 1231, 815, 721, 1625, 1682, 1674  (NO 1697)", "looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql:L%d" % next(i for i,l in enumerate(etl,1) if "1494,1551" in l), "COUNT(CASE WHEN ... THEN 1) per line item"],
        ["ETL audience_counts (om_con_dy)", "wm", "1049, 1238, 1237, 1239, 1388, 1389, 1422", "looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql:L%d" % next(i for i,l in enumerate(etl,1) if "1049,1238" in l), "same"],
    ]
    write_sheet(wb, "08_Audience_Targeting_IDs", ["Use", "source", "targeting_id list", "citation", "behaviour"], rows, [44, 8, 80, 90, 80], title="Audience-targeting ID lists (divisor of Looker Net Revenue when audience targeting is selected)",
                note="DIFFERENCE: the Looker view includes WBD id 1697, the ETL list does not. Evidence: line numbers cited. Also VERIFY the chat-pasted live SQL (CHAT-ONLY) matches the Looker list.")

    # ---- Live Looker custom dimensions
    rows = [
        ["uf_group", "Salesforce (Look 26238)", "12 values", "NO LookML on disk. Reproduced pieces: Linear non-sports (13,190/13,190); D+ via legacy discoveryplusflag (90/90). Not reproduced: Sports/Linear NCAA with NULL Property Detail, WBD Stream breadth, Turner Sports.", "VERIFIED-DATA (partial) + MISMATCH", "D-06"],
        ["sales_division", "Salesforce (Look 26238)", "Linear / Sports / Digital", "NO LookML on disk. Cannot be re-derived: raw sports_property/forecast_category/network not exported.", "NOT RE-DERIVABLE", "D-06"],
        ["Platform", "Salesforce (Look 26238)", "Linear / Digital", "Equals Record Type except 23 rows (BR, Nascar, Digital Media).", "VERIFIED-DATA + MISMATCH", "D-05"],
        ["Property / Property Detail", "Salesforce (Look 26238)", "56 / 66 values", "Property = COALESCE(PropMap, SiteMap, NetMap, raw) of Property Detail on 100% of non-null rows.", "VERIFIED-DATA", "D-07"],
        ["UF Year", "Salesforce (Look 26238)", "3 values", "Regex [0-9]{2}/[0-9]{2} on Classification, else 'N/A' - 100%.", "VERIFIED-DATA", ""],
        ["Status Group", "Salesforce (Look 26238)", "Order / Pipeline / Prospecting / closed_lost", "Field Logic lifecycle rule - 100%.", "VERIFIED-DATA", "D-04"],
        ["Market Type (SF)", "Salesforce (Look 26238)", "7 values", "Field Logic rule - 100%.", "VERIFIED-DATA", "D-01"],
        ["Record Type", "Salesforce (current LookML)", "Linear / Digital (/Other)", "IDs 012Vq000002N4ubIAC (Linear); 012Vq000002N4rNIAS & 012Vq000002N4szIAC (Digital); NULL id before FILE_DT 2026-05-04 -> Digital (secondary workbook; same IDs in chat).", "SECONDARY-XLSX + CHAT-ONLY", "D-05"],
        ["Buyer_AE / Client_AE / Planning_AE", "Salesforce (Look 26238)", "AE names", "Current LookML: Linear role permutation Name/Second/Third (secondary workbook).", "SECONDARY-XLSX", "D-14"],
        ["Linear Total Amount", "Salesforce measure", "number", "COALESCE(LINEAR_TOTAL_AMOUNT, TOTAL_ESTIMATED_AMOUNT) summed (secondary workbook).", "SECONDARY-XLSX", "D-11"],
        ["Projection Rank (live CASE)", "Salesforce", "A,B,C,D,F,NULL", "Live mapping reproduced from data (7 stages); the live CASE text is chat-only.", "VERIFIED-DATA + CHAT-ONLY", "D-04"],
    ]
    write_sheet(wb, "10_Live_Looker_CustomDims", ["Looker field", "Where", "Domain", "What is proven / where it comes from", "Evidence status", "Decision"], rows, [32, 26, 30, 110, 30, 10], status_cols=(4,), title="Live Looker custom dimensions that have no LookML on disk")

    # ---- UDF
    rows = [[r["line_no"], "LOWER(forecast_category)" if r["lower"] else "forecast_category", r["op"], r["pattern"], r["result"]] for r in A["udf_rules"]]
    write_sheet(wb, "11_UDF_OP_VERTICAL", ["Order", "Tested expression", "Operator", "Pattern", "Returns"], rows, [8, 30, 10, 50, 50], title=f"DAAP_RPT.UDF_OP_VERTICAL - {len(rows)} WHEN-branches parsed in order from legacy looker-etl-carl/snowflake/RA_UDF/op1_udf.sql",
                note="Field Logic says this is 'a Snowflake function we cannot read' - its definition IS in the legacy repo. First matching branch wins; unmatched -> the ELSE of the function (see source). Used by Looker 'Vertical' for Op1 (and Salesforce 'Digital Vertical').")

    # ---- Lists
    rows = []
    for nm, vals in A["lists"].items():
        for v in vals:
            if isinstance(v, tuple):
                rows.append([nm, v[0], v[1], A["list_desc"].get(nm)])
            else:
                rows.append([nm, v, "", A["list_desc"].get(nm)])
    write_sheet(wb, "12_Reference_Lists", ["List", "value / source value", "rolls up to", "description (Lists tab col C)"], rows, [22, 44, 40, 80], title="Lists tab of UC1_Fields_for_CARL_working (2).xlsx (every list, verbatim)")

    # ---- other maps
    V0 = A["verify"]
    rows = [["Projection Rank (live export, all stage->rank pairs)", x["a"], x["b"], x["n"]] for x in V0["sf_stage_to_rank"]]
    rows += [["Status Group (live export)", x["a"], x["b"], x["n"]] for x in V0["sf_stage_to_status"]]
    rows += [["Salesforce Classification -> Market Type", x["a"], x["b"], x["n"]] for x in V0["sf_class_to_market"]]
    rows += [["Salesforce Classification -> UF Year", x["a"], x["b"], x["n"]] for x in V0["sf_class_to_ufyear"]]
    rows += [["Platform vs Record Type", x["a"], x["b"], x["n"]] for x in V0["sf_platform_vs_recordtype"]]
    write_sheet(wb, "13_Observed_Maps", ["Map", "from", "to", "rows"], rows, [50, 44, 44, 10], title="Observed value maps in the Looker SF export (computed)")

    p = os.path.join(OUT, "UC1_Custom_Fields_Catalog.xlsx")
    wb.save(p)
    return p
