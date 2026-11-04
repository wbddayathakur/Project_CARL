"""
analysis.py - evidence loader + verifier for the UC1 Looker -> CARL field mapping.

Everything here is computed from files on disk. Nothing is typed in from memory.
Outputs a single dict (also dumped to work/analysis.json) consumed by build_xlsx.py / build_md.py.
"""
import json, re, os, sys
from collections import Counter, defaultdict, OrderedDict
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
DL = "/Users/dthakur/Downloads/"
XLSX = DL + "UC1_Fields_for_CARL_working (2).xlsx"
PIPE_JSON = DL + "PIPELINE_sample 2026-10-16T1926.json_label"
DIG_JSON = DL + "DIG_ORDER_sample 2026-10-16T1926.json_label"
LEG = os.path.join(WORK, "legacy", "carl-legacy-source-master")


# ----------------------------------------------------------------- workbook loaders
def fill_class(c):
    f = c.fill
    if not f or not f.fill_type:
        return "none"
    fg = f.fgColor
    if fg.type == "theme":
        t = round(fg.tint, 1)
        return {(6, 0.8): "GREEN", (6, 0.6): "GREEN", (5, 0.0): "RED", (5, 0.8): "RED"}.get((fg.theme, t), f"theme{fg.theme}")
    if fg.type == "rgb":
        return {"FFFFFF00": "YELLOW"}.get(str(fg.rgb), "rgb:" + str(fg.rgb))
    return "other"


def load_mvp(wb):
    ws = wb["MVP Fields"]
    cols = {"B": "linear_working", "C": "linear_revenue", "D": "pipeline_sf", "E": "digital_op1"}
    rows = []
    comments = {}
    for r in ws.iter_rows(min_row=1, max_row=ws.max_row):
        for c in r:
            if c.comment:
                comments[c.coordinate] = c.comment.text.strip().split("Comment:")[-1].strip()
    for r in range(1, ws.max_row + 1):
        row = {"row": r, "note": ws[f"A{r}"].value, "description": ws[f"F{r}"].value}
        for col, n in cols.items():
            c = ws[f"{col}{r}"]
            v = c.value
            if isinstance(v, str):
                v = v.strip()
            row[n] = v
            row[n + "_fill"] = fill_class(c)
            row[n + "_comment"] = comments.get(f"{col}{r}")
        rows.append(row)
    return rows, comments


def load_field_logic(wb):
    ws = wb["Field Logic"]
    out = []
    for r in range(5, ws.max_row + 1):
        vals = [ws.cell(r, c).value for c in range(1, 7)]
        if not any(v is not None for v in vals):
            continue
        out.append({"row": r, "system": vals[0], "column": vals[1], "build_order": vals[2], "sql": vals[3], "in_words": vals[4], "notes": vals[5]})
    return out


def load_fields(wb):
    ws = wb["Fields"]
    out = []
    cur = None
    for r in range(4, ws.max_row + 1):
        v = [ws.cell(r, c).value for c in range(1, 10)]
        if v[0]:
            cur = v[0]
        if not v[1]:
            continue
        out.append({"row": r, "group": cur, "field": v[1], "type": v[2], "what": v[3], "ideal": v[4], "op1": v[5], "sf": v[6], "need_v1": v[7], "notes": v[8]})
    return out


def load_lists(wb):
    ws = wb["Lists"]
    lists = OrderedDict()
    desc = {}
    cur = None
    two = False
    for r in range(1, ws.max_row + 1):
        a, b, c = ws.cell(r, 1).value, ws.cell(r, 2).value, ws.cell(r, 3).value
        if a is None and b is None:
            cur = None
            continue
        if cur is None:
            if r <= 3 and a and "Reference lists" in str(a):
                continue
            cur = str(a).strip()
            lists[cur] = []
            desc[cur] = c
            two = False
            continue
        if a == "Source value" and b == "Rolls up to":
            two = True
            continue
        lists[cur].append((str(a).strip(), (str(b).strip() if b is not None else None)) if two else str(a).strip())
    return lists, desc


def load_northstar(wb):
    ws = wb["iDeal Northstar Revenue sample"]
    hdr = [ws.cell(3, c).value for c in range(1, ws.max_column + 1)]
    row4 = [ws.cell(4, c).value for c in range(1, ws.max_column + 1)]
    n = 0
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, 1).value is not None:
            n += 1
    return {"header": [h for h in hdr if h], "sample_row": {h: v for h, v in zip(hdr, row4) if h}, "rows": n, "title": [ws.cell(1, c).value for c in range(1, 5)]}


def load_sample_headers(wb):
    out = {}
    for n in ["sample_sf", "sample_op1"]:
        ws = wb[n]
        kinds = [ws.cell(3, c).value for c in range(1, 60)]
        names = [ws.cell(4, c).value for c in range(1, 60)]
        formulas = [ws.cell(5, c).value for c in range(1, 60)]
        out[n] = [{"col": openpyxl.utils.get_column_letter(i + 1), "kind": k, "name": nm, "row5": str(f)[:300] if f is not None else None}
                  for i, (k, nm, f) in enumerate(zip(kinds, names, formulas)) if nm]
    ws = wb["sample_ideal"]
    out["sample_ideal"] = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    return out


# ----------------------------------------------------------------- JSON profiling
def to_num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except Exception:
        return None


