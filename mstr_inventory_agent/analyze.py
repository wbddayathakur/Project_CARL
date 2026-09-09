"""Derived analysis sheets: dashboards, folder-level linkage, coverage and data quality."""

from typing import List

import pandas as pd

from . import classify
from .build import report_scope


def dashboard_register(master: pd.DataFrame) -> pd.DataFrame:
    """Dashboard-class deliverables with the report grid that composes each one.

    MSTR dashboards are assembled from a folder of component reports, so the folder is treated
    as the dashboard boundary.
    """
    reports = master[master["Object Type"] == "Report"].copy()
    dash = reports[reports["Deliverable Class"] == "Dashboard"]
    if dash.empty:
        return pd.DataFrame(
            columns=["#", "Dashboard ID", "Dashboard (folder)", "Business Area",
                     "Component Objects", "Object Types", "Component Object IDs", "Folder Path"]
        )

    rows: List[dict] = []
    for folder, grp in dash.groupby("Folder Path", dropna=False):
        leaf = classify.subject_area(folder)
        rows.append(
            {
                "Dashboard ID": "DASH-" + grp["Surrogate GUID"].iloc[0][:12],
                "Dashboard (folder)": leaf,
                "Business Area": grp["Business Area"].iloc[0],
                "Component Objects": len(grp),
                "Object Types": ", ".join(sorted(set(grp["Object Subtype"].dropna()))),
                "Component Object IDs": ", ".join(grp["Object ID"].head(60)),
                "Folder Path": folder,
            }
        )
    out = pd.DataFrame(rows).sort_values(
        ["Business Area", "Dashboard (folder)"]).reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    return out


def report_object_links(master: pd.DataFrame) -> pd.DataFrame:
    """Evidence-based links only.

    The exports carry no report definitions, so true report-to-metric dependencies are not
    recoverable. The one hard signal available is an application object stored *inside* a
    shared report folder, which means that object belongs to that report.
    """
    blocks = master[master["Object Type"].isin(["Attribute", "Metric", "Filter"])].copy()
    blocks["__scope"] = blocks["Folder Path"].map(report_scope)
    scoped = blocks[blocks["__scope"].notna()]
    if scoped.empty:
        return pd.DataFrame(columns=["#", "Report Folder", "Object ID", "Object Type",
                                     "Object Name", "Evidence", "Folder Path"])

    reports = master[master["Object Type"] == "Report"].copy()
    reports["__scope"] = reports["Folder Path"].map(report_scope)

    rows: List[dict] = []
    for row in scoped.to_dict("records"):
        rows.append(
            {
                "Report Folder": row["__scope"],
                "Object ID": row["Object ID"],
                "Object Type": row["Object Type"],
                "Object Name": row["Object Name"],
                "Evidence": "Object is stored within the report's folder in MSTR metadata",
                "Folder Path": row["Folder Path"],
            }
        )
    out = pd.DataFrame(rows).sort_values(["Report Folder", "Object Type", "Object Name"])
    out = out.reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    return out


def business_area_coverage(master: pd.DataFrame) -> pd.DataFrame:
    pivot = pd.crosstab(master["Business Area"], master["Object Type"])
    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("Total", ascending=False).reset_index()
    return pivot


def owner_footprint(master: pd.DataFrame) -> pd.DataFrame:
    """Personal-folder sprawl by user: the primary migration/rationalisation risk."""
    personal = master[master["Location"].str.contains("Personal|Administrator personal",
                                                      na=False, regex=True)]
    if personal.empty:
        return pd.DataFrame(columns=["#", "Owner", "Owner Login", "Objects", "Object Types"])
    grp = personal.groupby(["Owner", "Owner Login"], dropna=False)
    out = grp.agg(
        Objects=("Object ID", "count"),
        **{"Object Types": ("Object Subtype",
                            lambda s: ", ".join(sorted(set(str(x) for x in s.dropna()))[:6]))},
    ).reset_index().sort_values("Objects", ascending=False).reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    return out


def duplicate_groups(master: pd.DataFrame):
    """Yield (key, frame) for every object type + name that occurs more than once."""
    dup = master[master["Duplicate Name"] == "Yes"]
    if dup.empty:
        return []
    return dup.groupby([dup["Object Type"], dup["Object Name"].str.casefold()])


