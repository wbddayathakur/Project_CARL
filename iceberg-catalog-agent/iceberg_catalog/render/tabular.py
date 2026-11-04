"""Render the entire catalog as tables and nothing else.

The prose-and-sections layout of the original snapshot buries the logical model
in three places at once: definitions in paragraphs at the top, attributes in
per-database sections, and stale counts in a tail table with a different shape.
Nothing can be sorted, filtered or pivoted without reading the whole document
first.

This renderer flattens all of it. Every fact becomes a row in one of ten
tables, the largest being a single inventory with one row per table name and
every attribute as a column. Paste that into Excel and the questions the
sectioned layout made you read for — which Gold tables have no producer, which
databases exist only in dev, what `dms_oracle_ideal` writes — become sorts.

Derived tables (producer jobs, source systems, cadences, lineage edges) are
pivots of the inventory rather than new information. They are included because
the inventory is 1,100 rows wide and those four questions are the ones actually
asked of it.
"""

from __future__ import annotations

import datetime as dt
from typing import Iterable, Optional

from ..model import Catalog, Table

DASH = "\u2014"
ENVS = ("dev", "qa", "stage", "prod")

# Reproduced from the prose of the original snapshot so the definitions survive
# the move to tabular form. Losing them would make several columns unreadable:
# "Cadence" in particular is meaningless without knowing it is the prod
# schedule and that lower environments may differ.
_COLUMN_DEFINITIONS = [
    (
        "Dev / QA / Stage / Prod",
        "Glue catalog `UpdateTime` for that environment's copy of the table.",
        "For an Iceberg table this moves when a commit publishes a new metadata "
        "file, so it is the last publish the catalog recorded. It is not a read. "
        "A dash means the table does not exist in that environment.",
    ),
    (
        "Source",
        "The system the table is loaded from.",
        "Ideal, CMP and linear-programming tables come from `gabprd`. "
        "Posting-schema tables come from `stwprd`. Salesforce and Metro tables, "
        "including the WRR and LDR feeds, come from Salesforce. A silver or gold "
        "table built from both is marked `gabprd, salesforce`. A dash means the "
        "origin is not in the pipeline configs.",
    ),
    (
        "Producer",
        "The prod job that writes the table.",
        "From `carl-data-engineering/manifests/jobs.yaml` joined through "
        "`producers.yaml`. A dash means the table is being updated in the catalog "
        "but no producer job in that inventory writes it.",
    ),
    (
        "Cadence",
        "The prod producer schedule, in plain language.",
        "Times are in the DAG timezone, Eastern or UTC as noted on each row. "
        "Lower environments sometimes run a different schedule; this column is "
        "always the prod one.",
    ),
    (
        "Consumers",
        "The jobs and steps that read the table.",
        "From `carl-data-engineering/manifests/consumers.yaml`. That inventory is "
        "a static read of prod pipeline code, so the same consumer list applies to "
        "every environment. A dash means no catalogued job reads the table — which "
        "is most of them, because the inventory only records reads it can see in "
        "`carl-data-engineering`.",
    ),
    (
        "Layer",
        "Bronze, silver, gold, landing or audit.",
        "Derived from the database name. `unknown` means the name carries no "
        "layer token.",
    ),
    (
        "Domain",
        "The business domain the database belongs to.",
        "From the `domains` map in config.yaml, falling back to the database name "
        "with its layer and environment suffixes stripped.",
    ),
    (
        "Tier",
        "How safe the table is to cite in a request.",
        "certified, production, pipeline, undocumented, sandbox or stale. See the "
        "tier table below.",
    ),
    (
        "Product",
        "The data product this table physically backs, if any.",
        "From `registry/products.yaml`. A dash means the table exists but nothing "
        "describes it to a business user.",
    ),
]

