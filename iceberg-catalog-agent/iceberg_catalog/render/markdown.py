"""Render the catalog as markdown.

Order is the whole argument of this document. It opens with what you can use
today, then the adoption numbers, and only then the full table listing. The
original snapshot opened with the listing, which is correct for an engineer
auditing the estate and wrong for the audience this agent publishes to — a
reader who has to scroll past 1,128 rows to find out whether their question is
already answered will conclude that nothing is, and file a new request.

`sources.snapshot.parse_markdown` can read this output back, but only the
offered tables — stale and sandbox rows are summarised rather than listed, so
the markdown is lossy by design. `sources.previous.load_json` is the
full-fidelity path and is what the agent actually falls back to.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional
from urllib.parse import quote

from ..adoption import AdoptionReport
from ..classify import TIER_CERTIFIED, TIER_SANDBOX, TIER_STALE
from ..model import Catalog, DataProduct

DASH = "\u2014"

_STATUS_NOTE = {
    "certified": "owner accountable, grain fixed, breaking changes announced",
    "beta": "real and refreshing, contract not frozen",
    "proposed": "designed, not built",
    "deprecated": "do not build anything new on this",
}

_FRESHNESS_NOTE = {
    "ok": "within SLA",
    "late": "past SLA but inside twice it",
    "stale": "well past SLA",
    "missing": "no live table found",
    "unknown": "not yet built",
}


def render(
    catalog: Catalog,
    report: AdoptionReport,
    *,
    intake_url: str = "",
    timezone_label: str = "Asia/Kolkata",
) -> str:
    out: list = []
    w = out.append

    generated = catalog.generated_at
    w(f"# CARL Iceberg & Cube {DASH} what's available")
    w("")
    w(
        f"Generated {generated:%Y-%m-%d %H:%M} ({timezone_label}) from the "
        f"{_source_label(catalog.source)}. A table counts as refreshed if the Glue "
        f"catalog recorded a publish inside the last {catalog.window_days} days in "
        f"at least one environment."
    )
    w("")
    w(
        "**Read this before filing an intake request.** If your question is already "
        "answered below, ask to use the existing product rather than to build a new "
        "one. That path is days rather than quarters."
    )
    w("")

    _products(w, catalog, intake_url)
    _adoption(w, report)
    _cube(w, catalog)
    _accounts(w, catalog)
    _listing(w, catalog)
    _notes(w, catalog)

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- products


def _products(w, catalog: Catalog, intake_url: str) -> None:
    products = catalog.products
    if not products:
        return

    available = [p for p in products if p.is_available]
    coming = [p for p in products if p.status == "proposed"]
    other = [p for p in products if p not in available and p not in coming]

    w("## Available now")
    w("")
    if available:
        w(
            f"{len(available)} products you can build on today. Each one has an owner "
            f"who is accountable for it and a grain that will not move without notice."
        )
        w("")
        _product_table(w, available, intake_url)
    else:
        w("No product currently meets the bar for available. See the sections below.")
    w("")

    if other:
        w("### Listed but not currently usable")
        w("")
        w(
            "These are registered products whose bindings did not resolve cleanly this "
            "run — stale, missing from prod, or past their freshness promise. They are "
            "shown rather than hidden so the gap is visible to whoever owns it."
        )
        w("")
        _product_table(w, other, intake_url)
        w("")

    if coming:
        w("### Designed, not yet built")
        w("")
        w(
            "Attach demand to these rather than opening a duplicate request. If you "
            "need one sooner, say so on the intake form and it moves up the queue."
        )
        w("")
        _product_table(w, coming, intake_url, show_gaps=True)
        w("")


def _product_table(w, products: list, intake_url: str, show_gaps: bool = False) -> None:
    header = "| Product | Answers | Domain | Status | Grain | Refresh | Owner |"
    w(header)
    w("|---|---|---|---|---|---|---|")
    for p in sorted(products, key=lambda x: (x.domain, x.product_id)):
        name = f"`{p.product_id}` {p.name}"
        if intake_url:
            name = f"[{p.name}]({_intake_link(intake_url, p, 'reuse')})<br>`{p.product_id}`"
        w(
            "| "
            + " | ".join(
                [
                    name,
                    _clean(p.answers),
                    p.domain,
                    _status_cell(p),
                    _clean(p.grain) or DASH,
                    _clean(p.cadence) or DASH,
                    p.owner or DASH,
                ]
            )
            + " |"
        )
    w("")

    if show_gaps:
        gapped = [p for p in products if p.known_gaps]
        if gapped:
            w("**What is blocking these**")
            w("")
            for p in gapped:
                w(f"- **{p.name}** (`{p.product_id}`)")
                for gap in p.known_gaps:
                    w(f"  - {_clean(gap)}")
            w("")


def _status_cell(product: DataProduct) -> str:
    note = _STATUS_NOTE.get(product.status, "")
    cell = f"**{product.status}**"
    if product.status != "proposed" and product.freshness_state != "ok":
        cell += f" {DASH} {_FRESHNESS_NOTE.get(product.freshness_state, '')}"
    elif note:
        cell += f" {DASH} {note}"
    return cell


def _intake_link(base: str, product: DataProduct, mode: str) -> str:
    joiner = "&" if "?" in base else "?"
    return (
        f"{base}{joiner}product_id={quote(product.product_id)}"
        f"&product_name={quote(product.name)}&mode={mode}"
    )


# ---------------------------------------------------------------- adoption


def _adoption(w, report: AdoptionReport) -> None:
    w("## Adoption")
    w("")

    if report.headlines:
        for line in report.headlines:
            w(f"- {line}")
        w("")

    w("| Metric | This week | Target | Question it answers | Owner |")
    w("|---|---:|---:|---|---|")
    for m in report.metrics:
        verdict = ""
        if m.target_pct is not None:
            verdict = f"{m.target_pct:.0f}%" + (" ✓" if m.meets_target else "")
        w(
            f"| {m.label} | {m.numerator}/{m.denominator} ({m.pct:.0f}%) | "
            f"{verdict or DASH} | {m.question} | {m.owner or DASH} |"
        )
    w("")

    if report.tier_counts:
        w("**Where every table sits**")
        w("")
        w("| Tier | Tables | Meaning |")
        w("|---|---:|---|")
        meanings = {
            "certified": "bound to a data product; safe to cite in a request",
            "production": "in prod, refreshed, and a manifest job writes it",
            "pipeline": "refreshed with a known producer, not yet promoted to prod",
            "undocumented": "refreshing, but no catalogued job claims to own it",
            "sandbox": "scratch database; not offered",
            "stale": "no publish inside the window",
        }
        for tier, count in report.tier_counts.items():
            w(f"| `{tier}` | {count} | {meanings.get(tier, '')} |")
        w("")


# ---------------------------------------------------------------- cube


def _cube(w, catalog: Catalog) -> None:
    if not catalog.cube_views:
        return

    w("## Cube semantic layer")
    w("")
    w(
        "Cube is the governed path to this data — a measure defined here means the "
        "same thing in every dashboard that reads it. Prefer a Cube view over raw "
        "Athena SQL wherever one exists."
    )
    w("")
    w("| View | Backed by | Grain | Measures | Status |")
    w("|---|---|---|---:|---|")
    for v in sorted(catalog.cube_views, key=lambda x: (x.status != "certified", x.name)):
        w(
            f"| `{v.name}` | {f'`{v.source_table}`' if v.source_table else DASH} | "
            f"{_clean(v.grain) or DASH} | {len(v.measures) or DASH} | {v.status} |"
        )
    w("")

    certified = [m for m in catalog.measures if m.status == "certified"]
    if certified:
        w("### Certified measures")
        w("")
        w("| Measure | View | Class | Definition | Basis |")
        w("|---|---|---|---|---|")
        for m in sorted(certified, key=lambda x: x.name):
            w(
                f"| **{m.name}** | `{m.cube_view}` | {m.kpi_class or DASH} | "
                f"{_clean(m.definition) or DASH} | {m.basis or DASH} |"
            )
        w("")


# ---------------------------------------------------------------- estate


def _accounts(w, catalog: Catalog) -> None:
    if not catalog.accounts:
        return
    w("## Accounts")
    w("")
    w("| Environment | Account | Databases with tables | Tables in catalog | Refreshed |")
    w("|---|---|---:|---:|---:|")
    for a in catalog.accounts:
        w(
            f"| {a.environment} | `{a.account_id}` | {a.databases_with_tables} | "
            f"{a.tables_in_catalog} | {a.tables_refreshed} |"
        )
    w("")


def _listing(w, catalog: Catalog) -> None:
    grouped = catalog.by_database()
    offered = {
        db: tables
        for db, tables in grouped.items()
        if any(t.tier not in (TIER_SANDBOX, TIER_STALE) for t in tables)
    }

    total = sum(len(t) for t in grouped.values())
    w("## Full table listing")
    w("")
    w(
        f"{total} tables across {len(grouped)} databases, counted once per name across "
        f"environments. This section is for engineers; a business reader wants the "
        f"products above."
    )
    w("")

    for database, tables in offered.items():
        shown = [t for t in tables if t.tier not in (TIER_SANDBOX, TIER_STALE)]
        if not shown:
            continue
        certified = sum(1 for t in shown if t.tier == TIER_CERTIFIED)
        w(f"### `{database}`")
        w("")
        w(
            f"{len(shown)} refreshed tables. Layer: {shown[0].layer}. "
            f"Domain: {shown[0].domain}. Certified as a product: {certified}."
        )
        w("")
        w("| Table | Dev | QA | Stage | Prod | Source | Cadence | Consumers |")
        w("|---|---|---|---|---|---|---|---|")
        for t in shown:
            w(
                "| "
                + " | ".join(
                    [
                        f"`{t.name}`",
                        _stamp(t, "dev"),
                        _stamp(t, "qa"),
                        _stamp(t, "stage"),
                        _stamp(t, "prod"),
                        t.source_system or DASH,
                        t.cadence or DASH,
                        "; ".join(t.consumers) if t.consumers else DASH,
                    ]
                )
                + " |"
            )
        w("")

    _stale_summary(w, grouped)


def _stale_summary(w, grouped: dict) -> None:
    rows = []
    for database, tables in grouped.items():
        counts = {env: 0 for env in ("dev", "qa", "stage", "prod")}
        for t in tables:
            if t.tier in (TIER_STALE, TIER_SANDBOX):
                for env in t.environments:
                    counts[env] += 1
        if any(counts.values()):
            rows.append((database, counts))

    if not rows:
        return

    w("## Not refreshed, or scratch")
    w("")
    w(
        "These exist in the catalog but are either past the refresh window or sit in a "
        "database marked as scratch. Counts are table copies, not distinct names."
    )
    w("")
    w("| Database | Dev | QA | Stage | Prod |")
    w("|---|---:|---:|---:|---:|")
    for database, counts in rows:
        cells = " | ".join(str(counts[e]) if counts[e] else DASH for e in ("dev", "qa", "stage", "prod"))
        w(f"| `{database}` | {cells} |")
    w("")


def _notes(w, catalog: Catalog) -> None:
    if not catalog.notes:
        return
    w("## Run notes")
    w("")
    for note in catalog.notes:
        w(f"- {note}")
    w("")


# ---------------------------------------------------------------- helpers


def _stamp(table, env: str) -> str:
    value = table.last_updated(env)
    return f"{value:%Y-%m-%d %H:%M}" if value else DASH


def _clean(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(str(value).split()).replace("|", "\\|")


def _source_label(source: str) -> str:
    return {
        "glue": "live Glue Data Catalog",
        "snapshot": "last published markdown snapshot",
        "glue+snapshot": "live Glue Data Catalog, with gaps filled from the last snapshot",
    }.get(source, source)
