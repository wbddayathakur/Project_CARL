"""Core objects shared by every collector, classifier and renderer.

Two tiers live here and they are deliberately different shapes.

`TableCopy` / `Table` are the *physical* tier: whatever the Glue catalog says
exists, one row per table name with an environment matrix hanging off it. They
are produced by a collector and never hand-edited.

`DataProduct` is the *curated* tier: the small set of things a non-engineer is
allowed to be told about, each one bound to physical tables and Cube views and
carrying an owner, a grain and a freshness promise. It comes from
`registry/products.yaml` and is hand-maintained.

Keeping the tiers apart is the point of the whole agent. The physical tier
answers "does this exist"; the curated tier answers "may I use it, and for
what". An intake form needs the second and drowns in the first.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable

ENVIRONMENTS: tuple[str, ...] = ("dev", "qa", "stage", "prod")

# Ordered most- to least-refined. `unknown` sorts last.
LAYERS: tuple[str, ...] = ("gold", "silver", "bronze", "landing", "audit", "unknown")


@dataclass(frozen=True)
class TableCopy:
    """One table as it exists in one environment."""

    environment: str
    account: str
    last_updated: dt.datetime | None
    location: str | None = None
    table_format: str | None = None
    record_count: int | None = None

    def age_days(self, asof: dt.datetime) -> float | None:
        if self.last_updated is None:
            return None
        return (asof - self.last_updated).total_seconds() / 86400.0


@dataclass
class Table:
    """A table name, and every environment copy of it that was found."""

    database: str
    name: str
    copies: dict[str, TableCopy] = field(default_factory=dict)

    # Pipeline metadata, joined in from the carl-data-engineering manifests.
    source_system: str | None = None
    cadence: str | None = None
    producers: list[str] = field(default_factory=list)
    consumers: list[str] = field(default_factory=list)

    # Filled in by classify.py.
    layer: str = "unknown"
    domain: str = "unassigned"
    tier: str = "unclassified"

    @property
    def fqn(self) -> str:
        return f"{self.database}.{self.name}"

    @property
    def environments(self) -> list[str]:
        return [e for e in ENVIRONMENTS if e in self.copies]

    @property
    def in_prod(self) -> bool:
        return "prod" in self.copies

    def last_updated(self, environment: str = "prod") -> dt.datetime | None:
        copy = self.copies.get(environment)
        return copy.last_updated if copy else None

    def freshest(self) -> dt.datetime | None:
        stamps = [c.last_updated for c in self.copies.values() if c.last_updated]
        return max(stamps) if stamps else None

    def is_refreshed(self, asof: dt.datetime, window_days: int = 14) -> bool:
        freshest = self.freshest()
        return freshest is not None and (asof - freshest).days <= window_days


@dataclass
class Measure:
    """A certified measure exposed by the Cube semantic layer."""

    name: str
    cube_view: str
    kpi_class: str | None = None          # Primary KPI / Child KPI / Derived KPI
    definition: str | None = None          # business-readable formula
    expression: str | None = None          # the Cube/SQL expression
    aggregation: str | None = None
    basis: str | None = None               # Net / Gross / n/a
    status: str = "proposed"               # proposed | certified | deprecated


@dataclass
class CubeView:
    """A view in the Cube semantic layer, and the Iceberg object behind it."""

    name: str
    source_table: str | None = None
    layer: str = "unknown"
    grain: str | None = None
    measures: list[str] = field(default_factory=list)
    dimensions: list[str] = field(default_factory=list)
    segments: list[str] = field(default_factory=list)
    status: str = "proposed"


@dataclass
class DataProduct:
    """The unit an intake request is allowed to reference.

    `answers` is the field that makes the catalog usable by someone who does not
    know the schema: it is the business question, written as a question.
    """

    product_id: str
    name: str
    domain: str
    answers: str
    status: str = "proposed"               # certified | beta | proposed | deprecated
    owner: str | None = None
    steward: str | None = None

    tables: list[str] = field(default_factory=list)      # db.table, physical binding
    cube_views: list[str] = field(default_factory=list)
    measures: list[str] = field(default_factory=list)
    dimensions: list[str] = field(default_factory=list)

    grain: str | None = None
    cadence: str | None = None
    freshness_sla_hours: int | None = None
    environments: list[str] = field(default_factory=list)

    query_athena: str | None = None
    query_cube: str | None = None
    known_gaps: list[str] = field(default_factory=list)
    related_requirements: list[str] = field(default_factory=list)

    # Filled in at build time by joining against the physical tier.
    resolved_tables: list[Table] = field(default_factory=list, repr=False)
    freshness_state: str = "unknown"       # ok | late | stale | missing
    hours_since_refresh: float | None = None

    @property
    def is_available(self) -> bool:
        """Available means: certified or beta, present in prod, and not stale."""
        return (
            self.status in ("certified", "beta")
            and "prod" in self.environments
            and self.freshness_state in ("ok", "late")
        )


@dataclass
class Account:
    environment: str
    account_id: str
    databases_with_tables: int = 0
    tables_in_catalog: int = 0
    tables_refreshed: int = 0


@dataclass
class Catalog:
    """Everything one weekly run produced."""

    generated_at: dt.datetime
    source: str                            # "glue" | "snapshot" | "glue+snapshot"
    window_days: int = 14
    accounts: list[Account] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    products: list[DataProduct] = field(default_factory=list)
    cube_views: list[CubeView] = field(default_factory=list)
    measures: list[Measure] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    # Table copies whose UpdateTime falls outside the window, as a per-database
    # per-environment count. Held as an aggregate rather than as `Table` rows
    # because the upstream snapshot reports it that way — it names no tables,
    # only how many there were.
    stale_counts: dict = field(default_factory=dict)

    def by_database(self) -> dict[str, list[Table]]:
        grouped: dict[str, list[Table]] = {}
        for table in self.tables:
            grouped.setdefault(table.database, []).append(table)
        for tables in grouped.values():
            tables.sort(key=lambda t: t.name)
        return dict(sorted(grouped.items()))

    def table_index(self) -> dict[str, Table]:
        return {t.fqn: t for t in self.tables}

    def find(self, fqn: str) -> Table | None:
        return self.table_index().get(fqn)

    def to_dict(self) -> dict[str, Any]:
        """Plain JSON, which is also the payload the read-only API serves."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "source": self.source,
            "window_days": self.window_days,
            "accounts": [asdict(a) for a in self.accounts],
            "products": [_product_json(p) for p in self.products],
            "cube_views": [asdict(v) for v in self.cube_views],
            "measures": [asdict(m) for m in self.measures],
            "tables": [_table_json(t) for t in self.tables],
            "stale_counts": self.stale_counts,
            "notes": list(self.notes),
        }


def _table_json(table: Table) -> dict[str, Any]:
    return {
        "fqn": table.fqn,
        "database": table.database,
        "name": table.name,
        "layer": table.layer,
        "domain": table.domain,
        "tier": table.tier,
        "source_system": table.source_system,
        "cadence": table.cadence,
        "producers": table.producers,
        "consumers": table.consumers,
        "environments": {
            env: {
                "account": copy.account,
                "last_updated": copy.last_updated.isoformat() if copy.last_updated else None,
                "location": copy.location,
            }
            for env, copy in table.copies.items()
        },
    }


def _product_json(product: DataProduct) -> dict[str, Any]:
    data = asdict(product)
    data.pop("resolved_tables", None)
    data["is_available"] = product.is_available
    return data


def sort_tables(tables: Iterable[Table]) -> list[Table]:
    order = {layer: i for i, layer in enumerate(LAYERS)}
    return sorted(
        tables,
        key=lambda t: (order.get(t.layer, len(LAYERS)), t.database, t.name),
    )
