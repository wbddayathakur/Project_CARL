# 02 - Salesforce / Pipeline: field-by-field logic (Look 26238, 33 labels)

Source export has 23,756 data rows. Every field: Looker logic, legacy citations with SQL, live-vs-legacy notes, CARL column (as far as evidenced), status and decision.

Status legend: **VERIFIED-DATA** = Behaviour reproduced / checked against the two Looker exports (PIPELINE_sample, DIG_ORDER_sample) by analysis.py. Re-runnable.; **LEGACY-SOURCE** = Logic read directly from a file in carl-legacy-source-master.zip (path:line cited). The legacy repo is an OLDER snapshot than live Looker; where live data disagrees, the data wins.; **SHEET** = Stated in UC1_Fields_for_CARL_working (2).xlsx (sheet!cell cited). It is a proposal / working note, not proof.; **SECONDARY-XLSX** = Stated in a prior analysis workbook (Salesforce_AdSales_LookML_Iceberg_Analysis.xlsx / Operative1_AdSales_Master_Analysis_Final.xlsx). These were derived from LookML you pasted earlier; the LookML text itself is not on disk.; **CHAT-ONLY** = Came from SQL / Slack text pasted into the earlier chat. The original text is NOT on disk and could not be re-read, so it is NOT re-verifiable. Save it into evidence/ to upgrade.; **NAME-MATCH** = CARL/silver column inferred ONLY because the name equals or resembles a column in the Northstar silver sample header. Not confirmed lineage.; **NOT FOUND** = Not present in any evidence provided. Left blank on purpose - not guessed.; **MISMATCH** = Looker/legacy behaviour differs from what Field Logic (or CARL) does. Needs a decision from Jason (Looker is the source of truth).

## 1. Salesforce Opportunity Stage

- **MVP row / fill:** 13 (D green)
- **Looker field kind:** dimension (native)
- **Status:** VERIFIED-DATA + LEGACY-SOURCE
- **Decision ref:** D-04
- **Field Logic column:** opportunity_stage (Field Logic!D15)
- **In sample sheet as RAW?:** Y (D)
- **CARL silver/gold column:** not found in provided evidence (Field Logic uses opportunity_stage as input name)

**Looker logic / definition**

Raw Salesforce opportunity stage text, passed through. Legacy: salesforce_reporting.opportunity_stage = ${TABLE}.opportunity_stage <- ETL OPPORTUNITY_STAGE_C of SITE_MONTH_BREAKOUT_V. The export has 7 values: Closed Won 13,336; Prospecting/Planning Costs 2,974; Verbal Commitment/HOLD 2,943; Proposal/Working 2,045; Proposal Low/Projection 1,219; Closed Lost 1,209; Cancelled 30.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L445-468 [dimension opportunity_stage]`
  ```
  ${TABLE}.opportunity_stage
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L107`
  ```
  site_month.OPPORTUNITY_STAGE_C AS OPPORTUNITY_STAGE,
  ```

**Live vs legacy / observations**

Legacy suggestion list uses different spellings (Won/Canceled/Verbal/Likely to Close/New Opportunity). Live export spellings differ -> legacy projection_rank CASE would return NULL for most live stages.

## 2. Salesforce Classification

- **MVP row / fill:** 19 (D: no fill)
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA + MISMATCH
- **Decision ref:** D-02
- **Field Logic column:** upf_vs_scat (Field Logic!D12,D13,D19)
- **In sample sheet as RAW?:** Y (G)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy upf_scat label 'Classification' = ${TABLE}.UPF_VS_SCAT <- ETL opp.CLASSIFICATION_C. Drives Market Type, UF Year (both reproduced 100% from it) and direct_response_flag. 19 distinct values; NULL on 1,574 rows (6.6%).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L663-670 [dimension upf_scat 'Classification']`
  ```
  ${TABLE}.UPF_VS_SCAT
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L123`
  ```
  opp.CLASSIFICATION_C AS UPF_VS_SCAT,
  ```

**Live vs legacy / observations**

MVP row 19 has NO fill for pipeline/digital, yet three MVP fields (Market Type, UF Year, uf_group Linear branch) depend on it. Risk: 'not in MVP' fields are required inputs.

## 3. UF Year

- **MVP row / fill:** 42 (D,E green; marked *)
- **Looker field kind:** custom dimension (no LookML on disk)
- **Status:** VERIFIED-DATA
- **Decision ref:** -
- **Field Logic column:** upfront_year (Field Logic!D13)
- **In sample sheet as RAW?:** n/a (BUILT)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

REPRODUCED: = first match of regex [0-9]{2}/[0-9]{2} in Salesforce Classification, else 'N/A'. 23,756/23,756 rows match the Field Logic rule (Field Logic!D13). Looker's own SQL is not on disk, so this is behavioural equivalence, not source proof.

