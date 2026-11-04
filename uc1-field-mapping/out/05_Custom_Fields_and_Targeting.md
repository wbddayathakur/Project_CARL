# 05 - Custom fields, targeting, UDF_OP_VERTICAL, reference lists

_Generated from `UC1_Custom_Fields_Catalog.xlsx`; all sheets are reproduced below._

## Operative order-level custom fields (36 derived fields from view oper_sales_order_custom_field_t)

Plain pass-through columns of the table (api_name, created_by, ...) are listed in sheet 04 raw columns below; only DERIVED custom fields appear here.

| Level | Looker field | Label | Kind | custom_field_id(s) | custom_field_name(s) | source filter | Looker expression | Citation | Backing table |
|---|---|---|---|---|---|---|---|---|---|
| ORDER | legacy_wm_payment_type |  | dimension | 36 |  | wm | CASE WHEN ${custom_field_id} IN (36) and ${source} = 'wm' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L71-75 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | legacy_wm_wbd_payment_type |  | dimension | 220 |  | wbd | CASE WHEN ${custom_field_id} IN (220) AND ${source} = 'wbd' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L77-81 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | wbd_payment_type |  | dimension | 16 |  | wbd | CASE WHEN ${custom_field_id} IN (16) AND ${source} = 'wbd' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L83-87 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | payment_type | Warner Payment Type | dimension |  |  |  | Coalesce(${legacy_wm_payment_type},${legacy_wm_wbd_payment_type}) | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L90-97 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | payment_type_wbd | Payment Type | dimension |  |  |  | ${wbd_payment_type} | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L100-106 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | guaranteed_demo | Target Demo | dimension | 93, 125 |  |  | CASE WHEN ${custom_field_id} IN (93,125) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L110-116 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | legacy_sales_oid | Legacy WM Sales Order ID | dimension | 230 |  |  | CASE WHEN ${custom_field_id} IN (230) THEN TRY_TO_NUMBER(${custom_field_value}) ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L118-124 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | invoice_affidavit | Invoice/Affidavit | dimension |  | Invoice/Affidavit |  | CASE WHEN ${custom_field_name} = 'Invoice/Affidavit' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L127-134 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | deal_type | Deal Type | dimension | 41, 214 |  |  | CASE WHEN ${custom_field_id} IN (41,214) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L136-156 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | nba_deal_type | NBA Deal Type | dimension |  |  |  | CASE WHEN ${deal_type} = 'NBA OMP' THEN 'NBA OMP' WHEN ${deal_type} = 'N/A' THEN 'Non NBA OMP' ELSE ${deal_type} END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L158-170 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | various_trig |  | dimension |  |  |  | CASE WHEN LOWER(${custom_field_name}) = 'various' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L172-176 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | various_flag | Is Various | dimension |  |  |  | ${various_trig} = 'Yes' | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L178-184 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | converge_spon | Converged Sponsorship (Yes/No) | dimension | 298 |  | wbd | CASE WHEN ${custom_field_id} IN (298) AND ${source} = 'wbd' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L186-193 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | wbd_iq_trig |  | dimension | 228, 122 |  |  | CASE WHEN ${custom_field_id} IN (228,122) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L197-201 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | wbd_iq_flag | Is WBD iQ | dimension |  |  |  | ${wbd_iq_trig} = 'Yes' | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L204-210 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | upfront |  | dimension |  | Upfront |  | CASE WHEN ${custom_field_name} = 'Upfront' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L212-216 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | upfront_type |  | dimension |  | Upfront Type |  | CASE WHEN ${custom_field_name} = 'Upfront Type' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L218-222 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | upfront_type_old |  | dimension |  | Upfront Type_Old |  | CASE WHEN ${custom_field_name} = 'Upfront Type_Old' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L224-228 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | upfront_type_fix |  | dimension |  |  |  | COALESCE(${upfront},${upfront_type},${upfront_type_old}) | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L230-234 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | is_upfront | Upfront Type | dimension |  |  |  | ${upfront_type_fix} | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L237-245 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | ssp | SSP | dimension | 204 |  | wbd | CASE WHEN ${custom_field_id} IN (204) AND ${source} = 'wbd' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L248-254 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | classification | Classification | dimension |  |  |  | CASE WHEN LOWER(${custom_field_name}) LIKE '%classification%' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L256-264 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | is_linear_addressable |  | dimension |  |  |  | ${classification} = 'Linear Addressable' | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L266-271 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | order_level_target | Order Level Target | dimension |  | Order Level Target; Warner Order Level Target |  | CASE WHEN ${custom_field_name} = 'Order Level Target' OR ${custom_field_name} = 'Warner Order Level Target' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L274-280 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | opportunity_id | Opportunity ID | dimension |  | Opportunity ID; Warner SF Deal ID |  | CASE WHEN ${custom_field_name} = 'Opportunity ID' OR ${custom_field_name} = 'Warner SF Deal ID' THEN COALESCE(${custom_field_value},${oper_sales_order_t.external_opportunity_id}) ELSE ${oper_sales_order_t.external_opportunity_id} END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L285-293 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | sales_split | Sales Split | dimension | 253, 33 |  |  | CASE WHEN ${custom_field_id} IN (253,33) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L296-303 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | tentpole_event | Sponsorship Event | dimension | 295 |  | wbd | CASE WHEN ${custom_field_id} IN (295) AND ${source} = 'wbd' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L306-313 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | ideal_deal_id | iDeal Deal ID | dimension | 147 |  | wbd | CASE WHEN ${custom_field_id} IN (147) AND ${source} = 'wbd' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L315-321 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | sales_split_number |  | dimension |  |  |  | CASE WHEN lower(${sales_split}) = 'paste ae split here using - http://harbor.turner.com/harborwebsearch' Then 0 ELSE regexp_count(regexp_replace(${sales_split}, '/\\[.*', ''), '/') END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L324-331 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | sales_split_percentage |  | dimension |  |  |  | case when ${sales_split_number}>0 then 1/${sales_split_number} else 0 end | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L333-338 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | vod_type | VOD Bucket | dimension |  |  |  | CASE WHEN ${deal_type} like '%Linear Cross Clearing%' THEN 'ADU' WHEN ${deal_type} Like '%Linear Led%' THEN 'Direct Linear' ELSE 'Digital' END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L342-353 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | is_programmatic |  | dimension |  |  |  | ${payment_type} = 'Indirect Sales' | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L356-361 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | vod_olv_fluidity | VOD/OLV Fluidity | dimension |  | VOD/OLV Fluidity |  | CASE WHEN ${custom_field_name} = 'VOD/OLV Fluidity' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L363-370 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | composite_key |  | dimension |  |  |  | CONCAT(CAST(${TABLE}.sales_order_id AS STRING), '_', CAST(${TABLE}.custom_field_id AS STRING)) | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L428-433 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | count |  | measure |  |  |  |  | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L435-438 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |
| ORDER | estimated_split_net_revenue |  | measure |  |  |  | ${sales_split_percentage}*${oper_sales_order_line_items_t.sum_net_cost} | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L441-448 | FINAL_OPERATIVE_WBD.OPER_SALES_ORDER_CUSTOM_FIELD_V |

