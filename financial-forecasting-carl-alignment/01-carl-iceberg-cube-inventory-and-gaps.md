# 01 — What exists in CARL today (Iceberg and Cube) and what is missing

Scope: the Financial Forecasting pipeline described in the 16–20 Oct thread. As-of dates and limits are in the [README](README.md).

## 1. Pipeline as described by the DF team

```
Snowflake share views (SHARE_PROD_ADS_ENGAGEMENT.GOLD, 11 source objects)
        │
        ▼
Databricks job DF_Run_Finance_Forecast_Capacity   (daily 08:00 ET; Terraform: foresite_digital/finance_forecast_capacity.tf;
        │                                          notebook: data_engineering/finance_forecast_capacity.ipynb)
        ├─ SP_LOAD_CAPACITY_HISTORY_FINANCE → CAPACITY_HISTORY_FINANCE   (INCREMENTAL, days_back=7, delete + insert in one transaction)
        └─ SP_LOAD_CAP_FIN_FORECAST         → CAPACITY_FORECAST_FINANCE  (full truncate + rebuild daily: actuals + 365-day forecast)
        │
        ▼
Snowflake-managed Iceberg  (EXT_VOL_DF_ICEBERG_<ENV>_SILVER/GOLD → s3://digital-forecasting-{silver|gold}-us-east-1-{dev|qa}/snowflake/iceberg/df_{silver|gold}; CATALOG='SNOWFLAKE')
        │
        ▼
DF_GOLD views: CAPACITY_FORECAST_FINANCE_ENT, VW_STREAMING_SPORTS_CAPACITY_ACTUALS_FINANCE  ──►  QuickSight dashboards (direct, no Athena, no Cube)
```

Not in the CARL Glue catalog: all DF Iceberg tables and DF_GOLD views.

## 2. CARL Iceberg — estate relevant to this pipeline

Total estate: 1,128 tables across 36 databases (24 Sep snapshot).

| Database | Layer | Tables | Dev | Prod | Notes |
|---|---|---|---|---|---|
| `freewheel_bronze` | Bronze | 77 (79 on 7 Oct) | Yes | **No** | 64 log tables done 1 Jul (CARL-746). Prod S3 landing exists; prod Glue not registered. Source retains only 7 days. |
| `freewheel_silver` | Silver | 20 | Yes | **No** | Phase 1: 1 fact (`fact_ad_stream_impression`, 137 cols) + 18 dims. Target 15 Dec (CARL-2887). |
| `freewheel_gold` | Gold | 1 (`rpt_reach_frequency_daily`) | Yes | No | Not relevant to the forecast. |
| `operative_bronze` | Bronze | 81 | Yes | **Yes** | All 4 environments, refreshed every 30 min 06:00–22:00 ET. 1,541 of 1,541 business columns typed `string`; 15 malformed column names across 9 tables (CARL-3509). |
| `operative1_bronze` | Bronze | 7 (8 on 7 Oct) | Yes | Yes | Targeting and map tables. |
| Operative One Silver / Gold | — | **0** | — | — | CARL-2888 To Do; 3 child stories unassigned. |
| `linear_digital_revenue_*` | Bronze 176 / Silver 156 / Gold 24 | — | Yes | Mostly | Gold has 3 certified products: pacing/budget, combined revenue + sales holes, sales teams. |
| `ddl_forecasting_*`, `linear_forecasting_silver` | Bronze/Silver | 1 and 4–6 | Yes | `ddl_*` only | DDL and Linear forecasting, not Finance. |
| `neo_*` | Bronze 12 / Silver 7 / Gold 7 | — | Yes | **No** | FreeWheel-derived NEO reporting. |

## 3. CARL Cube — views relevant to this pipeline

