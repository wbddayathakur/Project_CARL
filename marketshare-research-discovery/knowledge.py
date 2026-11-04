"""Curated discovery content for Research Market Share (intake Use Case 3(a)).

Facts are cited to the intake workbook, the Confluence pages read on 09-Oct, or
the CARL Glue catalog. Anything marked Proposed in the Status/Confidence column
is a design recommendation and must not be read as confirmed.
"""

JIRA_STORY = "https://wbdprod.atlassian.net/browse/CARL-3776"
JIRA_EPIC = "https://wbdprod.atlassian.net/browse/CARL-3775"

INTAKE = "CARL Discovery Intake v1.1, Use Case 3(a) Marketplace Performance Tracking (file named 'In-Flight Ops Monitoring Dashboard_7.24.26')"
CONF_MS = "Confluence: MarketShare: Pipeline + Dataset (v44)"
CONF_VAMI = "Confluence: VAMI Pipeline / Pipeline Step: Snowflake VAMI table (MIT_ADINTEL_SMI_V3)"
CONF_SMI2 = "Confluence: custom_smi2 (v4)"
CONF_MIT2 = "Confluence: custom_mit2 (v2)"
CONF_FP = "Confluence: FactProgram (WIP) (MarketShare) (v23)"
CONF_FA = "Confluence: FactAdIntel (MarketShare) (v18)"
CONF_S3 = "Confluence: MarketShare S3: About & How to Access"
CATALOG = "iceberg-catalog-agent/out/iceberg-live-2026-10-07.csv"
COLUMNS = "evidence/bronze_columns_prod_catalog_2026-08-27.json (Glue, Prod)"

PANEL_CUTOVER_LAST_DAY = "2025-09-28"
BIG_MIT_FIRST_DAY = "2025-09-29"

# ---------------------------------------------------------------------------
# Priority needs (acceptance criterion 1)
# ---------------------------------------------------------------------------
PRIORITIES = [
    # id, priority, need, intake ref, why it ranks here, CARL response, pipeline
    ("PN-01", "P0", "Join Nielsen MIT C3 impressions to Guideline:Telecast spend at telecast level",
     "2.1, 2.2, 3.7, 3.9; Metrics_Dims use case 1",
     "Called out as 'the key value'. Benchmarks, share and power ratio for exec/CFO/Board narratives all depend on it. The current VAMI join is not in use because duplicated Ad Intel rows corrupted it.",
     "Silver match bridge (Guideline telecast to Nielsen telecast, +/- N minutes) feeding two Gold facts that share a telecast key: supply (impressions) and demand (spend). Keeping them separate stops impressions being multiplied by buy-type rows.",
     "1"),
    ("PN-02", "P0", "Numbers within +/-3% of source, with errors caught before analysts start",
     "2.15, 2.19, 2.22, 2.23",
     "This is the success criterion and the Definition of Done. Today errors are found by chance, and duplicates inflate spend.",
     "DQ framework (Data Quality Plan sheet) using write-audit-publish: Gold is only published when blocker checks pass. Results land in an Iceberg dq_results table, and a monthly reconciliation runs against vendor UIs and the VAMI baseline.",
     "All"),
    ("PN-03", "P0", "Stitched viewership: Panel Only through 28-Sep-2025, Big Data + Panel from 29-Sep-2025, and analysts can always tell which",
     "2.19, 2.24, 2.25; Pain_Points (MIT)",
     "Nielsen changed methodology and MarketShare factProgram was never updated for Big MIT. Without this there is no continuous 5-10 year trend.",
     "Silver fct_mit_telecast_c3 carries both methodologies with a viewing_methodology column. An is_reporting_methodology flag is driven by a config row (the cutover date), not hard-coded. Overlap window 05-Aug-2024 to 31-Dec-2025 is kept for comparison.",
     "1"),
    ("PN-04", "P0", "Ad Intel spend without duplicates or stale revisions",
     "2.15, 2.19; Pain_Points (Ad Intel); Jira CARL-3776 comment 'Ad Intel - Data'",
     "Duplicated factAdIntel rows already broke VAMI. Ad Intel also feeds the only Ad Sales-wide dashboard (NextGen Advertising Spending).",
     "Phase 1: Silver from marketshare_bronze.factadintel with duplicate detection and an is_static_segment flag. Phase 2: direct Ad Intel occurrence feed with a MERGE on Nielsen's occurrence key so revisions replace rather than append.",
     "3"),
    ("PN-05", "P0", "One internal taxonomy for network, ownership, portfolio, genre and reporting status, replacing XREF_NETWORK and VAMI_REPORTING_NETWORKS",
     "2.19, 2.25; Pain_Points (Taxonomy); Data_Sources_Tables_Details rows 15-17",
     "Both tables are unmaintained and Research calls them 'a major bottleneck'. Every pipeline slices by these dimensions.",
     "Conformed dim_network (effective-dated) built from marketshare_bronze.dimnetwork, which already has ownershipgroup and reportingstatus. Add a managed Guideline-to-Nielsen network crosswalk with explicit cardinality, plus dim_program_taxonomy from dimnetworkprogramnamemapping.",
     "All"),
    ("PN-06", "P0", "Notifications (delivery, ETL done, errors) and a visible 'last updated'",
     "3.12, 2.22 Monitoring",
     "Silent Snowflake refresh failures on Guideline column changes are a named pain point. It is also a Non-Functional Requirement.",
     "Delivery manifest table, schema-contract check at landing, a data_freshness table per source and layer, and alerts to the Marketplace Insights channel. The freshness tile goes on every Quick dashboard.",
     "All"),
    ("PN-07", "P1", "Guideline:AccuTV queryable with internal taxonomy",
     "3.7 item 2, 3.9; Pain_Points (AccuTV)",
     "No downstream use today: analysts rely on the Apollo DataMiner UI. The MVP is just 'in the same system'.",
     "guideline_bronze.accutv_delivery, then Silver current-final, then Gold fct_category_spend joined to dim_network and the calendar.",
     "2"),
    ("PN-08", "P1", "Broadcast calendar with weeks-in-period normalisation and 6a-6a vs 24h dates",
     "Metrics_Dims calendar rows; Pain_Points (Other/General)",
     "Year-over-year comparisons are wrong when a broadcast month has 4 vs 5 weeks. This applies to all three pipelines.",
     "dim_broadcast_calendar (one row per date) with weeks_in_bc_month/quarter/year and season. Shared with the NextGen Research migration, which needs the same dimension.",
     "All"),
    ("PN-09", "P1", "Keep the last 3-6 final Guideline deliveries to measure 'bounce'",
     "2.19; Examples tab",
     "Every Guideline delivery restates full history. Gold must use only the latest; analysts want to see how estimates move.",
     "Bronze keeps every delivery partitioned by delivery_id. The manifest marks is_final_for_cycle. Silver fct_guideline_spend_bounce holds the last N final deliveries aggregated to network x broadcast month x buy type.",
     "1, 2"),
    ("PN-10", "P1", "Queryable metric/dimension definitions (SQL and AI) and Quick dashboards on Gold",
     "3.9, 3.10, 2.22 Usability",
     "Research wants AI chat and self-serve without re-deriving logic. The three Quick asks on CARL-3776 depend on it.",
     "Four Cube views (Cube Semantic Layer sheet) over Gold. Quick datasets read Cube/Athena; Cube /meta drives the AI-accessible definitions.",
     "All"),
    ("PN-11", "P1", "Data dictionaries, FAQ, flow diagrams, business-rule docs",
     "2.23 Documentation, 3.9",
     "Part of the Definition of Done; today none exist for Guideline.",
     "Generated from the iceberg-catalog-agent registry (products.yaml / cube_model.yaml) and published to Confluence weekly.",
     "All"),
    ("PN-12", "P1", "History: 5 years minimum, 10 ideal",
     "2.17, 2.2",
     "Guideline starts 01-Jan-2017, so 9 years is the ceiling in 2026. MIT Panel Only goes back to 29-Jun-2015.",
     "Backfill from 2017-01-01 for all pipelines; MIT from 2015 where it is cheap. Ad Intel depth is to be confirmed (FactAdIntel notes 'rolling 5 year?').",
     "All"),
    ("PN-13", "P2", "Ad Sales-facing Ad Intel dashboard with role-based access",
     "2.2 'if possible', 3.11",
     "Stretch goal. It has the widest audience (all Ad Sales, Finance), so access rules matter.",
     "Restricted Cube view marketplace_view_adintel_sales with a curated dimension list chosen by Marketplace Insights. Row/role access is enforced in Cube (queryRewrite) and Quick.",
     "3"),
    ("PN-14", "P2", "Clean program names and group cyclical sports events",
     "Pain_Points (MIT); 2.3 lists the sports taxonomy as an extension",
     "Real pain, but the sports taxonomy build is explicitly out of scope.",
     "Silver program_name_normalised (rule-based: strip network suffix, dates, 'SP-', article inversion). Expose the existing sport/sporttype/sportbrand/eventtype columns from dimnetworkprogramnamemapping. The full sports taxonomy stays backlog.",
     "1, 3"),
    ("PN-15", "P2", "Nielsen Ad Intel CTV",
     "2.2, About_Data_Sources row 7, 2.24",
     "Procurement and ownership are not decided, so nothing can be built yet.",
     "Reserve media_type in the Ad Intel model so CTV lands without a remodel. Track as a decision.",
     "3"),
]

