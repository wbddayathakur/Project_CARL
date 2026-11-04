-- Campaign-to-iDeal deal join (via GAB deal number) and plan versions relative to the flight.
-- audit_no is the iDeal revision key shared by deal_header, deal_revision and every plan table;
-- pre_flight_audit_no is the last revision confirmed before flight start (the plan a forecast would have used).
, rev AS (
    SELECT
        deal_id,
        count(*)                                   AS revisions,
        max(audit_no)                              AS latest_audit_no,
        min(revision_confirmed_at)                 AS first_confirmed_at,
        max(revision_confirmed_at)                 AS last_confirmed_at
    FROM deal_revision
    GROUP BY 1
),
pre_flight AS (
    SELECT pd.campaign_id, pd.deal_id, max(r.audit_no) AS pre_flight_audit_no
    FROM campaign_plan_deal pd
    JOIN campaign c ON c.campaign_id = pd.campaign_id
    JOIN deal_revision r ON r.deal_id = pd.deal_id AND CAST(r.revision_confirmed_at AS date) < c.flight_start
    GROUP BY 1, 2
)
SELECT
    c.campaign_id,
    c.campaign_name,
    c.campaign_type,
    c.flight_start,
    c.flight_end,
    cd.gab_deal_id,
    d.deal_id                                      AS ideal_internal_deal_id,
    d.deal_id IS NOT NULL                          AS deal_found,
    d.deal_status,
    d.deal_description,
    d.header_versions,
    d.audit_no                                     AS header_audit_no,
    d.deal_revision_no,
    d.plan_changed,
    d.upfront_scatter,
    d.guaranteed_ind,
    d.row_deleted_ind,
    rev.revisions,
    rev.latest_audit_no,
    rev.first_confirmed_at,
    rev.last_confirmed_at,
    pf.pre_flight_audit_no
FROM campaign c
JOIN campaign_deal cd ON cd.campaign_id = c.campaign_id
LEFT JOIN deal d ON d.gab_deal_id = cd.gab_deal_id
LEFT JOIN rev ON rev.deal_id = d.deal_id
LEFT JOIN pre_flight pf ON pf.campaign_id = c.campaign_id AND pf.deal_id = d.deal_id
WHERE c.has_videoamp AND c.is_linear
ORDER BY c.flight_end DESC, c.campaign_id, cd.gab_deal_id
