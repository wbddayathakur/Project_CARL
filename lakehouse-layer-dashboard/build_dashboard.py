"""Build a single-file HTML dashboard of what sits in Bronze, Silver, Gold and Cube.

Sources, all already in this repo:

    iceberg-catalog-agent/out/iceberg-live-<date>.csv     physical tables, live Glue (dev + prod)
    iceberg-catalog-agent/out/iceberg-catalog.json        producers, source systems, consumers
    iceberg-catalog-agent/registry/*.yaml                 curated data products, designed Cube views
    iceberg-catalog-agent/config.yaml                     domain patterns
    CARL_Cube_Semantic_Layer_Data_Inventory.xlsx          deployed Cube views, view fields, cubes

Run:  .venv/bin/python lakehouse-layer-dashboard/build_dashboard.py
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

import yaml

ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = ROOT / "iceberg-catalog-agent"
sys.path.insert(0, str(AGENT_DIR))

from iceberg_catalog.classify import _DEFAULT_SANDBOX_PATTERNS, domain_of, layer_of  # noqa: E402

AGENT_OUT = AGENT_DIR / "out"
WINDOW_DAYS = 14
LAYERS = ("bronze", "silver", "gold")


def latest_live_csv() -> Path:
    files = sorted(AGENT_OUT.glob("iceberg-live-*.csv"))
    if not files:
        raise SystemExit("No iceberg-live-*.csv in iceberg-catalog-agent/out")
    return files[-1]


def parse_ts(value: str):
    return dt.datetime.strptime(value, "%Y-%m-%d %H:%M") if value else None


def load_cube(xlsx: Path):
    wb = openpyxl.load_workbook(xlsx, read_only=True)

    def rows(sheet):
        it = wb[sheet].iter_rows(values_only=True)
        header = next(it)
        return [dict(zip(header, r)) for r in it if any(r)]

    return rows("Views (query these)"), rows("View fields"), rows("All cubes")


def split_tables(value) -> list:
    return [s for s in re.split(r"[,\s]+", value or "") if "." in s]


def build(out_path: Path) -> dict:
    live_csv = latest_live_csv()
    asof = dt.datetime.strptime(re.search(r"\d{4}-\d{2}-\d{2}", live_csv.name).group(), "%Y-%m-%d")
    catalog = json.loads((AGENT_OUT / "iceberg-catalog.json").read_text())
    domain_map = yaml.safe_load((AGENT_DIR / "config.yaml").read_text())["domains"]
    products = yaml.safe_load((AGENT_DIR / "registry" / "products.yaml").read_text())["products"]
    registry_views = yaml.safe_load((AGENT_DIR / "registry" / "cube_model.yaml").read_text())["views"]
    views, view_fields, cubes = load_cube(ROOT / "CARL_Cube_Semantic_Layer_Data_Inventory.xlsx")

    prior = {t["fqn"]: t for t in catalog["tables"]}
    product_of = {}
    for p in products:
        for fqn in p.get("tables") or []:
            product_of.setdefault(fqn, p["product_id"])
    certified = {fqn for p in products if p["status"] in ("certified", "beta") for fqn in p.get("tables") or []}

    # Cube source tables are written as e.g. dwhprd_gold.x; in Glue that is carl_dwhprd_gold_dev.x.
    cube_by_source = defaultdict(set)
    for c in cubes:
        for src in split_tables(c.get("Source table(s)")):
            cube_by_source[src].add(c["Cube"])
    view_by_source = defaultdict(set)
    for v in views:
        for src in split_tables(v.get("Base table")):
            view_by_source[src].add(v["View name"])
    for cv in registry_views:
        if cv.get("source_table"):
            view_by_source[cv["source_table"]].add(cv["name"])

    def cube_keys(database: str, table: str) -> list:
        keys = [f"{database}.{table}"]
        stem = re.sub(r"_(dev|qa|stage|prod)$", "", database)
        keys.append(f"{stem}.{table}")
        if stem.startswith("carl_"):
            keys.append(f"{stem[5:]}.{table}")
        return keys

    tables = []
    for row in csv.DictReader(live_csv.open()):
        db, name = row["database"], row["table"]
        fqn = f"{db}.{name}"
        p = prior.get(fqn, {})
        dev_ts, prod_ts = parse_ts(row["dev_last_updated"]), parse_ts(row["prod_last_updated"])
        last = max([t for t in (dev_ts, prod_ts) if t], default=None)
        in_prod = row["in_prod"] == "Y"
        producers = p.get("producers") or []

        if fqn in certified:
            tier = "certified"
        elif any(fnmatch.fnmatch(db, pat) for pat in _DEFAULT_SANDBOX_PATTERNS):
            tier = "sandbox"
        elif not last or (asof - last).days > WINDOW_DAYS:
            tier = "stale"
        elif producers:
            tier = "production" if in_prod else "pipeline"
        else:
            tier = "undocumented"

        cube_hits, view_hits = set(), set()
        for key in cube_keys(db, name):
            cube_hits |= cube_by_source.get(key, set())
            view_hits |= view_by_source.get(key, set())

        tables.append({
            "db": db,
            "t": name,
            "layer": row["layer"] if row["layer"] in LAYERS else layer_of(db) if layer_of(db) in LAYERS else "other",
            "domain": domain_of(db, domain_map),
            "tier": tier,
            "dev": row["in_dev"] == "Y",
            "prod": in_prod,
            "devTs": row["dev_last_updated"],
            "prodTs": row["prod_last_updated"],
            "src": p.get("source_system") or "",
            "producer": ", ".join(producers),
            "consumers": len(p.get("consumers") or []),
            "cubes": sorted(cube_hits),
            "views": sorted(view_hits),
            "product": product_of.get(fqn, ""),
        })

    fields_by_view = defaultdict(list)
    for f in view_fields:
        fields_by_view[f["View"]].append({
            "type": f["Type"], "name": f["Field (as exposed)"], "title": f["Title"],
            "dtype": f["Data type / agg"], "desc": f["Description"] or "",
            "cube": f["Source cube"], "member": f["Source member"],
        })

    deployed = {v["View name"] for v in views}
    cube_views = [{
        "domain": v["Domain"], "name": v["View name"], "title": v["Title"], "business": v["Business"] or "",
        "base": v["Base table"], "measures": v["# Measures"], "dims": v["# Dimensions"],
        "joins": v["# Cubes joined"], "access": v["Access policy"], "desc": v["Description"] or "",
        "file": v["File"], "status": "deployed", "fields": fields_by_view.get(v["View name"], []),
    } for v in views]
    for cv in registry_views:
        if cv["name"] in deployed:
            continue
        cube_views.append({
            "domain": "Registry — " + ("certified" if cv["status"] == "certified" else "designed, not deployed"),
            "name": cv["name"], "title": cv["name"].replace("_", " ").title(), "business": cv["name"].split("_view_")[0],
            "base": cv.get("source_table") or "", "measures": len(cv.get("measures") or []),
            "dims": len(cv.get("dimensions") or []), "joins": None, "access": "",
            "desc": "Grain: " + (cv.get("grain") or "").strip(), "file": "registry/cube_model.yaml",
            "status": cv["status"],
            "fields": [{"type": "measure", "name": m, "title": m, "dtype": "", "desc": "", "cube": "", "member": ""}
                       for m in cv.get("measures") or []] +
                      [{"type": "dimension", "name": d, "title": d, "dtype": "", "desc": "", "cube": "", "member": ""}
                       for d in cv.get("dimensions") or []],
        })

    cube_list = [{
        "domain": c["Domain"], "name": c["Cube"], "title": c["Title"], "kind": c["Kind"],
        "src": c["Source table(s)"] or "", "sql": c["Query-backed SQL"], "measures": c["# Measures"],
        "dims": c["# Dimensions"], "joins": c["Joins to"] or "", "preagg": c["Pre-aggregations"] or "",
        "views": c["Used in views"] or "", "desc": c["Description"] or "", "file": c["File"],
    } for c in cubes]

    payload = {
        "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "asof": asof.strftime("%Y-%m-%d"),
        "windowDays": WINDOW_DAYS,
        "sources": {
            "physical": f"iceberg-catalog-agent/out/{live_csv.name} (live Glue, dev + prod accounts)",
            "enrichment": f"iceberg-catalog-agent/out/iceberg-catalog.json (run {catalog['generated_at'][:10]})",
            "registry": "iceberg-catalog-agent/registry/products.yaml + cube_model.yaml",
            "cube": "CARL_Cube_Semantic_Layer_Data_Inventory.xlsx",
        },
        "tables": tables,
        "cubeViews": cube_views,
        "cubes": cube_list,
        "products": [{
            "id": p["product_id"], "name": p["name"], "domain": p["domain"], "status": p["status"],
            "answers": p.get("answers") or "", "tables": p.get("tables") or [], "views": p.get("cube_views") or [],
            "grain": p.get("grain") or "", "gaps": p.get("known_gaps") or [],
        } for p in products],
    }

    template = (Path(__file__).parent / "template.html").read_text()
    html = template.replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":"), default=str))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).parent / "out" / "CARL_Lakehouse_Layers_Dashboard.html")
    args = parser.parse_args()
    payload = build(args.out)
    counts = Counter(t["layer"] for t in payload["tables"])
    print(f"Wrote {args.out}")
    print("  " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())),
          f"| cube views={len(payload['cubeViews'])} cubes={len(payload['cubes'])}")


if __name__ == "__main__":
    main()