| Cube view | Base | Relevance |
|---|---|---|
| `finance_view_pacing_revenue_budget`, `finance_view_combined_revenue`, `finance_view_dim_teams` | `linear_digital_revenue_gold` | Finance views, but linear/digital **booked revenue**, not capacity forecast |
| `finance_view_inventory_fact`, `finance_view_invoice_revenue_fact`, `finance_view_projected_working_revenue_fact` | Lumos DWH gold | Linear ad sales finance; not this pipeline |
| 8 × `ad_sales_view_neo_*` | `neo_gold` | FreeWheel-derived delivery reports; not a revenue-by-video-asset model |
| `ad_sales_view_op_digital_orders` | `operative_bronze.sales_order_line_items` | Only Operative view; Bronze base |
| **Finance capacity forecast** | — | **No Cube view exists** |

Proposed Cube views in the registry (Ad Products, Market Share) are unrelated to this pipeline.

## 4. The 11 source objects against CARL

Numbering follows the thread (objects 2–10 are the FreeWheel and Operative lookups). Matching of names is **inferred from table names**; column-level validation is story FF-01.

Legend: ✅ exists in prod Glue · 🟡 exists, Bronze only and/or dev only · ❌ no CARL equivalent

| # | Source object | Best CARL candidate | Status | Notes and evidence |
|---|---|---|---|---|
| 1 | `FW_REV_VIDEOASSET_DY_SELLABLE_V` (main fact) | none | ❌ | Gerry-side curated table; "informational only" in the earlier DF dump. FreeWheel Silver Phase 1 fact is **impression grain** from `v4_logs`; it does not carry revenue by video asset by day or the sellable logic. |
| 2 | `VIDEO_AD_SITE_GROUP_V` | `freewheel_bronze.d_site_group`, `d_site_to_site_group` | 🟡 | Both are **not read in FreeWheel Silver Phase 1** (Table Catalog, 55 of 77 Bronze tables excluded). Dev only. |
| 3 | `SITE_GROUP_TO_SITE_GROUP_V` | `freewheel_bronze.d_site_group_to_site_group` | 🟡 | As above. |
| 4 | `SITE_SECTION_TO_SITE_GROUP_V` | `freewheel_bronze.d_site_section_to_site_group` | 🟡 | As above. `dim_site_section` exists in Silver but without the group mapping. |
| 5 | `VIDEO_ASSET_MASTER_V` | `freewheel_silver.dim_video`, `dim_video_series`; Bronze `d_video`, `d_video_group`, `d_video_to_video_group` | 🟡 | `dim_video` is in Phase 1 (CARL-3807). Video-group tables are **not** in Phase 1. CARL-4222 will add rating and air_date to `d_video` (To Do). API video data is a candidate for duration and rating. Dev only. |
| 6 | `LISTINGS_V` | `freewheel_bronze.d_listings` | 🟡 | Not in Phase 1: the fact keeps only `listing_id`. Dev only. |
| 7 | `API_PLACEMENTS_V` | `freewheel_silver.dim_placement` (log-based); FreeWheel **API** Bronze (CARL-1380) | 🟡 | The "API" in the name suggests the API feed, which is in testing and not in the 77-table log set. Unconfirmed. |
| 8 | `FW_VIDTYPE_MAP` | none | ❌ | No CARL table identified. |
| 9 | `OM_CON_DY_V` | inputs in `operative_bronze` (`sales_order_line_items`, `sales_order`, `currency_exchange_rate`, `sales_line_item_booked_delivered`) | ❌ (view) / ✅ (inputs) | The view is logic in the Looker ETL for the Op1 contracted snapshot (line-day expansion + currency + pacing). No standalone Iceberg table. CARL-3509 notes the DF consumer already hit `source` column absence here. |
| 10 | `OPERATIVE_SALES_ORDER_CUSTOM_FIELD_V` | `operative_bronze.sales_order_custom_field`, `sales_order_line_item_custom_field` | ✅ (Bronze) | In all 4 environments. All columns are strings; custom-field IDs and values need typing and mapping. |
| 11 | `EXCEL_SHEETS_V` (Looker Excel snapshot maps) | none | ❌ | No governed source. Gerry owns the maps. |

