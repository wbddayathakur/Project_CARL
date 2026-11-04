# 00 – Research Data Foundation: Shared Standards, Conformed Dimensions and Shared Silver

| Field | Value |
| --- | --- |
| Program | CARL (Iceberg on S3 + AWS Glue Catalog + Athena / Glue Spark + MWAA) and the Cube semantic layer |
| Jira | Epic CARL-3775 (Research Market Share Insight BI) · Epic CARL-11 (NextGen) |
| Owner | Daya Thakur (Product) · Ping Feng (Engineering) |
| Status | DRAFT v0.1 – 29 Oct 2026 |
| Companion documents | `01_marketshare_data_requirements.md` · `02_market_research_marketplace_insights_data_requirements.md` · `03_nextgen_research_dashboard_data_requirements.md` |

## Jira tracking

| Item | Jira |
| --- | --- |
| Databases `research_silver` / `research_gold`, Iceberg standards, WAP, `ref_pipeline_config`, `ops_*` tables | CARL-4399 |
| `big_mit_bronze.dimdate` + `dim_broadcast_calendar` | CARL-4395 |
| Shared calendar / demo / daypart / stream / network dims | CARL-557 (shared build), CARL-4116 (crosswalk, program taxonomy, advertiser) |
| Shared MIT Silver `dim_telecast` + `fct_mit_telecast_viewing` | CARL-4117; quarter-hour and universe Silver in CARL-555 |
| Methodology cutover and dedupe | CARL-4114 |
| Panel Only history backfill | Epic CARL-4292, CARL-4294 |
| DQ and freshness | CARL-4121 (Marketplace), CARL-4126 (NextGen), shared tables in CARL-4399 |
| Orchestration | CARL-4125 |

Decisions recorded on 29-Oct-2026:
- Panel history comes from a backfill (CARL-4292).
- `COMMON.DIMDATE` is landed as the calendar source.
- `research_*` naming is adopted.

## 0. How to read this set

Three business objectives share most of their data, so the requirements are split into one shared foundation and three objective documents.

| Doc | Objective | Main consumer today | What it owns |
| --- | --- | --- | --- |
| **00 (this)** | Shared foundation | All three | Naming, Iceberg standards, conformed dimensions (calendar, network, program, demo, daypart, viewing stream), shared Nielsen MIT Silver, DQ and freshness framework, Cube conventions |
| **01 MarketShare** | Rebuild the AMS BI MarketShare 2.0 consumption layer in CARL: taxonomy (Rules Engine + 4 mapping files) and Nielsen Ad Intel spend | Power BI NextGen **Ad Spend** dashboard (`FACTADINTEL`), Looker dimension views, VAMI | Taxonomy Bronze, taxonomy reference tables, advertiser and Ad Intel facts |
| **02 Market Research (Marketplace Insights / VAMI)** | Replace the Looker VAMI 3 Explore and the Marketplace Imps query: C3 impressions (Panel Only + Big MIT) joined to Guideline spend | Looker `VAMI 3` (`mit_adintel_smi_v2`), Research SQL, Quick | Guideline Bronze, telecast match, supply/demand facts, category spend |
| **03 NextGen Research** | Rebuild the NextGen Ad Sales **Research** Power BI dashboard on CARL, re-based from AMRLD to NRLD, plus MRI | Power BI `NextGenResearchDashboard` (dataset `NextGenResearchDataSource`) | MIT delivery/share/universe facts, NRLD reach and audience profiles, MRI index |

Every requirement carries a status:

- **Confirmed**: proven by data, code or a signed-off page.
- **Proposed**: a design recommendation. Needs review, but is the default if nobody objects.
- **Decision**: cannot be built until the named owner decides. A default is given.
- **To verify**: a fact that has to be checked against a live system before the build starts.

## 1. Current CARL state (evidence)

| Area | State | Evidence |
| --- | --- | --- |
| `big_mit_bronze` (8 tables) | Prod, daily 13:30 / 17:30 / 19:30 UTC | Glue Prod catalog 27-Aug-2026; Oct catalog scan |
| `marketshare_bronze` (10 tables) | Prod, weekly (Wed) | Same |
| `nrld_bronze` (12 tables) | **Dev only**; Prod files land but are not registered; duplicates and late rows open | CARL-2952 (Blocked), CARL-3781 (In Review), CARL-4124 (To Do) |
| Guideline Telecast / AccuTV | Not in CARL. Files land in `s3://turner-ams-bi-marketshare-smi/DataOutgoing/` (AWS account 689264014593) | S3 listing 26-Oct-2026 (latest Telecast 28-Sep-2026, AccuTV 26-Sep-2026) |
| MarketShare taxonomy S3 (`marketshare-prod/prod/mapping/`) | Not in CARL. Its outputs are in `marketshare_bronze` dims, except `distributormapping` | Taxonomy copy 23-Oct-2026 profiled 29-Oct-2026 |
| Nielsen MIT Panel Only (`AMS_ICUE_SHARE.MIT`) | Not in CARL (only indirectly via `marketshare_bronze.factprogram`) | Catalog |
| `COMMON.DIMDATE` | Not in CARL | Catalog |
| MRI (`AMS_ICUE_SHARE.MRI`), MRI Streaming RLD (SFTP) | Not in CARL | PRD S7, S8 |
| Silver / Gold / Cube for any research source | **None exist** | Catalog; `iceberg-catalog-agent/registry/cube_model.yaml` (all research views `proposed`) |

## 2. Database and naming standards

### 2.1 Databases (Glue catalog)

