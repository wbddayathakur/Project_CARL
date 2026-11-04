"""Workbooks 3 and 4 - Salesforce and Op1 column lineage."""
import re, json, os
from collections import OrderedDict
import knowledge as K
from common import *

V = "looker-inventory-analytics/views/"
SF_ETL = "looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql"
SF_DDL = "looker-etl-carl/airflow/dags/revops_etl/salesforce/ddl/wbd_sf.sql"
OP_ETL1 = "looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql"
OP_ETL2 = "looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/02_op1_contracted_w_rate.sql"
OP_PACE = "looker-etl-carl/snowflake/snowflake_views/op1_custom_pacing_imps_rev_mapping_v.sql"
SF_RAW = "airflow_prod_eds/metadata/salesforce_wbd/19916_site_month_breakout_load.sql"
LI = V + "base.oper_sales_order_line_items_t.view.lkml"
OT = V + "base.oper_sales_order_t.view.lkml"
MODEL = "looker-inventory-analytics/models/eg_order_management.model.lkml"


def split_top(s):
    out, depth, cur, q = [], 0, "", None
    i = 0
    while i < len(s):
        ch = s[i]
        if q:
            cur += ch
            if ch == q:
                q = None
        elif ch in "'\"":
            q = ch
            cur += ch
        elif ch == "(":
            depth += 1
            cur += ch
        elif ch == ")":
            depth -= 1
            cur += ch
        elif ch == "-" and s[i:i + 2] == "--":
            j = s.find("\n", i)
            j = len(s) if j < 0 else j
            cur += s[i:j]
            i = j - 1
        elif ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
        i += 1
    if cur.strip():
        out.append(cur)
    return out


def strip_comments(x):
    return re.sub(r"--[^\n]*", "", x)


def sf_pairs():
    lines = text_lines(SF_ETL)
    txt = "\n".join(lines)
    a = txt.index("INSERT INTO DAAP_RPT_STAGE.SALESFORCE_MTH_STG (")
    b = txt.index(")", a + 50)
    cols = [c.strip() for c in strip_comments(txt[a:b].split("(", 1)[1]).replace("\n", "").split(",") if c.strip()]
    sa = txt.index("SELECT", b)
    sb = txt.index("\nFROM\n", sa)
    exprs = split_top(txt[sa + 6:sb])
    # line number of each expression start
    out = []
    pos = sa + 6
    for c, e in zip(cols, exprs):
        e_clean = re.sub(r"\s+", " ", strip_comments(e)).strip()
        key = strip_comments(e).strip()[:30]
        k = txt.find(key, pos)
        ln = txt[:k].count("\n") + 1 if k >= 0 else None
        pos = k + 1 if k >= 0 else pos
        out.append((c, e_clean, ln))
    return out, len(cols), len(exprs)


