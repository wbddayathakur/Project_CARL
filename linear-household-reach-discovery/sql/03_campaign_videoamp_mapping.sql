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
