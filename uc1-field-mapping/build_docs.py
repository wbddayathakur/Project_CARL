"""Markdown documents. All content is generated from knowledge.py / the built workbooks, so md and xlsx cannot drift."""
import os, re, datetime
import openpyxl
import knowledge as K
from common import *


def cell(v):
    if v is None:
        return ""
    s = str(v).replace("\r", " ").replace("\n", " <br> ").replace("|", "\\|")
    return s


def sheet_rows(path, name):
    ws = openpyxl.load_workbook(path)[name]
    rows = list(ws.iter_rows(values_only=True))
    title = rows[0][0]
    note = None
    hr = 1
    if rows[1][0] is not None and all(c is None for c in rows[1][1:]):
        note = rows[1][0]
        hr = 2
    return title, note, [c for c in rows[hr]], rows[hr + 1:]


def md_table(headers, rows, cols=None):
    cols = cols or list(range(len(headers)))
    out = ["| " + " | ".join(cell(headers[i]) for i in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        out.append("| " + " | ".join(cell(r[i]) for i in cols) + " |")
    return "\n".join(out)


def write(name, text):
    p = os.path.join(OUT, name)
    open(p, "w", encoding="utf-8").write(text)
    return p


def field_doc(title, intro, fields, sample_key):
    L = [f"# {title}", "", intro, ""]
    L.append("Status legend: " + "; ".join(f"**{k}** = {v}" for k, v in K.STATUS.items()) if isinstance(K.STATUS, dict) else "")
    L.append("")
    for i, f in enumerate(fields, 1):
        L.append(f"## {i}. {f['label']}")
        L.append("")
        L.append(f"- **MVP row / fill:** {f['mvp']}")
        L.append(f"- **Looker field kind:** {f['kind']}")
        L.append(f"- **Status:** {f['status']}")
        L.append(f"- **Decision ref:** {f.get('decision') or '-'}")
        L.append(f"- **Field Logic column:** {f.get('fl_col') or '-'}")
        L.append(f"- **In sample sheet as RAW?:** {f.get(sample_key) or '-'}")
        L.append(f"- **CARL silver/gold column:** {f['carl']}")
        L.append("")
        L.append("**Looker logic / definition**")
        L.append("")
        L.append(f["logic"])
        L.append("")
        if f["legacy"]:
            L.append("**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**")
            L.append("")
            for ref in f["legacy"]:
                c, snip = resolve(ref)
                L.append(f"- `{c}`")
                if snip and "not found" not in c:
                    L.append("  ```")
                    L.append("  " + snip[:1200].replace("\n", " "))
                    L.append("  ```")
            L.append("")
        else:
            L.append("**Legacy evidence:** none in the legacy repo.")
            L.append("")
        L.append("**Live vs legacy / observations**")
        L.append("")
        L.append(f["live_vs_legacy"])
        L.append("")
    return "\n".join(L)


def build(A, built):
    M = built["master"]
    C = built["custom"]
    stamp = datetime.date.today().isoformat()
    files = []

    # 01 master crosswalk
    t, n, h, r = sheet_rows(M, "01_MVP_Crosswalk")
    L = ["# 01 - MVP field crosswalk (every MVP row -> Looker labels -> CARL)", "", f"_Generated {stamp} from `{os.path.basename(M)}` sheet 01._", "", n or "", "", md_table(h, r)]
    files.append(write("01_MVP_Crosswalk.md", "\n".join(L)))

    # 02 / 03 per-field logic
    files.append(write("02_Salesforce_Pipeline_Field_Logic.md", field_doc("02 - Salesforce / Pipeline: field-by-field logic (Look 26238, 33 labels)",
                                                                       f"Source export has {A['n_pipe']:,} data rows. Every field: Looker logic, legacy citations with SQL, live-vs-legacy notes, CARL column (as far as evidenced), status and decision.", K.SF_FIELDS, "sample_sf_raw")))
    files.append(write("03_Op1_Digital_Field_Logic.md", field_doc("03 - Op1 / Digital: field-by-field logic (Look 26239, 24 labels)",
                                                               f"Source export has {A['n_dig']:,} data rows. The export prefix 'Op1 Contracted Data' is the explore view_label.", K.OP1_FIELDS, "sample_op1_raw")))

    # 04 linear / field logic register
    t, n, h, r = sheet_rows(M, "05_FieldLogic_Register")
    t2, n2, h2, r2 = sheet_rows(M, "04_Linear_QuickMSTR")
    L = ["# 04 - Field Logic register and Linear (QuickMSTR / iDeal)", "", n or "", "", "## Field Logic register (rows 5-160)", "", md_table(h, r), "", "## Linear MVP rows vs Northstar silver sample", "", n2 or "", "", md_table(h2, r2)]
    files.append(write("04_FieldLogic_Register_and_Linear.md", "\n".join(L)))

    # 05 custom fields
    L = ["# 05 - Custom fields, targeting, UDF_OP_VERTICAL, reference lists", "", f"_Generated from `{os.path.basename(C)}`; all sheets are reproduced below._", ""]
    for sh in ("01_Op1_Order_CustomFields", "02_Op1_Line_CustomFields", "03_Op1_Product_CustomFields", "07_Salesforce_CustomFields", "08_Audience_Targeting_IDs", "09_Targeting_Listagg", "10_Live_Looker_CustomDims", "11_UDF_OP_VERTICAL", "13_Observed_Maps", "05_Unique_Keys"):
        t, n, h, r = sheet_rows(C, sh)
        L += [f"## {t}", "", n or "", "", md_table(h, r), ""]
    files.append(write("05_Custom_Fields_and_Targeting.md", "\n".join(L)))

    # 06 decisions
    t, n, h, r = sheet_rows(M, "06_Mismatches_Decisions")
    L = ["# 06 - Looker vs CARL: decisions for Jason", "", "Looker is the source of truth. Each row is a measured or evidenced difference; options are listed, no choice has been made.", ""]
    for row in r:
        L += [f"## {row[0]} - {row[1]}", ""]
        for j in range(2, len(h)):
            L.append(f"- **{h[j]}:** {cell(row[j])}")
        L.append("")
    t, n, h, r = sheet_rows(M, "06b_uf_group_tests")
    L += ["## Computed tests behind the uf_group decisions", "", md_table(h, r)]
    files.append(write("06_Looker_vs_CARL_Decisions.md", "\n".join(L)))

    # 07 gaps + evidence
    t, n, h, r = sheet_rows(M, "07_Gaps_NotFound")
    t2, n2, h2, r2 = sheet_rows(M, "08_Evidence_Index")
    L = ["# 07 - Evidence gaps and evidence index", "", "Nothing below was guessed. Items tagged CHAT-ONLY came from the pasted chat text, which is not saved on disk and therefore cannot be re-verified.", "", "## Gaps", "", md_table(h, r), "", "## Evidence index", "", md_table(h2, r2)]
    files.append(write("07_Evidence_Gaps_and_Index.md", "\n".join(L)))

    # lineage md
    L = ["# 08 - Lineage summaries", ""]
    for key, sh in (("sflin", "01_ETL_Column_Lineage"), ("sflin", "03_Sources_And_Joins"), ("sflin", "05_Measures"), ("op1lin", "02_ETL_Logic_Steps"), ("op1lin", "05_Explore_Filters"), ("op1lin", "03_LookML_Measures_Dims")):
        t, n, h, r = sheet_rows(built[key], sh)
        L += [f"## {t}", "", n or "", "", md_table(h, r), ""]
    files.append(write("08_Lineage_Salesforce_and_Op1.md", "\n".join(L)))

    # README index
    L = [f"# UC1 Looker -> CARL field-to-field mapping ({stamp})", "",
         "Looker is the source of truth. Every statement is tagged with its evidence class; anything not in the provided evidence is marked 'not found in provided evidence'.", "",
         "## Workbooks (`out/`)", ""]
    for k, d in (("master", "Master: MVP crosswalk, SF + Op1 field sheets, Linear, Field Logic register, decisions, gaps, evidence"),
                 ("custom", "Custom fields: Op1 order/line/product custom fields, occurrences, explore joins, targeting, UDF_OP_VERTICAL, lists, observed maps"),
                 ("sflin", "Salesforce lineage: ETL column -> LookML -> export label, sources, measures, DDL"),
                 ("op1lin", "Op1 lineage: ETL select list, currency/pacing, measures, 157 explore joins, filters, label lineage"),
                 ("prof", "Value profiles of both exports and every computed validation")):
        L.append(f"- `{os.path.basename(built[k])}` - {d}")
    L += ["", "## Documents (`out/`)", ""]
    for f in files:
        L.append(f"- `{os.path.basename(f)}`")
    L += ["", "## Evidence status taxonomy", ""]
    if isinstance(K.STATUS, dict):
        for k, v in K.STATUS.items():
            L.append(f"- **{k}**: {v}")
    L += ["", "## Headline numbers (recomputed on every build)", "",
          f"- Salesforce/Pipeline export rows: {A['n_pipe']:,}; Op1/Digital export rows: {A['n_dig']:,}",
          f"- Salesforce labels documented: {len(K.SF_FIELDS)}; Op1 labels documented: {len(K.OP1_FIELDS)}; decisions: {len(K.DECISIONS)}", "",
          "## Rebuild", "", "```", "cd uc1-field-mapping && python3 build.py", "```"]
    files.append(write("README.md", "\n".join(L)))
    return files
