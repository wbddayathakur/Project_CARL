"""Build v2 of the CARL Lakehouse dashboard: layers, Cube, roadmap, relationship map, risks.

Evidence, all refreshed by the pull_* scripts in this folder:

    iceberg-catalog-agent/out/iceberg-live-<date>.csv   live Glue, dev + prod     (pull_glue.py)
    evidence/cube-models-<env>-<date>/                   deployed Cube model, S3   (pull_cube.py)
    inputs/jira-live-<date>.json                         live Jira epic progress   (pull_jira.py)

Context, refreshed by hand:

    iceberg-catalog-agent/out/iceberg-catalog.json       producers, source systems (catalog agent run)
    iceberg-catalog-agent/registry/*.yaml                curated products, designed Cube views
    inputs/roadmap_v3_relationships.json                 roadmap items and relationships (Strategic Roadmap v3)
    inputs/roadmap_lanes.yaml                            how items roll up into executive roadmap rows
    inputs/risks.yaml                                    external dependencies and program risks

Run:  .venv/bin/python lakehouse-layer-dashboard-v2/build_dashboard_v2.py
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

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
AGENT_DIR = ROOT / "iceberg-catalog-agent"
sys.path.insert(0, str(AGENT_DIR))
sys.path.insert(0, str(HERE))

from iceberg_catalog.classify import _DEFAULT_SANDBOX_PATTERNS, domain_of, layer_of  # noqa: E402

import cube_model  # noqa: E402

AGENT_OUT = AGENT_DIR / "out"
WINDOW_DAYS = 14
LAYERS = ("bronze", "silver", "gold")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def latest(paths) -> Path:
    paths = sorted(paths, key=lambda p: DATE.search(p.name).group())
    if not paths:
        raise SystemExit("missing evidence — run the pull_* scripts first")
    return paths[-1]


def file_date(path: Path) -> str:
    return DATE.search(path.name).group()


def parse_ts(value: str):
    return dt.datetime.strptime(value, "%Y-%m-%d %H:%M") if value else None


def split_tables(value) -> list:
    return [s for s in re.split(r"[,\s]+", value or "") if "." in s]


def matches(db: str, patterns) -> bool:
    return any(fnmatch.fnmatch(db, p) for p in patterns or [])


# ---------------------------------------------------------------- physical

def physical_tables(live_csv: Path, asof: dt.datetime, catalog: dict, products: list,
                    cube: dict, registry_views: list) -> list:
    prior = {t["fqn"]: t for t in catalog["tables"]}
    domain_map = yaml.safe_load((AGENT_DIR / "config.yaml").read_text())["domains"]
    product_of = {}
    for p in products:
        for fqn in p.get("tables") or []:
            product_of.setdefault(fqn, p["product_id"])
    certified = {fqn for p in products if p["status"] in ("certified", "beta") for fqn in p.get("tables") or []}

    cube_by_source, view_by_source = defaultdict(set), defaultdict(set)
    for c in cube["cubes"]:
        for src in split_tables(c["src"]):
            cube_by_source[src].add(c["name"])
    for v in cube["views"]:
        for src in split_tables(v["base"]):
            view_by_source[src].add(v["name"])
    for cv in registry_views:
        if cv.get("source_table"):
            view_by_source[cv["source_table"]].add(cv["name"])

    def cube_keys(database: str, table: str) -> list:
        stem = re.sub(r"_(dev|qa|stage|prod)$", "", database)
        keys = [f"{database}.{table}", f"{stem}.{table}"]
        if stem.startswith("carl_"):
            keys.append(f"{stem[5:]}.{table}")
        return keys

    tables = []
    for row in csv.DictReader(live_csv.open()):
        db, name = row["database"], row["table"]
        fqn = f"{db}.{name}"
        p = prior.get(fqn, {})
        dev_ts, prod_ts = parse_ts(row.get("dev_last_updated", "")), parse_ts(row.get("prod_last_updated", ""))
        last = max([t for t in (dev_ts, prod_ts) if t], default=None)
        in_prod = row.get("in_prod") == "Y"
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

        layer = row["layer"] if row["layer"] in LAYERS else layer_of(db)
        tables.append({
            "db": db, "t": name,
            "layer": layer if layer in LAYERS else "other",
            "domain": domain_of(db, domain_map), "tier": tier,
            "dev": row.get("in_dev") == "Y", "prod": in_prod,
            "devTs": row.get("dev_last_updated", ""), "prodTs": row.get("prod_last_updated", ""),
            "src": p.get("source_system") or "", "producer": ", ".join(producers),
            "consumers": len(p.get("consumers") or []),
            "cubes": sorted(cube_hits), "views": sorted(view_hits),
            "product": product_of.get(fqn, ""),
        })
    return tables


def layer_counts(csv_path: Path) -> dict:
    out = Counter()
    for row in csv.DictReader(csv_path.open()):
        layer = row["layer"] if row["layer"] in LAYERS else "other"
        out[layer] += 1
        out["total"] += 1
        if row.get("in_prod") == "Y":
            out[layer + "_prod"] += 1
            out["prod"] += 1
    return dict(out)


# ---------------------------------------------------------------- cube

def cube_payload(dev_dir: Path, prod_dir: Path, registry_views: list) -> dict:
    model = cube_model.build(dev_dir, prod_dir)
    deployed = {v["name"] for v in model["views"]}
    views = list(model["views"])
    for cv in registry_views:
        if cv["name"] in deployed:
            continue
        views.append({
            "domain": "Registry — " + ("certified" if cv["status"] == "certified" else "designed, not deployed"),
            "name": cv["name"], "title": cv["name"].replace("_", " ").title(), "business": cv["name"].split("_view_")[0],
            "base": cv.get("source_table") or "", "measures": len(cv.get("measures") or []),
            "dims": len(cv.get("dimensions") or []), "joins": None, "access": "",
            "desc": "Grain: " + " ".join((cv.get("grain") or "").split()), "file": "registry/cube_model.yaml",
            "status": cv["status"], "envs": [],
            "fields": [{"type": "measure", "name": m, "title": m, "dtype": "", "desc": "", "cube": "", "member": ""}
                       for m in cv.get("measures") or []] +
                      [{"type": "dimension", "name": d, "title": d, "dtype": "", "desc": "", "cube": "", "member": ""}
                       for d in cv.get("dimensions") or []],
        })
    return {"views": views, "cubes": model["cubes"]}


def deploy_stamp(model_dir: Path) -> str:
    manifest = json.loads((model_dir / "_manifest.json").read_text())
    return max(m["modified"] for m in manifest)[:16].replace("T", " ")


# ---------------------------------------------------------------- roadmap

def epic_keys(raw) -> list:
    return ["CARL-" + re.sub(r"\D", "", p) for p in re.split(r"[/,\s]+", str(raw or "")) if re.search(r"\d", p)]


def item_state(item: dict, jira: dict) -> dict:
    epics = [jira[k] for k in epic_keys(item.get("k")) if k in jira]
    tickets = sum(e["tickets"] for e in epics)
    done = sum(e["done"] for e in epics)
    inprog = sum(e["inprog"] for e in epics)
    sp, sp_done = sum(e["sp"] for e in epics), sum(e["spDone"] for e in epics)
    if epics:
        cats = {e["category"] for e in epics}
        if cats == {"done"}:
            state = "delivered"
        elif "indeterminate" in cats or done or inprog or "done" in cats:
            state = "inprogress"
        else:
            state = "planned"
        status = " / ".join(dict.fromkeys(e["status"] for e in epics))
    else:
        state = {"Done": "delivered", "To Do": "planned", "In Triage": "planned", "Pending Scope": "planned"}.get(item["st"], "inprogress")
        status = item["st"]
    if state == "delivered":
        pct = 100
    elif sp:
        pct = round(100 * sp_done / sp)
    elif tickets:
        pct = round(100 * done / tickets)
    else:
        pct = 0
    end = (item.get("a") if state == "delivered" else None) or item.get("fc") or item.get("t") or item.get("a") or ""
    start = item.get("s") or ""
    return {
        "id": item["id"], "name": item["n"], "keys": epic_keys(item.get("k")), "status": status, "state": state,
        "pct": pct, "tickets": tickets, "done": done, "sp": round(sp), "spDone": round(sp_done),
        "start": start, "end": end, "delivered": item.get("a") if state == "delivered" else "",
        "owner": item.get("o") or "", "use": item.get("use") or "", "pri": item.get("pri") or "",
    }


def footprint(tables: list, patterns) -> dict:
    if not patterns:
        return {}
    rows = [t for t in tables if matches(t["db"], patterns)]
    out = {l: sum(t["layer"] == l for t in rows) for l in LAYERS}
    out["prod"] = sum(t["prod"] for t in rows)
    out["total"] = len(rows)
    out["dbs"] = sorted({t["db"] for t in rows})
    return out


def roadmap_payload(lanes_cfg: dict, v3: dict, jira: dict, tables: list) -> dict:
    items = {i["id"]: i for i in v3["ITEMS"]}
    lanes, row_of = [], {}
    for lane in lanes_cfg["lanes"]:
        rows = []
        for r in lane["rows"]:
            states = [item_state(items[i], jira) for i in r["items"] if i in items]
            for s in states:
                row_of[s["id"]] = r["id"]
            starts = [s["start"] for s in states if s["start"]] + [s["end"] for s in states if s["end"] and not s["start"]]
            ends = [s["end"] for s in states if s["end"]]
            weight = sum(max(s["sp"], 1) for s in states) or 1
            pct = round(sum(s["pct"] * max(s["sp"], 1) for s in states) / weight)
            kinds = {s["state"] for s in states}
            state = "delivered" if kinds == {"delivered"} else "planned" if kinds <= {"planned"} else "inprogress"
            rows.append({
                "id": r["id"], "name": r["name"], "note": r.get("note", ""), "lane": lane["id"],
                "start": min(starts) if starts else "", "end": max(ends) if ends else "",
                "pct": pct, "state": state, "items": states,
                "tickets": sum(s["tickets"] for s in states), "done": sum(s["done"] for s in states),
                "footprint": footprint(tables, r.get("dbs")),
            })
        lanes.append({"id": lane["id"], "name": lane["name"], "blurb": lane["blurb"], "rows": rows})
    return {"window": lanes_cfg["window"], "lanes": lanes, "rowOf": row_of}


def relationship_payload(v3: dict, roadmap: dict) -> dict:
    """Aggregate item-level links into row-level links. External dependency nodes are left out."""
    row_of = roadmap["rowOf"]
    lane_of = {r["id"]: lane["id"] for lane in roadmap["lanes"] for r in lane["rows"]}
    edges = Counter()
    detail = defaultdict(list)
    names = {i["id"]: i["n"] for i in v3["ITEMS"]}
    for a, b, kind in v3["RELS"]:
        if kind not in ("doc", "inf") or a not in row_of or b not in row_of:
            continue
        ra, rb = row_of[a], row_of[b]
        if ra == rb:
            continue
        edges[(ra, rb)] += 1
        detail[f"{ra}>{rb}"].append([names[a], names[b], kind])
    return {
        "edges": [{"a": a, "b": b, "n": n, "la": lane_of[a], "lb": lane_of[b]} for (a, b), n in edges.items()],
        "detail": detail,
    }


# ---------------------------------------------------------------- risks

def risks_payload(cfg: dict, facts: dict) -> dict:
    def fill(obj):
        if isinstance(obj, str):
            return obj.format(**facts)
        if isinstance(obj, list):
            return [fill(x) for x in obj]
        if isinstance(obj, dict):
            return {k: fill(v) for k, v in obj.items()}
        return obj
    return fill(cfg)


# ---------------------------------------------------------------- main

def build(out_path: Path) -> dict:
    live_csv = latest(AGENT_OUT.glob("iceberg-live-*.csv"))
    prev_csv = sorted((p for p in AGENT_OUT.glob("iceberg-live-*.csv") if p != live_csv), key=file_date)
    asof = dt.datetime.strptime(file_date(live_csv), "%Y-%m-%d")
    dev_dir = latest((HERE / "evidence").glob("cube-models-dev-*"))
    prod_dir = latest((HERE / "evidence").glob("cube-models-prod-*"))
    jira_file = latest((HERE / "inputs").glob("jira-live-*.json"))

    catalog = json.loads((AGENT_OUT / "iceberg-catalog.json").read_text())
    products = yaml.safe_load((AGENT_DIR / "registry" / "products.yaml").read_text())["products"]
    registry_views = yaml.safe_load((AGENT_DIR / "registry" / "cube_model.yaml").read_text())["views"]
    v3 = json.loads((HERE / "inputs" / "roadmap_v3_relationships.json").read_text())
    jira = json.loads(jira_file.read_text())
    lanes_cfg = yaml.safe_load((HERE / "inputs" / "roadmap_lanes.yaml").read_text())
    risks_cfg = yaml.safe_load((HERE / "inputs" / "risks.yaml").read_text())

    cube = cube_payload(dev_dir, prod_dir, registry_views)
    tables = physical_tables(live_csv, asof, catalog, products, cube, registry_views)
    roadmap = roadmap_payload(lanes_cfg, v3, jira["epics"], tables)
    relmap = relationship_payload(v3, roadmap)

    deployed = [v for v in cube["views"] if v["status"] == "deployed"]
    count = lambda db, layer: sum(t["prod"] for t in tables if t["db"].startswith(db) and t["layer"] == layer)
    facts = {
        "cube_views": len(deployed), "cube_prod_views": sum("prod" in v["envs"] for v in deployed),
        "fw_bronze_prod": count("freewheel", "bronze"), "fw_silver_prod": count("freewheel", "silver"),
        "op1_bronze_prod": count("operative", "bronze"),
    }

    payload = {
        "version": "v2",
        "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "asof": asof.strftime("%Y-%m-%d"),
        "windowDays": WINDOW_DAYS,
        "evidence": {
            "glue": {"file": f"iceberg-catalog-agent/out/{live_csv.name}", "date": file_date(live_csv), "label": "live Glue, dev + prod accounts"},
            "cube": {"dev": deploy_stamp(dev_dir), "prod": deploy_stamp(prod_dir),
                     "label": "deployed Cube model, s3://carl-cube-models-us-east-1-{dev,prod}/staging/core"},
            "jira": {"pulled": jira["pulled"], "label": "live Jira (CARL epics and child tickets)"},
        },
        "sources": {
            "physical": f"iceberg-catalog-agent/out/{live_csv.name} (live Glue, dev + prod accounts)",
            "cube": f"Cube model from S3 — dev deployed {deploy_stamp(dev_dir)} UTC, prod deployed {deploy_stamp(prod_dir)} UTC",
            "jira": f"Jira live, pulled {jira['pulled']}",
            "enrichment": f"iceberg-catalog-agent/out/iceberg-catalog.json (producers, run {catalog['generated_at'][:10]})",
            "registry": "iceberg-catalog-agent/registry/products.yaml + cube_model.yaml",
            "roadmap": "CARL_Strategic_Roadmap_Swimlane_v3.html; CARL_2026Q4_QuarterlyPlanning,Status&Roadmap(Q4 Roadmap + Status).csv; CARL_Program_Roadmap_v4 1-2026-11-04.html",
        },
        "previous": {"date": file_date(prev_csv[-1]), **layer_counts(prev_csv[-1])} if prev_csv else None,
        "current": layer_counts(live_csv),
        "tables": tables,
        "cubeViews": cube["views"],
        "cubes": cube["cubes"],
        "products": [{
            "id": p["product_id"], "name": p["name"], "domain": p["domain"], "status": p["status"],
            "answers": " ".join((p.get("answers") or "").split()), "tables": p.get("tables") or [],
            "views": p.get("cube_views") or [], "grain": p.get("grain") or "",
            "gaps": [" ".join(g.split()) for g in p.get("known_gaps") or []],
        } for p in products],
        "roadmap": roadmap,
        "relmap": relmap,
        "risks": risks_payload(risks_cfg, facts),
    }

    template = (HERE / "template_v2.html").read_text()
    html = template.replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":"), default=str))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=HERE / "out" / "CARL_Lakehouse_Layers_Dashboard_v2.html")
    args = parser.parse_args()
    payload = build(args.out)
    counts = Counter(t["layer"] for t in payload["tables"])
    print(f"Wrote {args.out}")
    print("  " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())),
          f"| cube views={len(payload['cubeViews'])} cubes={len(payload['cubes'])}",
          f"| roadmap rows={sum(len(l['rows']) for l in payload['roadmap']['lanes'])}",
          f"| relationship links={len(payload['relmap']['edges'])}")


if __name__ == "__main__":
    main()