**Legacy evidence:** none in the legacy repo.

**Live vs legacy / observations**

No legacy equivalent. Field Logic note: production hardcodes two year strings; Looker output on this sample is consistent with the pattern rule.

## 4. Status Group

- **MVP row / fill:** 43 (D yellow 'null?')
- **Looker field kind:** custom dimension (no LookML on disk)
- **Status:** VERIFIED-DATA
- **Decision ref:** D-04
- **Field Logic column:** lifecycle_state (Field Logic!D15)
- **In sample sheet as RAW?:** n/a (BUILT)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

REPRODUCED: Field Logic lifecycle_state rule (Field Logic!D15) using Stage, Projection Rank, Workflow Status and Looker's own sales_division reproduces Status Group on 23,756/23,756 rows. Values: Order 14,037 / Pipeline 5,813 / Prospecting 2,606 / closed_lost 1,300 (4 values).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.op_staq_sf_union_v.view.lkml:L296-309 [dimension status_group 'Status Group']`
  ```
  CASE WHEN LOWER(${projection_rank}) = 'f' THEN 'closed_lost' WHEN ${order_status} = 'closed_lost' THEN 'closed_lost' WHEN ${projection_rank} IN ('B','C','D') AND ${order_status} NOT IN ('closed_lost', 'proposed_order_modification','final_modification_approvals','active_order') THEN 'Pipeline' WHEN ${projection_rank} IN ('B','C','D') AND ${order_status} IS NULL THEN 'Pipeline' WHEN ${order_status} IS NULL THEN 'Order' ELSE 'Order' END
  ```

**Live vs legacy / observations**

Legacy status_group (STAQ union view) has 3 values (closed_lost/Order/Pipeline); live has 4 (adds Prospecting). Salesforce lifecycle needs 4 fields (Stage, Rank, Workflow Status, sales_division) - confirmed in meeting (Arlene: do not remove).

## 5. Property Detail

- **MVP row / fill:** 44 (D: no fill)
- **Looker field kind:** custom dimension (no LookML on disk)
- **Status:** VERIFIED-DATA (consistency) + LEGACY-SOURCE (analogue) + MISMATCH (NULL rows)
- **Decision ref:** D-07
- **Field Logic column:** property_detail (Field Logic!D11)
- **In sample sheet as RAW?:** Y (H,I,J = Linear Network, Booked Site, Sports Property)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Digital rows: the booked site (e.g. 'Discovery Networks', 'Bleacher Report (non-OMP)'). Linear rows: network (e.g. TBS, Food Network) or a sports_property value (MLB, CFBBig12 ...). Field Logic: COALESCE(sports_property, CASE Digital->forecast_category ELSE network). NULL on 724 rows (all Linear). Raw forecast_category / network / sports_property are NOT in the export, so the COALESCE cannot be re-derived, only compared.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L221-258 [dimension forecast_category 'Booked Site']`
  ```
  ${TABLE}.forecast_category
  ```
- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L279-309 [dimension network 'Linear Network']`
  ```
  ${TABLE}.network
  ```
- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L311-330 [dimension sports_property]`
  ```
  ${TABLE}.SPORTS_PROPERTY
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L156`
  ```
  END AS SPORTS_PROPERTY,
  ```

**Live vs legacy / observations**

Legacy ETL derives SPORTS_PROPERTY from deal type / site name (March Madness-Digital, NBA-Digital, Bleacher Report (non-OMP), MLB-Digital, NHL ...). Legacy ETL writes NETWORK = NULL for WBD SF, so linear network must come from another path in the live data. Linear sports property names in the export (CBBBig12, CFBBig12, Boxing, Soccer, Tennis, FIBA, WNBA ...) are not in any legacy CASE.

## 6. Property

- **MVP row / fill:** 45 (D green; marked *)
- **Looker field kind:** custom dimension (no LookML on disk)
- **Status:** VERIFIED-DATA
- **Decision ref:** -
- **Field Logic column:** property (Field Logic!D10)
- **In sample sheet as RAW?:** n/a (BUILT)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

CONSISTENT with Field Logic: for all 23,032 rows with a non-null Property Detail, Property = COALESCE(PropMap[detail], SiteMap[detail], NetMap[detail], detail) using the Lists tab. 0 exceptions.

**Legacy evidence:** none in the legacy repo.

**Live vs legacy / observations**

Property is NULL on exactly the rows where Property Detail is NULL (724).

## 7. Platform

- **MVP row / fill:** 3 ('Record Type . business_source')
- **Looker field kind:** custom dimension (no LookML on disk)
- **Status:** VERIFIED-DATA + MISMATCH
- **Decision ref:** D-05
- **Field Logic column:** platform (Field Logic!D6)
- **In sample sheet as RAW?:** n/a (BUILT)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Equals Record Type except on 23 rows (BR 9, Nascar 3, Digital Media 11) where Record Type = Linear but Platform = Digital. Looker output: Linear 16,208 / Digital 7,548 vs Record Type Linear 16,231 / Digital 7,525.

**Legacy evidence:** none in the legacy repo.

**Live vs legacy / observations**

Field Logic!F6 says only network 'Digital Media' is overridden and the override was dropped because 'all seven such rows carry $0'. Export shows 23 rows across THREE property details (Digital Media 11, BR 9, Nascar 3). Their summed Net Projections = $0 (verified), so Field Logic's '$0' reasoning holds for money in this sample, but the row count (23 vs 7) and the three property details differ from what Field Logic documents.

## 8. Market Type

- **MVP row / fill:** 4 (D,E green)
- **Looker field kind:** custom dimension (SF) / native (Op1)
- **Status:** VERIFIED-DATA
- **Decision ref:** D-01
- **Field Logic column:** market_type (Field Logic!D12)
- **In sample sheet as RAW?:** n/a (BUILT)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

SF: REPRODUCED 23,756/23,756 by Field Logic!D12 (Upfront if classification contains 'upfront'; Scatter if contains 'scatter' or in ScatterVals; ADU/PSA/International/Programmatic buckets; else Unmapped). Values in export: see Value_Profiles.

**Legacy evidence:** none in the legacy repo.

**Live vs legacy / observations**

SF and Op1 'Market Type' use DIFFERENT logic in Looker (SF from Classification; Op1 from is_upfront/is_dr). Field Logic!F33 says derive from Classification on every system.

## 9. uf_group

- **MVP row / fill:** 46 (D: no fill; marked *)
- **Looker field kind:** custom dimension (no LookML on disk)
- **Status:** VERIFIED-DATA + LEGACY-SOURCE + MISMATCH
- **Decision ref:** D-06
- **Field Logic column:** uf_group (Field Logic!D14)
- **In sample sheet as RAW?:** n/a (BUILT)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

12 values in the export: Linear - Traditional/DDL/Demo Direct/Premiere; Sports Linear - NCAA/Non-NCAA; Sports Digital - NCAA/Non-NCAA; Digital - WBD Stream/MAX/News/D+. Linear non-sports branch REPRODUCED 13,190/13,190 by 'Linear - '||classification when classification in (DDL, Demo Direct, Premiere) else Traditional. 'Digital - D+' reproduced exactly by the legacy discoveryplusflag (90/90, 0 false positives). See Mismatches for the 5 places Field Logic differs.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L712-722 [dimension discoveryplusflag 'Discovery+ Flag']`
  ```
  (${forecast_category} = 'Discovery Networks' OR ${forecast_category} = 'DCI ENT') AND (LOWER(${opportunity_name_id}) LIKE '%d+%' OR LOWER(${opportunity_name_id}) LIKE '%discovery+%' OR LOWER(${opportunity_name_id}) LIKE '%dplus%' OR LOWER(${opportunity_name_id}) LIKE '%discoveryplus%' ) OR ${forecast_category} = 'Discovery+'
  ```

**Live vs legacy / observations**

Mike's silver uf_group did not match Looker (fixed Oct 15-16 per meeting). The remaining Field Logic differences (T1-T6 in analysis) are listed in Mismatches_Decisions.

## 10. sales_division

- **MVP row / fill:** 11 (all 4 green; marked *; L,D,S)
- **Looker field kind:** custom dimension (no LookML on disk)
- **Status:** VERIFIED-DATA
- **Decision ref:** D-06
- **Field Logic column:** sales_division (Field Logic!D8)
- **In sample sheet as RAW?:** n/a (BUILT)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Three values: Linear (13,190 rows + 11 'Digital - WBD Stream' rows), Sports, Digital. Every uf_group maps to exactly ONE sales_division except 'Digital - WBD Stream' (Digital 2,737 + Linear 11). Field Logic!D8 builds it from sports_property / SportsSites / SportsNetworks lists.

**Legacy evidence:** none in the legacy repo.

**Live vs legacy / observations**

Legacy has 'division' (user.division / warner_sf_division_c) which is a different field. Field Logic builds a new sales_division; Looker's is a custom dimension.

## 11. Salesforce Opportunity ID

- **MVP row / fill:** 28 (D,E green 'Opp ID')
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** -
- **Field Logic column:** opportunity_id (sample_sf col A)
- **In sample sheet as RAW?:** Y (A)
- **CARL silver/gold column:** NAME-MATCH: Northstar silver has sf_opportunity_id (Linear)

**Looker logic / definition**