def build_sf(A):
    wb = new_wb()
    P = A["profile_pipe"]
    pairs, nc, ne = sf_pairs()
    view = lkml(V + "base.salesforce_reporting.view.lkml")
    # map ETL column -> LookML dims whose sql references ${TABLE}.<col>
    ref = {}
    for f in view["fields"]:
        for m in re.finditer(r"\$\{TABLE\}\.\"?(\w+)\"?", f["sql"] or "", re.I):
            ref.setdefault(m.group(1).upper(), []).append(f)
    export_lab = {  # LookML field -> export label (only where the mapping is certain from legacy label equality)
        "opportunity_stage": "Salesforce Opportunity Stage", "upf_scat": "Salesforce Classification", "opportunity": "Salesforce Opportunity ID", "opportunity_name_id": "Salesforce Opportunity Name",
        "advertiser_name": "Salesforce Advertiser Name", "agency_name": "Salesforce Agency", "total_amount": "Salesforce Total Amount", "projection_rank": "Salesforce Projection Rank",
        "broadway_io_id_c": "Salesforce iDeal ID", "placeholder_operative_order_id": "Salesforce Placeholder Operative Order ID", "opp_sales_order_id": "Salesforce Sales Order ID", "ad_type": "Salesforce Ad Type",
        "file_date_date": "Salesforce  Historical Snapshot Filter", "workflow_status": "Salesforce Workflow Status", "deal_type": "Salesforce Deal Type", "primary_ae": "related live dims Buyer_AE / Client_AE / Planning_AE (live role mapping not in repo; see 02_SF_Pipeline_Fields)",
        "secondary_ae": "related live dims Buyer_AE / Client_AE / Planning_AE (live role mapping not in repo)", "tertiary_ae": "related live dims Buyer_AE / Client_AE / Planning_AE (live role mapping not in repo)", "projection": "Salesforce Net Projections", "weighted_projection": "Salesforce Net Weighted Projections",
    }
    rows = []
    for i, (c, e, ln) in enumerate(pairs, 1):
        lk = ref.get(c.upper(), [])
        seen = set(); lk = [f for f in lk if not (f["name"], f["line_start"]) in seen and not seen.add((f["name"], f["line_start"]))]
        dims = "; ".join(f"{f['name']} ({f['kind']}" + (f", label '{f['label']}'" if f['label'] else "") + f") L{f['line_start']}" for f in lk)
        labs = "; ".join(OrderedDict.fromkeys(export_lab[f["name"]] for f in lk if f["name"] in export_lab))
        if c.upper() == "FORECASTED_VALUE":
            labs = labs or "Salesforce Net Projections (via measure projection)"
        if c.upper() == "WEIGHTED_SCHEDULED_PIPELINE":
            labs = labs or "Salesforce Net Weighted Projections (via measure weighted_projection)"
        rows.append([i, c, e[:900], f"{SF_ETL}:L{ln}" if ln else "", "DAAP_RPT_STAGE.SALESFORCE_MTH_STG -> swapped into DAAP_RPT.SALESFORCE_MTH (03_salesforce_swap.sql). Looker view reads DAAP_RPT.WBD_SALESFORCE_MTH_V; how that view derives from SALESFORCE_MTH is NOT in the repo", dims or "no LookML field reads this column", labs or "not in Look 26238 export"])
    write_sheet(wb, "01_ETL_Column_Lineage", ["#", "Target column (SALESFORCE_MTH_STG)", "SELECT expression in ETL (comments removed)", "ETL citation", "Landing / reporting object", "LookML field(s) reading it (base.salesforce_reporting)", "Look 26238 export label"], rows, [4, 32, 90, 62, 46, 70, 44],
                title=f"Salesforce: ETL column -> LookML field -> export label ({len(rows)} columns; INSERT list {nc}, SELECT list {ne})",
                note="ETL: PROD_AC.FINAL_SALESFORCE_WBD.SITE_MONTH_BREAKOUT_V (site_month) left-joined to AD_TYPE_V, OPPORTUNITY_V, USER_V x5 (primary/secondary/tertiary AE, DSSI, CSM), oper_etl_orders_activity_order_status_mappping_V and SF_CUSTOM_FIELD_NAME_PIVOT_MAP_V; WHERE IS_DELETED=0 AND FILE_DT=CURRENT_DATE; GROUP BY ALL. Raw feed: sf_site_month_breakout__c_<date> files loaded by job set 19916 into FINAL_SALESFORCE_WBD.SITE_MONTH_BREAKOUT.", freeze_col=2)

    # LookML fields
    rows = []
    for f in view["fields"]:
        rows.append([f["name"], f["kind"], f["type"], f["label"] or "", f["group_label"] or "", re.sub(r"\s+", " ", f["sql"] or "")[:900], re.sub(r"\s+", " ", f["description"] or ""), f"{V}base.salesforce_reporting.view.lkml:L{f['line_start']}-{f['line_end']}", export_lab.get(f["name"], "")])
    write_sheet(wb, "02_LookML_Fields", ["field", "kind", "type", "label", "group", "SQL", "description", "citation", "export label (certain matches only)"], rows, [30, 11, 10, 28, 16, 90, 50, 70, 34],
                title=f"Legacy LookML view salesforce_reporting ({len(rows)} fields; table {view['sql_table_name']})", freeze_col=1)

    # source / joins
    rows = [
        ["Raw landing", "FINAL_SALESFORCE_WBD.SITE_MONTH_BREAKOUT", f"S3 files matching regex sf_site_month_breakout__c_<date>; job set 19916 SALESFORCE-WBD-SITE_MONTH_BREAKOUT-LOAD (copy into STAGING_SALESFORCE_WBD.SITE_MONTH_BREAKOUT, audit parsed vs loaded rows, insert into clone + swap)", SF_RAW],
        ["ETL source (FROM)", "PROD_AC.FINAL_SALESFORCE_WBD.SITE_MONTH_BREAKOUT_V", "alias site_month; filtered IS_DELETED=0 and FILE_DT=CURRENT_DATE()", SF_ETL],
        ["ETL join", "AD_TYPE_V", "site_month.ad_type_c = ad_type.id", SF_ETL],
        ["ETL join", "OPPORTUNITY_V", "site_month.OPPORTUNITY_C = opp.id", SF_ETL],
        ["ETL join", "USER_V x5", "ON user.id = opp.primary_ae_c / opp.secondary_ae_c / opp.tertiary_ae_c / opp.DIGITAL_STRATEGIST_DSSI_C / opp.ACCOUNT_SPECIALIST_C", SF_ETL],
        ["ETL join", "DAAP_RPT.oper_etl_orders_activity_order_status_mappping_V", "FILE_DATE = site_month.file_dt AND SALES_ORDER_ID = site_month.OPERATIVE_ORDER_ID_C  (definition NOT in repo)", SF_ETL],
        ["ETL join", "DAAP_RPT.SF_CUSTOM_FIELD_NAME_PIVOT_MAP_V", "site_month.OPPORTUNITY_C = custom.opportunity  (definition NOT in repo)", SF_ETL],
        ["Staging (clone)", "DAAP_RPT_STAGE.SALESFORCE_MTH_STG", "00_salesforce_clone: CREATE OR REPLACE ... CLONE DAAP_RPT.SALESFORCE_MTH; 01: DELETE WHERE FILE_DT = CURRENT_DATE(); 02: INSERT (this lineage); 03: SWAP WITH DAAP_RPT.SALESFORCE_MTH. => table keeps one snapshot per FILE_DT (append by day, replace for the current day)", "looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/00_salesforce_clone.sql, 01_salesforce_stg_delete.sql, 03_salesforce_swap.sql"],
        ["Reporting object", "DAAP_RPT.WBD_SALESFORCE_MTH_V", "sql_table_name of base.salesforce_reporting (definition NOT in repo). DDL file ddl/wbd_sf.sql defines a table WBD_SF. A second view, base.wbd_salesforce_reporting (derived table), defines file_date_date as dateadd(day,-1,FILE_DT) whereas base.salesforce_reporting uses FILE_DT directly", V + "base.salesforce_reporting.view.lkml:L2, L213-L216; " + V + "base.wbd_salesforce_reporting.view.lkml:L133-L136"],
        ["Looker joins (SF explore)", "sf_opp_won_v, sales_office, op1_order_payment_type, pi_site_mapping", "Listed as external dependencies in the secondary workbook; not re-verified against the SF explore here", "Salesforce_AdSales_LookML_Iceberg_Analysis.xlsx sheet 3"],
    ]
    write_sheet(wb, "03_Sources_And_Joins", ["Stage", "Object", "Detail", "Citation"], rows, [26, 62, 100, 80], title="Salesforce source chain")
    ddl = text_lines(SF_DDL)
    rows = [[i, l.strip()[:300]] for i, l in enumerate(ddl, 1) if l.strip()]
    write_sheet(wb, "04_WBD_SF_DDL", ["line", "text"], rows, [8, 200], title=f"Legacy DDL: {SF_DDL}")

    # measures
    byname = {f["name"]: f for f in view["fields"]}
    def cit(n):
        f = byname[n]
        return f"{V}base.salesforce_reporting.view.lkml:L{f['line_start']}-L{f['line_end']}"
    tp = [c for c, e, ln in pairs if "TOTAL_PUBLISHED" in c.upper()]
    rows = [
        ["projection (measure) 'Net Projections'", "SUM(${forecasted_value})", "dimension forecasted_value = ${TABLE}.forecasted_value <- ETL " + dict((c, e) for c, e, l in pairs).get("FORECASTED_VALUE", "?")[:200], "Salesforce Net Projections", cit("projection") + "; " + cit("forecasted_value"), "LEGACY-SOURCE"],
        ["weighted_projection (measure) 'Net Weighted Projections'", "SUM(${weighted_scheduled_pipeline})", "dimension weighted_scheduled_pipeline = ${TABLE}.weighted_scheduled_pipeline <- ETL " + dict((c, e) for c, e, l in pairs).get("WEIGHTED_SCHEDULED_PIPELINE", "?")[:200], "Salesforce Net Weighted Projections", cit("weighted_projection") + "; " + cit("weighted_scheduled_pipeline"), "LEGACY-SOURCE"],
        ["opp_per_sales (dimension, label 'Opportunity Probability')", "ROUND(DIV0(weighted_scheduled_pipeline, forecasted_value), 4) - a ROW-LEVEL dimension, not a measure", "ratio of two stored columns", "(not in Look 26238)", cit("opp_per_sales"), "LEGACY-SOURCE"],
        ["TOTAL_PUBLISHED_REVENUE_SUM (measure)", "SUM(COALESCE(${TOTAL_PUBLISHED_REVENUE_SM_C},0)) ; the dimension reads ${TABLE}.TOTAL_TOTAL_PUBLISHED_REVENUE_SM_C (note the doubled TOTAL_ in the LookML). ETL SELECT columns containing TOTAL_PUBLISHED: " + (", ".join(tp) or "none"), "opportunity-level value", "(not in Look 26238)", cit("TOTAL_PUBLISHED_REVENUE_SUM") + "; " + cit("TOTAL_PUBLISHED_REVENUE_SM_C"), "LEGACY-SOURCE"],
        ["Linear Total Amount", "per secondary workbook: SUM(COALESCE(LINEAR_TOTAL_AMOUNT, TOTAL_ESTIMATED_AMOUNT)); not in the legacy repo", "current LookML only", "Salesforce Linear Total Amount", "Salesforce_AdSales_LookML_Iceberg_Analysis.xlsx sheet 1", "SECONDARY-XLSX + CHAT-ONLY"],
    ]
    write_sheet(wb, "05_Measures", ["Field", "Looker formula", "Upstream", "Export label", "Citation", "Status"], rows, [40, 70, 80, 36, 90, 24], title="Salesforce measures (legacy repo)")

    # live vs legacy
    legacy_dims = {f["name"] for f in view["fields"]}
    rows = []
    for f in K.SF_FIELDS:
        rows.append([f["label"], "yes" if f["legacy"] else "NO", f["status"], f["live_vs_legacy"][:500]])
    write_sheet(wb, "06_Live_vs_Legacy", ["Looker export label", "Has legacy LookML/ETL source?", "Status", "Note"], rows, [40, 22, 40, 120], status_cols=(2,), title="Which of the 33 live labels exist in the legacy repo")
    p = os.path.join(OUT, "UC1_Salesforce_Lineage.xlsx")
    wb.save(p)
    return p, nc, ne


