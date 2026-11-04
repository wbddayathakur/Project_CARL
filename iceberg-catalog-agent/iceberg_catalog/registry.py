"""Load the curated product registry and bind it to the physical catalog.

Binding is the part that earns its keep. The registry claims a product is
backed by `linear_digital_revenue_gold.fact_pacing_revenue_budget_month`; this
module checks that against what Glue actually returned this morning and records
the answer. A product whose tables have vanished, or gone stale, or never
reached prod, is downgraded in the published output rather than continuing to
advertise a freshness promise it is not keeping.

That means the catalog cannot drift quietly. The registry is hand-maintained,
so it will go out of date — the design assumption is that it does, and that the
weekly run is what surfaces it.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

import yaml

from .model import Catalog, CubeView, DataProduct, Measure

_KNOWN_FIELDS = set(DataProduct.__dataclass_fields__)  # type: ignore[attr-defined]


def load_products(path: str | Path) -> list:
    """Read products.yaml into `DataProduct` objects."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    products = []

    for entry in raw.get("products", []) or []:
        fields = {k: v for k, v in entry.items() if k in _KNOWN_FIELDS}
        unknown = set(entry) - _KNOWN_FIELDS
        if unknown:
            # Loud, because a mistyped key silently dropping an owner or an SLA
            # is exactly the sort of thing nobody notices for three months.
            raise ValueError(
                f"{entry.get('product_id', '?')}: unrecognised field(s) "
                f"{sorted(unknown)} in products.yaml"
            )
        for key in ("answers", "grain", "cadence"):
            if isinstance(fields.get(key), str):
                fields[key] = " ".join(fields[key].split())
        products.append(DataProduct(**fields))

    _assert_unique_ids(products)
    return products


def load_cube_views(path: str | Path) -> tuple:
    """Read the optional Cube model export into views and measures.

    Used when the Cube REST `/meta` endpoint is not reachable, or when views
    are still on paper — the Ad Products views exist as a design in the Jamie
    workbook long before any YAML is deployed, and intake needs to see them.
    """
    file = Path(path)
    if not file.exists():
        return [], []

    raw = yaml.safe_load(file.read_text(encoding="utf-8")) or {}

    views = [
        CubeView(
            name=v["name"],
            source_table=v.get("source_table"),
            layer=v.get("layer", "unknown"),
            grain=v.get("grain"),
            measures=v.get("measures", []) or [],
            dimensions=v.get("dimensions", []) or [],
            segments=v.get("segments", []) or [],
            status=v.get("status", "proposed"),
        )
        for v in raw.get("views", []) or []
    ]

    measures = [
        Measure(
            name=m["name"],
            cube_view=m.get("cube_view", ""),
            kpi_class=m.get("kpi_class"),
            definition=m.get("definition"),
            expression=m.get("expression"),
            aggregation=m.get("aggregation"),
            basis=m.get("basis"),
            status=m.get("status", "proposed"),
        )
        for m in raw.get("measures", []) or []
    ]

    return views, measures


def bind(catalog: Catalog, *, asof: Optional[dt.datetime] = None) -> Catalog:
    """Resolve each product's table list against the collected catalog.

    Sets `resolved_tables`, `environments`, `freshness_state` and
    `hours_since_refresh`, and appends a note for every binding that does not
    resolve.
    """
    asof = _naive(asof or catalog.generated_at)
    index = catalog.table_index()

    for product in catalog.products:
        resolved = []
        missing = []

        for fqn in product.tables:
            table = index.get(fqn)
            if table is None:
                missing.append(fqn)
            else:
                resolved.append(table)

        product.resolved_tables = resolved

        # A proposed product is *expected* to point at tables that do not exist
        # yet — that is what proposed means. Only warn once something claims to
        # be real.
        if missing and product.status != "proposed":
            catalog.notes.append(
                f"{product.product_id}: {len(missing)} declared table(s) not found "
                f"in the catalog — {', '.join(missing)}."
            )

        # Environments are observed, not declared. A registry entry claiming
        # prod when Glue disagrees should lose the argument.
        observed = sorted(
            {env for table in resolved for env in table.environments},
            key=["dev", "qa", "stage", "prod"].index,
        )
        if observed:
            product.environments = observed
        elif product.status != "proposed":
            catalog.notes.append(
                f"{product.product_id}: marked {product.status} but resolves to no "
                f"live table in any environment."
            )

        product.freshness_state, product.hours_since_refresh = _freshness(
            product, resolved, asof
        )

    return catalog


def _freshness(product: DataProduct, resolved: list, asof: dt.datetime) -> tuple:
    """Grade a product against its own SLA.

    Judged on the *oldest* bound table in prod, not the newest. A product is
    only as fresh as its stalest input, and reporting the newest is how a
    dashboard ends up quietly serving half-updated joins.
    """
    if not resolved:
        return ("missing" if product.status != "proposed" else "unknown"), None

    prod_stamps = [
        t.last_updated("prod") for t in resolved if t.last_updated("prod") is not None
    ]
    stamps = prod_stamps or [t.freshest() for t in resolved if t.freshest()]
    if not stamps:
        return "missing", None

    oldest = min(_naive(s) for s in stamps)
    hours = (asof - oldest).total_seconds() / 3600.0

    sla = product.freshness_sla_hours
    if sla is None:
        state = "ok" if hours <= 24 * 14 else "stale"
    elif hours <= sla:
        state = "ok"
    elif hours <= sla * 2:
        state = "late"
    else:
        state = "stale"

    return state, round(hours, 1)


def _assert_unique_ids(products: list) -> None:
    seen = set()
    for product in products:
        if product.product_id in seen:
            raise ValueError(f"duplicate product_id in products.yaml: {product.product_id}")
        seen.add(product.product_id)


def _naive(value: dt.datetime) -> dt.datetime:
    return value.replace(tzinfo=None) if value.tzinfo else value
