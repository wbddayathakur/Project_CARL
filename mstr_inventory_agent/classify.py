"""Derive location, ownership, business area and environment from MicroStrategy folder paths."""

import re
from typing import Optional

from .config import (
    BUSINESS_AREA_BY_FOLDER,
    DASHBOARD_NAME_HINTS,
    ENV_PATTERNS,
    LEGACY_OWNER_MARKERS,
)

_PROFILE_RE = re.compile(r"^(?P<display>.*?)\s*\((?P<login>[^()]*)\)\s*$")


def segments(path: Optional[str]):
    if not path:
        return []
    return [s for s in str(path).strip().strip("\\").split("\\") if s]


def location(path: Optional[str]) -> str:
    """Where the object lives in the metadata tree."""
    segs = segments(path)
    if not segs:
        return "Unspecified"
    head = segs[0]
    if head == "Profiles":
        return "Personal (My Reports/My Objects)"
    if head == "Administrator (Administrator)":
        return "Administrator personal"
    if head == "Object Templates":
        return "Object template"
    if head == "Public Objects":
        return "Shared (Public Objects)"
    if head == "Schema Objects" or "Schema Objects" in segs:
        return "Schema (shared)"
    return "Other"


def is_personal(path: Optional[str]) -> bool:
    return location(path) in {"Personal (My Reports/My Objects)", "Administrator personal"}


def owner(path: Optional[str]) -> Optional[str]:
    """Profile owner display name for personal objects; shared objects have no single owner."""
    segs = segments(path)
    if len(segs) >= 2 and segs[0] == "Profiles":
        m = _PROFILE_RE.match(segs[1])
        return m.group("display").strip() if m else segs[1]
    if segs and segs[0] == "Administrator (Administrator)":
        return "Administrator"
    return None


def owner_login(path: Optional[str]) -> Optional[str]:
    segs = segments(path)
    if len(segs) >= 2 and segs[0] == "Profiles":
        m = _PROFILE_RE.match(segs[1])
        if m:
            return m.group("login").strip()
    if segs and segs[0] == "Administrator (Administrator)":
        return "Administrator"
    return None


def business_area(path: Optional[str], object_type: str = "") -> str:
    """Owning business area, inferred from the shared-folder taxonomy."""
    segs = segments(path)
    if not segs:
        return "Unclassified"

    if segs[0] == "Public Objects":
        # \Public Objects\Reports\<Business Area>\... or \Public Objects\Metrics\<Domain>\...
        if len(segs) >= 3:
            mapped = BUSINESS_AREA_BY_FOLDER.get(segs[2])
            if mapped:
                return mapped
            return segs[2]
        if len(segs) == 2:
            return f"Shared {segs[1]}"
        return "Shared"

    if "Schema Objects" in segs:
        i = segs.index("Schema Objects")
        # \...\Schema Objects\Attributes\<Subject Area>
        if len(segs) > i + 2:
            return segs[i + 2]
        return "Schema"

    if is_personal(path):
        return "Personal / ungoverned"

    if segs[0] == "Object Templates":
        return "Object template"

    return "Unclassified"


def subject_area(path: Optional[str]) -> str:
    """Deepest meaningful folder, used as the object's immediate grouping."""
    segs = segments(path)
    return segs[-1] if segs else "Unspecified"


def is_dashboard(name: Optional[str], object_type: Optional[str],
                 path: Optional[str]) -> bool:
    """Dashboard-style deliverable.

    The reports export contains only report objects, so a dashboard is identified by the
    Executive Summary Dashboards folder or explicit naming, not by an MSTR document type.
    """
    haystack = " ".join(str(x or "").lower() for x in (name, path))
    return any(hint in haystack for hint in DASHBOARD_NAME_HINTS)


def deliverable_class(name, object_type, path) -> str:
    if is_dashboard(name, object_type, path):
        return "Dashboard"
    t = str(object_type or "")
    if t in {"Intelligent Cube", "Data Mart Report", "Incremental Refresh Report"}:
        return "Data asset / cube"
    if t in {"Graph Report", "Grid Graph Report"}:
        return "Visual report"
    if t == "SQL Report":
        return "SQL report"
    return "Report"


def environment(name: Optional[str]) -> str:
    low = str(name or "").lower()
    for env, pats in ENV_PATTERNS:
        if any(p in low for p in pats):
            return env
    return "Unclassified"


_SLUG_DESC_RE = re.compile(r"^[a-z0-9]+$")
_HEX_SUFFIX_RE = re.compile(r"[0-9A-F]{32}$")

# Descriptions MicroStrategy writes onto its own shipped objects.
_PLATFORM_DESC_MARKERS = (
    "dbrole",
    "system defined db instance",
    "created by configuration wizard",
    "data import primary database instance",
    "connection to microstrategy data server",
)
_PLATFORM_NAMES = {"tutorial data", "data import database instance", "csv data source",
                   "excel data source", "statistics database"}


def datasource_class(name: Optional[str], description: Optional[str]) -> str:
    """Separate MSTR's out-of-the-box connectors from genuinely configured data sources.

    The export lists both. Roughly a third of the database instances are Data Import connectors
    and system objects that ship with the platform (Zendesk, Amazon S3, Salesforce and similar);
    counting those as US Ad Sales data sources overstates the real estate.
    """
    n = str(name or "").strip()
    d = str(description or "").strip()
    low_d = d.lower()

    if n.lower() in _PLATFORM_NAMES:
        return "MSTR platform connector"
    if _HEX_SUFFIX_RE.search(n):
        return "MSTR platform connector"
    if d and _SLUG_DESC_RE.match(d):
        return "MSTR platform connector"
    if any(m in low_d for m in _PLATFORM_DESC_MARKERS):
        return "MSTR platform connector"
    if n.lower().startswith("data import"):
        return "MSTR platform connector"
    return "Configured data source"


def clean_description(description: Optional[str]) -> Optional[str]:
    """Strip MSTR's marketing/doc-link payload appended after '#DESCRIPTION#'."""
    if description is None:
        return None
    text = str(description).split("#DESCRIPTION#")[0].strip()
    return text or None


def is_legacy_owner(value: Optional[str]) -> bool:
    low = str(value or "").lower()
    return any(m in low for m in LEGACY_OWNER_MARKERS)


_VARIANT_RE = re.compile(r"^(?P<base>.*?)\s*\((?P<n>\d+)\)\s*$")


def name_variant(name: Optional[str]):
    """Detect MSTR's '(1)' copy suffix. Returns (base_name, is_variant)."""
    m = _VARIANT_RE.match(str(name or "").strip())
    if m:
        return m.group("base").strip(), True
    return str(name or "").strip(), False
