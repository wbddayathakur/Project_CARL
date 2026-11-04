-- The validation sample: completed, VideoAmp-measured Linear campaigns with a deal match and a
-- Linear Total household report, one row each, carrying every required field.
-- Forecast columns stay null: no pre-campaign reach forecast exists in CARL (see 08).
, deals_found AS (
    SELECT cd.campaign_id,
           array_agg(DISTINCT cd.gab_deal_id) AS ideal_deal_ids,
           count_if(d.deal_id IS NOT NULL) AS deals_found,
           max(d.audit_no) AS plan_audit_no
    FROM campaign_deal cd
    LEFT JOIN deal d ON d.gab_deal_id = cd.gab_deal_id
    GROUP BY 1
),
plan_hh AS (
    SELECT pd.campaign_id, sum(p.current_as_sold_imps) AS planned_linear_hh_imps
    FROM campaign_plan_deal pd
    JOIN (SELECT dp.*, row_number() OVER (PARTITION BY deal_id ORDER BY audit_no DESC) AS rn
          FROM deal_demo_plan dp WHERE demo_id = 1) p ON p.deal_id = pd.deal_id AND p.rn = 1
    GROUP BY 1
),
ue AS (
    SELECT campaign_id, ue_nat_hh AS hh_universe, ue_start AS universe_effective_start
    FROM (
        SELECT c.campaign_id, u.ue_nat_hh, u.ue_start,
               row_number() OVER (PARTITION BY c.campaign_id ORDER BY date_diff('day', u.ue_start, u.ue_end) DESC) AS rn
        FROM campaign c
        JOIN universe u
          ON date_add('day', date_diff('day', c.flight_start, c.flight_end) / 2, c.flight_start) BETWEEN u.ue_start AND u.ue_end
    ) WHERE rn = 1
),
assembled AS (
    SELECT
        c.campaign_id,
        c.campaign_name,
        c.campaign_type,
        df.ideal_deal_ids,
        cardinality(df.ideal_deal_ids) > 1                   AS multi_deal,
        c.flight_start,
        c.flight_end,
        f.req_start                                          AS measured_start,
        f.req_end                                            AS measured_end,
        f.slice_end                                          AS data_through,
        f.audience_id,
        ue.hh_universe,
        'NIELSEN_UE'                                         AS universe_source,
        ue.universe_effective_start,
        p.planned_linear_hh_imps,
        f.impressions / nullif(p.planned_linear_hh_imps, 0)  AS measured_to_plan_ratio,
        df.plan_audit_no,
        f.request_id                                         AS va_request_id,
        f.created_at                                         AS va_report_requested_at,
        f.impressions                                        AS va_linear_imps,
        f.reach                                              AS va_linear_hh_reach,
        f.reach / nullif(ue.hh_universe, 0)                  AS va_reach_pct,
        f.frequency                                          AS va_linear_frequency,
        coalesce(f.slice_end >= c.flight_end, CAST(f.created_at AS date) >= date_add('day', 17, c.flight_end)) AS is_final,
        f.mapping_paths,
        f.campaigns_sharing_request,
        f.window_exact_match,
        c.videoamp_planning_id,
        CAST(NULL AS double)                                 AS forecast_reach_hh,
        CAST(NULL AS timestamp)                              AS forecast_created_at,
        CAST(NULL AS varchar)                                AS forecast_version,
        row_number() OVER (PARTITION BY c.quarter
                           ORDER BY cardinality(df.ideal_deal_ids) DESC, c.flight_end DESC) AS rank_in_quarter
    FROM campaign c
    JOIN deals_found df ON df.campaign_id = c.campaign_id AND df.deals_found > 0
    JOIN final_report f ON f.campaign_id = c.campaign_id AND f.recency = 1
    LEFT JOIN plan_hh p ON p.campaign_id = c.campaign_id
    LEFT JOIN ue ON ue.campaign_id = c.campaign_id
    WHERE c.has_videoamp
      AND c.is_linear
      AND c.flight_end <= current_date - INTERVAL '21' DAY
      AND f.campaigns_sharing_request = 1
)
SELECT *
FROM assembled
WHERE rank_in_quarter <= 4
ORDER BY flight_end DESC
LIMIT 12
