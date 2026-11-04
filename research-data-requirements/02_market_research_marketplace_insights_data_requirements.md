# 02 – Market Research (Marketplace Insights / VAMI): Data Requirements

| Field | Value |
| --- | --- |
| Objective | Give Marketplace Insights one governed CARL source for **supply** (Nielsen C3 impressions, Panel Only then Big Data + Panel) and **demand** (Guideline Telecast and AccuTV spend), joined at telecast level. It replaces the Looker `VAMI 3` Explore, the Snowflake `MIT_ADINTEL_SMI_V3` table and the hand-run "Marketplace Imps" SQL |
| Consumers | Marketplace Insights analysts (Quick, Cube SQL API), AI agents through Cube, Research leadership decks |
| Jira | CARL-4113 (Guideline landing), CARL-4115, epic CARL-3775 |
| Depends on | `00_shared_foundation.md` (calendar, network, program taxonomy, `dim_telecast`, `fct_mit_telecast_viewing`, demo, DQ, Cube) and `01_marketshare_data_requirements.md` (taxonomy, advertiser, Ad Intel) |
| Status | DRAFT v0.1 – 29 Oct 2026 |

## Jira tracking

| Item | Jira |
| --- | --- |
| Guideline access + profiling (MR-01) | CARL-4113 |
| `guideline_bronze` landing, manifest, quarantine (MR-02) | CARL-4115 |
| `mit_panel_bronze` backfill (MR-03) | Epic CARL-4292, CARL-4294 |
| `big_mit_bronze.dimdate` + calendar (MR-04) | CARL-4395 |
| Crosswalk (MR-05) | CARL-4116 |
| Event map, program type/subtype, custom daypart seeds (MR-05) | CARL-4396 |
| Guideline Silver: spend, reject, bounce (MR-06) | CARL-4118 |
| Methodology stitching + breakout tie-break | CARL-4114 |
| Shared MIT Silver | CARL-4117 |
| Match bridge, supply, demand, `mi_fct_telecast_adintel` (MR-07, MR-08) | CARL-4120 |
| AccuTV `mi_fct_category_spend` | CARL-4119 |
| Cube `mi_view_*` (MR-09) | CARL-4121 |
| Marketplace Imps parity | CARL-4397 |
| VAMI 3 parallel run and Looker retirement (MR-10) | CARL-4398 |
| Discovery | CARL-3776 |

## 1. Scope

### 1.1 Priority 1: replace Looker Explore `VAMI 3` (model `iCUE Marketplace`, view `mit_adintel_smi_v2`)

The VAMI 3 measures and dimensions that survive are rebuilt as Cube views over Gold. The scope rules from Research are:

- **Prime measures (LookML rows 1184–1624) are not needed.** Do not rebuild the Prime-specific measure family. Prime remains available only as a daypart filter (`dim_daypart`, set `WBD`, value `Prime`) and a segment (BR-MR-12), so no measure code is duplicated per daypart.
- **All associated objects are needed except `dim_amrld_title_franchise` and `dim_bundle_map` / `icue_bundle_map`.** No title/franchise or bundle attributes are built (this closes the earlier questions Q-21 and Q-22).

| Looker object (VAMI 3 Explore) | Disposition | CARL target |
| --- | --- | --- |
| `mit_adintel_smi_v2` (base, telecast-level MIT + Ad Intel + SMI) | Rebuild | `mi_fct_telecast_supply` + `mi_fct_telecast_demand` + `mi_fct_telecast_adintel` → `mi_view_telecast_supply_demand` |
| `mvt_dimnetwork`, `dim_mktplc_network_v` | Replace | `research_gold.dim_network` |
| `mvt_dimnetworkprogramnamemapping` | Replace | `research_gold.dim_program_taxonomy` |
| `dim_mktplc_programtype_v` / `programsubtype_v` | Migrate as seed | `research_silver.ref_nielsen_program_type`, `ref_nielsen_program_subtype` (code → description) |
| `dim_adintel_common_dimdate` / `dimtime` | Replace | `dim_broadcast_calendar`, `dim_time_of_day` |
| `vami_reporting_networks` | Retire | `dim_network.is_reporting_network` + `is_guideline_measured` |
| `dim_advertiser_brand` (primary advertiser) | Replace | `research_gold.dim_advertiser_brand` (doc 01) via `mi_fct_telecast_adintel` (Q-MR-01) |
| `mit_premiere_telecasts` | Rebuild as segment | `dim_telecast.is_premiere` → Cube segment `premieres` |
| `icue_mit_custom_daypart` | Migrate | `ref_custom_daypart` seed → Cube dimension `custom_daypart` |
| `icue_vami3_demochart` | Rebuild as Cube pre-aggregation | Not persisted |
| `icue_vami3_bundlechart`, `icue_bundle_map` / `dim_bundle_map` | **Excluded** | none |
| `dim_amrld_title_franchise` (+ `dim_content`) | **Excluded** | none |
| `vami_validation` | Replace | `ops_dq_results` (DQ-MR-12) |

