# 03 – NextGen Research Dashboard (Power BI): Data Requirements

| Field | Value |
| --- | --- |
| Objective | Serve the Power BI **NextGen Ad Sales Research** dashboard from CARL Gold + Cube instead of Snowflake `BOLT_STUDIOS_BICONTENT_PROD.NEXT_GEN` (built on EmeraldDW AMRLD and MIT), and re-base respondent-level metrics from AMRLD to **NRLD**. MRI index is added in Phase 2 |
| Consumer | Power BI workspace `Next Gen Research`; report `NextGenResearchDashboard` (22 pages, 9 visible, 285 data-bound visuals); dataset `NextGenResearchDataSource` (41 tables, 166 measures referenced) |
| Jira | Epic CARL-11 (NextGen); NRLD promotion CARL-2952, CARL-3781, CARL-4124 |
| Depends on | `00_shared_foundation.md` (all conformed dims, MIT Silver, DQ, Cube); `01_marketshare_data_requirements.md` (network and program taxonomy) |
| Status | DRAFT v0.1 – 29 Oct 2026 |

## Jira tracking

| Item | Jira |
| --- | --- |
| TMDL / DAX export (NGR-01) | CARL-4122 |
| Hidden-page scope (NGR-20) | CARL-4123 |
| NRLD Prod promotion (NGR-02) | CARL-4124, CARL-2952 |
| NRLD duplicates / late rows (NGR-03) | CARL-3781 |
| NRLD Silver discovery, dictionary, AMRLD→NRLD map (NGR-04) | CARL-4275 (epic CARL-4272) |
| Shared dims + WBD attribute seed (NGR-05, NGR-06) | CARL-557 |
| MIT quarter-hour and universe Silver (NGR-07) | CARL-555 |
| Shared MIT telecast Silver (NGR-08) | CARL-4117 |
| MIT Gold delivery, program, universe, median age (NGR-09..11) | CARL-556; portfolio rollups CARL-558 |
| NRLD Silver / Gold reach and audience profiles (NGR-12, NGR-13) | CARL-337, CARL-338 |
| DAG (NGR-14) / DQ gates (NGR-15) | CARL-4125 / CARL-4126 |
| Cube `ngr_view_*` (NGR-16) | CARL-4400 |
| BI selectors (NGR-17) / parity (NGR-18) / decommission (NGR-19) | CARL-4127 / CARL-4128 / CARL-4129 |
| MRI discovery (Phase 2) | CARL-4401 |
| Databases, WAP, ops tables | CARL-4399 |

## 1. Scope

