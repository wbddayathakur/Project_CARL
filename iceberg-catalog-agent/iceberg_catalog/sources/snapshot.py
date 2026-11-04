"""Read a markdown snapshot back into a `Catalog`.

This is the fallback collector, and it matters more than a fallback usually
would. The agent is expected to run in places that cannot reach the four CARL
accounts — a laptop without a session, a reviewer's machine, a CI job whose
role was not provisioned yet. In all of those the last published markdown is
still a truthful record of what the catalog looked like, so the agent degrades
to re-rendering it rather than failing.

Two layouts are accepted, because both exist in the wild:

**Sectioned** — the original hand-run snapshot. One `## \\`database\\`` heading
per database, each followed by a table whose first column is the table name.
The database comes from the heading rather than from the row.

**Flat** — what `render/tabular.py` emits. One inventory table for the whole
estate, with `Database` as a column. Headers are matched by name, so column
order can change without breaking this.

Both are detected from the shape of each table's header row rather than from a
document-level mode flag, so a file containing both parses correctly and a file
containing neither yields an empty catalog instead of garbage.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Optional

from ..model import Account, Catalog, Table, TableCopy

DASH = {"", "-", "\u2014", "\u2013", "n/a", "N/A"}
ENVS = ("dev", "qa", "stage", "prod")

_DB_HEADING = re.compile(r"^#{2,3}\s+`([^`]+)`\s*$")
_HEADING = re.compile(r"^#{1,6}\s+")
# "## Not refreshed …" in the original, "## 11. Not refreshed …" in the tabular
# layout. The section number is not stable, so it is optional.
_NOT_REFRESHED = re.compile(r"^#{2,3}\s+(?:\d+\.\s*)?Not refreshed", re.IGNORECASE)

_TAKEN = re.compile(r"taken\s+(\d{4}-\d{2}-\d{2})")
_GENERATED_ROW = re.compile(
    r"^\|\s*Generated\s*\|\s*(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?\s*\|", re.IGNORECASE
)
_ACCOUNT_ROW = re.compile(
    r"^\|\s*(dev|qa|stage|prod)\s*\|\s*`?(\d{6,})`?\s*\|([^|]*)\|([^|]*)\|([^|]*)\|"
)

# Header classifications.
_INVENTORY_FLAT = "inventory_flat"
_INVENTORY_SECTIONED = "inventory_sectioned"
_STALE = "stale"
_IGNORE = "ignore"


def parse_markdown(path: str | Path, *, window_days: int = 14) -> Catalog:
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()

    catalog = Catalog(
        generated_at=_parse_generated_at(text, lines),
        source="snapshot",
        window_days=window_days,
        notes=[f"Parsed from markdown snapshot {Path(path).name}."],
    )

    catalog.accounts = _parse_accounts(lines)
    account_by_env = {a.environment: a.account_id for a in catalog.accounts}

    database: Optional[str] = None
    header: Optional[list] = None
    kind: str = _IGNORE
    in_stale_section = False

    for line in lines:
        stripped = line.strip()

        if _HEADING.match(stripped):
            # Any heading ends the current table. Track whether the new section
            # is the stale one, because its rows are counts rather than tables
            # and are only meaningful there.
            in_stale_section = bool(_NOT_REFRESHED.match(stripped))
            heading = _DB_HEADING.match(stripped)
            database = heading.group(1) if heading else None
            header = None
            kind = _IGNORE
            continue

        if not stripped.startswith("|"):
            continue

        cells = _split_row(stripped)
        if not cells or _is_separator(cells):
            continue

        if header is None:
            header = [c.strip().lower() for c in cells]
            kind = _classify(header, in_stale_section)
            continue

        if kind == _INVENTORY_FLAT:
            table = _parse_table_row(header, cells, account_by_env, database=None)
            if table:
                catalog.tables.append(table)
        elif kind == _INVENTORY_SECTIONED and database:
            table = _parse_table_row(header, cells, account_by_env, database=database)
            if table:
                catalog.tables.append(table)
        elif kind == _STALE:
            _parse_stale_row(header, cells, catalog.stale_counts)

    return catalog


def _classify(header: list, in_stale_section: bool) -> str:
    """Decide what a table is from its header row alone.

    Ordering matters. The stale table and the per-database summary table both
    carry `database` and the environment columns, and only the section they sit
    in tells them apart — so the stale check runs first and is gated on that.
    """
    columns = set(header)

    if in_stale_section and "database" in columns and "dev" in columns:
        return _STALE

    # `tables` (a count) is not `table` (a name). The per-database summary in
    # the tabular layout has the former and must not be read as inventory.
    has_name = "table" in columns
    if not has_name or "prod" not in columns:
        return _IGNORE

    return _INVENTORY_FLAT if "database" in columns else _INVENTORY_SECTIONED


def _parse_table_row(
    header: list,
    cells: list,
    account_by_env: dict,
    *,
    database: Optional[str],
) -> Optional[Table]:
    row = dict(zip(header, cells))

    name = _unbacktick(row.get("table", ""))
    resolved_db = database or _unbacktick(row.get("database", ""))
    if not name or not resolved_db:
        return None
    # Guard against reading a separator or a repeated header as data.
    if name.lower() == "table":
        return None

    table = Table(database=resolved_db, name=name)

    for env in ENVS:
        stamp = _parse_timestamp(row.get(env))
        if stamp is None:
            continue
        table.copies[env] = TableCopy(
            environment=env,
            account=account_by_env.get(env, ""),
            last_updated=stamp,
        )

    table.source_system = _clean(row.get("source"))
    table.consumers = _split_list(row.get("consumers"))

    # The tabular layout splits these into two columns; the sectioned one packs
    # both into `cadence` as "job_name, every 4 hours (UTC)".
    producer = _clean(row.get("producer"))
    cadence = _clean(row.get("cadence"))

    if producer:
        table.producers = [producer]
        table.cadence = ", ".join(p for p in (producer, cadence) if p)
    elif cadence:
        table.cadence = cadence
        lead = cadence.split(",", 1)[0].strip()
        if lead and " " not in lead:
            table.producers = [lead]

    return table


def _parse_stale_row(header: list, cells: list, into: dict) -> None:
    row = dict(zip(header, cells))

    database = _unbacktick(row.get("database", ""))
    if not database or database.lower() == "database":
        return

    counts = {}
    for env in ENVS:
        value = _clean(row.get(env))
        if value:
            digits = value.replace(",", "")
            if digits.isdigit():
                counts[env] = int(digits)

    if counts:
        into[database] = counts


def _parse_generated_at(text: str, lines: list) -> dt.datetime:
    match = _TAKEN.search(text)
    if match:
        return dt.datetime.strptime(match.group(1), "%Y-%m-%d")

    for line in lines:
        row = _GENERATED_ROW.match(line.strip())
        if row:
            stamp = row.group(1) + (f" {row.group(2)}" if row.group(2) else "")
            fmt = "%Y-%m-%d %H:%M" if row.group(2) else "%Y-%m-%d"
            return dt.datetime.strptime(stamp, fmt)

    return dt.datetime.now()


def _parse_accounts(lines: list) -> list:
    accounts = []
    for line in lines:
        match = _ACCOUNT_ROW.match(line.strip())
        if not match:
            continue
        env, account_id, databases, in_catalog, refreshed = match.groups()
        accounts.append(
            Account(
                environment=env,
                account_id=account_id,
                databases_with_tables=_as_int(databases),
                tables_in_catalog=_as_int(in_catalog),
                tables_refreshed=_as_int(refreshed),
            )
        )
        if len(accounts) == len(ENVS):
            break
    return accounts


def _split_row(line: str) -> list:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def _is_separator(cells: list) -> bool:
    return all(c and set(c) <= set("-: ") for c in cells)


def _unbacktick(value: str) -> str:
    return value.strip().strip("`").strip()


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = _unbacktick(value)
    return None if value in DASH else value


def _split_list(value: Optional[str]) -> list:
    cleaned = _clean(value)
    if not cleaned:
        return []
    return [part.strip() for part in cleaned.split(";") if part.strip()]


def _as_int(value: str) -> int:
    cleaned = value.strip().replace(",", "")
    return int(cleaned) if cleaned.isdigit() else 0


def _parse_timestamp(value: Optional[str]) -> Optional[dt.datetime]:
    cleaned = _clean(value)
    if not cleaned:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None
