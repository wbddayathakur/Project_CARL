# 01 – MarketShare: Data Requirements (Taxonomy, Advertiser, Ad Intel Spend)

| Field | Value |
| --- | --- |
| Objective | Rebuild the MarketShare 2.0 consumption layer in CARL. The research taxonomy and Nielsen Ad Intel spend should be governed Iceberg tables and Cube views, not Snowflake extracts and Excel round-trips |
| Consumers | Power BI **NextGen Ad Spend** dashboard (`EST. SPEND = SUM(FACTADINTEL[SPEND])`); Looker VAMI dimension views (`mvt_dimnetwork`, `mvt_dimnetworkprogramnamemapping`, `dim_advertiser_brand`); doc 02 (Marketplace Insights demand side); doc 03 (network attributes) |
| Depends on | `00_shared_foundation.md` (naming, audit columns, `dim_network`, `dim_program_taxonomy`, DQ framework, Cube conventions) |
| Business owners | Research taxonomy: Research / Marketplace Insights (Jeff Strauss). MarketShare ETL: AMS BI (Sean Malek, Hong Zhang) |
| Status | DRAFT v0.1 – 29 Oct 2026 |

## Jira tracking

| Item | Jira |
| --- | --- |
| Taxonomy S3 read access + `marketshare_taxonomy_bronze` (MS-01, MS-02) | CARL-4393 |
| Taxonomy Silver reference tables, Rules Engine logic, Research feed (MS-03, MS-08) | CARL-4394 |
| `dim_advertiser_brand`, `dim_media_type`, `dim_ad_attribute`, `dim_network`, `dim_program_taxonomy` (MS-04) | CARL-4116 |
| `fct_adintel_occurrence`, `ms_fct_adintel_spend_daily`, `ms_agg_category_share_month` (MS-05, MS-06) | CARL-4119 |
| Cube `ms_view_*` + golden queries (MS-07) | CARL-4121 |
| Ad Intel Bronze (existing) | Epic CARL-3499 |

## 1. Scope

| In scope | Out of scope |
| --- | --- |
| Landing the 5 MarketShare S3 mapping files (input and output) as versioned Bronze | Replacing the AMS BI Rules Engine ETL itself (Phase 2 option, section 6.6) |
| Silver reference tables: rules, distributor mapping, genre, product categories | Changing Research's upload workflow |
| `dim_advertiser_brand`, `dim_media_type`, `dim_ad_attribute`, publication of `dim_network` and `dim_program_taxonomy` | Nielsen Ad Intel raw files (CARL lands the AMS BI-processed `FACTADINTEL`) |
| `research_silver.fct_adintel_occurrence`, `research_gold.ms_fct_adintel_spend_daily` and `ms_agg_category_share_month` | Guideline spend (doc 02) |
| Cube views `marketplace_view_adintel_spend`, `marketplace_view_adintel_sales` (renamed to `ms_view_*`, 8.1) | |

### Taxonomy → CARL object map (as specified by Research)

| Research taxonomy (S3 file) | MarketShare dimension (Snowflake / `marketshare_bronze`) | CARL Silver | CARL Gold |
| --- | --- | --- | --- |
| Distributor Mapping (`distributormapping.csv`) | dimNetwork (Ad Intel distributor → network) | `ref_adintel_distributor` | joined into `dim_network`; used by `fct_adintel_occurrence` |
| Network (`network.csv`) | dimNetwork | `dim_network` (from `marketshare_bronze.dimnetwork`) | `research_gold.dim_network` |
| Product Categories (`productcategories.csv`) | dimAdvertiserBrand | `ref_product_category` | `research_gold.dim_advertiser_brand` |
| Four Part Genre (`fourpartgenre.csv`) | dimNetworkProgramNameMapping | `ref_program_genre` | attributes of `dim_program_taxonomy` |
| Rules Engine (`rules_engine.csv`) | dimNetworkProgramNameMapping | `ref_program_group_rule` | drives `program_group_summary/detail` in `dim_program_taxonomy` |

