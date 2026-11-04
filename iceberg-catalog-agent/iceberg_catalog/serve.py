"""A read-only JSON API over the last run.

This is the "live API" half of the brief. The weekly job writes
`out/iceberg-catalog.json`; this serves it, so the API is always exactly what
was published to Confluence and the two can never disagree.

The endpoint that matters is `/search`. It is what an intake form calls while
someone is still typing their request, so the form can say "three existing
products already answer something like this" before the request is ever filed.
Deflecting a duplicate at that moment is worth more than any amount of catalog
browsing after the fact.

    GET /health
    GET /catalog                    everything
    GET /products                   ?domain= &status= &available=true
    GET /products/<product_id>
    GET /tables                     ?q= &domain= &layer= &tier= &env= &limit=
    GET /adoption
    GET /search?q=<free text>       ranked products and tables

Stdlib only, single-threaded, no auth. It binds to localhost by default and is
meant to sit behind whatever already fronts your internal services.
"""

from __future__ import annotations

import json
import logging
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from .config import Config

log = logging.getLogger(__name__)

_WORD = re.compile(r"[a-z0-9]+")

# Requests arrive as sentences ("how is my team pacing against budget"), and
# the product descriptions are also prose, so the two overlap on filler words
# and every product matches everything. Scoring these at zero is the whole
# difference between a useful verdict and a list of ten irrelevant products.
_STOPWORDS = frozenset(
    """
    a an and any are as at be been by can could do does for from get give had has have
    how i if in into is it its me my need needs of on or our out over show than that the
    their them then there these they this to up us use used using want was we what when
    where which who why will with would you your against about across per each
    data table tables report reporting dashboard view
    """.split()
)


def serve(config: Config, *, port: int = 8787, host: str = "127.0.0.1") -> int:
    payload_path = config.output_dir / "iceberg-catalog.json"
    if not payload_path.exists():
        print(
            f"No catalog at {payload_path}. Run `python -m iceberg_catalog` first."
        )
        return 2

    handler = _make_handler(payload_path)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Serving {payload_path.name} on http://{host}:{port}  (ctrl-c to stop)")
    print(f"  try: http://{host}:{port}/search?q=pacing")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()
    return 0