Earlier drafts used three different target names: `marketplace_insights_*` (Market Share discovery), `measurement_*` (NextGen discovery) and `studios_gold` (the Databricks catalog in the CARL-88 page). This set replaces them with one Silver and one Gold database for the research domain. Dimensions are then built once and shared, and Cube joins never cross databases.

| Layer | Database | Contents | Status |
| --- | --- | --- | --- |
| Bronze | `big_mit_bronze`, `marketshare_bronze`, `nrld_bronze` | Existing. Add `big_mit_bronze.dimdate` (see 4.1) | Exists / Proposed addition |
| Bronze | `mit_panel_bronze` | One-time backfill of `AMS_ICUE_SHARE.MIT` Panel Only viewing and descriptors (doc 02) | Decision (Q-SH-03) |
| Bronze | `guideline_bronze` | Guideline Telecast + AccuTV deliveries and manifest (doc 02) | Proposed |
| Bronze | `marketshare_taxonomy_bronze` | Versioned snapshots of the 5 MarketShare S3 mapping files (doc 01) | Proposed |
| Bronze | `mri_bronze`, `mri_streaming_bronze` | MRI share objects and MRI Streaming RLD (doc 03, Phase 2) | Proposed |
| Silver | `research_silver` | Cleaned, deduplicated, conformed, source-aligned tables. Shared by all three objectives | Proposed |
| Gold | `research_gold` | Consumption tables: published `dim_*`, and product facts prefixed `ms_` (MarketShare), `mi_` (Marketplace Insights), `ngr_` (NextGen Research), plus `ops_*` | Proposed |

S3 locations follow the existing CARL convention: `s3://carl-{layer}-us-east-1-{env}/aws/iceberg/{database}/{table}/`. Environments are Dev → QA → Stage → Prod, promoted by release tag (NFR-05).

### 2.2 Table and column naming

| Item | Rule | Example |
| --- | --- | --- |
| Tables | `snake_case`; dimension `dim_`, fact `fct_`, aggregate `agg_`, reference/seed `ref_`, bridge `bridge_`, ops `ops_`; Gold facts carry the product prefix | `research_gold.mi_fct_telecast_supply` |
| Surrogate keys | `<entity>_key bigint` = `xxhash64` of the normalised natural key (upper, trimmed, `|`-joined). Deterministic, so keys survive rebuilds and environments | `network_key = xxhash64('NETWORK|' || _networksk)` |
| Source keys | Keep source names with a `src_` prefix when they are not the business key | `src_networksk` |
| Booleans | `is_` / `has_` prefix, never null (default false) | `is_reporting_network` |
| Units | Suffix the unit: `_000` thousands, `_sec`, `_min`, `_pct` (0–100), `_usd` | `gross_impressions_000`, `duration_sec` |
| Dates | `_date` (date), `_ts` (timestamp UTC), period keys as int: `date_key` YYYYMMDD, `broadcast_week_key` YYYYWW, `broadcast_month_key` YYYYMM, `broadcast_quarter_key` YYYYQ | `broadcast_month_key = 202509` |
| Codes vs labels | `_cd` for codes, `_desc` / `_name` for labels | `program_type_cd`, `program_type_desc` |

### 2.3 Standard audit columns (every Silver and Gold table)

| Column | Type | Rule |
| --- | --- | --- |
| `_source_system` | string | e.g. `NIELSEN_BIG_MIT`, `NIELSEN_PANEL_MIT`, `MARKETSHARE`, `GUIDELINE`, `NRLD`, `MRI`, `SEED` |
| `_source_table` | string | Fully qualified Bronze table |
| `_source_file` | string | Bronze `source_file` (or manifest `file_name`) |
| `_bronze_ingest_ts` | timestamp | `cast(ingest_timestamp as timestamp)`. Bronze stores it as **string**, so cast it explicitly |
| `_record_hash` | bigint | `xxhash64` of business columns, for change detection |
| `_run_id` | string | MWAA `dag_id/run_id` |
| `_load_ts` | timestamp | Write time (UTC) |

### 2.4 Iceberg table standards

| Setting | Silver | Gold | Why |
| --- | --- | --- | --- |
| `format-version` | 2 | 2 | Row-level deletes and MERGE |
| File format / codec | Parquet / zstd | Parquet / zstd | CARL standard |
| `write.delete.mode`, `write.update.mode`, `write.merge.mode` | `merge-on-read` for facts merged daily (MIT, Ad Intel); `copy-on-write` for dims and reference tables | `copy-on-write` | Silver absorbs frequent restatements cheaply; Gold is read-optimised for Athena and Cube |
| Compaction | `rewrite_data_files` (target 512 MB) and `rewrite_position_delete_files` daily for MoR tables | Weekly | Keeps Athena scans small |
| Snapshot expiry | 30 days (facts), 90 days (dims), 365 days (seeds, for audit) | 90 days | Time travel for restatement questions |
| Athena compatibility | Follow the CARL-3935 serialization rule on every writer, and `SELECT` from Athena in the acceptance criteria | Same | A known Athena read failure |
| Partitioning | Hidden partitions only (`months(broadcast_date)`, `identity(delivery_id)`). Never partition dims under 1 M rows | Same | Pruning without user-visible partition columns |
| Table lifecycle | Terraform owns databases and tables (CARL-3549); no dynamic DDL in Glue jobs | Same | CARL governance |

### 2.5 Write-audit-publish (WAP) for every Gold table