def profile(rows):
    keys = list(rows[0].keys())
    out = OrderedDict()
    n = len(rows)
    for k in keys:
        vals = [r.get(k) for r in rows]
        nn = [v for v in vals if v not in (None, "")]
        c = Counter(map(lambda x: str(x), nn))
        nums = [to_num(v) for v in nn]
        nums_ok = [x for x in nums if x is not None]
        numeric = len(nums_ok) == len(nn) and len(nn) > 0 and not all(str(x).lstrip("-").isdigit() and len(str(x)) > 12 for x in nn[:3])
        p = {
            "rows": n, "non_null": len(nn), "null": n - len(nn), "null_pct": round(100.0 * (n - len(nn)) / n, 2),
            "distinct": len(c), "python_types": dict(Counter(type(v).__name__ for v in vals if v is not None)),
            "min": (min(nums_ok) if numeric else None), "max": (max(nums_ok) if numeric else None),
            "sum": (round(sum(nums_ok), 2) if numeric and len(c) > 25 else None),
            "values": c.most_common(60 if len(c) > 60 else None),
            "all_values_listed": len(c) <= 60,
            "sample_raw": [str(v) for v in nn[:3]],
        }
        out[k] = p
    return out


def crosstab(rows, a, b):
    c = Counter((r.get(a), r.get(b)) for r in rows)
    return [{"a": ka, "b": kb, "n": v} for (ka, kb), v in sorted(c.items(), key=lambda x: -x[1])]


# ----------------------------------------------------------------- Field-Logic rule re-implementations
# (typed from the "Field Logic" sheet column D, row refs noted at each function)
def market_type_rule(cls, scatter_vals):
    # Field Logic!D12 / D33
    if not cls:
        return "Unmapped"
    l = cls.lower()
    if "upfront" in l:
        return "Upfront"
    if "scatter" in l:
        return "Scatter"
    if cls in scatter_vals:
        return "Scatter"
    if cls == "Audience Deficiency Unit":
        return "ADU / Makegood"
    if cls == "PSA":
        return "PSA"
    if cls == "International Sold":
        return "International"
    if cls == "Programmatic PPM":
        return "Programmatic - Unclassified"
    return "Unmapped"


def upfront_year_rule(cls):
    # Field Logic!D13 / D34
    m = re.search(r"[0-9]{2}/[0-9]{2}", cls or "")
    return m.group(0) if m else "N/A"


def lifecycle_sf_rule(r, order_wf, lost_wf):
    # Field Logic!D15
    st, rk, wf, sd = r["Salesforce Opportunity Stage"], r["Salesforce Projection Rank"], r["Salesforce Workflow Status"], r["sales_division"]
    if st == "Cancelled":
        return "closed_lost"
    if rk == "F":
        return "closed_lost"
    if wf in lost_wf:
        return "closed_lost"
    if sd in ("Sports", "Linear") and st == "Prospecting/Planning Costs":
        return "Prospecting"
    if sd in ("Sports", "Linear") and st == "Verbal Commitment/HOLD":
        return "Order"
    if wf in order_wf:
        return "Order"
    if wf == "HOL":
        return "Pipeline"
    if rk == "A":
        return "Order"
    return "Pipeline"


def lifecycle_op1_rule(r, order_wf, lost_wf, closed_won):
    # Field Logic!D37 ; sales_division for Op1 computed separately (here: 'Digital' except sports -> use site list)
    st = r["Op1 Contracted Data Sales Stage"]
    wf = r["Op1 Contracted Data Workflow Status"]
    sd = r.get("_sales_division")
    if st in ("Cancelled", "Closed Lost"):
        return "closed_lost"
    if wf in lost_wf:
        return "closed_lost"
    if sd in ("Sports", "Linear") and st == "Prospecting/Planning Costs":
        return "Prospecting"
    if sd in ("Sports", "Linear") and st == "Verbal Commitment/HOLD":
        return "Order"
    if st in closed_won:
        return "Order"
    if wf in order_wf:
        return "Order"
    return "Pipeline"