## 2. Sources and current state

### 2.1 MarketShare taxonomy S3

| Item | Value |
| --- | --- |
| Prod | `s3://marketshare-prod/prod/mapping/{input,output,semaphore}/` (Confluence 5429035023). QA: `s3://marketshare-nonprod/qa/mapping/` |
| Access | IAM access keys issued by AMS BI. Files cannot be deleted, only overwritten. **CARL needs a read role / bucket policy** (a cross-account `s3:GetObject` and `ListBucket` grant to the CARL Glue role), not user keys |
| Workflow | Research downloads `output/*.csv`, edits it in Excel, uploads it to `input/`, then uploads `semaphore/run-job-now/process_marketshare.semaphore`. The ETL runs for 3–7 minutes, then writes `output/marketshare_etl_end.txt` (or `marketshare_etl_error.txt`) and regenerates `output/*.csv` |
| Files | `input/`: distributormapping (310 rows), fourpartgenre (315), network (388), productcategories (2,906), rules_engine (385). `output/`: distributormapping (314), fourpartgenre (337), network (388), productcategories (2,906) + etl start/end markers (copy dated 23-Oct-2026) |

### 2.2 `marketshare_bronze` (Prod, weekly Wednesday)

| Table | Role here | Notes |
| --- | --- | --- |
| `dimnetwork` | → `dim_network` (doc 00) | Equals S3 `output/network.csv` |
| `dimnetworkprogramnamemapping` | → `dim_program_taxonomy` (doc 00) | Rules Engine **output** |
| `dimadvertiserbrand` | → `dim_advertiser_brand` | Product categories applied |
| `dimmediatype` | → `dim_media_type` | |
| `dimadintelattribute` | → `dim_ad_attribute` | |
| `dimdaypart`, `dimtimeshiftedviewing` | Validate the doc 00 seeds | |
| `dimprogramdescriptor` | Panel-era descriptor reference; MIT descriptors come from MIT (doc 00 5.1) | |
| `factadintel` | → `fct_adintel_occurrence` | Spend fact |
| `factprogram` | Not used for new Gold. Fallback Panel history source (Q-SH-03) | |

**Gap:** `distributormapping` is **not** in `marketshare_bronze`. It exists only on S3, which is the main reason to land the taxonomy (section 3).

## 3. Bronze: `marketshare_taxonomy_bronze`

### 3.1 Design

- **Trigger.** An EventBridge rule on `s3:ObjectCreated` for `output/marketshare_etl_end.txt` or `marketshare_etl_error.txt` starts the MWAA DAG `marketshare_taxonomy_landing`. A daily 06:00 UTC poll is the safety net.
- **Snapshot.** Each successful ETL run is one snapshot: copy every `input/*.csv` and `output/*.csv` to CARL landing, `s3://carl-landing-…/marketshare_taxonomy/snapshot_id=<etl_end_ts>/{input,output}/`, and land it.
  - Both folders are needed. `input` is what Research intended; `output` is what the ETL applied (it adds new Nielsen codes).
- **Pattern P1.** Append per snapshot, partitioned `identity(snapshot_id)`, never updated.
- **Error marker.** If `marketshare_etl_error.txt` is newer than `marketshare_etl_end.txt`, land the `input` files with `etl_status = 'ERROR'`, alert, and do **not** advance Silver.

### 3.2 File-reading contract (mandatory: leading zeros and Excel damage)