1. The Glue Spark job writes to the Iceberg branch `audit_<run_id>` (`spark.wap.branch`).
2. Blocker DQ checks (section 7) run against the branch.
3. Pass: `fast_forward('main', 'audit_<run_id>')`, then update `ops_data_freshness`, then refresh Cube pre-aggregations.
4. Fail: `main` is untouched, so Quick, Power BI and Cube keep showing the last good data. Results go to `ops_dq_results` and an alert is raised.

Status: Proposed. Confirm that the Glue version used by CARL supports Iceberg branches (Iceberg ≥ 1.2). If it does not, fall back to a staging table plus an atomic `INSERT OVERWRITE` / `MERGE` into the target.

## 3. Load patterns

| Pattern | Used for | Mechanics |
| --- | --- | --- |
| **P1 Append-per-delivery** | Vendor files that restate history (Guideline), taxonomy snapshots | Bronze partition `identity(delivery_id)` / `identity(snapshot_id)`. Never update a delivered partition. Silver picks the current version through the manifest |
| **P2 MERGE on natural key** | Nielsen MIT viewing and descriptors, Ad Intel occurrences, NRLD events | `MERGE INTO … USING (deduped batch) ON <natural key> WHEN MATCHED AND src._record_hash <> tgt._record_hash THEN UPDATE WHEN NOT MATCHED THEN INSERT`. Restatements replace, never append |
| **P3 Rolling-window rebuild** | Gold aggregates whose inputs restate (C3/L+7 settle) | Rebuild only affected `broadcast_month` partitions (`overwrite` with dynamic partition mode), found from the Silver changed-key set |
| **P4 SCD2 MERGE** | `dim_network`, `dim_advertiser_brand`, `dim_program_taxonomy` | Close the current row (`effective_to`, `is_current = false`) when `_record_hash` changes; insert a new row |
| **P5 Seed overwrite** | Git-managed CSVs (crosswalks, event map, WBD network attributes, demo/daypart definitions) | CSV in repo → CI validates the schema → `INSERT OVERWRITE`, snapshot tagged with the Git SHA |

## 4. Conformed dimensions (built once in `research_silver`, published to `research_gold`)

### 4.1 `dim_broadcast_calendar`

| Item | Specification |
| --- | --- |
| Grain | One row per calendar date, 2014-01-01 to 2030-12-31 |
| Primary key | `date_key` |
| Source | **Primary:** `big_mit_bronze.dimdate`, a new table landed from `SHARE_PROD_BIG_MIT.COMMON.DIMDATE` by adding it to the existing `landing_to_bronze_iceberg_bigmit` pipeline. The Research SQL and MarketShare join to this table, so sourcing from it guarantees parity. **Fallback / extension:** generated rows for dates outside the DIMDATE range |
| Load | P5-style full overwrite whenever DIMDATE changes (small, about 6 K rows) |
| Status | Proposed; DIMDATE column names To verify (known: `datesk`, `broadcastdate`, `broadcastquarter` formatted `'2025 Q3'`, `broadcastyear`) |

| Column | Type | Derivation |
| --- | --- | --- |
| `date_key` | int | `datesk` (YYYYMMDD) |
| `calendar_date` | date | `to_date(datesk)` |
| `day_of_week_num` / `day_of_week_name` | int / string | 1 = Monday … 7 = Sunday |
| `is_weekday` | boolean | Mon–Fri |
| `broadcast_week_start_date` | date | Monday of the week |
| `broadcast_week_key` | int | YYYYWW of the broadcast year |
| `broadcast_month_key` | int | YYYYMM. A broadcast month runs from the Monday of the week containing the 1st to the last Sunday of the month |
| `broadcast_month_start_date` / `_end_date` | date | |
| `broadcast_month_label` | string | `'Sep 2025'` (Power BI `MONTH_SORT`, `BC Month Text`) |
| `broadcast_quarter_key` | int | YYYYQ |
| `broadcast_quarter_label` | string | `'2025 Q3'`. **Must equal `DIMDATE.broadcastquarter`** (used by the Marketplace Imps query) |
| `broadcast_year` | int | |
| `weeks_in_broadcast_month` / `_quarter` / `_year` | int | 4/5, 13/14, 52/53 (BR-SH-03) |
| `season_label` | string | TV season (late Sep – Sep) e.g. `'2025-26'`; boundary rule To verify with Research |
| `ue_year`, `ue_quarter_key` | int | Nielsen universe-estimate year (starts in broadcast Q3, September). Used by NextGen `WM_UE_CALENDAR` |
| `calendar_month_key`, `calendar_quarter_key`, `calendar_year` | int | Gregorian equivalents |

Rules:
- **BR-SH-01 Broadcast date (6a–6a).** If the airing time is before 06:00 local, `broadcast_date = airing_date - 1`. Nielsen supplies `_broadcast_datesk` and `broadcast6_6datetime` already; use the supplied value and do not recompute it (test: 2022-04-24 05:45 → 2022-04-23). Confirmed.
- **BR-SH-02 Period keys come from the calendar, never from `date_trunc`.** Broadcast months do not align with calendar months. Confirmed.
- **BR-SH-03 Weeks-in-period normalisation.** `avg_per_bc_week = metric / count(distinct broadcast_week_key)` in the selected period. Confirmed (Market Share intake).

### 4.2 `dim_network` (SCD2)

| Item | Specification |
| --- | --- |
| Grain | One row per MarketShare network surrogate (`_networksk`) per effective period |
| Primary key | `network_key` + `effective_from` |
| Sources | `marketshare_bronze.dimnetwork` (388 rows; identical to the S3 `output/network.csv` on 23-Oct-2026: 0 differences on name, network, ownership, type, MIT code, media type); `ref_adintel_distributor` (doc 01); `ref_network_crosswalk` (doc 02); `ref_network_wbd_attributes` (doc 03) |
| Load | P4 SCD2 on `hash_value` change in Bronze |
| Status | Proposed |

