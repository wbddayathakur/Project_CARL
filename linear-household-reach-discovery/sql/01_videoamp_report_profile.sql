-- Validates the measured-reach definition: the dimension, slice, medium and
-- household-audience values the Measurement Summary SQL depends on must exist.
SELECT
    dimension_set_name,
    time_slice,
    medium,
    stream,
    is_household,
    CASE WHEN is_household THEN audience_id ELSE '(other audiences)' END AS audience,
    count(*)                                   AS report_rows,
    count(DISTINCT request_id)                 AS requests,
    count_if(slice_end IS NULL)                AS rows_unparsed_slice_end,
    min(slice_end_raw)                         AS min_slice_end_raw,
    max(slice_end_raw)                         AS max_slice_end_raw,
    min(reach)                                 AS min_reach,
    approx_percentile(reach, 0.5)              AS median_reach,
    max(reach)                                 AS max_reach,
    count_if(reach > impressions)              AS rows_reach_gt_imps
FROM va_report
WHERE dimension_set_name = 'medium'
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY time_slice, medium, is_household DESC
