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
final_report AS (
    SELECT
        cr.campaign_id, cr.request_id, cr.created_at, cr.req_start, cr.req_end, cr.mapping_path, cr.mapping_paths,
        h.audience_id, h.impressions, h.reach, h.frequency, h.slice_start, h.slice_end,
        count(*) OVER (PARTITION BY cr.request_id)                                AS campaigns_sharing_request,
        row_number() OVER (PARTITION BY cr.campaign_id ORDER BY cr.created_at DESC) AS recency
    FROM campaign_request cr
    JOIN va_linear_hh h ON h.request_id = cr.request_id
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
-- Planned Linear impressions for measured campaigns, by network x selling title (selling titles
-- carry the daypart in their name, e.g. 'CNN LATENIGHT M-F 12A-4A').
-- Household plan totals come from deal_demo_target (latest revision and the last revision confirmed
-- before flight start). The network x selling-title split is by planned spots; allocated_nielsen_hh_imps
-- spreads the deal HH plan by spot share, i.e. assumes equal impressions per spot.
, measured_deals AS (
    SELECT DISTINCT pd.campaign_id, pd.deal_id, c.flight_start
    FROM campaign_plan_deal pd
    JOIN campaign c ON c.campaign_id = pd.campaign_id
    WHERE c.has_videoamp AND c.is_linear
),
pre_flight AS (
    SELECT md.campaign_id, md.deal_id, max(r.audit_no) AS pre_flight_audit_no
    FROM measured_deals md
    JOIN deal_revision r ON r.deal_id = md.deal_id AND CAST(r.revision_confirmed_at AS date) < md.flight_start
    GROUP BY 1, 2
),
demo_latest AS (
    SELECT * FROM (
        SELECT p.*, row_number() OVER (PARTITION BY p.deal_id, p.demo_id ORDER BY p.audit_no DESC) AS rn
        FROM deal_demo_plan p
        JOIN (SELECT DISTINCT deal_id FROM measured_deals) d ON d.deal_id = p.deal_id
        WHERE p.demo_id IN (1, 1401, 100001)
    ) WHERE rn = 1
),
demo_pre_flight AS (
    SELECT * FROM (
        SELECT pf.campaign_id, p.*, row_number() OVER (PARTITION BY pf.campaign_id, p.deal_id, p.demo_id ORDER BY p.audit_no DESC) AS rn
        FROM deal_demo_plan p
        JOIN pre_flight pf ON pf.deal_id = p.deal_id AND p.audit_no <= pf.pre_flight_audit_no
        WHERE p.demo_id = 1
    ) WHERE rn = 1
),
deal_hh AS (
    SELECT md.campaign_id, md.deal_id,
           max(CASE WHEN l.demo_id = 1 THEN l.current_as_sold_imps END)      AS nielsen_hh_plan,
           max(CASE WHEN l.demo_id = 1401 THEN l.current_as_sold_imps END)   AS videoamp_hh_plan,
           max(CASE WHEN l.demo_id = 100001 THEN l.current_as_sold_imps END) AS bigdata_hh_plan,
           max(pf.current_as_sold_imps)                                      AS nielsen_hh_plan_pre_flight
    FROM measured_deals md
    LEFT JOIN demo_latest l ON l.deal_id = md.deal_id
    LEFT JOIN demo_pre_flight pf ON pf.campaign_id = md.campaign_id AND pf.deal_id = md.deal_id
    GROUP BY 1, 2
),
spots AS (
    SELECT md.campaign_id, s.deal_id, stn.net_id, s.selling_title_id,
           sum(s.spots) AS spots, count(DISTINCT s.week_of) AS weeks,
           min(s.week_of) AS first_week, max(s.week_of) AS last_week
    FROM measured_deals md
    JOIN plan_spots s ON s.deal_id = md.deal_id
    LEFT JOIN selling_title_network stn ON stn.selling_title_id = s.selling_title_id
    GROUP BY 1, 2, 3, 4
),
spot_share AS (
    SELECT sp.*, CAST(sp.spots AS double) / nullif(sum(sp.spots) OVER (PARTITION BY sp.campaign_id, sp.deal_id), 0) AS spot_share
    FROM spots sp
),
net AS (
    SELECT CAST(net_id AS bigint) AS net_id, max(va_load_network_code) AS va_network_code, max(nielsen_load_network_code) AS nielsen_network_code
    FROM linear_digital_revenue_bronze.ideal_dci_dci_net
    GROUP BY 1
),
campaign_total AS (
    SELECT campaign_id, sum(nielsen_hh_plan) AS campaign_nielsen_hh_plan, sum(nielsen_hh_plan_pre_flight) AS campaign_nielsen_hh_plan_pre_flight
    FROM deal_hh
    GROUP BY 1
)
SELECT
    ss.campaign_id,
    ss.deal_id,
    ss.net_id,
    n.va_network_code,
    n.nielsen_network_code,
    ss.selling_title_id,
    st.selling_title_name,
    ss.weeks,
    ss.first_week,
    ss.last_week,
    ss.spots,
    ss.spot_share,
    dh.nielsen_hh_plan * ss.spot_share                    AS allocated_nielsen_hh_imps,
    dh.nielsen_hh_plan                                    AS deal_nielsen_hh_plan,
    dh.videoamp_hh_plan                                   AS deal_videoamp_hh_plan,
    dh.bigdata_hh_plan                                    AS deal_bigdata_hh_plan,
    dh.nielsen_hh_plan_pre_flight                         AS deal_nielsen_hh_plan_pre_flight,
    ct.campaign_nielsen_hh_plan,
    f.impressions                                         AS va_linear_hh_imps,
    f.impressions / nullif(ct.campaign_nielsen_hh_plan, 0) AS measured_to_plan_ratio
FROM spot_share ss
JOIN deal_hh dh ON dh.campaign_id = ss.campaign_id AND dh.deal_id = ss.deal_id
JOIN campaign_total ct ON ct.campaign_id = ss.campaign_id
LEFT JOIN net n ON n.net_id = ss.net_id
LEFT JOIN linear_digital_revenue_gold.dim_selling_title st ON CAST(st.selling_title_id AS bigint) = ss.selling_title_id
LEFT JOIN final_report f ON f.campaign_id = ss.campaign_id AND f.recency = 1
ORDER BY ss.campaign_id, ss.deal_id, ss.spots DESC
