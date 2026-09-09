"""Assemble the unified inventory from the normalised source frames."""

from typing import Dict, List, Optional

import pandas as pd

from . import classify, describe, identity
from .config import SOURCES

# Column contract for the master inventory. Every object type is widened to this shape so a
# single sheet can carry reports, dashboards, attributes, metrics, filters, tables and data
# sources under one identifier scheme.
MASTER_COLUMNS = [
    "Object ID",
    "Surrogate GUID",
    "MSTR GUID",
    "Object Type",
    "Object Subtype",
    "Deliverable Class",
    "Object Name",
    "Description",
    "Description Source",
    "Business Area",
    "Subject Area / Folder",
    "Location",
    "Owner",
    "Owner Login",
    "Folder Path",
    "Full Path",
    "Path Depth",
    "Environment",
    "Warehouse Table Name",
    "Hidden",
    "Duplicate Name",
    "Name Variant",
    "Modification Time",
    "Source File",
]


def _val(row: dict, col: str) -> Optional[str]:
    v = row.get(col)
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    return v


def _base_record(prefix, object_type, name, folder):
    return {
        "Object ID": identity.object_id(prefix, object_type, folder, name),
        "Surrogate GUID": identity.surrogate_guid(object_type, folder, name),
        "MSTR GUID": pd.NA,
        "Object Type": object_type,
        "Object Name": name,
        "Folder Path": folder,
        "Full Path": identity.full_path(folder, name),
        "Path Depth": len(classify.segments(folder)),
        "Business Area": classify.business_area(folder, object_type),
        "Subject Area / Folder": classify.subject_area(folder),
        "Location": classify.location(folder),
        "Owner": classify.owner(folder),
        "Owner Login": classify.owner_login(folder),
        "Description Source": "Derived by agent (source export has no description)",
    }


def build_reports(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=MASTER_COLUMNS)
    spec = SOURCES["reports"]
    records: List[dict] = []
    for row in df.to_dict("records"):
        name, folder, rtype = _val(row, "Name"), _val(row, "Folder"), _val(row, "Type")
        rec = _base_record(spec.id_prefix, "Report", name, folder)
        rec.update(
            {
                "Object Subtype": rtype,
                "Deliverable Class": classify.deliverable_class(name, rtype, folder),
                "Description": describe.describe_report(name, rtype, folder),
                "Hidden": _bool(_val(row, "Hidden")),
                "Source File": _val(row, "__source_file") or spec.filename,
            }
        )
        records.append(rec)
    return _finish(pd.DataFrame(records))


def build_simple_objects(df: pd.DataFrame, source_key: str) -> pd.DataFrame:
    """Attributes, metrics and filters all share the Name/Path/Hidden export shape."""
    if df.empty:
        return pd.DataFrame(columns=MASTER_COLUMNS)
    spec = SOURCES[source_key]
    records: List[dict] = []
    for row in df.to_dict("records"):
        name, path = _val(row, "Name"), _val(row, "Path")
        rec = _base_record(spec.id_prefix, spec.object_type, name, path)
        scoped = report_scope(path)
        extra = (f"Defined inside the '{scoped}' report folder rather than the shared schema, "
                 "so it is local to that report" if scoped else "")
        rec.update(
            {
                "Object Subtype": spec.object_type,
                "Deliverable Class": "Building block",
                "Description": describe.describe_object(name, spec.object_type, path, extra),
                "Hidden": _bool(_val(row, "Hidden")),
                "Source File": _val(row, "__source_file") or spec.filename,
            }
        )
        records.append(rec)
    return _finish(pd.DataFrame(records))


def build_tables(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=MASTER_COLUMNS)
    spec = SOURCES["tables"]
    records: List[dict] = []
    for row in df.to_dict("records"):
        name, path = _val(row, "Name"), _val(row, "Path")
        wh = _val(row, "Warehouse Table Name")
        rec = _base_record(spec.id_prefix, "Table", name, path)
        rec.update(
            {
                "Object Subtype": describe.table_class(name),
                "Deliverable Class": "Warehouse table",
                "Description": describe.describe_table(name, path, wh),
                "Warehouse Table Name": wh,
                "Business Area": "Warehouse schema",
                "Subject Area / Folder": "Tables",
                "Source File": _val(row, "__source_file") or spec.filename,
            }
        )
        records.append(rec)
    return _finish(pd.DataFrame(records))