# ---------------------------------------------------------------------------
# Key findings
# ---------------------------------------------------------------------------
FINDINGS = [
    ("F-01", "MarketShare and Big MIT are already in CARL Prod Bronze",
     "marketshare_bronze: 10 tables, last Prod commit 01-Oct 09:05-09:25 UTC. big_mit_bronze: 8 tables, last Prod commit 07-Oct 05:31-05:47 UTC.",
     "Pipelines 1 (MIT side) and 3 can be modelled on CARL data now. No new Nielsen ingestion is needed to start.", CATALOG, "High"),
    ("F-02", "Guideline (SMI) Telecast and AccuTV are not in CARL at all",
     "No guideline/smi database in Glue. Today the files go S3 (aws-ams-bi-marketshare-developer / DataOutgoing) into Snowflake ICUE_DATAMART.ICUE_STAGING via Snowpipe and dynamic tables.",
     "Guideline landing is the critical path for Pipelines 1 and 2. It needs a read grant on the AMS BI bucket, or a direct vendor drop into CARL landing.", CATALOG + "; intake Data_Sources_Tables_Details", "High"),
    ("F-03", "Panel Only MIT reaches CARL only through MarketShare factprogram",
     "big_mit_bronze has the Big Data + Panel feed. Panel Only raw (AMS_ICUE_SHARE.MIT) is not landed. marketshare_bronze.factprogram is Panel Only and was never moved to Big MIT.",
     "Pick one: (a) one-time backfill of AMS_ICUE_SHARE.MIT program_viewing/program_descriptor through 31-Dec-2025, frozen afterwards (Research preference), or (b) use factprogram for the Panel history (lower trust).", CATALOG + "; " + CONF_FP + "; intake 2.19", "High"),
    ("F-04", "Bronze factadintel cannot implement 'revision replaces original'",
     "Bronze factadintel has 21 columns: surrogate keys only (_addatesk, _adtimesk, _networksk, _programdescriptorsk, _primary/secondary/tertiaryadvertiserbrandsk, _mediatypesk, _adintelattributesk), plus units, spend, duration, _delivereddatafileid, isactive, hash_value. There is no Nielsen occurrence id. Rows before ~10-Jun-2024 are a static copy whose _networksk is never updated.",
     "CARL can detect duplicates and filter isactive, but cannot prove which row is the revision. A full fix needs the Ad Intel occurrence feed (Phase 2). Until then, flag is_static_segment and report a duplicate count.", COLUMNS + "; " + CONF_FA, "High"),
    ("F-05", "Most of the internal taxonomy is already in CARL",
     "dimnetwork: ownershipgroup, network (continuous name), networkgroup, networkdivision, networktype, mediatypedescription, reportingstatus, mitnetworkid/cd. dimnetworkprogramnamemapping: programgroupsummary/detail, fourpartgenre, sport, sporttype, sportbrand, eventtype. dimdaypart: smidaypart, nntvdaypart, matcheddaypart. dimadvertiserbrand: internal category/subcategory next to Nielsen major/sub category.",
     "dimnetwork.reportingstatus can replace VAMI_REPORTING_NETWORKS. dimdaypart already aligns Guideline and Nielsen dayparts, which answers 'may not align' (Metrics_Dims row 31). Only the Guideline-to-Nielsen network crosswalk (XREF) is missing.", COLUMNS, "High"),
    ("F-06", "XREF_NETWORK fans out spend rows",
     "custom_smi2: 'Amazon NFL' maps to both PV and AMZ, which doubles rows. A later inner join on MIT network and time drops the duplicates.",
     "Spend conservation then depends on the join. The CARL crosswalk must declare cardinality and an effective date per mapping, and DQ-15 must prove spend in = spend out.", CONF_SMI2, "High"),
    ("F-07", "Breakout ranking: code and documentation disagree",
     "custom_mit2 code: row_number() over (partition by network_label, airing_datetime order by is_breakout desc), so the breakout row ranks 1 (comment: 'VAMI 2 assigned SMI spend to the breakout airing'). The prose on the same page says the non-breakout row gets rank 1.",
     "This decides which Nielsen row receives Guideline spend. Confirm with Eric Yarsinsky / Maggie Mullane before porting (Q-01).", CONF_MIT2, "High"),
    ("F-08", "Cutover dates are inconsistent inside the intake",
     "2.19 and 2.24: Panel Only through 9/28/2025, Big MIT from 9/29/2025. Pain_Points (MIT): 'through 9/26/2025 and then Big MIT for 9/28/2026 onward'.",
     "Treat the cutover as a config row, defaulting to 28-Sep / 29-Sep-2025, and confirm (Q-02).", INTAKE, "High"),
    ("F-09", "SMI duplicate tie-break silently drops spend",
     "custom_smi2: QUALIFY row_number() over (partition by nielsennetworkcd, minute(programstarttime) order by sum(grossmediaspend) desc) = 1 keeps only the higher of two concurrent spends.",
     "Port it, but write the dropped spend to a reject table and report it (DQ-17), so the +/-3% reconciliation can explain itself.", CONF_SMI2, "High"),
    ("F-10", "All requested demos can be built from Bronze buckets",
     "big_mit_bronze.program_viewing has females/males {2_5 ... 50_54, 55_64, 65plus}_delivery plus commercial_program_duration, end_airing_datetime, time_shifted_viewing_type, nielsen_data_type.",
     "P/F/M 2+, 18+, 25+, 55+, 18-49 and 25-54 are all sums of buckets, so the Gross Impressions formula is a Fit. Delivery units (thousands or persons) must be confirmed before CPM is defined (Q-09).", COLUMNS, "High"),
    ("F-11", "Calendar dimension is missing in CARL",
     "COMMON dimDATE/dimTIME (AMS_ICUE_SHARE.COMMON) is not in Glue. MarketShare factprogram only carries _broadcastdatesk.",
     "Build dim_broadcast_calendar once, shared with the NextGen migration. Use dimDATE as a validation oracle.", CATALOG, "High"),
    ("F-12", "Snowflake SQL access conflicts with an Iceberg-first target",
     "2.22 Usability asks for SQL 'in Snowflake' and in Quick.",
     "Default: Athena SQL + Cube + Quick on CARL Iceberg. If Snowflake is required, expose Gold through a Snowflake Iceberg catalog integration, read-only (Q-13).", INTAKE, "Proposed"),
    ("F-13", "Three Quick asks sit on CARL-3776",
     "Your CARL-3776 comment: (1) Eric/Maggie SMI + Cube market share remodel to Quick, (2) NextGen dashboard to Quick, (3) Time buy Looker report to Quick.",
     "(1) is this workbook. (2) is covered by nextgen-research-discovery/ and shares dim_broadcast_calendar and dim_network. (3) has no intake yet; raise one (Q-16).", "Jira CARL-3776", "High"),
]

