"""Pull today's Iceberg table list from live Glue into iceberg-live-<date>.csv.

Uses the iceberg-catalog-agent collector and the accounts in its config.yaml.
Only glue:GetDatabases and glue:GetTables are called; no table data is read.

Run:  .venv-snowflake/bin/python lakehouse-layer-dashboard-v2/pull_glue.py [--envs dev prod]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = ROOT / "iceberg-catalog-agent"
sys.path.insert(0, str(AGENT_DIR))

from iceberg_catalog.classify import layer_of  # noqa: E402
from iceberg_catalog.sources.glue import collect  # noqa: E402

SSO_PROFILES = {
    "dev": "aws-adsales-iceberg-dev-WBD_Iceberg_Developer",
    "prod": "aws-adsales-iceberg-prod-WBD_Iceberg_Developer",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--envs", nargs="+", default=["dev", "prod"])
    parser.add_argument("--profile", action="append", default=[], metavar="ENV=PROFILE",
                        help="Override the AWS profile for one environment")
    args = parser.parse_args()

    config = yaml.safe_load((AGENT_DIR / "config.yaml").read_text())
    overrides = {**SSO_PROFILES, **dict(p.split("=", 1) for p in args.profile)}
    envs = [{**e, "profile": overrides.get(e["name"], e.get("profile"))}
            for e in config["environments"] if e["name"] in args.envs]
    catalog = collect(
        envs,
        window_days=config["run"]["window_days"],
        iceberg_only=config["run"].get("iceberg_only", True),
        exclude_databases=config.get("exclude_databases", []),
    )

    today = dt.date.today().isoformat()
    out = AGENT_DIR / "out" / f"iceberg-live-{today}.csv"
    names = [e["name"] for e in envs]
    stamp = lambda v: v.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M") if v else ""

    with out.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["database", "layer", "table"] + [f"in_{n}" for n in names] +
                        [f"{n}_last_updated" for n in names] + [f"{n}_location" for n in names])
        for table in sorted(catalog.tables, key=lambda t: (t.database, t.name)):
            copies = [table.copies.get(n) for n in names]
            writer.writerow(
                [table.database, layer_of(table.database), table.name]
                + ["Y" if c else "" for c in copies]
                + [stamp(c.last_updated) if c else "" for c in copies]
                + [(c.location or "") if c else "" for c in copies]
            )

    print(f"Wrote {out} — {len(catalog.tables)} tables")
    for account in catalog.accounts:
        print(f"  {account.environment}: {account.tables_in_catalog} tables in "
              f"{account.databases_with_tables} databases, {account.tables_refreshed} refreshed")
    for note in catalog.notes:
        print("  note:", note)


if __name__ == "__main__":
    main()