### 1.2 Priority 2: the "Marketplace Imps" query (A25-54 gross impressions by program and quarter)

This must be reproducible from Cube with no hand SQL (section 6.4).

### 1.3 Priority 3: AccuTV category spend (Pipeline 2) and spend "bounce" history

### 1.4 Out of scope

- Pathmatics.
- AMRLD content data.
- Bundles.
- CTV Ad Intel (reserve the media type only).
- Genesis / MarketShare 1.0 explores.

## 2. Sources and current state

| ID | Source | Location | In CARL | Cadence / history | Notes |
| --- | --- | --- | --- | --- | --- |
| S-MR-01 | Guideline Telecast | `s3://turner-ams-bi-marketshare-smi/DataOutgoing/US_SMI_Telecast_Data_201701_<YYYYMM>_<YYYYMMDD>.txt.gz` (account 689264014593; role `aws-ams-bi-marketshare-developer`) | No | Monthly, delivered 20th–31st, 3–4 weeks after month end. **Each file restates all history from 2017-01** | CARL-4113 names the wrong bucket; correct it |
| S-MR-02 | Guideline AccuTV | Same prefix, `SMI_US_AccuTV_<YYYYMMDD>_PSC.txt.gz` | No | As above | No data dictionary (Q-MR-05) |
| S-MR-03 | Nielsen MIT Panel Only | Snowflake `AMS_ICUE_SHARE.MIT.PROGRAM_VIEWING`, `PROGRAM_DESCRIPTOR` | No | Ended; 2015-06-29 → 2025-12-31 | One-time backfill to `mit_panel_bronze` (Q-SH-03) |
| S-MR-04 | Nielsen MIT Big Data + Panel | `SHARE_PROD_BIG_MIT.MIT` → `big_mit_bronze` | **Yes, Prod** | Daily; 2024-04-26 → | Reporting source from 2025-09-29 |
| S-MR-05 | Broadcast calendar | `SHARE_PROD_BIG_MIT.COMMON.DIMDATE` | No | Static | Add to the Big MIT pipeline (doc 00 4.1) |
| S-MR-06 | Network | `WBD_TED_AMS_SHARE_PROD_MARKETSHARE.MARKETSHARE.DIMNETWORK` → `marketshare_bronze.dimnetwork` | **Yes, Prod** | Weekly | |
| S-MR-07 | Taxonomy, Ad Intel | `marketshare_bronze`, taxonomy S3 | Partly | Weekly | doc 01 |
| S-MR-08 | Event program list | `EVENT_MAP_RAW` CTE in the Marketplace Imps SQL (1,765 rows) | No | Ad hoc | Seed `ref_event_program_map` (doc 00 6) |
| S-MR-09 | Parity baseline | Snowflake `ICUE_DATAMART.MARKETPLACE.MIT_ADINTEL_SMI_V3` (278 M rows; daily 08:00 ET) | No | Daily | Parallel-run comparison only, then retire |

The six Snowflake objects the Marketplace Imps query uses are S-MR-03 (two tables), the Big MIT `PROGRAM_VIEWING` and `PROGRAM_DESCRIPTOR`, `COMMON.DIMDATE`, and `MARKETSHARE.DIMNETWORK`. Their existence and columns have **not** been verified live yet (Q-SH-07). The Big MIT and MarketShare objects are proven indirectly because CARL Bronze copies them.

## 3. Bronze

### 3.1 `guideline_bronze`

**Access.** Phase 1: a cross-account read grant from bucket `turner-ams-bi-marketshare-smi` to the CARL Glue/MWAA role, with S3 replication or a copy to CARL landing. Phase 2: Guideline delivers straight to CARL landing (Q-MR-04).