| Rule | Detail | Evidence |
| --- | --- | --- |
| TX-01 Read **every column as string** | No schema inference. Spark `inferSchema=false`, explicit `StringType` schema | `ProgramSubTypeCd = '00'` in 40 rows; leading-zero codes such as `'0123'` must survive |
| TX-02 Encoding `utf-8-sig` | Strip the BOM | `rules_engine.csv` starts with a BOM |
| TX-03 Trim header names; map to snake_case | Header names have trailing spaces | `rules_engine.csv` |
| TX-04 Keep the raw value | Store values exactly; do not trim in Bronze (trim in Silver) | Padding is diagnostic (301 padded `ProgramTypeDescription` rows) |
| TX-05 Drop fully blank rows, but count them | `_blank_row_count` in the manifest | 1 blank row in `fourpartgenre` input |
| TX-06 Never cast `HASH_VALUE` | Excel has turned it into scientific notation (`1.23457E+18`) in 1,467 of 2,906 `productcategories` input rows. It is unusable as a key; recompute hashes in Silver | Profiling 29-Oct |
| TX-07 Never trust `LAST_PROCESS_UTC` from `input/` | Excel has mangled it to `mm:ss.f` (e.g. `51:47.4`) in every input row | `distributormapping`, `network` |
| TX-08 Negative distributor codes are valid | Negative codes are syndicators (e.g. `-5` ESPN) | `distributormapping` |
| TX-09 Lineage columns | `snapshot_id`, `folder` (`input`/`output`), `source_file`, `source_row_number`, `ingest_timestamp` (string, per the Bronze standard), `file_md5` | |

The same rules apply to anyone loading the Snowflake sample CSVs. The samples in `MarketResearch-sample/` have every timestamp mangled, and `HASH_VALUE` in scientific notation in 167/388 (`dimNetwork`), 44/100 (`dimAdvertiserBrand`) and 46/100 (`dimNetworkProgramNameMapping`) rows. In Excel, choose **Data → From Text/CSV → "Do not detect data types"** (the "DON'T CONVERT" option).

### 3.3 Bronze tables

All columns are `string` and every table carries the TX-09 lineage columns.

| Table | Source file | Columns (as delivered, snake_cased) |
| --- | --- | --- |
| `taxonomy_run_manifest` | ETL markers + listing | `snapshot_id`, `etl_start_ts`, `etl_end_ts`, `etl_status`, `file_name`, `folder`, `row_count`, `blank_row_count`, `file_md5`, `s3_last_modified` |
| `distributormapping_raw` | `distributormapping.csv` | as delivered (distributor code, distributor name, network, `_networksk`, isactive, hash_value, last_process_utc). **Exact header To verify** |
| `network_raw` | `network.csv` | same columns as `marketshare_bronze.dimnetwork` |
| `fourpartgenre_raw` | `fourpartgenre.csv` | `programtypecd`, `programtypedescription`, `programsubtypecd`, `programsubtypedescription`, `fourpartgenre`, … |
| `productcategories_raw` | `productcategories.csv` | `productid`, `productdescription`, `productsubcategory`, `productmajorcategory`, `category`, `subcategory`, `hash_value`, … |
| `rules_engine_raw` | `rules_engine.csv` (input only; the ETL does not echo it) | `priority`, `rule_group`, `network`, `network_operator`, `program_name`, `program_name_operator`, `program_type`, `program_type_operator`, `program_subtype`, `program_subtype_operator`, `program_group_summary`, `program_group_detail`, … **Exact header To verify** |

### 3.4 Profiling findings to carry into DQ (23-Oct-2026 copy)