# ---------------------------------------------------------------------------
# Source inventory
# ---------------------------------------------------------------------------
SOURCES = [
    # id, source, vendor, current location, in CARL today, preferred access, trust, cadence / lag, revisions, history, disposition
    ("S-01", "Guideline:Telecast", "Guideline (SMI)",
     "S3 aws-ams-bi-marketshare-developer/DataOutgoing: US_SMI_Telecast_Data_201701_[end]_[delivered].txt.gz -> Snowflake ICUE_DATAMART.ICUE_STAGING.STG_SMI_US_SMI_TELECAST_DATA (via datastrategy.research.smi_telecast_pipe_load)",
     "No", "Direct file (defer to CARL)", "Med/High",
     "~Monthly, 20th-31st; 3-4 weeks after month end; occasional re-delivery",
     "Each file restates full history from 2017-01; recent months change ('bounce')", "2017-01-01 onward",
     "Land every delivery to guideline_bronze.telecast_delivery with a manifest. Gold uses the latest final delivery."),
    ("S-02", "Guideline:AccuTV", "Guideline (SMI)",
     "S3 same bucket: SMI_US_AccuTV_[delivered]_PSC.txt.gz -> Snowflake ICUE_STAGING.STG_SMI_US_ACCUTV (via smi_accutv_pipe_load)",
     "No", "Direct file (defer to CARL)", "Med/High", "As S-01", "As S-01", "2017-01-01 onward",
     "Land to guideline_bronze.accutv_delivery. Layout/dictionary not documented (Q-18)."),
    ("S-03", "Nielsen MIT: Panel Only", "Nielsen",
     "Snowflake WM_DATASTRATEGY.AMS_ICUE_SHARE.MIT (program_viewing, program_descriptor); also MarketShare FACTPROGRAM/DIMPROGRAMDESCRIPTOR",
     "Indirect only: marketshare_bronze.factprogram / dimprogramdescriptor", "Direct (preferred by Research)", "Med/High direct; Low/Med via MarketShare",
     "Daily + weekly; ~2 weeks after broadcast month end", "Unknown whether Nielsen reissues history (ask AMS BI)", "2015-06-29 to 2025-12-31 (ended)",
     "One-time backfill to mit_panel_bronze (proposed) and freeze; or use factprogram (Q-03)."),
    ("S-04", "Nielsen MIT: Big Data + Panel (Big MIT)", "Nielsen",
     "Snowflake SHARE_PROD_BIG_MIT.MIT -> CARL big_mit_bronze (landing_to_bronze_iceberg_bigmit)",
     "Yes, Prod: intab, program_descriptor, program_descriptor_serial, program_viewing, program_viewing_quarterhour, program_viewing_sellingdemos, timeperiod_quarterhour, universe_estimate",
     "Direct (preferred)", "Med/High", "Catalog: daily 13:30/17:30/19:30 UTC; last commit 07-Oct", "Unknown (ask AMS BI)", "2024-08-05 onward",
     "Primary source for C3 impressions from 29-Sep-2025."),
    ("S-05", "Nielsen Ad Intel (Linear)", "Nielsen",
     "Raw occurrence location unknown (Lake5?) -> MarketShare FACTADINTEL + DIMADINTELATTRIBUTE/DIMADVERTISERBRAND/DIMMEDIATYPE -> CARL marketshare_bronze",
     "Yes, Prod via MarketShare (factadintel, dimadintelattribute, dimadvertiserbrand, dimmediatype); weekly, last commit 01-Oct",
     "Direct (preferred, to fix duplicates)", "Low/Med via MarketShare",
     "Daily occurrence files + weekly OCF; pulled Wed evening, refreshed Thursday morning", "Yes: preliminary rows replaced by final; static pre-Jun-2024 segment not updated",
     "Rolling 5 years? (to confirm)", "Phase 1 from marketshare_bronze with DQ; Phase 2 direct occurrence feed (Q-04)."),
    ("S-06", "Nielsen Ad Intel (CTV)", "Nielsen", "Contract expansion in progress", "No", "TBD", "TBD", "TBD", "TBD", "Jan-2024 onward",
     "Out of MVP build. Reserve media_type; decide owner (Q-05)."),
    ("S-07", "Internal taxonomy (MarketShare S3 rules engine)", "WBD (Research)",
     "S3 marketshare-prod/prod/mapping/{input,output}: rules_engine, network, distributormapping, fourpartgenre, productcategories -> MarketShare DIMNETWORK, DIMNETWORKPROGRAMNAMEMAPPING, DIMADVERTISERBRAND",
     "Yes, as outputs: marketshare_bronze.dimnetwork, dimnetworkprogramnamemapping, dimadvertiserbrand, dimdaypart",
     "Defer to CARL (Research open to bypass)", "Med/High", "Wed 9pm ET + on-demand semaphore (3-7 min)", "Edited by Research through Cyberduck; no audit trail", "n/a",
     "Phase 1 consume the CARL Bronze outputs. Later, decide whether CARL owns the rules (Q-15)."),
    ("S-08", "XREF_NETWORK", "WBD (orphaned)", "Snowflake ICUE_DATAMART.ICUE_STAGING.XREF_NETWORK (SMI/AMRLD/Scarlett/Crossroads names)", "No", "Replace", "Low",
     "On command", "Manual", "n/a", "Replace with ref_network_crosswalk seed (effective-dated, explicit cardinality)."),
    ("S-09", "VAMI_REPORTING_NETWORKS", "WBD (orphaned)", "Snowflake ICUE_DATAMART.MARKETPLACE.VAMI_REPORTING_NETWORKS", "No", "Replace", "Low",
     "On command", "Manual", "n/a", "Retire. Use dimnetwork.reportingstatus plus a Guideline-measured flag on the crosswalk."),
    ("S-10", "COMMON dimDATE / dimTIME", "WBD (AMS BI)", "Snowflake AMS_ICUE_SHARE.COMMON (also in SHARE_PROD_BIG_MIT)", "No", "Build in CARL", "High",
     "Static", "n/a", "n/a", "Build dim_broadcast_calendar and dim_time_of_day. Use dimDATE as the validation oracle."),
    ("S-11", "VAMI table MIT_ADINTEL_SMI_V3", "WBD (Research DA)", "Snowflake ICUE_DATAMART.MARKETPLACE (dynamic table, daily 08:00 ET)", "No", "Parity baseline only", "Low/Med",
     "Daily", "Rebuilt", "2017 onward", "Use for the parallel-run parity check (DQ-19), then retire with the Looker VAMI 3 Explore."),
]

# ---------------------------------------------------------------------------
# Iceberg target model (acceptance criterion 2)
# ---------------------------------------------------------------------------
BRONZE = "guideline_bronze"
SILVER = "marketplace_insights_silver"
GOLD = "marketplace_insights_gold"