| Table | Grain | Columns | Partition | Write |
| --- | --- | --- | --- | --- |
| `delivery_manifest` | One row per vendor file | `delivery_id` (`<product>_<delivered_yyyymmdd>`), `product` (`TELECAST`/`ACCUTV`), `file_name`, `s3_uri`, `file_size_bytes`, `file_md5`, `coverage_start_month`, `coverage_end_month` (parsed from the name), `delivered_date`, `row_count`, `schema_hash`, `contract_version`, `status` (`LANDED`/`QUARANTINED`/`SUPERSEDED`/`FINAL`), `is_final_for_cycle`, `cycle_month`, `ingest_timestamp` | none | Append + status MERGE |
| `telecast_delivery` | One row per source row per delivery | **All delivered columns as string** (pipe-delimited `.txt.gz`), plus `delivery_id`, `source_file`, `source_row_number`, `row_hash`, `ingest_timestamp` | `identity(delivery_id)` | Append (P1) |
| `accutv_delivery` | As above | As above | `identity(delivery_id)` | Append (P1) |
| `quarantine` | One row per rejected file | `file_name`, `reason`, `expected_schema_hash`, `actual_schema_hash`, `detected_ts` | none | Append |

Rules:
- **BR-MR-01 Schema contract.** Before writing Bronze, compare the header (names, order, count) with the registered contract `contract_version`. On a mismatch, write to `quarantine`, alert, and write nothing to Bronze. This fixes the silent Snowpipe failures.
- **BR-MR-02 Final delivery.** `is_final_for_cycle` = the last delivery received before the first delivery of the next cycle. Gold is built only from the latest final delivery (Q-MR-03). A re-delivery inside a cycle marks the earlier file `SUPERSEDED`.
- **Retention.** Keep all deliveries in the current cycle plus the last 6 final deliveries (`guideline.bounce_depth`). A housekeeping job drops older partitions; Iceberg `DELETE WHERE delivery_id IN (…)` followed by snapshot expiry.
- **Text handling.** Same as doc 01 TX-01..05: string schema, no inference, keep leading zeros (e.g. network codes, ISCI-like codes, `'00'` subtypes).

### 3.2 `mit_panel_bronze` (one-time backfill, then frozen)

| Table | Source | Columns | Partition |
| --- | --- | --- | --- |
| `program_viewing` | `AMS_ICUE_SHARE.MIT.PROGRAM_VIEWING`, 2015-06-29 → 2025-12-31 | Same column set as `big_mit_bronze.program_viewing` (natural key, ratings, the 30 `*_delivery` cells, `commercial_program_duration`, `_broadcast_datesk`, `network_label`) + `partition_id`, `source_file`, `ingest_timestamp` | `months(airing_datetime)` |
| `program_descriptor` | `AMS_ICUE_SHARE.MIT.PROGRAM_DESCRIPTOR` | Same as `big_mit_bronze.program_descriptor` | none |

- **Extraction.** Snowflake `COPY INTO @stage … FILE_FORMAT = (TYPE = PARQUET)` per broadcast month, then a Glue job writes Iceberg.
- **Validation.** Row counts and `sum(average_audience)` per month in Snowflake equal the counts in Bronze.
- **After sign-off.** Tag the table `panel_frozen_v1`. No further writes.

### 3.3 `big_mit_bronze` (exists) and the new `dimdate`

Covered in doc 00 4.1.

## 4. Silver (`research_silver`)

### 4.1 Shared tables used here (defined in doc 00)

`dim_telecast` and `fct_mit_telecast_viewing` (with `stream_code = 'C3'`, `is_reporting_methodology`), `dim_network`, `dim_program_taxonomy`, `dim_broadcast_calendar`, `dim_demo`, `bridge_demo_cell`, `dim_daypart`, `ref_event_program_map`, `ref_pipeline_config`.

### 4.2 `ref_network_crosswalk` (seed, replaces `XREF_NETWORK`)

| Column | Type | Rule |
| --- | --- | --- |
| `source_system` | string | `GUIDELINE_TELECAST`, `GUIDELINE_ACCUTV`, `ADINTEL` |
| `source_network` | string | As delivered, upper and trimmed |
| `network_key` | bigint | → `dim_network` |
| `mit_network_cd` | string | Denormalised for the match |
| `include_flag` | boolean | False = explicit exclusion (e.g. promo-only feeds) |
| `cardinality_note` | string | Required when one source network maps to more than one Nielsen network |
| `effective_from`, `effective_to` | date | |
| `owner`, `reviewed_by`, `review_date` | string, string, date | |

- **PK:** `(source_system, source_network, effective_from)`.
- **DQ-MR-04:** every Guideline network seen in the current final delivery is either mapped or explicitly excluded.

### 4.3 `fct_guideline_telecast_spend`

| Item | Specification |
| --- | --- |
| Grain | One row per Guideline telecast line in the **latest final** delivery: `guideline_network × program_start_ts (minute) × buy_type × adu × spot_length × media_subtype` |
| PK | `guideline_line_key = xxhash64(delivery_id || natural key)` |
| Source | `guideline_bronze.telecast_delivery` where `delivery_id = latest final` |
| Partition | `months(broadcast_date)` |
| Write | Full overwrite per new final delivery; snapshot tagged `guideline_<cycle_month>_final` |