| # | Finding | Handling |
| --- | --- | --- |
| P-01 | `output/network.csv` equals `marketshare_bronze.dimnetwork` (0 differences) | Bronze dimnetwork stays the `dim_network` source; the S3 copy is for audit |
| P-02 | `distributormapping` output has 4 more codes than input (`-124`, `-125`, `45845`, `62292`) | The ETL adds new distributors. Silver uses output and flags codes missing from input (`is_auto_added`) |
| P-03 | 111 networks have more than one distributor code | Expected (feeds and syndicators). The key is the distributor code |
| P-04 | `fourpartgenre` output adds 23 type/subtype combos with blank genre | The ETL auto-appends new Nielsen codes. Raise them as `taxonomy_unmapped` for Research |
| P-05 | `rules_engine` priority 299 rule group reads `#NAME?` | Excel formula corruption. Blocks loading for that rule → DQ-MS-03 |
| P-06 | A priority 102 rule named "events" outputs `Non-Event` | Review with Research (Q-MS-04) |
| P-07 | Priorities 402 and 501 have `Unmapped` outputs, outside the 996–999 band | Review (Q-MS-04) |
| P-08 | `Sports ` with a trailing space in 54 rules | Trim in Silver |
| P-09 | `dimAdvertiserBrand` sample has `ISACTIVE = FALSE` in all 100 rows | **Never filter dims on `isactive`** |
| P-10 | 22 % of the `dimNetworkProgramNameMapping` sample is `Unmapped - Review` | Coverage KPI (DQ-MS-06) |

## 4. Silver: reference tables (`research_silver`)

All four tables are built from the **latest successful** snapshot (`taxonomy_run_manifest.etl_status = 'SUCCESS'`). Each is P4 SCD2 on `_record_hash`, so history of every Research edit is kept (`effective_from = etl_end_ts`).

### 4.1 `ref_program_group_rule`

| Column | Type | Rule |
| --- | --- | --- |
| `rule_key` | bigint | `xxhash64(priority || '|' || network || '|' || program_name || '|' || program_type || '|' || program_subtype)` |
| `priority` | int | Cast; must be unique per active rule set (DQ-MS-02) |
| `priority_band` | string | Derived: 0–99 Special, 100s Sports, 200s Kids, 300s News, 400s Female-skewed Ent, 500s Ent Tier 1, 600s Ent Tier 2, 700s Catch-all, 996–999 Unmapped |
| `network_type_band` | string | Tens digit: 00 cable, 10 Big 4, 20 other broadcast, 30 syndication, 40 streaming |
| `rule_group` | string | trimmed |
| `network`, `program_name`, `program_type`, `program_subtype` | string | Matching values, trimmed. `program_type` / `program_subtype` keep leading zeros |
| `network_op`, `program_name_op`, `program_type_op`, `program_subtype_op` | string | One of `=`, `any`, `like`. Anything else (e.g. `<>`) fails DQ-MS-01 |
| `program_group_summary`, `program_group_detail` | string | trimmed. 9 summary values, 19 detail values |
| `effective_from`, `effective_to`, `is_current`, `snapshot_id` | | |

**BR-MS-01 Rules Engine evaluation** (documented here so CARL can reproduce and test the ETL):
1. For each `(network, program)` row, evaluate current rules in ascending `priority`.
2. A rule matches when every condition matches:
   - `=`: case-insensitive equality after trim.
   - `any`: always true.
   - `like`: SQL `LIKE` with `%` wildcards, case-insensitive.
3. **First match wins.** It sets `program_group_summary` and `program_group_detail`.
4. If nothing matches, use `Unmapped - Review`.

Status: Confirmed semantics (Confluence 5478908116); exact case-sensitivity To verify (Q-MS-02).

### 4.2 `ref_adintel_distributor`

Grain: one row per `distributor_code`.

| Column | Type | Rule |
| --- | --- | --- |
| `distributor_code` | string | Keep as string, including negatives |
| `distributor_name` | string | trimmed |
| `network_key` | bigint | Resolve to `dim_network` via `_networksk` |
| `is_syndicator` | boolean | `distributor_code` starts with `-` |
| `is_auto_added` | boolean | P-02 |
| `is_active` | boolean | |
| SCD2 and audit columns | | |

### 4.3 `ref_program_genre`

Grain: one row per `(program_type_cd, program_subtype_cd)`, keeping leading zeros.