ICEBERG = [
    # layer, table, grain, key, sources, partition spec, write mode, retention / snapshots, pipeline, status
    ("Bronze", f"{BRONZE}.delivery_manifest", "One row per vendor file received",
     "file_name", "S3 landing listing", "none (small)", "Append",
     "Keep forever", "1, 2", "Proposed"),
    ("Bronze", f"{BRONZE}.telecast_delivery", "One row per source row per delivery (columns as delivered + delivery_id, coverage_end, delivered_date, source_file, row_hash, ingest_timestamp)",
     "delivery_id + row_hash", "Guideline Telecast .txt.gz", "identity(delivery_id)", "Append (never update a delivery)",
     "All deliveries in the current cycle + last 6 final deliveries; older partitions dropped by the housekeeping job", "1", "Proposed"),
    ("Bronze", f"{BRONZE}.accutv_delivery", "As above for AccuTV", "delivery_id + row_hash", "Guideline AccuTV .txt.gz", "identity(delivery_id)", "Append",
     "As above", "2", "Proposed"),
    ("Bronze", "mit_panel_bronze.program_viewing / program_descriptor", "As delivered by Nielsen (telecast x viewing type x data type)",
     "acn_program_code, trackage_id, telecast_number, time_shifted_viewing_type, nielsen_data_type", "AMS_ICUE_SHARE.MIT (one-time backfill)",
     "month(airing_datetime)", "One-time load, then frozen", "Keep forever", "1", "Decision (Q-03)"),
    ("Bronze", "big_mit_bronze.* (8 tables)", "As delivered", "as source", "SHARE_PROD_BIG_MIT", "existing", "existing", "existing", "1", "Exists (Prod)"),
    ("Bronze", "marketshare_bronze.* (10 tables)", "As delivered", "as source", "WBD_TED_AMS_SHARE_PROD_MARKETSHARE", "existing", "existing", "existing", "1, 3", "Exists (Prod)"),
    ("Silver", f"{SILVER}.dim_broadcast_calendar", "One row per calendar date",
     "calendar_date", "Generated; validated against COMMON.dimDATE", "none", "Overwrite (static)", "-", "All",
     "Proposed (shared with NextGen)"),
    ("Silver", f"{SILVER}.dim_network", "One row per Nielsen network per effective period (SCD2)",
     "network_key (+ effective_from)", "marketshare_bronze.dimnetwork + ref_network_crosswalk", "none", "MERGE (SCD2)",
     "Snapshots 90 days", "All", "Proposed"),
    ("Silver", f"{SILVER}.ref_network_crosswalk", "One row per (source_system, source_network, nielsen network_label, effective period)",
     "source_system, source_network, network_label, effective_from", "Seed maintained by Research (replaces XREF_NETWORK)", "none", "Overwrite from seed (Git-reviewed)",
     "Snapshots 1 year (audit)", "1, 2", "Proposed"),
    ("Silver", f"{SILVER}.dim_program_taxonomy", "One row per network_label x acn_program_code (x program_name)",
     "network_label, acn_program_code, program_name", "marketshare_bronze.dimnetworkprogramnamemapping (isactive)", "none", "Overwrite",
     "Snapshots 90 days", "1, 3", "Proposed"),
    ("Silver", f"{SILVER}.dim_advertiser_brand", "One row per advertiser brand SK", "advertiser_brand_key", "marketshare_bronze.dimadvertiserbrand", "none", "Overwrite", "-", "3", "Proposed"),
    ("Silver", f"{SILVER}.fct_mit_telecast_c3", "One row per telecast per viewing methodology (Live+3, ACM only); demo buckets as columns",
     "network_label, airing_datetime, acn_program_code, telecast_number, viewing_methodology",
     "big_mit_bronze.program_viewing + program_descriptor; Panel Only source (Q-03)",
     "month(broadcast_date), viewing_methodology", "MERGE on key (Nielsen restatements replace)",
     "Snapshots 30 days", "1", "Proposed"),
    ("Silver", f"{SILVER}.fct_guideline_telecast_spend", "Latest final delivery; non-promo; network x program start minute x buy type x ADU x spot length x media subtype",
     "delivery_id, network, program_start_minute, buy_type, adu, spot_length, media_subtype", f"{BRONZE}.telecast_delivery",
     "month(air_date)", "Full overwrite per new final delivery; snapshot tagged with delivery_id",
     "Tag retained 6 months per delivery for rollback", "1", "Proposed"),
    ("Silver", f"{SILVER}.fct_guideline_spend_bounce", "Last N final deliveries x network x broadcast month x buy type",
     "delivery_id, network, bc_month, buy_type", f"{BRONZE}.telecast_delivery (+ accutv)", "identity(delivery_id)", "Append per final delivery; drop > N",
     "-", "1, 2", "Proposed"),
    ("Silver", f"{SILVER}.match_telecast_guideline_mit", "One row per Guideline telecast (network + start minute) with its matched Nielsen telecast or a reject reason",
     "guideline_telecast_key", "fct_guideline_telecast_spend x fct_mit_telecast_c3 x ref_network_crosswalk", "month(broadcast_date)",
     "Rebuilt when either side changes", "Snapshots 30 days", "1", "Proposed"),
    ("Silver", f"{SILVER}.fct_adintel_occurrence", "One row per ad occurrence (as Bronze, deduplicated, isactive only)",
     "_factadintelsk (Phase 1) / Nielsen occurrence id (Phase 2)", "marketshare_bronze.factadintel + dims", "month(ad_date)",
     "MERGE on key", "Snapshots 30 days", "3", "Proposed"),
    ("Silver", f"{SILVER}.fct_guideline_accutv_spend", "Latest final AccuTV delivery at delivered grain", "delivery_id + natural key (TBC from layout)",
     f"{BRONZE}.accutv_delivery", "month(air_date)", "Full overwrite per final delivery", "Tag per delivery", "2", "Proposed"),
    ("Gold", f"{GOLD}.fct_telecast_supply", "One row per reporting Nielsen telecast x broad demo (long format, 18 demos)",
     "telecast_key, demo_code", "fct_mit_telecast_c3 (is_reporting_methodology), dim_program_taxonomy, dim_network, calendar",
     "month(broadcast_date)", "Published by WAP after DQ pass", "Snapshots 90 days (time travel for restatement questions)", "1", "Proposed"),
    ("Gold", f"{GOLD}.fct_telecast_demand", "One row per matched telecast x buy type x ADU x spot length (+ unmatched rows with telecast_key null)",
     "telecast_key, buy_type, adu, spot_length", "match bridge + fct_guideline_telecast_spend", "month(broadcast_date)", "WAP", "Snapshots 90 days", "1", "Proposed"),
    ("Gold", f"{GOLD}.fct_category_spend", "AccuTV grain + conformed network and calendar keys", "as Silver", "fct_guideline_accutv_spend + dim_network",
     "month(air_date)", "WAP", "Snapshots 90 days", "2", "Proposed"),
    ("Gold", f"{GOLD}.fct_adintel_spend", "Ad date x network x program x advertiser brand x media type x duration",
     "ad_date, network_key, program_key, advertiser_brand_key, media_type, duration", "fct_adintel_occurrence + dims",
     "month(ad_date)", "WAP", "Snapshots 90 days", "3", "Proposed"),
    ("Gold", f"{GOLD}.dim_network / dim_program / dim_advertiser_brand / dim_broadcast_calendar / dim_demo", "Conformed dimensions (published copies)",
     "as Silver", "Silver dims", "none", "WAP", "-", "All", "Proposed"),
    ("Ops", f"{GOLD}.dq_results", "One row per check per run", "check_id, run_id", "DQ job", "day(run_ts)", "Append", "2 years", "All", "Proposed"),
    ("Ops", f"{GOLD}.data_freshness", "One row per source x layer", "source, layer", "Ingest + publish jobs", "none", "MERGE", "-", "All", "Proposed"),
]

ICEBERG_PRACTICES = [
    ("Write-audit-publish", "Glue Spark jobs write Silver/Gold to an Iceberg audit branch, run the blocker DQ checks, then fast-forward main. A failed check leaves main untouched, so Quick never shows a half-loaded month.", "PN-02, PN-06", "Proposed (confirm Glue Iceberg version supports branches)"),
    ("Delivery-as-partition", "Guideline Bronze is partitioned by delivery_id. A re-delivery is a new partition, never an update, which makes 'which file is Gold built from' answerable and bounce a simple group-by.", "PN-09", "Proposed"),
    ("Snapshot tags", "Tag the Silver Guideline snapshot with its delivery_id (for example guideline_202604_final). Rollback is then one call. Bounce analysis still uses the explicit bounce table, because Quick cannot time-travel.", "PN-09", "Proposed"),
    ("MERGE for restatements", "MIT and Ad Intel facts MERGE on the Nielsen natural key, so a restated row replaces the original instead of appending. This is the failure that broke factAdIntel and VAMI.", "PN-03, PN-04", "Proposed"),
    ("Hidden partitioning", "Partition facts by month(broadcast_date), and add viewing_methodology for MIT. Quarterly benchmark queries prune to about 3 partitions; the 2017+ backfill stays manageable.", "PN-12", "Proposed"),
    ("Schema contract at landing", "Compare column names, count and types of each file to a registered contract before writing Bronze. On mismatch, quarantine the file and alert. Fixes the silent Snowflake refresh failure.", "PN-06", "Proposed"),
    ("Config, not code, for business dates", "The Panel/Big MIT cutover, the match tolerance (minutes) and the bounce depth (N) live in a ref_pipeline_config table that Research can see.", "PN-03, PN-09", "Proposed"),
    ("Two facts, one key", "Supply (impressions) and demand (spend) are separate Gold facts joined on telecast_key in Cube. Impressions are never repeated across buy-type rows, so they cannot be over-summed.", "PN-01", "Proposed"),
]