Columns:
- `delivery_id`, `guideline_network`, `network_key` (via crosswalk), `broadcast_date`, `program_start_ts`, `program_start_minute_key`, `program_name_guideline`.
- `buy_type` (`Upfront`, `Scatter/Other`, `Direct Response`), `adu`, `promo_type`, `spot_length_sec`, `media_subtype`, `daypart_guideline`.
- `gross_media_spend_usd decimal(18,2)`, `spot_count`, `eq30_spot_count decimal(18,4)`, plus the audit columns.
- Final column names come from the Telecast header once the file is landed (Q-MR-05).

Rules:
- **BR-MR-03 Non-promo.** Keep `promo_type = 'Non-Promo'`; drop `adu = 'Promo'`. Confirmed (VAMI `custom_smi2`).
- **BR-MR-04 Concurrent duplicates.** Per `(network_key, program_start_minute_key)`, keep the line with the highest gross spend for each `(buy_type, adu, spot_length)` group. The other lines go to `fct_guideline_reject` with reason `CONCURRENT_DUPLICATE`. Confirmed (VAMI `custom_smi2`), plus a reject table.
- **BR-MR-05 History floor.** `broadcast_date >= 2017-01-01`.

### 4.4 `fct_guideline_reject`

Grain: one row per rejected Guideline line. Columns: `delivery_id`, `guideline_line_key`, `reason` (`CONCURRENT_DUPLICATE`, `UNMAPPED_NETWORK`, `NO_TELECAST_MATCH`, `PROMO`, `PRE_HISTORY`), `gross_media_spend_usd`, `detail`. Spend must be conserved (DQ-MR-06).

### 4.5 `fct_guideline_spend_bounce`

| Item | Specification |
| --- | --- |
| Grain | `delivery_id × network_key × broadcast_month_key × buy_type` for the last N final deliveries |
| Columns | `gross_media_spend_usd`, `eq30_spot_count`, `delivery_rank` (1 = latest), `delta_vs_previous_usd`, `delta_vs_previous_pct` |
| Write | Append one delivery per final delivery; drop rank > N |
| Why | Analysts need to see how estimates move ("bounce"). Quick cannot time-travel, so the history is a table |

### 4.6 `match_telecast_guideline_mit` (the telecast bridge)

| Item | Specification |
| --- | --- |
| Grain | One row per Guideline telecast `(network_key, program_start_minute_key)` in the current final delivery |
| Columns | `guideline_telecast_key`, `network_key`, `broadcast_date`, `program_start_ts`, `telecast_key` (null when not matched), `match_offset_min`, `match_rank`, `match_status` (`MATCHED`, `NO_CANDIDATE`, `NETWORK_UNMAPPED`), `candidate_count`, `matched_viewing_source` |
| Source | `fct_guideline_telecast_spend` × `dim_telecast` / `fct_mit_telecast_viewing` (C3, `is_reporting_methodology`) × `ref_network_crosswalk` |
| Write | Rebuild the affected months when either side changes |

- **BR-MR-06 Telecast match.**
  - Candidates: same `network_key`, same `broadcast_date`, and `abs(airing_ts - program_start_ts) <= guideline.match_tolerance_min` (default 5).
  - Choose the smallest offset. Ties go to the breakout airing first (VAMI `custom_mit2` code; Q-MR-02), then to non-short-duration airings, then to the lowest `telecast_number`.
  - Status: Decision for the tolerance and tie-break (Q-MR-02, Q-MR-06).
- **BR-MR-07 No fan-out.** Each Guideline telecast matches at most one Nielsen telecast. A Nielsen telecast may receive several Guideline telecasts.

### 4.7 `fct_guideline_accutv_spend`

The latest final AccuTV delivery at delivered grain, with `network_key`, `date_key`, category / subcategory, `buy_type`, `adu`, `daypart`, `promo_type`, `gross_media_spend_usd`, `eq30_spot_count`, `spot_length_sec`. The full grain and natural key come from profiling the first landed file (Q-MR-05). Partition `months(air_date)`; overwrite per final delivery.

### 4.8 Seeds

- `ref_nielsen_program_type`: `program_type_cd`, `program_type_desc`.
- `ref_nielsen_program_subtype`: `program_subtype_cd`, `program_subtype_desc`, `parent_type_cd`.

  Both are exported once from the Looker views and keep leading zeros.
