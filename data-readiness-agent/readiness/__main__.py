"""CLI: python3 -m readiness [--today YYYY-MM-DD]"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .inputs import load
from .match import reconcile
from .report import write_outputs
from .score import score


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Evidence-based data-readiness PoC for CARL")
    ap.add_argument("--data-dir", type=Path, default=root / "data")
    ap.add_argument("--config", type=Path, default=root / "config" / "rubric.json")
    ap.add_argument("--out-dir", type=Path, default=root / "out")
    ap.add_argument("--today", type=date.fromisoformat, default=date.today())
    a = ap.parse_args()

    inp = load(a.data_dir, a.config)
    recon = reconcile(inp)
    sc = score(inp, recon)
    write_outputs(a.out_dir, inp, recon, sc, a.today)
    print(f"wrote {a.out_dir}/readiness_report.md, readiness.json, jira_glue_reconciliation.csv")


if __name__ == "__main__":
    main()
