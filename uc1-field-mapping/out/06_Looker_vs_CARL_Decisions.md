# 06 - Looker vs CARL: decisions for Jason

Looker is the source of truth. Each row is a measured or evidenced difference; options are listed, no choice has been made.

## D-01 - Market Type (Op1)

- **Finding (evidence):** Looker Op1 Market Type = is_upfront / is_dr / else Scatter. Field Logic/CARL = derive from Classification text. They disagree on 4,683 of 13,285 comparable rows (35%), $469.8M of $1,341.0M net revenue in the export (3,125 rows Looker=Upfront but classification says Scatter; 1,279 the reverse).
- **Options for Jason:** A) Keep Looker's logic (needs UPFRONT_TYPE_OP_V + is_dr inputs in silver). B) Adopt Classification-derived (change Looker or document variance).
- **Why it matters:** Looker is source of truth per Jason; this needs his explicit pick.
- **Evidence:** VERIFIED-DATA

## D-02 - Classification not on MVP list

- **Finding (evidence):** MVP row 19 (Classification) has no fill for Pipeline and Digital, yet Market Type, UF Year, uf_group(Linear) and direct_response_flag all derive from it. Same for Ad Type (row 49) and Property Detail (row 44).
- **Options for Jason:** Add Classification, Ad Type, Property Detail to MVP, or accept that derived fields cannot be validated.
- **Why it matters:** Dependency inversion; raised in meeting ('fields in Field Logic not in MVP').
- **Evidence:** VERIFIED-DATA + SHEET

## D-03 - Deal Type meaning differs by platform

- **Finding (evidence):** SF Deal Type: NULL on all 16,231 Linear rows, populated for Digital only (12 values). Linear (iDeal) deal type is a different field; Field Logic renames it 'Sold Type'. Op1 Deal Type is an order custom field (IDs 41/214), 'N/A' on 11,418 rows. MVP shows Deal Type green on all 4 tables.
- **Options for Jason:** Define one conformed deal_type with per-source definitions, or split into sold_type / deal_type.
- **Why it matters:** Prevents false 'converged' claim.
- **Evidence:** VERIFIED-DATA + SHEET

## D-04 - Salesforce lifecycle (Status Group) inputs

- **Finding (evidence):** Status Group needs Stage, Projection Rank, Workflow Status and sales_division (4 fields; Field Logic rule reproduces Looker 100%). Aishwarya (CHAT-ONLY) says Workflow Status is not available in SF silver and Opportunity Stage is not available in Op1 silver; MVP marks Op1 Workflow Status RED. Live Looker has Prospecting as a 4th status; legacy STAQ view has 3.
- **Options for Jason:** Confirm sources for Workflow Status (order-status mapping view) and sales_division, or define a lifecycle without them.
- **Why it matters:** Arlene: do not remove the lifecycle fields.
- **Evidence:** VERIFIED-DATA + CHAT-ONLY

## D-05 - Platform override

- **Finding (evidence):** Looker Platform differs from Record Type on 23 rows (Digital Media 11, BR 9, Nascar 3). Field Logic dropped the override saying 7 rows with $0 projection. Export check: 23 rows, summed Net Projections $0 - so revenue is unaffected in this sample, but dimension counts (Platform, uf_group, sales_division) differ for those 23 rows.
- **Options for Jason:** Keep Looker override (list the networks) or document the 23-row difference.
- **Why it matters:** Looker is source of truth.
- **Evidence:** VERIFIED-DATA

## D-06 - uf_group (SF and Op1) - 6 differences

- **Finding (evidence):** T1: Field Logic emits 'Digital - Sports' for Turner Sports; Looker never does (263 rows -> 'Sports Digital - Non-NCAA'). T2: 'TNT/TBS Linear Spon' -> Field Logic 'Linear Spon', Looker 'Digital - WBD Stream' (18 rows). T3: Looker WBD Stream also holds 165 rows whose Property Detail is outside WBDStreamSites (WarnerMedia Family 69, Run of WBD 26, Turner Entertainment 20, ...). T4: Looker D+ = legacy Discovery+ Flag (90/90 exact) - Field Logic puts D+ on Discovery+ site only. T5: 193 'Sports Linear - NCAA' rows with NULL Property Detail (186 have an 'NCAA Linear ...' opportunity name). T6: iDeal LeftSide lists 'DDV','Syndication','USH' linear groups that Looker SF never emits (Looker has DDL).
- **Options for Jason:** Align CARL uf_group to Looker's 12 values; add the opportunity-name rule for NCAA Linear and the Discovery+ flag.
- **Why it matters:** Mike fixed part on Oct 15-16; remaining rows need Looker SQL (CHAT-ONLY) to close.
- **Evidence:** VERIFIED-DATA + LEGACY-SOURCE + SHEET