Legacy label 'Opportunity ID' = ${TABLE}.opportunity <- ETL site_month.OPPORTUNITY_C (SF opportunity id). 0 nulls in export (7,233 distinct).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L425-435 [dimension opportunity 'Opportunity ID']`
  ```
  ${TABLE}.opportunity
  ```

**Live vs legacy / observations**

Note ETL also exposes OPP_ID = opp.WARNER_SF_OPPORTUNITY_ID_C (different field). Which of the two the live label uses is NOT proven; the sample_raw value in the export looks like a SF 18-char id.

## 12. Salesforce Opportunity Name

- **MVP row / fill:** 29 (D 'Opp Name')
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE
- **Decision ref:** -
- **Field Logic column:** opportunity_name (Field Logic!D16)
- **In sample sheet as RAW?:** Y (B)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy opportunity_name_id label 'Opportunity Name' <- ETL site_month.OPPORTUNITY_NAME_C. Also the text the Discovery+ flag tests.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L437-443 [dimension opportunity_name_id 'Opportunity Name']`
  ```
  ${TABLE}.opportunity_name_id
  ```

**Live vs legacy / observations**



## 13. Salesforce Advertiser Name

- **MVP row / fill:** 6 (D 'Advertiser')
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE
- **Decision ref:** -
- **Field Logic column:** advertiser (sample_sf col M)
- **In sample sheet as RAW?:** Y (M)
- **CARL silver/gold column:** NAME-MATCH: Northstar silver has advertiser / advertiser_id (Linear)

**Looker logic / definition**

Legacy advertiser_name = ${TABLE}.advertiser_name <- ETL site_month.ADVERTISER_NAME_C.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L41-45 [dimension advertiser_name]`
  ```
  ${TABLE}.advertiser_name
  ```

**Live vs legacy / observations**



## 14. Salesforce Agency

- **MVP row / fill:** 7 (D 'Agency')
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE + SECONDARY-XLSX
- **Decision ref:** D-09
- **Field Logic column:** agency_name (Field Logic!D21); sample_sf has both Agency (N) and Buying Agency (O)
- **In sample sheet as RAW?:** Y (N,O)
- **CARL silver/gold column:** NAME-MATCH: Northstar silver buying_agency / planning_agency (Linear)

**Looker logic / definition**

Legacy agency_name label 'Buying Agency' <- ETL site_month.BILLING_AGENCY_NAME_C. Current LookML (secondary workbook) has THREE agency fields: agency_name 'Agency' (${TABLE}.agency_name), buy_agency_name (BUYING_AGENCY_NAME), plan_agency_name (PLANNING_AGENCY_NAME), upfront_agency_name (UPFRONT_AGENCY_NAME).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L102-107 [dimension agency_name 'Buying Agency']`
  ```
  ${TABLE}.agency_name
  ```

**Live vs legacy / observations**

Export label is 'Agency'; MVP linear columns say 'Buying Agency' while pipeline says 'Agency'. Which physical column feeds the live 'Agency' for Linear vs Digital is not provable from provided files.

## 15. Salesforce Mega Agency

- **MVP row / fill:** 8 (all green)
- **Looker field kind:** dimension (native, joined view)
- **Status:** LEGACY-SOURCE (partial) + NOT FOUND (mapping tables)
- **Decision ref:** D-10
- **Field Logic column:** mega_agency / holdco_conformed (Field Logic!D20)
- **In sample sheet as RAW?:** Y (P)
- **CARL silver/gold column:** NAME-MATCH: Northstar silver mega_agency, holdco_conformed (Linear)

**Looker logic / definition**

Legacy Looker 'Mega Agency' = agency.parentagency = COALESCE(INSIGHT_DIMAGENCY.parentagency, sf_agency.parentagency) where sf_agency.parentagency = UPPER(SF_MEGA_AGENCY.mega_agency). In the Op1 explore: agency joins FULL OUTER on oper_sales_order_t.agency_name = agency.agency AND source='wbd'; sf_agency joins LEFT on LOWER(agency_name) = LOWER(sf_agency.agency) where sf_agency.agency = SF_MEGA_AGENCY.buying_agency. Field Logic holdco_conformed (SIMPLIFIED) = COALESCE(NULLIF(mega_agency,''),'INDEPENDENT'); production cascade quoted in Field Logic!D20: COALESCE(INSIGHT_DIMAGENCY.parentagency, SF_MEGA_AGENCY.mega_agency, PI_AGENCY_MAPPING.REV_A...).

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

SF_MEGA_AGENCY, PI_AGENCY_MAPPING / pi_holdco_mapping table contents are NOT in the repo (only the Looker view wrappers). Export: 719 null of 23,756; 115 distinct values (Op1 export: 910 null, 57 distinct).

## 16. Salesforce Activity Quarter

