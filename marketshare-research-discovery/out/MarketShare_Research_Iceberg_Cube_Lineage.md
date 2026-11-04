# Research Market Share: Iceberg + Cube discovery

Jira: [CARL-3776](https://wbdprod.atlassian.net/browse/CARL-3776) (epic [CARL-3775](https://wbdprod.atlassian.net/browse/CARL-3775)). Generated 12 Oct 2026 by `build_workbook.py`; detail in `MarketShare_Research_Discovery_Iceberg_Cube.xlsx`.

## Priority needs (P0)

- **PN-01 Join Nielsen MIT C3 impressions to Guideline:Telecast spend at telecast level**: Silver match bridge (Guideline telecast to Nielsen telecast, +/- N minutes) feeding two Gold facts that share a telecast key: supply (impressions) and demand (spend). Keeping them separate stops impressions being multiplied by buy-type rows.
- **PN-02 Numbers within +/-3% of source, with errors caught before analysts start**: DQ framework (Data Quality Plan sheet) using write-audit-publish: Gold is only published when blocker checks pass. Results land in an Iceberg dq_results table, and a monthly reconciliation runs against vendor UIs and the VAMI baseline.
- **PN-03 Stitched viewership: Panel Only through 28-Sep-2025, Big Data + Panel from 29-Sep-2025, and analysts can always tell which**: Silver fct_mit_telecast_c3 carries both methodologies with a viewing_methodology column. An is_reporting_methodology flag is driven by a config row (the cutover date), not hard-coded. Overlap window 05-Aug-2024 to 31-Dec-2025 is kept for comparison.
- **PN-04 Ad Intel spend without duplicates or stale revisions**: Phase 1: Silver from marketshare_bronze.factadintel with duplicate detection and an is_static_segment flag. Phase 2: direct Ad Intel occurrence feed with a MERGE on Nielsen's occurrence key so revisions replace rather than append.
- **PN-05 One internal taxonomy for network, ownership, portfolio, genre and reporting status, replacing XREF_NETWORK and VAMI_REPORTING_NETWORKS**: Conformed dim_network (effective-dated) built from marketshare_bronze.dimnetwork, which already has ownershipgroup and reportingstatus. Add a managed Guideline-to-Nielsen network crosswalk with explicit cardinality, plus dim_program_taxonomy from dimnetworkprogramnamemapping.
- **PN-06 Notifications (delivery, ETL done, errors) and a visible 'last updated'**: Delivery manifest table, schema-contract check at landing, a data_freshness table per source and layer, and alerts to the Marketplace Insights channel. The freshness tile goes on every Quick dashboard.

Field coverage from the intake: 113 fields, 47 available on CARL Bronze today, 30 blocked on Guideline landing.

## Target lineage

Green = in CARL Prod today, red = not yet landed.

```mermaid
flowchart LR
  subgraph SRC[Sources]
    GT[Guideline Telecast<br/>S3 txt.gz monthly]
    GA[Guideline AccuTV<br/>S3 txt.gz monthly]
    MP[Nielsen MIT Panel Only<br/>AMS_ICUE_SHARE.MIT]
    MB[Nielsen Big MIT<br/>SHARE_PROD_BIG_MIT]
    MS[MarketShare<br/>AMS BI, weekly]
    TX[Research taxonomy<br/>MarketShare S3 rules engine]
  end
  subgraph BR[CARL Bronze - Iceberg]
    GB[guideline_bronze<br/>telecast_delivery, accutv_delivery, delivery_manifest]:::gap
    PB[mit_panel_bronze]:::gap
    BB[big_mit_bronze - Prod]:::ok
    MSB[marketshare_bronze - Prod<br/>factadintel, factprogram, dims]:::ok
  end
  subgraph SV[marketplace_insights_silver]
    CAL[dim_broadcast_calendar]
    DN[dim_network SCD2 + ref_network_crosswalk]
    DP[dim_program_taxonomy]
    C3[fct_mit_telecast_c3]
    GS[fct_guideline_telecast_spend + bounce]
    GAS[fct_guideline_accutv_spend]
    MT[match_telecast_guideline_mit]
    AI[fct_adintel_occurrence]
  end
  subgraph GD[marketplace_insights_gold - published by WAP]
    SUP[fct_telecast_supply]
    DEM[fct_telecast_demand]
    CAT[fct_category_spend]
    ADS[fct_adintel_spend]
    DQ[dq_results + data_freshness]
  end
  subgraph SEM[Cube]
    V1[marketplace_view_telecast_supply_demand]
    V2[marketplace_view_category_spend]
    V3[marketplace_view_adintel_spend / _sales]
    V4[marketplace_view_data_freshness]
  end
  Q[Amazon Quick<br/>dashboards + AI chat]
  GT --> GB
  GA --> GB
  MP --> PB
  MB --> BB
  MS --> MSB
  TX --> MS
  GB --> GS
  GB --> GAS
  PB --> C3
  BB --> C3
  MSB --> DN
  MSB --> DP
  MSB --> AI
  C3 --> MT
  GS --> MT
  DN --> MT
  C3 --> SUP
  MT --> DEM
  GS --> DEM
  GAS --> CAT
  AI --> ADS
  DP --> SUP
  CAL --> SUP
  SUP --> V1
  DEM --> V1
  CAT --> V2
  ADS --> V3
  DQ --> V4
  V1 --> Q
  V2 --> Q
  V3 --> Q
  V4 --> Q
  classDef ok fill:#C6EFCE,stroke:#2e7d32
  classDef gap fill:#FFC7CE,stroke:#c62828
```

## Gold ERD

```mermaid
erDiagram
  dim_broadcast_calendar ||--o{ fct_telecast_supply : broadcast_date
  dim_network ||--o{ fct_telecast_supply : network_key
  dim_program ||--o{ fct_telecast_supply : program_key
  dim_demo ||--o{ fct_telecast_supply : demo_code
  fct_telecast_supply ||--o{ fct_telecast_demand : telecast_key
  dim_network ||--o{ fct_category_spend : network_key
  dim_broadcast_calendar ||--o{ fct_category_spend : air_date
  dim_network ||--o{ fct_adintel_spend : network_key
  dim_program ||--o{ fct_adintel_spend : program_key
  dim_advertiser_brand ||--o{ fct_adintel_spend : advertiser_brand_key
  dim_broadcast_calendar ||--o{ fct_adintel_spend : ad_date
  fct_telecast_supply {
    string telecast_key PK
    string demo_code PK
    date broadcast_date
    timestamp airing_minute
    string viewing_methodology
    double gross_impressions
    int commercial_program_duration
    int duration
    boolean is_breakout
    boolean is_short_duration
  }
  fct_telecast_demand {
    string telecast_key FK
    string buy_type
    string adu
    int spot_length
    decimal gross_media_spend
    double eq30_spot_count
    string delivery_id
    int match_offset_minutes
  }
  dim_network {
    string network_key PK
    string network_label
    string network
    string ownership_group
    string network_type
    boolean reporting_status
    date effective_from
    date effective_to
  }
  fct_adintel_spend {
    date ad_date
    string network_key FK
    string program_key FK
    string advertiser_brand_key FK
    string media_type
    int duration
    decimal spend
    int units
    boolean is_static_segment
  }
```

## Data quality gate

```mermaid
flowchart LR
  L[File lands] --> C{Schema contract<br/>DQ-02/03}
  C -- fail --> QZ[Quarantine + alert]
  C -- pass --> B[Bronze append<br/>partition = delivery_id]
  B --> S[Silver build on audit branch]
  S --> T{Blocker checks<br/>DQ-08,09,11,12,14,15,17,21}
  T -- fail --> A[Alert, main unchanged,<br/>Quick shows last good data]
  T -- pass --> P[Fast-forward main<br/>update data_freshness]
  P --> R[Weekly audit + monthly +/-3% reconciliation]
```

## Decisions needed first

- **Q-01** custom_mit2 ranks breakout airings first in code but the doc says non-breakout first. Which should receive Guideline spend? (Eric Yarsinsky / Maggie Mullane)
- **Q-02** Cutover: Panel Only through 28-Sep-2025 and Big MIT from 29-Sep-2025? (Pain_Points says 26-Sep and '2026') (Eric Yarsinsky)
- **Q-03** Panel Only history: one-time backfill from AMS_ICUE_SHARE.MIT, or use marketshare factprogram? (AMS BI (Hong Zhang, Sean Malek) + Research)
- **Q-04** Ad Intel: can CARL get the raw occurrence feed (and Nielsen's occurrence id)? Is the factAdIntel duplicate fix confirmed for all years? (AMS BI (Sean Malek))
- **Q-05** Ad Intel CTV: who procures and owns the ingestion? (Research sponsor + AMS BI)
- **Q-06** Truth source: vendor file or vendor UI? (Research + CARL)
- **Q-07** CARL read access to s3 aws-ams-bi-marketshare-developer/DataOutgoing, or redirect Guideline delivery to CARL landing? (AMS BI + CARL DE)
- **Q-08** Bounce depth: 3 or 6 final deliveries? Is 'final' = last file before the next cycle's first file? (Eric Yarsinsky)