| Column | Type | Source / rule |
| --- | --- | --- |
| `network_key` | bigint | `xxhash64('NETWORK|' || _networksk)` |
| `src_networksk` | bigint | `_networksk` |
| `network_code` | string | `name` (e.g. `TBSC`, `HFAM`). Can be null for SK 0 |
| `mit_network_cd` | string | `mitnetworkcd` (join key from MIT `network_label`; unique where not null; 24 nulls) |
| `mit_network_id` | bigint | `mitnetworkid` (join key from MIT `nielsennetworkid`) |
| `network_name` | string | `network`. The **continuous reporting name** (e.g. `Hallmark Family` covers HLDRM and HFAM). **Always aggregate on this column** (BR-SH-04) |
| `network_long_name` | string | `mvlongformname` |
| `mediaview_net_list` | string | `mediaviewnetlist` |
| `ownership_group` | string | `ownershipgroup` (9 values: Other, Warner Bros. Discovery, Paramount, Disney, NBCUniversal, Fox Corp, Versant, A+E Global Media, AMC Global Media). Null in 47 rows → `'Unassigned'` |
| `network_group` | string | `networkgroup` (WBD, PSKY, DIS, …) |
| `network_division` | string | `networkdivision` (`Core 8 + CNN`, `Non-Core`; WBD only) |
| `network_type` | string | `networktype` (10 values; null → `'Unassigned'`) |
| `media_type_desc` | string | `mediatypedescription` (Cable TV, Network TV, Syndicated TV, Spanish Language Cable TV, Spanish Language Network TV, National Streaming) |
| `is_reporting_network` | boolean | `reportingstatus` (114 true). Replaces `VAMI_REPORTING_NETWORKS` |
| `is_active` | boolean | `isactive`. **Do not filter facts on it.** Inactive networks still have history |
| `is_wbd` | boolean | `ownership_group = 'Warner Bros. Discovery'` |
| `is_junk_sk` | boolean | True when the SK has no rows in any MIT or Ad Intel fact (e.g. SK 270 `TBS` vs active SK 271 `TBSC`). Computed weekly |
| `is_guideline_measured` | boolean | Exists in `ref_network_crosswalk` with an include flag (doc 02) |
| WBD presentation attributes | various | Left-joined from `ref_network_wbd_attributes` (doc 03): display name, conglomerate, Main ASCO owner, tier group, `is_asco`, `is_spanish_language`, logo URI |
| `effective_from`, `effective_to`, `is_current` | date, date, boolean | SCD2 |
| Audit columns | | 2.3 |

Rules:
- **BR-SH-04 Network continuity.** Report on `network_name` (continuous); keep `network_code` / `mit_network_cd` as aired. 39 `network_name` values map to more than one SK (e.g. Great American Family = GAC, GACF, GFAM). Confirmed (VAMI hub: "always join and aggregate on `DIMNETWORK.NETWORK`").
- **BR-SH-05 MIT join.** `MIT.network_label = dim_network.mit_network_cd` (Research SQL) and `nielsennetworkid = mit_network_id`. When both are present they must agree, and disagreements go to DQ (DQ-SH-06). Confirmed.
- **BR-SH-06 Case.** Upper-case and trim both sides of every network join (the WEtv vs WETV duplicate in the Looker VAMI 3 Explore). Confirmed.

### 4.3 `dim_program_taxonomy`

| Item | Specification |
| --- | --- |
| Grain | One row per `(nielsen_network_id, acn_program_code)` (the MarketShare program-name mapping grain) |
| Primary key | `program_key = xxhash64(nielsennetworkid || '|' || acn_program_code)` |
| Sources | `marketshare_bronze.dimnetworkprogramnamemapping` (Rules Engine output); `ref_program_genre` (doc 01); `ref_event_program_map` (doc 02) |
| Load | P4 SCD2 |
| Status | Proposed; grain uniqueness To verify (DQ-SH-04) |

| Column | Type | Rule |
| --- | --- | --- |
| `program_key` | bigint | above |
| `src_networkprogramnamemappingsk` | bigint | |
| `nielsen_network_id`, `network_label` | bigint, string | |
| `acn_program_code` | bigint | |
| `program_name` | string | as delivered |
| `program_name_key` | string | `regexp_replace(upper(program_name), '[^A-Z0-9]', '')`, the event-map match key (BR-SH-09) |
| `program_type_cd`, `program_subtype_cd` | string | `program_type`, `program_subtype`. **String, keep leading zeros** (`'00'`) |
| `program_type_desc`, `program_subtype_desc` | string | trimmed |
| `program_group_summary`, `program_group_detail` | string | Rules Engine output, **trimmed** (the source has `'Sports '` with a trailing space on 54 rules). Values: Sports, Kids, News, Entertainment Female-Skewed, Entertainment Tier 1, Entertainment Tier 2, Streaming, Unmapped, Unmapped - Review |
| `is_unmapped` | boolean | `program_group_summary in ('Unmapped','Unmapped - Review')` (22 of 100 sample rows are `Unmapped - Review`) |
| `nielsen_genre_simple` | string | BR-SH-07 |
| `event_name` | string | BR-SH-08 |
| `four_part_genre` | string | `fourpartgenre`. **Deprecated**: keep for lineage, do not expose in Cube (VAMI hub "Four Part Genre Deprecation") |
| `sport`, `sport_type`, `sport_brand`, `event_type` | string | as delivered |
| SCD2 and audit columns | | |

