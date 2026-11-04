# 03 - Op1 / Digital: field-by-field logic (Look 26239, 24 labels)

Source export has 14,084 data rows. The export prefix 'Op1 Contracted Data' is the explore view_label.

Status legend: **VERIFIED-DATA** = Behaviour reproduced / checked against the two Looker exports (PIPELINE_sample, DIG_ORDER_sample) by analysis.py. Re-runnable.; **LEGACY-SOURCE** = Logic read directly from a file in carl-legacy-source-master.zip (path:line cited). The legacy repo is an OLDER snapshot than live Looker; where live data disagrees, the data wins.; **SHEET** = Stated in UC1_Fields_for_CARL_working (2).xlsx (sheet!cell cited). It is a proposal / working note, not proof.; **SECONDARY-XLSX** = Stated in a prior analysis workbook (Salesforce_AdSales_LookML_Iceberg_Analysis.xlsx / Operative1_AdSales_Master_Analysis_Final.xlsx). These were derived from LookML you pasted earlier; the LookML text itself is not on disk.; **CHAT-ONLY** = Came from SQL / Slack text pasted into the earlier chat. The original text is NOT on disk and could not be re-read, so it is NOT re-verifiable. Save it into evidence/ to upgrade.; **NAME-MATCH** = CARL/silver column inferred ONLY because the name equals or resembles a column in the Northstar silver sample header. Not confirmed lineage.; **NOT FOUND** = Not present in any evidence provided. Left blank on purpose - not guessed.; **MISMATCH** = Looker/legacy behaviour differs from what Field Logic (or CARL) does. Needs a decision from Jason (Looker is the source of truth).

## 1. Op1 Contracted Data Classification

- **MVP row / fill:** 19 (E: no fill)
- **Looker field kind:** custom-field dimension (order custom field)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-02
- **Field Logic column:** classification (Field Logic!D33,D34,D40)
- **In sample sheet as RAW?:** Y (T)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_custom_field_t.classification = CASE WHEN LOWER(custom_field_name) LIKE '%classification%' THEN custom_field_value END. Matched by NAME pattern, not by ID. Null 575 rows. Separately bolt_views.sql (older) pivots custom_field_id 141 as CLASSIFICATION and 16 as PAYMENT_TYPE.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L256-264 [dimension classification 'Classification']`
  ```
  CASE WHEN LOWER(${custom_field_name}) LIKE '%classification%' THEN ${custom_field_value} ELSE NULL END
  ```
- `looker-etl-carl/snowflake/snowflake_views/bolt_views/bolt_views.sql:L1819`
  ```
  MAX(CASE WHEN CUSTOM_FIELD_ID = 141 THEN CUSTOM_FIELD_VALUE END) AS CLASSIFICATION,
  ```

**Live vs legacy / observations**

Name-pattern match can catch several fields containing 'classification' (risk: duplicates). The ID-based bolt view uses 141. Not reconciled in evidence.

## 2. Op1 Contracted Data Sales Stage

- **MVP row / fill:** 14 (E green 'Sales Stage (op sales stage)')
- **Looker field kind:** dimension (order)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-04
- **Field Logic column:** sales_stage (Field Logic!D37)
- **In sample sheet as RAW?:** Y (V)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_t.sales_stage_name = ${TABLE}.sales_stage_name (Operative order's own sales stage; NOT Salesforce's stage). 14 values incl. 'Closed/Won' 478, '0%' 94, '100%' 44, Verbal Commitment/HOLD, Cancelled, Closed Lost. 'booking_status' CASE (Booked/Hold/Pitched/Lost) is built from order_status + sales_stage_name.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_t.view.lkml:L993-1013 [dimension sales_stage_name 'Sales Stage']`
  ```
  ${TABLE}.sales_stage_name
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_t.view.lkml:L328-355 [dimension booking_status 'Booking Status']`
  ```
  CASE WHEN ${sales_stage_name} IN ('Closed Lost','Lost') THEN 'Lost' When ${order_status} LIKE '%active_order%' then 'Booked' When ${order_status} LIKE '%final_modification^_%' ESCAPE '^' then 'Booked' When ${order_status} LIKE '%preliminary_modification^_%' ESCAPE '^' then 'Booked' When ${order_status} LIKE '%proposed_order%' then 'Booked' When ${order_status} LIKE '%final_order^_%' ESCAPE '^' then 'Hold' When ${order_status} LIKE '%client_proposal%' then 'Pitched' When ${order_status} LIKE '%proposal_approval%' then 'Pending YM Approval' When ${order_status} LIKE '%proposal_creation%' then 'Model/Starting Point' When ${order_status} LIKE '%closed_lost%' then 'Lost' ELSE 'Unknown' END
  ```