Additional DF-side objects named in the thread:

| Object | CARL status | Notes |
|---|---|---|
| `RESELLER_TYPE_MAP`, `SITE_SECTION_NETWORK_LDCI_MAP`, `BRAND_GROUP_STANDARD_NAME_MAPPING` | ❌ | DF-owned tables in `DF_SILVER`. CARL-4222 folds `d_reseller` into `dim_network`; check overlap with `RESELLER_TYPE_MAP`. |
| `VW_PORTFOLIO_FORECASTING_FORECAST` (ML forecast) | ❌ | One-time dump to `cmp_test`; no recurring prod feed. Owner: Ankit. |
| `CAPACITY_HISTORY_FINANCE`, `CAPACITY_FORECAST_FINANCE`, DF_GOLD views | Not in CARL | Snowflake-managed; own S3 buckets; QuickSight reads Gold directly. |

### Score

| Result | Count | Objects |
|---|---|---|
| Prod CARL table exists (Bronze) | 1 | 10 |
| Bronze candidates, dev only | 5 | 2, 3, 4, 5, 6 |
| Unconfirmed (depends on whether the source is the log feed or the API feed) | 1 | 7 |
| No CARL table (object 9 has logic only; its inputs exist in prod Bronze) | 4 | 1, 8, 9, 11 |
| **Total** | **11** | |

## 5. Gaps (what is missing)

| # | Gap | Impact | Story |
|---|---|---|---|
| G1 | FreeWheel not registered in prod Glue (Bronze and Silver are dev only) | Nothing FreeWheel-based can be prod-ready in CARL | FF-09 |
| G2 | Site-group, video-group and listings tables are Bronze only; excluded from Silver Phase 1 | Lookups would read Bronze directly or wait for Silver Phase 1.1 | FF-03 |
| G3 | No CARL fact for revenue by video asset by day (sellable) | The core forecast input has no CARL home | FF-04, FF-05 |
| G4 | `FW_VIDTYPE_MAP` has no CARL table | Video-type classification cannot be reproduced | FF-06 |
| G5 | `OM_CON_DY_V` logic not in CARL; Op1 Silver not started; Op1 Bronze defects open (CARL-3509) | Operative contracted revenue by day cannot be rebuilt cleanly | FF-07 |
| G6 | Operative custom-field Bronze is all strings with malformed names | Custom-field lookups need explicit casting and mapping | FF-08 |
| G7 | Excel snapshot maps and 3 DF-owned maps are ungoverned | Reference data can change without review | FF-10, FF-11 |
| G8 | ML portfolio forecast is a one-time dump | No ongoing prod feed | FF-12 |
| G9 | DF Snowflake-managed Iceberg is invisible to CARL Glue | No lineage or discovery; federation status unclear (CARL-580 Done in Jira, "at risk" in weekly status) | FF-13 |
| G10 | No reconciliation between the Gerry-side FreeWheel share and CARL `freewheel_bronze` | Numbers may not match other CARL FreeWheel reporting | FF-14 |
| G11 | Prod parity with DEV undocumented | Unknown prod risk | FF-15 |
| G12 | No Cube view for the Finance capacity forecast | Dashboards bypass the semantic layer | FF-17 |

## 6. Risks carried by this inventory

- **Source retention.** The roadmap records that FreeWheel retains only 7 days at source. The DF daily job rebuilds the last 7 activity dates, so any repoint must prove CARL Bronze holds the same window, including late-arriving corrections (FF-14).
- **Third-party enriched feed.** FreeWheel decoupling from the third-party enriched data has no date (AI-087, due 31 Oct, behind pace).
- **Typed vs string data.** Operative Bronze columns are all strings; implicit string comparisons give silently wrong answers (e.g. `'80' >= '9'` is false).
