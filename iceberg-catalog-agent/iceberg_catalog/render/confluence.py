"""Render the catalog as Confluence storage format (XHTML).

Confluence is not a markdown host, so this is a separate renderer rather than a
conversion. It uses the two macros that actually change how the page reads:
`status` for the coloured product/tier lozenges, and `expand` to fold the
1,128-row listing away so the page opens on the products instead of on a wall
of table names.

Everything is escaped. Table names, job names and free-text gap notes all come
from upstream systems, and one stray `&` in a cadence string is enough to make
Confluence reject the whole page body.
"""

from __future__ import annotations

from typing import Iterable, Optional
from urllib.parse import quote
from xml.sax.saxutils import escape, quoteattr

from ..adoption import AdoptionReport
from ..classify import TIER_SANDBOX, TIER_STALE
from ..model import Catalog, DataProduct

DASH = "\u2014"

_STATUS_COLOUR = {
    "certified": "Green",
    "beta": "Blue",
    "proposed": "Grey",
    "deprecated": "Red",
}

_FRESHNESS_COLOUR = {"ok": "Green", "late": "Yellow", "stale": "Red", "missing": "Red"}

_TIER_COLOUR = {
    "certified": "Green",
    "production": "Blue",
    "pipeline": "Yellow",
    "undocumented": "Yellow",
    "sandbox": "Grey",
    "stale": "Red",
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

    w(
        _panel(
            "info",
            f"<p><strong>Read this before filing an intake request.</strong> If your "
            f"question is already answered by a product below, ask to use it rather "
            f"than to build something new. That path is days rather than quarters.</p>"
            f"<p>Regenerated automatically every week. Last run "
            f"{escape(f'{catalog.generated_at:%Y-%m-%d %H:%M}')} ({escape(timezone_label)}) "
            f"from the {escape(_source_label(catalog.source))}.</p>",
        )
    )

    _products(w, catalog, intake_url)
    _adoption(w, report)
    _cube(w, catalog)
    _estate(w, catalog)
    _notes(w, catalog)

    return "".join(out)


# ---------------------------------------------------------------- products


def _products(w, catalog: Catalog, intake_url: str) -> None:
    if not catalog.products:
        return

    available = [p for p in catalog.products if p.is_available]
    coming = [p for p in catalog.products if p.status == "proposed"]
    other = [p for p in catalog.products if p not in available and p not in coming]

    w("<h2>Available now</h2>")
    if available:
        w(
            f"<p>{len(available)} products you can build on today. Each has an owner "
            f"accountable for it and a grain that will not move without notice.</p>"
        )
        w(_product_table(available, intake_url))
    else:
        w("<p>No product currently meets the bar for available.</p>")

    if other:
        w("<h2>Listed but not currently usable</h2>")
        w(
            "<p>Registered products whose bindings did not resolve cleanly this run "
            "— stale, missing from prod, or past their freshness promise. Shown "
            "rather than hidden so the gap is visible to whoever owns it.</p>"
        )
        w(_product_table(other, intake_url))

    if coming:
        w("<h2>Designed, not yet built</h2>")
        w(
            "<p>Attach demand to these rather than opening a duplicate request. If you "
            "need one sooner, say so on the intake form and it moves up the queue.</p>"
        )
        w(_product_table(coming, intake_url))
        w(_gaps(coming))


def _product_table(products: Iterable, intake_url: str) -> str:
    rows = [
        _tr(
            [
                _product_cell(p, intake_url),
                escape(_clean(p.answers)),
                escape(p.domain),
                _status_cell(p),
                escape(_clean(p.grain) or DASH),
                escape(_clean(p.cadence) or DASH),
                escape(p.owner or DASH),
            ]
        )
        for p in sorted(products, key=lambda x: (x.domain, x.product_id))
    ]
    return _table(
        ["Product", "Answers", "Domain", "Status", "Grain", "Refresh", "Owner"], rows
    )


def _product_cell(product: DataProduct, intake_url: str) -> str:
    name = f"<strong>{escape(product.name)}</strong>"
    if intake_url:
        href = _intake_link(intake_url, product, "reuse")
        name = f"<a href={quoteattr(href)}>{escape(product.name)}</a>"
    return f"{name}<br/><code>{escape(product.product_id)}</code>"


def _status_cell(product: DataProduct) -> str:
    cell = _status(_STATUS_COLOUR.get(product.status, "Grey"), product.status)
    if product.status != "proposed" and product.freshness_state != "ok":
        cell += " " + _status(
            _FRESHNESS_COLOUR.get(product.freshness_state, "Grey"),
            product.freshness_state,
        )
    return cell


def _gaps(products: Iterable) -> str:
    gapped = [p for p in products if p.known_gaps]
    if not gapped:
        return ""
    body = ["<p><strong>What is blocking these</strong></p><ul>"]
    for p in gapped:
        body.append(f"<li><strong>{escape(p.name)}</strong><ul>")
        for gap in p.known_gaps:
            body.append(f"<li>{escape(_clean(gap))}</li>")
        body.append("</ul></li>")
    body.append("</ul>")
    return "".join(body)


def _intake_link(base: str, product: DataProduct, mode: str) -> str:
    joiner = "&" if "?" in base else "?"
    return (
        f"{base}{joiner}product_id={quote(product.product_id)}"
        f"&product_name={quote(product.name)}&mode={mode}"
    )


# ---------------------------------------------------------------- adoption


def _adoption(w, report: AdoptionReport) -> None:
    w("<h2>Adoption</h2>")

    if report.headlines:
        w("<ul>" + "".join(f"<li>{escape(h)}</li>" for h in report.headlines) + "</ul>")

    rows = []
    for m in report.metrics:
        if m.target_pct is None:
            verdict = DASH
        else:
            colour = "Green" if m.meets_target else "Yellow"
            verdict = _status(colour, f"target {m.target_pct:.0f}%")
        rows.append(
            _tr(
                [
                    escape(m.label),
                    f"<strong>{m.pct:.0f}%</strong><br/>{m.numerator} of {m.denominator}",
                    verdict,
                    escape(m.question),
                    escape(m.owner or DASH),
                ]
            )
        )
    w(_table(["Metric", "This week", "Target", "Question it answers", "Owner"], rows))

    if report.tier_counts:
        meanings = {
            "certified": "bound to a data product; safe to cite in a request",
            "production": "in prod, refreshed, and a manifest job writes it",
            "pipeline": "refreshed with a known producer, not yet promoted to prod",
            "undocumented": "refreshing, but no catalogued job claims to own it",
            "sandbox": "scratch database; not offered",
            "stale": "no publish inside the window",
        }
        rows = [
            _tr(
                [
                    _status(_TIER_COLOUR.get(tier, "Grey"), tier),
                    str(count),
                    escape(meanings.get(tier, "")),
                ]
            )
            for tier, count in report.tier_counts.items()
        ]
        w("<h3>Where every table sits</h3>")
        w(_table(["Tier", "Tables", "Meaning"], rows))


# ---------------------------------------------------------------- cube


def _cube(w, catalog: Catalog) -> None:
    if not catalog.cube_views:
        return
    w("<h2>Cube semantic layer</h2>")
    w(
        "<p>Cube is the governed path to this data — a measure defined here means the "
        "same thing in every dashboard that reads it. Prefer a Cube view over raw "
        "Athena SQL wherever one exists.</p>"
    )
    rows = [
        _tr(
            [
                f"<code>{escape(v.name)}</code>",
                f"<code>{escape(v.source_table)}</code>" if v.source_table else DASH,
                escape(_clean(v.grain) or DASH),
                str(len(v.measures)) if v.measures else DASH,
                _status(_STATUS_COLOUR.get(v.status, "Grey"), v.status),
            ]
        )
        for v in sorted(catalog.cube_views, key=lambda x: (x.status != "certified", x.name))
    ]
    w(_table(["View", "Backed by", "Grain", "Measures", "Status"], rows))


# ---------------------------------------------------------------- estate


def _estate(w, catalog: Catalog) -> None:
    if catalog.accounts:
        w("<h2>Accounts</h2>")
        rows = [
            _tr(
                [
                    escape(a.environment),
                    f"<code>{escape(a.account_id)}</code>",
                    str(a.databases_with_tables),
                    str(a.tables_in_catalog),
                    str(a.tables_refreshed),
                ]
            )
            for a in catalog.accounts
        ]
        w(
            _table(
                ["Environment", "Account", "Databases with tables", "Tables in catalog", "Refreshed"],
                rows,
            )
        )

    grouped = catalog.by_database()
    if not grouped:
        return

    total = sum(len(t) for t in grouped.values())
    body = [
        f"<p>{total} tables across {len(grouped)} databases, counted once per name "
        f"across environments. This is the engineering view; a business reader wants "
        f"the products above.</p>"
    ]

    for database, tables in grouped.items():
        shown = [t for t in tables if t.tier not in (TIER_SANDBOX, TIER_STALE)]
        if not shown:
            continue
        body.append(f"<h3><code>{escape(database)}</code></h3>")
        body.append(
            f"<p>{len(shown)} refreshed tables. Layer: {escape(shown[0].layer)}. "
            f"Domain: {escape(shown[0].domain)}.</p>"
        )
        rows = [
            _tr(
                [
                    f"<code>{escape(t.name)}</code>",
                    _stamp(t, "dev"),
                    _stamp(t, "qa"),
                    _stamp(t, "stage"),
                    _stamp(t, "prod"),
                    escape(t.source_system or DASH),
                    escape(t.cadence or DASH),
                    escape("; ".join(t.consumers) if t.consumers else DASH),
                ]
            )
            for t in shown
        ]
        body.append(
            _table(
                ["Table", "Dev", "QA", "Stage", "Prod", "Source", "Cadence", "Consumers"],
                rows,
            )
        )

    w("<h2>Full table listing</h2>")
    w(_expand("Open the full listing", "".join(body)))


def _notes(w, catalog: Catalog) -> None:
    if not catalog.notes:
        return
    w(
        _panel(
            "note",
            "<p><strong>Run notes</strong></p><ul>"
            + "".join(f"<li>{escape(n)}</li>" for n in catalog.notes)
            + "</ul>",
        )
    )


# ---------------------------------------------------------------- primitives


def _table(headers: list, rows: list) -> str:
    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _tr(cells: list) -> str:
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def _status(colour: str, text: str) -> str:
    return (
        '<ac:structured-macro ac:name="status">'
        f'<ac:parameter ac:name="colour">{escape(colour)}</ac:parameter>'
        f'<ac:parameter ac:name="title">{escape(text)}</ac:parameter>'
        "</ac:structured-macro>"
    )


def _panel(kind: str, body: str) -> str:
    return (
        f'<ac:structured-macro ac:name="{escape(kind)}">'
        f"<ac:rich-text-body>{body}</ac:rich-text-body>"
        "</ac:structured-macro>"
    )


def _expand(title: str, body: str) -> str:
    return (
        '<ac:structured-macro ac:name="expand">'
        f'<ac:parameter ac:name="title">{escape(title)}</ac:parameter>'
        f"<ac:rich-text-body>{body}</ac:rich-text-body>"
        "</ac:structured-macro>"
    )


def _stamp(table, env: str) -> str:
    value = table.last_updated(env)
    return escape(f"{value:%Y-%m-%d %H:%M}") if value else DASH


def _clean(value: Optional[str]) -> str:
    return " ".join(str(value).split()) if value else ""


def _source_label(source: str) -> str:
    return {
        "glue": "live Glue Data Catalog",
        "snapshot": "last published markdown snapshot",
        "glue+snapshot": "live Glue Data Catalog, with gaps filled from the last snapshot",
    }.get(source, source)