# ---------------------------------------------------------------------------
# Business rules
# ---------------------------------------------------------------------------
RULES = [
    ("BR-01", "C3 viewing only", "time_shifted_viewing_type = 'Live+3' AND nielsen_data_type = 'ACM'", "Metrics_Dims; custom_mit2", f"{SILVER}.fct_mit_telecast_c3", "Confirmed"),
    ("BR-02", "History floor", "broadcast_date >= 2017-01-01 for matched outputs (custom_mit2 uses _broadcastdatesk >= 20170101; custom_smi2 uses >= 2016-01-01)", "custom_mit2, custom_smi2", "Silver", "Confirmed (MIT can go back to 2015)"),
    ("BR-03", "Gross impressions", "commercial_program_duration / 30 * sum(delivery for demo buckets in the demo)", "Metrics_Dims row 4", f"{GOLD}.fct_telecast_supply", "Confirmed; units Q-09"),
    ("BR-04", "Broad demos", "P/F/M x {2+, 18+, 25+, 55+, 18-49, 25-54}; P = F + M; 18-49 = 18_20..45_49; 25-54 = 25_29..50_54; 55+ = 55_64 + 65plus; 2+ = all", "Metrics_Dims rows 4, 32", "dim_demo", "Confirmed (55-64 also requested)"),
    ("BR-05", "Broadcast date (6a-6a)", "If airing time < 06:00 then broadcast_date = airing date - 1, else airing date. Test: 2022-04-24 05:45 -> 2022-04-23", "Metrics_Dims row 13", "fct_mit_telecast_c3", "Confirmed"),
    ("BR-06", "Methodology cutover", f"is_reporting_methodology = (Panel Only AND broadcast_date <= {PANEL_CUTOVER_LAST_DAY}) OR (Big MIT AND broadcast_date >= {BIG_MIT_FIRST_DAY})", "2.19, 2.24", "fct_mit_telecast_c3", "Q-02"),
    ("BR-07", "Breakout de-duplication", "Per (network_label, airing_datetime): rank by is_breakout. VAMI code ranks breakout first. For breakout airings, prefer non-short-duration; non-breakout rows default rn=1", "custom_mit2", "fct_mit_telecast_c3", "Q-01 (code vs doc conflict)"),
    ("BR-08", "Guideline non-promo", "promotype = 'Non-Promo'; drop ADU = 'Promo'", "custom_smi2; Metrics_Dims row 19", "fct_guideline_telecast_spend", "Confirmed"),
    ("BR-09", "Guideline concurrent duplicate", "Per (nielsen network, program start minute) keep the row with the highest gross spend; write the rest to a reject table", "custom_smi2", "fct_guideline_telecast_spend", "Confirmed + reject table proposed"),
    ("BR-10", "Buy-type split", "upfront_spend = buytype 'Upfront'; dr_spend = 'Direct Response'; scatter_other_spend = 'Scatter/Other'", "custom_smi2", "fct_telecast_demand", "Confirmed; Guideline DR differs from internal DR (document)"),
    ("BR-11", "Telecast match", "Guideline network -> Nielsen network_label via crosswalk; same broadcast date; program start within +/- N minutes (intake: 3-5); prefer smallest offset; honour BR-07", "3.7", "match_telecast_guideline_mit", "Q-14 for N"),
    ("BR-12", "Gold uses latest final Guideline delivery", "is_final_for_cycle = last delivery received before the next cycle's first delivery; Gold built only from the latest final", "2.19; Examples", "manifest / Silver", "Proposed definition Q-08"),
    ("BR-13", "Weeks-in-period normalisation", "avg_per_bc_week = metric / count(distinct bc_week) in the selected period", "Metrics_Dims row 5; Pain_Points Other", "Cube measure", "Confirmed"),
    ("BR-14", "Network continuity", "Report on dim_network.network (continuous, e.g. HLDRM -> HFM); keep network_label as aired for 'former name' questions", "FactProgram page; 2.24", "dim_network (SCD2)", "Q-12"),
    ("BR-15", "Reporting networks", "Include in routine reporting where dim_network.reporting_status = true AND (for spend) network is Guideline-measured", "Data_Sources_Tables_Details row 15", "dim_network / Cube segment", "Proposed"),
    ("BR-16", "Ad Intel active rows", "isactive = true; flag is_static_segment for ad_date < 2024-06-10; the static segment uses its own _networksk, which is not refreshed", "FactAdIntel page", "fct_adintel_occurrence", "Confirmed; boundary date to confirm"),
    ("BR-17", "Ad Intel unit explosion", "Never join occurrence facts to telecast facts before aggregating; aggregate to the shared grain first", "FactAdIntel page", "Gold build", "Confirmed"),
    ("BR-18", "Taxonomy genre", "Programming Genre = programgroupsummary if in (Sports, News, Kids) else 'Entertainment'; Genre Type/Subtype = programgroupsummary / programgroupdetail", "Metrics_Dims rows 20-22", "dim_program_taxonomy", "Proposed mapping (confirm)"),
    ("BR-19", "WBD Prime / Mirror", "hour(airing) 20-23 = 'WBD Prime'; 0-3 = 'WBD Mirror'", "custom_mit2", "fct_mit_telecast_c3", "Confirmed"),
]

# ---------------------------------------------------------------------------
# Cube semantic layer
# ---------------------------------------------------------------------------
CUBE_VIEWS = [
    # name, source tables, grain, measures, dimensions, segments, audience / access, pipeline
    ("marketplace_view_telecast_supply_demand", f"{GOLD}.fct_telecast_supply + {GOLD}.fct_telecast_demand (joined on telecast_key) + dims",
     "Telecast (supply) / telecast x buy type x ADU x spot length (demand)",
     "Gross Impressions, Gross Impressions per BC Week, Gross Spend, Gross Spend per BC Week, Upfront Spend, Scatter/Other Spend, DR Spend, EQ30 Spot Count, Commercial Duration, Program Duration, Telecast Count, CPM, Share of Spend, Share of Impressions, Power Ratio, Match Rate",
     "Ownership, Network, Network Group, Network Type, Media Type, Program, Program (normalised), Telecast, Episode, Programming Genre / Type / Subtype, Nielsen Program Type / Subtype, Daypart, Buy Type, ADU, Spot Length, Demo, Viewing Methodology, Broadcast and Gregorian calendar",
     "wbd_only, reporting_networks, prime, mirror, panel_only, big_data_panel, matched_only",
     "Marketplace Insights, AMS BI, CARL", "1"),
    ("marketplace_view_category_spend", f"{GOLD}.fct_category_spend + dims", "AccuTV delivered grain",
     "Gross Media Spend, Gross Spend per BC Week, EQ30 Spot Count, Spot Length (sum), Share of Spend",
     "Media Parent Owner, Ownership (internal), Network, Media Subtype, Category Group, Category, Subcategory, Buy Type, ADU, Daypart, Program Genre/Subgenre, Episode/Event/Run/Source Type, Promo Type, calendar",
     "wbd_only, reporting_networks, excl_promo", "Marketplace Insights, AMS BI, CARL", "2"),
    ("marketplace_view_adintel_spend", f"{GOLD}.fct_adintel_spend + dims", "Ad date x network x program x brand x media type x duration",
     "Estimated Spend, Estimated Spend per BC Week, Units, EQ30 Units, Share of Spend",
     "Media Type (Linear/CTV), Category (internal), Nielsen Major/Sub Category, Parent Company, Subsidiary, Brand, Network, Ownership, Program, Program Type/Subtype, calendar",
     "wbd_only, reporting_networks, linear, ctv, excl_static_segment", "Marketplace Insights, AMS BI, CARL", "3"),
    ("marketplace_view_adintel_sales", "Same as marketplace_view_adintel_spend", "Pre-aggregated to brand x network x bc month",
     "Estimated Spend, Share of Spend", "Curated subset chosen by Marketplace Insights (Q-11 list)", "wbd_only",
     "All Research, all Ad Sales, Ad Sales Finance (role-based)", "3"),
    ("marketplace_view_data_freshness", f"{GOLD}.data_freshness + {GOLD}.dq_results", "Source x layer / check x run",
     "Hours Since Last Delivery, Hours Since Last Publish, Checks Failed", "Source, Layer, Check, Severity, Run Date", "-",
     "Everyone with access to any view", "All"),
]

