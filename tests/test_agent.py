"""Tests for the MSTR inventory agent.

Focus is on the properties the inventory is trusted for: identifier stability and uniqueness,
correct classification, and no silent row loss between export and workbook.
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mstr_inventory_agent import build, classify, describe, identity  # noqa: E402


# --------------------------------------------------------------------------- identifiers

def test_ids_are_deterministic():
    a = identity.object_id("RPT", "Report", "\\Public Objects\\Reports", "Revenue")
    b = identity.object_id("RPT", "Report", "\\Public Objects\\Reports", "Revenue")
    assert a == b
    assert a.startswith("RPT-") and len(a) == 16


def test_ids_ignore_trailing_separator_and_whitespace():
    a = identity.object_id("RPT", "Report", "\\Public Objects\\Reports\\", " Revenue ")
    b = identity.object_id("RPT", "Report", "\\Public Objects\\Reports", "Revenue")
    assert a == b


def test_ids_distinguish_case_and_internal_spacing():
    """MSTR allows siblings differing only by case or spacing; they must not collide."""
    a = identity.object_id("RPT", "Report", "\\P", "Capacities cal")
    b = identity.object_id("RPT", "Report", "\\P", "Capacities Cal")
    c = identity.object_id("RPT", "Report", "\\P", "Capacities  cal")
    assert len({a, b, c}) == 3


def test_ids_differ_across_object_types_and_folders():
    assert (identity.object_id("MTRC", "Metric", "\\P", "Revenue")
            != identity.object_id("ATTR", "Attribute", "\\P", "Revenue"))
    assert (identity.object_id("RPT", "Report", "\\A", "Revenue")
            != identity.object_id("RPT", "Report", "\\B", "Revenue"))


def test_surrogate_guid_shape():
    g = identity.surrogate_guid("Report", "\\P", "Revenue")
    assert len(g) == 32 and g == g.upper()
    assert all(ch in "0123456789ABCDEF" for ch in g)


def test_full_path_joins_without_double_separator():
    assert identity.full_path("\\Public Objects\\", "X") == "\\Public Objects\\X"
    assert identity.full_path(None, "X") == "X"


# --------------------------------------------------------------------------- classification

@pytest.mark.parametrize("path,expected", [
    ("\\Public Objects\\Reports\\Finance Shared Reports\\A", "Shared (Public Objects)"),
    ("\\Profiles\\Jane Doe (jdoe)\\My Reports", "Personal (My Reports/My Objects)"),
    ("\\Administrator (Administrator)\\My Reports", "Administrator personal"),
    ("\\US AdSales Reporting\\Schema Objects\\Tables", "Schema (shared)"),
    ("\\Object Templates", "Object template"),
])
def test_location(path, expected):
    assert classify.location(path) == expected


def test_owner_parsed_from_profile_path():
    p = "\\Profiles\\Krawchuk, Susan (SKrawchuk)\\My Reports"
    assert classify.owner(p) == "Krawchuk, Susan"
    assert classify.owner_login(p) == "SKrawchuk"


def test_shared_objects_have_no_single_owner():
    assert classify.owner("\\Public Objects\\Reports\\Finance Shared Reports") is None


def test_business_area_maps_known_folder():
    p = "\\Public Objects\\Reports\\Finance Shared Reports\\Billing"
    assert classify.business_area(p) == "Finance"


def test_business_area_falls_back_to_folder_name():
    p = "\\Public Objects\\Reports\\Some New Team Folder\\X"
    assert classify.business_area(p) == "Some New Team Folder"


def test_dashboard_detected_from_folder():
    p = "\\Public Objects\\Reports\\Executive Summary Dashboards\\Sales Revenue Analysis"
    assert classify.deliverable_class("Advertiser Trend", "Grid Report", p) == "Dashboard"


def test_cube_classified_as_data_asset():
    p = "\\Public Objects\\Reports\\Finance Shared Reports"
    assert classify.deliverable_class("Rev Cube", "Intelligent Cube", p) == "Data asset / cube"


@pytest.mark.parametrize("name,env", [
    ("AS-WH-PRD", "PROD"), ("AS-WH-DEV", "DEV"), ("AMS-WH-TST", "TEST/QA"),
    ("Lake5", "Unclassified"),
])
def test_environment_inference(name, env):
    assert classify.environment(name) == env


def test_name_variant_detection():
    assert classify.name_variant("AS-WH-DEV (1)") == ("AS-WH-DEV", True)
    assert classify.name_variant("AS-WH-DEV") == ("AS-WH-DEV", False)


@pytest.mark.parametrize("name,desc,expected", [
    ("Amazon S3", "amazons3", "MSTR platform connector"),
    ("Data Import External Twitter", "Data Import External Twitter DBRole",
     "MSTR platform connector"),
    ("workdayE88B20C1F30443E0AA8DEA709F2356BC", "This is a system defined DB instance",
     "MSTR platform connector"),
    ("Statistics", "Created by Configuration Wizard for Default Staging Repository",
     "MSTR platform connector"),
    ("NMA-WH-PRD", "New Media Analytics Prod WH Server Connection", "Configured data source"),
    ("AS-WH-PRD", None, "Configured data source"),
    ("SymphonyAMDB", "SymphonyAMDB", "Configured data source"),
])
def test_datasource_class(name, desc, expected):
    assert classify.datasource_class(name, desc) == expected


def test_clean_description_strips_doc_payload():
    raw = "Connect to marketing data#DESCRIPTION#INTRODUCTION#https://example.com"
    assert classify.clean_description(raw) == "Connect to marketing data"


# --------------------------------------------------------------------------- descriptions

def test_report_description_is_a_sentence():
    d = describe.describe_report(
        "Booked Revenue by Daypart", "Grid Report",
        "\\Public Objects\\Reports\\Finance Shared Reports\\Revenue")
    assert d.endswith(".") and d[0].isupper()
    assert "Finance" in d and "daypart" in d.lower()


def test_personal_report_description_flags_governance():
    d = describe.describe_report(
        "My Scratch", "Grid Report", "\\Profiles\\Jane Doe (jdoe)\\My Reports")
    assert "Jane Doe" in d and "personal" in d.lower()


def test_glossary_prefers_longest_match():
    d = describe.describe_object(
        "ACM7 Delivery", "Metric", "\\Public Objects\\Metrics\\Booked Impressions and CPM")
    assert "7-day" in d


def test_table_class_inference():
    assert describe.table_class("INVOICE_REVENUE_FACT") == "Fact"
    assert describe.table_class("NETWORK_DIM") == "Dimension"
    assert describe.table_class("ABS_ADJACTUALS_PIVOT") == "Pivot / staging"


def test_table_variant_description_flags_duplicate():
    d = describe.describe_table("ACCOUNT_PROPERTY_CATEGORY_DIM (1)", "\\p",
                                "ACCOUNT_PROPERTY_CATEGORY_DIM")
    assert "duplicate" in d.lower()


# --------------------------------------------------------------------------- build

def _frames():
    return {
        "reports": pd.DataFrame({
            "Name": ["Rev A", "Rev A", "Exec View"],
            "Type": ["Grid Report", "Grid Report", "Graph Report"],
            "Folder": ["\\Public Objects\\Reports\\Finance Shared Reports",
                       "\\Profiles\\Jane Doe (jdoe)\\My Reports",
                       "\\Public Objects\\Reports\\Executive Summary Dashboards\\Exec"],
            "Hidden": ["False", "False", "False"],
        }),
        "metrics": pd.DataFrame({
            "Name": ["Booked Revenue"],
            "Path": ["\\Public Objects\\Metrics\\Booked Revenue"],
            "Hidden": ["False"],
            "__source_file": ["metrics_usaddsales.xls"],
        }),
        "metrics_target_demo": pd.DataFrame({
            "Name": ["Booked Revenue"],
            "Path": ["\\Public Objects\\Metrics\\Booked Revenue"],
            "Hidden": ["False"],
            "__source_file": ["metrics_Target Demographic_folder.xls"],
        }),
        "dbinstances": pd.DataFrame({
            "Database Instance": ["AS-WH-PRD", "Amazon S3"],
            "Owner": ["Administrator", "Administrator"],
            "Modification Time": [None, None],
            "Description": [None, "amazons3"],
        }),
    }


def test_master_has_one_row_per_object_and_unique_ids():
    m = build.build_master(_frames())
    # 3 reports + 1 deduplicated metric + 2 db instances
    assert len(m) == 6
    assert m["Object ID"].is_unique
    assert m["Surrogate GUID"].is_unique


def test_overlapping_metric_exports_are_deduplicated_with_provenance():
    m = build.build_master(_frames())
    metric = m[m["Object Type"] == "Metric"]
    assert len(metric) == 1
    src = metric["Source File"].iloc[0]
    assert "metrics_usaddsales.xls" in src
    assert "metrics_Target Demographic_folder.xls" in src


def test_duplicate_name_flagged_across_shared_and_personal():
    m = build.build_master(_frames())
    rev = m[m["Object Name"] == "Rev A"]
    assert len(rev) == 2
    assert set(rev["Duplicate Name"]) == {"Yes"}
    assert rev["Object ID"].nunique() == 2


def test_every_object_gets_a_description():
    m = build.build_master(_frames())
    assert m["Description"].notna().all()
    assert m["Description Source"].notna().all()


def test_mstr_guid_column_is_reserved_and_empty():
    m = build.build_master(_frames())
    assert "MSTR GUID" in m.columns
    assert m["MSTR GUID"].isna().all()


def test_id_uniqueness_is_enforced_even_on_collision(monkeypatch):
    monkeypatch.setattr(build.identity, "object_id", lambda *a, **k: "RPT-COLLIDE")
    monkeypatch.setattr(build.identity, "surrogate_guid", lambda *a, **k: "A" * 32)
    m = build.build_master(_frames())
    assert m["Object ID"].is_unique
