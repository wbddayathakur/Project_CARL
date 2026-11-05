"""Read the deployed Cube model (YAML pulled from the carl-cube-models S3 buckets).

Produces the same view / field / cube records the v1 dashboard took from
CARL_Cube_Semantic_Layer_Data_Inventory.xlsx, plus which environments each one
is deployed to.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

CATALOG = re.compile(r"\{\{\s*catalog\(\s*['\"](\w+)['\"]\s*\)\s*\}\}")
JINJA = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.S)
TABLE_REF = re.compile(r"\b([a-z][a-z0-9_]*_(?:bronze|silver|gold|serving|canonical)[a-z0-9_]*)\.([a-z0-9_]+)", re.I)

DOMAIN_LABELS = {
    "Lumos": "Lumos (DWH gold – linear ad sales, finance, intl, content)",
    "Neo": "NEO (digital ad delivery – FreeWheel)",
    "Venus": "Venus (iDeal modernization – impressions)",
    "linear_digital_revenue": "Linear/Digital revenue (Salesforce, exec)",
    "operative": "Operative One (digital orders)",
    "Operative": "Operative One (digital orders)",
    "baked": "Baked (sales holes)",
}


def _domain(rel: Path) -> str:
    parts = rel.parts
    key = parts[1] if parts[0] == "efs" and len(parts) > 1 else parts[0]
    return DOMAIN_LABELS.get(key, key.replace("_", " ").title())


def _load(path: Path, logical: dict) -> dict:
    text = CATALOG.sub(lambda m: logical.get(m.group(1), m.group(1)), path.read_text())
    text = JINJA.sub("", text)
    return yaml.safe_load(text) or {}


def _tables(cube: dict) -> list[str]:
    src = cube.get("sql_table") or ""
    if src:
        return [src.strip().strip('"')]
    return sorted({f"{d}.{t}" for d, t in TABLE_REF.findall(cube.get("sql") or "") if not d.startswith("cube_")})


def _kind(cube: dict) -> str:
    real = [m for m in cube.get("measures") or [] if m.get("type") not in (None, "count")]
    return "Fact / metric" if real else "Dimension"


def load_env(model_dir: Path) -> dict:
    """Parse one environment's model tree. Logical catalog names are kept (dwhprd_gold.x)."""
    globals_json = json.loads((model_dir / "globals.json").read_text())
    logical = {k: k for k in globals_json.get("catalogs", {})}
    physical = {k: v for k, v in globals_json.get("catalogs", {}).items()}

    cubes, views = {}, {}
    for path in sorted(model_dir.rglob("*.y*ml")):
        rel = path.relative_to(model_dir)
        doc = _load(path, logical)
        for c in doc.get("cubes") or []:
            cubes[c["name"]] = {**c, "_file": str(rel), "_domain": _domain(rel)}
        for v in doc.get("views") or []:
            views[v["name"]] = {**v, "_file": str(rel), "_domain": _domain(rel)}
    return {"cubes": cubes, "views": views, "catalogs": physical}


def _members(cube: dict) -> dict:
    out = {}
    for kind in ("measures", "dimensions", "segments"):
        for m in cube.get(kind) or []:
            out[m["name"]] = (kind[:-1], m)
    return out


def view_fields(view: dict, cubes: dict) -> list[dict]:
    fields = []
    for ref in view.get("cubes") or []:
        path = (ref.get("join_path") or "").split(".")
        cube = cubes.get(path[-1], {})
        members = _members(cube)
        includes = ref.get("includes", "*")
        excludes = set(ref.get("excludes") or [])
        prefix = ref.get("prefix")
        picks = (
            [{"name": n} for n in members if n not in excludes]
            if includes == "*" else [i if isinstance(i, dict) else {"name": i} for i in includes]
        )
        for pick in picks:
            kind, member = members.get(pick["name"], ("dimension", {}))
            if kind == "segment":
                continue
            exposed = pick.get("alias") or pick["name"]
            if prefix:
                exposed = f"{path[-1]}_{exposed}"
            fields.append({
                "type": kind,
                "name": exposed,
                "title": pick.get("title") or member.get("title") or pick["name"].replace("_", " ").title(),
                "dtype": member.get("type", ""),
                "desc": (pick.get("description") or member.get("description") or "").strip(),
                "cube": path[-1],
                "member": pick["name"],
            })
    return fields


def build(dev_dir: Path, prod_dir: Path) -> dict:
    envs = {"dev": load_env(dev_dir), "prod": load_env(prod_dir)}
    dev = envs["dev"]
    all_cubes = {**envs["prod"]["cubes"], **dev["cubes"]}
    all_views = {**envs["prod"]["views"], **dev["views"]}

    used_in = {}
    for v in all_views.values():
        for ref in v.get("cubes") or []:
            for name in (ref.get("join_path") or "").split("."):
                used_in.setdefault(name, set()).add(v["name"])

    cube_rows = []
    for name, c in sorted(all_cubes.items()):
        cube_rows.append({
            "domain": c["_domain"], "name": name, "title": c.get("title") or name, "kind": _kind(c),
            "src": ", ".join(_tables(c)), "sql": "Yes" if c.get("sql") and not c.get("sql_table") else "No",
            "measures": len(c.get("measures") or []), "dims": len(c.get("dimensions") or []),
            "joins": ", ".join(j["name"] for j in c.get("joins") or []),
            "preagg": ", ".join(p["name"] for p in c.get("pre_aggregations") or []),
            "views": ", ".join(sorted(used_in.get(name, []))),
            "desc": " ".join((c.get("description") or "").split()), "file": c["_file"],
            "envs": [e for e in ("dev", "prod") if name in envs[e]["cubes"]],
        })

    view_rows = []
    for name, v in sorted(all_views.items(), key=lambda kv: (kv[1]["_domain"], kv[0])):
        fields = view_fields(v, all_cubes)
        roots = {(ref.get("join_path") or "").split(".")[0] for ref in v.get("cubes") or []}
        joined = {n for ref in v.get("cubes") or [] for n in (ref.get("join_path") or "").split(".") if n}
        base = sorted({t for r in roots for t in _tables(all_cubes.get(r, {}))})
        meta = v.get("meta") or {}
        view_rows.append({
            "domain": v["_domain"], "name": name, "title": v.get("title") or name,
            "business": meta.get("business") or "", "base": ", ".join(base),
            "measures": sum(f["type"] == "measure" for f in fields),
            "dims": sum(f["type"] != "measure" for f in fields), "joins": len(joined),
            "access": "Yes" if v.get("access_policy") else "No",
            "desc": " ".join((v.get("description") or "").split()), "file": v["_file"],
            "status": "deployed", "fields": fields,
            "envs": [e for e in ("dev", "prod") if name in envs[e]["views"]],
        })
    return {"views": view_rows, "cubes": cube_rows, "catalogs": dev["catalogs"]}