_TIER_MEANINGS = [
    ("certified", "Bound to a data product. An owner is accountable and the grain is fixed."),
    ("production", "In prod, refreshed inside the window, and a manifest job writes it."),
    ("pipeline", "Refreshed with a known producer, but not yet promoted to prod."),
    ("undocumented", "Refreshing on a schedule, but no catalogued job claims to own it."),
    ("sandbox", "A database whose name marks it as scratch. Never offered."),
    ("stale", "No publish recorded inside the refresh window."),
]


def render(
    catalog: Catalog,
    *,
    timezone_label: str = "Asia/Kolkata",
) -> str:
    out: list = []
    w = out.append

    product_by_table = _product_index(catalog)

    w("# CARL Iceberg catalog — tabular inventory")
    w("")
    w(
        "Every fact in this document is a row. Section 6 is the full inventory, one "
        "row per table name with every attribute as a column; sections 7 to 10 are "
        "pivots of it and carry nothing section 6 does not already hold."
    )
    w("")

    _run(w, catalog, timezone_label)
    _definitions(w)
    _tiers(w)
    _accounts(w, catalog)
    _databases(w, catalog, product_by_table)
    _inventory(w, catalog, product_by_table)
    _lineage(w, catalog)
    _producers(w, catalog)
    _sources(w, catalog)
    _cadences(w, catalog)
    _stale(w, catalog)
    _notes(w, catalog)

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 1. run


def _run(w, catalog: Catalog, timezone_label: str) -> None:
    grouped = catalog.by_database()
    copies = sum(len(t.copies) for t in catalog.tables)
    stale_copies = sum(sum(v.values()) for v in catalog.stale_counts.values())

    rows = [
        ("Generated", f"{catalog.generated_at:%Y-%m-%d %H:%M}"),
        ("Timezone", timezone_label),
        ("Collected from", _source_label(catalog.source)),
        ("Refresh window", f"{catalog.window_days} days"),
        ("Environments", ", ".join(a.environment for a in catalog.accounts) or DASH),
        ("Distinct table names", f"{len(catalog.tables):,}"),
        ("Table copies across environments", f"{copies:,}"),
        ("Databases holding refreshed tables", f"{len(grouped):,}"),
        ("Tables with a catalogued producer", f"{sum(1 for t in catalog.tables if t.producers):,}"),
        ("Tables with a catalogued consumer", f"{sum(1 for t in catalog.tables if t.consumers):,}"),
        ("Tables bound to a data product", f"{sum(1 for t in catalog.tables if t.tier == 'certified'):,}"),
        ("Stale table copies (outside the window)", f"{stale_copies:,}"),
        ("Databases holding stale copies", f"{len(catalog.stale_counts):,}"),
    ]

    w("## 1. Run")
    w("")
    _table(w, ["Field", "Value"], [[k, v] for k, v in rows])


# ---------------------------------------------------------------- 2-3. keys


def _definitions(w) -> None:
    w("## 2. Column definitions")
    w("")
    _table(
        w,
        ["Column", "What it is", "How to read it"],
        [[f"**{name}**", what, how] for name, what, how in _COLUMN_DEFINITIONS],
    )


def _tiers(w) -> None:
    w("## 3. Tier values")
    w("")
    _table(
        w,
        ["Tier", "Meaning"],
        [[f"`{tier}`", meaning] for tier, meaning in _TIER_MEANINGS],
    )


# ---------------------------------------------------------------- 4. accounts


def _accounts(w, catalog: Catalog) -> None:
    w("## 4. Accounts")
    w("")
    if not catalog.accounts:
        _table(w, ["Environment", "Account"], [])
        return
    _table(
        w,
        [
            "Environment",
            "Account",
            "Databases with tables",
            "Tables in catalog",
            "Copies refreshed in window",
        ],
        [
            [
                a.environment,
                f"`{a.account_id}`",
                f"{a.databases_with_tables:,}",
                f"{a.tables_in_catalog:,}",
                f"{a.tables_refreshed:,}",
            ]
            for a in catalog.accounts
        ],
        align=["left", "left", "right", "right", "right"],
    )


