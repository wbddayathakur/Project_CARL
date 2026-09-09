"""Compose object descriptions.

None of the MicroStrategy exports for US Ad Sales carry a description field (the only exception
is the Description column on database instances, which is empty in the current export). Every
description this module produces is therefore *derived* from the object's name, type and folder
taxonomy, and is stamped as such in the ``Description Source`` column. Derived text is intended
as a starting point for stewards to confirm, not as authoritative documentation.
"""

import re
from typing import List, Optional

from . import classify
from .config import TERM_GLOSSARY

# Longest phrases first so "booked revenue" beats "revenue" and "acm7" beats "acm".
_GLOSSARY_TERMS = sorted(TERM_GLOSSARY.items(), key=lambda kv: -len(kv[0]))

_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")


def _topics(*texts: Optional[str], limit: int = 4) -> List[str]:
    """Glossary phrases matched in the supplied text, in glossary-priority order."""
    haystack = " ".join(str(t or "").lower() for t in texts)
    padded = " " + _TOKEN_SPLIT.sub(" ", haystack).strip() + " "

    found: List[str] = []
    consumed = padded
    for term, phrase in _GLOSSARY_TERMS:
        needle = " " + term.replace("/", " ").strip() + " "
        if needle in consumed and phrase not in found:
            found.append(phrase)
            consumed = consumed.replace(needle, " ")
        if len(found) >= limit:
            break
    return found


def _paragraph(sentences: List[str]) -> str:
    """Join non-empty clauses into properly terminated sentences."""
    out = []
    for s in sentences:
        s = re.sub(r"\s+", " ", str(s or "")).strip().strip(",")
        if not s:
            continue
        if not s.endswith("."):
            s += "."
        out.append(s[0].upper() + s[1:])
    return " ".join(out)


def describe_report(name, report_type, folder) -> str:
    klass = classify.deliverable_class(name, report_type, folder)
    area = classify.business_area(folder)
    leaf = classify.subject_area(folder)
    topics = _topics(name, leaf)

    lead = f"{klass} ({report_type})" if report_type else klass
    if classify.is_personal(folder):
        who = classify.owner(folder)
        lead += f" held in the personal folder of {who}" if who else " held in a personal folder"
    elif area not in {"Unclassified", "Personal / ungoverned"}:
        lead += f" owned by {area}"
    if leaf and leaf != area:
        lead += f", filed under '{leaf}'"

    topic_note = f"Covers {_join(topics)}" if topics else ""

    tail = ""
    if classify.is_personal(folder):
        tail = "Not a governed shared asset; confirm it is still in use before migration"
    elif report_type == "Intelligent Cube":
        tail = "Serves as a cached in-memory source for downstream reports"
    elif report_type == "Data Mart Report":
        tail = "Writes results back to the warehouse for downstream consumption"

    return _paragraph([lead, topic_note, tail])


def describe_object(name, object_type, path, extra: Optional[str] = None) -> str:
    """Description for schema/application objects: attributes, metrics, filters."""
    area = classify.business_area(path)
    leaf = classify.subject_area(path)
    topics = _topics(name, leaf)

    if object_type == "Attribute":
        lead = f"Attribute used to group and qualify results by {_humanise(name)}"
    elif object_type == "Metric":
        lead = f"Metric calculating {_humanise(name)}"
    elif object_type == "Filter":
        lead = f"Filter restricting results to {_humanise(name)}"
    else:
        lead = f"{object_type} {_humanise(name)}"

    if leaf and leaf != "Unspecified":
        lead += f", published in the '{leaf}' folder"
    if area not in {"Unclassified", leaf}:
        lead += f" of the {area} subject area"

    topic_note = f"Relates to {_join(topics)}" if topics else ""
    return _paragraph([lead, topic_note, extra or ""])


def describe_table(name, path, warehouse_name) -> str:
    klass = table_class(name)
    base, variant = classify.name_variant(name)
    lead = f"{klass} table '{warehouse_name or name}' in the US AdSales warehouse schema"
    tail = (f"Metadata duplicate of '{base}' created by an MSTR copy operation; "
            "candidate for removal") if variant else ""
    return _paragraph([lead, tail])


def table_class(name: Optional[str]) -> str:
    # Strip MSTR's " (1)" copy suffix so duplicates still classify by their real role.
    n = re.sub(r"\s*\(\d+\)$", "", str(name or "").upper()).strip()
    if n.endswith("_VW") or n.startswith("VW_"):
        return "View"
    if n.endswith("_PIVOT") or "_PIVOT" in n:
        return "Pivot / staging"
    if n.endswith("_FACT") or "_FACT_" in n:
        return "Fact"
    if n.endswith("_DIM") or "_DIM_" in n:
        return "Dimension"
    if n.endswith("_LU") or n.startswith("LU_"):
        return "Lookup"
    if "_REL" in n or n.endswith("_REL"):
        return "Relationship"
    if "AGG" in n:
        return "Aggregate"
    return "Other"


def describe_db_instance(name, owner, description, klass=None) -> str:
    if klass == "MSTR platform connector":
        detail = f" ({description})" if description and description.lower() != str(name).lower() else ""
        return _paragraph([
            f"MicroStrategy out-of-the-box Data Import connector '{name}'{detail}",
            "Ships with the platform rather than being a configured US Ad Sales data source; "
            "exclude from data source migration scope unless actively used",
        ])
    if description and str(description).strip():
        return _paragraph([str(description).strip()])
    env = classify.environment(name)
    env_note = (f"{env} environment" if env != "Unclassified"
                else "environment not identifiable from the name")
    owner_note = f"registered to {owner}" if owner else "with no owner recorded"
    legacy = ("Owner account is flagged legacy; reassign stewardship"
              if classify.is_legacy_owner(owner) else "")
    return _paragraph(
        [f"MicroStrategy database instance '{name}' pointing at the {env_note}, {owner_note}",
         legacy]
    )


def describe_db_connection(name) -> str:
    env = classify.environment(name)
    base, variant = classify.name_variant(name)
    env_note = (f"the {env} environment" if env != "Unclassified"
                else "an environment not identifiable from the name")
    tail = f"Name variant of '{base}'; likely a stale duplicate connection" if variant else ""
    return _paragraph([f"Database connection '{name}' resolving to {env_note}", tail])


def _humanise(name: Optional[str]) -> str:
    text = str(name or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text.rstrip(".") if text else "an unnamed object"


def _join(items: List[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]
