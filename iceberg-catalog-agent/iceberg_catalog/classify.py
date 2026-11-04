"""Assign every table a layer, a domain and a shareability tier.

The tier is the field that makes the catalog safe to circulate. The Glue
catalog does not distinguish a certified Gold fact from somebody's
`dev_test_ideal_linear_serving_nf3`, and if you publish both with equal
weight the audience learns to distrust the whole document. Tiering sorts that
out once, centrally, so the renderers can simply obey it:

    certified     bound to a data product in the registry; safe to cite
    production    lives in prod, refreshed, and a manifest job writes it
    pipeline      refreshed with a known producer, but not yet promoted to prod
    undocumented  refreshed, but nothing in the manifests claims to write it
    sandbox       a database whose name marks it as scratch
    stale         no publish inside the freshness window

`undocumented` is deliberately not called "orphan". A table can be perfectly
healthy and still be invisible to the manifests — the inventory only sees what
`carl-data-engineering` writes, so anything loaded by another repo or by hand
lands here. It means "we cannot vouch for this", not "this is broken".
"""

from __future__ import annotations

import datetime as dt
import fnmatch
import re
from typing import Iterable, Optional, Sequence

from .model import Catalog, DataProduct, Table

TIER_CERTIFIED = "certified"
TIER_PRODUCTION = "production"
TIER_PIPELINE = "pipeline"
TIER_UNDOCUMENTED = "undocumented"
TIER_SANDBOX = "sandbox"
TIER_STALE = "stale"

TIER_ORDER = (
    TIER_CERTIFIED,
    TIER_PRODUCTION,
    TIER_PIPELINE,
    TIER_UNDOCUMENTED,
    TIER_SANDBOX,
    TIER_STALE,
)

# Matched against the database name, longest suffix first.
_LAYER_TOKENS = (
    ("_gold", "gold"),
    ("_silver", "silver"),
    ("_bronze", "bronze"),
    ("_landing", "landing"),
    ("_audit", "audit"),
    ("_raw", "bronze"),
)

_DEFAULT_SANDBOX_PATTERNS = (
    "*test*",
    "*_poc*",
    "*poc_*",
    "*sample*",
    "*example*",
    "default",
    "vg_*",
    "glue-*",
    "glue_db_*",
    "*sandbox*",
    "*_uat*",
)

# Environment suffixes that are part of the deployment, not the domain.
_ENV_SUFFIX = re.compile(r"_(dev|qa|stage|stg|prod|uat)$")


def classify(
    catalog: Catalog,
    *,
    asof: Optional[dt.datetime] = None,
    domain_map: Optional[dict] = None,
    sandbox_patterns: Sequence[str] = (),
) -> Catalog:
    """Set `layer`, `domain` and `tier` on every table, in place."""
    asof = asof or catalog.generated_at
    domain_map = domain_map or {}
    patterns = tuple(sandbox_patterns) or _DEFAULT_SANDBOX_PATTERNS

    certified = _certified_tables(catalog.products)

    for table in catalog.tables:
        table.layer = layer_of(table.database)
        table.domain = domain_of(table.database, domain_map)
        table.tier = tier_of(
            table,
            asof=asof,
            window_days=catalog.window_days,
            certified=certified,
            sandbox_patterns=patterns,
        )

    return catalog


def layer_of(database: str) -> str:
    lowered = database.lower()
    for token, layer in _LAYER_TOKENS:
        if token in lowered:
            return layer
    if lowered.endswith("_canonical") or lowered.endswith("_serving"):
        return "silver"
    return "unknown"


def domain_of(database: str, domain_map: Optional[dict] = None) -> str:
    """Group databases into business domains.

    An explicit `domains:` entry in config always wins. Otherwise the domain is
    the database name with its layer and environment suffixes stripped, which
    is right often enough to be useful and obvious when it is wrong.
    """
    domain_map = domain_map or {}

    for domain, patterns in domain_map.items():
        for pattern in patterns:
            if fnmatch.fnmatch(database, pattern):
                return domain

    stem = _ENV_SUFFIX.sub("", database.lower())
    for token, _ in _LAYER_TOKENS:
        stem = stem.replace(token, "")
    stem = stem.rstrip("_-")
    return stem or "unassigned"


def tier_of(
    table: Table,
    *,
    asof: dt.datetime,
    window_days: int,
    certified: Iterable[str] = (),
    sandbox_patterns: Sequence[str] = _DEFAULT_SANDBOX_PATTERNS,
) -> str:
    certified = set(certified)

    if table.fqn in certified:
        return TIER_CERTIFIED
    if any(fnmatch.fnmatch(table.database, p) for p in sandbox_patterns):
        return TIER_SANDBOX
    if not table.is_refreshed(_naive(asof), window_days):
        return TIER_STALE
    if table.producers:
        return TIER_PRODUCTION if table.in_prod else TIER_PIPELINE
    return TIER_UNDOCUMENTED


def _certified_tables(products: Iterable[DataProduct]) -> set:
    certified = set()
    for product in products:
        if product.status in ("certified", "beta"):
            certified.update(product.tables)
    return certified


def _naive(value: dt.datetime) -> dt.datetime:
    """Snapshot timestamps are naive, Glue's are aware. Compare like for like."""
    return value.replace(tzinfo=None) if value.tzinfo else value
