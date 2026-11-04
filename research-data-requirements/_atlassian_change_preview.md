# Preview: Confluence and Jira changes (nothing applied yet)

Site: wbdprod.atlassian.net · Space: PAYTV (CALS) · Project: CARL · Prepared 29-Oct-2026

## A. Decisions needed before anything is written

| # | Conflict | In Jira today | In the new docs | Recommended |
| --- | --- | --- | --- | --- |
| D1 | Panel Only history source | CARL-4114 says de-scope `AMS_ICUE_SHARE.MIT` and use `marketshare_bronze.factprogram` (176.25 M rows, 2015-06-29 → present). But epic CARL-4292 / story CARL-4294 (26-Oct) plan "MIT Panel Based Historical Data in Iceberg" | One-time backfill into `mit_panel_bronze` (Q-SH-03) | Follow CARL-4292 (backfill); keep `factprogram` as the fallback and parity source. Comment on CARL-4114 so it stops saying "de-scope" |
| D2 | Broadcast calendar source | CARL-4116 / CARL-557: generate it algorithmically, then validate against `EMERALDDW_PROD.COMMON.DIMDATE` | Land `SHARE_PROD_BIG_MIT.COMMON.DIMDATE` into `big_mit_bronze.dimdate` (the same object the Marketplace Imps SQL joins) | Land DIMDATE (exact parity with the Research SQL) **and** keep generation for dates outside its range |
| D3 | Database names | Stories use `marketplace_insights_silver/gold` (CARL-3775) and `measurement_silver/gold` (CARL-11) | One `research_silver` / `research_gold`, with `ms_` / `mi_` / `ngr_` prefixes | Adopt `research_*`; comments on each story give the old → new mapping |
| D4 | Duplicate stories across epics | CARL-4116 ↔ CARL-557 (conformed dims); CARL-4117 ↔ CARL-555 (MIT Silver); CARL-4121 ↔ CARL-4126 (DQ framework) | One shared build per item (doc 00) | Keep both keys, but split scope: CARL-557 = shared calendar / demo / daypart / stream / network; CARL-4116 = crosswalk + program taxonomy + advertiser; CARL-4117 = shared `dim_telecast` + `fct_mit_telecast_viewing` (all streams); CARL-555 = quarter-hour time period + universe estimates; CARL-4121 = shared `ops_*` tables + Marketplace Cube; CARL-4126 = NextGen gates writing to the same `ops_dq_results`. Add "relates to" links |

Doc corrections I'll make whatever you decide:
- CARL-4114 shows `big_mit_bronze.program_viewing` starting **2024-04-26**; my docs said 2024-08-05. I'll change the docs to 2024-04-26.
- The overlap window becomes 2024-04-26 → 2025-09-28.

## B. Confluence

### B1. New pages (4)

| Page title | Parent page | Content |
| --- | --- | --- |
| Research Data Requirements 00 – Shared Foundation (Bronze/Silver/Gold standards, conformed dims, shared MIT Silver, DQ, Cube) | PRD – Market Research Data Foundation & NextGen (7931527171) | `00_shared_foundation.md` |
| Research Data Requirements 01 – MarketShare (Taxonomy, Advertiser, Ad Intel) | Research Market Share Data Discovery (7955710014) | `01_marketshare_data_requirements.md` |
| Research Data Requirements 02 – Market Research / Marketplace Insights (VAMI 3, Marketplace Imps, Guideline) | Research Market Share Data Discovery (7955710014) | `02_market_research_marketplace_insights_data_requirements.md` |
| Research Data Requirements 03 – NextGen Research Dashboard (Power BI) | Technical Research & Data Architecture Spec: NextGen (7953154172) | `03_nextgen_research_dashboard_data_requirements.md` |

Each page gets a Jira links section listing the existing and new keys from section C.

### B2. Updates to existing pages

The existing body is not rewritten. A dated panel is added at the top of each page.

**7931527171 PRD** (panel "Update 29-Oct-2026: data requirements published"):
- Links to the 4 new pages.
- One database pair: `research_silver` / `research_gold` (D3).
- Methodology correction: `nielsen_data_type` = program vs ACM; Panel vs Big Data is `viewing_source`.
- Panel → Big MIT cutover is held in config (last Panel day 2025-09-28), matching the Marketplace Imps SQL quarter boundary.

**7955710014 Research Market Share Discovery** (panel "Findings 29-Oct-2026"):
- Guideline bucket corrected: `s3://turner-ams-bi-marketshare-smi/DataOutgoing/` (account 689264014593); `aws-ams-bi-marketshare-developer` is the IAM role, not the bucket.
- Taxonomy S3 profiling:
  - `output/network.csv` = `marketshare_bronze.dimnetwork` (0 differences).
  - `distributormapping` is not in Bronze.
  - The ETL appends new codes: +4 distributors and +23 genre type/subtype combos with a blank genre.
