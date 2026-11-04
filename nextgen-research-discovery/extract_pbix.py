"""Extract the report-side model footprint from a thin (live-connected) .pbix.

A live-connected .pbix carries no DataModel, so DAX, Power Query and SQL are not
recoverable from it. What it does carry is every field reference made by every
visual, filter and bookmark, plus the model diagram's table list. That is enough
to prove which tables, columns and measures the report depends on, page by page.

Usage:
    python extract_pbix.py ~/Downloads/NextGenResearchDashboard.pbix evidence/pbix_report.json
"""
import collections
import json
import sys
import zipfile


def _decode(raw: bytes) -> str:
    if raw[:2] == b"\xff\xfe" or (len(raw) > 1 and raw[1] == 0):
        return raw.decode("utf-16-le").lstrip("\ufeff")
    return raw.decode("utf-8-sig")


def _walk_json(o):
    if isinstance(o, str) and o[:1] in "{[":
        try:
            return json.loads(o)
        except ValueError:
            return o
    return o


def collect_refs(o, alias, out):
    o = _walk_json(o)
    if isinstance(o, dict):
        if isinstance(o.get("From"), list):
            for f in o["From"]:
                alias[f.get("Name")] = f.get("Entity")
        for kind in ("Column", "Measure"):
            x = o.get(kind)
            if isinstance(x, dict) and "Property" in x:
                sr = x.get("Expression", {}).get("SourceRef", {})
                ent = sr.get("Entity") or alias.get(sr.get("Source"))
                if ent:
                    out.add((kind, ent, x["Property"]))
        for v in o.values():
            collect_refs(v, alias, out)
    elif isinstance(o, list):
        for v in o:
            collect_refs(v, alias, out)


def _col_of(expr, alias):
    c = expr.get("Column") or expr.get("Measure")
    if not c:
        return None
    sr = c.get("Expression", {}).get("SourceRef", {})
    return sr.get("Entity") or alias.get(sr.get("Source")), c.get("Property")


COMPARISON = {0: "=", 1: ">", 2: ">=", 3: "<", 4: "<="}


def collect_literals(o, alias, out):
    o = _walk_json(o)
    if isinstance(o, dict):
        if isinstance(o.get("From"), list):
            for f in o["From"]:
                alias[f.get("Name")] = f.get("Entity")
        if isinstance(o.get("In"), dict):
            cols = [_col_of(e, alias) for e in o["In"].get("Expressions", [])]
            for row in o["In"].get("Values", []):
                for i, v in enumerate(row):
                    lit = v.get("Literal", {}).get("Value")
                    if lit is not None and i < len(cols) and cols[i]:
                        out[cols[i]].add("in " + lit)
        if isinstance(o.get("Comparison"), dict):
            c = o["Comparison"]
            col = _col_of(c.get("Left", {}), alias)
            lit = c.get("Right", {}).get("Literal", {}).get("Value")
            if col and lit is not None:
                out[col].add(COMPARISON.get(c.get("ComparisonKind", 0), "?") + " " + lit)
        for v in o.values():
            collect_literals(v, alias, out)
    elif isinstance(o, list):
        for v in o:
            collect_literals(v, alias, out)