Rules (two genre taxonomies exist and both are needed):
- **BR-SH-07 Simple Nielsen genre** (the Marketplace Imps query): `program_type_cd = 'N'` → `News`; `in ('SC','SE','SA')` → `Sports`; else `Entertainment`. Confirmed (SQL).
- **BR-SH-08 Event tag** (the Marketplace Imps query), evaluated in order:
  1. Match in `ref_event_program_map` on `(upper(trim(network_name)), program_name_key)` → its event.
  2. `program_subtype_cd in ('OLYC','OLYM')` → `Olympics`.
  3. `= 'NFSB'` → `Super Bowl`.
  4. `in ('SMWC','SWWC')` → `World Cup`.
  5. Otherwise `Non-Event`.

  Events are tagged, not excluded. Confirmed (SQL).
- **BR-SH-09 Program match key** strips everything except A–Z and 0–9 after upper-casing, so `'FINAL DRAW ?22'` matches `'FINAL DRAW ''22'`. Confirmed (SQL).
- **BR-SH-10 Program Group Summary** comes from the Rules Engine (doc 01). It is the Research-owned genre for VAMI and Looker, and is a separate attribute from BR-SH-07. Confirmed.

### 4.4 `dim_telecast` (shared MIT descriptor)

Defined in section 5.1.

### 4.5 `dim_demo` and `bridge_demo_cell`

| Item | Specification |
| --- | --- |
| Grain | `dim_demo`: one row per demo. `bridge_demo_cell`: one row per (demo, age/gender cell) |
| Source | Seed (P5), validated against MIT cells and `program_viewing_sellingdemos` |
| Cells | 30 Nielsen cells in MIT Bronze: `females|males` × `2_5, 6_8, 9_11, 12_14, 15_17, 18_20, 21_24, 25_29, 30_34, 35_39, 40_44, 45_49, 50_54, 55_64, 65plus` (`*_delivery` columns) |
| Status | Confirmed (cells); Proposed (demo list) |

`dim_demo` columns: `demo_code` (PK, e.g. `P25-54`, `W25-54`, `M18-49`, `K2-11`, `T12-17`, `P2+`), `gender_cd` (P / W / M; `F` accepted as an alias of `W` on input), `age_min`, `age_max` (999 = open), `demo_desc`, `is_broad_demo` (the 18 Market Share demos), `is_nextgen_demo`, `is_exec_portfolio_demo`, `sort_order`.

Demo lists:
- Market Share broad demos (18): P/W/M × {2+, 18+, 25+, 55+, 18-49, 25-54}.
- NextGen: every `WM_DEMO[DEMO_DESC]` and `DEMO_DESC_FOR_EXEC_PORTFOLIO` value (25+ demos, including K2-11 and K12-17).

Rules:
- **BR-SH-11.** A demo audience is the sum of its cells: `P = W + M`; `25-54 = 25_29 … 50_54`; `18-49 = 18_20 … 45_49`; `55+ = 55_64 + 65plus`; `2+ = all`. Confirmed.
- **BR-SH-12.** Demos overlap, so a metric must never be summed across demos. Cube enforces this (8.3). Confirmed.

### 4.6 `dim_daypart`, `bridge_daypart_quarterhour`

Seed (P5) with two daypart sets:
- `WBD` (Early Fringe, Late Fringe, Prime, Sales Prime, Total Day, Weekday Daytime, Weekday Morning, Weekend Daytime).
- `NIELSEN` (Daytime M-F, Early Morning M-F, Fringe, Latenight, Overnight, Prime 8-11, Prime, Sales Prime, Total Day, Weekend Daytime, Weekend Early Morning).

Validate the boundaries against `marketshare_bronze.dimdaypart` (`smidaypart`, `nntvdaypart`, `matcheddaypart`, which already align Guideline and Nielsen dayparts). Columns: `daypart_key`, `daypart_set`, `daypart_name`, `days_of_week`, `start_time_et`, `end_time_et`, `sort_order`. The bridge maps each (day of week, quarter-hour) to every daypart it belongs to. Total Day = 06:00–05:59.

The custom per-network research and sales dayparts (Looker `icue_mit_custom_daypart`) are an optional `ref_custom_daypart` seed (doc 02, Decision).

### 4.7 `dim_viewing_stream` (TSV × data type)

Nielsen expresses commercial ratings as a combination of two columns, so the dimension is keyed on both: `time_shifted_viewing_type` (Live, Live+SD, Live+3, Live+7) and `nielsen_data_type` (program vs `ACM` average commercial minute).

| `stream_code` | `time_shifted_viewing_type` | `nielsen_data_type` | Used by |
| --- | --- | --- | --- |
| `LIVE` | Live | program value (To verify, e.g. `'Program'`) | NextGen |
| `LIVE_SD` | Live+SD | program value | NextGen (Top Titles, rankers) |
| `LIVE_3` | Live+3 | program value | NextGen (Exec Portfolio L+3) |
| `LIVE_7` | Live+7 | program value | NextGen |
| `C3` | Live+3 | `ACM` | Market Research (all C3 impressions), NextGen |
| `C7` | Live+7 | `ACM` | NextGen |

Columns: `stream_code` (PK), `time_shifted_viewing_type`, `nielsen_data_type`, `is_commercial`, `days_credited` (0, 0, 3, 7, 3, 7), `display_name` (Power BI `WM_TSV` "Data Stream"), `sort_order`. Validate against `marketshare_bronze.dimtimeshiftedviewing`.