- `ref_custom_daypart`: `network_key`, `daypart_name`, `daypart_type` (`RESEARCH`/`SALES`), `days_of_week`, `start_time_et`, `end_time_et`, `effective_from`, `effective_to`.

## 5. Gold (`research_gold`)

Supply and demand are separate facts that share `telecast_key`. Impressions therefore never repeat across buy-type rows and cannot be over-summed.

### 5.1 `mi_fct_telecast_supply`

| Item | Specification |
| --- | --- |
| Grain | One row per **reporting** Nielsen telecast × `demo_code` (C3, long format) |
| PK | `telecast_key, demo_code` |
| Source | `fct_mit_telecast_viewing` (`stream_code = 'C3'`, `is_reporting_methodology = true`, `broadcast_date >= 2017-01-01`) × `bridge_demo_cell` |
| Partition | `months(broadcast_date)` |
| Write | P3 rebuild of the affected months, then WAP |

| Column | Type | Rule |
| --- | --- | --- |
| `telecast_key`, `demo_code`, `network_key`, `program_key`, `date_key`, `daypart_key` | | Keys |
| `broadcast_date`, `airing_ts`, `hour_of_day` | | |
| `viewing_source`, `viewing_methodology` | string | `PANEL` / `BIG_MIT`; `Panel Only` / `Big Data + Panel` |
| `demo_audience` | double | `sum(cells in demo)` (BR-SH-11) |
| `gross_impressions` | double | **BR-MR-08:** `(commercial_program_duration_sec / 30) × demo_audience` |
| `gross_impressions_000` | double | Scaled per Q-SH-02 |
| `average_audience`, `duration_min`, `commercial_program_duration_sec` | | Weighted-average inputs |
| `nielsen_genre_simple`, `event_name`, `program_group_summary`, `program_group_detail` | string | Denormalised for pre-aggregation speed (doc 00 BR-SH-07..10) |
| `media_type_desc`, `ownership_group`, `network_name`, `is_reporting_network` | string / boolean | Denormalised |
| `is_premiere`, `is_breakout`, `is_live`, `is_wbd_prime`, `is_wbd_mirror` | boolean | **BR-MR-12:** `is_wbd_prime` = airing hour 20–23; `is_wbd_mirror` = 0–3 |

Demos materialised: the 18 broad demos plus `P55-64`. Any other demo is computed in Cube from a Silver cell-level view (Q-MR-07).

### 5.2 `mi_fct_telecast_demand`

| Item | Specification |
| --- | --- |
| Grain | One row per matched telecast × `buy_type × adu × spot_length_sec × media_subtype`, plus unmatched rows with `telecast_key = null` |
| Columns | `telecast_key`, `network_key`, `date_key`, `buy_type`, `adu`, `spot_length_sec`, `media_subtype`, `gross_media_spend_usd`, `upfront_spend_usd`, `scatter_other_spend_usd`, `dr_spend_usd`, `spot_count`, `eq30_spot_count`, `match_status`, `match_offset_min`, `delivery_id` |
| Rule | **BR-MR-09 Buy-type split:** each spend column is filtered on its `buy_type` value. Guideline's "Direct Response" differs from the internal DR definition; document this in the measure description |

### 5.3 `mi_fct_telecast_adintel` (primary advertiser per telecast; scope Q-MR-01)

| Item | Specification |
| --- | --- |
| Grain | `telecast_key × primary_advertiser_brand_key` |
| Columns | `ad_units`, `ad_eq30_units`, `ad_est_spend_usd`, `is_primary_advertiser` |
| Build | Aggregate `fct_adintel_occurrence` to `(network_key, date_key, airing window)` **before** joining to the telecast (**BR-MR-10:** never join occurrences to telecast rows unaggregated) |

This preserves VAMI 3's advertiser dimension without multiplying impressions.

### 5.4 `mi_fct_category_spend` (AccuTV)

AccuTV grain from 4.7 with conformed keys. Partition `months(broadcast_date)`; WAP.

### 5.5 `mi_agg_program_quarter_imps` (Marketplace Imps output; optional materialisation)

| Item | Specification |
| --- | --- |
| Grain | `viewing_source × network_name × ownership_group × media_type_desc × nielsen_genre_simple × event_name × is_reporting_network × program_type_cd × program_subtype_cd × program_name × broadcast_quarter_label × broadcast_year` |
| Measure | `a25_54_gross_imps` |
| Filters | `media_type_desc in ('Cable TV','Network TV')` (`mi.media_types_in_scope`), C3, reporting methodology |
| Preferred delivery | A Cube **pre-aggregation** on `mi_view_telecast_supply_demand`. Materialise as a table only if Quick needs a flat extract |

