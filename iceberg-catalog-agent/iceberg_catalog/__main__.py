"""Command line entry point.

    python -m iceberg_catalog                          collect live, write to out/
    python -m iceberg_catalog --publish                and update the Confluence page
    python -m iceberg_catalog --source snapshot \
        --snapshot path/to/last.md                     re-render without AWS
    python -m iceberg_catalog serve                    read-only JSON API on :8787
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import agent, config as config_module

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="iceberg-catalog-agent",
        description="Publish what's available in the CARL Iceberg lakehouse and Cube "
        "semantic layer, and the adoption numbers that go with it.",
    )
    parser.add_argument("command", nargs="?", default="run", choices=["run", "serve"])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--source",
        choices=["auto", "glue", "snapshot"],
        default="auto",
        help="auto tries Glue and falls back to --snapshot; glue fails hard instead",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="markdown snapshot to parse, or to fall back to when Glue is unreachable",
    )
    parser.add_argument("--publish", action="store_true", help="update the Confluence page")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="with --publish, render and validate but do not write to Confluence",
    )
    parser.add_argument(
        "--tabular-out",
        type=Path,
        help="also write the fully tabular inventory to this path, keeping a .bak "
        "of whatever was there. Safe to point at the input snapshot.",
    )
    parser.add_argument("--port", type=int, default=8787, help="port for serve")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if not args.config.exists():
        print(f"No config at {args.config}", file=sys.stderr)
        return 2

    config = config_module.load(args.config)

    if args.command == "serve":
        from .serve import serve

        return serve(config, port=args.port)

    result = agent.run(
        config,
        source=args.source,
        snapshot_path=args.snapshot,
        publish=args.publish,
        dry_run=args.dry_run,
        tabular_out=args.tabular_out,
    )

    _summarise(result)
    return 0


def _summarise(result: agent.RunResult) -> None:
    catalog = result.catalog
    report = result.report

    available = sum(1 for p in catalog.products if p.is_available)
    proposed = sum(1 for p in catalog.products if p.status == "proposed")

    print()
    print(f"Source            {catalog.source}")
    print(f"Generated         {catalog.generated_at:%Y-%m-%d %H:%M}")
    print(f"Tables            {len(catalog.tables)} across {len(catalog.by_database())} databases")
    print(f"Products          {available} available, {proposed} designed but not built")
    print()
    print("Adoption")
    for metric in report.metrics:
        verdict = ""
        if metric.target_pct is not None:
            verdict = "  (target {:.0f}%{})".format(
                metric.target_pct, ", met" if metric.meets_target else ", not met"
            )
        print(
            f"  {metric.pct:5.1f}%  {metric.label}"
            f"  [{metric.numerator}/{metric.denominator}]{verdict}"
        )

    if report.headlines:
        print()
        print("Headlines")
        for line in report.headlines:
            print(f"  - {line}")

    print()
    for name, path in result.outputs.items():
        print(f"{name:<18}{path}")

    if result.published_url:
        print(f"{'published':<18}{result.published_url}")

    if catalog.notes:
        print()
        print("Notes")
        for note in catalog.notes:
            print(f"  - {note}")


if __name__ == "__main__":
    raise SystemExit(main())