- **MVP row / fill:** 31 (D yellow)
- **Looker field kind:** dimension / custom
- **Status:** LEGACY-SOURCE + SECONDARY-XLSX + OPEN
- **Decision ref:** D-08
- **Field Logic column:** not in Field Logic
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Export values are 'YYYY-MM' (17 distinct; 418 null). Legacy dimension_group 'Activity' (end): WM SF -> end_date, else month; timeframes month/quarter/year. Secondary workbook (current LookML): Linear -> first month of BROADCAST quarter; WM SF -> end_date; else month.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L154-170 [dimension_group end 'Activity']`
  ```
  CASE WHEN ${source} = 'WM SF' THEN ${TABLE}.end_date ELSE ${TABLE}.month END
  ```

**Live vs legacy / observations**

Mixed business meanings in one date (secondary workbook R-03). MVP marks it yellow (open). Format in export is not Looker's native 'YYYY-Qn'.

## 17. Salesforce Total Amount

- **MVP row / fill:** 60 (D: no fill)
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE + CHAT-ONLY
- **Decision ref:** D-11
- **Field Logic column:** not in Field Logic
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** CHAT-ONLY: total_amt_gross / total_amt_net (fact_pipeline_sf, CARL-3949)

**Looker logic / definition**

Legacy total_amount = ${TABLE}.TOTAL_AMOUNT <- ETL opp.total_amount_c (opportunity-level total, repeated on every site-month row). SUM over the export is not meaningful (7.26B) - it is an opportunity attribute, not an additive measure.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L545-551 [dimension total_amount 'Total Amount']`
  ```
  ${TABLE}.TOTAL_AMOUNT
  ```

**Live vs legacy / observations**

Mike's change (CHAT-ONLY): total_amt_gross = cast(lo.cost__c as decimal(22,2)); total_amt_net = null.

## 18. Salesforce Projection Rank

- **MVP row / fill:** 48 (D: no fill)
- **Looker field kind:** dimension (native CASE)
- **Status:** VERIFIED-DATA + LEGACY-SOURCE (stale) + CHAT-ONLY
- **Decision ref:** D-04
- **Field Logic column:** projection_rank (Field Logic!D15)
- **In sample sheet as RAW?:** Y (F)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy CASE on LOWER(opportunity_stage): won/canceled->A, verbal->B, new opportunity->D, likely to close->C, closed lost->F, else NULL. LIVE export mapping (all 7 stages): Closed Won->A; Verbal Commitment/HOLD->B; Proposal/Working->C; Proposal Low/Projection->D; Closed Lost->F; Prospecting/Planning Costs->NULL; Cancelled->NULL (30 rows). Status Group rule treats rank F as lost, A as Order.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L470-485 [dimension projection_rank 'Projection Rank']`
  ```
  CASE WHEN LOWER(${opportunity_stage}) IN ('won','canceled') THEN 'A' WHEN LOWER(${opportunity_stage}) = 'verbal' THEN 'B' WHEN LOWER(${opportunity_stage}) = 'new opportunity' THEN 'D' WHEN LOWER(${opportunity_stage}) = 'likely to close' THEN 'C' WHEN LOWER(${opportunity_stage}) = 'closed lost' THEN 'F' ELSE NULL END
  ```

**Live vs legacy / observations**

Live stage spellings differ from the legacy CASE, so the live CASE was changed. The exact live CASE text is only CHAT-ONLY (Ping/Looker SQL); the table above is reproduced from the data.

## 19. Salesforce Order ID

- **MVP row / fill:** 34 (D 'Order ID')
- **Looker field kind:** dimension (native)
- **Status:** SECONDARY-XLSX + VERIFIED-DATA
- **Decision ref:** D-12
- **Field Logic column:** not in Field Logic
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** NAME-MATCH: Northstar silver order_id / order_no (Linear)

**Looker logic / definition**

Linear-group field ORDER_ID (secondary workbook: ${TABLE}.ORDER_ID, group 'Linear'). Non-null: Linear 15,484 / Digital 23. Not in the legacy repo (older view has no ORDER_ID).

**Legacy evidence:** none in the legacy repo.

**Live vs legacy / observations**

Likely the iDeal/linear order id (not Operative). Not proven.

## 20. Salesforce iDeal ID

- **MVP row / fill:** 25 (D,B,C 'iDeal ID' / 'GAB Deal ID')
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE + SECONDARY-XLSX + VERIFIED-DATA
- **Decision ref:** D-12
- **Field Logic column:** ideal_id (sample_sf col T)
- **In sample sheet as RAW?:** Y (T)
- **CARL silver/gold column:** NAME-MATCH: Northstar silver gab_deal_id / deal_id (Linear)

**Looker logic / definition**

Legacy broadway_io_id_c label 'iDeal ID' = ${TABLE}.broadway_io_id_c <- ETL opp.BROADWAY_IO_ID_C ('ideal id'). Current LookML: ${TABLE}.IDEAL_DEAL_ID (secondary workbook). Non-null: Linear 16,025 / Digital 23. Description in legacy: attribution field between linear and digital sponsorships (CNN).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L704-710 [dimension broadway_io_id_c 'iDeal ID']`
  ```
  ${TABLE}.broadway_io_id_c
  ```