Columns: `program_type_cd`, `program_type_desc` (trimmed), `program_subtype_cd`, `program_subtype_desc`, `four_part_genre`, `is_unmapped` (blank genre), `is_auto_added`, plus the SCD2 columns.

Four Part Genre is deprecated for reporting. Keep the table because it provides type and subtype descriptions and the backlog of new codes.

### 4.4 `ref_product_category`

Grain: one row per `product_id`.

Columns: `product_id` (string), `product_desc`, `product_subcategory`, `product_major_category`, `category` (24 values), `subcategory`, `_record_hash` (recomputed, TX-06), plus the SCD2 columns.

## 5. Silver: dimensions and Ad Intel fact

### 5.1 `dim_advertiser_brand` (SCD2, published to Gold)

| Item | Value |
| --- | --- |
| Grain | One row per `_advertiserbrandsk` |
| Source | `marketshare_bronze.dimadvertiserbrand` + `ref_product_category` |

| Column | Rule |
| --- | --- |
| `advertiser_brand_key` | `xxhash64('ADVBRAND|' || _advertiserbrandsk)` |
| `brand_code`, `brand_desc`, `brand_variant` | as delivered |
| `advertiser_parent_code` / `_desc`, `advertiser_subsidiary_code` / `_desc` | as delivered |
| `product_id`, `product_desc`, `product_subcategory`, `product_major_category` | as delivered |
| `category`, `subcategory` | Research category, from `ref_product_category` when the Bronze value is blank |
| `is_active` | Kept for display; never used as a filter (P-09) |

### 5.2 `dim_media_type`, `dim_ad_attribute`

Straight Silver copies with standard keys:
- `media_type_key`, `media_type_desc` (6 values) from `dimmediatype`.
- `ad_attribute_key` plus the attribute columns from `dimadintelattribute`. Column list To verify against Bronze.

### 5.3 `fct_adintel_occurrence`

| Item | Specification |
| --- | --- |
| Grain | One row per Ad Intel occurrence (`_factadintelsk`) |
| PK | `adintel_occurrence_key = xxhash64(_factadintelsk)` |
| Source | `marketshare_bronze.factadintel` |
| Partition | `months(ad_date)` |
| Load | P2 MERGE on `_factadintelsk`, using `hash_value` change detection. Weekly MarketShare reloads restate the trailing weeks |

| Column | Type | Rule |
| --- | --- | --- |
| `ad_date`, `date_key` | date, int | from `_addatesk` |
| `ad_time` | string | from `_adtimesk` |
| `daypart_key` | bigint | via `bridge_daypart_quarterhour` |
| `network_key`, `media_type_key` | bigint | from `_networksk`, `_mediatypesk` |
| `primary_advertiser_brand_key`, `secondary_…`, `tertiary_…` | bigint | from the three brand SKs |
| `program_descriptor_sk`, `ad_attribute_key` | bigint | |
| `units` | int | |
| `duration_sec` | int | |
| `spend_usd` | decimal(38,4) | `spend` |
| `eq30_units` | decimal(18,4) | `units * duration_sec / 30` |
| `is_static_segment` | boolean | `ad_date < adintel.static_segment_end_date`. Before mid-2024 FACTADINTEL is a frozen MS1.0 snapshot (VAMI hub "Major Nuance"), so this segment is never restated |
| `is_active` | boolean | Keep the source value; Gold filters on it only when Q-MS-01 says to |
| `src_delivered_data_file_id`, `src_partition_year` | | lineage |

## 6. Gold (`research_gold`)

### 6.1 Published dimensions

`dim_network`, `dim_program_taxonomy`, `dim_advertiser_brand`, `dim_media_type`, `dim_ad_attribute`, `dim_broadcast_calendar`, `dim_daypart`. Copy-on-write, published by WAP.

### 6.2 `ms_fct_adintel_spend_daily`