Status: Confirmed (C3 = Live+3 + ACM, from the SQL); **To verify**: the exact non-ACM `nielsen_data_type` value(s) (`select distinct` on `big_mit_bronze.program_viewing`).

**Correction to earlier NextGen drafts:** `nielsen_data_type` is **not** the Panel vs Big Data methodology. Methodology is carried separately as `viewing_source` (5.2).

### 4.8 `dim_media_type`, `dim_advertiser_brand`

Owned by doc 01 (sourced from MarketShare).

## 5. Shared Nielsen MIT Silver (used by docs 02 and 03)

### 5.1 `research_silver.dim_telecast`

| Item | Specification |
| --- | --- |
| Grain | One row per `(viewing_source, acn_program_code, trackage_id, telecast_number)` |
| Primary key | `telecast_key = xxhash64(viewing_source || '|' || acn_program_code || '|' || trackage_id || '|' || telecast_number)` |
| Sources | `big_mit_bronze.program_descriptor` (+ `_serial`) → `viewing_source = 'BIG_MIT'`; `mit_panel_bronze.program_descriptor` → `'PANEL'` (doc 02) |
| Load | P2 MERGE |
| Dedupe | **BR-SH-13** below |

Columns: `telecast_key`, `viewing_source`, `acn_program_code`, `trackage_id`, `telecast_number`, `nielsen_network_id`, `network_label`, `network_key` (via BR-SH-05), `program_key` (to `dim_program_taxonomy`), `program_name`, `program_name_key`, `episode_id`, `episode_name`, `trackage_name`, `program_type_cd`, `program_subtype_cd` (strings), `nielsen_daypart`, `broadcast_date` (from `_broadcast_datesk`), `airing_ts` (`airing_datetime`), `broadcast_6_6_ts`, `duration_min`, and the flags `is_premiere`, `is_live`, `is_repeat`, `is_breakout`, `is_short_duration`, `is_special`, `is_movie`, `is_team_sports`, `is_preliminary`, `is_syndication`, `is_primary_feed_pattern`. Also `src_processid`, `descriptor_variant_count`, and the audit columns.

- **BR-SH-13 Descriptor dedupe.**
  - Big MIT: keep the row with the highest `processid`, then the latest `ingest_timestamp`.
  - Panel: keep the latest load; if a combination has more than one row, take the first by `program_type, program_subtype, program_name`, which reproduces the Research SQL.
  - Always write `descriptor_variant_count` and report combinations whose variants disagree on `program_type_cd` / `program_subtype_cd` (DQ-SH-05).
  - Status: Proposed. The Research SQL uses a different tie-break in each branch (Panel sorts by type, subtype, name; Big Data by type, name), which is not deterministic across sources.

### 5.2 `research_silver.fct_mit_telecast_viewing`

| Item | Specification |
| --- | --- |
| Grain | One row per `(viewing_source, acn_program_code, trackage_id, telecast_number, time_shifted_viewing_type, nielsen_data_type)` |
| Primary key | `telecast_key` + `stream_code` |
| Sources | `big_mit_bronze.program_viewing` (Big Data + Panel; from 2024-04-26); `mit_panel_bronze.program_viewing` (Panel Only; doc 02, Q-SH-03) |
| Partition | `months(broadcast_date)`, `identity(viewing_source)` |
| Load | P2 MERGE; reprocess a trailing 15-day window on every run (L+7 / C7 restatements) |
| Status | Proposed |

| Column group | Columns | Rule |
| --- | --- | --- |
| Keys | `telecast_key`, `stream_code`, `viewing_source`, `network_key`, `program_key`, `date_key` | BR-SH-05, 4.7 |
| Natural | `acn_program_code`, `trackage_id`, `telecast_number`, `time_shifted_viewing_type`, `nielsen_data_type`, `nielsen_network_id`, `network_label` | |
| Time | `broadcast_date`, `airing_ts`, `end_airing_ts` | BR-SH-01 |
| Durations | `duration_min` (`duration`), `commercial_program_duration_sec` (`commercial_program_duration`), `number_of_contributing_commercial_telecasts` | Units To verify (Q-SH-02) |
| Ratings | `average_audience`, `national_rating`, `national_share`, `national_hut`, `coverage_rating`, `coverage_share`, `coverage_hut`, `ue_nat`, `ue_cov` | as delivered |
| Demo cells (30) | `f2_5_delivery … f65plus_delivery`, `m2_5_delivery … m65plus_delivery` | Keep wide in Silver; Gold computes demos through `bridge_demo_cell` |
| Methodology | `viewing_methodology` (`Panel Only` / `Big Data + Panel`), `is_reporting_methodology` | BR-SH-14 |
| Lineage | `src_processid`, `src_gzfileid_demo`, audit columns | |

- **BR-SH-14 Methodology stitching.**
  - `is_reporting_methodology = (viewing_source = 'PANEL' and broadcast_date <= cutover_last_panel_date) or (viewing_source = 'BIG_MIT' and broadcast_date > cutover_last_panel_date)`.
  - `cutover_last_panel_date` lives in `research_silver.ref_pipeline_config` and defaults to **2025-09-28**, the last day of broadcast 2025 Q3.
  - The Marketplace Imps SQL uses Panel for broadcast quarters 2021 Q1–2025 Q3 and Big Data for every other quarter, which gives the same boundary. Overlap rows (2024-04-26 to 2025-12-31) are kept for comparison, with `is_reporting_methodology = false`.
  - Status: Confirmed by SQL; sign-off Q-SH-01.
- **BR-SH-15 Restatement.** Latest `processid` wins per natural key, and a final row replaces a preliminary one. Confirmed (Bronze has `processid`; `is_preliminary` is on the descriptor).