CUBE_MEASURES = [
    # name, view, kpi_class, definition, expression, aggregation, status note
    ("Gross Impressions", "marketplace_view_telecast_supply_demand", "Primary KPI",
     "C3 gross impressions for the selected demo. Exactly one demo must be in the query (demos overlap, so they cannot be summed).",
     "sum(gross_impressions) where demo_code = selected", "Sum", "Units Q-09"),
    ("Gross Impressions per BC Week", "marketplace_view_telecast_supply_demand", "Derived KPI",
     "Gross Impressions divided by the number of broadcast weeks in the selected period", "sum(gross_impressions) / count(distinct bc_week_start)", "Calculated", "BR-13"),
    ("Gross Spend", "marketplace_view_telecast_supply_demand", "Primary KPI",
     "Guideline gross media spend mapped to Nielsen telecasts (non-promo)", "sum(gross_media_spend)", "Sum", "BR-08..11"),
    ("Gross Spend per BC Week", "marketplace_view_telecast_supply_demand", "Derived KPI", "Gross Spend / broadcast weeks in period",
     "sum(gross_media_spend) / count(distinct bc_week_start)", "Calculated", "BR-13"),
    ("Upfront Spend", "marketplace_view_telecast_supply_demand", "Primary KPI", "Gross Spend where buy type = Upfront", "sum(gross_media_spend) filter buy_type='Upfront'", "Sum", "BR-10"),
    ("Scatter/Other Spend", "marketplace_view_telecast_supply_demand", "Primary KPI", "Gross Spend where buy type = Scatter/Other", "sum(...) filter buy_type='Scatter/Other'", "Sum", "BR-10"),
    ("DR Spend", "marketplace_view_telecast_supply_demand", "Primary KPI", "Gross Spend where buy type = Direct Response (Guideline definition)", "sum(...) filter buy_type='Direct Response'", "Sum", "BR-10"),
    ("EQ30 Spot Count", "marketplace_view_telecast_supply_demand", "Primary KPI", "Spots equivalised to :30", "sum(equivalized_30s_spot_count)", "Sum", "-"),
    ("Commercial Duration", "marketplace_view_telecast_supply_demand", "Supporting", "Seconds of national commercial time in the telecast", "sum(commercial_program_duration)", "Sum", "-"),
    ("Program Duration", "marketplace_view_telecast_supply_demand", "Supporting", "Minutes of telecast", "sum(duration)", "Sum", "-"),
    ("Telecast Count", "marketplace_view_telecast_supply_demand", "Supporting", "Distinct reporting telecasts", "count(distinct telecast_key)", "Count distinct", "-"),
    ("CPM", "marketplace_view_telecast_supply_demand", "Derived KPI", "Spend per thousand impressions for matched telecasts", "sum(gross_media_spend) / nullif(sum(gross_impressions) / 1000, 0)", "Calculated", "Proposed; units Q-09"),
    ("Share of Spend", "all spend views", "Derived KPI", "Selected group's spend over spend of all groups in the same filter context (for example WBD / all owners)", "multi-stage measure: sum(spend) / sum(spend) reduce_by ownership", "Calculated", "Proposed (Cube multi-stage or Quick table calc)"),
    ("Share of Impressions", "marketplace_view_telecast_supply_demand", "Derived KPI", "As Share of Spend, on Gross Impressions", "multi-stage", "Calculated", "Proposed"),
    ("Power Ratio", "marketplace_view_telecast_supply_demand", "Derived KPI", "Share of Spend / Share of Impressions; >1 means monetising above audience share", "share_of_spend / nullif(share_of_impressions, 0)", "Calculated", "Proposed (intake marks Med?)"),
    ("Average Audience", "marketplace_view_telecast_supply_demand", "Supporting", "Duration-weighted average audience; never summed", "sum(average_audience * duration) / sum(duration)", "Calculated", "Proposed (intake: 'table calculation?')"),
    ("Match Rate", "marketplace_view_telecast_supply_demand", "Quality", "Share of Guideline spend matched to a Nielsen telecast", "sum(spend) filter telecast_key is not null / sum(spend)", "Calculated", "DQ-16"),
    ("Gross Media Spend", "marketplace_view_category_spend", "Primary KPI", "Guideline AccuTV gross media spend", "sum(gross_media_spend)", "Sum", "-"),
    ("Estimated Spend", "marketplace_view_adintel_spend", "Primary KPI", "Nielsen Ad Intel estimated spend (US$)", "sum(spend)", "Sum", "BR-16"),
    ("Units", "marketplace_view_adintel_spend", "Supporting", "Ad occurrences", "sum(units)", "Sum", "-"),
    ("EQ30 Units", "marketplace_view_adintel_spend", "Supporting", ":30 equivalised units", "sum(units * duration / 30)", "Sum", "Proposed (custom_adintel2 has one; confirm formula)"),
    ("Hours Since Last Delivery", "marketplace_view_data_freshness", "Operational", "Age of the latest source delivery", "date_diff('hour', max(last_delivery_ts), now())", "Calculated", "PN-06"),
]

# ---------------------------------------------------------------------------
# Data quality plan (acceptance criterion 3)
# ---------------------------------------------------------------------------
DQ = [
    # id, layer, object, check, rule, threshold, severity, on failure
    ("DQ-01", "Landing", "Guideline S3 prefix", "Delivery arrival", "New file matching the pattern appears", "Expected 20th-31st; alert if none by day 5 of the next month", "Warn", "Notify Marketplace Insights: 'Guideline file late'"),
    ("DQ-02", "Landing", "Each Guideline file", "Schema contract", "Column count, names and order equal the registered contract; numeric columns parse", "Exact", "Blocker", "Quarantine file, alert. Nothing written to Bronze"),
    ("DQ-03", "Bronze", "delivery_manifest", "Coverage parse", "Coverage end in file name = max(air_date) month in file; delivered_date >= coverage end", "Exact", "Blocker", "Quarantine, alert"),
    ("DQ-04", "Bronze", "telecast_delivery", "Volume vs previous final", "Row count for overlapping months within +/-X% of the previous final delivery; one new month added", "X = 5% (tune after 3 cycles)", "Warn", "Alert with a per-month diff"),
    ("DQ-05", "Bronze", "delivery_manifest", "Re-delivery", "Second file covering the same window marks the earlier one superseded", "-", "Info", "Notify 'revised delivery received'"),
    ("DQ-06", "Silver", "fct_guideline_spend_bounce", "Bounce", "Spend change by network-month vs previous final delivery", "Flag > 10% for months older than 3", "Warn", "Weekly audit report"),
    ("DQ-07", "Bronze", "big_mit_bronze, marketshare_bronze", "Freshness", "Last Prod commit age", "MIT < 36h; MarketShare < 8 days", "Blocker for Gold publish", "Alert CARL DE + AMS BI"),
    ("DQ-08", "Silver", "fct_mit_telecast_c3", "Uniqueness", "One row per (network_label, airing_datetime, acn_program_code, telecast_number, viewing_methodology)", "0 duplicates", "Blocker", "Fail WAP"),
    ("DQ-09", "Silver", "fct_mit_telecast_c3", "Demo arithmetic", "P = F + M for every broad demo; all deliveries >= 0; commercial_program_duration <= duration * 60", "0 violations", "Blocker", "Fail WAP"),
    ("DQ-10", "Silver", "fct_mit_telecast_c3", "Methodology overlap", "Panel vs Big MIT % difference by network-month, 2024-08-05..2025-12-31", "Report only", "Info", "Publish to Research as context"),
    ("DQ-11", "Silver", "fct_mit_telecast_c3", "Cutover completeness", "Every reporting date has exactly one methodology", "0 gaps / 0 overlaps", "Blocker", "Fail WAP"),
    ("DQ-12", "Silver", "fct_adintel_occurrence", "Duplicate occurrences", "count(*) > 1 grouped by all SKs + _addatesk + _adtimesk + duration (isactive)", "0 for ad_date >= 2025-01-01; trend reported for earlier", "Blocker (2025+) / Warn", "Fail WAP; send the list to AMS BI (Sean Malek)"),
    ("DQ-13", "Silver", "fct_adintel_occurrence", "Static/dynamic seam", "Monthly spend step change around 2024-06 vs seasonal baseline", "Flag > 15%", "Warn", "Audit report"),
    ("DQ-14", "Silver", "all facts", "Referential integrity", "Fact keys resolve to dim_network, dim_program_taxonomy, dim_advertiser_brand, calendar", ">= 99.5% of spend / impressions", "Blocker", "Fail WAP; list orphans"),
    ("DQ-15", "Silver", "ref_network_crosswalk", "Spend conservation through mapping", "sum(spend) before mapping = sum(spend) after (no fan-out); every Guideline network is mapped or explicitly excluded", "Exact", "Blocker", "Fail WAP; unmapped list to Research"),
    ("DQ-16", "Silver", "match_telecast_guideline_mit", "Match rate", "Matched spend / total non-promo spend by network-month", "Baseline from the VAMI parity run; alert on a > 2pt drop", "Warn", "Audit report with reject reasons"),
    ("DQ-17", "Gold", "fct_telecast_demand", "Spend conservation end-to-end", "Gold spend + unmatched + BR-09 rejects = Silver non-promo spend", "Exact", "Blocker", "Fail WAP"),
    ("DQ-18", "Gold", "all Gold facts", "Source reconciliation", "Network x broadcast month totals vs vendor UI (Apollo DataMiner, Nielsen NTV View / Lake5) for a fixed sample of 10 network-months", "+/-3% (intake 2.22)", "Blocker for sign-off; Warn monthly", "Monthly report; Research signs off"),
    ("DQ-19", "Gold", "fct_telecast_supply/demand", "VAMI parity", "CARL vs ICUE_DATAMART.MARKETPLACE.MIT_ADINTEL_SMI_V3, 2023-2025, network x month", "+/-3%, every gap explained", "Blocker for go-live", "Parallel-run report"),
    ("DQ-20", "Gold", "dim_program_taxonomy", "Taxonomy coverage", "% reporting telecasts with programgroupsummary; list new unmapped network/program pairs", "Report; target >= 99% of impressions", "Warn", "Feed the unmapped list to Research (replaces the S3 append loop)"),
    ("DQ-21", "Silver", "dim_broadcast_calendar", "Calendar tests", "Weeks per bc month in {4,5}; 52/53 per year; BR-05 test cases; equals COMMON.dimDATE on overlapping columns", "Exact", "Blocker", "Fail build"),
    ("DQ-22", "Semantic", "Cube views", "Golden queries", "10 agreed questions (for example WBD share of C3 impressions P25-54 Q2 2025) return the same value from Cube and from SQL on Gold", "Exact", "Blocker for Cube deploy", "Block release"),
    ("DQ-23", "Ops", "data_freshness", "Freshness publish", "Every run updates data_freshness; Quick tile shows last delivery + last publish per source", "-", "Blocker", "Alert CARL DE"),
    ("DQ-24", "Ops", "dq_results", "Weekly audit", "Summary of all checks for the week, emailed/Slacked to Marketplace Insights", "Weekly, Thursday after the MarketShare refresh", "Info", "-"),
]