def build_op1(A):
    wb = new_wb()
    D = A["profile_dig"]
    # ---- ETL select list (om_con_dy) lines 119-179
    lines = text_lines(OP_ETL1)
    a = next(i for i, l in enumerate(lines) if l.strip() == "SELECT" and i > 100)
    b = next(i for i, l in enumerate(lines) if l.strip() == "FROM" and i > a)
    rows = []
    for i in range(a + 1, b):
        l = lines[i].strip().rstrip(",")
        if not l or l.startswith("--"):
            continue
        m = re.search(r"\bas\s+(\w+)\s*$", l, re.I)
        alias = m.group(1) if m else l.split(".")[-1].split(" ")[0]
        rows.append([len(rows) + 1, alias, l, f"{OP_ETL1}:L{i + 1}"])
    write_sheet(wb, "01_om_con_dy_SelectList", ["#", "column", "expression in inner SELECT", "citation"], rows, [4, 38, 120, 70],
                title=f"om_con_dy ETL (DAAP_RPT_STAGE.STG_OM_CON_DY): inner SELECT list ({len(rows)} expressions)",
                note="Grain = one row per sales-order line item per calendar day (INNER JOIN to oper_dimdate_v between line start and end). Per-day values = value / ((day_num+1) * counts), day_num = DATEDIFF(day, line start, line end), counts = COALESCE(production line count,1). Several LEFT JOINs (production line items, publisher map, custom fields) can multiply rows, so the divisor counts compensates. Filters: cost_type IN ('CPM','SOV-Flat Rate','Flat Rate','Cost Per Unit'); line_item_status IN ('sent_to_production','active','incomplete','modified'); group_type IN ('', 'RunOf'); CALENDARDATE >= '2020-01-01'.")
    outer = []
    for i in range(40, 118):
        l = lines[i].strip().rstrip(",")
        if l and not l.startswith("--") and l not in ("SELECT",):
            outer.append([len(outer) + 1, l, f"{OP_ETL1}:L{i + 1}"])
    write_sheet(wb, "01b_om_con_dy_OuterColumns", ["#", "outer column", "citation"], outer, [4, 90, 70], title="STG_OM_CON_DY final column order (outer SELECT; op1.* from the line-item SQL, map.* from the custom pacing view)")
    # ---- ETL logic steps
    rows = [
        ["Forecast category (Site base)", "COALESCE(line.forecast_category, OPER_PRODUCT_SITE.SITE, 'Uncategorized Revenue'); site join on product_id + rate_card_id", OP_ETL1, "L:coalesce(oper_sales_order_line_items_v.forecast_category"],
        ["Day expansion", "INNER JOIN FINAL_OPERATIVE.oper_dimdate_v ON line start <= calendardate <= line end", OP_ETL1, "L:INNER JOIN FINAL_OPERATIVE.oper_dimdate_v"],
        ["Per-day cost / qty", "net_cost, gross_cost, quantity, production_quantity, net_unit_cost, gross_unit_cost, added_value_amount each / ((day_num+1) * counts)", OP_ETL1, "L:net_cost_per_day"],
        ["counts", "COALESCE(line_counts, 1); line_counts = COUNT(*) per sales_order_line_item_id over oper_production_line_item_v LEFT JOIN oper_publisher_system_ad_prod_line_item_map_v. Used as divisor because the main query LEFT JOINs production line items and fans rows out", OP_ETL1, "L:COALESCE(line_counts, 1) as counts"],
        ["audience_counts", "COUNT of rows in oper_sales_line_item_targeting_v per (source, line) whose targeting_id is in a hard-coded list: source wm {1049,1238,1237,1239,1388,1389,1422}; source wbd {1494,1551,1550,1556,1501,1499,1500,1635,1231,815,721,1625,1682,1674}", OP_ETL1, "L:AS audience_counts"],
        ["payment_type", "order custom field name 'Warner Payment Type' OR ('Payment Type' AND source='wm')", OP_ETL1, "L:(payment_type.custom_field_name = 'Warner Payment Type'"],
        ["deal_type", "IFNULL(order custom field 'Warner Deal Type' OR ('Deal Type' AND source='wm'), 'None')", OP_ETL1, "L:IFNULL(deal_type.custom_field_value,'None') as deal_type"],
        ["ad_type", "product custom field 'Ad Type' (product_id + source)", OP_ETL1, "L:ad_type.custom_field_value as ad_type"],
        ["Notes", "line custom field names 'Line Internal Notes' or 'Notes'", OP_ETL1, "L:notes.custom_field_name IN ('Line Internal Notes','Notes')"],
        ["future_rate / past_rate", "COALESCE(OPER_CURRENCY_EXCHANGE_RATE_FORECAST_V.FORECAST_RATE,1) for dates after the latest forecast file_date; COALESCE(oper_curr_rate_wbd.rate,1) for the exact calendar date (wbd only)", OP_ETL1, "L:COALESCE(future_rate.FORECAST_RATE, 1) as future_rate"],
        ["Line filters", "cost_type IN ('CPM','SOV-Flat Rate','Flat Rate','Cost Per Unit') AND line_item_status IN ('sent_to_production','active','incomplete','modified')", OP_ETL1, "L:cost_type IN ('CPM'"],
        ["Outer filters", "group_type IN ('', 'RunOf') AND CALENDARDATE >= '2020-01-01'; LEFT JOIN custom pacing map on line id + pacing_date = calendardate", OP_ETL1, "L:WHERE group_type IN"],
        ["Currency applied", "Only NET_UNIT_COST_PER_DAY, NET_COST_PER_DAY, GROSS_UNIT_COST_PER_DAY, GROSS_COST_PER_DAY are multiplied: CASE WHEN CALENDARDATE >= CURRENCY_FILE_DATE THEN x*FUTURE_RATE ELSE x*PAST_RATE END. PACING_* columns, quantities and ADDED_VALUE_AMOUNT_PER_DAY are passed through UNCONVERTED. CURRENCY_FILE_DATE is NULL when no forecast-rate row matched, so the ELSE branch (PAST_RATE) applies.", OP_ETL2, "L:CURRENCY_FILE_DATE"],
        ["Ad Type / Buy Type (rate step)", "02 file: AD_TYPE = IFNULL(product custom field 'Ad Type', product custom field 'Buy Type') (this overrides the Ad Type from the first step). LookML view then adds its own Ad Type logic on top", OP_ETL2, "L:ad_type.custom_field_name = 'Ad Type'"],
        ["Custom pacing", "PCT_OF_TOTAL_x = x * pacing_pct/100 (rows with pacing_pct != 0); PACING_x = (PCT_OF_TOTAL_x - previous change_date PCT_OF_TOTAL_x, 0 if none) / PACING_DAYS for PQ, QUANTITY, NET_COST, GROSS_COST; rows with pacing_pct = 0 unioned with PACING_x = 0; running totals via SUM() OVER (PARTITION BY line ORDER BY PACING_DATE); PACING_FLAG = 'Yes'. Source rows come from OP1_CUSTOM_PACING_REPORT_V (definition not in repo)", OP_PACE, "L:PACING_NET_COST"],
    ]
    out = []
    for step, logic, f, needle in rows:
        c, snip = resolve((f, needle))
        out.append([step, logic, c, snip[:300]])
    write_sheet(wb, "02_ETL_Logic_Steps", ["Step", "Logic", "Citation", "Source line"], out, [28, 110, 80, 90], title="om_con_dy / currency / pacing logic CARL silver must reproduce")
    # ---- measures
    rows = []
    for nm in ("sum_net_cost", "sum_net_cost_dim", "sum_gross_cost", "sum_gross_cost_dim", "net_parent_gross_cost", "sum_quantity", "sum_quantity_dim", "sum_production_quantity", "sum_production_quantity_dim", "product_counts", "net_cost_per_day", "quantity_per_day", "production_quantity_per_day",
               "even_pacing_sum_net_cost", "even_pacing_sum_gross_cost", "even_pacing_sum_quantity", "even_pacing_sum_production_quantity", "market_type", "is_dr", "team", "forecast_category", "vertical", "property", "sports_property", "booking_status", "calendar"):
        c, s = resolve((LI, nm))
        if "not found" in c:
            continue
        rows.append([nm, c, s])
    write_sheet(wb, "03_LookML_Measures_Dims", ["Looker field", "Citation", "Looker SQL (verbatim, whitespace-collapsed)"], rows, [34, 90, 200], title="Op1 explore: measures and derived dimensions (legacy LookML)",
                note="sum_net_cost_dim / sum_gross_cost_dim / sum_quantity_dim contain {% if ... _in_query %} templating: the audience-targeting divisor (oper_targeting_count) and contextual divisors apply only when those fields are selected in the Look.")
    # ---- joins
    joins = json.load(open(os.path.join(HERE, "work", "explore_joins_op1.json")))
    rows = [[j["join"], j["frm"] or j["join"], j["type"], j["relationship"] if "relationship" in j else "", j["view_label"], j["sql_on"][:700], f"{MODEL}:L{j['line']}-{j['end']}"] for j in joins]
    write_sheet(wb, "04_Explore_Joins", ["join alias", "from view", "join type", "relationship", "view_label", "sql_on", "citation"], rows, [32, 36, 12, 14, 24, 110, 70], title=f"Explore oper_sales_order_line_items_t: all {len(rows)} joins (model lines 8-2394)",
                note="Join types matter: INNER joins drop base rows when the joined row is missing (e.g. oper_sales_order_t). FULL OUTER (agency) can add rows. The prior analysis workbook flags these as risks J-01..J-08.")
    # ---- explore filters
    rows = [
        ["always_filter", "is_linear_addressable.is_linear_addressable = 'No'", MODEL + ":L99-L109", "default (user can change)"],
        ["always_filter", "oper_sales_order_line_items_t.is_default_media_plan = 'Yes'", MODEL + ":L99-L109", "default"],
        ["sql_always_where", "line_item_status IN ('sent_to_production', 'active', 'incomplete', 'modified')", MODEL + ":L111-L113", "not changeable"],
        ["Derived-table exclusions (per prior analysis)", "described in the secondary workbook; NOT re-verified in the legacy repo", "Operative1_AdSales_Master_Analysis_Final.xlsx sheet 05", "SECONDARY-XLSX"],
        ["persist_for", "1 hours (explore cache)", MODEL + ":L12", "freshness"],
    ]
    write_sheet(wb, "05_Explore_Filters", ["Type", "Rule", "Citation", "Note"], rows, [26, 100, 70, 30], title="Mandatory explore filters (must be replicated for parity)")
    # ---- label lineage
    rows = []
    for f in K.OP1_FIELDS:
        cites = [resolve(r)[0] for r in f["legacy"]]
        rows.append([f["label"], f["kind"], f["logic"][:700], "\n".join(cites), f["mvp"], f["status"]])
    write_sheet(wb, "06_Label_Lineage", ["export label (Look 26239)", "kind", "logic", "legacy citations", "MVP row", "status"], rows, [40, 28, 120, 90, 24, 28], status_cols=(5,), title="Look 26239 labels -> Looker field -> upstream")
    p = os.path.join(OUT, "UC1_Op1_Lineage.xlsx")
    wb.save(p)
    return p