# ---------------------------------------------------------------- 5. databases


def _databases(w, catalog: Catalog, product_by_table: dict) -> None:
    grouped = catalog.by_database()

    rows = []
    for index, (database, tables) in enumerate(grouped.items(), start=1):
        first = tables[0]
        per_env = {env: sum(1 for t in tables if env in t.copies) for env in ENVS}
        rows.append(
            [
                str(index),
                f"`{database}`",
                first.layer,
                first.domain,
                f"{len(tables):,}",
                *[_count(per_env[env]) for env in ENVS],
                _count(sum(1 for t in tables if t.producers)),
                _count(sum(1 for t in tables if t.consumers)),
                _count(sum(1 for t in tables if t.fqn in product_by_table)),
                _count(sum(catalog.stale_counts.get(database, {}).values())),
            ]
        )

    w("## 5. Databases")
    w("")
    w(
        f"{len(grouped)} databases holding at least one refreshed table. "
        f"Environment columns count table copies present, not refreshed."
    )
    w("")
    _table(
        w,
        [
            "#",
            "Database",
            "Layer",
            "Domain",
            "Tables",
            "Dev",
            "QA",
            "Stage",
            "Prod",
            "With producer",
            "With consumer",
            "In a product",
            "Stale copies",
        ],
        rows,
        align=["right", "left", "left", "left"] + ["right"] * 9,
    )


# ---------------------------------------------------------------- 6. inventory


def _inventory(w, catalog: Catalog, product_by_table: dict) -> None:
    ordered = sorted(catalog.tables, key=lambda t: (t.database, t.name))

    rows = []
    for index, table in enumerate(ordered, start=1):
        producer, cadence = _split_cadence(table)
        freshest = table.freshest()
        rows.append(
            [
                str(index),
                f"`{table.database}`",
                f"`{table.name}`",
                table.layer,
                table.domain,
                f"`{table.tier}`",
                product_by_table.get(table.fqn, DASH),
                *[_stamp(table, env) for env in ENVS],
                str(len(table.copies)),
                f"{freshest:%Y-%m-%d %H:%M}" if freshest else DASH,
                _cell(table.source_system),
                _cell(producer),
                _cell(cadence),
                _cell("; ".join(table.consumers)),
            ]
        )

    w("## 6. Table inventory")
    w("")
    w(
        f"{len(ordered):,} distinct table names, one row each. A table present in "
        f"four environments is still one row; the environment columns carry its "
        f"four publish timestamps. This is the table to sort and filter — every "
        f"other section is a pivot of it."
    )
    w("")
    _table(
        w,
        [
            "#",
            "Database",
            "Table",
            "Layer",
            "Domain",
            "Tier",
            "Product",
            "Dev",
            "QA",
            "Stage",
            "Prod",
            "Envs",
            "Last refresh",
            "Source",
            "Producer",
            "Cadence",
            "Consumers",
        ],
        rows,
        align=["right", "left", "left", "left", "left", "left", "left"]
        + ["left"] * 4
        + ["right", "left", "left", "left", "left", "left"],
    )


# ---------------------------------------------------------------- 7. lineage


def _lineage(w, catalog: Catalog) -> None:
    rows = []
    index = 0
    for table in sorted(catalog.tables, key=lambda t: (t.database, t.name)):
        for consumer in table.consumers:
            index += 1
            job, _, step = consumer.partition("/")
            rows.append(
                [
                    str(index),
                    f"`{table.database}`",
                    f"`{table.name}`",
                    f"`{job.strip()}`",
                    f"`{step.strip()}`" if step.strip() else DASH,
                ]
            )

    w("## 7. Lineage — table to consumer")
    w("")
    w(
        f"{len(rows)} read edges across "
        f"{len({r[2] for r in rows})} tables. One row per table-consumer pair, so a "
        f"table read by three steps appears three times. Sourced from "
        f"`consumers.yaml`, which only sees reads inside `carl-data-engineering` — "
        f"absence from this table is not evidence that nothing reads it."
    )
    w("")
    _table(
        w,
        ["#", "Database", "Table", "Consumer job", "Consumer step"],
        rows,
        align=["right", "left", "left", "left", "left"],
    )


