"""Collect the live Glue Data Catalog across the four CARL accounts.

Each environment is a separate AWS account, so each needs its own credentials.
Two ways are supported per environment and both appear in `config.yaml`:

    profile:  a named profile in ~/.aws/config (what a laptop normally has)
    role_arn: a role this run's base credentials may assume (what CI has)

A run touches only `glue:GetDatabases` and `glue:GetTables`. It never reads
table data, so a read-only catalog policy is enough and no row ever leaves the
account.

Nothing here raises on a single environment failing. An expired session for
`stage` should cost you the stage column, not the whole weekly publish, so the
failure is recorded in `catalog.notes` and the run continues.
"""

from __future__ import annotations

import datetime as dt
import fnmatch
import logging
from typing import Any, Iterator, Optional, Sequence

from ..model import Account, Catalog, Table, TableCopy

log = logging.getLogger(__name__)

# Glue's Iceberg tables carry this in their parameters.
_ICEBERG_MARKERS = ("iceberg", "ICEBERG")


class GlueUnavailable(RuntimeError):
    """boto3 is missing, or no environment could be reached."""


def collect(
    environments: Sequence[dict],
    *,
    window_days: int = 14,
    asof: Optional[dt.datetime] = None,
    iceberg_only: bool = True,
    exclude_databases: Sequence[str] = (),
) -> Catalog:
    """Build a `Catalog` from live Glue.

    `environments` is the `environments:` block of config.yaml — a list of
    dicts with `name`, `account_id`, `region`, and one of `profile`/`role_arn`.
    """
    try:
        import boto3  # noqa: F401
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise GlueUnavailable(
            "boto3 is not installed. Run: pip install -r requirements.txt"
        ) from exc

    asof = asof or dt.datetime.now(dt.timezone.utc)
    catalog = Catalog(generated_at=asof, source="glue", window_days=window_days)

    merged: dict[str, Table] = {}
    reached = 0

    for env_config in environments:
        env = env_config["name"]
        try:
            client = _client(env_config)
        except Exception as exc:
            catalog.notes.append(f"{env}: could not authenticate ({exc}).")
            log.warning("skipping %s: %s", env, exc)
            continue

        try:
            account = Account(
                environment=env,
                account_id=str(env_config.get("account_id", "")),
            )
            databases = [
                db
                for db in _databases(client)
                if not _excluded(db, exclude_databases)
            ]

            for database in databases:
                found_any = False
                for raw in _tables(client, database):
                    if iceberg_only and not _is_iceberg(raw):
                        continue
                    found_any = True
                    account.tables_in_catalog += 1

                    copy = _to_copy(raw, env, account.account_id)
                    if copy.last_updated and (asof - _aware(copy.last_updated)).days <= window_days:
                        account.tables_refreshed += 1

                    key = f"{database}.{raw['Name']}"
                    table = merged.get(key)
                    if table is None:
                        table = Table(database=database, name=raw["Name"])
                        merged[key] = table
                    table.copies[env] = copy

                if found_any:
                    account.databases_with_tables += 1

            catalog.accounts.append(account)
            reached += 1
        except Exception as exc:
            catalog.notes.append(f"{env}: collection failed partway ({exc}).")
            log.warning("collection failed for %s: %s", env, exc)

    if reached == 0:
        raise GlueUnavailable(
            "No environment could be reached. Check credentials, or run with "
            "--source snapshot to re-render the last published markdown."
        )
    if reached < len(environments):
        catalog.notes.append(
            f"Partial run: {reached} of {len(environments)} environments reached. "
            "Columns for the missing environments are blank, not empty."
        )

    catalog.tables = list(merged.values())
    return catalog


def _client(env_config: dict):
    import boto3

    region = env_config.get("region", "us-east-1")

    if env_config.get("role_arn"):
        sts = boto3.client("sts")
        assumed = sts.assume_role(
            RoleArn=env_config["role_arn"],
            RoleSessionName="iceberg-catalog-agent",
        )
        creds = assumed["Credentials"]
        return boto3.client(
            "glue",
            region_name=region,
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
        )

    session = boto3.Session(profile_name=env_config.get("profile"))
    return session.client("glue", region_name=region)


def _databases(client) -> Iterator[str]:
    paginator = client.get_paginator("get_databases")
    for page in paginator.paginate():
        for database in page.get("DatabaseList", []):
            yield database["Name"]


def _tables(client, database: str) -> Iterator[dict]:
    paginator = client.get_paginator("get_tables")
    for page in paginator.paginate(DatabaseName=database):
        for table in page.get("TableList", []):
            yield table


def _is_iceberg(raw: dict) -> bool:
    params = {k.lower(): str(v) for k, v in (raw.get("Parameters") or {}).items()}
    table_type = params.get("table_type", "")
    if any(marker.lower() in table_type.lower() for marker in _ICEBERG_MARKERS):
        return True
    # Some writers only set metadata_location rather than table_type.
    return "metadata_location" in params


def _to_copy(raw: dict, environment: str, account: str) -> TableCopy:
    storage = raw.get("StorageDescriptor") or {}
    params = raw.get("Parameters") or {}
    record_count = params.get("recordCount")

    return TableCopy(
        environment=environment,
        account=account,
        last_updated=raw.get("UpdateTime"),
        location=storage.get("Location"),
        table_format="iceberg" if _is_iceberg(raw) else None,
        record_count=int(record_count) if str(record_count).isdigit() else None,
    )


def _excluded(database: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(database, pattern) for pattern in patterns)


def _aware(value: dt.datetime) -> dt.datetime:
    """Glue returns tz-aware stamps; snapshots parse naive ones. Normalise."""
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.timezone.utc)
    return value
