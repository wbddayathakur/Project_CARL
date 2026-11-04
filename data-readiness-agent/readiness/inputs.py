"""Load the three real inputs and classify each Glue table (source, layer, noise)."""
from __future__ import annotations

import csv
import fnmatch
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

LAYER_SUFFIXES = ("_bronze", "_silver", "_gold", "_dev", "_raw")


@dataclass
class Table:
    db: str
    name: str
    layer: str
    in_dev: bool
    in_prod: bool
    dev_updated: Optional[date]
    prod_updated: Optional[date]
    source: str = ""
    noise: bool = False
    sandbox_db: bool = False
    history: Optional[dict] = None  # prod load history row, if any

    @property
    def fqn(self) -> str:
        return f"{self.db}.{self.name}"


@dataclass
class Inputs:
    tables: List[Table]
    jira: dict
    cfg: dict
    glue_as_of: date
    history_as_of: date
    jira_as_of: date
    history_tables: int = 0
    history_unmatched: int = 0
    notes: List[str] = field(default_factory=list)


def _d(s: str) -> Optional[date]:
    s = (s or "").strip()
    return date.fromisoformat(s[:10]) if s else None


def _any(name: str, patterns) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def source_for(db: str, table: str, cfg: dict) -> str:
    for rule in cfg["sources"]:
        if not fnmatch.fnmatch(db, rule["db"]):
            continue
        prefixes = rule.get("table_prefix")
        if prefixes and not any(table.startswith(p) for p in prefixes):
            continue
        return rule["name"]
    root, changed = db, True
    while changed:
        changed = False
        for suf in LAYER_SUFFIXES:
            if root.endswith(suf):
                root, changed = root[: -len(suf)], True
    return root


def load(data_dir: Path, cfg_path: Path) -> Inputs:
    cfg = json.loads(cfg_path.read_text())

    glue_files = sorted(data_dir.glob("glue_inventory_*.csv"))
    hist_files = sorted(data_dir.glob("prod_load_history_*.json"))
    if not glue_files or not hist_files:
        raise FileNotFoundError("expected glue_inventory_*.csv and prod_load_history_*.json in data dir")
    glue_as_of = date.fromisoformat(glue_files[-1].stem.split("_")[-1])
    history_as_of = date.fromisoformat(hist_files[-1].stem.split("_")[-1])

    tables: Dict[tuple, Table] = {}
    with glue_files[-1].open() as f:
        for r in csv.DictReader(f):
            t = Table(
                db=r["database"],
                name=r["table"],
                layer=r["layer"],
                in_dev=r["in_dev"] == "Y",
                in_prod=r["in_prod"] == "Y",
                dev_updated=_d(r.get("dev_last_updated", "")),
                prod_updated=_d(r.get("prod_last_updated", "")),
            )
            t.source = source_for(t.db, t.name, cfg)
            t.noise = _any(t.name, cfg["noise_table_patterns"])
            t.sandbox_db = _any(t.db, cfg["sandbox_db_patterns"])
            tables[(t.db, t.name)] = t

    history = json.loads(hist_files[-1].read_text())
    unmatched = 0
    for h in history:
        t = tables.get((h["db"], h["table"]))
        if t is None:
            unmatched += 1
        else:
            t.history = h

    jira = json.loads((data_dir / "jira_snapshot.json").read_text())
    return Inputs(
        tables=list(tables.values()),
        jira=jira,
        cfg=cfg,
        glue_as_of=glue_as_of,
        history_as_of=history_as_of,
        jira_as_of=date.fromisoformat(jira["retrieved"]),
        history_tables=len(history),
        history_unmatched=unmatched,
    )


def in_scope(t: Table) -> bool:
    """A table is scored only if it is in a real DB, is not noise, and has a medallion layer."""
    return t.layer in ("bronze", "silver", "gold") and not t.sandbox_db and not t.noise