**Live vs legacy / observations**

Column renamed BROADWAY_IO_ID_C -> IDEAL_DEAL_ID between legacy and current. MVP shows iDeal ID joins to GAB Deal ID on the linear side.

## 21. Salesforce Placeholder Operative Order ID

- **MVP row / fill:** 36 (D 'Operative Order ID')
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA (all null)
- **Decision ref:** D-12
- **Field Logic column:** not in Field Logic
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy placeholder_operative_order_id <- ETL custom.Placeholder_Operative_Order_ID (SF_CUSTOM_FIELD_NAME_PIVOT_MAP_V). 100% NULL in this export (0/23,756).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L697-701 [dimension placeholder_operative_order_id]`
  ```
  ${TABLE}.placeholder_operative_order_id
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L171`
  ```
  custom.Placeholder_Operative_Order_ID,
  ```

**Live vs legacy / observations**

MVP row 36 is green although the export has zero populated values - cannot be validated from this sample.

## 22. Salesforce Sales Order ID

- **MVP row / fill:** 35 (D,E green)
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-12
- **Field Logic column:** sales_order_id (sample_sf col S)
- **In sample sheet as RAW?:** Y (S)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy opp_sales_order_id label 'Sales Order ID' <- ETL site_month.OPERATIVE_ORDER_ID_C. NULL on 926 rows (Linear 724, Digital 202). Unique key with Opp ID + Activity Quarter + Ad Type + Property Detail (23,756 distinct).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L412-423 [dimension opp_sales_order_id 'Sales Order ID']`
  ```
  ${TABLE}.opp_sales_order_id
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L113`
  ```
  site_month.OPERATIVE_ORDER_ID_C AS OPP_SALES_ORDER_ID,
  ```

**Live vs legacy / observations**

Join key to Op1 Sales Order ID (cross-system link). Null for 926 rows -> those cannot link to Op1.

## 23. Salesforce Ad Type

- **MVP row / fill:** 49 (D: no fill)
- **Looker field kind:** dimension (native CASE)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-02
- **Field Logic column:** ad_type (Field Logic!D16,D17)
- **In sample sheet as RAW?:** Y (K)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy: Social Seeding->LaunchPad; Audio->Podcast; else ad_type. <- ETL ad_type.name (AD_TYPE_V on site_month.ad_type_c). Null 724 in export (all Linear).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L4-38 [dimension ad_type 'Ad Type']`
  ```
  CASE WHEN ${TABLE}.ad_type = 'Social Seeding' THEN 'LaunchPad' WHEN ${TABLE}.ad_type = 'Audio' THEN 'Podcast' ELSE ${TABLE}.ad_type END
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L114`
  ```
  ad_type.name as AD_TYPE,
  ```

**Live vs legacy / observations**

Used by Field Logic placeholder_flag ('Placeholder') and production_fee_flag (LIKE '%prod%') - not in MVP list.

## 24. Salesforce Record Type

- **MVP row / fill:** 3 ('Record Type')
- **Looker field kind:** custom dimension (current LookML, not on disk)
- **Status:** SECONDARY-XLSX + CHAT-ONLY + VERIFIED-DATA (values)
- **Decision ref:** D-05
- **Field Logic column:** record_type (Field Logic!D6)
- **In sample sheet as RAW?:** Y (C)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Secondary workbook: Linear for RECORD_TYPE_ID 012Vq000002N4ubIAC; Digital for NULL id before FILE_DT 2026-05-04 or ids 012Vq000002N4rNIAS / 012Vq000002N4szIAC; else Other. Export values: Linear 16,231 / Digital 7,525 (no 'Other').

**Legacy evidence:** none in the legacy repo.

**Live vs legacy / observations**

Hard-coded IDs + date cutoff (risk R-01). IDs also appear in the pasted chat (CHAT-ONLY) and match.

## 25. Salesforce  Historical Snapshot Filter

- **MVP row / fill:** 50 (D: no fill)
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA
- **Decision ref:** D-13
- **Field Logic column:** snapshot_date (Field Logic!D7)
- **In sample sheet as RAW?:** Y (W)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy file_date_date = ${TABLE}.FILE_DT (label ' Historical Snapshot Filter'); the wbd_salesforce_reporting variant shows FILE_DT minus 1 day. Export has ONE value only (2026-10-16): a current-day filter, not a history.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L213-218 [dimension file_date_date ' Historical Snapshot Filter']`
  ```
  ${TABLE}.FILE_DT
  ```