def _make_handler(payload_path: Path):
    class Handler(BaseHTTPRequestHandler):
        server_version = "iceberg-catalog-agent"
        _cache: dict = {"mtime": None, "data": None}

        def log_message(self, fmt, *args):  # quieter than the default
            log.debug(fmt, *args)

        # The file is rewritten weekly by a separate process, so reload it when
        # its mtime moves rather than caching for the life of the server.
        def payload(self) -> dict:
            mtime = payload_path.stat().st_mtime
            if self._cache["mtime"] != mtime:
                Handler._cache = {
                    "mtime": mtime,
                    "data": json.loads(payload_path.read_text(encoding="utf-8")),
                }
            return self._cache["data"]

        def do_GET(self):  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            query = {k: v[0] for k, v in parse_qs(parsed.query).items()}

            try:
                status, body = self.route(path, query)
            except Exception as exc:  # pragma: no cover
                log.exception("request failed")
                status, body = 500, {"error": str(exc)}

            encoded = json.dumps(body, indent=2, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(encoded)

        def route(self, path: str, query: dict):
            data = self.payload()

            if path in ("/", "/health"):
                return 200, {
                    "status": "ok",
                    "generated_at": data.get("generated_at"),
                    "source": data.get("source"),
                    "products": len(data.get("products", [])),
                    "tables": len(data.get("tables", [])),
                    "endpoints": [
                        "/catalog",
                        "/products",
                        "/products/<product_id>",
                        "/tables",
                        "/adoption",
                        "/search?q=",
                    ],
                }

            if path == "/catalog":
                return 200, data

            if path == "/adoption":
                return 200, data.get("adoption", {})

            if path == "/products":
                return 200, {"products": _filter_products(data["products"], query)}

            if path.startswith("/products/"):
                wanted = path.split("/", 2)[2].upper()
                product = next(
                    (p for p in data["products"] if p["product_id"].upper() == wanted),
                    None,
                )
                if product is None:
                    return 404, {"error": f"no product {wanted}"}
                product = dict(product)
                index = {t["fqn"]: t for t in data["tables"]}
                product["resolved_tables"] = [
                    index[fqn] for fqn in product.get("tables", []) if fqn in index
                ]
                return 200, product

            if path == "/tables":
                return 200, {"tables": _filter_tables(data["tables"], query)}

            if path == "/search":
                term = query.get("q", "").strip()
                if not term:
                    return 400, {"error": "pass ?q=<what you are looking for>"}
                return 200, _search(data, term, int(query.get("limit", 10)))

            return 404, {"error": f"no route {path}"}

    return Handler


def _filter_products(products: list, query: dict) -> list:
    results = products
    if "domain" in query:
        results = [p for p in results if p["domain"].lower() == query["domain"].lower()]
    if "status" in query:
        results = [p for p in results if p["status"] == query["status"]]
    if query.get("available", "").lower() in ("1", "true", "yes"):
        results = [p for p in results if p.get("is_available")]
    return results


def _filter_tables(tables: list, query: dict) -> list:
    results = tables
    for key in ("domain", "layer", "tier"):
        if key in query:
            results = [t for t in results if str(t.get(key, "")).lower() == query[key].lower()]
    if "env" in query:
        results = [t for t in results if query["env"] in (t.get("environments") or {})]
    if "q" in query:
        needle = query["q"].lower()
        results = [t for t in results if needle in t["fqn"].lower()]
    limit = int(query.get("limit", 200))
    return results[:limit]


def _search(data: dict, term: str, limit: int) -> dict:
    """Rank products above tables for the same score.

    A product match is a better answer than a table match even when the table
    matched more strongly, because the product comes with an owner and a
    grain and the table comes with neither.
    """
    tokens = {t for t in _WORD.findall(term.lower()) if t not in _STOPWORDS and len(t) > 2}
    if not tokens:
        return {
            "query": term,
            "verdict": "Nothing specific enough to search on — name a metric, a "
                       "business area or a system.",
            "products": [],
            "tables": [],
        }

    scored_products = []
    for product in data.get("products", []):
        score = _score_product(tokens, product)
        if score >= _RELEVANCE_FLOOR:
            scored_products.append((score, product))

    scored_tables = []
    for table in data.get("tables", []):
        haystack = " ".join(
            [
                table["fqn"],
                str(table.get("domain", "")),
                str(table.get("layer", "")),
                str(table.get("source_system", "") or ""),
            ]
        )
        score = _score(tokens, haystack)
        if score:
            if table.get("tier") == "certified":
                score += 2
            elif table.get("tier") in ("sandbox", "stale"):
                score -= 2
            scored_tables.append((score, table))

    scored_products.sort(key=lambda pair: -pair[0])
    scored_tables.sort(key=lambda pair: -pair[0])

    products = [p for _, p in scored_products[:limit]]
    tables = [t for _, t in scored_tables[:limit]]

    return {
        "query": term,
        "verdict": _verdict(products, tables),
        "products": products,
        "tables": tables,
    }


def _verdict(products: list, tables: list) -> str:
    """The single sentence an intake form shows the requester.

    Available and proposed products are reported together rather than the
    second only when the first is empty. A request that exactly describes a
    product already on the roadmap is the most valuable thing this endpoint can
    catch — it is a duplicate build about to be scoped — and hiding it behind a
    weaker available match defeats the purpose.
    """
    available = [p for p in products if p.get("is_available")]
    proposed = [p for p in products if p.get("status") == "proposed"]

    parts = []
    if available:
        names = _names(available)
        parts.append(
            f"{_count(len(available), 'existing product')} may already answer this: "
            f"{names}. Ask to use one before requesting a new build."
        )
    if proposed:
        names = _names(proposed)
        lead = (
            "Also designed but not yet built"
            if available
            else "Nothing is available yet, but these are already designed"
        )
        parts.append(
            f"{lead}: {names}. Attach your demand to one rather than opening a duplicate."
        )

    if parts:
        return " ".join(parts)
    if tables:
        return (
            f"No published product matches, but {_count(len(tables), 'table')} in the "
            f"lakehouse look related. A data engineer should confirm before new work "
            f"is scoped."
        )
    return "Nothing in the catalog matches. This looks like genuinely new demand."


def _names(products: list, limit: int = 3) -> str:
    shown = ", ".join(p["name"] for p in products[:limit])
    extra = len(products) - limit
    return f"{shown}, and {extra} more" if extra > 0 else shown


def _count(n: int, noun: str) -> str:
    return f"{n} {noun}" + ("" if n == 1 else "s")


# Fields are weighted because they are not equally diagnostic. A hit on the
# product name or on the business question it answers means the product is
# probably the answer; a hit on the domain only means it is in roughly the
# right part of the business, which is true of most things.
_PRODUCT_FIELD_WEIGHTS = (
    ("name", 4),
    ("answers", 3),
    ("product_id", 3),
    ("measures", 2),
    ("dimensions", 2),
    ("tables", 2),
    ("cube_views", 2),
    ("grain", 1),
    ("domain", 1),
)

# A single weak hit — one token, in one low-weight field — is noise. Two points
# is the lowest score a name or answers match can produce.
_RELEVANCE_FLOOR = 2


def _score_product(tokens: set, product: dict) -> int:
    score = 0
    for field, weight in _PRODUCT_FIELD_WEIGHTS:
        value = product.get(field)
        if not value:
            continue
        text = " ".join(value) if isinstance(value, list) else str(value)
        score += weight * _score(tokens, text)

    if score == 0:
        return 0

    # Only ever a tie-break between things that actually matched. Applied
    # before the relevance check it would float every available product to the
    # top of every search, including searches about nothing in the catalog.
    if product.get("is_available"):
        score += 2
    return score


def _score(tokens: set, haystack: str) -> int:
    lowered = haystack.lower()
    words = set(_WORD.findall(lowered))
    score = 0
    for token in tokens:
        if token in words:
            score += 3          # whole-word hit
        elif len(token) > 3 and token in lowered:
            score += 1          # substring hit, e.g. "pacing" inside a table name
    return score