- Excel damage:
  - `LAST_PROCESS_UTC` is mangled in every input row.
  - `HASH_VALUE` is in scientific notation in 1,467/2,906 `productcategories` rows.
  - The Snowflake sample CSVs have the same damage.
  - Rule: read every column as string and keep leading zeros (`'00'` subtypes).
- Rules Engine anomalies: `#NAME?` at priority 299; a priority-102 "events" rule outputs Non-Event; Unmapped outputs at 402 and 501; `'Sports '` with a trailing space (54 rules).
- VAMI 3 scope: Prime measures (LookML rows 1184–1624) dropped; `dim_amrld_title_franchise` and `dim_bundle_map` excluded; everything else kept, including the advertiser.
- Marketplace Imps SQL mapped rule by rule. Known differences: the dedupe tie-break differs between the Panel and Big branches; the Big branch also covers pre-2021 quarters.

**7953154172 NextGen Tech Spec** (panel "Update 29-Oct-2026"):
- Link to doc 03.
- `nielsen_data_type` correction (above).
- Source table is `big_mit_bronze.timeperiod_quarterhour` (not `timeperiod_viewing`).
- Target databases renamed (D3).
- NRLD still Dev-only (CARL-4124, CARL-3781).

**7952761094 NextGen Semantic Layer (CARL-88)** (panel):
- Cube view list `ngr_view_delivery`, `_program_performance`, `_universe`, `_reach_frequency`, `_audience_profile`, `_data_availability`.
- Non-additive measures are built from numerator and denominator.
- `legacy_names` meta maps each Cube measure to its DAX measure.

**7961149449 VAMI Hub** (owned by the ASR team): a **page comment only**, no edit. It links to doc 02 and the Prime / excluded-object scope.

## C. Jira

### C1. Existing issues: comments (non-destructive)

Every comment starts with "Data requirements update (29-Oct-2026) – see Confluence page <link>". The key points per issue:

