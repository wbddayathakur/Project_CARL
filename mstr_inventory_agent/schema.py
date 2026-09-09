"""Logical schema view of the US Ad Sales warehouse.

Scope and honesty note: the MicroStrategy exports contain table *names* only — no columns, data
types, primary/foreign keys or join expressions, and no attribute-to-column mapping. A physical
schema (DDL) therefore cannot be produced from this data.

What can be produced is a **logical star-schema view**:
  * fact and dimension tables classified by naming convention,
  * the fact-to-dimension bus matrix carried forward from the validated draft analysis,
  * dimension conformance (which dimensions are shared across facts),
  * orphan detection, and
  * an inferred attribute-to-table mapping based on name matching, with explicit confidence.

Everything derived here is labelled with its evidence and confidence so it is never mistaken for
an authoritative extract of the warehouse schema.
"""

import re
from typing import Dict, List, Optional, Tuple

import pandas as pd

TABLE_SUFFIXES = ["_FACT", "_DIM", "_PIVOT", "_VW", "_LU", "_REL"]

_STOPWORD_TOKENS = {"ABS", "ID", "NAME", "CODE", "NUM", "NUMBER", "DESC", "DESCRIPTION",
                    "IND", "INDICATOR", "FLAG", "TYPE", "KEY"}


def table_stem(name: str) -> str:
    """Table name with its class suffix removed: ADVERTISER_DIM -> ADVERTISER."""
    n = str(name or "").upper().strip()
    n = re.sub(r"\s*\(\d+\)$", "", n)
    for suf in TABLE_SUFFIXES:
        if n.endswith(suf):
            return n[: -len(suf)]
    return n


def _tokens(text) -> List[str]:
    return [t for t in re.sub(r"[^A-Z0-9]+", " ", str(text or "").upper()).split() if t]


# --------------------------------------------------------------------------- table register