**Live vs legacy / observations**

Dirty values ('0%','100%', two closed-won spellings); Field Logic!F37 notes this. ClosedWonStages list on Lists tab must cover 'Closed/Won'.

## 3. Salesforce Opportunity Stage

- **MVP row / fill:** 13 (E green)
- **Looker field kind:** dimension (joined Salesforce view)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA + CHAT-ONLY + MISMATCH
- **Decision ref:** D-04
- **Field Logic column:** not an Op1 input in Field Logic (lifecycle_state uses sales_stage)
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Op1 explore joins salesforce_eds (OPPORTUNITY_V): stage_name = ${TABLE}.STAGE_NAME, matched on the Op1 Opportunity ID. NULL on 679 rows (618 of them have NULL Opportunity ID, so 61 have an ID that did not resolve).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_eds.view.lkml:L9-31 [dimension stage_name 'Opportunity Stage']`
  ```
  ${TABLE}."STAGE_NAME"
  ```
- `looker-inventory-analytics/views/base.opportunity_v.view.lkml:L723-726 [dimension stage_name]`
  ```
  ${TABLE}."STAGE_NAME"
  ```

**Live vs legacy / observations**

Aishwarya (CHAT-ONLY): 'Opportunity Stage' NOT available for Op1 silver. MVP says green. Contradiction to raise.

## 4. Op1 Contracted Data Site

- **MVP row / fill:** 51 (E: no fill)
- **Looker field kind:** dimension (derived CASE)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA + CHAT-ONLY
- **Decision ref:** D-15
- **Field Logic column:** site (Field Logic!D29-D35)
- **In sample sheet as RAW?:** Y (O)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_line_items_t.forecast_category label 'Site': CASE WHEN forecast_category='N/A' -> 'Uncategorized Revenue'; WHEN LOWER(dt_oper_hbo_targeting.discovery_inventory_package) LIKE '%discovery+%' -> 'Discovery+'; ELSE the stored forecast_category. Stored forecast_category (ETL) = COALESCE(line forecast_category, OPER_PRODUCT_SITE.SITE, 'Uncategorized Revenue'). 32 distinct values in export (Value_Profiles).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L217-352 [dimension forecast_category 'Site']`
  ```
  CASE WHEN ${TABLE}.forecast_category = 'N/A' THEN 'Uncategorized Revenue' WHEN lower(${dt_oper_hbo_targeting.discovery_inventory_package}) like '%discovery+%' THEN 'Discovery+' ELSE ${TABLE}.forecast_category END
  ```
- `looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql:L128`
  ```
  coalesce(oper_sales_order_line_items_v.forecast_category,SITE.SITE,'Uncategorized Revenue') AS forecast_category ,
  ```

**Live vs legacy / observations**

Depends on the targeting listagg (discovery_inventory_package, ID 1774) -> a targeting table must be in silver for Site to match Looker. Aishwarya (CHAT-ONLY): Site NOT available in Op1 silver.

## 5. Op1 Contracted Data Package Name