# ---------------------------------------------------------------------------
# Open questions / decisions
# ---------------------------------------------------------------------------
QUESTIONS = [
    ("Q-01", "custom_mit2 ranks breakout airings first in code but the doc says non-breakout first. Which should receive Guideline spend?", "Eric Yarsinsky / Maggie Mullane", "Pipeline 1 match", "Follow the code (breakout first), since the VAMI 2 comment says spend went to the breakout airing"),
    ("Q-02", "Cutover: Panel Only through 28-Sep-2025 and Big MIT from 29-Sep-2025? (Pain_Points says 26-Sep and '2026')", "Eric Yarsinsky", "PN-03", "28-Sep / 29-Sep-2025, held as config"),
    ("Q-03", "Panel Only history: one-time backfill from AMS_ICUE_SHARE.MIT, or use marketshare factprogram?", "AMS BI (Hong Zhang, Sean Malek) + Research", "Pipeline 1 history", "Direct backfill, frozen after 31-Dec-2025"),
    ("Q-04", "Ad Intel: can CARL get the raw occurrence feed (and Nielsen's occurrence id)? Is the factAdIntel duplicate fix confirmed for all years?", "AMS BI (Sean Malek)", "Pipeline 3 Phase 2", "Phase 1 on marketshare_bronze with DQ-12"),
    ("Q-05", "Ad Intel CTV: who procures and owns the ingestion?", "Research sponsor + AMS BI", "PN-15", "Out of MVP"),
    ("Q-06", "Truth source: vendor file or vendor UI?", "Research + CARL", "DQ-18", "Vendor file is the system of record; the UI is a sampled reconciliation"),
    ("Q-07", "CARL read access to s3 aws-ams-bi-marketshare-developer/DataOutgoing, or redirect Guideline delivery to CARL landing?", "AMS BI + CARL DE", "MSD-01", "Cross-account read grant first"),
    ("Q-08", "Bounce depth: 3 or 6 final deliveries? Is 'final' = last file before the next cycle's first file?", "Eric Yarsinsky", "PN-09", "6, with that definition"),
    ("Q-09", "Are MIT *_delivery values in thousands or persons?", "AMS BI / Nielsen docs", "CPM, impressions", "Check against Nielsen NTV View on one telecast"),
    ("Q-10", "Demos: static broad list or dynamic building blocks?", "Research", "Cube demo dimension", "Static 18 broad demos in Gold; buckets kept in Silver"),
    ("Q-11", "Which dimensions does the Ad Sales-facing Ad Intel view expose?", "Marketplace Insights", "PN-13", "-"),
    ("Q-12", "Keep former network names (DIY vs MAG)?", "Research", "dim_network", "Yes: SCD2 with network (continuous) and network_label (as aired)"),
    ("Q-13", "Is Snowflake SQL access to Gold required, or are Athena + Cube + Quick enough?", "Research + CARL architecture", "F-12", "Athena + Cube + Quick"),
    ("Q-14", "Match tolerance +/-3 or +/-5 minutes; tie-break rule?", "Eric Yarsinsky", "BR-11", "+/-5, smallest offset wins, flag offset in the bridge"),
    ("Q-15", "After MarketShare, who owns taxonomy edits: AMS BI S3 rules engine or a CARL-managed seed?", "Research + AMS BI + CARL", "PN-05", "Phase 1 consume MarketShare outputs; Phase 2 CARL seed with Git review"),
    ("Q-16", "Time buy Looker report (3rd Quick ask on CARL-3776): owner, source and scope?", "Daya Thakur / Ping Feng", "Separate intake", "-"),
    ("Q-17", "Co-sponsor sign-off from Finance (Jenn Blue) is 'in progress'. Who accepts?", "David Porter", "Definition of Done", "-"),
    ("Q-18", "AccuTV file layout and grain (no dictionary exists)", "Research + Guideline", "Pipeline 2 model", "Profile the first landed file"),
    ("Q-19", "Ad Intel history depth (rolling 5 years?) vs the 10-year ask", "AMS BI", "PN-12", "-"),
]

# ---------------------------------------------------------------------------
# Looker iCUE Marketplace model (connection icue_ted_datamart) -> CARL layers
# ---------------------------------------------------------------------------
LOOKER_SRC = "LookML model 'iCUE Marketplace' (connection icue_ted_datamart), pasted 12-Oct"