## Operative line-item-level custom fields (21 derived fields)



| Level | Looker field | Label | Kind | custom_field_id(s) | custom_field_name(s) | source filter | Looker expression | Citation | Backing table |
|---|---|---|---|---|---|---|---|---|---|
| LINE ITEM | is_canceled | Is Canceled | dimension | 27 |  |  | (${custom_field_id} = '27' AND ${custom_field_value} = '1') | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L49-56 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | demo_guaranteed | Demo Guaranteed | dimension | 208, 38 | Line Level Intent |  | CASE WHEN ${custom_field_name} = 'Line Level Intent' OR ${custom_field_id} IN (208,38) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L59-66 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | mg_av_reason | Makegood/Added Value Reason | dimension | 115, 267 |  |  | CASE WHEN ${custom_field_id} IN (115,267) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L68-74 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | line_notes | Line Item Notes | dimension | 46, 25 |  |  | CASE WHEN ${custom_field_id} IN (46,25) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L76-81 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | show_exclusions |  | dimension |  | Show Exclusions; Warner Show Exclusions |  | CASE WHEN ${custom_field_name} IN ('Show Exclusions','Warner Show Exclusions') THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L84-89 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | site_exclusions |  | dimension |  | Site Exclusions; Warner Site Exclusions |  | CASE WHEN ${custom_field_name} IN('Site Exclusions','Warner Site Exclusions') THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L92-97 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | billable_third_party_server | Billable Third-Party Server | dimension |  | LIKE 'Billable Third-Party Server' |  | CASE WHEN ${custom_field_name} LIKE 'Billable Third-Party Server' THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L100-105 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | demo_composition_percentage | Planned Demo Comp % | dimension | 84, 184, 133 |  |  | CASE WHEN ${custom_field_id} IN (84,184,133) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L107-113 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | oo_matching_line_item_id | OO Matching Line Item ID | dimension | 282 |  |  | CASE WHEN ${custom_field_id} IN (282) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L115-121 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | order_id_rev_run | Original Order ID for Rev Run | dimension | 290 |  |  | CASE WHEN ${custom_field_id} IN (290) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L123-128 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | frequency_cap | Frequency Cap | dimension | 85, 258 |  | wbd, wm | ${custom_field_id} = 85 AND ${source} = 'wm' OR ${custom_field_id} = 258 AND ${source} = 'wbd' OR ${feq_cap_mea_fw.feq_cap_mea_fw} IS NOT NULL OR ${feq_cap_mea_fw_pg.feq_cap_mea_fw_pg} IS NOT NULL | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L130-143 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | nielsen_dar_id |  | dimension | 255, 47 |  |  | CASE WHEN ${custom_field_id} IN (255,47) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L146-151 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | nielsen_dar_platform |  | dimension | 113, 212 |  |  | CASE WHEN ${custom_field_id} IN (113,212) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L153-158 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | target_demo | Line Item - Target Demo | dimension | 132 |  |  | CASE WHEN ${custom_field_id} IN (132) THEN ${custom_field_value} ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L160-166 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | legacy_li | Legacy WM Line Item ID | dimension | 233 |  |  | CASE WHEN ${custom_field_id} IN (233) THEN TRY_TO_NUMBER(${custom_field_value}) ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L168-174 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | run_revenue_num |  | dimension | 288 |  |  | CASE WHEN ${custom_field_id} IN (288) THEN TRY_TO_NUMBER(${custom_field_value}) ELSE NULL END | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L176-179 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | run_revenue | Run Revenue | dimension |  |  |  | ${run_revenue_num} = 1 | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L181-187 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | composite_key |  | dimension |  |  |  | CONCAT(CAST(${TABLE}.sales_order_line_item_id AS STRING), '_', CAST(${TABLE}.custom_field_id AS STRING)) | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L272-276 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | demo_comp_number |  | dimension |  |  |  | ${demo_composition_percentage} | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L278-282 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | count |  | measure |  |  |  |  | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L284-287 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |
| LINE ITEM | demo_comp | Demo Composition % | measure |  |  |  | ${demo_composition_percentage} | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L289-295 | final_operative_wbd.oper_sales_order_line_item_custom_field_v |

## Operative product-level custom fields (5 derived fields; Ad Type / Buy Type)

Ad Type/Buy Type is read from DAAP_RPT.AD_TYPE_BUY_TYPE_PRODUCT_V (a view whose DDL is not in the evidence). The ETL reads the product custom field names 'Ad Type' and 'Buy Type' (02_op1_contracted_w_rate.sql L95/L99).

