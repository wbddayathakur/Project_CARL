-- Shared CTEs for the validation queries (Athena / Trino, CARL Dev Glue catalog).
-- Every raw column name lives here; queries 01-09 only use the normalized names.
-- Column names verified against Dev Glue on 2026-11-02 (evidence/glue_columns_2026-11-02.json).
-- impact_bronze exists in Dev only.
WITH
campaign AS (
    SELECT
        CAST(campaign_id AS varchar)                                           AS campaign_id,
        campaign_name,
        campaign_type,
        media_type,
        lower(concat(coalesce(campaign_type, ''), ' ', coalesce(media_type, ''))) LIKE '%linear%' AS is_linear,
        flight_start_date                                                      AS flight_start,
        flight_end_date                                                        AS flight_end,
        quarter,
        coalesce(has_videoamp_measurement, false)                              AS has_videoamp,
        ideal_ids                                                              AS ideal_deal_ids_raw,
        freewheel_digital_campaign_ids                                         AS fw_campaign_ids_raw,
        array_join(array_sort(filter(transform(split(coalesce(freewheel_digital_campaign_ids, ''), ','), s -> trim(s)), s -> s <> '')), ',') AS fw_key,
        videoamp_audience_ids,
        videoamp_campaign_id,
        videoamp_planning_id,
        advertiser_id,
        advertiser
    FROM impact_bronze.campaign
),
-- Impact ideal_ids and request ideal_ids hold the iDeal GAB deal number (deal_header.gab_deal_id),
-- not the internal deal_id that the plan tables key on.
campaign_deal AS (
    SELECT DISTINCT c.campaign_id, try(CAST(trim(d) AS bigint)) AS gab_deal_id
    FROM campaign c
    CROSS JOIN UNNEST(split(coalesce(c.ideal_deal_ids_raw, ''), ',')) AS t(d)
    WHERE try(CAST(trim(d) AS bigint)) IS NOT NULL
),
va_request AS (
    SELECT
        request_id,
        report_id,
        campaignids                                                            AS fw_campaign_ids_raw,
        array_join(array_sort(filter(transform(split(coalesce(campaignids, ''), ','), s -> trim(s)), s -> s <> '')), ',') AS fw_key,
        ideal_ids                                                              AS ideal_deal_ids_raw,
        try(CAST(regexp_extract(postlog, '^\s*(\d+)', 1) AS bigint))           AS postlog_deal_id,
        postlog,
        report_name,
        CAST(advertiserid AS varchar)                                          AS advertiser_id,
        start_date                                                             AS req_start,
        end_date                                                               AS req_end,
        createdat                                                              AS created_at
    FROM impact_bronze.videoamp_request
),
va_request_deal AS (
    SELECT DISTINCT r.request_id, try(CAST(trim(d) AS bigint)) AS gab_deal_id
    FROM va_request r
    CROSS JOIN UNNEST(split(coalesce(r.ideal_deal_ids_raw, ''), ',')) AS t(d)
    WHERE try(CAST(trim(d) AS bigint)) IS NOT NULL
),
va_report AS (
    SELECT
        _request_uuid                                                          AS request_id,
        dimension_set_name,
        dimension,
        time_slice,
        try(CAST(date_parse(CAST(CAST(time_slice_start_date AS bigint) AS varchar), '%Y%m%d') AS date)) AS slice_start,
        try(CAST(date_parse(CAST(CAST(time_slice_end_date AS bigint) AS varchar), '%Y%m%d') AS date))   AS slice_end,
        time_slice_start_date                                                  AS slice_start_raw,
        time_slice_end_date                                                    AS slice_end_raw,
        medium,
        stream,
        audience_id,
        audience_level,
        trim(audience_id) = '-1' OR audience_id LIKE '%(-1)'                   AS is_household,
        CAST(impressions AS double)                                            AS impressions,
        CAST(reach AS double)                                                  AS reach,
        average_frequency                                                      AS frequency,
        cumulative_reach,
        _created_at                                                            AS report_created_at
    FROM impact_bronze.videoamp_measurement_report
),
va_linear_hh AS (
    SELECT *
    FROM va_report
    WHERE dimension_set_name = 'medium'
      AND time_slice = 'Report To Date'
      AND medium = 'Linear Total'
      AND stream = 'plus3'
      AND is_household
      AND reach >= 0
),
campaign_request_all AS (
    SELECT c.campaign_id, r.request_id, r.created_at, r.req_start, r.req_end, 'FW_IDS' AS mapping_path
    FROM campaign c
    JOIN va_request r ON c.fw_key <> '' AND r.fw_key = c.fw_key
    UNION ALL
    SELECT cd.campaign_id, r.request_id, r.created_at, r.req_start, r.req_end, 'REQUEST_IDEAL_IDS' AS mapping_path
    FROM campaign_deal cd
    JOIN va_request_deal rd ON rd.gab_deal_id = cd.gab_deal_id
    JOIN va_request r ON r.request_id = rd.request_id
    UNION ALL
    SELECT cd.campaign_id, r.request_id, r.created_at, r.req_start, r.req_end, 'POSTLOG_DEAL' AS mapping_path
    FROM campaign_deal cd
    JOIN va_request r ON r.postlog_deal_id = cd.gab_deal_id
),
campaign_request AS (
    SELECT campaign_id, request_id, created_at, req_start, req_end, mapping_path, mapping_paths
    FROM (
        SELECT a.*,
               array_join(array_sort(array_distinct(array_agg(mapping_path) OVER (PARTITION BY campaign_id, request_id))), '+') AS mapping_paths,
               row_number() OVER (PARTITION BY campaign_id, request_id
                                  ORDER BY CASE mapping_path WHEN 'FW_IDS' THEN 1 WHEN 'REQUEST_IDEAL_IDS' THEN 2 ELSE 3 END) AS rn
        FROM campaign_request_all a
    )
    WHERE rn = 1
),
-- Shared FreeWheel IDs / deals can attach one request to several campaigns, so a request only counts
-- for a campaign when its measured window overlaps the flight, and exact window matches win.
final_report AS (
    SELECT
        cr.campaign_id, cr.request_id, cr.created_at, cr.req_start, cr.req_end, cr.mapping_path, cr.mapping_paths,
        cr.req_start = c.flight_start AND cr.req_end = c.flight_end              AS window_exact_match,
        h.audience_id, h.impressions, h.reach, h.frequency, h.slice_start, h.slice_end,
        count(*) OVER (PARTITION BY cr.request_id)                                AS campaigns_sharing_request,
        row_number() OVER (PARTITION BY cr.campaign_id
                           ORDER BY CASE WHEN cr.req_start = c.flight_start AND cr.req_end = c.flight_end THEN 0 ELSE 1 END,
                                    cr.created_at DESC)                           AS recency
    FROM campaign_request cr
    JOIN campaign c ON c.campaign_id = cr.campaign_id
    JOIN va_linear_hh h ON h.request_id = cr.request_id
    WHERE cr.req_start <= c.flight_end AND cr.req_end >= c.flight_start
),
deal_history AS (
    SELECT
        CAST(deal_id AS bigint)                                                AS deal_id,
        CAST(gab_deal_id AS bigint)                                            AS gab_deal_id,
        CAST(audit_no AS integer)                                              AS audit_no,
        CAST(deal_revision_no AS integer)                                      AS deal_revision_no,
        CAST(create_dt AS date)                                                AS deal_created,
        CAST(plan_chg_dt AS date)                                              AS plan_changed,
        CAST(chg_dt AS date)                                                   AS last_changed,
        CAST(adver_id AS varchar)                                              AS ideal_advertiser_id,
        CAST(broadcast_year AS varchar)                                        AS broadcast_year,
        upfront_scatter_code                                                   AS upfront_scatter,
        guaranteed_ind,
        deal_status,
        deal_description,
        coalesce(row_deleted_ind, 'N')                                         AS row_deleted_ind
    FROM linear_digital_revenue_bronze.ideal_dealbldr_dci_deal_header
),
deal AS (
    SELECT * FROM (
        SELECT h.*, count(*) OVER (PARTITION BY deal_id) AS header_versions,
               row_number() OVER (PARTITION BY deal_id ORDER BY audit_no DESC) AS rn
        FROM deal_history h
    ) WHERE rn = 1
),
campaign_plan_deal AS (
    SELECT DISTINCT cd.campaign_id, cd.gab_deal_id, d.deal_id
    FROM campaign_deal cd
    JOIN deal d ON d.gab_deal_id = cd.gab_deal_id
),
deal_revision AS (
    SELECT
        CAST(deal_id AS bigint)                                                AS deal_id,
        audit_no,
        reason,
        start_dt                                                               AS revision_started_at,
        confirm_dt                                                             AS revision_confirmed_at,
        chg_dt
    FROM linear_digital_revenue_bronze.ideal_dealbldr_dci_deal_revision
),
-- Deal-level as-sold impressions by demo, stored in thousands. Household demos per currency
-- (ideal_dealbldr_idl_hh_demo_map): 1 = Nielsen HH, 1401 = VideoAmp HH, 100001 = Big Data HH.
deal_demo_plan AS (
    SELECT
        CAST(deal_id AS bigint)                                                AS deal_id,
        CAST(demo_id AS bigint)                                                AS demo_id,
        CAST(audit_no AS integer)                                              AS audit_no,
        CAST(current_as_sold_imps AS double) * 1000                            AS current_as_sold_imps,
        CAST(original_as_sold_imps AS double) * 1000                           AS original_as_sold_imps,
        CAST(tracking_imps AS double) * 1000                                   AS tracking_imps,
        chg_dt
    FROM linear_digital_revenue_bronze.ideal_dealbldr_dci_deal_demo_target
    WHERE coalesce(row_deleted_ind, 'N') <> 'Y'
),
-- Spots per selling line per broadcast week, latest audit_no per (line, week).
plan_spots AS (
    SELECT
        w.deal_id, w.line_sell_id, ls.selling_title_id, w.week_of, w.spots, w.audit_no
    FROM (
        SELECT CAST(deal_id AS bigint) AS deal_id, CAST(line_sell_id AS bigint) AS line_sell_id,
               CAST(week_of_dt AS date) AS week_of, CAST(num_spots AS integer) AS spots, CAST(audit_no AS integer) AS audit_no,
               row_number() OVER (PARTITION BY line_sell_id, week_of_dt ORDER BY audit_no DESC) AS rn
        FROM linear_digital_revenue_bronze.ideal_dealbldr_dci_order_line_sell_weeks
        WHERE coalesce(row_deleted_ind, 'N') <> 'Y'
    ) w
    LEFT JOIN (
        SELECT CAST(line_sell_id AS bigint) AS line_sell_id, max(CAST(sell_id AS bigint)) AS selling_title_id
        FROM linear_digital_revenue_bronze.ideal_dealbldr_dci_order_line_sell
        GROUP BY 1
    ) ls ON ls.line_sell_id = w.line_sell_id
    WHERE w.rn = 1
),
-- Selling title -> network. The silver selling_title_network_map does not share keys with iDeal sell_id.
selling_title_network AS (
    SELECT CAST(sell_id AS bigint) AS selling_title_id,
           min(CAST(net_id AS bigint)) AS net_id,
           count(DISTINCT net_id)      AS networks_mapped
    FROM linear_digital_revenue_bronze.ideal_dealbldr_dci_pricing_rating
    GROUP BY 1
),
-- ue_nat / ue_cov are in thousands. Weekly and season-long periods overlap; season rows are the
-- published UE, so callers pick the longest period containing the date.
universe AS (
    SELECT
        CAST(nielsennetworkid AS varchar)                                      AS nielsen_network_id,
        CAST(date_parse(CAST(CAST(_start_datesk AS bigint) AS varchar), '%Y%m%d') AS date) AS ue_start,
        CAST(date_parse(CAST(CAST(_end_datesk AS bigint) AS varchar), '%Y%m%d') AS date)   AS ue_end,
        CAST(ue_nat AS double) * 1000                                          AS ue_nat_hh,
        CAST(ue_nat AS double)                                                 AS ue_nat,
        CAST(ue_cov AS double)                                                 AS ue_cov
    FROM big_mit_bronze.universe_estimate
)
-- Campaign-to-VideoAmp mapping coverage for measured Linear campaigns, by path:
-- FW_IDS (FreeWheel IDs), REQUEST_IDEAL_IDS (request.ideal_ids overlaps campaign deals),
-- POSTLOG_DEAL (As-Run filename deal prefix).
, per_campaign AS (
    SELECT
        c.campaign_id,
        c.campaign_name,
        c.campaign_type,
        c.flight_start,
        c.flight_end,
        count(DISTINCT CASE WHEN a.mapping_path = 'FW_IDS' THEN a.request_id END)            AS requests_by_fw_ids,
        count(DISTINCT CASE WHEN a.mapping_path = 'REQUEST_IDEAL_IDS' THEN a.request_id END) AS requests_by_ideal_ids,
        count(DISTINCT CASE WHEN a.mapping_path = 'POSTLOG_DEAL' THEN a.request_id END)      AS requests_by_postlog_deal,
        count(DISTINCT a.request_id)                                                         AS requests_total,
        max(a.created_at)                                                                    AS latest_request_at,
        count_if(a.req_start <> c.flight_start OR a.req_end <> c.flight_end)                 AS request_rows_window_differs
    FROM campaign c
    LEFT JOIN campaign_request_all a ON a.campaign_id = c.campaign_id
    WHERE c.has_videoamp AND c.is_linear
    GROUP BY 1, 2, 3, 4, 5
)
SELECT
    p.*,
    CASE
        WHEN requests_total = 0 THEN 'UNMAPPED'
        WHEN requests_by_fw_ids > 0 AND requests_by_ideal_ids > 0 THEN 'FW_AND_IDEAL'
        WHEN requests_by_fw_ids > 0 THEN 'FW_ONLY'
        WHEN requests_by_ideal_ids > 0 THEN 'IDEAL_ONLY'
        ELSE 'POSTLOG_ONLY'
    END AS mapping_status,
    f.request_id IS NOT NULL AS has_linear_hh_report
FROM per_campaign p
LEFT JOIN final_report f ON f.campaign_id = p.campaign_id AND f.recency = 1
ORDER BY mapping_status, flight_end DESC
