-- Nielsen national TV household universe (season period containing the flight midpoint) and reach %
-- on that basis. distinct_ue_nat > 1 would mean ue_nat is network-specific.
, flight AS (
    SELECT c.campaign_id, c.flight_start, c.flight_end,
           date_add('day', date_diff('day', c.flight_start, c.flight_end) / 2, c.flight_start) AS flight_mid
    FROM campaign c
    WHERE c.has_videoamp AND c.is_linear AND c.flight_start IS NOT NULL AND c.flight_end IS NOT NULL
),
ue_periods AS (
    SELECT f.campaign_id, u.ue_start, u.ue_end,
           max(u.ue_nat_hh) AS ue_nat_hh,
           count(DISTINCT u.ue_nat) AS distinct_ue_nat,
           count(DISTINCT u.nielsen_network_id) AS networks,
           row_number() OVER (PARTITION BY f.campaign_id ORDER BY date_diff('day', u.ue_start, u.ue_end) DESC) AS rn
    FROM flight f
    JOIN universe u ON f.flight_mid BETWEEN u.ue_start AND u.ue_end
    GROUP BY 1, 2, 3
),
ue_for_flight AS (
    SELECT * FROM ue_periods WHERE rn = 1
)
SELECT
    f.campaign_id,
    f.flight_start,
    f.flight_end,
    f.flight_mid,
    ue.ue_start                        AS universe_effective_start,
    ue.ue_end                          AS universe_effective_end,
    ue.ue_nat_hh                       AS nielsen_hh_universe,
    ue.distinct_ue_nat,
    ue.networks,
    r.reach                            AS va_linear_hh_reach,
    r.reach / nullif(ue.ue_nat_hh, 0)  AS reach_pct
FROM flight f
LEFT JOIN ue_for_flight ue ON ue.campaign_id = f.campaign_id
LEFT JOIN final_report r ON r.campaign_id = f.campaign_id AND r.recency = 1
ORDER BY f.flight_end DESC