## 6. Reference and configuration tables (shared)

| Table | Grain | Source | Load | Owner |
| --- | --- | --- | --- | --- |
| `research_silver.ref_pipeline_config` | One row per key | Seed (P5) | Git-reviewed | CARL DE + Research |
| `research_silver.ref_event_program_map` | One row per (network_name, program_name) | Seed from the 1,765-row `EVENT_MAP_RAW` in the Marketplace Imps SQL (World Cup 920, Olympics 677, Super Bowl 168) | P5 | Research (Marketplace Insights) |

`ref_pipeline_config` initial keys:

| Key | Default | Used by | Status |
| --- | --- | --- | --- |
| `mit.cutover_last_panel_date` | 2025-09-28 | BR-SH-14 | Q-SH-01 |
| `mit.history_floor_date` | 2017-01-01 (Market Research), 2015-06-29 (MIT available) | doc 02 | Confirmed |
| `guideline.match_tolerance_min` | 5 | doc 02 BR-MR-06 | Decision |
| `guideline.bounce_depth` | 6 | doc 02 | Decision |
| `adintel.static_segment_end_date` | 2024-06-10 | doc 01 | To verify |
| `mi.media_types_in_scope` | `Cable TV, Network TV` | doc 02 (SQL filter) | Confirmed |

## 7. Data quality, freshness and alerting framework

### 7.1 Tables

`research_gold.ops_dq_results` (append, `days(run_ts)`, retained 2 years):

| Column | Type |
| --- | --- |
| `run_id` | string |
| `run_ts` | timestamp |
| `dag_id` | string |
| `layer` | string |
| `table_name` | string |
| `check_id` | string |
| `check_desc` | string |
| `severity` | `BLOCKER` / `WARN` / `INFO` |
| `status` | `PASS` / `FAIL` / `ERROR` |
| `observed_value` | double |
| `threshold` | string |
| `failed_row_count` | bigint |
| `sample_failed_keys` | string (JSON) |
| `partition_scope` | string |

`research_gold.ops_data_freshness` (MERGE on `source, layer, table_name`):
- Columns: `source`, `layer`, `table_name`, `last_source_delivery_ts`, `last_bronze_commit_ts`, `last_publish_ts`, `latest_complete_date` (per stream where relevant), `stream_code`, `expected_cadence`, `sla_hours`, `is_late`.
- It feeds every dashboard's "Last updated" tile, the NextGen `DATE_LAST_REFRESHED` / `DATA_AVAILABILITY`, and Cube pre-aggregation refresh keys.

### 7.2 Shared checks

| ID | Layer | Object | Check | Threshold | Severity |
| --- | --- | --- | --- | --- | --- |
| DQ-SH-01 | Bronze | `big_mit_bronze.*` | Freshness of last Prod commit | < 36 h | BLOCKER for Gold publish |
| DQ-SH-02 | Bronze | `marketshare_bronze.*` | Freshness | < 8 days | BLOCKER |
| DQ-SH-03 | Silver | `dim_broadcast_calendar` | Weeks per broadcast month ∈ {4,5}; 52/53 per year; BR-SH-01 tests; `broadcast_quarter_label` = DIMDATE `broadcastquarter` on every date | Exact | BLOCKER |
| DQ-SH-04 | Silver | `dim_program_taxonomy` | Unique on `(nielsen_network_id, acn_program_code)` for current rows | 0 duplicates | BLOCKER |
| DQ-SH-05 | Silver | `dim_telecast` | Descriptor variants disagreeing on type/subtype | Report count | WARN |
| DQ-SH-06 | Silver | `dim_network` | `mit_network_cd` unique among current rows; `mitnetworkid` and `mitnetworkcd` resolve the same SK | 0 | BLOCKER |
| DQ-SH-07 | Silver | `fct_mit_telecast_viewing` | Unique on PK | 0 duplicates | BLOCKER |
| DQ-SH-08 | Silver | `fct_mit_telecast_viewing` | Every reporting date has exactly one `is_reporting_methodology` source per network | 0 gaps / overlaps | BLOCKER |
| DQ-SH-09 | Silver | `fct_mit_telecast_viewing` | Cells ≥ 0; `commercial_program_duration_sec ≤ duration_min × 60` | 0 violations | BLOCKER |
| DQ-SH-10 | Silver | MIT facts → `dim_network` | Orphan `network_label` share of impressions | ≤ 0.5 % | BLOCKER; list orphans |
| DQ-SH-11 | Silver | MIT facts → `dim_telecast` | Viewing rows with no descriptor | ≤ 0.1 % | WARN |
| DQ-SH-12 | Silver | Row-count reconciliation | Silver vs Bronze per `broadcast_date × stream × source` | Exact after dedupe accounting | BLOCKER |
| DQ-SH-13 | Semantic | Cube | Golden queries return the same value from Cube and SQL on Gold | Exact | BLOCKER for Cube deploy |

### 7.3 Alerts

- **Routing.** Blocker failures and late deliveries go to SNS, then to Slack (one channel per objective: Marketplace Insights, NextGen Research, CARL DE).
- **Message content:** `check_id`, `table_name`, `partition_scope`, `observed_value` vs `threshold`, a link to the run.
- **Weekly audit.** A summary of `ops_dq_results` is sent every Thursday after the MarketShare refresh (Market Share PN-06).

## 8. Cube semantic layer conventions

### 8.1 Structure

