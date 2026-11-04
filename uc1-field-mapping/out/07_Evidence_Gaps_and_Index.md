# 07 - Evidence gaps and evidence index

Nothing below was guessed. Items tagged CHAT-ONLY came from the pasted chat text, which is not saved on disk and therefore cannot be re-verified.

## Gaps

| ID | Gap | Impact on mapping | Needed to close | Owner |
|---|---|---|---|---|
| G-01 | Pasted Looker SQL (Salesforce explore, Op1 explore incl. CTEs oper_targeting_count and dt_oper_hbo_targeting) and Slack history are NOT on disk. | All 'CHAT-ONLY' tags (record-type IDs, Mike's SQL changes, PR numbers, Aishwarya's availability lists, measure formulas) cannot be re-verified. | Save the two Looker SQLs, Ping's uf_group SQL and the Slack export into uc1-field-mapping/evidence/ and re-run build.py for a verification pass. | Daya |
| G-02 | Live Looker custom dimensions with no LookML on disk: Platform, uf_group, sales_division, Property, Property Detail, UF Year, Status Group, SF Market Type, Buyer_AE/Client_AE/Planning_AE. | Only behavioural equivalence is proven (see Validation workbook), not the Looker expressions. | Export the live LookML for salesforce_reporting (current version) into evidence/. | Looker owner |
| G-03 | CARL silver/gold column lists for fact_pipeline_sf, fact_digital_op1, fact_linear_working_ms, fact_linear_revenue_ms are not on disk (only chat-quoted partial names and the Northstar silver sample header). | The 'CARL column' of most rows is 'not found in provided evidence'. No column names were invented. | Provide DESCRIBE/DDL for the four gold tables and silver.fact_linear_ms_revenue / SF / Op1 silver tables. | Mike / Aishwarya |
| G-04 | oper_etl_orders_activity_order_status_mappping_V (SF Workflow Status source) definition. | Workflow Status mapping cannot be reproduced from evidence. | DDL of the view. | Looker/Snowflake owner |
| G-05 | PI_SITE_MAPPING, PI_HOLDCO_MAPPING, PI_AGENCY_MAPPING, SF_MEGA_AGENCY table contents; INSIGHT_DIMAGENCY (EMERALDDW_PROD). | holdco_conformed / Mega Agency cascade not reproducible (Field Logic!D20). | Table extracts. | Data steward |
| G-06 | oper_dimdate_v (broadcast calendar) and OPER_PRODUCT_SITE contents. | Calendar Quarter / Site fallback cannot be reproduced. | Table extracts. | Data Engineering |
| G-07 | Legacy repo is an older snapshot (no date in the zip). | Live fields renamed since (e.g. BROADWAY_IO_ID_C -> IDEAL_DEAL_ID; agency fields; record_type) are known only from the secondary workbook. | Confirm snapshot date or provide the current repo. | Daya |
| G-08 | Both Look exports are label-keyed samples at the Look's own grain (not row-level source tables). | Raw inputs (sports_property, forecast_category, network, payment_type, ad_type for Op1, etc.) are not in the exports, so some Field Logic columns are 'NOT RE-DERIVABLE'. | Export the sample_sf / sample_op1 raw inputs at the same grain. | Daya |
| G-09 | MVP lists fields as green for fact_digital_op1 (sales_division, UF Year, business_source) that Look 26239 does not contain. | MVP parity cannot be tested for these on the Looker side. | Confirm whether Jason's Op1 look should include them. | Jason |
| G-10 | Northstar sample has Excel date-formatted integers (calendar_year -> 1905-07-18, calendar_qtr_num -> 1900-01-01). | Sample file defect, not necessarily a silver defect. | Re-export the sample with numeric formats. | Daya |

## Evidence index

| ID | Artifact | Location | What it provides | Availability |
|---|---|---|---|---|
| E01 | UC1_Fields_for_CARL_working (2).xlsx | /Users/dthakur/Downloads/ | Sheets: Fields, MVP Fields, Field Logic, sample_sf, sample_op1, sample_ideal, Lists, Finance Dates, reference documents, iDeal Northstar Revenue sample | ON DISK |
| E02 | PIPELINE_sample 2026-10-16T1926.json_label | /Users/dthakur/Downloads/ | Looker Look 26238 export: 23,757 rows (1 is a Looker grand-total row), 33 labels, label-keyed | ON DISK |
| E03 | DIG_ORDER_sample 2026-10-16T1926.json_label | /Users/dthakur/Downloads/ | Looker Look 26239 export: 14,084 rows, 24 labels, label-keyed; money/qty are formatted strings | ON DISK |
| E04 | carl-legacy-source-master.zip | /Users/dthakur/Downloads/ | Legacy repo: looker-inventory-analytics (LookML), looker-etl-carl (Airflow SQL, Snowflake UDF/views), airflow_prod_eds, dai-digital-ads | ON DISK (older snapshot) |
| E05 | Operative1_AdSales_Master_Analysis_Final.xlsx | LocalRepo / OneDrive | Prior analysis of the Op1 explore (secondary) | ON DISK (secondary) |
| E06 | Salesforce_AdSales_LookML_Iceberg_Analysis.xlsx | LocalRepo / OneDrive | Prior analysis of the CURRENT Salesforce LookML incl. record_type, AE roles, IDEAL_DEAL_ID (secondary) | ON DISK (secondary) |
| E07 | CARL_UC1_Readiness_Tracker.xlsx, CARL_UC1_Status_Pack v1-v3 | LocalRepo / OneDrive | Program trackers (secondary; context only) | ON DISK (secondary) |
| E08 | 7 meeting screenshots | .cursor/projects/.../assets/ | Meeting decisions (MVP = Jason's Looker list; mismatches flagged for Jason; SF lifecycle needs 4 fields; Mike's uf_group fix) | ON DISK |
| E09 | Pasted Slack history + Mike's SQL changes + Aishwarya's availability summary + Looker SQL (Salesforce, Op1) + Ping's uf_group SQL | earlier chat | Table names/tickets, PR numbers, decimal(38,15), measure formulas, record-type IDs, field-availability lists | CHAT-ONLY (not on disk) |