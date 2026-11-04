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
