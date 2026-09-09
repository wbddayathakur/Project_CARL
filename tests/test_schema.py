"""Tests for the logical schema view.

These lock the properties the schema sheets are trusted for: correct table classification, an
edge list that matches the bus matrix exactly, conformance arithmetic, and attribute lineage
that never overstates its confidence.
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mstr_inventory_agent import build, describe, diagram, schema  # noqa: E402


# --------------------------------------------------------------------------- fixtures

def _master():
    frames = {
        "tables": pd.DataFrame({
            "Name": ["INVOICE_REVENUE_FACT", "RATINGS_FACT", "NETWORK_DIM", "ADVERTISER_DIM",
                     "TELECAST_DIM", "RETIRED_DIM", "CORP_EPISODE_VW",
                     "ACCOUNT_PROPERTY_CATEGORY_DIM (1)"],
            "Path": ["\\US AdSales Reporting\\Schema Objects\\Tables"] * 8,
            "Warehouse Table Name": ["INVOICE_REVENUE_FACT", "RATINGS_FACT", "NETWORK_DIM",
                                     "ADVERTISER_DIM", "TELECAST_DIM", "RETIRED_DIM",
                                     "CORP_EPISODE_VW", "ACCOUNT_PROPERTY_CATEGORY_DIM"],
        }),
        "attributes": pd.DataFrame({
            "Name": ["Advertiser Name", "Network", "ABS Advertiser", "A Or Z Spot Indicator"],
            "Path": ["\\Schema Objects\\Attributes\\Deal and Order",
                     "\\Schema Objects\\Attributes\\Network",
                     "\\Schema Objects\\Attributes\\ABS Data Directly From Source",
                     "\\Schema Objects\\Attributes\\USN"],
            "Hidden": ["False"] * 4,
        }),
    }
    return build.build_master(frames)


def _draft():
    return {
        "Fact x Dim Matrix": pd.DataFrame({
            "Dimension \\ Fact": ["NETWORK_DIM", "ADVERTISER_DIM", "TELECAST_DIM"],
            "INVOICE_REVENUE": ["X", "X", None],
            "RATINGS": ["X", None, "X"],
        }),
        "Fact-Dimension Join Map": pd.DataFrame({
            "Fact Table": ["INVOICE_REVENUE_FACT", "RATINGS_FACT"],
            "Business Area": ["Finance – Actual invoiced revenue", "Research – Ratings"],
            "Key Grain / Notes": ["148.6M rows", "Demo heavy"],
            "Confidence": ["High", "Medium"],
        }),
    }


@pytest.fixture
def ctx():
    m = _master()
    d = _draft()
    edges = schema.fact_dimension_edges(d, m)
    return m, d, edges


# --------------------------------------------------------------------------- classification

@pytest.mark.parametrize("name,expected", [
    ("INVOICE_REVENUE_FACT", "Fact"),
    ("NETWORK_DIM", "Dimension"),
    ("ABS_ADJACTUALS_PIVOT", "Pivot / staging"),
    ("CORP_EPISODE_VW", "View"),
    ("ACCOUNT_PROPERTY_CATEGORY_DIM (1)", "Dimension"),
])
def test_table_class(name, expected):
    assert describe.table_class(name) == expected


@pytest.mark.parametrize("name,stem", [
    ("ADVERTISER_DIM", "ADVERTISER"),
    ("INVOICE_REVENUE_FACT", "INVOICE_REVENUE"),
    ("ACCOUNT_PROPERTY_CATEGORY_DIM (1)", "ACCOUNT_PROPERTY_CATEGORY"),
    ("CORP_EPISODE_VW", "CORP_EPISODE"),
])
def test_table_stem(name, stem):
    assert schema.table_stem(name) == stem


# --------------------------------------------------------------------------- edges

def test_edges_match_the_bus_matrix_cell_for_cell(ctx):
    _, _, edges = ctx
    assert len(edges) == 4  # three X marks on INVOICE_REVENUE/RATINGS columns
    pairs = set(zip(edges["Fact Table"], edges["Dimension Table"]))
    assert pairs == {
        ("INVOICE_REVENUE_FACT", "NETWORK_DIM"),
        ("INVOICE_REVENUE_FACT", "ADVERTISER_DIM"),
        ("RATINGS_FACT", "NETWORK_DIM"),
        ("RATINGS_FACT", "TELECAST_DIM"),
    }


def test_matrix_column_headers_expand_to_full_fact_names(ctx):
    _, _, edges = ctx
    assert all(f.endswith("_FACT") for f in edges["Fact Table"])


def test_edges_carry_business_area_and_confidence_from_join_map(ctx):
    _, _, edges = ctx
    inv = edges[edges["Fact Table"] == "INVOICE_REVENUE_FACT"].iloc[0]
    assert inv["Confidence"] == "High"
    assert "Finance" in inv["Business Area"]


def test_edges_flag_dimensions_missing_from_the_tables_export():
    m = _master()
    draft = _draft()
    draft["Fact x Dim Matrix"].loc[3] = ["PHANTOM_DIM", "X", None]
    edges = schema.fact_dimension_edges(draft, m)
    phantom = edges[edges["Dimension Table"] == "PHANTOM_DIM"]
    assert phantom["Dimension Exists In Export"].iloc[0] == "No"


def test_missing_draft_degrades_gracefully():
    edges = schema.fact_dimension_edges({}, _master())
    assert edges.empty
    assert schema.star_schema_map(edges, {}).empty


# --------------------------------------------------------------------------- conformance

def test_conformance_counts_facts_per_dimension(ctx):
    m, _, edges = ctx
    conf = schema.dimension_conformance(edges, m)
    by_dim = conf.set_index("Dimension Table")
    assert by_dim.loc["NETWORK_DIM", "Facts Using It"] == 2
    assert by_dim.loc["NETWORK_DIM", "Classification"] == "Conformed (shared)"
    assert by_dim.loc["TELECAST_DIM", "Classification"] == "Private to one fact"


def test_unlinked_dimension_is_reported(ctx):
    m, _, edges = ctx
    conf = schema.dimension_conformance(edges, m)
    retired = conf[conf["Dimension Table"] == "RETIRED_DIM"].iloc[0]
    assert retired["Facts Using It"] == 0
    assert retired["Classification"] == "Unlinked / possibly retired"


def test_star_map_splits_conformed_and_private(ctx):
    _, d, edges = ctx
    star = schema.star_schema_map(edges, d)
    inv = star[star["Fact Table"] == "INVOICE_REVENUE_FACT"].iloc[0]
    assert inv["Dimensions"] == 2
    assert inv["Conformed Dimensions"] == 1   # NETWORK_DIM
    assert inv["Private Dimensions"] == 1     # ADVERTISER_DIM
    assert inv["Key Grain / Notes"] == "148.6M rows"


def test_star_map_dimension_counts_reconcile_with_edges(ctx):
    _, d, edges = ctx
    star = schema.star_schema_map(edges, d)
    assert star["Dimensions"].sum() == len(edges)


# --------------------------------------------------------------------------- table register

def test_table_register_assigns_star_roles(ctx):
    m, _, edges = ctx
    reg = schema.table_register(m, edges).set_index("Table Name")
    assert reg.loc["NETWORK_DIM", "Star Schema Role"] == "Conformed dimension"
    assert reg.loc["TELECAST_DIM", "Star Schema Role"] == "Private dimension"
    assert reg.loc["RETIRED_DIM", "Star Schema Role"] == "Unlinked dimension"
    assert reg.loc["INVOICE_REVENUE_FACT", "Star Schema Role"] == "Fact"


def test_table_register_covers_every_table(ctx):
    m, _, edges = ctx
    reg = schema.table_register(m, edges)
    assert len(reg) == int((m["Object Type"] == "Table").sum())


def test_table_register_flags_copy_suffix_duplicates(ctx):
    m, _, edges = ctx
    reg = schema.table_register(m, edges).set_index("Table Name")
    assert reg.loc["ACCOUNT_PROPERTY_CATEGORY_DIM (1)", "Duplicate?"] == "Yes"


# --------------------------------------------------------------------------- attribute lineage

def test_attribute_maps_to_most_specific_table(ctx):
    m, _, _ = ctx
    amap = schema.attribute_table_map(m).set_index("Attribute")
    assert amap.loc["Advertiser Name", "Inferred Table"] == "ADVERTISER_DIM"


def test_source_system_attribute_is_downgraded_not_claimed_as_lineage(ctx):
    m, _, _ = ctx
    amap = schema.attribute_table_map(m).set_index("Attribute")
    row = amap.loc["ABS Advertiser"]
    assert row["Confidence"] == "Low"
    assert "not lineage" in row["Basis"]


def test_unmatched_attribute_is_reported_rather_than_guessed(ctx):
    m, _, _ = ctx
    amap = schema.attribute_table_map(m).set_index("Attribute")
    row = amap.loc["A Or Z Spot Indicator"]
    assert row["Confidence"] == "No match"
    assert row["Inferred Table"] == ""


def test_every_attribute_appears_exactly_once(ctx):
    m, _, _ = ctx
    amap = schema.attribute_table_map(m)
    assert len(amap) == int((m["Object Type"] == "Attribute").sum())
    assert amap["Object ID"].is_unique


# --------------------------------------------------------------------------- diagrams

def test_mermaid_written_with_one_diagram_per_fact(tmp_path, ctx):
    _, d, edges = ctx
    star = schema.star_schema_map(edges, d)
    path = diagram.write_mermaid(str(tmp_path / "s.md"), edges, star)
    text = open(path, encoding="utf-8").read()
    assert text.count("```mermaid") == star["Fact Table"].nunique()
    assert "INVOICE_REVENUE_FACT }o--|| NETWORK_DIM" in text
    assert "erDiagram" in text


def test_mermaid_skipped_when_no_edges(tmp_path):
    assert diagram.write_mermaid(str(tmp_path / "s.md"), pd.DataFrame(), pd.DataFrame()) is None


def test_bus_matrix_image_is_written(tmp_path, ctx):
    _, _, edges = ctx
    path = diagram.write_bus_matrix_image(str(tmp_path / "m.png"), edges)
    if path is None:
        pytest.skip("matplotlib not installed")
    assert os.path.getsize(path) > 5000


# --------------------------------------------------------------------------- overview

def test_overview_states_the_limitations(ctx):
    m, _, edges = ctx
    conf = schema.dimension_conformance(edges, m)
    amap = schema.attribute_table_map(m)
    ov = schema.schema_overview(m, edges, conf, amap)
    limits = ov[ov["Section"] == "Limitations"]
    assert len(limits) == 3
    assert all("No" in str(v) for v in limits["Value"])