# ---------------------------------------------------------------- 8. producers


def _producers(w, catalog: Catalog) -> None:
    jobs: dict = {}
    for table in catalog.tables:
        producer, cadence = _split_cadence(table)
        if not producer:
            continue
        entry = jobs.setdefault(
            producer, {"tables": 0, "databases": set(), "cadences": set(), "layers": set()}
        )
        entry["tables"] += 1
        entry["databases"].add(table.database)
        entry["layers"].add(table.layer)
        if cadence:
            entry["cadences"].add(cadence)

    rows = [
        [
            f"`{job}`",
            f"{entry['tables']:,}",
            str(len(entry["databases"])),
            ", ".join(sorted(entry["layers"])),
            _cell("; ".join(sorted(entry["cadences"]))),
            ", ".join(f"`{d}`" for d in sorted(entry["databases"])),
        ]
        for job, entry in sorted(jobs.items(), key=lambda kv: -kv[1]["tables"])
    ]

    w("## 8. Producer jobs")
    w("")
    w(
        f"{len(jobs)} jobs write the "
        f"{sum(1 for t in catalog.tables if t.producers):,} tables that have a "
        f"catalogued producer."
    )
    w("")
    _table(
        w,
        ["Job", "Tables written", "Databases", "Layers", "Cadence", "Writes into"],
        rows,
        align=["left", "right", "right", "left", "left", "left"],
    )


# ---------------------------------------------------------------- 9. sources


def _sources(w, catalog: Catalog) -> None:
    sources: dict = {}
    for table in catalog.tables:
        key = table.source_system or DASH
        entry = sources.setdefault(key, {"tables": 0, "databases": set(), "layers": set()})
        entry["tables"] += 1
        entry["databases"].add(table.database)
        entry["layers"].add(table.layer)

    rows = [
        [
            f"`{source}`" if source != DASH else DASH,
            f"{entry['tables']:,}",
            str(len(entry["databases"])),
            ", ".join(sorted(entry["layers"])),
        ]
        for source, entry in sorted(sources.items(), key=lambda kv: -kv[1]["tables"])
    ]

    w("## 9. Source systems")
    w("")
    _table(
        w,
        ["Source", "Tables", "Databases", "Layers"],
        rows,
        align=["left", "right", "right", "left"],
    )


def _cadences(w, catalog: Catalog) -> None:
    cadences: dict = {}
    for table in catalog.tables:
        _, cadence = _split_cadence(table)
        if not cadence:
            continue
        entry = cadences.setdefault(cadence, {"tables": 0, "jobs": set()})
        entry["tables"] += 1
        producer, _ = _split_cadence(table)
        if producer:
            entry["jobs"].add(producer)

    rows = [
        [cadence, f"{entry['tables']:,}", str(len(entry["jobs"]))]
        for cadence, entry in sorted(cadences.items(), key=lambda kv: -kv[1]["tables"])
    ]

    w("## 10. Refresh cadences")
    w("")
    _table(
        w,
        ["Cadence", "Tables", "Jobs"],
        rows,
        align=["left", "right", "right"],
    )


# ---------------------------------------------------------------- 11. stale


def _stale(w, catalog: Catalog) -> None:
    if not catalog.stale_counts:
        return

    rows = []
    for index, (database, counts) in enumerate(sorted(catalog.stale_counts.items()), start=1):
        rows.append(
            [
                str(index),
                f"`{database}`",
                *[str(counts.get(env, 0)) if counts.get(env) else DASH for env in ENVS],
                f"{sum(counts.values()):,}",
            ]
        )

    total = sum(sum(c.values()) for c in catalog.stale_counts.values())

    w("## 11. Not refreshed in the last 14 days")
    w("")
    w(
        f"{total:,} table copies across {len(catalog.stale_counts)} databases whose "
        f"Glue `UpdateTime` is older than the window in that environment. Counts are "
        f"table copies, not distinct names, and the source does not name them."
    )
    w("")
    _table(
        w,
        ["#", "Database", "Dev", "QA", "Stage", "Prod", "Total"],
        rows,
        align=["right", "left", "right", "right", "right", "right", "right"],
    )