- **MVP row / fill:** 52 (E: no fill)
- **Looker field kind:** dimension
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-06
- **Field Logic column:** package_name (Field Logic!D36)
- **In sample sheet as RAW?:** Y (M)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_line_items_t.package_name (line item's package). NULL on 4,757 rows (non-package lines). Field Logic wbd_stream_package_flag = package_name ILIKE '%WBD Stream%' OR '%Stream+%'.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L729-734 [dimension package_name]`
  ```
  ${TABLE}.package_name
  ```

**Live vs legacy / observations**

Used by Field Logic uf_group (the 'WBD Stream is a PACKAGE, not a site' rule, Field Logic!F35/D36).

## 6. Op1 Contracted Data Product Name

- **MVP row / fill:** 53 (E: no fill)
- **Looker field kind:** dimension
- **Status:** LEGACY-SOURCE
- **Decision ref:** -
- **Field Logic column:** product_name (sample_op1 col N)
- **In sample sheet as RAW?:** Y (N)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_line_items_t.product_name. Also an input to is_dr (product name LIKE '%direct response%').

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L773-778 [dimension product_name]`
  ```
  ${TABLE}.product_name
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L932-944 [dimension is_dr 'Direct Response Flag']`
  ```
  CASE WHEN lower(${product_name}) like '%direct response%' THEN 'Direct Response' WHEN ${TABLE}.DEAL_TYPE = 'Direct Response' THEN 'Direct Response' WHEN ${op1_order_classification.classification} = 'Direct Response' THEN 'Direct Response' ELSE 'N/A' END
  ```

**Live vs legacy / observations**



## 7. Op1 Contracted Data Market Type

- **MVP row / fill:** 4 (E green)
- **Looker field kind:** dimension (derived CASE)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA + MISMATCH
- **Decision ref:** D-01
- **Field Logic column:** market_type (Field Logic!D33)
- **In sample sheet as RAW?:** N (deliberately excluded, Field Logic!F33)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_line_items_t.market_type: IF op1_order_is_upfront.is_upfront <> 'No' THEN 'Upfront' ELSE IF is_dr = 'Direct Response' THEN 'DR' ELSE 'Scatter'. is_upfront = IFNULL(UPFRONT_TYPE_OP_V.UPFRONT_TYPE,'No') (via custom fields 'Upfront'/'Upfront Type'/'Upfront Type_Old'). 3 values in export (Upfront 6,907 / Scatter 6,898 / DR 279).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L947-960 [dimension market_type]`
  ```
  CASE WHEN ${op1_order_is_upfront.is_upfront} <> 'No' THEN 'Upfront' WHEN ${is_dr} = 'Direct Response' THEN 'DR' ELSE 'Scatter' END
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L932-944 [dimension is_dr 'Direct Response Flag']`
  ```
  CASE WHEN lower(${product_name}) like '%direct response%' THEN 'Direct Response' WHEN ${TABLE}.DEAL_TYPE = 'Direct Response' THEN 'Direct Response' WHEN ${op1_order_classification.classification} = 'Direct Response' THEN 'Direct Response' ELSE 'N/A' END
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L237-245 [dimension is_upfront 'Upfront Type']`
  ```
  ${upfront_type_fix}
  ```
- `looker-inventory-analytics/views/base.upfront_type_op_v.view.lkml:L8-15 [dimension is_upfront 'Upfront Type']`
  ```
  IFNULL(${TABLE}."UPFRONT_TYPE",'No')
  ```

**Live vs legacy / observations**

DISAGREES with Field Logic/Classification-derived market_type on 4,683 of 13,285 comparable rows (35%), $469.8M of $1,341.0M net revenue. Field Logic!F33 says it was left out of the sample on purpose. Looker is the source of truth -> Jason must pick.

## 8. Op1 Contracted Data Sales Order ID

- **MVP row / fill:** 35 (E green)
- **Looker field kind:** dimension
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-12
- **Field Logic column:** sales_order_id (sample_op1 col A)
- **In sample sheet as RAW?:** Y (A)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_t.sales_order_id (also on line items). 2,938 distinct in 14,084 rows. Link key to Salesforce Sales Order ID.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_t.view.lkml:L932-948 [dimension sales_order_id 'Delivery Look']`
  ```
  ${TABLE}.sales_order_id
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L1223-1226 [dimension sales_order_id]`
  ```
  ${TABLE}.sales_order_id
  ```

**Live vs legacy / observations**



## 9. Op1 Contracted Data Order Name

- **MVP row / fill:** 29 (E green 'Order Name')
- **Looker field kind:** dimension
- **Status:** LEGACY-SOURCE
- **Decision ref:** D-06
- **Field Logic column:** order_name (Field Logic!D38)
- **In sample sheet as RAW?:** Y (D)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_t.sales_order_name. Also the text the Op1 Discovery+ flag tests (legacy discoveryplusflag on line items uses sales_order_name).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_t.view.lkml:L961-968 [dimension sales_order_name 'Order Name']`
  ```
  ${TABLE}.sales_order_name
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L354-364 [dimension discoveryplusflag 'Discovery+ Flag']`
  ```
  (${forecast_category} = 'Discovery Networks' OR ${forecast_category} = 'DCI ENT') AND (LOWER(${sales_order_name}) LIKE '%d+%' OR LOWER(${sales_order_name}) LIKE '%discovery+%' OR LOWER(${sales_order_name}) LIKE '%dplus%' OR LOWER(${sales_order_name}) LIKE '%discoveryplus%' ) OR ${forecast_category} = 'Discovery+'
  ```

**Live vs legacy / observations**



## 10. Op1 Contracted Data Agency

- **MVP row / fill:** 7 (E green)
- **Looker field kind:** dimension (cleaned)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-09
- **Field Logic column:** agency (Field Logic!D42)
- **In sample sheet as RAW?:** Y (G)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_t.agency_name = regexp_replace(agency_name_raw, '\s+\(\d+\)', '') - strips a trailing ' (digits)' suffix. Null 93 rows.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_t.view.lkml:L60-70 [dimension agency_name 'Agency']`
  ```
  regexp_replace(${agency_name_raw}, '\\s+\\(\\d+\\)', '')
  ```

**Live vs legacy / observations**

CARL silver must apply the same suffix strip or names will not match Looker.

## 11. Op1 Contracted Data Mega Agency

- **MVP row / fill:** 8 (E green)
- **Looker field kind:** dimension (joined mapping views)
- **Status:** LEGACY-SOURCE (partial) + NOT FOUND (tables)
- **Decision ref:** D-10
- **Field Logic column:** mega_agency / holdco_conformed (Field Logic!D41)
- **In sample sheet as RAW?:** Y (H)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Exact legacy definition: agency.parentagency = COALESCE(INSIGHT_DIMAGENCY.parentagency, UPPER(SF_MEGA_AGENCY.mega_agency)); joins: agency FULL OUTER on oper_sales_order_t.agency_name = agency.agency AND LOWER(source)='wbd' (model line 791); sf_agency LEFT on LOWER(agency_name) = LOWER(buying_agency) (line 803). Holding company (Revised Holding Company) = pi_holdco_mapping.REV_HOLD joined on COALESCE(LOWER(agency.parentagency), LOWER(pi_agency_mapping.rev_agy), LOWER(agency_name)) = LOWER(ORI_HOLD) (line 2373). The table contents are not in the repo. 910 null of 14,084 in export; 57 distinct (SF export: 115 distinct).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.agency.view.lkml:L11-20 [dimension parentagency 'Mega Agency']`
  ```
  COALESCE(${TABLE}.parentagency,${sf_agency.parentagency})
  ```
- `looker-inventory-analytics/views/base.sf_agency.view.lkml:L10-17 [dimension parentagency 'Mega Agency - SF']`
  ```
  UPPER(${TABLE}.mega_agency)
  ```
- `looker-inventory-analytics/views/base.pi_holdco_mapping.view.lkml:L9-13 [dimension rev_agy 'Revised Holding Company']`
  ```
  ${TABLE}."REV_HOLD"
  ```

**Live vs legacy / observations**

PI_ mapping tables (pi_holdco_mapping) not in repo.

## 12. Op1 Contracted Data Advertiser

- **MVP row / fill:** 6 (E green)
- **Looker field kind:** dimension
- **Status:** LEGACY-SOURCE
- **Decision ref:** -
- **Field Logic column:** advertiser (sample_op1 col E)
- **In sample sheet as RAW?:** Y (E)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_t.advertiser_name = ${TABLE}.advertiser_name.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_t.view.lkml:L37-47 [dimension advertiser_name 'Advertiser']`
  ```
  ${TABLE}.advertiser_name
  ```

**Live vs legacy / observations**



## 13. Op1 Contracted Data Calendar Quarter

- **MVP row / fill:** 9 (E green)
- **Looker field kind:** dimension_group timeframe (quarter)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA + CHAT-ONLY
- **Decision ref:** D-16
- **Field Logic column:** calendar_quarter (sample_op1 col AA)
- **In sample sheet as RAW?:** Y (AA)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Timeframe 'quarter' of calendar_date (om_con_dy.CALENDARDATE) - the DAY the prorated revenue lands on. Export format 'YYYY-Qn' (e.g. 2026-Q4). Because revenue is prorated per day, one order line spreads across quarters.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L1464-1481 [dimension_group calendar]`
  ```
  ${TABLE}.calendardate
  ```

**Live vs legacy / observations**

CARL: Aishwarya (CHAT-ONLY) Calendar Quarter NOT available in Op1 silver. Silver needs a line-day grain (or equivalent proration) to reproduce.

## 14. Op1 Contracted Data Opportunity ID

- **MVP row / fill:** 28 (E green 'Opp ID')
- **Looker field kind:** custom-field dimension (order custom field)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-12
- **Field Logic column:** opportunity_id (sample_op1 col B)
- **In sample sheet as RAW?:** Y (B)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_custom_field_t.opportunity_id: when custom_field_name is 'Opportunity ID' or 'Warner SF Deal ID' -> COALESCE(custom_field_value, oper_sales_order_t.external_opportunity_id); else external_opportunity_id. NULL on 618 rows (4.4%).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L285-293 [dimension opportunity_id 'Opportunity ID']`
  ```
  CASE WHEN ${custom_field_name} = 'Opportunity ID' OR ${custom_field_name} = 'Warner SF Deal ID' THEN COALESCE(${custom_field_value},${oper_sales_order_t.external_opportunity_id}) ELSE ${oper_sales_order_t.external_opportunity_id} END
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L1745-1748 [dimension external_opportunity_id]`
  ```
  ${TABLE}.external_opportunity_id
  ```

**Live vs legacy / observations**

Name-based custom field + fallback. Drives the Salesforce Opportunity Stage join.

## 15. Op1 Contracted Data Workflow Status

- **MVP row / fill:** 16 (E RED)
- **Looker field kind:** dimension
- **Status:** LEGACY-SOURCE + VERIFIED-DATA + MISMATCH
- **Decision ref:** D-04
- **Field Logic column:** workflow_status (Field Logic!D37)
- **In sample sheet as RAW?:** Y (W)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_t.order_status labelled 'Workflow Status' = ${TABLE}.order_status. 9 values in export.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_t.view.lkml:L316-326 [dimension order_status 'Workflow Status']`
  ```
  ${TABLE}.order_status
  ```

**Live vs legacy / observations**

MVP marks RED, and Aishwarya (CHAT-ONLY) says not available - but the Looker export contains it and Field Logic!D37 reads it for lifecycle_state.

## 16. Op1 Contracted Data Sales Order Start Date

- **MVP row / fill:** 39 (E green)
- **Looker field kind:** dimension (date)
- **Status:** LEGACY-SOURCE
- **Decision ref:** -
- **Field Logic column:** not in Field Logic
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** NAME-MATCH: Northstar order_flight_start_date (Linear)

**Looker logic / definition**

oper_sales_order_line_items_t.sales_order_start_date = ${string_order_start_date} (order header start).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L1870-1874 [dimension sales_order_start_date]`
  ```
  ${string_order_start_date}
  ```

**Live vs legacy / observations**



## 17. Op1 Contracted Data Sales Order End Date

- **MVP row / fill:** 40 (E green)
- **Looker field kind:** dimension (date)
- **Status:** LEGACY-SOURCE
- **Decision ref:** -
- **Field Logic column:** not in Field Logic
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** NAME-MATCH: Northstar order_flight_end_date (Linear)

**Looker logic / definition**

oper_sales_order_line_items_t.sales_order_end_date = ${string_order_end_date}.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L1876-1880 [dimension sales_order_end_date]`
  ```
  ${string_order_end_date}
  ```

**Live vs legacy / observations**



## 18. Op1 Contracted Data SSP

- **MVP row / fill:** 54 (E: no fill)
- **Looker field kind:** custom-field dimension (order custom field)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA + CHAT-ONLY
- **Decision ref:** D-17
- **Field Logic column:** ssp (sample_op1 col Z)
- **In sample sheet as RAW?:** Y (Z)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_custom_field_t.ssp = CASE WHEN custom_field_id IN (204) AND source='wbd' THEN custom_field_value END. Populated on only 742 of 14,084 rows (Magnite, Freewheel SSP, Amazon APS, Google ...).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L248-254 [dimension ssp 'SSP']`
  ```
  CASE WHEN ${custom_field_id} IN (204) AND ${source} = 'wbd' THEN ${custom_field_value} ELSE NULL END
  ```

**Live vs legacy / observations**

Aishwarya (CHAT-ONLY): SSP NOT available in Op1 silver.

## 19. Op1 Contracted Data Deal Type

- **MVP row / fill:** 5 (E green)
- **Looker field kind:** custom-field dimension (order custom field)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-03
- **Field Logic column:** deal_type (sample_op1 col U)
- **In sample sheet as RAW?:** Y (U)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_custom_field_t.deal_type = CASE WHEN custom_field_id IN (41,214) THEN custom_field_value END. 11 values; 'N/A' on 11,418 rows. (ETL om_con_dy uses IFNULL(Warner Deal Type,'None') instead.)

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L136-156 [dimension deal_type 'Deal Type']`
  ```
  CASE WHEN ${custom_field_id} IN (41,214) THEN ${custom_field_value} ELSE NULL END
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L2136-2142 [dimension deal_type 'Deal Type']`
  ```
  ${op1_order_deal_type.deal_type}
  ```

**Live vs legacy / observations**

LookML uses IDs 41/214; ETL uses custom_field_name 'Warner Deal Type' (or 'Deal Type' for wm). Not proven identical.

## 20. Op1 Contracted Data Primary AE

- **MVP row / fill:** 20 (E '.' green)
- **Looker field kind:** dimension (parsed)
- **Status:** LEGACY-SOURCE
- **Decision ref:** D-14
- **Field Logic column:** primary_ae (sample_op1 col I)
- **In sample sheet as RAW?:** Y (I)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

oper_sales_order_t.primary_salesperson_name = SPLIT_PART(primary_salesperson_name, '_', 1) - keeps the text before the first underscore.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_t.view.lkml:L382-392 [dimension primary_salesperson_name 'Primary AE']`
  ```
  SPLIT_PART(${TABLE}.primary_salesperson_name,'_',1)
  ```

**Live vs legacy / observations**

CARL must replicate the SPLIT_PART or AE names will not match.

## 21. Op1 Contracted Data Net Revenue

- **MVP row / fill:** 55 (E green)
- **Looker field kind:** measure (derived prorated sum)
- **Status:** LEGACY-SOURCE + CHAT-ONLY + VERIFIED-DATA
- **Decision ref:** D-16
- **Field Logic column:** net_revenue (Field Logic!D43,D44,D45)
- **In sample sheet as RAW?:** Y (AB)
- **CARL silver/gold column:** CHAT-ONLY: Op1 op1 measure formula; CARL column not found

**Looker logic / definition**

SUM(sum_net_cost_dim) where sum_net_cost_dim = COALESCE(PACING_NET_COST / product_counts, net_cost_per_day, 0) [divided further by oper_targeting_count only when audience_targeting is in the query]. net_cost_per_day = net_cost / ((day_num+1) * counts) from the om_con_dy ETL; currency applied in 02_op1_contracted_w_rate.sql (x FUTURE_RATE if CALENDARDATE >= CURRENCY_FILE_DATE else x PAST_RATE). Export values are strings like '$25,137' - whole-dollar rounding.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L2474-2481 [measure sum_net_cost 'Net Revenue']`
  ```
  SUM(${sum_net_cost_dim})
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L2444-2455 [dimension sum_net_cost_dim]`
  ```
  {% if oper_sales_line_item_targeting_t.audience_targeting._in_query %} COALESCE((${PACING_NET_COST}/${product_counts})/IFNULL(${oper_targeting_count.target_count},1),${net_cost_per_day}/IFNULL(${oper_targeting_count.target_count},1),0) {% else %} COALESCE(${PACING_NET_COST}/${product_counts},${net_cost_per_day},0) {% endif %}
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L669-672 [dimension net_cost_per_day]`
  ```
  ${TABLE}.net_cost_per_day
  ```
- `looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql:L174`
  ```
  oper_sales_order_line_items_v.net_cost / ((day_count.day_num + 1) * counts) AS net_cost_per_day,
  ```

**Live vs legacy / observations**

Proration + currency + custom pacing (OP1_CUSTOM_PACING_IMPS_REV_MAPPING_V) are ETL steps CARL silver must reproduce. Export total 1,341,033,379 (rounded display values).

## 22. Op1 Contracted Data Gross Revenue

- **MVP row / fill:** 56 (E green)
- **Looker field kind:** measure (derived prorated sum)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-16
- **Field Logic column:** gross_revenue (Field Logic!D45)
- **In sample sheet as RAW?:** Y (AC)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

SUM(sum_gross_cost_dim) where sum_gross_cost_dim = COALESCE(PACING_GROSS_COST / product_counts, net_parent_gross_cost) and net_parent_gross_cost = GROSS_COST_PER_DAY. Gross = Net on 97.85% of rows (13,781 / 14,084); 3 gross nulls; where they differ the spread totals 2,626,015.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L2520-2527 [measure sum_gross_cost 'Gross Revenue']`
  ```
  SUM(${sum_gross_cost_dim})
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L2512-2518 [dimension sum_gross_cost_dim]`
  ```
  COALESCE(${PACING_GROSS_COST}/${product_counts},${net_parent_gross_cost})
  ```
- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L706-710 [dimension net_parent_gross_cost]`
  ```
  ${TABLE}.GROSS_COST_PER_DAY
  ```

**Live vs legacy / observations**

Field Logic!F45: carry both columns, do not alias one to the other.

## 23. Op1 Contracted Data Contracted Quantity

- **MVP row / fill:** 61 (E: no fill)
- **Looker field kind:** measure
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-16
- **Field Logic column:** quantity (sample_op1 col AD)
- **In sample sheet as RAW?:** Y (AD)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

SUM(sum_quantity_dim) where sum_quantity_dim = COALESCE(PACING_QUANTITY / product_counts, quantity_per_day). quantity_per_day = quantity / ((day_num+1)*counts).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L2382-2389 [measure sum_quantity 'Contracted Quantity']`
  ```
  SUM(${sum_quantity_dim})
  ```

**Live vs legacy / observations**

Label says 'do not sum' for the raw quantity dimension; only the prorated measure is summable.

## 24. Op1 Contracted Data Contracted Production Quantity

- **MVP row / fill:** 62 (E: no fill)
- **Looker field kind:** measure
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-16
- **Field Logic column:** production_quantity (sample_op1 col AE)
- **In sample sheet as RAW?:** Y (AE)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

SUM(sum_production_quantity_dim) where = COALESCE(PACING_PQ / product_counts, production_quantity_per_day).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.oper_sales_order_line_items_t.view.lkml:L2407-2414 [measure sum_production_quantity 'Contracted Production Quantity']`
  ```
  SUM(${sum_production_quantity_dim})
  ```

**Live vs legacy / observations**