| Issue | Epic | Comment content |
| --- | --- | --- |
| CARL-3776 Research Market Share Data Discovery | 3775 | Discovery outputs delivered (4 pages). Open: live verification of the 6 Snowflake objects used by Marketplace Imps (AMS_ICUE_SHARE.MIT ×2, SHARE_PROD_BIG_MIT.MIT ×2, COMMON.DIMDATE, MARKETSHARE.DIMNETWORK); the Okta connector session was interrupted. List of new stories |
| CARL-4113 Guideline profiling spike | 3775 | Correct bucket; latest files seen 26-Oct (Telecast 28-Sep, AccuTV 26-Sep); file patterns `US_SMI_Telecast_Data_201701_<YYYYMM>_<YYYYMMDD>.txt.gz`, `SMI_US_AccuTV_<YYYYMMDD>_PSC.txt.gz`; all-string read rule; contract v1 from the first profiled file |
| CARL-4115 Guideline Bronze | 3775 | Correct bucket; manifest columns (`is_final_for_cycle`, `SUPERSEDED`); retention = current cycle + 6 finals; `quarantine` table; target `guideline_bronze` |
| CARL-4114 Methodology spike | 3775 | D1 outcome; cutover in `ref_pipeline_config`; one deterministic descriptor dedupe for both sources (the SQL tie-breaks differ); overlap window kept with `is_reporting_methodology = false` |
| CARL-4116 Conformed Marketplace dims | 3775 | D2 / D4 scope split; `dim_network` attribute list (`is_reporting_network`, `is_junk_sk`, continuity on `network_name`); `dim_program_taxonomy` with two genre fields (`nielsen_genre_simple` + Program Group Summary) and `event_name`; never filter dims on `isactive`; `ref_network_crosswalk` columns |
| CARL-4117 Silver C3 + MIT backfill | 3775 | Becomes the shared `research_silver.dim_telecast` + `fct_mit_telecast_viewing` (all 6 streams, not only C3); grain; MERGE plus a trailing 15-day restatement; links CARL-4292 / CARL-4294 for the backfill |
| CARL-4118 Guideline Silver | 3775 | Non-promo / concurrent-duplicate rules → `fct_guideline_reject` with reason codes; bounce table spec; snapshot tag per final delivery |
| CARL-4119 Ad Intel + AccuTV | 3775 | `fct_adintel_occurrence` columns (`eq30_units`, `is_static_segment`, all three brand keys); Gold `ms_fct_adintel_spend_daily` = parity with the Power BI NextGen Ad Spend `EST. SPEND`; static-segment unchanged guard (DQ-MS-08); `mi_fct_category_spend` |
| CARL-4120 Match bridge + supply/demand | 3775 | Tie-break order; tolerance in config (default ±5); supply long by demo (18 broad demos + P55-64); add `mi_fct_telecast_adintel` (primary advertiser per telecast, aggregated before the join) to keep VAMI 3 advertiser |
| CARL-4121 DQ + Marketplace Cube | 3775 | Shared `ops_dq_results` / `ops_data_freshness` schemas; Cube views `mi_view_telecast_supply_demand` (Prime family excluded), `mi_view_category_spend`, `mi_view_spend_bounce`, `ms_view_adintel_*`; 10 golden queries |
| CARL-4122 TMDL spike | 11 | Definitions needed from DAX: Program Gross, Program Eff, YTD weighting, ASC Avg (simple vs weighted) |
| CARL-4123 Hidden pages | 11 | Default proposed: build `ngr_fct_avg_audience_day`; defer LW rankers |
| CARL-4124 NRLD Prod promotion | 11 | Add NB-02 column dictionary and NB-04 history depth to acceptance; table list in the story includes `tv_household_person_sample`, which is not among the 12 tables seen. Verify |
| CARL-3781 NRLD duplicates bug | 11 | Provisional natural keys per table (doc 03 3.1) for the dedupe rule |
| CARL-4275 NRLD Silver discovery | 4272 | NRLD Silver table list (`nrld_viewing_event` … `ref_marketbreak`) and the AMRLD → NRLD map deliverable |
| CARL-555 MIT Silver | 11 | Source is `timeperiod_quarterhour` (not `timeperiod_viewing`); grain adds `viewing_source` + `stream_code`; `nielsen_data_type` correction; D4 split |
| CARL-556 MIT Gold | 11 | Keep numerator / denominator columns for Cube; quarter built from quarter-hour, not months; `viewing_methodology` on every fact |
| CARL-557 Conformed dims (NextGen) | 11 | `marketshare_bronze.dimdate` does not exist; D2 outcome; shared with CARL-4116 (D4); `ref_network_wbd_attributes` must include non-WBD owners |
| CARL-558 MarketShare Gold (portfolio) | 11 | Build on `research_gold.ngr_fct_avg_audience_month`; share denominators (Total TV vs Pay TV ASCO) |
| CARL-337 / CARL-338 NRLD Silver / Gold | 11 | Reach at target grain only; C3/C7 qualification via `advertisement_event`; `ref_marketbreak` config; marketbreak availability check first |
| CARL-4125 DAGs / CARL-4126 DQ gates | 11 | Shared DAG names (`research_conformed_dims`, `research_mit_silver`, `nextgen_research_gold`); DQ writes to the shared `ops_dq_results` |
| CARL-4294 MIT Panel discovery | 4292 | `mit_panel_bronze` spec (2015-06-29 → 2025-12-31, Parquet unload per month, reconciliation, tag `panel_frozen_v1`) |

### C2. Description edits (factual errors only)

| Issue | Change |
| --- | --- |
| CARL-4113 | Replace `s3://aws-ams-bi-marketshare-developer/DataOutgoing/` (4 places) with `s3://turner-ams-bi-marketshare-smi/DataOutgoing/` (AWS account 689264014593; role `aws-ams-bi-marketshare-developer`). Delivery window "20th and 5th" → "20th–31st (alert if none by the 5th)" |
| CARL-4115 | Same bucket replacement in the trigger section |

### C3. New stories (items with no Jira coverage)

All new stories: type Story, status To Do, no assignee, label `research-data-requirements`, and a link to the Confluence page.

**NEW-1 · Epic CARL-3775 · [MarketShare] CARL read access and versioned Bronze landing for the MarketShare taxonomy S3 files**
> As a data engineer, when Research uploads taxonomy changes through the MarketShare semaphore, I want each ETL run's input and output mapping files landed as a versioned snapshot in `marketshare_taxonomy_bronze`, so that distributor mapping (not in Bronze today) and every Research edit are queryable and auditable.
>
> AC:
> 1. Cross-account read role on `marketshare-prod/prod/mapping/` (not user access keys).
> 2. EventBridge on `marketshare_etl_end.txt` / `_error.txt` plus a daily poll.
> 3. 5 files × input/output landed all-string, utf-8-sig, headers trimmed, leading zeros preserved.
> 4. `taxonomy_run_manifest` with `etl_status`.
> 5. An error run does not advance Silver.
> 6. Row counts match the 23-Oct copy (310/315/388/2,906/385 input; 314/337/388/2,906 output).