def build_db_instances(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=MASTER_COLUMNS)
    spec = SOURCES["dbinstances"]
    records: List[dict] = []
    for row in df.to_dict("records"):
        name = _val(row, "Database Instance")
        owner = _val(row, "Owner")
        desc = classify.clean_description(_val(row, "Description"))
        klass = classify.datasource_class(name, desc)
        rec = _base_record(spec.id_prefix, "Database Instance", name, None)
        rec.update(
            {
                "Object Subtype": klass,
                "Deliverable Class": "Data source",
                "Description": describe.describe_db_instance(name, owner, desc, klass),
                "Description Source": (
                    "From source export" if desc and klass == "Configured data source"
                    else "Derived by agent (source export has no description)"
                ),
                "Business Area": "Data source",
                "Subject Area / Folder": "Database Instances",
                "Location": "Configuration",
                "Owner": owner,
                "Environment": classify.environment(name),
                "Modification Time": _val(row, "Modification Time"),
                "Source File": _val(row, "__source_file") or spec.filename,
            }
        )
        records.append(rec)
    return _finish(pd.DataFrame(records))


def build_db_connections(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=MASTER_COLUMNS)
    spec = SOURCES["dbconnections"]
    records: List[dict] = []
    for row in df.to_dict("records"):
        name = _val(row, "Database Connection")
        rec = _base_record(spec.id_prefix, "Database Connection", name, None)
        rec.update(
            {
                "Object Subtype": "Database Connection",
                "Deliverable Class": "Data source",
                "Description": describe.describe_db_connection(name),
                "Business Area": "Data source",
                "Subject Area / Folder": "Database Connections",
                "Location": "Configuration",
                "Environment": classify.environment(name),
                "Source File": _val(row, "__source_file") or spec.filename,
            }
        )
        records.append(rec)
    return _finish(pd.DataFrame(records))


def build_master(frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    metrics = merge_metric_sources(frames)
    parts = [
        build_reports(frames.get("reports", pd.DataFrame())),
        build_simple_objects(frames.get("attributes", pd.DataFrame()), "attributes"),
        build_simple_objects(metrics, "metrics"),
        build_simple_objects(frames.get("filters", pd.DataFrame()), "filters"),
        build_tables(frames.get("tables", pd.DataFrame())),
        build_db_instances(frames.get("dbinstances", pd.DataFrame())),
        build_db_connections(frames.get("dbconnections", pd.DataFrame())),
    ]
    master = pd.concat([p for p in parts if not p.empty], ignore_index=True)

    key = (master["Object Type"].astype(str) + "||"
           + master["Object Name"].astype(str).str.casefold())
    counts = key.value_counts()
    master["Duplicate Name"] = key.map(counts).gt(1).map({True: "Yes", False: ""})
    master["Name Variant"] = master["Object Name"].map(
        lambda n: "Yes" if classify.name_variant(n)[1] else ""
    )

    master = master.sort_values(
        ["Object Type", "Business Area", "Object Name"], kind="stable"
    ).reset_index(drop=True)
    master = _enforce_unique_ids(master)
    master.insert(0, "#", range(1, len(master) + 1))
    return master


def _enforce_unique_ids(master: pd.DataFrame) -> pd.DataFrame:
    """Guarantee identifier uniqueness.

    Identity keys preserve case and spacing, so collisions should not occur. This is a
    last-resort tiebreak that suffixes later duplicates deterministically (by sorted position)
    rather than letting two objects share an identifier.
    """
    dup_mask = master["Object ID"].duplicated(keep="first")
    if not dup_mask.any():
        return master
    for idx in master.index[dup_mask]:
        n = 2
        while True:
            candidate = f"{master.at[idx, 'Object ID']}-{n}"
            if candidate not in set(master["Object ID"]):
                break
            n += 1
        master.at[idx, "Object ID"] = candidate
        master.at[idx, "Surrogate GUID"] = (
            master.at[idx, "Surrogate GUID"][:-2] + f"{n:02X}"
        )
    return master


def merge_metric_sources(frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """The Target Demographic export is a subset of the main metrics export; union them."""
    main = frames.get("metrics", pd.DataFrame())
    demo = frames.get("metrics_target_demo", pd.DataFrame())
    if demo.empty:
        return main
    if main.empty:
        return demo
    combined = pd.concat([main, demo], ignore_index=True)
    norm = (combined["Name"].map(identity.normalize) + "||"
            + combined["Path"].map(identity.normalize))
    combined = combined.assign(__norm=norm)
    files = combined.groupby("__norm")["__source_file"].apply(
        lambda s: "; ".join(sorted(set(s.dropna())))
    )
    combined = combined.drop_duplicates(subset="__norm", keep="first").copy()
    combined["__source_file"] = combined["__norm"].map(files)
    return combined.drop(columns="__norm").reset_index(drop=True)


def report_scope(path) -> Optional[str]:
    """If an object is defined inside a shared report folder, return that folder name."""
    segs = classify.segments(path)
    if len(segs) >= 3 and segs[0] == "Public Objects" and segs[1] == "Reports":
        return segs[2]
    return None


def _bool(value):
    if value is None:
        return pd.NA
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return "Yes"
    if text in {"false", "0", "no"}:
        return ""
    return pd.NA


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    for col in MASTER_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[MASTER_COLUMNS]