- `looker-inventory-analytics/views/base.wbd_salesforce_reporting.view.lkml:L133-138 [dimension file_date_date ' Historical Snapshot Filter']`
  ```
  dateadd('day',-1, CAST(${TABLE}.FILE_DT as date))
  ```

**Live vs legacy / observations**

Label in export has a double space ('Salesforce  Historical ...'). Snapshots must be append-mode with a current-state view (Jason).

## 26. Salesforce Workflow Status

- **MVP row / fill:** 16 (D green)
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE + CHAT-ONLY (availability) + NOT FOUND (view def)
- **Decision ref:** D-04
- **Field Logic column:** workflow_status (Field Logic!D15)
- **In sample sheet as RAW?:** Y (E)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy workflow_status <- ETL workflowStatus.order_status from DAAP_RPT.oper_etl_orders_activity_order_status_mappping_V joined on FILE_DATE + OPERATIVE_ORDER_ID_C. View DEFINITION is not in the repo. 15 values; 929 null of 23,756.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L47-52 [dimension workflow_status 'Workflow Status']`
  ```
  ${TABLE}.workflow_status
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L169`
  ```
  workflowStatus.order_status as WORKFLOW_STATUS,
  ```

**Live vs legacy / observations**

Aishwarya (CHAT-ONLY): Workflow Status NOT available in Salesforce silver. Yet required by lifecycle_state (reproduces Status Group 100%).

## 27. Salesforce Deal Type

- **MVP row / fill:** 5 (all green)
- **Looker field kind:** dimension (native)
- **Status:** LEGACY-SOURCE + VERIFIED-DATA + MISMATCH
- **Decision ref:** D-03
- **Field Logic column:** deal_type (iDeal Field Logic row 137; Field Logic!D76 uses it for LeftSide)
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** NAME-MATCH: Northstar silver has buy_type (Linear) - no deal_type column

**Looker logic / definition**

Legacy deal_type = ${TABLE}.DEAL_TYPE <- ETL opp.WARNER_DEAL_TYPE_C. In export: NULL on ALL 16,231 Linear rows; populated only on Digital (7,525 rows, 12 values).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L590-608 [dimension deal_type]`
  ```
  ${TABLE}.DEAL_TYPE
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L125`
  ```
  opp.WARNER_DEAL_TYPE_C AS DEAL_TYPE,
  ```

**Live vs legacy / observations**

MVP 'Deal Type' is green on all 4 tables, but for Linear it is a different concept (iDeal deal type vs SF digital deal type). Field Logic renames iDeal 'Deal Type' to 'Sold Type' (Field Logic row 64).

## 28. Buyer_AE

- **MVP row / fill:** 20 (D yellow 'Primary AE (Buying AE)')
- **Looker field kind:** custom dimension
- **Status:** LEGACY-SOURCE + SECONDARY-XLSX + VERIFIED-DATA
- **Decision ref:** D-14
- **Field Logic column:** primary_ae (sample_sf col Q 'Primary AE')
- **In sample sheet as RAW?:** Y (Q)
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy primary_ae = ${TABLE}.name (user.name of opp.primary_ae_c). Current LookML (secondary workbook): for the Linear record type primary_ae = THIRD_NAME; else NAME. Export 'Buyer_AE' null 724 (all Linear). Same person as Planning_AE on 19,506 rows.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L56-61 [dimension primary_ae 'Primary AE']`
  ```
  ${TABLE}.name
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L157`
  ```
  user.name AS NAME,
  ```

**Live vs legacy / observations**

Role permutation by record type (R-02): Name/SECOND_NAME/THIRD_NAME mean different roles on Linear. Meeting: ingest all 3 AEs (Buying/Client/Planning).

## 29. Client_AE

- **MVP row / fill:** 21 (D RED: 'not avail, only alternate AE')
- **Looker field kind:** custom dimension
- **Status:** MISMATCH + VERIFIED-DATA
- **Decision ref:** D-14
- **Field Logic column:** not in Field Logic
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy secondary_ae = ${TABLE}.SECOND_NAME (usersec.name of opp.secondary_ae_c). Current LookML: Linear -> NAME, else SECOND_NAME (secondary workbook). Null 1,659 (724 Linear + 935 Digital).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L63-68 [dimension secondary_ae 'Secondary AE']`
  ```
  ${TABLE}.SECOND_NAME
  ```

**Live vs legacy / observations**

MVP marks RED ('not avail') but the Looker export HAS the column populated (Digital 6,613 of 7,548). Contradiction to raise with Arlene/Rose.

## 30. Planning_AE

- **MVP row / fill:** 22 (D RED: 'not avail, only alternate AE')
- **Looker field kind:** custom dimension
- **Status:** MISMATCH + VERIFIED-DATA
- **Decision ref:** D-14
- **Field Logic column:** not in Field Logic
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** not found in provided evidence