## D-07 - Property Detail NULL on Linear

- **Finding (evidence):** 724 rows (all Linear) have NULL Property Detail and Property; 193 of them are in 'Sports Linear - NCAA' by opportunity name.
- **Options for Jason:** Accept NULL or default (e.g. 'Unmapped').
- **Why it matters:** 
- **Evidence:** VERIFIED-DATA

## D-08 - Activity Quarter / Activity date

- **Finding (evidence):** Export 'YYYY-MM' quarter-start months; legacy 'Activity' = WM SF end_date else month; current LookML = first month of broadcast quarter for Linear (secondary). MVP marks yellow.
- **Options for Jason:** Decide business meaning (broadcast vs calendar) per platform.
- **Why it matters:** 
- **Evidence:** SECONDARY-XLSX + VERIFIED-DATA

## D-09 - Agency naming

- **Finding (evidence):** SF 'Agency' vs 'Buying Agency' (linear) vs 'Planning/Upfront Agency'; Op1 Agency strips ' (digits)'. Linear silver has buying_agency (clean) and buying_agency_bi.
- **Options for Jason:** One conformed agency name rule + whether SF Agency = billing or buying agency.
- **Why it matters:** 
- **Evidence:** LEGACY-SOURCE + SECONDARY-XLSX

## D-10 - Mega Agency / holdco

- **Finding (evidence):** Production cascade COALESCE(INSIGHT_DIMAGENCY.parentagency, SF_MEGA_AGENCY.mega_agency, PI_AGENCY_MAPPING...) - mapping tables are not on disk. Field Logic uses a SIMPLIFIED COALESCE(...,'INDEPENDENT'). Export: Op1 910 null / 57 distinct; SF 719 null / 115 distinct.
- **Options for Jason:** Port the PI_ mapping tables (Field Logic!D20 says that is 'the actual ask').
- **Why it matters:** 
- **Evidence:** LEGACY-SOURCE + SHEET

## D-11 - Money fields: gross/net/weighted/linear total

- **Finding (evidence):** CHAT-ONLY: Mike nulled total_amt_net, set total_amt_gross = cost__c, weighted = x probability/100, linear_total_amount = x 0.85. Aishwarya: Net Projections, Net Weighted, Linear Total Amount not available in SF silver. Export: Linear Total Amount non-zero only for Linear.
- **Options for Jason:** Confirm each money column's source and whether the x0.85 and null conventions are intended vs Looker.
- **Why it matters:** Not verifiable until the chat SQL is saved to evidence/.
- **Evidence:** CHAT-ONLY + VERIFIED-DATA

## D-12 - Cross-system keys

- **Finding (evidence):** SF Sales Order ID null on 926 rows; iDeal ID non-null Linear 16,025 / Digital 23; Placeholder Operative Order ID 100% null; Op1 Opportunity ID null 618 and SF stage unresolved on 679.
- **Options for Jason:** Define which keys are mandatory for pipeline<->booked joins.
- **Why it matters:** 
- **Evidence:** VERIFIED-DATA

## D-13 - Snapshots

- **Finding (evidence):** Export has a single Historical Snapshot value. Jason: ingest as append snapshots with a current-state view. Op1 has no snapshot date (Field Logic!D28 'TO BUILD').
- **Options for Jason:** Confirm snapshot_date semantics (file_dt vs file_dt-1).
- **Why it matters:** 
- **Evidence:** LEGACY-SOURCE + SHEET

## D-14 - AE roles

- **Finding (evidence):** Looker Linear permutes Name/Second/Third; MVP marks Client/Planning AE red; export populates them. Op1 Primary AE = SPLIT_PART(name,'_',1).
- **Options for Jason:** Confirm ingestion of all 3 AEs and the Linear permutation.
- **Why it matters:** Jason: ingest all 3 AEs.
- **Evidence:** SECONDARY-XLSX + VERIFIED-DATA + MISMATCH

## D-15 - Op1 Site depends on targeting

- **Finding (evidence):** Looker Site = forecast_category with an override from the discovery_inventory_package targeting listagg (ID 1774).
- **Options for Jason:** Bring targeting into silver or drop the override and document variance.
- **Why it matters:** 
- **Evidence:** LEGACY-SOURCE

## D-16 - Op1 revenue needs proration/currency/pacing

- **Finding (evidence):** Net/Gross/Qty measures come from the om_con_dy line-day expansion + currency + custom pacing view.
- **Options for Jason:** Confirm CARL silver grain is line-day and includes currency + pacing logic.
- **Why it matters:** 
- **Evidence:** LEGACY-SOURCE