def duplicate_names(master: pd.DataFrame) -> pd.DataFrame:
    """Full duplicate-name register, one row per repeated name."""
    rows: List[dict] = []
    for _, grp in duplicate_groups(master):
        shared = grp[grp["Location"].str.startswith("Shared", na=False)]
        rows.append(
            {
                "Object Type": grp["Object Type"].iloc[0],
                "Object Name": grp["Object Name"].iloc[0],
                "Total Copies": len(grp),
                "Shared Copies": len(shared),
                "Personal Copies": len(grp) - len(shared),
                "Scope": ("Shared-space collision" if len(shared) > 1
                          else "Shared + personal copies" if len(shared) == 1
                          else "Personal folders only"),
                "Business Areas": ", ".join(sorted(set(grp["Business Area"].dropna()))[:6]),
                "Object IDs": ", ".join(grp["Object ID"].head(40)),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["#", "Object Type", "Object Name", "Total Copies",
                                     "Shared Copies", "Personal Copies", "Scope",
                                     "Business Areas", "Object IDs"])
    out = pd.DataFrame(rows).sort_values(
        ["Shared Copies", "Total Copies"], ascending=False).reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    return out


def data_quality(master: pd.DataFrame) -> pd.DataFrame:
    issues: List[dict] = []

    def add(kind, severity, detail, action, obj_id=None):
        issues.append(
            {
                "Issue Type": kind,
                "Severity": severity,
                "Object ID": obj_id or "",
                "Detail": detail,
                "Recommended Action": action,
            }
        )

    # 1. Copy-suffix name variants, e.g. "AS-WH-DEV (1)".
    for row in master[master["Name Variant"] == "Yes"].to_dict("records"):
        base = classify.name_variant(row["Object Name"])[0]
        add("Name variant / copy suffix", "Review",
            f"{row['Object Type']} '{row['Object Name']}' looks like a copy of '{base}'",
            "Confirm which object is authoritative and retire the duplicate",
            row["Object ID"])

    # 2. Same name reused across folders. Only shared-space collisions are itemised here;
    #    personal-only repetition is expected sprawl and is rolled up to keep this sheet
    #    actionable. The full list lives on the Duplicate Names sheet.
    personal_only = 0
    for _, grp in duplicate_groups(master):
        otype = grp["Object Type"].iloc[0]
        shared = grp[grp["Location"].str.startswith("Shared", na=False)]
        if len(shared) > 1:
            add("Duplicate name in shared space", "High",
                f"{otype} named '{grp['Object Name'].iloc[0]}' exists in {len(shared)} different "
                f"shared folders ({len(grp)} copies in total)",
                "Verify whether these are true copies; consolidate or rename so lineage is "
                "unambiguous")
        elif len(shared) == 1:
            add("Personal copies of a shared object", "Review",
                f"{otype} '{grp['Object Name'].iloc[0]}' is published once in shared space but "
                f"has {len(grp) - 1} personal copies",
                "Point users at the governed shared version and retire the personal copies")
        else:
            personal_only += 1
    if personal_only:
        add("Repeated names in personal folders", "Low",
            f"{personal_only:,} object names are repeated only across personal folders",
            "No shared-space impact; handle as part of personal folder triage. See the "
            "'Duplicate Names' sheet for the full list")

    # 3. Personal-folder sprawl.
    personal = master[master["Location"].str.contains("Personal", na=False)]
    if len(personal):
        by_owner = personal.groupby("Owner").size().sort_values(ascending=False)
        add("Ungoverned personal content", "High",
            f"{len(personal):,} objects live in personal My Reports folders across "
            f"{by_owner.size} users (largest: {by_owner.index[0]} with {by_owner.iloc[0]:,})",
            "Triage for migration: promote actively used reports to shared folders, archive rest")

    # 4. Hidden objects.
    hidden = master[master["Hidden"] == "Yes"]
    if len(hidden):
        add("Hidden objects", "Review",
            f"{len(hidden)} objects are flagged Hidden in MSTR metadata",
            "Confirm these are intentional helper objects rather than forgotten content")

    # 5. Legacy / missing owners on data sources. Scoped to genuinely configured instances,
    #    since MSTR's shipped connectors are all owned by Administrator by design.
    all_dbi = master[master["Object Type"] == "Database Instance"]
    dbi = all_dbi[all_dbi["Object Subtype"] == "Configured data source"]
    platform = all_dbi[all_dbi["Object Subtype"] == "MSTR platform connector"]
    if len(platform):
        add("Platform connectors counted as data sources", "Low",
            f"{len(platform)} of {len(all_dbi)} database instances are MicroStrategy "
            "out-of-the-box Data Import connectors, not configured US Ad Sales sources",
            "Exclude from migration scope; only the "
            f"{len(dbi)} configured instances need review")
    legacy = dbi[dbi["Owner"].map(classify.is_legacy_owner)]
    for row in legacy.to_dict("records"):
        add("Legacy owner on data source", "High", row["Object ID"] and
            f"Database instance '{row['Object Name']}' is owned by '{row['Owner']}'",
            "Reassign to an active steward; legacy accounts block credential rotation",
            row["Object ID"])
    missing_owner = dbi[dbi["Owner"].isna()]
    if len(missing_owner):
        add("Missing owner on data source", "High",
            f"{len(missing_owner)} database instances have no owner recorded",
            "Assign an accountable owner before migration")

    # 6. Environment ambiguity on connections.
    conns = master[master["Object Type"] == "Database Connection"]
    unknown_env = conns[conns["Environment"] == "Unclassified"]
    if len(unknown_env):
        add("Unclassifiable environment", "Review",
            f"{len(unknown_env)} of {len(conns)} database connections have no DEV/TEST/PROD "
            "marker in the name",
            "Adopt a naming standard so environment is unambiguous from the connection name")

    # 7. Instances without a matching connection and vice versa.
    inst_names = set(dbi["Object Name"].str.casefold())
    conn_names = set(conns["Object Name"].str.casefold())
    only_inst, only_conn = inst_names - conn_names, conn_names - inst_names
    if only_inst:
        add("Instance without matching connection", "Review",
            f"{len(only_inst)} database instances have no like-named connection "
            f"(e.g. {', '.join(sorted(only_inst)[:3])})",
            "Confirm the instance is still wired to a live connection")
    if only_conn:
        add("Connection without matching instance", "Review",
            f"{len(only_conn)} database connections have no like-named instance "
            f"(e.g. {', '.join(sorted(only_conn)[:3])})",
            "Retire orphaned connections")

    # 8. Deep folder nesting hampers governance.
    deep = master[master["Path Depth"] >= 7]
    if len(deep):
        add("Deep folder nesting", "Low",
            f"{len(deep)} objects sit {int(master['Path Depth'].max())} levels deep at the "
            "deepest point",
            "Flatten folder structure during migration to improve discoverability")

    out = pd.DataFrame(issues)
    if out.empty:
        return out
    order = {"High": 0, "Review": 1, "Low": 2}
    out = out.sort_values(
        ["Severity", "Issue Type"], key=lambda s: s.map(order).fillna(9) if s.name == "Severity" else s
    ).reset_index(drop=True)
    out.insert(0, "#", range(1, len(out) + 1))
    return out[["#", "Issue Type", "Severity", "Object ID", "Detail", "Recommended Action"]]


def summary(master: pd.DataFrame, provenance: List[dict]) -> pd.DataFrame:
    rows: List[dict] = []

    def add(section, metric, value):
        rows.append({"Section": section, "Metric": metric, "Value": value})

    add("Inventory", "Total catalogued objects", len(master))
    for otype, n in master["Object Type"].value_counts().items():
        add("Inventory", f"  {otype}s", int(n))

    reports = master[master["Object Type"] == "Report"]
    add("Reports & dashboards", "Total report objects", len(reports))
    for klass, n in reports["Deliverable Class"].value_counts().items():
        add("Reports & dashboards", f"  {klass}", int(n))
    shared = reports[reports["Location"].str.startswith("Shared", na=False)]
    add("Reports & dashboards", "In shared (governed) folders", len(shared))
    add("Reports & dashboards", "In personal folders",
        int(reports["Location"].str.contains("Personal", na=False).sum()))
    add("Reports & dashboards", "Distinct business areas (shared)",
        int(shared["Business Area"].nunique()))

    dbi = master[master["Object Type"] == "Database Instance"]
    conns = master[master["Object Type"] == "Database Connection"]
    add("Data sources", "Database instances (total)", len(dbi))
    add("Data sources", "  Configured US Ad Sales instances",
        int((dbi["Object Subtype"] == "Configured data source").sum()))
    add("Data sources", "  MSTR platform connectors (out of scope)",
        int((dbi["Object Subtype"] == "MSTR platform connector").sum()))
    add("Data sources", "Database connections", len(conns))
    add("Data sources", "  Production connections",
        int((conns["Environment"] == "PROD").sum()))

    add("Identifiers", "Objects with surrogate ID + GUID", int(master["Object ID"].notna().sum()))
    add("Identifiers", "Objects with real MSTR GUID populated",
        int(master["MSTR GUID"].notna().sum()))
    add("Identifiers", "Duplicate Object IDs (must be 0)",
        int(master["Object ID"].duplicated().sum()))

    add("Descriptions", "Descriptions present", int(master["Description"].notna().sum()))
    add("Descriptions", "Sourced from export",
        int((master["Description Source"] == "From source export").sum()))
    add("Descriptions", "Derived by agent",
        int(master["Description Source"].str.startswith("Derived", na=False).sum()))

    add("Sources", "Export files read", len(provenance))
    add("Sources", "Total rows read", int(sum(p["Rows Read"] for p in provenance)))

    return pd.DataFrame(rows)