**Looker logic / definition**

Legacy tertiary_ae = ${TABLE}.THIRD_NAME (userthi.name of opp.tertiary_ae_c). Current LookML: Linear -> SECOND_NAME, else THIRD_NAME. Null 1,808 (724 Linear + 1,084 Digital).

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L70-75 [dimension tertiary_ae 'Tertiary AE']`
  ```
  ${TABLE}.THIRD_NAME
  ```

**Live vs legacy / observations**

Same contradiction as Client_AE (MVP red but export populated).

## 31. Salesforce Net Projections

- **MVP row / fill:** 57 (D green)
- **Looker field kind:** measure
- **Status:** LEGACY-SOURCE + VERIFIED-DATA + CHAT-ONLY
- **Decision ref:** D-11
- **Field Logic column:** forecasted_value (Field Logic!D23,D24)
- **In sample sheet as RAW?:** Y (X)
- **CARL silver/gold column:** CHAT-ONLY: rev_net (fact_pipeline_sf, CARL-3949)

**Looker logic / definition**

Looker: SUM(forecasted_value) (legacy measure 'projection'). forecasted_value <- ETL SUM(site_month.PUBLISHED_REVENUE_FM_C). Weekly check: Net Projections is numeric in export; sum of rows = 4,516,462,794.61 equals the grand-total row exactly.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L803-808 [measure projection 'Net Projections']`
  ```
  ${forecasted_value}
  ```
- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L407-410 [dimension forecasted_value]`
  ```
  ${TABLE}.forecasted_value
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L174`
  ```
  SUM(site_month.PUBLISHED_REVENUE_FM_C) as FORECASTED_VALUE,
  ```

**Live vs legacy / observations**

Aishwarya (CHAT-ONLY): 'Net Projections' not available in Salesforce silver. Mike's fix (CHAT-ONLY): rev_net = sum(cast(smb0.published_revenue_fm__c ...)). Silver money is decimal(38,15) (CHAT-ONLY).

## 32. Salesforce Net Weighted Projections

- **MVP row / fill:** 58 (D green)
- **Looker field kind:** measure
- **Status:** LEGACY-SOURCE + VERIFIED-DATA + CHAT-ONLY
- **Decision ref:** D-11
- **Field Logic column:** weighted_scheduled_pipeline (Field Logic!D22,D25)
- **In sample sheet as RAW?:** Y (Y)
- **CARL silver/gold column:** CHAT-ONLY: net_weighted_projections (fact_pipeline_sf)

**Looker logic / definition**

Looker: SUM(weighted_scheduled_pipeline); ETL SUM(PUBLISHED_REVENUE_FM_C * opp.probability / 100). Weighted/Net ratio per row is a clean ladder: 1.00 (9,376), 0.00 (3,729), 0.95 (2,317), 0.65 (1,710), 0.15 (829), 0.20 (785), 4 other. Grand total 2,571,115,093.29.

**Legacy evidence (file:lines, SQL verbatim, whitespace collapsed)**

- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L810-816 [measure weighted_projection 'Net Weighted Projections']`
  ```
  ${weighted_scheduled_pipeline}
  ```
- `looker-inventory-analytics/views/base.salesforce_reporting.view.lkml:L577-580 [dimension weighted_scheduled_pipeline]`
  ```
  ${TABLE}.weighted_scheduled_pipeline
  ```
- `looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql:L175`
  ```
  SUM(site_month.PUBLISHED_REVENUE_FM_C * opp.probability / 100) as WEIGHTED_SCHEDULED_PIPELINE,
  ```

**Live vs legacy / observations**

Mike (CHAT-ONLY): net_weighted_projections = ... * opp.probability/100. Aishwarya (CHAT-ONLY): not available in SF silver.

## 33. Salesforce Linear Total Amount

- **MVP row / fill:** 59 (D: no fill; typo 'Linear Total mount')
- **Looker field kind:** measure
- **Status:** SECONDARY-XLSX + CHAT-ONLY + VERIFIED-DATA
- **Decision ref:** D-11
- **Field Logic column:** not in Field Logic
- **In sample sheet as RAW?:** N
- **CARL silver/gold column:** CHAT-ONLY: linear_total_amount (fact_pipeline_sf)

**Looker logic / definition**

Secondary workbook: linear_total_amount = COALESCE(LINEAR_TOTAL_AMOUNT, TOTAL_ESTIMATED_AMOUNT); measure = SUM(...). In export non-zero ONLY for Linear (11,694 rows); grand total 2,539,147,914.48. Not in the legacy repo.

**Legacy evidence:** none in the legacy repo.

**Live vs legacy / observations**

Mike (CHAT-ONLY): linear_total_amount = ... * 0.85. Aishwarya (CHAT-ONLY): not available in SF silver.
