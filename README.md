# MSTR Inventory Agent — CARL / US Ad Sales

Reads the MicroStrategy exports for US Ad Sales and produces **one** consolidated inventory
workbook covering reports, dashboards, attributes, metrics, filters, warehouse tables, database
instances and database connections under a single identifier scheme.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install pandas openpyxl "xlrd>=2.0.1" xlsxwriter matplotlib
.venv/bin/python -m mstr_inventory_agent
```

`matplotlib` is optional — without it every sheet is still produced, only the bus-matrix image
is skipped.

By default the agent reads from and writes to the OneDrive `US Ad Sales Reports- MSTR` folder.

```bash
# explicit paths
.venv/bin/python -m mstr_inventory_agent --source-dir /path/to/exports --out /path/to/inventory.xlsx

# also emit the master sheet as CSV
.venv/bin/python -m mstr_inventory_agent --csv-dir ./out
```

Tests: `.venv/bin/python -m pytest tests/ -q`

## Input files

| File | Object type | Rows |
| --- | --- | --- |
| `reports_usaddsales.xls` | Report | 13,894 |
| `metrics_usaddsales.xls` | Metric | 475 |
| `metrics_Target Demographic_folder.xls` | Metric (subset, deduplicated) | 41 |
| `attributes_usaddsales.xls` | Attribute | 457 |
| `filters_usaddsales.xls` | Filter | 387 |
| `tables_usaddsales.xls` | Table | 120 |
| `dbinstances.xls` | Database Instance | 187 |
| `dbconnections.xls` | Database Connection | 140 |

`CARL_USAdSales_Inventory_Validated - Draft.xlsx` is not re-derived; its two hand-built
fact/dimension analysis sheets are carried forward into the output.

## Identifiers

The exports contain **no MicroStrategy GUIDs**, so the agent mints deterministic surrogates from
`SHA-256(object type + folder path + name)`:

- `Object ID` — short quotable form, e.g. `RPT-1A2B3C4D5E6F`
- `Surrogate GUID` — 32-character MSTR-shaped form
- `MSTR GUID` — deliberately empty, reserved for real GUIDs from Command Manager

Identity keys preserve case and internal spacing, because MSTR permits sibling objects that
differ only in those ways. Uniqueness is asserted on every run. Because IDs are path-derived,
moving or renaming an object changes its ID — bind real GUIDs before using them as durable keys.

## Descriptions

No export carries a description field (the only real ones are on 81 database instances). All
other descriptions are **derived** from name, type and folder taxonomy plus an ad-sales glossary,
and every row states its provenance in `Description Source`.

## Schema view

Alongside the inventory the agent emits a **logical star-schema view**. Three artefacts are
written next to the workbook:

| Artefact | Contents |
| --- | --- |
| `..._Master_Inventory.xlsx` | Six schema sheets (below) |
| `..._Schema.md` | Mermaid ER diagram per fact table, renders in Cursor and GitHub |
| `..._BusMatrix.png` | Dimension bus matrix, conformed vs private |

Sheets: `Schema Overview`, `Table Register`, `Star Schema Map`, `Fact-Dimension Edges`,
`Dimension Conformance`, `Attribute to Table Map`.

What it shows: 120 tables (9 facts, 106 dimensions, 3 views, 2 pivot/staging), 174 validated
fact-to-dimension joins, and dimension conformance — 37 conformed, 39 private, 29 unlinked.

**This is not a physical schema.** The exports list table *names* only, with no columns, data
types, primary/foreign keys or join expressions, and no attribute-to-column mapping. The star
schema is inferred from naming conventions plus the fact/dimension analysis carried forward from
the draft, which the agent re-validates against the tables export on every run (currently zero
joins point at a non-existent table). Attribute-to-table lineage is inferred by name matching and
graded `High` / `Medium` / `Low` / `No match`; attributes in "directly from source" subject areas
are forced to `Low` because they read from source-system extracts rather than this schema.

## Known gaps in the source data

These cannot be resolved from the supplied files and need an Enterprise Manager or Command
Manager extract:

1. **No report definitions** — true report-to-metric/attribute/filter dependencies are not
   recoverable. `Report Object Links` contains only evidence-backed links where an object
   physically sits inside a report's folder.
2. **No document/dossier export** — dashboards are identified by folder and naming convention
   rather than by MSTR object type.
3. **No usage statistics** — whether a report is actually used cannot be determined, which is the
   key input for rationalising the 11,304 personal-folder reports.

## Module map

| Module | Responsibility |
| --- | --- |
| `config.py` | Source registry, folder-to-business-area map, ad-sales glossary |
| `loaders.py` | Read and normalise exports, record provenance |
| `identity.py` | Deterministic IDs and surrogate GUIDs |
| `classify.py` | Location, owner, business area, environment, data-source class |
| `describe.py` | Derived descriptions |
| `build.py` | Assemble the unified master inventory |
| `analyze.py` | Dashboards, coverage, duplicates, data quality, summary |
| `schema.py` | Star schema, conformance, table register, attribute lineage |
| `diagram.py` | Mermaid ER diagrams and bus-matrix image |
| `export.py` | Formatted Excel output |
| `agent.py` | Orchestration |