**NEW-2 · Epic CARL-3775 · [MarketShare] Silver taxonomy reference tables and Rules Engine logic, with unmapped/anomaly feed to Research**
> As a research analyst, I want the Rules Engine, distributor mapping, genre and product categories as SCD2 Silver reference tables with the first-match-by-priority logic documented and tested, so that program grouping is governed and errors are caught before they reach dashboards.
>
> AC:
> 1. `ref_program_group_rule`, `ref_adintel_distributor`, `ref_program_genre`, `ref_product_category`.
> 2. Operators limited to `=`, `any`, `like`.
> 3. Priority unique.
> 4. Excel error values block the load (`#NAME?` at priority 299 caught).
> 5. Weekly feed of unmapped programs and auto-added codes to Research.
> 6. Replaying the rules reproduces `dimnetworkprogramnamemapping` on a sample.

**NEW-3 · Epic CARL-3775 · [Shared] Land SHARE_PROD_BIG_MIT.COMMON.DIMDATE to big_mit_bronze.dimdate** *(only if D2 = land)*
> AC:
> 1. Table added to the Big MIT pipeline.
> 2. `dim_broadcast_calendar.broadcast_quarter_label` equals `DIMDATE.broadcastquarter` on every date.
> 3. Calendar tests (4/5 weeks per month, 52/53 per year, 6a–6a rule) pass.

**NEW-4 · Epic CARL-3775 · [Market Research] Reference seeds: event program map, Nielsen program type/subtype, custom dayparts**
> AC:
> 1. `ref_event_program_map` seeded from the 1,765-row map in the Marketplace Imps SQL (World Cup 920, Olympics 677, Super Bowl 168), matched on `regexp_replace(upper(program_name),'[^A-Z0-9]','')`.
> 2. Program type/subtype seeds exported from the Looker views, keeping leading zeros.
> 3. `ref_custom_daypart` exported from `icue_mit_custom_daypart`.
> 4. Git-reviewed with an owner.

**NEW-5 · Epic CARL-3775 · [Market Research] Reproduce "Marketplace Imps" (A25-54 C3 gross impressions by program and quarter) from Cube**
> AC:
> 1. Cube pre-aggregation `marketplace_imps_quarterly`.
> 2. Athena parity query (doc 02 6.3) within ±0.5 % of the Snowflake SQL by network × quarter, 2021 Q1 → latest.
> 3. Every out-of-tolerance row explained (dedupe tie-break, pre-2021 Big branch, rebrand event matches).
> 4. Genre and event rules identical to the SQL.

**NEW-6 · Epic CARL-3775 · [Market Research] VAMI 3 parallel run and Looker Explore retirement**
> AC:
> 1. LookML field export (`mit_adintel_smi_v2`) mapped to Cube members with `legacy_names`, excluding the Prime measures (rows 1184–1624), `dim_amrld_title_franchise` and `dim_bundle_map`.
> 2. Parity within ±3 % vs `MIT_ADINTEL_SMI_V3` for 2023–2025, network × month, gaps explained.
> 3. Research sign-off.
> 4. Explore hidden, then retired.

**NEW-7 · Epic CARL-3775 (linked to CARL-11) · [Shared] Provision research_silver / research_gold, Iceberg table standards and write-audit-publish** *(only if D3 = adopt)*
> AC:
> 1. Terraform databases in all environments.
> 2. Table property defaults (format v2, zstd, CoW for Gold / MoR for Silver facts, CARL-3935 serialization).
> 3. WAP branch publish proven on one table (or the staging + swap fallback).
> 4. `ref_pipeline_config` seeded (cutover 2025-09-28, tolerance 5, bounce depth 6, static segment end date).
> 5. Old → new name map published.

**NEW-8 · Epic CARL-11 · [NextGen] Cube views ngr_view_* over research_gold**
> AC:
> 1. Six views (delivery, program performance, universe, reach/frequency, audience profile, data availability).
> 2. Non-additive measures from numerator/denominator.
> 3. Reach exposed only at stored grain.
> 4. Universe selector (Total TV / Pay TV ASCO).
> 5. `legacy_names` for every DAX measure.
> 6. Registered `proposed` in `cube_model.yaml`, then certified after the CARL-4128 parity harness.

**NEW-9 · Epic CARL-11 · [Spike] MRI and MRI Streaming RLD ingestion discovery (Phase 2)**
> AC:
> 1. MRI share objects and SFTP Streaming RLD layouts documented.
> 2. Cadence and owner confirmed.
> 3. `mri_bronze` / `mri_streaming_bronze` contract drafted.
> 4. Index metric definitions agreed with Research.

Not creating stories for:
- WBD network attribute seed and logos (covered by CARL-557).
- Selectors (CARL-4127), parity harness (CARL-4128), decommission (CARL-4129).
- NRLD promotion (CARL-4124 / CARL-2952).
- Panel backfill (CARL-4292 / CARL-4294).
