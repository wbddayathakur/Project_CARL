"""Build the Research Market Share discovery workbook and lineage/ERD doc.

    python build_workbook.py            # writes into ./out
"""
import json
import os
import re
from datetime import date

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

import knowledge as K

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
INTAKE_XLSX = os.path.join(HERE, "evidence", "intake_use_case_3a_marketplace.xlsx")
BRONZE_COLS = json.load(open(os.path.join(HERE, "evidence", "bronze_columns_prod_catalog_2026-08-27.json")))

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(bold=True, color="FFFFFF")
TITLE_FONT = Font(bold=True, size=14)
WRAP = Alignment(wrap_text=True, vertical="top")
STATUS_FILL = {
    "Fit": "C6EFCE", "Exists (Prod)": "C6EFCE", "Confirmed": "C6EFCE", "P0": "FFC7CE",
    "Partial": "FFEB9C", "Decision": "FFEB9C", "Build": "FFEB9C", "P1": "FFEB9C", "Proposed": "DDEBF7",
    "Gap": "FFC7CE", "Blocker": "FFC7CE", "Migrate": "C6EFCE", "Replace": "C6EFCE",
    "Retire": "D9D9D9", "Out of scope": "D9D9D9", "Rebuild as Cube": "DDEBF7", "Rebuild, then retire": "DDEBF7", "Unknown": "FFEB9C", "Warn": "FFEB9C", "P2": "DDEBF7",
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
            c = ws.cell(row=r, column=i, value=v)
            c.alignment = WRAP
        if status_col is not None:
            key = str(row[status_col]).split(" (")[0]
            fill = STATUS_FILL.get(key)
            if fill:
                ws.cell(row=r, column=status_col + 1).fill = PatternFill("solid", fgColor=fill)
    widths = widths or [24] * len(headers)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "B5"
    if rows:
        ws.auto_filter.ref = f"A4:{get_column_letter(len(headers))}{len(rows) + 4}"
    return ws


# ---------------------------------------------------------------------------
# Field mapping: intake Metrics_Dims -> Bronze -> Iceberg -> Cube
# ---------------------------------------------------------------------------
def has_col(table, col):
    return any(c[0] == col for c in BRONZE_COLS.get(table, []))


PV, PD = "big_mit_bronze.program_viewing", "big_mit_bronze.program_descriptor"
S, G = K.SILVER, K.GOLD
TEL = "guideline_bronze.telecast_delivery"
ACC = "guideline_bronze.accutv_delivery"

# (use case, regex on field) -> bronze table, bronze column(s), target, cube member, status
FIELD_RULES = [
    ("1", r"^gross spend", TEL, "GROSSMEDIASPEND", f"{G}.fct_telecast_demand.gross_media_spend", "Gross Spend", "Gap"),
    ("1", r"eq30", TEL, "EQUIVALIZED_30S_SPOT_COUNT", f"{G}.fct_telecast_demand.eq30_spot_count", "EQ30 Spot Count", "Gap"),
    ("1", r"gross impressions \(gross", PV, "commercial_program_duration, *_delivery", f"{G}.fct_telecast_supply.gross_impressions", "Gross Impressions", "Fit"),
    ("1", r"gross impressions \(avg", PV, "as above + calendar", "Cube measure", "Gross Impressions per BC Week", "Partial"),
    ("1", r"power ratio", "-", "-", "Cube measure", "Power Ratio", "Proposed"),
    ("1", r"average audience", PV, "average_audience", f"{G}.fct_telecast_supply.average_audience", "Average Audience", "Fit"),
    ("1", r"program duration", PV, "duration", f"{G}.fct_telecast_supply.duration", "Program Duration", "Fit"),
    ("1", r"commercial duration", PV, "commercial_program_duration", f"{G}.fct_telecast_supply.commercial_program_duration", "Commercial Duration", "Fit"),
    ("1", r"spot length", TEL, "SPOTLENGTH", f"{G}.fct_telecast_demand.spot_length", "Spot Length", "Gap"),
    ("1", r"airing date/time", PV, "airing_datetime", f"{G}.fct_telecast_supply.airing_minute", "Airing Date/Time", "Fit"),
    ("1", r"airing date \(calendar", PV, "airing_datetime", f"{G}.fct_telecast_supply.airing_date", "Airing Date", "Fit"),
    ("1", r"broadcast date", PD, "broadcast6_6datetime / _broadcast_datesk", f"{G}.fct_telecast_supply.broadcast_date", "Broadcast Date", "Fit"),
    ("1", r"^start time", PD, "airing_datetime / nielsenreportingtime", f"{G}.fct_telecast_supply.start_time", "Start Time", "Fit"),
    ("1", r"time shift", PV, "time_shifted_viewing_type", "Silver filter (BR-01)", "-", "Fit"),
    ("1", r"nielsen data type", PV, "nielsen_data_type", "Silver filter (BR-01)", "-", "Fit"),
    ("1", r"buy type", TEL, "BUYTYPE", f"{G}.fct_telecast_demand.buy_type", "Buy Type", "Gap"),
    ("1", r"^adu", TEL, "ADU", f"{G}.fct_telecast_demand.adu", "ADU", "Gap"),
    ("1", r"programming genre type", "marketshare_bronze.dimnetworkprogramnamemapping", "programgroupsummary", f"{G}.dim_program.genre_type", "Programming Genre Type", "Fit"),
    ("1", r"programming genre subtype", "marketshare_bronze.dimnetworkprogramnamemapping", "programgroupdetail", f"{G}.dim_program.genre_subtype", "Programming Genre Subtype", "Fit"),
    ("1", r"programming genre$", "marketshare_bronze.dimnetworkprogramnamemapping", "programgroupsummary (BR-18)", f"{G}.dim_program.genre", "Programming Genre", "Partial"),
    ("1", r"program type description", "marketshare_bronze.dimnetworkprogramnamemapping", "programtypedescription", f"{G}.dim_program.nielsen_program_type_desc", "Nielsen Program Type", "Partial"),
    ("1", r"program type code", PD, "program_type", f"{G}.dim_program.nielsen_program_type", "Nielsen Program Type Code", "Fit"),
    ("1", r"subtype description", "marketshare_bronze.dimnetworkprogramnamemapping", "programsubtypedescription", f"{G}.dim_program.nielsen_program_subtype_desc", "Nielsen Program Subtype", "Partial"),
    ("1", r"subtype code", PD, "program_subtype", f"{G}.dim_program.nielsen_program_subtype", "Nielsen Program Subtype Code", "Fit"),
    ("1", r"network type", "marketshare_bronze.dimnetwork", "networktype", f"{G}.dim_network.network_type", "Network Type", "Fit"),
    ("1", r"^program$", PD, "program_name", f"{G}.dim_program.program_name (+ program_name_normalised)", "Program", "Partial"),
    ("1", r"^telecast$", PD, "program_name + airing_datetime + network_label", f"{G}.fct_telecast_supply.telecast_key", "Telecast", "Fit"),
    ("1", r"episode name", PD, "episode_name", f"{G}.fct_telecast_supply.episode_name", "Episode", "Fit"),
    ("1", r"daypart", "marketshare_bronze.dimdaypart", "nntvdaypart / smidaypart / matcheddaypart", f"{G}.dim_daypart", "Daypart", "Fit"),
    ("1", r"demo schema", PV, "*_delivery buckets", f"{G}.dim_demo", "Demo", "Fit"),
    ("", r"portfolio/network", "marketshare_bronze.dimnetwork", "network, networkgroup, networkdivision, ownershipgroup", f"{G}.dim_network", "Network / Network Group", "Fit"),
    ("", r"^ownership", "marketshare_bronze.dimnetwork", "ownershipgroup", f"{G}.dim_network.ownership_group", "Ownership", "Fit"),
    ("", r"reporting status", "marketshare_bronze.dimnetwork", "reportingstatus", f"{G}.dim_network.reporting_status", "segment reporting_networks", "Fit"),
    ("", r"calendar schema|b'calendar|quarter|month|weeks in month|broadcast season|calendar year|leap year", "-", "generated (COMMON.dimDATE as oracle)", f"{G}.dim_broadcast_calendar", "Broadcast / Gregorian calendar", "Build"),
    ("1", r"^is ", PD, None, f"{G}.fct_telecast_supply.<flag>", "flag dimension", "Fit"),
    ("1", r"program start time|air date", TEL, "PROGRAMSTARTTIME / AIRDATE", f"{S}.fct_guideline_telecast_spend", "- (match input)", "Gap"),
    ("1", r"cyclical", "marketshare_bronze.dimnetworkprogramnamemapping", "sport, sporttype, sportbrand, eventtype", f"{G}.dim_program.sport_*", "Sport / Event Type", "Partial"),
    ("2", r"gross media spend", ACC, "GROSSMEDIASPEND (TBC)", f"{G}.fct_category_spend.gross_media_spend", "Gross Media Spend", "Gap"),
    ("2", r"equivalized", ACC, "EQUIVALIZED_30S_SPOT_COUNT (TBC)", f"{G}.fct_category_spend.eq30_spot_count", "EQ30 Spot Count", "Gap"),
    ("2", r"media parent owner", ACC, "MASTEROWNER", f"{G}.fct_category_spend.media_parent_owner", "Media Parent Owner", "Gap"),
    ("2", r"category group", ACC, "PRODUCTCATEGORYGROUP", f"{G}.fct_category_spend.category_group", "Category Group", "Gap"),
    ("2", r"^category$", ACC, "PRODUCTCATEGORY", f"{G}.fct_category_spend.category", "Category", "Gap"),
    ("2", r"subcategory", ACC, "PRODUCTSUBCATEGORY", f"{G}.fct_category_spend.subcategory", "Subcategory", "Gap"),
    ("2", r"spot length", ACC, "SPOTLENGTH (TBC)", f"{G}.fct_category_spend.spot_length", "Spot Length", "Gap"),
    ("2", r"buy type", ACC, "BUYTYPE (TBC)", f"{G}.fct_category_spend.buy_type", "Buy Type", "Gap"),
    ("2", r"^adu", ACC, "ADU (TBC)", f"{G}.fct_category_spend.adu", "ADU", "Gap"),
    ("2", r"media subtype", ACC, "MEDIASUBTYPE (TBC)", f"{G}.fct_category_spend.media_subtype", "Media Subtype", "Gap"),
    ("2", r"daypart", ACC, "daypart (TBC); align via dimdaypart.smidaypart", f"{G}.dim_daypart", "Daypart", "Gap"),
    ("2", r"network \(guideline", ACC, "NETWORK", f"{G}.dim_network via ref_network_crosswalk", "Network", "Gap"),
    ("2", r".", ACC, "(column TBC from file layout, Q-18)", f"{G}.fct_category_spend", "as named", "Gap"),
    ("3", r"estimated spend", "marketshare_bronze.factadintel", "spend", f"{G}.fct_adintel_spend.spend", "Estimated Spend", "Partial"),
    ("3", r"media type", "marketshare_bronze.dimmediatype", "mediatypedescription", f"{G}.fct_adintel_spend.media_type", "Media Type", "Partial"),
    ("3", r"^category", "marketshare_bronze.dimadvertiserbrand", "category / subcategory (+ productmajorcategory)", f"{G}.dim_advertiser_brand", "Category", "Fit"),
    ("3", r"parent company", "marketshare_bronze.dimadvertiserbrand", "advertiserparentdescription", f"{G}.dim_advertiser_brand.parent_company", "Parent Company", "Fit"),
    ("3", r"subsidiary", "marketshare_bronze.dimadvertiserbrand", "advertisersubsidiarydescription", f"{G}.dim_advertiser_brand.subsidiary", "Subsidiary", "Fit"),
    ("3", r"brand", "marketshare_bronze.dimadvertiserbrand", "branddescription", f"{G}.dim_advertiser_brand.brand", "Brand", "Fit"),
    ("3", r"network", "marketshare_bronze.dimnetwork", "via factadintel._networksk", f"{G}.dim_network", "Network", "Partial"),
    ("3", r"program", "marketshare_bronze.dimprogramdescriptor", "program_name / program_type / program_subtype via _programdescriptorsk", f"{G}.dim_program", "Program", "Fit"),
]


def map_field(uc, field):
    f = field.lower().strip()
    for rule_uc, rx, bt, bc, target, cube, status in FIELD_RULES:
        if rule_uc and not uc.startswith(rule_uc):
            continue
        if re.search(rx, f):
            if bc is None:
                col = "is_" + re.sub(r"[^a-z]+", "_", f.replace("is ", "", 1).rstrip("?")).strip("_")
                col = {"is_preliminary": "is_preliminary", "is_team_sports": "is_team_sports"}.get(col, col)
                bc = col
                status = "Fit" if has_col(PD, col) else "Partial"
                target = target.replace("<flag>", col)
            elif bt in BRONZE_COLS and "," not in bc and " " not in bc and not has_col(bt, bc):
                status = "Partial"
            return bt, bc, target, cube, status
    return "-", "-", "TBC", "TBC", "Decision"


def field_rows():
    ws = load_workbook(INTAKE_XLSX, data_only=True)["Metrics_Dims"]
    rows, uc = [], ""
    for r in ws.iter_rows(min_row=2, values_only=True):
        a, b, c, d, e, f, g, h, i, j = (list(r) + [None] * 10)[:10]
        if a not in (None, ""):
            uc = str(a)
        field = c or (b if b and str(b).lower() not in ("metric", "dimension", "dimension(s)") else None)
        if not field:
            continue
        bt, bc, target, cube, status = map_field(uc, str(field))
        rows.append((uc, b or "", str(field).strip(), d or "", bt, bc, target, cube, status,
                     (str(i) if i else "")[:300], (str(j) if j else "")[:300]))
    return rows


# ---------------------------------------------------------------------------
# Workbook
# ---------------------------------------------------------------------------
def build_workbook(path):
    wb = Workbook()
    wb.remove(wb.active)
    frows = field_rows()
    fit = sum(1 for r in frows if r[8] == "Fit")
    gap = sum(1 for r in frows if r[8] == "Gap")
    build = sum(1 for r in frows if r[8] == "Build")

    readme = [
        ("Jira", f"Story CARL-3776 Research Market Share Data Discovery ({K.JIRA_STORY}), epic CARL-3775 Research Market Share Insight BI Support ({K.JIRA_EPIC}). Sprint: CARL Sprint 19."),
        ("Purpose", "Initial full-scale data requirement gathering for intake Use Case 3(a) Marketplace Performance Tracking (MarketShare + Guideline/SMI + VAMI). Covers priority needs, the Iceberg remodel, the Cube semantic layer, the data quality plan, open decisions and proposed stories."),
        ("Acceptance criteria -> sheets", "1 Identify priority needs -> 'Priority Needs'. 2 How to remodel in Iceberg -> 'Iceberg Target Model', 'Iceberg Practices', 'Field Mapping', 'Business Rules', 'Cube Views', 'Cube Measures'. 3 Ensure data quality -> 'Data Quality Plan'."),
        ("Prepared", f"{date.today():%d %b %Y}, generated by marketshare-research-discovery/build_workbook.py"),
        ("Evidence", "; ".join([K.INTAKE, K.CONF_MS, K.CONF_VAMI, K.CONF_SMI2, K.CONF_MIT2, K.CONF_FP, K.CONF_FA, K.CONF_S3, K.CATALOG, K.COLUMNS])),
        ("Not reached this pass", "Live Athena profiling (row counts, duplicate counts, date ranges) was not run. The DQ checks are written so they can be run as-is once access is confirmed. AccuTV and Guideline Telecast file layouts are not documented anywhere."),
        ("Field coverage", f"{len(frows)} fields from the intake Metrics_Dims tab: {fit} Fit on CARL Bronze today, {gap} Gap (source not in CARL: all Guideline), {build} Build (calendar, generated in CARL), rest Partial/Proposed/Decision."),
        ("Other Quick asks on CARL-3776", "(1) SMI + Cube market share remodel to Quick: this workbook. (2) NextGen dashboard to Quick: nextgen-research-discovery/ (shares dim_broadcast_calendar and dim_network). (3) Time buy Looker report to Quick: no intake yet (Q-16)."),
        ("Target names", f"{K.BRONZE}, {K.SILVER}, {K.GOLD}, mit_panel_bronze and all table names are PROPOSED and need CARL DE naming sign-off."),
        ("Registry", "Proposed products MSI-* and Cube views marketplace_view_* were added to iceberg-catalog-agent/registry (status: proposed), so the weekly catalog lists them."),
        ("Status legend", "Fit = available in CARL Bronze today. Build = generated in CARL, no source needed. Partial = available but needs logic/confirmation. Gap = source not in CARL. Decision = blocked on a question. Proposed = design recommendation."),
        ("Companion file", "MarketShare_Research_Iceberg_Cube_Lineage.md: target lineage, Gold ERD, DQ gate (Mermaid)."),
    ]
    sheet(wb, "Read Me", "Scope, evidence and how to read this workbook", ["Item", "Detail"], readme, [28, 150])
    sheet(wb, "Priority Needs", "Acceptance criterion 1: the intake's priority needs, ranked, with the CARL response",
          ["ID", "Priority", "Need", "Intake ref", "Why this priority", "CARL response (Iceberg / Cube / DQ)", "Pipeline"],
          K.PRIORITIES, [7, 9, 44, 26, 60, 80, 9], status_col=1)
    sheet(wb, "Key Findings", "What discovery found that changes the plan",
          ["ID", "Finding", "Evidence", "So what / action", "Source", "Confidence"], K.FINDINGS, [7, 40, 80, 70, 36, 12])
    sheet(wb, "Source Inventory", "Every source in the intake: where it is today, whether CARL has it, and what to do",
          ["ID", "Source", "Vendor", "Current location", "In CARL Iceberg today", "Preferred access", "Trust", "Cadence / lag", "Revisions", "History", "Disposition"],
          K.SOURCES, [6, 24, 14, 60, 44, 20, 14, 30, 34, 18, 50])
    sheet(wb, "Iceberg Target Model", "Acceptance criterion 2: Bronze / Silver / Gold tables, grain, keys, partitioning and write strategy",
          ["Layer", "Table", "Grain", "Key", "Sources", "Partition spec", "Write mode", "Retention / snapshots", "Pipeline", "Status"],
          K.ICEBERG, [8, 46, 50, 40, 50, 26, 30, 32, 8, 18], status_col=9)
    sheet(wb, "Iceberg Practices", "Iceberg features used and the need each one serves",
          ["Practice", "How", "Serves", "Status"], K.ICEBERG_PRACTICES, [26, 110, 16, 30])
    sheet(wb, "Field Mapping", "Every field in intake Metrics_Dims mapped to its Bronze source, Iceberg target and Cube member",
          ["Use case", "Type", "Intake field", "Priority", "Bronze table", "Bronze column(s)", "Iceberg target", "Cube member", "Status", "Known nuances (intake)", "Open questions (intake)"],
          frows, [8, 11, 32, 8, 38, 36, 48, 28, 10, 50, 40], status_col=8)
    sheet(wb, "Business Rules", "Rules to implement, with the evidence each comes from",
          ["ID", "Rule", "Logic", "Source", "Implemented in", "Status"], K.RULES, [7, 30, 90, 26, 34, 28], status_col=5)
    sheet(wb, "Cube Views", "Proposed Cube semantic layer over Gold (to be added to carl-semantic-layer once Gold exists)",
          ["View", "Source tables", "Grain", "Measures", "Dimensions", "Segments", "Audience / access", "Pipeline"],
          K.CUBE_VIEWS, [36, 50, 34, 70, 80, 36, 34, 8])
    sheet(wb, "Cube Measures", "Measure catalog: definition, expression, aggregation",
          ["Measure", "Cube view", "KPI class", "Definition", "Expression", "Aggregation", "Note"],
          K.CUBE_MEASURES, [28, 36, 14, 60, 56, 14, 30])
    sheet(wb, "Data Quality Plan", "Acceptance criterion 3: checks by layer. Blocker checks gate the Gold publish (write-audit-publish)",
          ["ID", "Layer", "Object", "Check", "Rule", "Threshold", "Severity", "On failure"],
          K.DQ, [7, 10, 30, 26, 80, 36, 18, 44], status_col=6)
    sheet(wb, "Looker -> CARL Layers", f"Every explore/view in {K.LOOKER_SRC} mapped to Bronze / Silver / Gold / Cube",
          ["Looker object", "Kind", "What it is", "Verdict", "Bronze", "Silver", "Gold / Cube", "Note"],
          K.LOOKER, [44, 9, 44, 18, 36, 44, 50, 70], status_col=3)
    sheet(wb, "Open Questions", "Decisions needed, owner, what they block, and the default if no answer comes back",
          ["ID", "Question", "Owner", "Blocks", "Proposed default"], K.QUESTIONS, [7, 90, 34, 24, 60])
    sheet(wb, "Proposed Stories", "Backlog proposal for epic CARL-3775 (sizes are first-pass story points)",
          ["ID", "Story", "Pipeline", "Layer", "Depends on", "Acceptance", "Points"], K.STORIES, [8, 70, 9, 14, 24, 70, 8])
    wb.save(path)
    return len(frows), fit, gap


# ---------------------------------------------------------------------------
# Lineage / ERD doc
# ---------------------------------------------------------------------------
LINEAGE = f"""```mermaid
flowchart LR
  subgraph SRC[Sources]
    GT[Guideline Telecast<br/>S3 txt.gz monthly]
    GA[Guideline AccuTV<br/>S3 txt.gz monthly]
    MP[Nielsen MIT Panel Only<br/>AMS_ICUE_SHARE.MIT]
    MB[Nielsen Big MIT<br/>SHARE_PROD_BIG_MIT]
    MS[MarketShare<br/>AMS BI, weekly]
    TX[Research taxonomy<br/>MarketShare S3 rules engine]
  end
  subgraph BR[CARL Bronze - Iceberg]
    GB[{K.BRONZE}<br/>telecast_delivery, accutv_delivery, delivery_manifest]:::gap
    PB[mit_panel_bronze]:::gap
    BB[big_mit_bronze - Prod]:::ok
    MSB[marketshare_bronze - Prod<br/>factadintel, factprogram, dims]:::ok
  end
  subgraph SV[{K.SILVER}]
    CAL[dim_broadcast_calendar]
    DN[dim_network SCD2 + ref_network_crosswalk]
    DP[dim_program_taxonomy]
    C3[fct_mit_telecast_c3]
    GS[fct_guideline_telecast_spend + bounce]
    GAS[fct_guideline_accutv_spend]
    MT[match_telecast_guideline_mit]
    AI[fct_adintel_occurrence]
  end
  subgraph GD[{K.GOLD} - published by WAP]
    SUP[fct_telecast_supply]
    DEM[fct_telecast_demand]
    CAT[fct_category_spend]
    ADS[fct_adintel_spend]
    DQ[dq_results + data_freshness]
  end
  subgraph SEM[Cube]
    V1[marketplace_view_telecast_supply_demand]
    V2[marketplace_view_category_spend]
    V3[marketplace_view_adintel_spend / _sales]
    V4[marketplace_view_data_freshness]
  end
  Q[Amazon Quick<br/>dashboards + AI chat]
  GT --> GB
  GA --> GB
  MP --> PB
  MB --> BB
  MS --> MSB
  TX --> MS
  GB --> GS
  GB --> GAS
  PB --> C3
  BB --> C3
  MSB --> DN
  MSB --> DP
  MSB --> AI
  C3 --> MT
  GS --> MT
  DN --> MT
  C3 --> SUP
  MT --> DEM
  GS --> DEM
  GAS --> CAT
  AI --> ADS
  DP --> SUP
  CAL --> SUP
  SUP --> V1
  DEM --> V1
  CAT --> V2
  ADS --> V3
  DQ --> V4
  V1 --> Q
  V2 --> Q
  V3 --> Q
  V4 --> Q
  classDef ok fill:#C6EFCE,stroke:#2e7d32
  classDef gap fill:#FFC7CE,stroke:#c62828
```"""

ERD = """```mermaid
erDiagram
  dim_broadcast_calendar ||--o{ fct_telecast_supply : broadcast_date
  dim_network ||--o{ fct_telecast_supply : network_key
  dim_program ||--o{ fct_telecast_supply : program_key
  dim_demo ||--o{ fct_telecast_supply : demo_code
  fct_telecast_supply ||--o{ fct_telecast_demand : telecast_key
  dim_network ||--o{ fct_category_spend : network_key
  dim_broadcast_calendar ||--o{ fct_category_spend : air_date
  dim_network ||--o{ fct_adintel_spend : network_key
  dim_program ||--o{ fct_adintel_spend : program_key
  dim_advertiser_brand ||--o{ fct_adintel_spend : advertiser_brand_key
  dim_broadcast_calendar ||--o{ fct_adintel_spend : ad_date
  fct_telecast_supply {
    string telecast_key PK
    string demo_code PK
    date broadcast_date
    timestamp airing_minute
    string viewing_methodology
    double gross_impressions
    int commercial_program_duration
    int duration
    boolean is_breakout
    boolean is_short_duration
  }
  fct_telecast_demand {
    string telecast_key FK
    string buy_type
    string adu
    int spot_length
    decimal gross_media_spend
    double eq30_spot_count
    string delivery_id
    int match_offset_minutes
  }
  dim_network {
    string network_key PK
    string network_label
    string network
    string ownership_group
    string network_type
    boolean reporting_status
    date effective_from
    date effective_to
  }
  fct_adintel_spend {
    date ad_date
    string network_key FK
    string program_key FK
    string advertiser_brand_key FK
    string media_type
    int duration
    decimal spend
    int units
    boolean is_static_segment
  }
```"""

GATE = """```mermaid
flowchart LR
  L[File lands] --> C{Schema contract<br/>DQ-02/03}
  C -- fail --> QZ[Quarantine + alert]
  C -- pass --> B[Bronze append<br/>partition = delivery_id]
  B --> S[Silver build on audit branch]
  S --> T{Blocker checks<br/>DQ-08,09,11,12,14,15,17,21}
  T -- fail --> A[Alert, main unchanged,<br/>Quick shows last good data]
  T -- pass --> P[Fast-forward main<br/>update data_freshness]
  P --> R[Weekly audit + monthly +/-3% reconciliation]
```"""


def build_md(path, n, fit, gap):
    p0 = [p for p in K.PRIORITIES if p[1] == "P0"]
    lines = [
        "# Research Market Share: Iceberg + Cube discovery",
        "",
        f"Jira: [CARL-3776]({K.JIRA_STORY}) (epic [CARL-3775]({K.JIRA_EPIC})). Generated {date.today():%d %b %Y} by `build_workbook.py`; detail in `MarketShare_Research_Discovery_Iceberg_Cube.xlsx`.",
        "",
        "## Priority needs (P0)",
        "",
    ]
    lines += [f"- **{p[0]} {p[2]}**: {p[5]}" for p in p0]
    lines += ["", f"Field coverage from the intake: {n} fields, {fit} available on CARL Bronze today, {gap} blocked on Guideline landing.", "",
              "## Target lineage", "", "Green = in CARL Prod today, red = not yet landed.", "", LINEAGE, "",
              "## Gold ERD", "", ERD, "", "## Data quality gate", "", GATE, "",
              "## Decisions needed first", ""]
    lines += [f"- **{q[0]}** {q[1]} ({q[2]})" for q in K.QUESTIONS[:8]]
    open(path, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    xlsx = os.path.join(OUT, "MarketShare_Research_Discovery_Iceberg_Cube.xlsx")
    md = os.path.join(OUT, "MarketShare_Research_Iceberg_Cube_Lineage.md")
    n, fit, gap = build_workbook(xlsx)
    build_md(md, n, fit, gap)
    print(f"wrote {xlsx}\nwrote {md}\nfields={n} fit={fit} gap={gap}")
