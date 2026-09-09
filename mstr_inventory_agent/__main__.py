"""CLI entry point: python -m mstr_inventory_agent [--source-dir DIR] [--out FILE]"""

import argparse
import sys

from .agent import InventoryAgent
from .config import DEFAULT_SOURCE_DIR
from .loaders import SourceError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstr_inventory_agent",
        description="Consolidate US Ad Sales MicroStrategy exports into one master inventory.",
    )
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE_DIR,
                        help="Folder holding the MSTR .xls exports")
    parser.add_argument("--out", default=None,
                        help="Output .xlsx path (default: master inventory in the source folder)")
    parser.add_argument("--csv-dir", default=None,
                        help="Optional folder to also write the master inventory as CSV")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    agent = InventoryAgent(args.source_dir, args.out, verbose=not args.quiet)
    try:
        path = agent.run()
    except SourceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.csv_dir:
        import os
        os.makedirs(args.csv_dir, exist_ok=True)
        csv_path = os.path.join(args.csv_dir, "master_inventory.csv")
        agent.master.to_csv(csv_path, index=False)
        if not args.quiet:
            print(f"CSV written: {csv_path}")

    print(f"\nInventory written to:\n  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
