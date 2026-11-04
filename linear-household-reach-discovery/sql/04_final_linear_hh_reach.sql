-- Final measured VideoAmp Linear Total household reach per campaign, with consistency checks.
-- is_final uses the report's slice end date (data-through); reports from early 2025 have none, so they
-- fall back to requested >= flight_end + 17 days (Linear data lags ~17 days).
SELECT
    c.campaign_id,
    c.campaign_name,
    c.flight_start,
    c.flight_end,
    f.req_start                                                        AS measured_start,
    f.req_end                                                          AS measured_end,
    f.slice_start                                                      AS data_from,
    f.slice_end                                                        AS data_through,
    date_diff('day', f.slice_end, c.flight_end)                        AS days_short_of_flight_end,
    coalesce(f.slice_end >= c.flight_end, CAST(f.created_at AS date) >= date_add('day', 17, c.flight_end)) AS is_final,
    CASE WHEN f.slice_end IS NULL THEN 'REQUEST_DATE_RULE' ELSE 'DATA_THROUGH' END AS is_final_basis,
    f.request_id,
    f.created_at                                                       AS report_requested_at,
    f.mapping_path,
    f.mapping_paths,
    f.campaigns_sharing_request,
    f.window_exact_match,
    f.audience_id,
    f.impressions                                                      AS linear_hh_impressions,
    f.reach                                                            AS linear_hh_reach,
    f.frequency                                                        AS linear_hh_frequency,
    f.reach <= f.impressions                                           AS check_reach_le_imps,
    abs(f.reach * f.frequency - f.impressions) / nullif(f.impressions, 0) AS freq_consistency_error,
    abs(f.reach * f.frequency - f.impressions) / nullif(f.impressions, 0) < 0.01 AS check_freq_consistent,
    count(r.request_id)                                                AS later_requests_without_linear_hh
FROM final_report f
JOIN campaign c ON c.campaign_id = f.campaign_id
LEFT JOIN campaign_request r ON r.campaign_id = f.campaign_id AND r.created_at > f.created_at
WHERE f.recency = 1
GROUP BY c.campaign_id, c.campaign_name, c.flight_start, c.flight_end, f.req_start, f.req_end, f.slice_start, f.slice_end,
         f.request_id, f.created_at, f.mapping_path, f.mapping_paths, f.campaigns_sharing_request, f.window_exact_match, f.audience_id, f.impressions, f.reach, f.frequency
ORDER BY c.flight_end DESC