| Item | Specification |
| --- | --- |
| Grain | `date_key × network_key × media_type_key × primary_advertiser_brand_key × daypart_key` |
| Measures | `spend_usd` (sum), `units` (sum), `eq30_units` (sum), `occurrence_count` |
| Filters | Rows kept per Q-MS-01 (`is_active`) |
| Partition | `months(ad_date)` |
| Load | P3 rebuild of the affected months |

### 6.3 `ms_agg_category_share_month`

| Item | Specification |
| --- | --- |
| Grain | `broadcast_month_key × network_key × category` |
| Measures | `spend_usd`, `units`, `eq30_units` |
| Derived in Cube | `spend_share_of_category_pct`, `wbd_share_pct` |

### 6.4 Additional rules

- **BR-MS-02 Estimated spend.** `EST. SPEND = sum(spend_usd)`, with no further transformation. This is parity with the Power BI Ad Spend dashboard. Confirmed.
- **BR-MS-03 Network rebrands.** Aggregate on `dim_network.network_name` (doc 00 BR-SH-04). Examples: HLDRM→HFAM, DIY→MAG, NLX→CRS. Confirmed.
- **BR-MS-04 Junk SKs.** Exclude `is_junk_sk` networks only from the network picker in Cube, never from totals. Proposed.

### 6.5 `factprogram`

Do not use it to build new Gold. Use it only as the Panel-history fallback (Q-SH-03) and for parity tests against legacy MarketShare outputs.

### 6.6 Phase 2: CARL-native Rules Engine (option)

CARL could apply `ref_program_group_rule` to MIT descriptors itself (BR-MS-01) and produce `dim_program_taxonomy` without waiting for the weekly AMS BI ETL.

- **Acceptance:** 100 % agreement with `dimnetworkprogramnamemapping` on a full snapshot.
- **Status:** Decision (Q-MS-05).

## 7. Data quality

| ID | Object | Check | Severity |
| --- | --- | --- | --- |
| DQ-MS-01 | `ref_program_group_rule` | Operators ∈ {`=`, `any`, `like`} | BLOCKER |
| DQ-MS-02 | `ref_program_group_rule` | `priority` unique among current rules | BLOCKER |
| DQ-MS-03 | All taxonomy Silver tables | No `#NAME?`, `#REF!`, `#VALUE!` or `#N/A` values; no scientific-notation codes | BLOCKER (P-05) |
| DQ-MS-04 | `ref_program_genre` | Leading-zero codes preserved (`'00'` count is the same in Bronze and Silver) | BLOCKER |
| DQ-MS-05 | Taxonomy snapshot | Row counts within ±10 % of the previous snapshot; any key deleted vs previous | WARN |
| DQ-MS-06 | `dim_program_taxonomy` | Share of current rows `is_unmapped`; share of MIT impressions on unmapped programs | WARN (target < 5 % of impressions) |
| DQ-MS-07 | `fct_adintel_occurrence` | Orphan FK share for network, brand and media type | ≤ 0.1 % BLOCKER |
| DQ-MS-08 | `fct_adintel_occurrence` | Static segment (`is_static_segment`) row count and spend are unchanged week to week | BLOCKER (detects accidental restatement of MS1.0) |
| DQ-MS-09 | `ms_fct_adintel_spend_daily` | Sum of spend = Bronze `factadintel` sum for the same filters | Exact, BLOCKER |
| DQ-MS-10 | Taxonomy run | `etl_status = 'ERROR'` or no new snapshot for 14 days when input files changed | WARN |

## 8. Cube

### 8.1 Views

| View | Grain | Key measures | Key dimensions |
| --- | --- | --- | --- |
| `ms_view_adintel_spend` (alias `marketplace_view_adintel_spend`) | daily | `est_spend` (= `sum(spend_usd)`), `units`, `eq30_units`, `occurrences`, `spend_share_of_selection_pct` (multi-stage) | broadcast calendar, network (name, ownership, type, division, is_wbd), media type, advertiser parent / subsidiary / brand, category / subcategory, daypart |
| `ms_view_adintel_sales` | Restricted subset for Ad Sales | `est_spend`, `units` | the same, without brand variant or product detail |
| `ms_view_taxonomy_coverage` | rule / program | `unmapped_programs`, `unmapped_impressions_pct` | rule group, priority band, network |