LOOKER = [
    # object, kind, what it is, verdict, bronze, silver, gold / cube, note
    ("Marketplace_adintel (fact_adintel_v)", "Explore", "Ad Intel occurrences with primary/secondary/tertiary advertiser, attribute, media type, network, program, date, time",
     "Migrate (Pipeline 3)", "marketshare_bronze.factadintel + dims (exists)", f"{SILVER}.fct_adintel_occurrence", f"{GOLD}.fct_adintel_spend / marketplace_view_adintel_spend",
     "Secondary and tertiary advertiser roles are used in Looker; keep all three brand keys in Gold (the design only named the primary)."),
    ("dim_adintel_*_v (advertiserbrand, adintelattribute, mediatype, network, programdescriptor, networkprogramnamemapping)", "Views", "Thin views over MarketShare tables",
     "Replace", "marketshare_bronze.* (exists)", "dim_advertiser_brand, dim_network, dim_program_taxonomy, dim_media_type", "Gold dims", "No new ingestion needed."),
    ("dim_adintel_common_dimdate / dimtime", "Views", "COMMON calendar and time-of-day",
     "Replace", "Not landed (COMMON); validation oracle only", "dim_broadcast_calendar, dim_time_of_day", "Gold dims", "6a-6a date via broadcastdate6_6; the 3a-3a join is commented out, so not needed."),
    ("dim_mktplc_programtype_v / dim_mktplc_programsubtype_v", "Views", "Nielsen program type/subtype code -> description lookups",
     "Migrate", "Seed from these views (small, static)", "ref_nielsen_program_type, ref_nielsen_program_subtype", "Gold dim_program columns",
     "Answers the intake open question 'where does Description match Code' (Metrics_Dims rows 23/25)."),
    ("dim_mktplc_network_v, nielsendatatype, nielsendaypartcd, timeshiftedviewingtype, refdate, reftime, programdescriptor", "Views", "Genesis-era Marketplace lookups",
     "Replace", "-", "Covered by dim_network, dim_daypart, dim_broadcast_calendar, dim_time_of_day; data type / viewing type become filters (BR-01)", "-",
     "The two network dims are joined by try_cast(mitnetworkid as integer). The conformed dim_network removes that fragile join."),
    ("Marketplace_smi_genesis (fact_genesis_smi_mktplc_factprogram_v)", "Explore", "Genesis (MarketShare 1.0) viewership + SMI",
     "Retire", "-", "-", "Superseded by fct_telecast_supply/demand",
     "MarketShare 1.0 was decommissioned 14-Mar-2025. Only keep if Research needs pre-2017 Genesis history."),
    ("ams_mit_program_descriptor_genesis_aliases_v", "View", "Genesis <-> AMS program descriptor aliasing", "Retire", "-", "-", "-", "Only needed while Genesis explores live."),
    ("mit_smi_adintel (fact_adintel_mit_smi)", "Explore", "'AMS share MIT Data TEST': MIT + Ad Intel + MarketShare + SMI",
     "Retire", "-", "-", "Superseded by Pipeline 1 Gold", "A test explore. Use it as a reference for join keys only."),
    ("mit_adintel_smi_v2 ('VAMI 3')", "Explore", "Telecast-level MIT + Ad Intel + SMI at advertiser level (Snowflake VAMI table)",
     "Rebuild, then retire", "big_mit_bronze, marketshare_bronze, guideline_bronze", "match_telecast_guideline_mit, fct_mit_telecast_c3", "fct_telecast_supply/demand / marketplace_view_telecast_supply_demand",
     "Parity baseline (DQ-19). It carries a primary advertiser, but the intake drops Ad Intel from the Pipeline 1 merge, so advertiser-level VAMI needs a decision (Q-20). Its network join upper(trim(mitnetworkcd)) = network_label goes away."),
    ("vami_reporting_networks", "View", "Reporting-network include list", "Retire", "-", "dim_network.reporting_status", "segment reporting_networks", "Matches PN-05."),
    ("icue_bundle_map", "View", "network_label + program type -> bundle", "Migrate", "Seed (export current contents)", "ref_network_bundle", "dim_program.bundle / Cube dimension Bundle",
     "Not in the intake. Ask Research whether bundles are still reported (Q-21)."),
    ("dim_amrld_title_franchise + dim_content", "Views", "Telecast -> title/franchise -> content attributes ('Content Data')",
     "Decision", "Out of intake scope (AMRLD excluded)", "dim_title_franchise if kept", "dim_program.title / franchise",
     "Used in 3 explores. Confirm whether Content Data must survive the move (Q-22)."),
    ("rpt_ad_overunder_share ('Ad Market Share Analysis')", "Explore", "Pre-built over/under share report table",
     "Rebuild as Cube", "-", "-", "Cube multi-stage Share of Spend / Power Ratio on Gold", "Source SQL unknown; get it before parity testing (Q-23)."),
    ("smi_us_telecast", "Explore", "Raw Guideline Telecast staging",
     "Migrate", f"{BRONZE}.telecast_delivery", f"{SILVER}.fct_guideline_telecast_spend", "-", "Raw exploration stays at Silver; not exposed in Quick by default."),
    ("smi_us_accutv", "Explore", "Raw Guideline AccuTV staging",
     "Migrate (Pipeline 2 MVP)", f"{BRONZE}.accutv_delivery", f"{SILVER}.fct_guideline_accutv_spend", f"{GOLD}.fct_category_spend / marketplace_view_category_spend",
     "This is the 'just make AccuTV queryable' MVP."),
    ("icue_vami3_demochart / icue_vami3_bundlechart", "Explores", "Chart-specific derived tables over VAMI 3",
     "Rebuild as Cube", "-", "-", "Cube pre-aggregations on marketplace_view_telecast_supply_demand (by demo / by bundle)", "Do not persist as separate Gold tables."),
    ("mit_premiere_telecasts", "Explore", "Premiere telecasts list", "Rebuild as Cube", "-", "is_premiere on fct_mit_telecast_c3", "Cube segment 'premieres'",
     "NextGen's PREMIERES table needs the same thing; build it once."),
    ("icue_mit_custom_daypart", "Explore", "MIT C3 matched to custom research/sales dayparts per network",
     "Migrate", "Seed (export the custom daypart definitions)", "ref_custom_daypart (network x time range)", "Cube dimension Custom Daypart",
     "Not in the intake. Network-specific daypart table needed."),
    ("genesis_validation / vami_validation", "Explores", "Validation of Genesis and VAMI telecast counts vs AMS MIT",
     "Replace", "-", "-", f"{GOLD}.dq_results (DQ-16, DQ-19) / marketplace_view_data_freshness", "Validation becomes automated checks, not explores."),
    ("pathmatics, pathmatics_top_advertisers, pathmatics_zero_share (+ pathmatics_wm_map, pathmatics_sitemap)", "Explores", "Pathmatics digital spend",
     "Out of scope", "Future: pathmatics_bronze", "Future: advertiser and site maps", "Future", "Intake 2.3 lists Pathmatics as future roadmap."),
    ("edo_tv_airings (hidden)", "Explore", "EDO airings validation for custom projects", "Out of scope", "-", "-", "-", "Not in the intake."),
    ("/icue_research/*.view", "Views", "Unlisted research views included by wildcard", "Unknown", "-", "-", "-", "Need the folder contents to classify (Q-23)."),
]

QUESTIONS += [
    ("Q-20", "Looker VAMI 3 is advertiser-level (primary Ad Intel brand per telecast). Does Pipeline 1 need advertiser, given the intake removes Ad Intel from the merge?", "Eric Yarsinsky / Maggie Mullane", "Pipeline 1 grain", "No advertiser in Pipeline 1; advertiser questions go to Pipeline 3"),
    ("Q-21", "Is icue_bundle_map (network + program type -> bundle) still used? Who maintains it?", "Research", "ref_network_bundle", "Migrate as a seed"),
    ("Q-22", "Must 'Content Data' (dim_amrld_title_franchise + dim_content) survive the move, even though AMRLD is out of scope?", "Research", "dim_program title/franchise", "-"),
    ("Q-23", "Source SQL for rpt_ad_overunder_share, icue_mit_custom_daypart and the /icue_research views", "Looker owner (ICUE project)", "Parity tests", "-"),
]

# ---------------------------------------------------------------------------
# Proposed stories under CARL-3775
# ---------------------------------------------------------------------------
STORIES = [
    ("MSD-01", "Land Guideline Telecast + AccuTV to guideline_bronze with manifest and schema contract", "1, 2", "Bronze", "Q-07",
     "Every delivery since go-live is a partition; DQ-01..05 run and alert; re-delivery marks supersession", "8"),
    ("MSD-02", "dim_broadcast_calendar (shared with NextGen)", "All", "Silver/Gold", "-", "DQ-21 passes; matches COMMON.dimDATE", "3"),
    ("MSD-03", "Conformed dim_network + ref_network_crosswalk (retire XREF_NETWORK, VAMI_REPORTING_NETWORKS)", "All", "Silver/Gold", "Q-12, Q-15",
     "Every Guideline and Ad Intel network maps or is excluded; DQ-15 passes; Research reviews the seed", "5"),
    ("MSD-04", "dim_program_taxonomy + unmapped-program feed", "1, 3", "Silver/Gold", "-", "DQ-20 report delivered to Research", "3"),
    ("MSD-05", "Panel Only MIT history (decision + backfill)", "1", "Bronze", "Q-03", "History 2017-01 to 2025-12 queryable; row counts reconcile to source", "5"),
    ("MSD-06", "fct_mit_telecast_c3 with methodology stitching and dedupe flags", "1", "Silver", "MSD-05, Q-01, Q-02", "DQ-08..11 pass", "8"),
    ("MSD-07", "Guideline Silver: current-final spend + bounce + reject table", "1, 2", "Silver", "MSD-01, Q-08", "BR-08..10, BR-12; DQ-06", "5"),
    ("MSD-08", "Telecast match bridge Guideline <-> Nielsen", "1", "Silver", "MSD-03, MSD-06, MSD-07, Q-14", "DQ-16 baseline set; reject reasons populated", "8"),
    ("MSD-09", "Gold Pipeline 1: fct_telecast_supply + fct_telecast_demand", "1", "Gold", "MSD-08", "DQ-17 exact; WAP gate live", "5"),
    ("MSD-10", "Ad Intel Phase 1: Silver/Gold from marketshare_bronze with duplicate checks", "3", "Silver/Gold", "Q-04", "DQ-12, DQ-13 reported; is_static_segment flag", "5"),
    ("MSD-11", "Gold Pipeline 2: fct_category_spend (AccuTV)", "2", "Silver/Gold", "MSD-01, Q-18", "Queryable with taxonomy; DQ-18 sample passes", "5"),
    ("MSD-12", "DQ framework: dq_results, data_freshness, WAP, alerts, weekly audit", "All", "Ops", "-", "DQ-23, DQ-24 running; alerts reach the Marketplace Insights channel", "8"),
    ("MSD-13", "Cube views + measures (5 views) and golden-query tests", "All", "Semantic", "MSD-09..11", "DQ-22 passes; views listed in cube_model.yaml as certified", "8"),
    ("MSD-14", "Quick datasets, 3 practice dashboards, freshness tile, training links", "All", "BI", "MSD-13", "Research builds a dashboard unaided", "8"),
    ("MSD-15", "Parallel run: VAMI parity + +/-3% source reconciliation, sign-off", "1, 3", "Validation", "MSD-09, MSD-10", "DQ-18, DQ-19 signed off by Eric/Maggie", "5"),
    ("MSD-16", "Data dictionary, FAQ, flow diagrams published from the registry", "All", "Docs", "MSD-13", "Approved by Research + CARL SMEs", "3"),
    ("MSD-17", "Ad Sales-facing Ad Intel view + dashboard with role-based access", "3", "Semantic/BI", "MSD-13, Q-11", "Access verified for 3 roles", "5"),
    ("MSD-18", "Ad Intel Phase 2 (direct occurrence feed, revision MERGE) + CTV readiness", "3", "Bronze/Silver", "Q-04, Q-05", "Duplicates = 0 all years", "13"),
]