- **Cubes and views.** One cube per Gold table (`research_gold.*`), named after the table without the prefix (e.g. `telecast_supply`). Cubes are private building blocks. **Views** are the public contract that Quick, Power BI and AI read: `marketplace_view_*`, `ngr_view_*`.
- **Shared dimension cubes** (`dim_network`, `dim_program`, `dim_broadcast_calendar`, `dim_demo`, `dim_daypart`, `dim_viewing_stream`, `dim_advertiser_brand`, `dim_media_type`) are defined once and joined `many_to_one` from facts on `*_key`.
- **Registry.** Every view is registered in `iceberg-catalog-agent/registry/cube_model.yaml` with status `proposed`, then `certified` after golden-query parity.

### 8.2 Measure metadata (required on every measure)

`title`, `description` (business definition), and `meta`:

```yaml
meta:
  kpi_class: primary | derived | supporting | quality | operational
  formula: "sum(gross_media_spend) / nullif(sum(gross_impressions_000), 0)"
  grain: "telecast x demo"
  additivity: additive | semi_additive | non_additive
  null_handling: "null spend treated as 0; null impressions excluded from denominator"
  legacy_names: ["WM_REACH_AND_FREQUENCY.Reach", "Looker vami3.gross_spend"]
  owner: "Marketplace Insights"
  source_rule: "BR-MR-04"
```

This satisfies PRD FR-16 (glossary mapping legacy names) and FR-18 (definition, formula, null handling, grain).

### 8.3 Modelling rules

- **CB-01 No sums of ratios.** Non-additive measures (reach, share, ratings, composition %, CPM, median) are built from additive numerator and denominator measures, then divided (`type: number`). Pre-computed reach in Gold is exposed only at the grain it was computed at (doc 03).
- **CB-02 Exactly one demo.** Views with demo-long facts reject queries without exactly one `demo_code` filter (`queryRewrite`). They also expose named convenience measures (e.g. `gross_impressions_p2554`) that carry a fixed demo filter.
- **CB-03 Share of X.** Use Cube multi-stage measures (`reduce_by: [dim_network.ownership_group]` or `[dim_network.network_name]`) so share is calculated within the user's filter context.
- **CB-04 Pre-aggregations.** Each view declares pre-aggregations for its dashboard queries. `refresh_key` is `select max(last_publish_ts) from research_gold.ops_data_freshness where table_name = '<table>'`. Partition pre-aggregations by `broadcast_month`.
- **CB-05 Access.** Row and column access is enforced in Cube `access_policy` / `queryRewrite` using the user's group claim. Restricted views (e.g. Ad Sales-facing Ad Intel) expose a curated subset only.
- **CB-06 Golden queries.** Each objective document lists 10 agreed questions. CI runs them against Cube and Athena and blocks the deploy on any difference (DQ-SH-13).

## 9. Orchestration

| DAG | Trigger | Steps |
| --- | --- | --- |
| `research_conformed_dims` | Airflow Dataset on `marketshare_bronze` and `big_mit_bronze.dimdate` updates; seeds on merge to main | calendar, network, program taxonomy, advertiser, demo, daypart, stream → DQ → publish `research_gold.dim_*` |
| `research_mit_silver` | Dataset on `landing_to_bronze_iceberg_bigmit` success (after the 19:30 UTC run) | `dim_telecast` → `fct_mit_telecast_viewing` (trailing 15 days) → DQ-SH-07..12 |
| `marketshare_gold` | after `research_conformed_dims` | doc 01 |
| `marketplace_insights_gold` | after `research_mit_silver` + Guideline manifest event | doc 02 |
| `nextgen_research_gold` | after `research_mit_silver`; NRLD on month close per stream | doc 03 |

- **Retries:** 3 retries with exponential backoff on every task.
- **On failure:** alert (section 7.3). The May 2026 MRI task failure was never retried (NFR-03).
- **Coupling:** no fixed-time coupling between DAGs. Use Airflow Datasets or sensors.

## 10. Shared open decisions

| ID | Decision | Owner | Default | Blocks |
| --- | --- | --- | --- | --- |
| Q-SH-01 | Confirm the Panel → Big MIT cutover: last Panel day 2025-09-28, matching the SQL's 2025 Q3 boundary | Eric Yarsinsky | 2025-09-28 | BR-SH-14 |
| Q-SH-02 | MIT `*_delivery` units (persons vs thousands) and `commercial_program_duration` units (seconds) | AMS BI / Nielsen docs | Validate on one telecast against Nielsen NTV View | Every impressions and CPM measure |
| Q-SH-03 | Panel Only history: one-time backfill from `AMS_ICUE_SHARE.MIT` (preferred) vs `marketshare_bronze.factprogram` | AMS BI (Hong Zhang, Sean Malek) + Research | **Decided 29-Oct:** backfill and freeze (epic CARL-4292); `factprogram` is the fallback and parity source | Docs 02, 03 |
| Q-SH-04 | Use one `research_silver` / `research_gold` pair instead of `marketplace_insights_*`, `measurement_*`, `studios_gold` | Ping Feng | Yes | Naming in all docs |
| Q-SH-05 | Iceberg branch (WAP) support in the CARL Glue version | CARL DE | Use branches; fall back to staging + swap | Section 2.5 |
| Q-SH-06 | Confirm the non-ACM `nielsen_data_type` value(s) | CARL DE (Athena query) | Profile Bronze | 4.7 |
| Q-SH-07 | Live verification of the six Snowflake objects used by the Marketplace Imps query (not yet done: the previous connection attempt was interrupted) | Daya Thakur / anyone with Snowflake read | Run the `SHOW TABLES` checks | Docs 02, 01 |