### 8.2 Golden queries

1. WBD est. spend by month, broadcast 2025.
2. Top 10 advertisers by spend on TBS, Q3 2025.
3. Category share for Cable TV, Sep 2025.
4. Spend by ownership group, last 13 broadcast weeks.
5. Eq30 units by daypart for TNT.
6. Spend for Hallmark Family across the HLDRM→HFAM rebrand, which must be continuous.
7. Static-segment spend total, which must equal the MS1.0 baseline.
8. Spend for `Cable TV` + `Network TV`.
9. Unmapped program count.
10. Spend by network type.

Each value must match the legacy Power BI Ad Spend dashboard or Snowflake SQL within ±0.1 %, and match the Gold SQL exactly.

## 9. Orchestration

| DAG | Trigger | Steps |
| --- | --- | --- |
| `marketshare_taxonomy_landing` | EventBridge on the ETL end/error marker; daily poll | copy snapshot → Bronze (P1) → manifest → DQ-MS-03/04/05 → Silver ref tables (P4) |
| `research_conformed_dims` | doc 00 | dims |
| `marketshare_gold` | Dataset on `marketshare_bronze.factadintel` (weekly, Wednesday) | `fct_adintel_occurrence` (MERGE) → Gold (P3) → DQ-MS-07..09 → WAP publish → Cube refresh |

## 10. Open decisions

| ID | Question | Owner | Default |
| --- | --- | --- | --- |
| Q-MS-01 | Filter `factadintel.isactive = true` in Gold? Is "inactive" a soft delete? | AMS BI | Exclude inactive facts; keep inactive dims |
| Q-MS-02 | Rules Engine match: case-insensitive? Is `like` SQL-style `%`? | AMS BI | Case-insensitive, SQL `%` |
| Q-MS-03 | Exact column headers of `distributormapping.csv` and `rules_engine.csv` | CARL DE (from the S3 copy) | Read from the 23-Oct copy |
| Q-MS-04 | Fix the rule anomalies P-05, P-06, P-07 | Research | Research fixes them in the next upload |
| Q-MS-05 | Build the CARL-native Rules Engine (6.6)? | Ping Feng + Research | Phase 2 |
| Q-MS-06 | CARL read access to `marketshare-prod` (cross-account role, not user keys) | AMS BI + CARL Platform | Bucket policy grant |
| Q-MS-07 | Static-segment end date (`adintel.static_segment_end_date`) | AMS BI | 2024-06-10 (To verify) |

## 11. Backlog (proposed Jira stories, under epic CARL-3775)

| Story | Summary | Depends on |
| --- | --- | --- |
| MS-01 | Grant CARL read access to `marketshare-prod/prod/mapping` | Q-MS-06 |
| MS-02 | `marketshare_taxonomy_bronze` landing DAG + manifest (TX-01..09) | MS-01 |
| MS-03 | Silver ref tables `ref_program_group_rule`, `ref_adintel_distributor`, `ref_program_genre`, `ref_product_category` | MS-02 |
| MS-04 | `dim_advertiser_brand`, `dim_media_type`, `dim_ad_attribute` | doc 00 dims |
| MS-05 | `fct_adintel_occurrence` MERGE + static segment guard | MS-04 |
| MS-06 | Gold `ms_fct_adintel_spend_daily`, `ms_agg_category_share_month` + WAP | MS-05 |
| MS-07 | Cube views + golden queries vs Power BI Ad Spend | MS-06 |
| MS-08 | Taxonomy DQ dashboard + Research alerts (P-04, P-05, DQ-MS-06) | MS-03 |
