# Research Data Requirements: Bronze, Silver and Gold on CARL Iceberg + Cube

| # | Document | Objective |
| --- | --- | --- |
| 00 | [Shared foundation](00_shared_foundation.md) | Naming, Iceberg standards, load patterns, conformed dimensions, shared Nielsen MIT Silver, DQ / freshness, Cube conventions |
| 01 | [MarketShare](01_marketshare_data_requirements.md) | Taxonomy (Rules Engine + 4 mapping files), advertiser, Nielsen Ad Intel spend → Power BI NextGen Ad Spend, Looker dims |
| 02 | [Market Research / Marketplace Insights](02_market_research_marketplace_insights_data_requirements.md) | Looker VAMI 3 replacement, Marketplace Imps query, Guideline Telecast / AccuTV, telecast match |
| 03 | [NextGen Research dashboard](03_nextgen_research_dashboard_data_requirements.md) | Power BI NextGen Research on MIT + NRLD (MRI Phase 2) |

```
Bronze (as delivered, all-string where files)        Silver research_silver (conformed, deduped)        Gold research_gold          Cube
big_mit_bronze (+dimdate) ───────────────┐           dim_broadcast_calendar, dim_network,               dim_* (published)          mi_view_*
mit_panel_bronze (one-time) ─────────────┤──────────▶ dim_program_taxonomy, dim_telecast,    ─────────▶ mi_fct_* (Market Research) ms_view_*
marketshare_bronze ──────────────────────┤           fct_mit_telecast_viewing, mit_timeperiod_qh_demo,   ms_fct_* (MarketShare)     ngr_view_*
marketshare_taxonomy_bronze ─────────────┤           ref_* (rules, distributor, genre, product,          ngr_fct_* (NextGen)
guideline_bronze ────────────────────────┤           crosswalk, events, config), Guideline spend,        ops_dq_results,
nrld_bronze (promote) ───────────────────┤           match bridge, NRLD person-level                     ops_data_freshness
mri_bronze / mri_streaming_bronze (P2) ──┘
```

`profile_taxonomy.py` reproduces the taxonomy profiling findings (doc 01 section 3.4). Run it against a local copy of `marketshare-prod/prod/mapping/`.
