# UC1 Looker -> CARL field-to-field mapping (2026-10-16)

Looker is the source of truth. Every statement is tagged with its evidence class; anything not in the provided evidence is marked 'not found in provided evidence'.

## Workbooks (`out/`)

- `UC1_Field_to_Field_Mapping_Master.xlsx` - Master: MVP crosswalk, SF + Op1 field sheets, Linear, Field Logic register, decisions, gaps, evidence
- `UC1_Custom_Fields_Catalog.xlsx` - Custom fields: Op1 order/line/product custom fields, occurrences, explore joins, targeting, UDF_OP_VERTICAL, lists, observed maps
- `UC1_Salesforce_Lineage.xlsx` - Salesforce lineage: ETL column -> LookML -> export label, sources, measures, DDL
- `UC1_Op1_Lineage.xlsx` - Op1 lineage: ETL select list, currency/pacing, measures, 157 explore joins, filters, label lineage
- `UC1_Value_Profiles_and_Validation.xlsx` - Value profiles of both exports and every computed validation

## Documents (`out/`)

- `01_MVP_Crosswalk.md`
- `02_Salesforce_Pipeline_Field_Logic.md`
- `03_Op1_Digital_Field_Logic.md`
- `04_FieldLogic_Register_and_Linear.md`
- `05_Custom_Fields_and_Targeting.md`
- `06_Looker_vs_CARL_Decisions.md`
- `07_Evidence_Gaps_and_Index.md`
- `08_Lineage_Salesforce_and_Op1.md`

## Evidence status taxonomy

- **VERIFIED-DATA**: Behaviour reproduced / checked against the two Looker exports (PIPELINE_sample, DIG_ORDER_sample) by analysis.py. Re-runnable.
- **LEGACY-SOURCE**: Logic read directly from a file in carl-legacy-source-master.zip (path:line cited). The legacy repo is an OLDER snapshot than live Looker; where live data disagrees, the data wins.
- **SHEET**: Stated in UC1_Fields_for_CARL_working (2).xlsx (sheet!cell cited). It is a proposal / working note, not proof.
- **SECONDARY-XLSX**: Stated in a prior analysis workbook (Salesforce_AdSales_LookML_Iceberg_Analysis.xlsx / Operative1_AdSales_Master_Analysis_Final.xlsx). These were derived from LookML you pasted earlier; the LookML text itself is not on disk.
- **CHAT-ONLY**: Came from SQL / Slack text pasted into the earlier chat. The original text is NOT on disk and could not be re-read, so it is NOT re-verifiable. Save it into evidence/ to upgrade.
- **NAME-MATCH**: CARL/silver column inferred ONLY because the name equals or resembles a column in the Northstar silver sample header. Not confirmed lineage.
- **NOT FOUND**: Not present in any evidence provided. Left blank on purpose - not guessed.
- **MISMATCH**: Looker/legacy behaviour differs from what Field Logic (or CARL) does. Needs a decision from Jason (Looker is the source of truth).

## Headline numbers (recomputed on every build)

- Salesforce/Pipeline export rows: 23,756; Op1/Digital export rows: 14,084
- Salesforce labels documented: 33; Op1 labels documented: 24; decisions: 17

## Rebuild

```
cd uc1-field-mapping && python3 build.py
```