## D-17 - Op1 SSP and other custom fields

- **Finding (evidence):** SSP = custom field 204 (wbd), populated on 742 rows only.
- **Options for Jason:** Confirm custom-field extraction in silver (see Custom_Fields workbook).
- **Why it matters:** 
- **Evidence:** LEGACY-SOURCE + VERIFIED-DATA

## Computed tests behind the uf_group decisions

| Test | Result (computed from export) |
|---|---|
| T1 Field Logic uf_group branch 1 emits 'Digital - Sports' for GenericSports ('Turner Sports'); Looker values never include it | {"looker_has_value_Digital_-_Sports": false, "digital_rows_property_detail_Turner_Sports": 263, "looker_uf_group_for_those_rows": {"Sports Digital - Non-NCAA": 263}} |
| T2 'Linear Spon' sites -> Field Logic 'Linear Spon'; Looker gives 'Digital - WBD Stream' | {"rows": 18, "looker_uf_group": {"Digital - WBD Stream": 18}, "looker_has_value_Linear_Spon": false} |
| T3 Looker 'Digital - WBD Stream' is broader than Field Logic WBDStreamSites | {"looker_rows": 2748, "rows_with_property_detail_in_WBDStreamSites": 2583, "rows_outside_WBDStreamSites": 165, "outside_breakdown": {"WarnerMedia Family": 69, "Run of WBD": 26, "Turner Entertainment": 20, "TNT Linear Spon": 13, "Digital Media": 11, "TBS Linear Spon": 5, "FOOD_site": 5, "TRAVEL_site": 4, "HGTV": 3, "Food": 2, "Food Network": 2, "Run of WBD Programmatic": 2, "HGTV_SV": 1, "Adult Swim": 1, "Cartoon Network": 1}} |
| T4 'Digital - D+' in Looker for 'Discovery Networks' rows (Field Logic DPlusSites = Discovery+/Discovery Plus only) | {"looker_D+_rows": 90, "looker_D+_property_detail": {"Discovery Networks": 90}, "discovery_networks_rows": 1216, "discovery_networks_split": {"Digital - WBD Stream": 1126, "Digital - D+": 90}} |
| T5 Linear non-sports uf_group: Field Logic 'Linear - '\|\|classification (DDL/Demo Direct/Premiere) else Traditional | {"rows_tested": 13190, "matches": 13190, "mismatch_detail": []} |
| T6 Linear rows with Property Detail NULL | {"rows": 724, "by_uf_group": {"Linear - Traditional": 443, "Linear - DDL": 79, "Linear - Demo Direct": 4, "Linear - Premiere": 5, "Sports Linear - NCAA": 193}, "note": "Field Logic property_detail = COALESCE(sports_property, network) cannot be NULL for a row that Looker puts in 'Sports Linear - NCAA' (needs sports_property or network='NBA TV'); Looker Property Detail is NULL on these rows."} |
| T7 Platform override: Looker Platform != Record Type | {"rows": 23, "by_property_detail": {"BR": 9, "Nascar": 3, "Digital Media": 11}, "note": "Field Logic!F6 says only network 'Digital Media' is overridden; the export shows BR and Nascar rows overridden as well."} |
| T8 Property: Looker Property vs Field Logic COALESCE(PropMap, SiteMap, NetMap, raw) using Property Detail as the key | {"rows_tested": 23032, "matches": 23032, "mismatch_detail": []} |
| T9 Observed driver of the 193 'Sports Linear - NCAA' rows with NULL Property Detail (pattern in Opportunity Name; Looker SQL not on disk) | {"rows": 193, "opp_name_starts_with_'NCAA Linear'": 186, "other_name_prefixes": {"MM - NCAA -Cop": 2, "Scatter-2026-O": 1, "Upfront Broadc": 4}} |
| T10 Legacy LookML discoveryplusflag vs live Looker uf_group 'Digital - D+' (Digital record-type rows) | {"rows_tested": 7525, "agree": 7525, "looker_D+_and_flag_yes": 90, "looker_D+_but_flag_no": 0, "looker_not_D+_but_flag_yes": 0, "rule": "(site IN ('Discovery Networks','DCI ENT') AND LOWER(opportunity name) LIKE any of '%d+%','%discovery+%','%dplus%','%discoveryplus%') OR site='Discovery+'", "source": "legacy base.salesforce_reporting.view.lkml:712-720 (uses opportunity_name_id); Op1 version uses sales_order_name"} |
| T11 Op1: legacy discoveryplusflag evaluated on the Op1 export (Site, Order Name) | {"Discovery+\|flag=Yes": 865, "DCI ENT\|flag=No": 1123, "DCI ENT\|flag=Yes": 21} |