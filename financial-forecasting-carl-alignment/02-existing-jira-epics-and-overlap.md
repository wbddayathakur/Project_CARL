# 02 — Existing Jira epics and overlap

Read live from `wbdprod.atlassian.net`, project CARL, on 21 Oct 2026. No tickets were changed.

## Conclusion

**No existing epic covers the DF Financial Forecasting pipeline** (Snowflake share → Databricks → DF Iceberg → QuickSight capacity forecast). Two "Finance forecast" epics exist, but they are a different workstream. The source-side dependencies already have epics (FreeWheel Bronze/Silver, Operative Bronze/Silver). The proposal is **one new epic** plus stories linked to those dependency epics. See [03](03-proposed-epic-and-story-map.md).

## Epics found

### Finance workstream (adjacent, not the same)

| Key | Summary | Status | Assignee | Scope in one line |
|---|---|---|---|---|
| CARL-1364 | Finance Forecasting Pacing Dashboard | In Progress | Arlene Rose | QuickSight-native weekly Finance **booked revenue / pipeline / forecast pacing** dashboard; Phase 1b adds Finance's WRR/SAP forecast feed. Out of scope: building the forecast model. |
| CARL-1479 | Finance Forecast Feed | In Progress | Arlene Rose | Ingest the **EPM forecast** (OTB, open, pipeline, forecast, digital hedge) weekly via CSV/email. Labelled "Highly Sensitive / SOX". 8 children: 2 Done, 6 In Progress. Parent: CARL-1476 (SharePoint Based Data Feed, In Triage). |

Children of CARL-1364 / CARL-1479 (for reference): CARL-1365 (Done), CARL-1366, CARL-1688 (Done), CARL-3643 *Linear and Digital Forecast Table (Silver)* (To Do, description is a one-line placeholder), CARL-3951, CARL-3952, CARL-4095; and CARL-1488 (Done), CARL-3950 *Silver Table: fact_finance_weekly_quarter_forecast*, CARL-3992 (Done), CARL-4100–4104 (email-to-Bronze, In Review).

**Why these are not the DF pipeline:** they build CARL-native Gold and a QuickSight pacing dashboard from Operative, iDeal, Salesforce and WRR/SAP. The DF pipeline produces **capacity** forecast tables (`CAPACITY_FORECAST_FINANCE`, `CAPACITY_HISTORY_FINANCE`) in Snowflake from FreeWheel-centric views. Please confirm (Q5 in the README). **Risk of overlap:** both end in QuickSight "Finance forecasting" content, and CARL-1364 aims to align definitions across sources, so the two could drift apart.

### Source dependency epics (reuse, do not duplicate)

| Key | Summary | Status | Assignee | Relevance |
|---|---|---|---|---|
| CARL-746 | Ingest Freewheel Data (Bronze) | Done | Hong Zhang | 64 log tables, done 1 Jul |
| CARL-1380 | Ingest - FreeWheel API Bronze | Ready for Testing | Hong Zhang | Candidate for `API_PLACEMENTS_V` and video rating/duration; priority lowered P1 → P2 |
| CARL-1756 | Ingest Freewheel Data (Bronze Phase 2) | Ready for Testing | Sean Malek | Data never before in WBD; P2 |
| CARL-2887 | Freewheel (Silver) | In Progress | Hong Zhang | Phase 1 target 15 Dec; 28 children |
| CARL-744 | Ingest Operative Data (Bronze) | Done | Diana Saafi | 81 + 7 tables |
| CARL-2888 | Operative One (Silver) | To Do | Mike Hodge | 3 children (CARL-2889, 2890, 2891), all To Do and unassigned |
| CARL-628 | Digital Forecasting Data Ingestion | Done | Hong Zhang | DAAP_RPT Bronze; Silver blocked downstream |
| CARL-4001 | [Cross Project Support] DDL-forecasting | To Do | Avinaag Bonam | DDL forecasting; 5 children |
| CARL-4097 | [Cross Project Support] Linear-forecasting | To Do | Avinaag Bonam | Linear forecasting; created 7 Oct |

### Stories under those epics that directly affect this pipeline

| Key | Summary | Status | Why it matters |
|---|---|---|---|
| CARL-3509 | operative_bronze findings from Digital Forecasting review | To Do (Avinaag Bonam) | Three findings against `operative_bronze`: malformed column names (15 columns, 9 tables), missing `source` column (mirrors `om_con_dy_v`), all columns typed string. **Directly blocks FF-07 and FF-08.** |
| CARL-3807 | Develop FreeWheel dim_video in Silver | Ready for Testing | Candidate for object 5 |
| CARL-3803 | Develop FreeWheel dim_placement in Silver | Ready for Testing | Candidate for object 7 |
| CARL-3804 / CARL-3805 | dim_site / dim_site_section in Silver | Ready for Testing | Partial cover for objects 2 and 4 |
| CARL-3809 | fact_ad_stream_impression in Silver | In Progress | **Not** the sellable revenue fact; impression grain |
| CARL-4222 | add dim_postal_code_package, fold d_reseller into dim_network, add d_video rating and air_date | To Do | Possible overlap with `RESELLER_TYPE_MAP`; adds fields to `dim_video` |
| CARL-3852 | Bring freewheel_bronze and freewheel_silver under carl-infra Glue and Lake Formation | **Archive** | The closest existing story to the prod Glue registration gap (G1). Archived, so it is not being worked. See FF-09. |
| CARL-580 | Configure Catalog Federation — Snowflake to Glue | Done (story) | Weekly status of 19 Oct still lists federation AT RISK with manual-sync fallback. Reconcile before FF-13. |

## Where each proposed story would be filed

| Proposed story | File under | Notes |
|---|---|---|
| FF-01, FF-02, FF-04, FF-05, FF-06, FF-07, FF-08, FF-10, FF-11, FF-12, FF-14, FF-15, FF-16, FF-17 | **New epic** "Financial Forecasting — CARL Source Alignment" | DF-owned per Daya's note |
| FF-03 | New epic (DF decision) with linked story under CARL-2887 if Silver Phase 1.1 is chosen | |
| FF-09 | CARL-2887 or CARL-746 (CARL-owned, linked to new epic as a dependency) | Re-open or replace archived CARL-3852 |
| FF-13 | New epic, linked to CARL-580 | |

## Duplicate check on the draft stories

| Draft | Closest existing | Verdict |
|---|---|---|
| FF-07 | CARL-2888 / CARL-2891 (Op1 Silver pipeline) | Not a duplicate: FF-07 is a forecast-specific consumer story; it **depends on** Op1 Silver and CARL-3509 |
| FF-09 | CARL-3852 (Archive) | Overlap; decide whether to un-archive or create a new story referencing it |
| FF-03 | CARL-2887 children | Not a duplicate: those 18 dims exclude the site-group, video-group and listings tables |
| FF-12 | none | New |
| FF-17 | Registry proposals for Ad Products / Market Share | Unrelated; no Finance capacity view is proposed |
