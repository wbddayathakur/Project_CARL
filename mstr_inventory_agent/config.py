"""Source file registry and shared vocabulary for the US Ad Sales MSTR inventory."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

DEFAULT_SOURCE_DIR = (
    "/Users/dthakur/Library/CloudStorage/OneDrive-WarnerBros.Discovery/Documents/"
    "CARL - MSTR/US Ad Sales Reports- MSTR"
)

DEFAULT_OUTPUT_NAME = "CARL_USAdSales_MSTR_Master_Inventory.xlsx"


@dataclass
class SourceSpec:
    """One MicroStrategy export feeding the inventory."""

    key: str
    filename: str
    object_type: str
    id_prefix: str
    name_col: str
    path_col: Optional[str] = None
    extra_cols: List[str] = field(default_factory=list)
    required: bool = True


SOURCES: Dict[str, SourceSpec] = {
    s.key: s
    for s in [
        SourceSpec("reports", "reports_usaddsales.xls", "Report", "RPT", "Name", "Folder",
                   ["Type", "Hidden"]),
        SourceSpec("attributes", "attributes_usaddsales.xls", "Attribute", "ATTR", "Name", "Path",
                   ["Hidden"]),
        SourceSpec("metrics", "metrics_usaddsales.xls", "Metric", "MTRC", "Name", "Path",
                   ["Hidden"]),
        SourceSpec("metrics_target_demo", "metrics_Target Demographic_folder.xls", "Metric",
                   "MTRC", "Name", "Path", ["Hidden"]),
        SourceSpec("filters", "filters_usaddsales.xls", "Filter", "FLTR", "Name", "Path",
                   ["Hidden"]),
        SourceSpec("tables", "tables_usaddsales.xls", "Table", "TBL", "Name", "Path",
                   ["Warehouse Table Name"]),
        SourceSpec("dbinstances", "dbinstances.xls", "Database Instance", "DBI",
                   "Database Instance", None, ["Owner", "Modification Time", "Description"]),
        SourceSpec("dbconnections", "dbconnections.xls", "Database Connection", "DBC",
                   "Database Connection", None, []),
    ]
}

# Prior hand-analysed workbook. Sheets listed here are carried forward verbatim because they
# contain fact/dimension analysis that is absent from the raw exports.
DRAFT_FILENAME = "CARL_USAdSales_Inventory_Validated - Draft.xlsx"
DRAFT_CARRY_FORWARD_SHEETS = ["Fact-Dimension Join Map", "Fact x Dim Matrix"]


# Second path segment under \Public Objects\Reports\ -> owning business area.
BUSINESS_AREA_BY_FOLDER = {
    "Finance Shared Reports": "Finance",
    "S3 Shared Reports": "S3 (Sales Support Systems)",
    "Sports Pricing & Planning Shared Reports": "Sports Pricing & Planning",
    "Ad Sales Planning and Operations Shared Reports": "Ad Sales Planning & Operations",
    "Revenue Strategy & Analytics Shared Folder": "Revenue Strategy & Analytics",
    "Executive Summary Dashboards": "Executive Reporting",
    "IT Shared Reports": "IT",
    "USN Ad Sales Accounting Shared Reports": "USN Ad Sales Accounting",
    "Direct Response Shared Reports": "Direct Response",
    "Ad Sales Research Shared Reports": "Ad Sales Research",
    "Revenue Analysis": "Revenue Analysis",
    "USN Content Reporting": "USN Content Reporting",
    "CNNI Reports": "CNNI",
    "Ad Sales Proposals Shared Reports": "Ad Sales Proposals",
    "Revenue Ranking": "Revenue Analysis",
    "Revenue Evaluation": "Revenue Analysis",
    "Inventory Reports": "Inventory & Capacity",
    "USH Nets Shared Reports for DLA Sales": "USH Nets / DLA Sales",
    "Sold LOA Reports": "Sold LOA",
    "Commercial Operations Shared Reports": "Commercial Operations",
    "Rating Reports": "Ad Sales Research",
    "Ad Sales Support Shared Folder": "Ad Sales Support",
    "BBCA DR Shared Reports Folder": "Direct Response",
    "DLA Kids Shared Folder": "USH Nets / DLA Sales",
    "USH Nets Shared Reports for DLA Finance": "USH Nets / DLA Finance",
    "Revenue Activity Report": "Revenue Analysis",
}

# Domain glossary used to compose derived descriptions. Ordered longest-first at match time so
# that multi-word phrases win over their component words.
TERM_GLOSSARY = {
    "booked impressions": "booked audience impressions",
    "booked revenue": "booked revenue",
    "projected/working": "projected/working (pipeline) figures",
    "projected working": "projected/working (pipeline) figures",
    "invoiced": "invoiced (actualised) revenue",
    "unit level actual": "unit-level actual delivery",
    "avg unit rate": "average unit rate",
    "unit rate": "unit rate",
    "sell out": "sell-out / capacity utilisation",
    "sellout": "sell-out / capacity utilisation",
    "market track": "market tracking",
    "rateclass": "rate class",
    "equiv30": "30-second equivalent units",
    "make good": "make-good spots",
    "makegood": "make-good spots",
    "cpm": "CPM (cost per thousand)",
    "cpp": "CPP (cost per point)",
    "acm7": "ACM7 (average commercial minute, 7-day)",
    "acm": "ACM (average commercial minute)",
    "ecm": "ECM (equivalent commercial minute)",
    "pal": "PAL (program average load) delivery",
    "guar/target": "guarantee vs target delivery",
    "guarantee": "audience guarantee",
    "impressions": "audience impressions",
    "ratings": "Nielsen ratings",
    "demo": "demographic",
    "demographic": "demographic",
    "daypart": "daypart",
    "telecast": "telecast",
    "program": "program",
    "network": "network",
    "advertiser": "advertiser",
    "agency": "agency",
    "brand": "brand",
    "property": "property",
    "inventory": "inventory / capacity",
    "capacity": "inventory / capacity",
    "pacing": "pacing",
    "scatter": "scatter market",
    "upfront": "upfront market",
    "pending": "pending business",
    "backlog": "backlog",
    "snapshot": "point-in-time snapshot",
    "forecast": "forecast",
    "budget": "budget",
    "variance": "variance",
    "ranking": "ranking",
    "trend": "trend analysis",
    "pivot": "pivoted source extract",
    "billing": "billing",
    "invoice": "invoicing",
    "deal": "deal",
    "order": "order",
    "proposal": "proposal",
    "spot": "commercial spot",
    "pod": "commercial pod",
    "loa": "LOA (letter of agreement)",
    "bap": "BaP (Booked-as-Placed) extract",
    "dr": "Direct Response",
    "sox": "SOX compliance",
    "audit": "audit",
    "reconciliation": "reconciliation",
    "recon": "reconciliation",
    "export": "data export",
    "extract": "data extract",
    "dashboard": "dashboard",
    "summary": "summary",
    "detail": "detail-level",
    "weekly": "weekly",
    "monthly": "monthly",
    "quarterly": "quarterly",
    "yearly": "annual",
    "ytd": "year-to-date",
    "qtd": "quarter-to-date",
}

# Report/dashboard classification hints.
DASHBOARD_NAME_HINTS = ("dashboard", "scorecard", "executive summary", "dossier")

# Environment inference for database connections and instances.
ENV_PATTERNS = [
    ("PROD", ("-prd", "-prod", " prd", " prod", "production", "_prd", "prd_")),
    ("DEV", ("-dev", " dev", "development", "_dev", "dev_")),
    ("TEST/QA", ("-tst", "-test", " tst", " test", " qa", "-qa", "_tst", "_qa")),
    ("UAT", ("-uat", " uat", "_uat")),
]

LEGACY_OWNER_MARKERS = ("_legacy", "legacy")