def table_register(master: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    """Every warehouse table with its role in the star schema."""
    tables = master[master["Object Type"] == "Table"].copy()
    if tables.empty:
        return pd.DataFrame()

    fact_use = edges.groupby("Dimension Table")["Fact Table"].apply(list).to_dict() if not edges.empty else {}
    fact_dims = edges.groupby("Fact Table")["Dimension Table"].apply(list).to_dict() if not edges.empty else {}

    rows: List[dict] = []
    for r in tables.to_dict("records"):
        wh = str(r.get("Warehouse Table Name") or r["Object Name"]).upper()
        klass = r["Object Subtype"]
        used_by = fact_use.get(wh, [])
        joins = fact_dims.get(wh, [])

        if klass == "Fact":
            role = "Fact"
            linked = len(joins)
            note = (f"Joins {linked} dimensions" if linked
                    else "No dimension joins mapped; not covered by the fact/dimension analysis")
        elif klass == "Dimension":
            role = ("Conformed dimension" if len(used_by) > 1
                    else "Private dimension" if len(used_by) == 1
                    else "Unlinked dimension")
            linked = len(used_by)
            note = (f"Used by {linked} fact(s): {', '.join(sorted(used_by))}" if used_by
                    else "Not joined to any fact in the mapped star schemas; verify whether it is "
                         "still used or is a retired table")
        else:
            role = klass
            linked = 0
            note = "Staging / view object rather than a star-schema table"

        rows.append(
            {
                "Object ID": r["Object ID"],
                "Table Name": r["Object Name"],
                "Warehouse Table Name": r.get("Warehouse Table Name"),
                "Table Class": klass,
                "Star Schema Role": role,
                "Linked Facts / Dims": linked,
                "Duplicate?": "Yes" if r.get("Name Variant") == "Yes" else "",
                "Notes": note,
            }
        )

    out = pd.DataFrame(rows).sort_values(
        ["Table Class", "Linked Facts / Dims", "Table Name"], ascending=[True, False, True]
    ).reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    return out


# --------------------------------------------------------------------------- star schema

def fact_dimension_edges(draft_sheets: Dict[str, pd.DataFrame],
                         master: pd.DataFrame) -> pd.DataFrame:
    """Normalise the bus matrix into one row per fact-to-dimension join.

    Source of truth is the 'Fact x Dim Matrix' carried forward from the validated draft. Each
    edge is checked against the tables export so a mapping to a non-existent table cannot slip
    through unnoticed.
    """
    matrix = draft_sheets.get("Fact x Dim Matrix")
    join_map = draft_sheets.get("Fact-Dimension Join Map")
    if matrix is None or matrix.empty:
        return pd.DataFrame(columns=["#", "Fact Table", "Dimension Table", "Business Area",
                                     "Confidence", "Evidence", "Dimension Exists In Export"])

    real_tables = _real_table_names(master)
    area_by_fact, conf_by_fact = _fact_metadata(join_map)

    dim_col = matrix.columns[0]
    rows: List[dict] = []
    for rec in matrix.to_dict("records"):
        dim = str(rec[dim_col]).strip().upper()
        if not dim or dim == "NAN":
            continue
        for fact_short in matrix.columns[1:]:
            if pd.isna(rec[fact_short]):
                continue
            fact = _expand_fact_name(str(fact_short), real_tables)
            rows.append(
                {
                    "Fact Table": fact,
                    "Dimension Table": dim,
                    "Business Area": area_by_fact.get(fact, ""),
                    "Confidence": conf_by_fact.get(fact, "Medium"),
                    "Evidence": "Fact/dimension analysis validated against the tables export",
                    "Dimension Exists In Export": "Yes" if dim in real_tables else "No",
                }
            )

    out = pd.DataFrame(rows).sort_values(["Fact Table", "Dimension Table"]).reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    return out


def star_schema_map(edges: pd.DataFrame, draft_sheets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One row per fact table: its grain, dimension count and conformed-dimension share."""
    if edges.empty:
        return pd.DataFrame()

    join_map = draft_sheets.get("Fact-Dimension Join Map")
    grain = {}
    if join_map is not None and not join_map.empty:
        for rec in join_map.to_dict("records"):
            grain[str(rec.get("Fact Table", "")).strip().upper()] = rec.get("Key Grain / Notes")

    dim_use = edges.groupby("Dimension Table")["Fact Table"].nunique()
    conformed = set(dim_use[dim_use > 1].index)

    rows: List[dict] = []
    for fact, grp in edges.groupby("Fact Table"):
        dims = sorted(grp["Dimension Table"].unique())
        shared = [d for d in dims if d in conformed]
        rows.append(
            {
                "Fact Table": fact,
                "Business Area": grp["Business Area"].iloc[0],
                "Dimensions": len(dims),
                "Conformed Dimensions": len(shared),
                "Private Dimensions": len(dims) - len(shared),
                "Key Grain / Notes": grain.get(fact, ""),
                "Confidence": grp["Confidence"].iloc[0],
                "Dimension Tables": ", ".join(dims),
            }
        )
    out = pd.DataFrame(rows).sort_values("Dimensions", ascending=False).reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    return out


def dimension_conformance(edges: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    """Per dimension: how many facts use it. Conformed dimensions are the reusable core."""
    dim_tables = master[(master["Object Type"] == "Table")
                        & (master["Object Subtype"] == "Dimension")]
    all_dims = sorted({str(n).upper() for n in dim_tables["Object Name"]})

    used = (edges.groupby("Dimension Table")["Fact Table"].apply(lambda s: sorted(set(s)))
            if not edges.empty else pd.Series(dtype=object))

    rows: List[dict] = []
    for dim in sorted(set(all_dims) | set(used.index if len(used) else [])):
        facts = used.get(dim, [])
        rows.append(
            {
                "Dimension Table": dim,
                "Facts Using It": len(facts),
                "Classification": ("Conformed (shared)" if len(facts) > 1
                                   else "Private to one fact" if len(facts) == 1
                                   else "Unlinked / possibly retired"),
                "In Tables Export": "Yes" if dim in all_dims else "No",
                "Fact Tables": ", ".join(facts),
            }
        )
    out = pd.DataFrame(rows).sort_values(
        ["Facts Using It", "Dimension Table"], ascending=[False, True]).reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    return out


# --------------------------------------------------------------- attribute-to-table inference

def attribute_table_map(master: pd.DataFrame) -> pd.DataFrame:
    """Infer which table each MSTR attribute most likely reads from.

    The exports carry no attribute-to-column mapping, so this matches attribute name tokens
    against table name stems. A match requires the table's full stem to appear in the attribute
    name, and the most specific (longest) stem wins. Confidence is graded so low-signal
    single-token matches are not mistaken for verified lineage.
    """
    tables = master[master["Object Type"] == "Table"]
    attrs = master[master["Object Type"] == "Attribute"]
    if tables.empty or attrs.empty:
        return pd.DataFrame()

    candidates: List[Tuple[str, List[str], str]] = []
    for r in tables.to_dict("records"):
        wh = str(r.get("Warehouse Table Name") or r["Object Name"]).upper()
        stem_tokens = _tokens(table_stem(wh))
        if stem_tokens:
            candidates.append((wh, stem_tokens, r["Object Subtype"]))

    rows: List[dict] = []
    for a in attrs.to_dict("records"):
        attr_tokens = set(_tokens(a["Object Name"]))
        folder_tokens = set(_tokens(a.get("Subject Area / Folder")))

        best: Optional[Tuple[str, List[str], str]] = None
        for wh, stem_tokens, klass in candidates:
            if set(stem_tokens).issubset(attr_tokens):
                if best is None or len(stem_tokens) > len(best[1]):
                    best = (wh, stem_tokens, klass)

        if best is None:
            rows.append(
                {
                    "Object ID": a["Object ID"],
                    "Attribute": a["Object Name"],
                    "Subject Area": a["Business Area"],
                    "Inferred Table": "",
                    "Table Class": "",
                    "Confidence": "No match",
                    "Basis": "No table name stem appears in the attribute name",
                }
            )
            continue

        wh, stem_tokens, klass = best
        signal = [t for t in stem_tokens if t not in _STOPWORD_TOKENS]
        if len(signal) >= 2:
            conf = "High"
        elif len(signal) == 1 and signal[0] in folder_tokens:
            conf = "High"
        elif len(signal) == 1:
            conf = "Medium"
        else:
            conf = "Low"

        basis = f"Attribute name contains the table stem '{' '.join(stem_tokens)}'"
        if conf == "High" and len(signal) == 1:
            basis += " and the folder agrees"

        # Attributes fed directly from a source system do not read from this star schema, so a
        # name match against a warehouse dimension is coincidental rather than lineage.
        if _is_source_system_attribute(a):
            conf = "Low"
            basis = ("Attribute belongs to a 'directly from source' subject area, so it reads "
                     f"from source-system extracts; the name match to {wh} is not lineage")

        rows.append(
            {
                "Object ID": a["Object ID"],
                "Attribute": a["Object Name"],
                "Subject Area": a["Business Area"],
                "Inferred Table": wh,
                "Table Class": klass,
                "Confidence": conf,
                "Basis": basis,
            }
        )

    order = {"High": 0, "Medium": 1, "Low": 2, "No match": 3}
    out = pd.DataFrame(rows)
    out = out.sort_values(
        ["Confidence", "Attribute"],
        key=lambda s: s.map(order) if s.name == "Confidence" else s,
    ).reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    return out


# --------------------------------------------------------------------------- overview

def schema_overview(master: pd.DataFrame, edges: pd.DataFrame,
                    conformance: pd.DataFrame, attr_map: pd.DataFrame) -> pd.DataFrame:
    rows: List[dict] = []

    def add(section, metric, value):
        rows.append({"Section": section, "Metric": metric, "Value": value})

    tables = master[master["Object Type"] == "Table"]
    add("Tables", "Warehouse tables catalogued", len(tables))
    for klass, n in tables["Object Subtype"].value_counts().items():
        add("Tables", f"  {klass}", int(n))

    add("Star schema", "Fact tables with a mapped star", int(edges["Fact Table"].nunique())
        if not edges.empty else 0)
    add("Star schema", "Fact-to-dimension joins mapped", len(edges))
    if not edges.empty:
        add("Star schema", "Dimension joins pointing at a missing table",
            int((edges["Dimension Exists In Export"] == "No").sum()))

    if not conformance.empty:
        add("Dimensions", "Dimension tables", len(conformance))
        for klass, n in conformance["Classification"].value_counts().items():
            add("Dimensions", f"  {klass}", int(n))
        top = conformance.head(1)
        if len(top):
            add("Dimensions", "Most reused dimension",
                f"{top['Dimension Table'].iloc[0]} ({int(top['Facts Using It'].iloc[0])} facts)")

    if not attr_map.empty:
        add("Attribute lineage", "Attributes examined", len(attr_map))
        for conf, n in attr_map["Confidence"].value_counts().items():
            add("Attribute lineage", f"  {conf}", int(n))

    add("Limitations", "Column-level schema available", "No — exports carry table names only")
    add("Limitations", "Primary/foreign keys available", "No")
    add("Limitations", "Attribute-to-column mapping available", "No — inferred by name only")

    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- helpers

def _is_source_system_attribute(attr: dict) -> bool:
    """Subject areas that feed straight from a source system, not the warehouse star schema."""
    haystack = " ".join(
        str(attr.get(k) or "") for k in ("Business Area", "Subject Area / Folder", "Folder Path")
    ).lower()
    return "directly from source" in haystack


def _real_table_names(master: pd.DataFrame) -> set:
    tables = master[master["Object Type"] == "Table"]
    names = set()
    for r in tables.to_dict("records"):
        names.add(str(r["Object Name"]).upper())
        wh = r.get("Warehouse Table Name")
        if wh:
            names.add(str(wh).upper())
    return names


def _expand_fact_name(short: str, real_tables: set) -> str:
    """The bus matrix drops the _FACT suffix from its column headers."""
    s = short.strip().upper()
    if s in real_tables:
        return s
    if f"{s}_FACT" in real_tables:
        return f"{s}_FACT"
    return s


def _fact_metadata(join_map: Optional[pd.DataFrame]):
    area, conf = {}, {}
    if join_map is None or join_map.empty:
        return area, conf
    for rec in join_map.to_dict("records"):
        fact = str(rec.get("Fact Table", "")).strip().upper()
        area[fact] = rec.get("Business Area", "")
        conf[fact] = rec.get("Confidence", "Medium")
    return area, conf
