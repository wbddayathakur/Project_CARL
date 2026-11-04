-- How many campaigns are candidates: Linear, VideoAmp-measured, completed, with plan IDs.
SELECT
    campaign_type,
    media_type,
    is_linear,
    has_videoamp,
    flight_end <= current_date - INTERVAL '21' DAY            AS completed,
    count(*)                                                  AS campaigns,
    count_if(ideal_deal_ids_raw IS NOT NULL AND trim(ideal_deal_ids_raw) <> '') AS with_ideal_deal_ids,
    count_if(strpos(coalesce(ideal_deal_ids_raw, ''), ',') > 0) AS with_multiple_deals,
    count_if(fw_key <> '')                                    AS with_fw_campaign_ids,
    count_if(videoamp_planning_id IS NOT NULL AND trim(videoamp_planning_id) <> '') AS with_videoamp_planning_id,
    count_if(flight_start IS NULL OR flight_end IS NULL)      AS bad_flight_dates,
    count_if(flight_end < flight_start)                       AS end_before_start,
    min(flight_start)                                         AS earliest_flight,
    max(flight_end)                                           AS latest_flight
FROM campaign
GROUP BY 1, 2, 3, 4, 5
ORDER BY is_linear DESC, has_videoamp DESC, completed DESC