# ----------------------------------------------------------------- legacy UDF_OP_VERTICAL parser
def parse_udf(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    body = txt.split("$$")[1]
    rules = []
    for m in re.finditer(r"WHEN\s+(lower\(forecast_category\)|LOWER\(forecast_category\)|forecast_category)\s*(=|LIKE|like)\s*'([^']*)'\s*THEN\s*(?:'([^']*)'|forecast_category)", body):
        lhs, op, pat, res = m.groups()
        rules.append({"lower": lhs.lower().startswith("lower"), "op": op.upper(), "pattern": pat, "result": res if res is not None else "<returns forecast_category itself>", "line_no": len(rules) + 1})
    return rules


def udf_eval(rules, fc):
    if fc is None:
        return "Unknown"
    for r in rules:
        v = fc.lower() if r["lower"] else fc
        p = r["pattern"].lower() if r["lower"] else r["pattern"]
        if r["op"] == "=":
            ok = v == p
        else:
            rx = "^" + re.escape(p).replace("%", ".*") + "$"
            rx = rx.replace(r"\%", ".*")
            ok = re.match("^" + "".join(".*" if ch == "%" else re.escape(ch) for ch in p) + "$", v, re.S) is not None
        if ok:
            return fc if r["result"].startswith("<returns") else r["result"]
    return "Unknown"


# ----------------------------------------------------------------- main analysis
def run():
    wb = openpyxl.load_workbook(XLSX)
    A = OrderedDict()
    A["mvp"], A["mvp_comments"] = load_mvp(wb)
    A["field_logic"] = load_field_logic(wb)
    A["fields_sheet"] = load_fields(wb)
    A["lists"], A["list_desc"] = load_lists(wb)
    A["northstar"] = load_northstar(wb)
    A["sample_headers"] = load_sample_headers(wb)

    P_all = json.load(open(PIPE_JSON))
    D = json.load(open(DIG_JSON))
    dims = [k for k in P_all[0] if not k.startswith(("Salesforce Net", "Salesforce Linear Total"))]
    totals_rows = [r for r in P_all if all(r.get(k) is None for k in dims)]
    A["pipe_totals_row"] = totals_rows
    P = [r for r in P_all if r not in totals_rows]
    A["n_pipe_raw"] = len(P_all)
    A["n_pipe"], A["n_dig"] = len(P), len(D)
    A["profile_pipe"] = profile(P)
    A["profile_dig"] = profile(D)

    L = A["lists"]
    scatter_vals = set(L["ScatterVals"])
    order_wf, lost_wf, closed_won = set(L["OrderWF"]), set(L["LostWF"]), set(L["ClosedWonStages"])

    V = OrderedDict()   # verifications

    # ---- V1/V2/V3 SF reproduction tests
    valid = P
    V["sf_market_type"] = {"rows_tested": len(valid), "matches": sum(market_type_rule(r["Salesforce Classification"], scatter_vals) == r["Market Type"] for r in valid),
                           "rule_ref": "Field Logic!D12", "looker_label": "Market Type", "input": "Salesforce Classification"}
    V["sf_upfront_year"] = {"rows_tested": len(valid), "matches": sum(upfront_year_rule(r["Salesforce Classification"]) == r["UF Year"] for r in valid),
                            "rule_ref": "Field Logic!D13", "looker_label": "UF Year", "input": "Salesforce Classification"}
    conf = Counter()
    for r in valid:
        conf[(lifecycle_sf_rule(r, order_wf, lost_wf), r["Status Group"])] += 1
    V["sf_lifecycle_state"] = {"rows_tested": len(valid), "matches": sum(v for (a, b), v in conf.items() if a == b), "rule_ref": "Field Logic!D15", "looker_label": "Status Group",
                               "inputs": "Salesforce Opportunity Stage, Projection Rank, Workflow Status, Looker sales_division (NOT recomputed)",
                               "confusion": [{"rule": a, "looker": b, "n": n} for (a, b), n in conf.most_common()]}
    V["sf_stage_to_rank"] = crosstab(P, "Salesforce Opportunity Stage", "Salesforce Projection Rank")
    V["sf_stage_to_status"] = crosstab(P, "Salesforce Opportunity Stage", "Status Group")
    V["sf_workflow_to_status"] = crosstab(P, "Salesforce Workflow Status", "Status Group")
    V["sf_class_to_market"] = crosstab(P, "Salesforce Classification", "Market Type")
    V["sf_class_to_ufyear"] = crosstab(P, "Salesforce Classification", "UF Year")
    V["sf_platform_vs_recordtype"] = crosstab(P, "Platform", "Salesforce Record Type")
    V["sf_platform_override_rows"] = [{"property_detail": a[0], "platform": a[1], "record_type": a[2], "sales_division": a[3], "uf_group": a[4], "n": n}
                                      for a, n in Counter((r["Property Detail"], r["Platform"], r["Salesforce Record Type"], r["sales_division"], r["uf_group"]) for r in P if r["Platform"] != r["Salesforce Record Type"]).most_common()]
    V["sf_division_vs_platform"] = crosstab(P, "sales_division", "Platform")

    # ---- V7 uf_group coverage vs Field Logic lists
    sports_sites, generic, ncaa_props, ncaa_sites = set(L["SportsSites"]), set(L["GenericSports"]), set(L["NCAAProps"]), set(L["NCAASites"])
    news_sites, ss_sites, max_sites, dplus, wbd_stream = set(L["NewsSites"]), set(L["SSSites"]), set(L["MaxSites"]), set(L["DPlusSites"]), set(L["WBDStreamSites"])
    linear_mkt = set(L["LinearMktTypes"])
    propmap = dict(L["PropMap"]); sitemap = dict(L["SiteMap"]); netmap = dict(L["NetMap"])
    sports_networks = set(L["SportsNetworks"])

    pdc = defaultdict(Counter)
    for r in P:
        if r.get("Status Group") is None:
            continue
        pdc[(r["Salesforce Record Type"], r["Property Detail"])][(r["uf_group"], r["sales_division"], r["Property"], r["Platform"])] += 1
    rows = []
    for (rt, pd_), cnt in sorted(pdc.items(), key=lambda x: (str(x[0][0]), str(x[0][1]))):
        for (uf, sd, prop, plat), n in cnt.most_common():
            ls = []
            # membership of Property Detail in each Field Logic reference list
            for nm, st in [("SportsSites", sports_sites), ("GenericSports", generic), ("NCAAProps", ncaa_props), ("NCAASites", ncaa_sites), ("NewsSites", news_sites), ("SSSites", ss_sites),
                           ("MaxSites", max_sites), ("DPlusSites", dplus), ("WBDStreamSites", wbd_stream), ("SportsNetworks", sports_networks)]:
                if pd_ in st:
                    ls.append(nm)
            if pd_ in propmap: ls.append("PropMap")
            if pd_ in sitemap: ls.append("SiteMap")
            if pd_ in netmap: ls.append("NetMap")
            rows.append({"record_type": rt, "property_detail": pd_, "looker_uf_group": uf, "looker_sales_division": sd, "looker_property": prop, "looker_platform": plat, "n": n, "in_field_logic_lists": ", ".join(ls) or "(none)"})
    V["sf_ufgroup_by_property_detail"] = rows

    # Targeted contradictions (data-computed)
    def cnt(pred):
        return sum(1 for r in P if r.get("Status Group") is not None and pred(r))
    FL = OrderedDict()
    FL["T1 Field Logic uf_group branch 1 emits 'Digital - Sports' for GenericSports ('Turner Sports'); Looker values never include it"] = {
        "looker_has_value_Digital_-_Sports": any(r["uf_group"] == "Digital - Sports" for r in P),
        "digital_rows_property_detail_Turner_Sports": cnt(lambda r: r["Property Detail"] == "Turner Sports" and r["Salesforce Record Type"] == "Digital"),
        "looker_uf_group_for_those_rows": dict(Counter(r["uf_group"] for r in P if r["Property Detail"] == "Turner Sports"))}
    FL["T2 'Linear Spon' sites -> Field Logic 'Linear Spon'; Looker gives 'Digital - WBD Stream'"] = {
        "rows": cnt(lambda r: r["Property Detail"] and "Linear Spon" in r["Property Detail"]),
        "looker_uf_group": dict(Counter(r["uf_group"] for r in P if r["Property Detail"] and "Linear Spon" in r["Property Detail"])),
        "looker_has_value_Linear_Spon": any(r["uf_group"] == "Linear Spon" for r in P)}
    wbd_rows = [r for r in P if r["uf_group"] == "Digital - WBD Stream"]
    FL["T3 Looker 'Digital - WBD Stream' is broader than Field Logic WBDStreamSites"] = {
        "looker_rows": len(wbd_rows),
        "rows_with_property_detail_in_WBDStreamSites": sum(1 for r in wbd_rows if r["Property Detail"] in wbd_stream),
        "rows_outside_WBDStreamSites": sum(1 for r in wbd_rows if r["Property Detail"] not in wbd_stream),
        "outside_breakdown": dict(Counter(r["Property Detail"] for r in wbd_rows if r["Property Detail"] not in wbd_stream).most_common())}
    FL["T4 'Digital - D+' in Looker for 'Discovery Networks' rows (Field Logic DPlusSites = Discovery+/Discovery Plus only)"] = {
        "looker_D+_rows": sum(1 for r in P if r["uf_group"] == "Digital - D+"),
        "looker_D+_property_detail": dict(Counter(r["Property Detail"] for r in P if r["uf_group"] == "Digital - D+")),
        "discovery_networks_rows": cnt(lambda r: r["Property Detail"] == "Discovery Networks"),
        "discovery_networks_split": dict(Counter(r["uf_group"] for r in P if r["Property Detail"] == "Discovery Networks"))}
    ln = [r for r in P if r["Salesforce Record Type"] == "Linear" and r["Platform"] == "Linear" and not str(r["uf_group"]).startswith("Sports")]
    def lin_rule(r):
        c = r["Salesforce Classification"]
        return ("Linear - " + c) if c in linear_mkt else "Linear - Traditional"
    FL["T5 Linear non-sports uf_group: Field Logic 'Linear - '||classification (DDL/Demo Direct/Premiere) else Traditional"] = {
        "rows_tested": len(ln), "matches": sum(1 for r in ln if lin_rule(r) == r["uf_group"]),
        "mismatch_detail": [{"classification": a[0], "looker": a[1], "rule": a[2], "n": n} for a, n in Counter((r["Salesforce Classification"], r["uf_group"], lin_rule(r)) for r in ln if lin_rule(r) != r["uf_group"]).most_common()]}
    FL["T6 Linear rows with Property Detail NULL"] = {
        "rows": sum(1 for r in P if r["Property Detail"] is None and r["Status Group"] is not None),
        "by_uf_group": dict(Counter(r["uf_group"] for r in P if r["Property Detail"] is None and r["Status Group"] is not None)),
        "note": "Field Logic property_detail = COALESCE(sports_property, network) cannot be NULL for a row that Looker puts in 'Sports Linear - NCAA' (needs sports_property or network='NBA TV'); Looker Property Detail is NULL on these rows."}
    FL["T7 Platform override: Looker Platform != Record Type"] = {
        "rows": sum(1 for r in P if r["Platform"] != r["Salesforce Record Type"] and r["Status Group"] is not None),
        "by_property_detail": dict(Counter(r["Property Detail"] for r in P if r["Platform"] != r["Salesforce Record Type"] and r["Status Group"] is not None)),
        "note": "Field Logic!F6 says only network 'Digital Media' is overridden; the export shows BR and Nascar rows overridden as well."}
    # Property vs maps
    mism = Counter()
    ok = 0
    tot = 0
    for r in P:
        pd_, pr = r["Property Detail"], r["Property"]
        if pd_ is None:
            continue
        tot += 1
        exp = propmap.get(pd_) or sitemap.get(pd_) or netmap.get(pd_) or pd_
        if exp == pr:
            ok += 1
        else:
            mism[(pd_, pr, exp)] += 1
    FL["T8 Property: Looker Property vs Field Logic COALESCE(PropMap, SiteMap, NetMap, raw) using Property Detail as the key"] = {
        "rows_tested": tot, "matches": ok, "mismatch_detail": [{"property_detail": a[0], "looker_property": a[1], "lists_tab_expected": a[2], "n": n} for a, n in mism.most_common(60)]}
    x = [r for r in P if r["Property Detail"] is None and r["uf_group"] == "Sports Linear - NCAA"]
    FL["T9 Observed driver of the 193 'Sports Linear - NCAA' rows with NULL Property Detail (pattern in Opportunity Name; Looker SQL not on disk)"] = {
        "rows": len(x), "opp_name_starts_with_'NCAA Linear'": sum(1 for r in x if re.match(r"NCAA Linear", r["Salesforce Opportunity Name"] or "")),
        "other_name_prefixes": dict(Counter((r["Salesforce Opportunity Name"] or "")[:14] for r in x if not re.match(r"NCAA Linear", r["Salesforce Opportunity Name"] or "")))}
    def dplus_flag(fc, name):
        # legacy LookML discoveryplusflag (base.salesforce_reporting.view.lkml:712-720 / base.oper_sales_order_line_items_t.view.lkml:354-362)
        n = (name or "").lower()
        return (fc in ("Discovery Networks", "DCI ENT") and any(p in n for p in ("d+", "discovery+", "dplus", "discoveryplus"))) or fc == "Discovery+"
    dig = [r for r in P if r["Salesforce Record Type"] == "Digital"]
    cc = Counter((r["uf_group"] == "Digital - D+", dplus_flag(r["Property Detail"], r["Salesforce Opportunity Name"])) for r in dig)
    FL["T10 Legacy LookML discoveryplusflag vs live Looker uf_group 'Digital - D+' (Digital record-type rows)"] = {
        "rows_tested": len(dig), "agree": cc[(True, True)] + cc[(False, False)], "looker_D+_and_flag_yes": cc[(True, True)], "looker_D+_but_flag_no": cc[(True, False)], "looker_not_D+_but_flag_yes": cc[(False, True)],
        "rule": "(site IN ('Discovery Networks','DCI ENT') AND LOWER(opportunity name) LIKE any of '%d+%','%discovery+%','%dplus%','%discoveryplus%') OR site='Discovery+'",
        "source": "legacy base.salesforce_reporting.view.lkml:712-720 (uses opportunity_name_id); Op1 version uses sales_order_name"}
    op1_flag = Counter((r["Op1 Contracted Data Site"], dplus_flag(r["Op1 Contracted Data Site"], r["Op1 Contracted Data Order Name"])) for r in D if r["Op1 Contracted Data Site"] in ("Discovery Networks", "DCI ENT", "Discovery+"))
    FL["T11 Op1: legacy discoveryplusflag evaluated on the Op1 export (Site, Order Name)"] = {"{}|{}".format(k[0], "flag=Yes" if k[1] else "flag=No"): v for k, v in op1_flag.items()}
    V["sf_fieldlogic_tests"] = FL

    # AE role analysis
    V["sf_ae_null_by_platform"] = [{"platform": pl, "rows": sum(1 for r in P if r["Platform"] == pl and r["Status Group"] is not None),
                                    "buyer_null": sum(1 for r in P if r["Platform"] == pl and r["Status Group"] is not None and not r["Buyer_AE"]),
                                    "client_null": sum(1 for r in P if r["Platform"] == pl and r["Status Group"] is not None and not r["Client_AE"]),
                                    "planning_null": sum(1 for r in P if r["Platform"] == pl and r["Status Group"] is not None and not r["Planning_AE"])} for pl in ("Linear", "Digital")]
    V["sf_ae_same_person"] = {"buyer==client": sum(1 for r in P if r["Buyer_AE"] and r["Buyer_AE"] == r["Client_AE"]), "buyer==planning": sum(1 for r in P if r["Buyer_AE"] and r["Buyer_AE"] == r["Planning_AE"]),
                              "client==planning": sum(1 for r in P if r["Client_AE"] and r["Client_AE"] == r["Planning_AE"])}
    # money relationships
    nz = [r for r in P if r["Salesforce Net Projections"] not in (None, 0)]
    ladder = Counter(round(r["Salesforce Net Weighted Projections"] / r["Salesforce Net Projections"], 2) for r in nz)
    V["sf_weighted_ratio_ladder"] = [{"ratio": k, "n": v} for k, v in sorted(ladder.items(), key=lambda x: -x[1])[:25]]
    V["sf_money_totals"] = {"net_projections_sum": round(sum(r["Salesforce Net Projections"] or 0 for r in P), 2),
                            "net_weighted_sum": round(sum(r["Salesforce Net Weighted Projections"] or 0 for r in P), 2),
                            "linear_total_amount_sum": round(sum(r["Salesforce Linear Total Amount"] or 0 for r in P), 2),
                            "total_amount_sum": round(sum(r["Salesforce Total Amount"] or 0 for r in P), 2),
                            "net_by_status_group": {k: round(v, 2) for k, v in Counter({sg: sum(r["Salesforce Net Projections"] or 0 for r in P if r["Status Group"] == sg) for sg in set(r["Status Group"] for r in P)}).items() if k},
                            "linear_total_amount_nonzero_by_platform": dict(Counter(r["Platform"] for r in P if r["Salesforce Linear Total Amount"])),
                            "net_projections_nonzero_by_platform": dict(Counter(r["Platform"] for r in P if r["Salesforce Net Projections"]))}
    V["sf_key_coverage"] = {"opp_id_null": sum(1 for r in P if not r["Salesforce Opportunity ID"]), "sales_order_id_null_by_platform": dict(Counter(r["Platform"] for r in P if not r["Salesforce Sales Order ID"])),
                            "ideal_id_non_null_by_platform": dict(Counter(r["Platform"] for r in P if r["Salesforce iDeal ID"])), "order_id_non_null_by_platform": dict(Counter(r["Platform"] for r in P if r["Salesforce Order ID"])),
                            "placeholder_op_order_id_non_null": sum(1 for r in P if r["Salesforce Placeholder Operative Order ID"]),
                            "deal_type_non_null_by_platform": dict(Counter(r["Platform"] for r in P if r["Salesforce Deal Type"]))}
    V["sf_activity_quarter_by_platform"] = [{"platform": a[0], "activity_quarter": a[1], "n": n} for a, n in sorted(Counter((r["Platform"], r["Salesforce Activity Quarter"]) for r in P).items(), key=lambda x: (str(x[0][0]), str(x[0][1])))]
    # Grain evidence
    c = Counter((r["Salesforce Opportunity ID"], r["Salesforce Activity Quarter"], r["Salesforce Ad Type"], r["Property Detail"]) for r in P)
    c2 = Counter((r["Salesforce Opportunity ID"], r["Salesforce Activity Quarter"], r["Salesforce Ad Type"], r["Property Detail"], r["Salesforce Sales Order ID"]) for r in P)
    V["sf_grain"] = {"rows": len(P), "distinct_opp_id": len(set(r["Salesforce Opportunity ID"] for r in P)),
                     "distinct_opp_qtr_adtype_propdetail": len(c), "distinct_plus_sales_order_id": len(c2), "unique_with_sales_order_id": len(c2) == len(P)}

    # ---- Op1
    V["op1_marketype_looker_vs_classification"] = []
    cc = Counter((r["Op1 Contracted Data Classification"], r["Op1 Contracted Data Market Type"], market_type_rule(r["Op1 Contracted Data Classification"], scatter_vals)) for r in D)
    for (cl, lk, rule), n in cc.most_common():
        V["op1_marketype_looker_vs_classification"].append({"classification": cl, "looker_market_type": lk, "field_logic_market_type": rule, "n": n})

    def collapse(x):  # collapse Field Logic output to Looker's three-value domain for a fair comparison
        return {"Upfront": "Upfront", "Scatter": "Scatter"}.get(x, "n/a-not-comparable")
    comparable = [r for r in D if market_type_rule(r["Op1 Contracted Data Classification"], scatter_vals) in ("Upfront", "Scatter")]
    V["op1_marketype_summary"] = {"rows": len(D), "comparable_rows (rule returns Upfront or Scatter)": len(comparable),
                                  "agree": sum(1 for r in comparable if market_type_rule(r["Op1 Contracted Data Classification"], scatter_vals) == r["Op1 Contracted Data Market Type"]),
                                  "disagree": sum(1 for r in comparable if market_type_rule(r["Op1 Contracted Data Classification"], scatter_vals) != r["Op1 Contracted Data Market Type"]),
                                  "looker_upfront_but_classification_scatter": sum(1 for r in D if r["Op1 Contracted Data Market Type"] == "Upfront" and market_type_rule(r["Op1 Contracted Data Classification"], scatter_vals) == "Scatter"),
                                  "looker_scatter_but_classification_upfront": sum(1 for r in D if r["Op1 Contracted Data Market Type"] == "Scatter" and market_type_rule(r["Op1 Contracted Data Classification"], scatter_vals) == "Upfront"),
                                  "net_revenue_disagree_usd": round(sum(to_num(r["Op1 Contracted Data Net Revenue"]) or 0 for r in comparable if market_type_rule(r["Op1 Contracted Data Classification"], scatter_vals) != r["Op1 Contracted Data Market Type"]), 2),
                                  "net_revenue_total_usd": round(sum(to_num(r["Op1 Contracted Data Net Revenue"]) or 0 for r in D), 2)}
    V["op1_salesstage_vs_sfstage"] = crosstab(D, "Op1 Contracted Data Sales Stage", "Salesforce Opportunity Stage")
    V["op1_workflow_vs_salesstage"] = crosstab(D, "Op1 Contracted Data Workflow Status", "Op1 Contracted Data Sales Stage")
    V["op1_net_vs_gross"] = {"rows": len(D), "equal": sum(1 for r in D if to_num(r["Op1 Contracted Data Net Revenue"]) == to_num(r["Op1 Contracted Data Gross Revenue"])),
                             "differ": sum(1 for r in D if to_num(r["Op1 Contracted Data Net Revenue"]) != to_num(r["Op1 Contracted Data Gross Revenue"])),
                             "gross_null": sum(1 for r in D if r["Op1 Contracted Data Gross Revenue"] in (None, "")),
                             "net_total": round(sum(to_num(r["Op1 Contracted Data Net Revenue"]) or 0 for r in D), 2),
                             "gross_total": round(sum(to_num(r["Op1 Contracted Data Gross Revenue"]) or 0 for r in D), 2),
                             "delta_total_where_differ": round(sum((to_num(r["Op1 Contracted Data Gross Revenue"]) or 0) - (to_num(r["Op1 Contracted Data Net Revenue"]) or 0) for r in D if to_num(r["Op1 Contracted Data Net Revenue"]) != to_num(r["Op1 Contracted Data Gross Revenue"])), 2),
                             "value_format": "strings, e.g. '$25,137' and '351,561' (must be parsed; not numeric in the export)"}
    V["op1_key_coverage"] = {"opp_id_null": sum(1 for r in D if not r["Op1 Contracted Data Opportunity ID"]), "sf_stage_null": sum(1 for r in D if not r["Salesforce Opportunity Stage"]),
                             "package_name_null": sum(1 for r in D if not r["Op1 Contracted Data Package Name"]), "ssp_non_null": sum(1 for r in D if r["Op1 Contracted Data SSP"]),
                             "deal_type_NA": sum(1 for r in D if r["Op1 Contracted Data Deal Type"] == "N/A"), "mega_agency_null": sum(1 for r in D if not r["Op1 Contracted Data Mega Agency"]),
                             "agency_null": sum(1 for r in D if not r["Op1 Contracted Data Agency"]), "classification_null": sum(1 for r in D if not r["Op1 Contracted Data Classification"]),
                             "distinct_sales_orders": len(set(r["Op1 Contracted Data Sales Order ID"] for r in D)),
                             "opp_id_with_both_nulls_sf_stage": sum(1 for r in D if not r["Op1 Contracted Data Opportunity ID"] and not r["Salesforce Opportunity Stage"])}
    V["op1_grain"] = {"rows": len(D), "distinct_so_site_pkg_prod_qtr": len(set((r["Op1 Contracted Data Sales Order ID"], r["Op1 Contracted Data Site"], r["Op1 Contracted Data Package Name"], r["Op1 Contracted Data Product Name"], r["Op1 Contracted Data Calendar Quarter"]) for r in D))}
    # Op1 SSP vs deal type (PG)
    V["op1_ssp_by_dealtype"] = crosstab(D, "Op1 Contracted Data SSP", "Op1 Contracted Data Deal Type")
    # Site-level: Field Logic derived values vs UDF vertical
    rules = parse_udf(os.path.join(LEG, "looker-etl-carl", "snowflake", "RA_UDF", "op1_udf.sql"))
    A["udf_rules"] = rules
    sites = Counter(r["Op1 Contracted Data Site"] for r in D)
    site_rows = []
    for s, n in sites.most_common():
        # Field Logic Op1 business_unit (D30), sales_division (D29, sports_property unknown -> not evaluable), property (D31, uses Property field not in export)
        if s in sports_sites:
            bu = "Sports"
        elif s in set(L["StreamingBU"]):
            bu = "Streaming"
        elif s in news_sites:
            bu = "News"
        else:
            bu = "Entertainment"
        if s in generic:
            sd = "Sports"
        elif s in sports_sites:
            sd = "Sports"
        else:
            sd = "Digital"
        if s in generic:
            uf = "Digital - Sports"
        elif "Linear Spon" in s:
            uf = "Linear Spon"
        elif s in ncaa_sites:
            uf = "Sports Digital - NCAA"
        elif s in sports_sites:
            uf = "Sports Digital - Non-NCAA"
        elif s in news_sites:
            uf = "Digital - News"
        elif s in ss_sites:
            uf = "S&S"
        elif s in max_sites:
            uf = "Digital - MAX"
        elif s in dplus:
            uf = "Digital - D+"
        elif s in wbd_stream:
            uf = "Digital - WBD Stream"
        else:
            uf = "Unmapped"
        site_rows.append({"site": s, "rows": n, "legacy_UDF_OP_VERTICAL_vertical": udf_eval(rules, s), "field_logic_business_unit": bu, "field_logic_sales_division_site_only": sd, "field_logic_uf_group_site_only (package override not applied)": uf,
                          "field_logic_property_via_SiteMap": sitemap.get(s, s)})
    V["op1_site_derivations"] = site_rows
    # package override effect
    pkg_override = Counter()
    for r in D:
        pk = (r["Op1 Contracted Data Package Name"] or "")
        if re.search(r"wbd stream|stream\+", pk, re.I):
            pkg_override[r["Op1 Contracted Data Site"]] += 1
    V["op1_wbd_stream_package_by_site"] = [{"site": k, "rows": v} for k, v in pkg_override.most_common()]
    # CARL-expected lifecycle (needs sales_division for Op1: derived from site only)
    for r in D:
        s = r["Op1 Contracted Data Site"]
        r["_sales_division"] = "Sports" if (s in generic or s in sports_sites) else "Digital"
    life = Counter(lifecycle_op1_rule(r, order_wf, lost_wf, closed_won) for r in D)
    V["op1_lifecycle_rule_distribution"] = dict(life)
    V["op1_sales_stage_in_closed_won_list"] = {k: (k in closed_won) for k in sorted(set(r["Op1 Contracted Data Sales Stage"] for r in D))}
    V["op1_calendar_quarter_vs_start_date"] = {"calendar_quarter_values": dict(Counter(r["Op1 Contracted Data Calendar Quarter"] for r in D)),
                                               "so_start_year_range": [min(r["Op1 Contracted Data Sales Order Start Date"] for r in D), max(r["Op1 Contracted Data Sales Order Start Date"] for r in D)],
                                               "so_end_year_range": [min(r["Op1 Contracted Data Sales Order End Date"] for r in D), max(r["Op1 Contracted Data Sales Order End Date"] for r in D)]}

    # ---- Field Logic flag checks computed on the exports (rows quoted in Field Logic come from a DIFFERENT sample)
    C = OrderedDict()
    ph_ad = [r for r in P if r["Salesforce Ad Type"] == "Placeholder"]
    ph_nm = [r for r in P if "placeholder" in (r["Salesforce Opportunity Name"] or "").lower()]
    C["sf_placeholder_flag"] = {"ad_type_Placeholder_rows": len(ph_ad), "ad_type_Placeholder_net_projections": round(sum(r["Salesforce Net Projections"] or 0 for r in ph_ad), 2),
                                "opp_name_like_placeholder_rows": len(ph_nm), "opp_name_net_projections": round(sum(r["Salesforce Net Projections"] or 0 for r in ph_nm), 2),
                                "overlap_rows": len([r for r in ph_ad if r in ph_nm]), "field_logic_quote": "Ad Type 591 rows / $205.8M; name 68 / $29.0M; overlap 31 (Field Logic!F16, different sample)"}
    prod = [r for r in P if "prod" in (r["Salesforce Ad Type"] or "").lower()]
    C["sf_production_fee_flag"] = {"rows": len(prod), "net_projections": round(sum(r["Salesforce Net Projections"] or 0 for r in prod), 2), "ad_types": dict(Counter(r["Salesforce Ad Type"] for r in prod))}
    dr = [r for r in P if r["Salesforce Classification"] == "Direct Response"]
    C["sf_direct_response_flag"] = {"rows": len(dr), "by_platform": dict(Counter(r["Platform"] for r in dr)), "field_logic_quote": "23 rows, all digital (Field Logic!F19, different sample)"}
    C["sf_holdco"] = {"mega_agency_null": sum(1 for r in P if not r["Salesforce Mega Agency"]), "unmatched_flag_rows (mega null AND agency not null)": sum(1 for r in P if not r["Salesforce Mega Agency"] and r["Salesforce Agency"]),
                      "distinct_mega_agency": len(set(r["Salesforce Mega Agency"] for r in P if r["Salesforce Mega Agency"])),
                      "mega_agency_case_variants": len(set(r["Salesforce Mega Agency"] for r in P if r["Salesforce Mega Agency"])) - len(set((r["Salesforce Mega Agency"] or "").upper() for r in P if r["Salesforce Mega Agency"]))}
    C["sf_lifecycle_revenue"] = {k: round(v, 2) for k, v in V["sf_money_totals"]["net_by_status_group"].items()}
    C["sf_override_projection"] = {"rows": sum(1 for r in P if r["Platform"] != r["Salesforce Record Type"]), "net_projections": round(sum(r["Salesforce Net Projections"] or 0 for r in P if r["Platform"] != r["Salesforce Record Type"]), 2)}
    C["op1_placeholder_flag"] = {"order_name_like_placeholder_rows": sum(1 for r in D if "placeholder" in (r["Op1 Contracted Data Order Name"] or "").lower())}
    C["op1_direct_response_flag"] = {"classification_DR_rows": sum(1 for r in D if r["Op1 Contracted Data Classification"] == "Direct Response"), "deal_type_DR_rows": sum(1 for r in D if r["Op1 Contracted Data Deal Type"] == "Direct Response"),
                                     "looker_market_type_DR_rows": sum(1 for r in D if r["Op1 Contracted Data Market Type"] == "DR"),
                                     "classification_DR_and_deal_type_DR": sum(1 for r in D if r["Op1 Contracted Data Classification"] == "Direct Response" and r["Op1 Contracted Data Deal Type"] == "Direct Response")}
    sp = [r for r in D if re.search(r"wbd stream|stream\+", r["Op1 Contracted Data Package Name"] or "", re.I)]
    C["op1_wbd_stream_package_flag"] = {"rows": len(sp), "net_revenue": round(sum(to_num(r["Op1 Contracted Data Net Revenue"]) or 0 for r in sp), 2), "by_site": dict(Counter(r["Op1 Contracted Data Site"] for r in sp).most_common())}
    C["op1_holdco"] = {"mega_agency_null": sum(1 for r in D if not r["Op1 Contracted Data Mega Agency"]), "unmatched_flag_rows": sum(1 for r in D if not r["Op1 Contracted Data Mega Agency"] and r["Op1 Contracted Data Agency"]),
                       "distinct_mega_agency": len(set(r["Op1 Contracted Data Mega Agency"] for r in D if r["Op1 Contracted Data Mega Agency"]))}
    C["op1_upfront_year_fl"] = dict(Counter(upfront_year_rule(r["Op1 Contracted Data Classification"]) for r in D))
    C["op1_revenue_by_lifecycle_rule"] = {k: round(v, 2) for k, v in Counter({lc: sum(to_num(r["Op1 Contracted Data Net Revenue"]) or 0 for r in D if lifecycle_op1_rule(r, order_wf, lost_wf, closed_won) == lc) for lc in ("Order", "Pipeline", "Prospecting", "closed_lost")}).items()}
    C["op1_closed_won_list_check"] = {k: (k in closed_won) for k in sorted(set(r["Op1 Contracted Data Sales Stage"] for r in D))}
    C["op1_discovery_plus_override"] = {"site_Discovery+_rows": sum(1 for r in D if r["Op1 Contracted Data Site"] == "Discovery+")}
    V["fl_checks"] = C
    A["verify"] = V
    return A


if __name__ == "__main__":
    A = run()
    json.dump(A, open(os.path.join(WORK, "analysis.json"), "w"), indent=1, default=str)
    V = A["verify"]
    print("market_type", V["sf_market_type"]["matches"], "/", V["sf_market_type"]["rows_tested"])
    print("upfront_year", V["sf_upfront_year"]["matches"], "/", V["sf_upfront_year"]["rows_tested"])
    print("lifecycle", V["sf_lifecycle_state"]["matches"], "/", V["sf_lifecycle_state"]["rows_tested"])
    print(json.dumps(V["sf_fieldlogic_tests"], indent=1)[:6000])
    print(V["op1_marketype_summary"])
    print(V["op1_net_vs_gross"])
    print(len(A["udf_rules"]), "UDF rules")