## 6. Business rules: Marketplace Imps parity

### 6.1 Rule mapping (SQL → CARL)

| SQL element | CARL rule |
| --- | --- |
| `TIME_SHIFTED_VIEWING_TYPE = 'Live+3' AND NIELSEN_DATA_TYPE = 'ACM'` | `stream_code = 'C3'` (doc 00 4.7) |
| Panel for `broadcastquarter IN ('2021 Q1' … '2025 Q3')`, Big for `NOT IN` | `is_reporting_methodology` with cutover 2025-09-28 (BR-SH-14). The SQL lower bound of 2021 Q1 is a query choice, so apply it as a Cube filter, not a data rule |
| `QUALIFY ROW_NUMBER() … ORDER BY PROGRAM_TYPE, PROGRAM_SUBTYPE, program_name` (Panel) / `PROGRAM_TYPE, program_name` (Big) | `dim_telecast` dedupe BR-SH-13 (one deterministic rule for both sources) |
| `JOIN DIMDATE ON _broadcast_datesk = datesk` | `date_key` → `dim_broadcast_calendar` |
| `JOIN DIMNETWORK ON network_label = mitnetworkcd` | `network_key` via BR-SH-05 |
| `CASE PROGRAM_TYPE …` genre | `nielsen_genre_simple` (BR-SH-07) |
| `EVENT_MAP` + subtype fallback | `event_name` (BR-SH-08, BR-SH-09) |
| `SUM((COMMERCIAL_PROGRAM_DURATION/30) * (M25_29..M50_54 + F25_29..F50_54))` | `gross_impressions` for `demo_code = 'P25-54'` (BR-MR-08) |
| `MEDIATYPEDESCRIPTION IN ('Cable TV','Network TV')` | `dim_network.media_type_desc` filter |
| `UNION ALL` of the two branches with `DATA_SOURCE` | `viewing_source` dimension |

### 6.2 Known differences to sign off

- **D-01.** The SQL's Big Data branch orders by `PROGRAM_TYPE, program_name` and the Panel branch by `PROGRAM_TYPE, PROGRAM_SUBTYPE, program_name`. CARL uses one rule. Expect small differences in the program-type split on multi-descriptor telecasts. Report the count (DQ-SH-05).
- **D-02.** The SQL takes the Big branch for quarters *outside* 2021 Q1–2025 Q3, which includes pre-2021 quarters where Big MIT has no data. CARL makes the boundary explicit.
- **D-03.** The SQL event match uses `UPPER(TRIM(d.network))` against the map's network. CARL uses `dim_network.network_name` (continuous), so rebranded networks still match.

### 6.3 Athena parity query (acceptance test)

```sql
SELECT s.viewing_source AS data_source,
       n.network_name   AS network,
       n.ownership_group,
       n.media_type_desc,
       s.nielsen_genre_simple AS genre,
       s.event_name     AS event,
       n.is_reporting_network AS reportingstatus,
       p.program_type_cd, p.program_subtype_cd, p.program_name,
       c.broadcast_quarter_label AS broadcastquarter,
       c.broadcast_year,
       SUM(s.gross_impressions) AS "A25-54 Gross Imps"
FROM research_gold.mi_fct_telecast_supply s
JOIN research_gold.dim_network n
  ON s.network_key = n.network_key AND n.is_current
JOIN research_gold.dim_program_taxonomy p
  ON s.program_key = p.program_key AND p.is_current
JOIN research_gold.dim_broadcast_calendar c
  ON s.date_key = c.date_key
WHERE s.demo_code = 'P25-54'
  AND n.media_type_desc IN ('Cable TV', 'Network TV')
  AND c.broadcast_quarter_key >= 20211
GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12;
```

Acceptance: compared with the Snowflake SQL, the totals by `network × broadcast_quarter` agree within ±0.5 %, and every row outside tolerance is explained by D-01, D-02 or D-03.

### 6.4 Cube equivalent

Query `mi_view_telecast_supply_demand` with measure `gross_impressions`, filter `demo_code = 'P25-54'`, and the dimensions listed in 5.5. Provide the pre-aggregation `marketplace_imps_quarterly`.

## 7. Cube

### 7.1 `mi_view_telecast_supply_demand` (VAMI 3 replacement)

**Measures (Prime family excluded):**