def main(pbix_path, out_path):
    z = zipfile.ZipFile(pbix_path)
    names = set(z.namelist())
    layout = json.loads(_decode(z.read("Report/Layout")))
    diagram = json.loads(_decode(z.read("DiagramLayout")))
    connections = json.loads(_decode(z.read("Connections")))

    model_tables = [n["nodeIndex"] for n in diagram["diagrams"][0]["nodes"]]
    diagram_groups = {
        d["name"]: [n["nodeIndex"] for n in d["nodes"]] for d in diagram["diagrams"][1:]
    }

    pages, visuals = [], []
    literals = collections.defaultdict(set)
    field_pages = collections.defaultdict(set)
    report_filters = set()
    collect_refs(layout.get("filters", "[]"), {}, report_filters)
    collect_literals(layout.get("filters", "[]"), {}, literals)

    for s in layout["sections"]:
        pc = json.loads(s.get("config", "{}"))
        hidden = pc.get("visibility") == 1
        page_refs = set()
        collect_refs(s.get("filters", "[]"), {}, page_refs)
        collect_literals(s.get("filters", "[]"), {}, literals)
        types = collections.Counter()
        for v in s.get("visualContainers", []):
            try:
                c = json.loads(v["config"])
            except (KeyError, ValueError):
                continue
            sv = c.get("singleVisual")
            if not sv:
                types["group"] += 1
                continue
            t = sv.get("visualType")
            types[t] += 1
            try:
                title = sv["vcObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"].strip("'")
            except (KeyError, IndexError, TypeError):
                title = None
            live = set()
            collect_refs({"p": sv.get("projections"), "q": sv.get("prototypeQuery"), "f": v.get("filters")}, {}, live)
            formatting = set()
            collect_refs({"o": sv.get("objects"), "v": sv.get("vcObjects")}, {}, formatting)
            live |= {r for r in formatting if r[0] == "Measure"}
            stale = set()
            collect_refs({"o": sv.get("objects"), "t": v.get("dataTransforms")}, {}, stale)
            collect_literals(v, {}, literals)
            page_refs |= live
            if live:
                visuals.append(
                    dict(
                        page=s["displayName"],
                        page_hidden=hidden,
                        type=t,
                        title=title,
                        measures=sorted({p for k, e, p in live if k == "Measure"}),
                        columns=sorted({f"{e}[{p}]" for k, e, p in live if k == "Column"}),
                        tables=sorted({e for _, e, _ in live}),
                        formatting_measures=sorted({p for k, _, p in formatting if k == "Measure"}),
                        stale_only_tables=sorted({e for _, e, _ in stale} - {e for _, e, _ in live}),
                    )
                )
        for kind, ent, prop in page_refs:
            field_pages[(kind, ent, prop)].add(s["displayName"])
        pages.append(
            dict(
                ordinal=s.get("ordinal", 0),
                page=s["displayName"],
                hidden=hidden,
                container_count=len(s.get("visualContainers", [])),
                visual_types=dict(types),
                tables=sorted({e for _, e, _ in page_refs}),
                measure_count=len({p for k, _, p in page_refs if k == "Measure"}),
            )
        )
    for kind, ent, prop in report_filters:
        field_pages[(kind, ent, prop)].add("(report-level filter)")

    used_tables = {e for _, e, _ in field_pages}
    cfg = json.loads(layout.get("config", "{}"))
    out = dict(
        source_file=pbix_path,
        has_data_model="DataModel" in names,
        connection=connections,
        model_tables=model_tables,
        diagram_groups=diagram_groups,
        pages=sorted(pages, key=lambda p: p["ordinal"]),
        visuals=visuals,
        fields=[
            dict(kind=k, table=e, field=p, pages=sorted(pg))
            for (k, e, p), pg in sorted(field_pages.items(), key=lambda x: (x[0][1], x[0][2]))
        ],
        filter_literals={f"{e}[{p}]": sorted(v) for (e, p), v in sorted(literals.items()) if e},
        report_filters=sorted(f"{e}[{p}]" for _, e, p in report_filters),
        bookmarks=[b.get("displayName") for b in cfg.get("bookmarks", [])]
        + [c.get("displayName") for b in cfg.get("bookmarks", []) for c in b.get("children", [])],
        tables_referenced_not_in_model=sorted(used_tables - set(model_tables)),
        model_tables_not_referenced_by_visuals=sorted(set(model_tables) - used_tables),
    )
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    print(
        f"{len(model_tables)} model tables, {len(out['pages'])} pages, {len(visuals)} data visuals, "
        f"{sum(1 for x in out['fields'] if x['kind'] == 'Measure')} measures, "
        f"{sum(1 for x in out['fields'] if x['kind'] == 'Column')} columns -> {out_path}"
    )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