def _notes(w, catalog: Catalog) -> None:
    if not catalog.notes:
        return
    w("## 12. Run notes")
    w("")
    _table(w, ["#", "Note"], [[str(i), n] for i, n in enumerate(catalog.notes, start=1)],
           align=["right", "left"])


# ---------------------------------------------------------------- helpers


def _table(w, headers: list, rows: list, align: Optional[list] = None) -> None:
    w("| " + " | ".join(headers) + " |")

    markers = []
    for index in range(len(headers)):
        side = (align[index] if align and index < len(align) else "left")
        markers.append("---:" if side == "right" else "---")
    w("|" + "|".join(markers) + "|")

    for row in rows:
        w("| " + " | ".join(_escape(cell) for cell in row) + " |")
    w("")


def _escape(value) -> str:
    return " ".join(str(value).split()).replace("|", "\\|") or DASH


def _count(value: int) -> str:
    """Zero reads as a dash, so a column scans for "which have none"."""
    return f"{value:,}" if value else DASH


def _cell(value: Optional[str]) -> str:
    cleaned = " ".join(str(value).split()) if value else ""
    return cleaned or DASH


def _stamp(table: Table, env: str) -> str:
    value = table.last_updated(env)
    return f"{value:%Y-%m-%d %H:%M}" if value else DASH


def _split_cadence(table: Table) -> tuple:
    """Separate the producer job from its schedule.

    The upstream snapshot packs both into one cell as
    "dms_oracle_ideal, every 4 hours (UTC), plus 10:00 ET". The job name is the
    leading comma-delimited token when it looks like an identifier.
    """
    if not table.cadence:
        return (table.producers[0] if table.producers else None), None

    lead, _, rest = table.cadence.partition(",")
    lead = lead.strip()
    if lead and " " not in lead:
        return lead, rest.strip() or None
    return (table.producers[0] if table.producers else None), table.cadence


def _product_index(catalog: Catalog) -> dict:
    index = {}
    for product in catalog.products:
        for fqn in product.tables:
            index[fqn] = f"`{product.product_id}`"
    return index


def _source_label(source: str) -> str:
    return {
        "glue": "live Glue Data Catalog",
        "snapshot": "markdown snapshot",
        "glue+snapshot": "live Glue Data Catalog, gaps filled from the last snapshot",
    }.get(source, source)


def csv_rows(catalog: Catalog) -> Iterable[list]:
    """The inventory as CSV rows, header first.

    Markdown tables cannot be sorted or pivoted. The same inventory is written
    alongside as CSV so it can be opened in Excel, which is where these
    questions actually get answered.
    """
    product_by_table = _product_index(catalog)

    yield [
        "database", "table", "layer", "domain", "tier", "product",
        "dev", "qa", "stage", "prod", "environments", "last_refresh",
        "source", "producer", "cadence", "consumers",
    ]

    for table in sorted(catalog.tables, key=lambda t: (t.database, t.name)):
        producer, cadence = _split_cadence(table)
        freshest = table.freshest()
        yield [
            table.database,
            table.name,
            table.layer,
            table.domain,
            table.tier,
            product_by_table.get(table.fqn, "").strip("`"),
            *[_iso(table.last_updated(env)) for env in ENVS],
            len(table.copies),
            _iso(freshest),
            table.source_system or "",
            producer or "",
            cadence or "",
            "; ".join(table.consumers),
        ]


def _iso(value: Optional[dt.datetime]) -> str:
    return f"{value:%Y-%m-%d %H:%M}" if value else ""