| Measure | Definition | Type |
| --- | --- | --- |
| `gross_impressions` | `sum(gross_impressions)`; requires exactly one demo (CB-02) | additive within a demo |
| `gross_impressions_p2554`, `_p1849`, `_p2plus`, `_w2554`, `_m2554` | Fixed-demo convenience measures | additive |
| `gross_impressions_per_bc_week` | `gross_impressions / count(distinct broadcast_week_key)` | ratio |
| `gross_spend` | `sum(gross_media_spend_usd)` | additive |
| `upfront_spend`, `scatter_other_spend`, `dr_spend` | BR-MR-09 | additive |
| `gross_spend_per_bc_week` | ratio | ratio |
| `eq30_spot_count`, `spot_count` | sum | additive |
| `commercial_duration_sec`, `program_duration_min`, `telecast_count` (count distinct `telecast_key`) | supporting | |
| `average_audience` | `sum(average_audience × duration_min) / sum(duration_min)` | non-additive |
| `cpm` | `gross_spend / nullif(gross_impressions_000, 0)` | non-additive |
| `share_of_spend`, `share_of_impressions` | multi-stage, `reduce_by` ownership or network (CB-03) | non-additive |
| `power_ratio` | `share_of_spend / nullif(share_of_impressions, 0)` | non-additive |
| `match_rate` | matched spend / total non-promo spend | quality |
| `adintel_est_spend`, `adintel_units` | from `mi_fct_telecast_adintel` (Q-MR-01) | additive |

**Dimensions:**
- Network: ownership group, network (continuous), network code as aired, network group / type / division, media type, `is_wbd`.
- Program: program name, Nielsen program type / subtype (code and description), Programming Genre (`nielsen_genre_simple`), Program Group Summary / Detail, event.
- Telecast: telecast, episode, airing time, hour.
- Daypart: Nielsen, WBD and custom.
- Spend: buy type, ADU, spot length, media subtype.
- Other: demo, viewing methodology / source, primary advertiser parent / brand / category, broadcast and Gregorian calendar.

**Segments:** `wbd_only`, `reporting_networks`, `wbd_prime`, `wbd_mirror`, `premieres`, `panel_only`, `big_data_panel`, `matched_only`, `events_only`, `excluding_events`.

**Pre-aggregations:**
- `monthly_network_demo`: network × broadcast month × demo × methodology.
- `marketplace_imps_quarterly`.
- `demo_chart`: replaces `icue_vami3_demochart`.

### 7.2 `mi_view_category_spend` (AccuTV)

- **Measures:** `gross_media_spend`, `gross_spend_per_bc_week`, `eq30_spot_count`, `share_of_spend`.
- **Dimensions:** media parent owner, ownership group, network, media subtype, category group / category / subcategory, buy type, ADU, daypart, promo type, calendar.

### 7.3 `mi_view_spend_bounce`

- **Measures:** `spend_by_delivery`, `delta_vs_previous_pct`.
- **Dimensions:** delivery, network, broadcast month, buy type.

### 7.4 Golden queries (parity tests)

1. WBD share of C3 P25-54 impressions, Q2 2025.
2. A25-54 gross impressions by network and quarter (Marketplace Imps), 2024 Q1–2026 Q2.
3. Gross spend by buy type for TNT, Sep 2025.
4. CPM P25-54 by ownership group, 2025.
5. Match rate by network, latest month.
6. World Cup impressions by network, 2026 Q2.
7. Power ratio, WBD vs NBCU, 2025.
8. Premieres count on HGTV, 2025 Q3.
9. AccuTV spend by category, Aug 2026.
10. Bounce: spend change for Jul 2026 across the last 3 deliveries.

Each must equal the Gold SQL exactly, and be within ±3 % of VAMI 3 / `MIT_ADINTEL_SMI_V3` for 2023–2025 (DQ-MR-11), with every gap explained.

## 8. Data quality