| Level | Looker field | Label | Kind | custom_field_id(s) | custom_field_name(s) | source filter | Looker expression | Citation | Backing table |
|---|---|---|---|---|---|---|---|---|---|
| PRODUCT | ad_type | Ad Type/Buy Type | dimension |  |  |  | CASE WHEN ${ad_type_default} = 'Video' THEN 'Video' WHEN ${ad_type_default} = 'TVE' THEN 'Video' WHEN ${ad_type_default} = 'Display' THEN 'Display' WHEN ${ad_type_default} = 'Asset Management Bill Back' THEN 'Asset Management Bill Back' WHEN ${ad_type_default} = 'Production Fee' THEN 'Production Fee' WHEN ${ad_type_default} = 'Mobile' THEN 'Display' WHEN ${ad_type_default} = 'VOD' THEN 'VOD' WHEN ${ad_type_default} = 'Branded Entertainment' THEN 'Branded Entertainment' WHEN ${ad_type_default} = 'Social' THEN 'Social' WHEN ${ad_type_default} = 'Native' THEN 'Native' WHEN ${ad_type_default} = 'Social Seeding' THEN 'LaunchPad' WHEN ${ad_type_default} = 'Talent Fee' THEN 'Talent Fee' WHEN ${ad_t | looker-inventory-analytics/views/base.oper_product_custom_field_t.view.lkml:L79-107 | DAAP_RPT.AD_TYPE_BUY_TYPE_PRODUCT_V |
| PRODUCT | ad_type2 | News Variables Ad Type | dimension |  |  |  | CASE WHEN lower(${product_name}) like '%mobile app%' THEN 'Mobile App' WHEN lower(${product_name}) like '%mobile web%' THEN 'Mobile Web' ELSE ${ad_type} END | looker-inventory-analytics/views/base.oper_product_custom_field_t.view.lkml:L110-121 | DAAP_RPT.AD_TYPE_BUY_TYPE_PRODUCT_V |
| PRODUCT | launchpad_flag | LaunchPad Flag | dimension |  |  |  | CASE WHEN lower(${ad_type_default}) != 'display' THEN CASE WHEN lower(${product_name}) = 'tastemade_pack production + rrss_ul' THEN 'No' WHEN lower(${product_name}) LIKE '%cnn^_chile^_ul^_redes sociales%' ESCAPE '^' THEN 'No' WHEN lower(${ad_type_default}) = 'social seeding' AND ${product_name} != 'TruTV UL_true[X] Sponsored Stream' THEN 'Yes' WHEN lower(${ad_type_default}) = 'branded entertainment' THEN 'Yes' WHEN lower(${product_name}) LIKE '%launch%pad%' THEN 'Yes' WHEN (lower(${product_name}) LIKE 'br%social%' AND lower(${product_name}) NOT LIKE'%twitter%') THEN 'Yes' WHEN lower(${product_name}) LIKE 'br%snapchat%' THEN 'Yes' WHEN lower(${product_name}) LIKE 'br%instagram%' THEN 'Yes' WH | looker-inventory-analytics/views/base.oper_product_custom_field_t.view.lkml:L123-160 | DAAP_RPT.AD_TYPE_BUY_TYPE_PRODUCT_V |
| PRODUCT | composite_key |  | dimension |  |  |  | CONCAT(CAST(${TABLE}.product_id AS STRING), '_', CAST(${TABLE}.custom_field_id AS STRING)) | looker-inventory-analytics/views/base.oper_product_custom_field_t.view.lkml:L207-212 | DAAP_RPT.AD_TYPE_BUY_TYPE_PRODUCT_V |
| PRODUCT | count |  | measure |  |  |  |  | looker-inventory-analytics/views/base.oper_product_custom_field_t.view.lkml:L224-227 | DAAP_RPT.AD_TYPE_BUY_TYPE_PRODUCT_V |

## Salesforce custom (_C) fields and pivoted custom fields used by the reporting view

The pivot SF_CUSTOM_FIELD_NAME_PIVOT_MAP_V definition is not in the repo. All _C columns are as written in the ETL SELECT (02_salesforce_stg_insert.sql). Current (renamed) columns RECORD_TYPE_ID, BUYING_AGENCY_NAME, PLANNING_AGENCY_NAME, UPFRONT_AGENCY_NAME, ORDER_ID, BRAND_NAME, ORDER_CPM, IDEAL_DEAL_ID, LINEAR_TOTAL_AMOUNT, TOTAL_ESTIMATED_AMOUNT are known only from the secondary workbook.

| Salesforce custom field (_C) | Source object | ETL mapping | Looker field | Citation | Status |
|---|---|---|---|---|---|
| Links_to_Placeholder | SF_CUSTOM_FIELD_NAME_PIVOT_MAP_V | ETL: custom.Links_to_Placeholder | salesforce_reporting.links_to_placeholder (label 'Links to Placeholder') | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| Placeholder_Operative_Order_ID | SF_CUSTOM_FIELD_NAME_PIVOT_MAP_V | ETL: custom.Placeholder_Operative_Order_ID | salesforce_reporting.placeholder_operative_order_id | same | LEGACY-SOURCE (100% null in 2026-10-16 export) |
| WARNER_DEAL_TYPE_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> DEAL_TYPE | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| WARNER_PAYMENT_TYPE_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> PAYMENT_TYPE | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| WARNER_SF_OPPORTUNITY_ID_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> OPP_ID | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| WARNER_OPPORTUNITY_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> OPP | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| BROADWAY_IO_ID_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> BROADWAY_IO_ID_C (iDeal ID) | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| CLASSIFICATION_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> UPF_VS_SCAT | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| UPFRONT_TYPE_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> UPF_TYPE | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| PAYMENT_TYPE_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> INVOICE_TYPE | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| PROJECTION_CHANGE_REASON_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> PROJECTION_CHANGE_REASON | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| CLOSED_LOST_CATEGORY_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> CLOSED_LOST_CATEGORY | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| COORDINATOR_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> VAR1 (Client Success Coordinator) | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| ACCOUNT_SPECIALIST_C -> user.name | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> VAR2 (Account Specialist) | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| DIGITAL_STRATEGIST_DSSI_C -> user.name | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> DSSI | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| TOTAL_LI_TRAFFICKED_C / TOTAL_LI_DELIVERY_C / ACTIVE_LI_TRAFFICKED_C / ACTIVE_LI_DELIVERY_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> TOTAL_LINE_TRAFF / TOTAL_LINE_DEL / ACTIVE_LINE_TRAFF / ACTIVE_LINE_DEL | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| total_proposed_revenue_sm_c | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> TOTAL_OP_PROP_REV | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| TOTAL_PUBLISHED_REVENUE_SM_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> TOTAL_TOTAL_PUBLISHED_REVENUE_SM_C | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| warner_sf_report_team_c | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> TEAM | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| warner_sf_vp_c | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> VP | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| warner_sf_division_c / user.division | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> DIVISION | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |
| PRIMARY_AE_OFFICE_REGION_C / PRIMARY_AE_OFFICE_C / SECONDARY_AE_OFFICE_C / TERTIARY_AE_OFFICE_C | OPPORTUNITY_V / SITE_MONTH_BREAKOUT_V / USER_V (typed Salesforce columns, '_C' = custom) | -> REGION / OFFICE / SECOND_OFFICE / THIRD_OFFICE | see Salesforce lineage workbook | looker-etl-carl/airflow/dags/revops_etl/salesforce/dml/02_salesforce_stg_insert.sql | LEGACY-SOURCE |

## Audience-targeting ID lists (divisor of Looker Net Revenue when audience targeting is selected)

DIFFERENCE: the Looker view includes WBD id 1697, the ETL list does not. Evidence: line numbers cited. Also VERIFY the chat-pasted live SQL (CHAT-ONLY) matches the Looker list.

| Use | source | targeting_id list | citation | behaviour |
|---|---|---|---|---|
| Looker audience divisor (oper_targeting_count) | wbd | 1494, 1551, 1550, 1556, 1501, 1499, 1500, 1635, 1231, 815, 721, 1625, 1682, 1674, 1697 | looker-inventory-analytics/views/base.dt_oper_targeting_count.view.lkml:L12 | target_count = avg over line of COUNT(DISTINCT targeting_option_name); applied to Net Revenue ONLY when audience_targeting is in the query |
| Looker audience divisor (oper_targeting_count) | wm | 1049, 1238, 1237, 1239, 1388, 1389, 1422 | looker-inventory-analytics/views/base.dt_oper_targeting_count.view.lkml:L13 | same |
| ETL audience_counts (om_con_dy) | wbd | 1494, 1551, 1550, 1556, 1501, 1499, 1500, 1635, 1231, 815, 721, 1625, 1682, 1674  (NO 1697) | looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql:L225 | COUNT(CASE WHEN ... THEN 1) per line item |
| ETL audience_counts (om_con_dy) | wm | 1049, 1238, 1237, 1239, 1388, 1389, 1422 | looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql:L220 | same |

## dt_oper_hbo_targeting: 26 LISTAGG columns (one string per line item)

Legacy view has 26 columns. The pasted live Op1 SQL (CHAT-ONLY) also had hbo_max_series_include_by_season_fw, which is NOT in the legacy view - the live view is newer. Site (export label) depends on discovery_inventory_package (ID 1774).

| # | column | targeting_id(s) | Looker label | group | description | citation | source |
|---|---|---|---|---|---|---|---|
| 1 | fw_gen_excl | 1380, 1524 | FreeWheel Genre Exclusions | Line Item | Grouping line item activity by genre. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L7 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 2 | fw_mv_rat_excl | 1382, 1526 | FreeWheel Movie Rating Exclusions | Line Item | Grouping line item activity by movie rating. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L8 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 3 | fw_mv_rat_incl_nc | 1383, 1547 | FreeWheel Movie Rating Inclusions - NR/NC-17 | Line Item | Grouping line item activity by movie rating. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L9 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 4 | fw_prof_excl | 1376, 1522 | FreeWheel Profile Exclusions | Line Item | Grouping line item activity by profile. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L10 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 5 | fw_tv_rat_excl | 1381, 1525 | FreeWheel TV Rating Exclusions | Line Item | Grouping line item activity by TV rating. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L11 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 6 | fw_con_age_excl | 1410, 1552 | FreeWheel Content Age Exclusions | Line Item | Grouping line item activity by age content rating. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L12 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 7 | hbo_aud_seg | 1422, 1556 | HBO Max Audience Segment | Line Item | Grouping line item activity by audience segment. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L13 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 8 | BR_inventory_package_include | 1793, 1794 | BR Inventory Package Include | Line Item | Grouping FW line items by untargeted video package vs sport targeted. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L14 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 9 | title_spon | 1746 | Max Title Sponsorship | Line Item | Showcasing lines that have less than 100% Title Sponsorship | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L15 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 10 | dplus_wbd_stream_title_spon | 1753 | D+/WBD Stream Title Sponsorship | Line Item | Showcasing D+/WBD Stream lines that have Title Sponsorship | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L16 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 11 | exclude_video_group_fw | 1206 | Exclude Video Group | Line Item | This field is sourced from Op1 | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L17 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 12 | exclude_site_group_fw | 1207 | Exclude Site Group | Line Item | This field is sourced from Op1 | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L18 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 13 | audience_segment | 1635 | Audience Segment Grouped | Line Item | This field is sourced from Op1 | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L19 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 14 | series_include | 1646 |  |  |  | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L20 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 15 | max_content_group_include | 1664 | Max Content Group Include | Line Item | This field is sourced from Op1 | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L21 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 16 | max_content_group_exclude | 1644 | Max Content Group Exclude | Line Item | This field is sourced from Op1 | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L22 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 17 | lwm_ent_title_spons_fw | 1763 | LWM ENT Title Sponsorship | Line Item | This field is sourced from Op1 | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L23 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 18 | max_advertiser_include_exclude | 1654 | Max Advertiser Include/Exclude (Op1) | Line Item | This field is sourced from Op1 | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L24 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 19 | news_ent_advertiser_include_exclude_fw | 1690 | News/ENT Advertiser Include/Exclude (Op1) | Line Item | This field is sourced from Op1 | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L25 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 20 | max_device_targeting | 1641 | Max Device Targeting | Line Item | This field is sourced from Op1 | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L26 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 21 | discovery_brand_include | 1819 | Discovery+ Brand Include (FW) | Line Item | Grouping line item activity by Discovery+ branding. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L27 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 22 | discovery_inventory_package | 1774 | Discovery Inventory Package | Line Item | Grouping line item activity by Discovery inventory packaging. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L28 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 23 | max_series_exclude_all_seasons | 1647 |  |  |  | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L29 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 24 | max_series_exclude_by_seasons | 1645 |  |  |  | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L30 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 25 | max_content_rating_exclude | 1660 | Max Content Rating Exclude | Line Item | Grouping line item activity by content rating. Please use 'contains' when filtering. | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L31 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |
| 26 | hbo_max_inventory_package | 1890 | HBO Max Inventory Package | Line Item | This field is sourced from Op1 | looker-inventory-analytics/views/base.dt_oper_hbo_targeting.view.lkml:L32 | FINAL_OPERATIVE_WBD.oper_sales_line_item_targeting_v (targeting_option_name per targeting_id) |

## Live Looker custom dimensions that have no LookML on disk



| Looker field | Where | Domain | What is proven / where it comes from | Evidence status | Decision |
|---|---|---|---|---|---|
| uf_group | Salesforce (Look 26238) | 12 values | NO LookML on disk. Reproduced pieces: Linear non-sports (13,190/13,190); D+ via legacy discoveryplusflag (90/90). Not reproduced: Sports/Linear NCAA with NULL Property Detail, WBD Stream breadth, Turner Sports. | VERIFIED-DATA (partial) + MISMATCH | D-06 |
| sales_division | Salesforce (Look 26238) | Linear / Sports / Digital | NO LookML on disk. Cannot be re-derived: raw sports_property/forecast_category/network not exported. | NOT RE-DERIVABLE | D-06 |
| Platform | Salesforce (Look 26238) | Linear / Digital | Equals Record Type except 23 rows (BR, Nascar, Digital Media). | VERIFIED-DATA + MISMATCH | D-05 |
| Property / Property Detail | Salesforce (Look 26238) | 56 / 66 values | Property = COALESCE(PropMap, SiteMap, NetMap, raw) of Property Detail on 100% of non-null rows. | VERIFIED-DATA | D-07 |
| UF Year | Salesforce (Look 26238) | 3 values | Regex [0-9]{2}/[0-9]{2} on Classification, else 'N/A' - 100%. | VERIFIED-DATA |  |
| Status Group | Salesforce (Look 26238) | Order / Pipeline / Prospecting / closed_lost | Field Logic lifecycle rule - 100%. | VERIFIED-DATA | D-04 |
| Market Type (SF) | Salesforce (Look 26238) | 7 values | Field Logic rule - 100%. | VERIFIED-DATA | D-01 |
| Record Type | Salesforce (current LookML) | Linear / Digital (/Other) | IDs 012Vq000002N4ubIAC (Linear); 012Vq000002N4rNIAS & 012Vq000002N4szIAC (Digital); NULL id before FILE_DT 2026-05-04 -> Digital (secondary workbook; same IDs in chat). | SECONDARY-XLSX + CHAT-ONLY | D-05 |
| Buyer_AE / Client_AE / Planning_AE | Salesforce (Look 26238) | AE names | Current LookML: Linear role permutation Name/Second/Third (secondary workbook). | SECONDARY-XLSX | D-14 |
| Linear Total Amount | Salesforce measure | number | COALESCE(LINEAR_TOTAL_AMOUNT, TOTAL_ESTIMATED_AMOUNT) summed (secondary workbook). | SECONDARY-XLSX | D-11 |
| Projection Rank (live CASE) | Salesforce | A,B,C,D,F,NULL | Live mapping reproduced from data (7 stages); the live CASE text is chat-only. | VERIFIED-DATA + CHAT-ONLY | D-04 |

## DAAP_RPT.UDF_OP_VERTICAL - 137 WHEN-branches parsed in order from legacy looker-etl-carl/snowflake/RA_UDF/op1_udf.sql

Field Logic says this is 'a Snowflake function we cannot read' - its definition IS in the legacy repo. First matching branch wins; unmatched -> the ELSE of the function (see source). Used by Looker 'Vertical' for Op1 (and Salesforce 'Digital Vertical').

| Order | Tested expression | Operator | Pattern | Returns |
|---|---|---|---|---|
| 1 | LOWER(forecast_category) | = | turner nba | Sports |
| 2 | LOWER(forecast_category) | = | turner sports | Sports |
| 3 | LOWER(forecast_category) | = | turner wbb | Sports |
| 4 | forecast_category | = | Adult Swim | Entertainment |
| 5 | forecast_category | = | Amo El Cine | Other/Intl |
| 6 | forecast_category | = | Bleacher Report | Sports |
| 7 | forecast_category | = | Bleacher Report Live | Sports |
| 8 | forecast_category | = | Bleacher Report UK | Sports |
| 9 | forecast_category | = | BoomLA.com | Other/Intl |
| 10 | forecast_category | = | CanalTBS.com | Other/Intl |
| 11 | forecast_category | = | Cartoon Network | Entertainment |
| 12 | forecast_category | = | Cartoon Network AR | Other/Intl |
| 13 | forecast_category | = | Cartoon Network AS | Other/Intl |
| 14 | forecast_category | = | Cartoon Network AU | Other/Intl |
| 15 | forecast_category | = | Cartoon Network BR | Other/Intl |
| 16 | forecast_category | = | Cartoon Network CO | Other/Intl |
| 17 | forecast_category | = | Cartoon Network HQ | Other/Intl |
| 18 | forecast_category | = | Cartoon Network IN | Other/Intl |
| 19 | forecast_category | = | Cartoon Network LA | Other/Intl |
| 20 | forecast_category | = | Cartoon Network MX | Other/Intl |
| 21 | forecast_category | = | Cartoon Network UK | Other/Intl |
| 22 | forecast_category | = | CNN TAP | Other/Intl |
| 23 | forecast_category | = | Cartoon Network CZ | Other/Intl |
| 24 | forecast_category | = | Turner MLB | Sports |
| 25 | forecast_category | = | Boomerang TV AU | Other/Intl |
| 26 | forecast_category | = | Esporte Interativo | Other/Intl |
| 27 | forecast_category | = | TNT Sports AR | Other/Intl |
| 28 | forecast_category | = | Cartoonito UK | Other/Intl |
| 29 | forecast_category | = | Cartoon Network VE | Other/Intl |
| 30 | forecast_category | = | Boomerang UK | Other/Intl |
| 31 | forecast_category | = | Turner UEFA | Sports |
| 32 | forecast_category | = | OHK TV | Other/Intl |
| 33 | forecast_category | = | TCM.com | TCM |
| 34 | forecast_category | = | CBSSports.com | Sports |
| 35 | forecast_category | = | CNN Arabic | Other/Intl |
| 36 | forecast_category | = | CNN.com | News |
| 37 | forecast_category | = | CNN Business | News |
| 38 | forecast_category | = | CNN.com Espanol | Other/Intl |
| 39 | forecast_category | = | CNN.com Espanol US | Other/Intl |
| 40 | forecast_category | = | CNN.com Intl | Other/Intl |
| 41 | forecast_category | = | CNN.com Intl Edition | Other/Intl |
| 42 | forecast_category | = | CNNMoney.com | News |
| 43 | forecast_category | = | CNNMoney.com Intl | Other/Intl |
| 44 | forecast_category | = | ELEAGUE | Sports |
| 45 | forecast_category | = | Great Big Story | GBS |
| 46 | forecast_category | = | Great Big Story Intl | GBS |
| 47 | forecast_category | = | HLN.tv | News |
| 48 | forecast_category | = | HTV.com | Other/Intl |
| 49 | forecast_category | = | NASCAR.com | Sports |
| 50 | forecast_category | = | NBA.com | Sports |
| 51 | forecast_category | = | NCAA.com | Sports |
| 52 | forecast_category | = | PGA.com | Sports |
| 53 | forecast_category | = | POGO.tv | Other/Intl |
| 54 | forecast_category | = | Super Deluxe | Entertainment |
| 55 | forecast_category | = | TBS.com | Entertainment |
| 56 | forecast_category | = | TCMLA.com | Other/Intl |
| 57 | forecast_category | = | The Turner Network | Turner Network |
| 58 | forecast_category | = | TNTDrama.com | Entertainment |
| 59 | forecast_category | = | TNTLA.com | Other/Intl |
| 60 | forecast_category | = | truTV.com | Entertainment |
| 61 | forecast_category | = | Turner Entertainment | Entertainment |
| 62 | forecast_category | = | Turner NBA | Sports |
| 63 | forecast_category | = | Turner News | News |
| 64 | forecast_category | = | Turner Schedule Bill | Other/Intl |
| 65 | forecast_category | = | Turner Sports | Sports |
| 66 | forecast_category | = | WarnerLA.com | Other/Intl |
| 67 | forecast_category | = | Bleacher Report Intl | Other/Intl |
| 68 | forecast_category | = | ISAT.TV | Other/Intl |
| 69 | forecast_category | = | SpaceAmo.com | Other/Intl |
| 70 | forecast_category | = | MuchLA.com | Other/Intl |
| 71 | forecast_category | = | CNN Business Intl Ed | Other/Intl |
| 72 | forecast_category | = | CNN Business Intl | Other/Intl |
| 73 | forecast_category | = | Uncategorized Revenue | Other/Intl |
| 74 | forecast_category | = | GlitzTVLA.com | Other/Intl |
| 75 | forecast_category | = | Cartoon Network CL | Other/Intl |
| 76 | forecast_category | = | Cartoon Network FR | Other/Intl |
| 77 | forecast_category | = | Cartoon Network RU | Other/Intl |
| 78 | forecast_category | = | Cartoon Network IT | Other/Intl |
| 79 | forecast_category | = | Cartoon Network DE | Other/Intl |
| 80 | forecast_category | = | ELEAGUE Intl | Other/Intl |
| 81 | forecast_category | = | Canal De Futbol | Other/Intl |
| 82 | forecast_category | = | Chilevision | Other/Intl |
| 83 | forecast_category | = | FunnyOrDie.com | Entertainment |
| 84 | forecast_category | = | Team Coco | Entertainment |
| 85 | forecast_category | = | Crunchyroll | Entertainment |
| 86 | forecast_category | = | Rooster Teeth | Entertainment |
| 87 | forecast_category | = | VRV | Entertainment |
| 88 | forecast_category | = | Yahoo Sports NBA | Sports |
| 89 | forecast_category | = | Yahoo Sports Golf | Sports |
| 90 | forecast_category | = | CNN Partners | News |
| 91 | forecast_category | = | FullScreen | Entertainment |
| 92 | forecast_category | = | Turner PGA | Sports |
| 93 | forecast_category | = | Turner NHL | Sports |
| 94 | forecast_category | = | Turner US Soccer | Sports |
| 95 | forecast_category | = | Sports Digital | Sports |
| 96 | forecast_category | = | DC Kids | Entertainment |
| 97 | forecast_category | = | WB Kids | Entertainment |
| 98 | forecast_category | = | WarnerMedia Family | Entertainment |
| 99 | LOWER(forecast_category) | = | tmz | WB |
| 100 | LOWER(forecast_category) | = | toofab | WB |
| 101 | LOWER(forecast_category) | = | the real | WB |
| 102 | LOWER(forecast_category) | = | true crime daily | WB |
| 103 | LOWER(forecast_category) | = | extratv | WB |
| 104 | LOWER(forecast_category) | = | bachelornation | WB |
| 105 | LOWER(forecast_category) | = | the wb network | WB |
| 106 | LOWER(forecast_category) | = | hbo max | Streaming |
| 107 | LOWER(forecast_category) | = | run of wb kids | Entertainment |
| 108 | LOWER(forecast_category) | = | max | Streaming |
| 109 | LOWER(forecast_category) | = | discovery+ | Streaming |
| 110 | LOWER(forecast_category) | = | dci ent | Entertainment |
| 111 | LOWER(forecast_category) | LIKE | %dci% | <returns forecast_category itself> |
| 112 | LOWER(forecast_category) | LIKE | %nba% | Sports |
| 113 | LOWER(forecast_category) | LIKE | %nhl% | Sports |
| 114 | LOWER(forecast_category) | LIKE | %mlb% | Sports |
| 115 | LOWER(forecast_category) | LIKE | %ncaa% | Sports |
| 116 | LOWER(forecast_category) | LIKE | %pga% | Sports |
| 117 | LOWER(forecast_category) | LIKE | %soccer% | Sports |
| 118 | LOWER(forecast_category) | LIKE | %futbol% | Sports |
| 119 | LOWER(forecast_category) | LIKE | %nascar% | Sports |
| 120 | LOWER(forecast_category) | LIKE | %sports% | Sports |
| 121 | LOWER(forecast_category) | LIKE | %kids% | Entertainment |
| 122 | LOWER(forecast_category) | LIKE | %family% | Entertainment |
| 123 | LOWER(forecast_category) | LIKE | %gaming% | Entertainment |
| 124 | LOWER(forecast_category) | LIKE | %true crime% | Entertainment |
| 125 | LOWER(forecast_category) | LIKE | %tnt% | Entertainment |
| 126 | LOWER(forecast_category) | LIKE | %trutv% | Entertainment |
| 127 | LOWER(forecast_category) | LIKE | %tbs% | Entertainment |
| 128 | LOWER(forecast_category) | LIKE | %wb network% | Entertainment |
| 129 | LOWER(forecast_category) | LIKE | %true crime% | Entertainment |
| 130 | LOWER(forecast_category) | LIKE | %adult swim% | Entertainment |
| 131 | LOWER(forecast_category) | LIKE | %turner nba% | Sports |
| 132 | LOWER(forecast_category) | LIKE | %turner sports% | Sports |
| 133 | LOWER(forecast_category) | LIKE | %turner wbb% | Sports |
| 134 | LOWER(forecast_category) | LIKE | %turner roland garros% | Sports |
| 135 | LOWER(forecast_category) | LIKE | %turner march madness% | Sports |
| 136 | LOWER(forecast_category) | LIKE | %turner big 12 football% | Sports |
| 137 | LOWER(forecast_category) | LIKE | %turner% | Other/Intl |

## Observed value maps in the Looker SF export (computed)



| Map | from | to | rows |
|---|---|---|---|
| Projection Rank (live export, all stage->rank pairs) | Closed Won | A | 13336 |
| Projection Rank (live export, all stage->rank pairs) | Prospecting/Planning Costs |  | 2974 |
| Projection Rank (live export, all stage->rank pairs) | Verbal Commitment/HOLD | B | 2943 |
| Projection Rank (live export, all stage->rank pairs) | Proposal/Working | C | 2045 |
| Projection Rank (live export, all stage->rank pairs) | Proposal Low/Projection | D | 1219 |
| Projection Rank (live export, all stage->rank pairs) | Closed Lost | F | 1209 |
| Projection Rank (live export, all stage->rank pairs) | Cancelled |  | 30 |
| Status Group (live export) | Closed Won | Order | 13284 |
| Status Group (live export) | Prospecting/Planning Costs | Prospecting | 2606 |
| Status Group (live export) | Verbal Commitment/HOLD | Pipeline | 2184 |
| Status Group (live export) | Proposal/Working | Pipeline | 2045 |
| Status Group (live export) | Proposal Low/Projection | Pipeline | 1217 |
| Status Group (live export) | Closed Lost | closed_lost | 1209 |
| Status Group (live export) | Verbal Commitment/HOLD | Order | 753 |
| Status Group (live export) | Prospecting/Planning Costs | Pipeline | 367 |
| Status Group (live export) | Closed Won | closed_lost | 52 |
| Status Group (live export) | Cancelled | closed_lost | 30 |
| Status Group (live export) | Verbal Commitment/HOLD | closed_lost | 6 |
| Status Group (live export) | Proposal Low/Projection | closed_lost | 2 |
| Status Group (live export) | Prospecting/Planning Costs | closed_lost | 1 |
| Salesforce Classification -> Market Type | Upfront 26/27 | Upfront | 11517 |
| Salesforce Classification -> Market Type | Scatter | Scatter | 6098 |
| Salesforce Classification -> Market Type | DDL | Scatter | 1963 |
| Salesforce Classification -> Market Type |  | Unmapped | 1574 |
| Salesforce Classification -> Market Type | Programmatic National Upfront 26/27 | Upfront | 689 |
| Salesforce Classification -> Market Type | Demo Direct | Scatter | 398 |
| Salesforce Classification -> Market Type | Premiere | Scatter | 371 |
| Salesforce Classification -> Market Type | Upfront 25/26 | Upfront | 321 |
| Salesforce Classification -> Market Type | Direct Response | Scatter | 305 |
| Salesforce Classification -> Market Type | Upfront PMP 26/27 | Upfront | 171 |
| Salesforce Classification -> Market Type | Programmatic National Scatter | Scatter | 137 |
| Salesforce Classification -> Market Type | International Sold | International | 73 |
| Salesforce Classification -> Market Type | Programmatic National Upfront 25/26 | Upfront | 60 |
| Salesforce Classification -> Market Type | Audience Deficiency Unit | ADU / Makegood | 29 |
| Salesforce Classification -> Market Type | Programmatic Umbrella Order | Unmapped | 17 |
| Salesforce Classification -> Market Type | PSA | PSA | 15 |
| Salesforce Classification -> Market Type | Upfront PMP 25/26 | Upfront | 11 |
| Salesforce Classification -> Market Type | Sports Fees | Unmapped | 3 |
| Salesforce Classification -> Market Type | Linear Addressable | Unmapped | 2 |
| Salesforce Classification -> Market Type | Programmatic PPM | Programmatic - Unclassified | 2 |
| Salesforce Classification -> UF Year | Upfront 26/27 | 26/27 | 11517 |
| Salesforce Classification -> UF Year | Scatter | N/A | 6098 |
| Salesforce Classification -> UF Year | DDL | N/A | 1963 |
| Salesforce Classification -> UF Year |  | N/A | 1574 |
| Salesforce Classification -> UF Year | Programmatic National Upfront 26/27 | 26/27 | 689 |
| Salesforce Classification -> UF Year | Demo Direct | N/A | 398 |
| Salesforce Classification -> UF Year | Premiere | N/A | 371 |
| Salesforce Classification -> UF Year | Upfront 25/26 | 25/26 | 321 |
| Salesforce Classification -> UF Year | Direct Response | N/A | 305 |
| Salesforce Classification -> UF Year | Upfront PMP 26/27 | 26/27 | 171 |
| Salesforce Classification -> UF Year | Programmatic National Scatter | N/A | 137 |
| Salesforce Classification -> UF Year | International Sold | N/A | 73 |
| Salesforce Classification -> UF Year | Programmatic National Upfront 25/26 | 25/26 | 60 |
| Salesforce Classification -> UF Year | Audience Deficiency Unit | N/A | 29 |
| Salesforce Classification -> UF Year | Programmatic Umbrella Order | N/A | 17 |
| Salesforce Classification -> UF Year | PSA | N/A | 15 |
| Salesforce Classification -> UF Year | Upfront PMP 25/26 | 25/26 | 11 |
| Salesforce Classification -> UF Year | Sports Fees | N/A | 3 |
| Salesforce Classification -> UF Year | Linear Addressable | N/A | 2 |
| Salesforce Classification -> UF Year | Programmatic PPM | N/A | 2 |
| Platform vs Record Type | Linear | Linear | 16208 |
| Platform vs Record Type | Digital | Digital | 7525 |
| Platform vs Record Type | Digital | Linear | 23 |

## Unique custom-field ids/names referenced (83)



| Key (ID or NAME) | hits | distinct files | first location | files |
|---|---|---|---|---|
| ID 93 | 8 | 4 | looker-inventory-analytics/models/eg_order_management.model.lkml:L343 | looker-etl-carl/airflow/dags/revops_etl/nielsen/vod_op1/dml/02_insert_overwrite_nielsenvod_op1_wk.sql; looker-inventory-analytics/models/eg_ad_server.model.lkml; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 125 | 8 | 4 | looker-inventory-analytics/models/eg_order_management.model.lkml:L343 | looker-etl-carl/airflow/dags/revops_etl/nielsen/vod_op1/dml/02_insert_overwrite_nielsenvod_op1_wk.sql; looker-inventory-analytics/models/eg_ad_server.model.lkml; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 220 | 7 | 2 | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L79 | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml; looker-inventory-analytics/views/base.site_zero.view.lkml |
| ID 208 | 6 | 3 | looker-inventory-analytics/models/eg_order_management.model.lkml:L4024 | looker-etl-carl/airflow/dags/revops_etl/nielsen/vod_op1/dml/02_insert_overwrite_nielsenvod_op1_wk.sql; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 38 | 6 | 3 | looker-inventory-analytics/models/eg_order_management.model.lkml:L4024 | looker-etl-carl/airflow/dags/revops_etl/nielsen/vod_op1/dml/02_insert_overwrite_nielsenvod_op1_wk.sql; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 41 | 5 | 3 | looker-inventory-analytics/models/eg_audience.model.lkml:L100 | looker-inventory-analytics/models/eg_audience.model.lkml; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 214 | 5 | 3 | looker-inventory-analytics/models/eg_audience.model.lkml:L100 | looker-inventory-analytics/models/eg_audience.model.lkml; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 230 | 5 | 4 | looker-inventory-analytics/models/eg_order_management.model.lkml:L359 | looker-inventory-analytics/explores/cnn_adobe.explore.lkml; looker-inventory-analytics/models/eg_ad_server.model.lkml; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 132 | 4 | 3 | looker-inventory-analytics/models/eg_order_management.model.lkml:L1695 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 36 | 4 | 2 | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L73 | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml; looker-inventory-analytics/views/base.site_zero.view.lkml |
| ID 16 | 4 | 3 | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L85 | dai-digital-ads/airflow/resources/sql/operative/project_neo_source.sql; looker-etl-carl/snowflake/snowflake_views/bolt_views/bolt_views.sql; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 122 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L410 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 228 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L410 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 253 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L546 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 33 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L546 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 84 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L847 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 184 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L847 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 133 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L847 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 85 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L861 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 258 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L861 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 115 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L1680 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 267 | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L1680 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 141 | 3 | 2 | looker-etl-carl/snowflake/snowflake_views/bolt_views/bolt_views.sql:L1819 | dai-digital-ads/airflow/resources/sql/operative/project_neo_source.sql; looker-etl-carl/snowflake/snowflake_views/bolt_views/bolt_views.sql |
| ID 295 | 2 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L560 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 147 | 2 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L574 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 46 | 2 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L3410 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 25 | 2 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L3410 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 282 | 2 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L3914 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 27 | 2 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L3942 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 255 | 2 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L4050 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 47 | 2 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L4050 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 113 | 2 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L4064 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 212 | 2 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L4064 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 298 | 1 | 1 | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L191 | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 204 | 1 | 1 | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L253 | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| ID 290 | 1 | 1 | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L127 | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 233 | 1 | 1 | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L172 | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| ID 288 | 1 | 1 | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L178 | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| NAME Ad Type | 38 | 12 | looker-etl-carl/archive/Op1_JOTF_Archive/01_jotf_day_new_snapshot.sql:L361 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_line_items_staging.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_sb_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_05_jotf_day_adserver_insert.sql; looker-etl-carl/ |
| NAME Buy Type | 19 | 6 | looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/02_op1_contracted_w_rate.sql:L99 | looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_sb_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/02_op1_contracted_w_rate.sql |
| NAME Payment Type | 14 | 14 | looker-inventory-analytics/models/eg_sales.model.lkml:L75 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_sb_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dag |
| NAME Deal Type | 9 | 9 | looker-etl-carl/archive/Op1_JOTF_Archive/01_jotf_day_new_snapshot.sql:L450 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_sb_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dag |
| NAME Warner Payment Type | 9 | 9 | looker-etl-carl/airflow/dags/revops_etl/fw_etl_workflow_intraday/dml/fw_04_05_op_map_insert.sql:L30 | looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_sb_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/fw_etl_workflow_intraday/dml/fw_04_05_op_map_insert.sql; looker-etl-carl/airflow |
| NAME Line Internal Notes | 8 | 8 | looker-etl-carl/archive/Op1_JOTF_Archive/01_jotf_day_new_snapshot.sql:L536 | looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_sb_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql; looker-etl-carl/archive/O |
| NAME Warner Deal Type | 7 | 7 | looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql:L263 | looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Intraday/dml/03_05_jotf_day_sb_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_02_jotf_day_insert.sql; looker-etl-carl/airflow/dags/revops_etl/Op1_JOTF_Sports_Intraday/dml/01_05_jotf_day_adserver_insert.sql; looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql; looker-etl-carl/airflow/d |
| NAME Order Level Target | 5 | 3 | looker-inventory-analytics/models/eg_order_management.model.lkml:L520 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| NAME Invoice/Affidavit | 5 | 4 | looker-inventory-analytics/models/eg_order_management.model.lkml:L2147 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql; looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| NAME Opportunity ID | 4 | 3 | looker-inventory-analytics/models/eg_order_management.model.lkml:L533 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| NAME Warner SF Deal ID | 4 | 3 | looker-inventory-analytics/models/eg_order_management.model.lkml:L533 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| NAME Upfront | 4 | 3 | looker-inventory-analytics/explores/cnn_adobe.explore.lkml:L313 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql; looker-inventory-analytics/explores/cnn_adobe.explore.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| NAME Warner Line Item ID | 4 | 4 | looker-inventory-analytics/views/base.dt_adjuster_booked_delivered.view.lkml:L21 | looker-etl-carl/airflow/dags/revops_etl/op1_booked_delivered/01_deli_w_line_stg.sql; looker-etl-carl/airflow/dags/revops_etl/op1_booked_delivered/08_deli_insert_stg.sql; looker-inventory-analytics/views/base.dt_adjuster_booked_delivered.view.lkml; looker-inventory-analytics/views/base.dt_adjuster_booked_delivered_non_billable.view.lkml |
| NAME SSP | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L474 | looker-inventory-analytics/models/eg_ad_server.model.lkml; looker-inventory-analytics/models/eg_order_management.model.lkml |
| NAME Warner Order Level Target | 3 | 3 | looker-inventory-analytics/models/eg_order_management.model.lkml:L520 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql; looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| NAME Show Exclusions | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L820 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| NAME Warner Show Exclusions | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L820 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| NAME Site Exclusions | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L833 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| NAME Warner Site Exclusions | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L833 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| NAME VOD/OLV Fluidity | 3 | 2 | looker-inventory-analytics/models/eg_order_management.model.lkml:L886 | looker-inventory-analytics/models/eg_order_management.model.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| NAME Upfront Type | 3 | 3 | looker-inventory-analytics/explores/cnn_adobe.explore.lkml:L1143 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql; looker-inventory-analytics/explores/cnn_adobe.explore.lkml; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| NAME Line Level Intent | 3 | 3 | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L65 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_line_items_staging.sql; looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01a_insert_oper_etl_sales_order_line_items_staging.sql; looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| NAME Sales Split | 2 | 2 | looker-inventory-analytics/models/eg_sales.model.lkml:L88 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql; looker-inventory-analytics/models/eg_sales.model.lkml |
| NAME Converged Sponsorship | 2 | 1 | looker-inventory-analytics/models/eg_order_management.model.lkml:L447 | looker-inventory-analytics/models/eg_order_management.model.lkml |
| NAME Upfront Type_Old | 2 | 2 | looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml:L226 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql; looker-inventory-analytics/views/base.oper_sales_order_custom_field_t.view.lkml |
| NAME Ad Type International | 2 | 2 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01a_insert_oper_etl_sales_order_line_items_staging.sql:L71 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_line_items_staging.sql; looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01a_insert_oper_etl_sales_order_line_items_staging.sql |
| NAME Third Party Rep Name | 2 | 2 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql:L60 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql; looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql |
| NAME Order Internal Notes | 2 | 2 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql:L65 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql; looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql |
| NAME Sponsorship Event | 1 | 1 | looker-inventory-analytics/models/eg_sales.model.lkml:L101 | looker-inventory-analytics/models/eg_sales.model.lkml |
| NAME various_flag | 1 | 1 | looker-inventory-analytics/models/eg_order_management.model.lkml:L434 | looker-inventory-analytics/models/eg_order_management.model.lkml |
| NAME DSP__c | 1 | 1 | looker-inventory-analytics/models/eg_order_management.model.lkml:L4206 | looker-inventory-analytics/models/eg_order_management.model.lkml |
| NAME Demo Guaranteed | 1 | 1 | looker-inventory-analytics/explores/cnn_adobe.explore.lkml:L491 | looker-inventory-analytics/explores/cnn_adobe.explore.lkml |
| NAME LIKE 'Billable Third-Party Server' | 1 | 1 | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml:L104 | looker-inventory-analytics/views/base.oper_sales_order_line_item_custom_field_t.view.lkml |
| NAME Notes | 1 | 1 | looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql:L268 | looker-etl-carl/airflow/dags/revops_etl/op1_contracted_wbd/01_op1_contracted_new_snapshot.sql |
| NAME Warner SF Sales Split ID | 1 | 1 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql:L58 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql |
| NAME Warner TV Integration | 1 | 1 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql:L62 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql |
| NAME Warner Viewability | 1 | 1 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql:L64 | looker-etl-carl/airflow/dags/revops_etl/op1_ra_snapshot_etl/01b_insert_oper_etl_sales_order_staging.sql |
| NAME Nielsen DAR ID | 1 | 1 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql:L30 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql |
| NAME Warner Nielsen DAR ID | 1 | 1 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql:L30 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql |
| NAME Guaranteed Demo | 1 | 1 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql:L65 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql |
| NAME Target Demo | 1 | 1 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql:L65 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql |
| NAME Nielsen Guaranteed Platform | 1 | 1 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql:L70 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql |
| NAME Warner Nielsen Guaranteed Platform | 1 | 1 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql:L70 | looker-etl-carl/airflow/dags/revops_etl/nielsen/dar_op1/dml/03_Insert_overwrite_op_join_nielsen_base.sql |
| NAME TV Integration | 1 | 1 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql:L31 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql |
| NAME Viewability | 1 | 1 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql:L33 | airflow_prod_eds/dags/eds/edslib/data/sql/operative/insert_oper_etl_sales_order_staging.sql |