| Page / area (Power BI) | In scope | Data family | Gold table |
| --- | --- | --- | --- |
| KPIs Trends (AA, Share, Reach %, Avg Frequency, Avg Time Spent, MoM/YoY) | Yes | MIT + NRLD | `ngr_fct_avg_audience_month`, `ngr_fct_reach_freq_timespent_month` |
| Portfolio Share (Share TV Avg '000, WBD vs non-WBD, rank, YTD growth) | Yes | MIT | `ngr_fct_avg_audience_month` |
| Daypart Comparison / Custom Comparison | Yes | MIT | `ngr_fct_avg_audience_month` |
| Channel Performance (Top Titles Live+SD, DOW, CVG rating, premieres) | Yes | MIT | `ngr_fct_program_telecast_month` |
| TV Universe (CVGUE000, variance waterfall) | Yes | MIT | `ngr_fct_universe_estimate_month` / `_quarter` |
| Age and Gender (Median Age P2+, Male Skew P25-54, gender pie) | Yes | MIT (decision N-05) | `ngr_fct_median_age_month`, `ngr_fct_avg_audience_month` |
| Audience Profiles (≈45 trait composition %, ASC Avg, Median HHI) | Yes | NRLD | `ngr_fct_audience_profile_quarter` |
| Reference page (data availability, last refreshed) | Yes | Ops | `ngr_ref_data_availability` |
| Exec Portfolio Report, Delivery Trends, Ad Sales Rankers (hidden pages) | **Decision N-03**; default: build only `ngr_fct_avg_audience_day` (cheap), defer rankers LW | MIT | `ngr_fct_avg_audience_day`, `ngr_fct_program_telecast` |
| MRI index (new requirement R-03/R-04) | Phase 2 | MRI | `ngr_fct_mri_index` |
| Ad Intel competitive spend (R-01) | Served by doc 01 (`ms_view_adintel_spend`) | Ad Intel | |
| Selectors, field parameters, dynamic titles, colours | **Stay in BI** | — | — |

## 2. Sources and current state

| ID | Source | CARL state | Used for |
| --- | --- | --- | --- |
| SRC-NG-01 | `big_mit_bronze.timeperiod_quarterhour` | Prod, daily | Time-period delivery, share, PUT, median age, exec portfolio |
| SRC-NG-02 | `big_mit_bronze.program_viewing`, `program_descriptor` (+ `_serial`) | Prod | Program performance, premieres, rankers (via doc 00 shared Silver) |
| SRC-NG-03 | `big_mit_bronze.universe_estimate` | Prod | Coverage UE |
| SRC-NG-04 | `big_mit_bronze.program_viewing_sellingdemos`, `intab` | Prod | Demo cross-check; sample-size flags |
| SRC-NG-05 | `marketshare_bronze.dimnetwork`, `dimnetworkprogramnamemapping`, `dimtimeshiftedviewing`, `dimdaypart` | Prod | Conformed dims (doc 00) |
| SRC-NG-06 | `nrld_bronze` (12 tables) | **Dev only**; Prod files land at `s3://carl-bronze-us-east-1-prod/snowflake/nrld/bronze/` but are not registered; duplicates and late rows unresolved | Reach / frequency / time spent, audience profiles |
| SRC-NG-07 | `mit_panel_bronze` (doc 02) | Proposed | Pre-2024-04 history for YoY (history needed back to 2018 for `MONTH_SORT`) |
| SRC-NG-08 | MRI (`AMS_ICUE_SHARE.MRI` → `mri_bronze`), MRI Streaming RLD (SFTP → `mri_streaming_bronze`) | Not in CARL | Phase 2 |
| SRC-NG-09 | Snowflake `NEXT_GEN` (3 gold, 3 silver, 2 views) + 34 JavaScript procedures | Prod (Snowflake) | **Parity baseline and logic reference only**; do not land |
| SRC-NG-10 | EmeraldDW `AMRLD`, `COMMON` | Prod (Snowflake) | Not landed. `DIMDATE` is replaced by `SHARE_PROD_BIG_MIT.COMMON.DIMDATE` (doc 00) |

### Correction carried from discovery

Earlier NextGen drafts treated `nielsen_data_type` as "Panel vs Big Data + Panel". That is wrong: `nielsen_data_type` distinguishes program from ACM (commercial) data.

- **Methodology** is `viewing_source` / `viewing_methodology` (doc 00 5.2).
- **Commercial vs program** is part of `stream_code` (doc 00 4.7).

The Gold spec below uses this.

## 3. Bronze requirements

### 3.1 `nrld_bronze`: promote and harden (blocker for reach and audience profiles)

| Req | Detail | Acceptance |
| --- | --- | --- |
| NB-01 | Merge CARL-2952; register all 12 tables in the Prod Glue catalog (`sf-iceberg-glue-register-nrld-prod` or a Terraform replacement) | Athena `SELECT` on every table in Prod |
| NB-02 | Load the column dictionary (`DESCRIBE`) into the Bronze catalog; columns are currently unknown | 12 tables documented |
| NB-03 | Natural key per table; dedupe rule; late-arrival rule (latest `ingest_timestamp`/vendor version wins) | Duplicates = 0 on the natural key for the last 90 days after Silver dedupe; daily row counts equal `SHARE_PROD_NRLD` |
| NB-04 | History depth ≥ 25 months (YoY on a 13-month trend) | Documented per table |
| NB-05 | AMRLD → NRLD object map (`PROGRAMVIEWINGRESPONDENTS`, `RESPONDENTWEIGHTS`, `RESPONDENTS`, `HOUSEHOLDS`, `UNIVERSEESTIMATE`, `PROGRAMVIEWINGRESPONDENTMOP`, `PROGRAMDESCRIPTION`) | Map signed off |
| NB-06 | For each of the 23 marketbreak attributes: Available / Derivable / Not available in NRLD | List agreed with Research before NGR Gold build |

Provisional natural keys, to verify after NB-02:

| Table | Provisional key |
| --- | --- |
| `tv_household_person_program_coded_viewing_event` | household, person, originator, event start, event end, TSV / stream, viewing date |
| `dtvr_household_person_program_coded_viewing_event` | Same as above (digital) |
| `tv_household_person_weight` | household, person, weight date, weight type |
| `tv_household_weight` | household, weight date |
| `tv_household_person_characteristics` | household, person, effective date, characteristic code |
| `universe_estimate` | demo / marketbreak, UE period |
| `market_break_universe_estimates_with_adjustment_factor` | marketbreak, value, period |
| `advertisement`, `advertisement_event` | advertisement id; event id |
| `originator_lineup` | originator, effective date |
| `code_description_mapping` | code type, code |
| `mdr_national_data_availability` | stream, date |

### 3.2 `big_mit_bronze`

No change, other than adding `dimdate` (doc 00).

### 3.3 MRI (Phase 2)

- `mri_bronze`: land the share objects as delivered, monthly on the 1st.
- `mri_streaming_bronze`: SFTP → landing → Bronze (P1 append per delivery).
- The detailed contract is deferred to the Phase 2 intake.

## 4. Silver (`research_silver`)

### 4.1 Shared (doc 00)

`dim_broadcast_calendar`, `dim_network`, `dim_program_taxonomy`, `dim_demo` + `bridge_demo_cell`, `dim_daypart` + `bridge_daypart_quarterhour`, `dim_viewing_stream`, `dim_telecast`, `fct_mit_telecast_viewing`.

### 4.2 `ref_network_wbd_attributes` (seed; replaces `WM_NETWORKS` curated columns)

| Column | Type | Source column in Power BI |
| --- | --- | --- |
| `src_networksk` / `network_key` | bigint | join |
| `display_name` | string | `WM_NETWORKS[DISPLAY]` |
| `conglomerate` | string | `CONGLOMERATE` |
| `main_asco_owner` | string | `Main ASCO Owners` |
| `portfolio_owner` | string | `Owners (Porfolio Share '000)` |
| `owner_tier_group` | string | `EXEC_PORT_TIERED_GROUPS` (WBD8, USN8, DSNY5, PAR6, NBCU3, AETV3, FOX2, HALL, RLZC) |
| `network_type_1` | string | `NETWORK TYPE 1` (e.g. Ad-Supported-Cable, Big 4 Broadcast) |
| `is_asco` | boolean | ad-supported cable originator (drives the `Pay TV (ASCO)` universe) |
| `wbd_tier` | string | `Tiered WBD Networks` |
| `is_spanish_language` | boolean | `SPANISH_LANG_NET` |
| `is_excluded_from_report` | boolean | Replaces the report-level `DISPLAY` exclusion filter |
| `logo_uri` | string | Managed S3 asset (not companieslogo.com or wikimedia; N-08) |
| `steward`, `effective_from`, `effective_to` | | |

The seed must hold non-WBD owners too (Disney, Fox, NBCU, Paramount, A&E, AMC, Hallmark, Univision). Its source and owner must be confirmed (N-02).

### 4.3 `mit_timeperiod_qh_demo`

| Item | Specification |
| --- | --- |
| Grain | `viewing_source × nielsen_network_id × broadcast_date × quarterhour_id × stream_code × cell_code` (cells unpivoted) |
| Source | `big_mit_bronze.timeperiod_quarterhour` (+ Panel equivalent if backfilled) |
| Columns | keys + `network_key`, `date_key`, `quarterhour_time_key`, `daypart_keys` (via the bridge, exploded in Gold, not here), `delivery`, `put_cvg`, `put_nat`, `average_audience`, `coverage_rating`, `national_rating`, `ue_cov`, `ue_nat`, `quarterhour_duration_min`, `is_preliminary`, `src_processid`, `viewing_methodology`, `is_reporting_methodology` |
| Dedupe | Latest `processid` per key; final replaces preliminary (BR-SH-15) |
| Partition | `months(broadcast_date)`, `identity(stream_code)` |
| Load | P2 MERGE; trailing 15-day restatement |

### 4.4 `mit_universe_estimate_demo`

- **Grain:** `nielsen_network_id × ue_start_date × ue_end_date × cell_code`. Columns: `ue_cov`, `ue_nat`.
- **Expansion:** expanded in Gold to broadcast month and quarter over the validity window.

### 4.5 NRLD Silver (after NB-01..06)

| Table | Grain | Purpose |
| --- | --- | --- |
| `nrld_viewing_event` | Deduped viewing events (NB-03) | Source for crediting |
| `nrld_person_network_day` | `person × household × network_key × broadcast_date × daypart_key × stream_code` | `minutes_viewed`, `qualified_commercial_seconds` (C3/C7 from `advertisement_event`; AMRLD rule `durationqualifiedcommercialseconds >= 1`) |
| `nrld_person_weight_day` | `person × date` | Unified weight (AMRLD equivalent: `RESPONDENTWEIGHTS.monthlyunifiedweight`; NRLD weight type To verify) |
| `nrld_person_characteristics` | `person × effective period` | The 23 marketbreak flags pivoted from characteristics + household |
| `nrld_universe_estimate` | demo / marketbreak × period | Universes and adjustment factors (replaces `AP_ADJ_FACTOR_SILVER`) |
| `nrld_originator_map` | `originator × effective period` → `network_key` | Map NRLD originators to `dim_network` (DQ-NG-05) |
| `nrld_data_availability` | `stream × date` | From `mdr_national_data_availability` |
| `ref_marketbreak` (seed) | `marketbreak × value` | Config-driven definitions: income bands, race, ethnicity, education, occupation, HH size, children, home ownership, county size, DVR, SVOD, vMVPD, smart TV, internet connected device, 3+ smartphones, video game, pets, wine, moviegoer, age, P18+, P2+. Replaces 23 near-identical procedures |

Partition the NRLD facts by `months(broadcast_date)`. These are person-level data, so Cube access is restricted to aggregated Gold (section 7).

## 5. Gold (`research_gold`, prefix `ngr_`)

All Gold facts:
- Carry `viewing_methodology` (Panel Only / Big Data + Panel) and `is_complete` (every day of the period loaded for that stream).
- Are written by WAP.
- Use decimal types from doc 00 2.2.

### 5.1 `ngr_fct_avg_audience_month`

| Item | Specification |
| --- | --- |
| Grain | `broadcast_month_key × network_key × demo_code × daypart_key × stream_code × viewing_methodology` |
| Source | `mit_timeperiod_qh_demo` × `bridge_demo_cell` × `bridge_daypart_quarterhour` |
| Partition | `months(broadcast_month_start_date)` (hidden partitioning, doc 00 2.4) |

| Column | Type | Definition |
| --- | --- | --- |
| `avg_audience_000` | decimal(18,3) | `sum(demo_aa × qh_minutes) / sum(qh_minutes) / 1000` (BR-NG-01) |
| `aa_minutes_numerator` | decimal(24,3) | `sum(demo_aa × qh_minutes)`, kept so Cube can re-weight across months |
| `minutes` | int | denominator |
| `put_total_000`, `put_total_numerator` | decimal | Persons using TV (total TV) |
| `put_asco_000`, `put_asco_numerator` | decimal | Sum of ASCO networks' AA (Pay TV denominator) |
| `coverage_rating`, `national_rating` | decimal(9,4) | AA / UE × 100 |
| `ue_cov_000` | decimal(18,3) | |
| `male_avg_audience_000`, `female_avg_audience_000` | decimal(18,3) | for skew and gender pie (`GENDER_SKEW_AP`) |
| `is_complete` | boolean | |
| `src_processid_max`, audit columns | | |

### 5.2 `ngr_fct_avg_audience_day`

The same measures at `date_key × network_key × demo_code × daypart_key × stream_code` (exec portfolio uses `LIVE_3`).

### 5.3 `ngr_fct_avg_audience_quarter`

Built from **quarter-hour Silver** (not by averaging months). Same columns.

### 5.4 `ngr_fct_program_telecast_month` and `ngr_fct_program_telecast`

| Item | Specification |
| --- | --- |
| Grain (month) | `broadcast_month_key × network_key × program_key × demo_code × stream_code` |
| Grain (telecast) | `telecast_key × demo_code × stream_code` (rankers LW; Channel Performance DOW) |
| Source | `fct_mit_telecast_viewing` (doc 00) × `dim_telecast` × `bridge_demo_cell` |

| Column | Definition |
| --- | --- |
| `telecast_count` | Program TC's |
| `premiere_count` | Telecasts with `is_premiere` (replaces `PREMIERES`) |
| `avg_audience_000` | Duration-weighted across telecasts |
| `aa_minutes_numerator`, `minutes` | For re-weighting |
| `max_telecast_avg_audience_000`, `max_telecast_coverage_rating` | Best telecast |
| `coverage_rating` | AA / coverage UE × 100 |
| `gross_impressions_000` | Definition from DAX (N-01 TMDL export). Default: `sum(avg_audience × telecasts)` |
| `program_minutes`, `network_schedule_minutes` | % Sched = program / network minutes |
| `day_of_week_name` | DOW chart (telecast grain) |

### 5.5 `ngr_fct_universe_estimate_month` / `_quarter`

- **Grain:** period × `network_key` × `demo_code`.
- **Columns:** `ue_cov_000`, `ue_nat_000`, `ue_year`, `ue_quarter_key`.
- **Expansion:** the UE validity window is expanded to periods. `L5_MONTH_UES_AND_HISTORICAL_UES` becomes a Cube view filter, not a table.

### 5.6 `ngr_fct_median_age_month`

- **Grain:** `broadcast_month_key × network_key × daypart_key × stream_code`.
- **Columns:** `median_age_p2 decimal(5,2)`, `band_delivery_json` (the age-band distribution used, for audit).
- **BR-NG-05:** a linear-interpolated median over age-band delivery (MIT cells). The basis is Decision N-05.

### 5.7 `ngr_fct_reach_freq_timespent_month` / `_quarter`

| Item | Specification |
| --- | --- |
| Grain | period × `network_key × demo_code × daypart_key × stream_code` |
| Source | `nrld_person_network_day` × `nrld_person_weight_day` × `nrld_universe_estimate` × `nrld_person_characteristics` (demo) |
| Rule | **BR-NG-02:** reach is computed from person-level data **at the target grain**, never summed or averaged across months or networks. The quarter table is built separately from person data |

| Column | Definition |
| --- | --- |
| `reach_000` | Σ weight of persons with ≥ threshold minutes (threshold N-04; C3/C7 require qualified commercial seconds ≥ 1) |
| `universe_000` | demo universe |
| `reach_pct` | reach / universe × 100 |
| `avg_frequency_days` | Σ (weight × distinct viewing days) / Σ weight of reached |
| `avg_time_spent_min` | Σ (weight × minutes) / Σ weight of reached |
| `weighted_days_numerator`, `weighted_minutes_numerator` | Cube components |
| `respondent_count` | Unweighted sample (quality flag; DQ-NG-07) |

### 5.8 `ngr_fct_audience_profile_quarter`

| Item | Specification |
| --- | --- |
| Grain | `broadcast_quarter_key × network_key (null for benchmark) × is_asc_benchmark × daypart_key × marketbreak × marketbreak_value` |
| Columns | `viewers_000`, `viewers_with_trait_000`, `comp_pct` (BR-NG-03), `median_value` (median age / HHI rows), `respondent_count` |
| Rule | **BR-NG-03:** `comp_pct = Σ weight viewers with trait / Σ weight viewers × 100`. **BR-NG-04:** ASC Avg = simple mean of `comp_pct` across ASC networks (simple vs weighted To verify against `AP_ASC_MKTBRKS_GOLD`) |
| Cadence | Quarterly, after quarter close plus the Live+7 settle |

### 5.9 `ngr_ref_data_availability`

- **Grain:** `source × stream_code`.
- **Columns:** `latest_complete_date`, `latest_complete_month_key`, `last_loaded_ts`.
- **Feeds:** `DATA_AVAILABILITY`, `WM_BROADCAST_CALENDAR_MAX_DATES`, `DATE_LAST_REFRESHED`.
- **Implementation:** a view over `ops_data_freshness` (doc 00).

### 5.10 `ngr_fct_mri_index` (Phase 2)

- **Grain:** MRI study × network × demo × attribute.
- **Columns:** `index`, `pct_composition`, `projection_000`.
- The specification is deferred to the MRI intake.

## 6. Business rules (summary)

| ID | Rule | Status |
| --- | --- | --- |
| BR-NG-01 | AA is duration-weighted over quarter hours in daypart and period (`/1000` for '000) | Medium; confirm vs DAX (N-01) |
| BR-NG-02 | Reach, frequency and time spent are computed at the target grain from person data | Confirmed (procedure logic) |
| BR-NG-03 | Composition % definition | Confirmed |
| BR-NG-04 | ASC benchmark = mean across ASC networks | To verify |
| BR-NG-05 | Median age = interpolated median over age bands | Decision N-05 |
| BR-NG-06 | Share = network AA / PUT × 100. The `UNIVERSE` selector switches the denominator: `Total TV` → `put_total`, `Pay TV (ASCO)` → `put_asco` | Confirmed (measure names) |
| BR-NG-07 | Male skew P25-54 = AA(M25-54) / AA(P25-54) | Confirmed |
| BR-NG-08 | MoM / YoY / QoQ: prior = same broadcast month last year for YoY; computed in Cube with `time_shift` on `dim_broadcast_calendar` | Confirmed |
| BR-NG-09 | YTD = duration-weighted from broadcast year start to the selected month (numerator / denominator sums) | Medium |
| BR-NG-10 | Rankers: rank by AA desc; Top 20 (`rank < 21`); `AA > 0`; stream `LIVE_SD` | Confirmed (visual filters) |
| BR-NG-11 | Report-level filters become `dim_network.is_excluded_from_report = false`, `demo_code is not null`, plus stream and daypart lists | Confirmed |
| BR-NG-12 | Reporting methodology follows doc 00 BR-SH-14 unless Research chooses to expose both (N-10) | Decision |

## 7. Cube

| View | Gold tables | Key measures (Cube) | Dimensions | Segments |
| --- | --- | --- | --- | --- |
| `ngr_view_delivery` | `ngr_fct_avg_audience_month/_quarter/_day` | `avg_audience_000` (= Σ numerator / Σ minutes / 1000), `share_pct`, `share_of_tv_pct` (universe-switch), `coverage_rating`, `male_skew_pct`, `demo_comp_pct`, MoM / YoY / QoQ / YTD variants | network (all attributes + WBD seed), demo, daypart (WBD / Nielsen), stream, calendar, methodology, universe selector | `wbd`, `non_wbd`, `asco`, `report_networks`, `complete_periods` |
| `ngr_view_program_performance` | `ngr_fct_program_telecast_month`, `ngr_fct_program_telecast` | `program_avg_audience_000`, `program_cvg_rating`, `telecast_count`, `premiere_count`, `max_tc_*`, `gross_impressions_000`, `schedule_share_pct` | program (name, type, Program Group Summary), network, DOW, demo, stream | `premieres`, `live_sd` |
| `ngr_view_universe` | `ngr_fct_universe_estimate_*` | `ue_cov_000`, QoQ / YoY variance | network, demo, UE calendar | `last_5_months` |
| `ngr_view_reach_frequency` | `ngr_fct_reach_freq_timespent_*` | `reach_pct`, `avg_frequency_days`, `avg_time_spent_min` (exposed **only at stored grain**; CB-01) | network, demo, daypart, stream, month / quarter | |
| `ngr_view_audience_profile` | `ngr_fct_audience_profile_quarter` | `comp_pct`, `asc_avg_comp_pct`, `median_value`, `reach_000` | network, marketbreak, value, daypart, quarter | `asc_benchmark` |
| `ngr_view_data_availability` | `ngr_ref_data_availability` | `latest_complete_date`, `last_loaded_ts` | source, stream | |

Rules:
- Every Cube measure has a `meta.legacy_names` entry pointing to the DAX measure (e.g. `"Share TV Avg '000 WBD"`). This lets the Power BI rebuild map 1:1 (FR-16).
- About 45 presentation measures (titles, labels, colours) and the selector tables stay in Power BI.
- **Pre-aggregations:**
  - `delivery_monthly`: network × demo × daypart × stream × month.
  - `delivery_daily_l3`: exec portfolio.
  - `program_monthly_lsd`.
  - Refresh is keyed to `ops_data_freshness`.
- **Power BI connection:** Decision NG-D1. Repoint to the Cube SQL API (keeps custom visuals Advance Card, Multiple Axes, Chiclet Slicer), or rebuild in Quick.

## 8. Orchestration and cadence

| Data | Source cadence | CARL schedule |
| --- | --- | --- |
| MIT Live / Live+SD | Daily | `nextgen_research_gold` after `research_mit_silver` (~20:30 UTC) |
| MIT Live+3 / C3, Live+7 / C7 | Daily, restated | Same run; trailing 15-day restatement; month built only when `is_complete` |
| Universe estimates | Per UE period (Sept reset) | Daily check; rebuild on change |
| NRLD reach | Daily delivery | Monthly per stream once the month closes (replaces `RUN_REACH_FREQUENCY_TIMESPENT_IF_NEEDED`) |
| NRLD audience profiles | Quarterly | After quarter close + Live+7 settle (mirrors Friday, days 8–28 of Jan / Apr / Jul / Oct) |
| Cube / Power BI | — | Pre-aggregation refresh after each Gold publish |

DAG `nextgen_research_gold`:
1. Sensors on `research_mit_silver` and NRLD Silver.
2. Build each Gold table when needed (availability check).
3. DQ.
4. WAP publish.
5. Update `ngr_ref_data_availability`.
6. Cube refresh.

## 9. Data quality and parity

| ID | Check | Threshold | Severity |
| --- | --- | --- | --- |
| DQ-NG-01 | `mit_timeperiod_qh_demo` unique on key; reconciles to Bronze per day × stream (count, Σ AA) | Exact | BLOCKER |
| DQ-NG-02 | Per-day completeness per stream before a month is `is_complete` | All days | BLOCKER for month build |
| DQ-NG-03 | P2+ cell sum = MIT total AA | ±0.1 % | BLOCKER |
| DQ-NG-04 | NRLD duplicates on natural key | 0 | BLOCKER |
| DQ-NG-05 | NRLD originators mapped to `dim_network` | 100 % of weighted minutes | BLOCKER |
| DQ-NG-06 | Reach ≤ universe; frequency ≥ 1; composition 0–100 | 0 violations | BLOCKER |
| DQ-NG-07 | Respondent count below the sample floor (to agree; e.g. 50) | Flag rows | WARN |
| DQ-NG-08 | MIT parity vs Power BI: 5 networks (incl. 2 non-WBD) × 4 demos × 3 dayparts × 3 streams × 3 months | AA / Share ±0.5 %; Top-20 rankers exact | BLOCKER for cutover |
| DQ-NG-09 | NRLD vs AMRLD variance report (methodology change expected) | Tolerance agreed up front; Research sign-off | BLOCKER for cutover |
| DQ-NG-10 | 7 legacy-name visuals (`BROADCAST_CALENDAR`, `CONGLOMERATE_LKP`, `DAY_PART`, `DEMO_DIM`, `DATASTREAM_DIM`, `WM_AVG_AUDIENCE_QUARTER`, `Yes/No`) fixed or removed before baselines are captured | — | BLOCKER for baseline |

## 10. Power BI table → CARL map (41 model tables)

| Power BI table | CARL target | Disposition |
| --- | --- | --- |
| `WM_REACH_AND_FREQUENCY`, `_QTR` | `ngr_fct_reach_freq_timespent_month` / `_quarter` | Rebuild on NRLD |
| `WM_AVG_AUDIENCE_MONTH`, `GENDER_SKEW_AP` | `ngr_fct_avg_audience_month` | Rebuild on MIT |
| `EXEC_PORTFOLIO_BY_DAY_L3` | `ngr_fct_avg_audience_day` | Rebuild (N-03) |
| `CHANNEL_PERFORMANCE`, `AD_SALES_RANKERS_MONTH_LSD`, `PREMIERES` | `ngr_fct_program_telecast_month` | Rebuild |
| `AD_SALES_RANKERS_LW_LSD` | `ngr_fct_program_telecast` (last week) | Rebuild or de-scope (N-03) |
| `NET_AUDIENCE_NEW`, `ASC_AUDIENCE_NEW` | `ngr_fct_audience_profile_quarter` | Rebuild on NRLD |
| `WM_MEDIAN_AGE_MONTH` | `ngr_fct_median_age_month` | Rebuild (N-05) |
| `WM_UNIVERSE_ESTIMATE_MONTH`, `_QUARTER`, `L5_MONTH_UES_AND_HISTORICAL_UES` | `ngr_fct_universe_estimate_*` (+ Cube filter) | Rebuild |
| `WM_NETWORKS`, `DIM_ALL_MAIN_OWNERS`, `EXEC_PORT_TIERED_GROUPS` | `dim_network` + `ref_network_wbd_attributes` | Rebuild + seed |
| `WM_BROADCAST_CALENDAR`, `WM_UE_CALENDAR`, `MONTH_SORT` | `dim_broadcast_calendar` | Rebuild |
| `WM_BROADCAST_CALENDAR_MAX_DATES`, `DATA_AVAILABILITY`, `DATE_LAST_REFRESHED` | `ngr_ref_data_availability` | Rebuild |
| `WM_DEMO` | `dim_demo` | Rebuild + seed |
| `WM_DAYPART`, `WM_DAYPART_ALL` | `dim_daypart` | Seed |
| `WM_TSV` | `dim_viewing_stream` | Rebuild |
| `WM_PROGRAM_CATEGORY` | `dim_program_taxonomy` | Rebuild |
| `UNIVERSE`, `DAYPART 1/2`, `CUSTOM_COMPARISON_*`, `TIME_PERIOD`, `CHANNEL_SELECTOR`, `WM_DATE_SELECTION`, `VERSION`, `Info - *` | Power BI | Keep in BI |
| `*MEASURES` (166) | Cube measures (≈120) + BI presentation (≈45) | Re-express |

## 11. Open decisions

| ID | Question | Owner | Default |
| --- | --- | --- | --- |
| N-01 | Export TMDL/BIM for partitions and DAX (definitions of Gross, Eff, YTD, ASC Avg) | Tatiana Rocha / PBI admin | Required before Gold build of 5.4 and 5.8 |
| N-02 | Source and owner of `WM_NETWORKS` curated attributes (includes non-WBD owners) | Tatiana Rocha / Research | Seed `ref_network_wbd_attributes` with a named steward |
| N-03 | Hidden pages (Exec Portfolio, Delivery Trends, Ad Sales Rankers): keep, drop or defer | Heather Coghill / Tatiana | Build `ngr_fct_avg_audience_day`; defer LW rankers |
| N-04 | Reach qualifying-minute threshold | Procedure author | Read from the `*_REACH_FREQ_TS` source |
| N-05 | Median age basis (MIT age bands vs NRLD respondent age) | Tatiana Rocha | MIT age bands, monthly |
| N-10 | Expose Panel vs Big Data + Panel as a choice, or report one methodology | Heather Coghill | Report one (BR-SH-14); keep the dimension for analysis |
| NG-D1 | Power BI on the Cube SQL API vs a Quick rebuild | Product + BI | Power BI on Cube (custom visuals) |
| NG-D2 | Pre-2024-04 history: Panel backfill (doc 02) is needed for YoY before Apr 2025 | Research | Yes, reuse `mit_panel_bronze` |

## 12. Backlog (proposed Jira stories, under epic CARL-11)

| Story | Summary | Depends on |
| --- | --- | --- |
| NGR-01 | TMDL export + measure DAX | N-01 |
| NGR-02 | NRLD Prod promotion + Glue registration (NB-01) | CARL-2952 |
| NGR-03 | NRLD dedupe / late-arrival rules (NB-03) | NGR-02 |
| NGR-04 | NRLD column dictionary + AMRLD→NRLD map + marketbreak availability (NB-02, 05, 06) | NGR-02 |
| NGR-05 | `ref_network_wbd_attributes` seed + logos to S3 | N-02; doc 00 `dim_network` |
| NGR-06 | Shared dims (doc 00) | — |
| NGR-07 | `mit_timeperiod_qh_demo` | NGR-06 |
| NGR-08 | Shared MIT telecast Silver (doc 00) | NGR-06 |
| NGR-09 | `ngr_fct_avg_audience_*` | NGR-07, NGR-05 |
| NGR-10 | `ngr_fct_program_telecast*` | NGR-08, NGR-01 |
| NGR-11 | Universe + median age | NGR-07 |
| NGR-12 | Reach / frequency / time spent on NRLD | NGR-03, NGR-04 |
| NGR-13 | Audience profiles on NRLD (config-driven) | NGR-04, NGR-12 |
| NGR-14 | `nextgen_research_gold` DAG + availability | NGR-07..13 |
| NGR-15 | DQ gates (section 9) | NGR-07, NGR-03 |
| NGR-16 | Cube `ngr_view_*` | NGR-09..13 |
| NGR-17 | Rebuild selectors / presentation in BI | NGR-16 |
| NGR-18 | Parity harness + cutover decision | NGR-09..17 |
| NGR-19 | Register products; retire Snowflake `NEXT_GEN` | NGR-18 |
| NGR-20 | Confirm hidden-page scope | N-03 |