| ID | Layer | Check | Threshold | Severity |
| --- | --- | --- | --- | --- |
| DQ-MR-01 | Landing | Guideline delivery arrival | Alert if none by the 5th of the next month | WARN |
| DQ-MR-02 | Landing | Schema contract (BR-MR-01) | Exact | BLOCKER (quarantine) |
| DQ-MR-03 | Bronze | File-name coverage = `max(month)` in file; row count vs previous final ±5 % for overlapping months; exactly one new month | as stated | BLOCKER / WARN |
| DQ-MR-04 | Silver | Crosswalk coverage (4.2) | 100 % mapped or excluded | BLOCKER |
| DQ-MR-05 | Silver | Concurrent duplicates handled | Reject table populated; spend conserved | BLOCKER |
| DQ-MR-06 | Gold | Spend conservation: Gold demand + rejects = Silver non-promo spend | Exact | BLOCKER |
| DQ-MR-07 | Silver | Match rate by network-month | Baseline from parity; alert on a drop > 2 points | WARN |
| DQ-MR-08 | Silver | Bounce > 10 % for months older than 3 | Report | WARN |
| DQ-MR-09 | Gold | `P = W + M` for every broad demo in `mi_fct_telecast_supply` | 0 violations | BLOCKER |
| DQ-MR-10 | Gold | Panel vs Big overlap difference by network-month (2024-04-26 → 2025-12-31) | Report | INFO |
| DQ-MR-11 | Gold | Parity vs `MIT_ADINTEL_SMI_V3` and the Marketplace Imps SQL | ±3 % (VAMI), ±0.5 % (Imps) | BLOCKER for go-live |
| DQ-MR-12 | Gold | Vendor UI reconciliation (Apollo DataMiner, Nielsen NTV View) on 10 fixed network-months | ±3 % | BLOCKER for sign-off |
| DQ-MR-13 | Gold | Event coverage: every `ref_event_program_map` row matches at least one telecast in its event window | Report unmatched | WARN |
| DQ-MR-14 | Gold | Taxonomy coverage: impressions on `is_unmapped` programs | < 1 % | WARN |

## 9. Orchestration

| DAG | Trigger | Steps |
| --- | --- | --- |
| `guideline_landing` | S3 event on `DataOutgoing/` (or replicated prefix) + daily poll | detect → manifest → contract check → Bronze append → mark final / superseded → DQ-MR-01..03 |
| `mit_panel_backfill` | Manual, once | export per month → Bronze → reconcile → tag `panel_frozen_v1` |
| `marketplace_insights_gold` | Dataset: `research_mit_silver` success **or** new final Guideline delivery | Guideline Silver (4.3–4.5) → match bridge (4.6) → Gold 5.1–5.5 (affected months) → DQ → WAP → Cube refresh |
| `accutv_gold` | New final AccuTV delivery | 4.7 → 5.4 → DQ → WAP |

## 10. Open decisions

| ID | Question | Owner | Default |
| --- | --- | --- | --- |
| Q-MR-01 | Does the VAMI 3 replacement need advertiser (primary Ad Intel brand per telecast)? Research said "all associated objects", which includes `dim_advertiser_brand` | Eric Yarsinsky / Maggie Mullane | **Yes**, via `mi_fct_telecast_adintel` (5.3) |
| Q-MR-02 | Breakout tie-break: the code ranks breakout first, the doc says non-breakout | Eric Yarsinsky | Follow the code |
| Q-MR-03 | Bounce depth (3 or 6) and the definition of "final" | Eric Yarsinsky | 6; last file before the next cycle's first |
| Q-MR-04 | Guideline access: cross-account grant vs vendor redirect to CARL landing | AMS BI + CARL DE | Grant first |
| Q-MR-05 | Telecast and AccuTV file layouts (no dictionary) | Research + Guideline | Profile the first landed file; register contract v1 |
| Q-MR-06 | Match tolerance ±3 or ±5 minutes | Eric Yarsinsky | ±5, smallest offset |
| Q-MR-07 | Demo list beyond the 18 broad demos + P55-64 | Research | Cell-level Silver view for ad hoc demos |
| Q-MR-08 | Which LookML fields (outside the Prime rows 1184–1624) must survive with legacy names | Research | Export the field list; map each to a Cube member (`legacy_names`) |

## 11. Backlog (proposed Jira stories)

| Story | Summary | Depends on |
| --- | --- | --- |
| MR-01 | Correct CARL-4113 bucket path; Guideline cross-account read | Q-MR-04 |
| MR-02 | `guideline_bronze` landing + manifest + contract + quarantine | MR-01 |
| MR-03 | `mit_panel_bronze` one-time backfill + reconciliation | Q-SH-03 |
| MR-04 | `big_mit_bronze.dimdate` + `dim_broadcast_calendar` | doc 00 |
| MR-05 | `ref_network_crosswalk`, `ref_event_program_map`, program type/subtype and custom daypart seeds | MR-02 |
| MR-06 | Guideline Silver: current-final spend, reject, bounce | MR-02, Q-MR-03 |
| MR-07 | Telecast match bridge | MR-05, MR-06, doc 00 MIT Silver |
| MR-08 | Gold supply / demand / adintel / category spend + WAP | MR-07 |
| MR-09 | Cube `mi_view_*` + pre-aggregations + golden queries | MR-08 |
| MR-10 | Parallel run vs VAMI 3 and the Marketplace Imps SQL; retire the Looker Explore | MR-09 |
