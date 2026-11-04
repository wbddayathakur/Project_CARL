-- Forecast availability for measured Linear campaigns. Neither forecast source carries reach
-- (Glue check 2026-11-02): the Nielsen Linear forecast is C3/C7 ratings by network x demo x QH,
-- and the Foresite VideoAmp forecast is HH C3 average audience (000) by VideoAmp audience.
-- This shows what pre-flight forecast metadata exists for each campaign and the forecast grain.
-- Reads the bronze VideoAmp forecast: the silver copy fails in Dev and Prod (Iceberg table without metadata location).
, runs AS (
    SELECT forecast_run_id, model_name, model_version, CAST(completed_at AS date) AS completed_on,
           forecast_horizon_start, forecast_horizon_end, status
    FROM linear_forecasting_bronze.dim_forecast_run
),
va_fcst AS (
    SELECT CAST(audience_id AS varchar) AS audience_id,
           min(broadcast_date) AS first_forecast_date,
           max(broadcast_date) AS last_forecast_date,
           min(datetime_utc_processed_by_foresite) AS first_processed,
           max(datetime_utc_processed_by_foresite) AS last_processed
    FROM ddl_forecasting_bronze.ddl_forecasts_daily_tracking_videoamp
    GROUP BY 1
),
measured AS (
    SELECT c.campaign_id, c.campaign_name, c.campaign_type, c.flight_start, c.flight_end, c.videoamp_audience_ids, c.videoamp_planning_id
    FROM campaign c
    WHERE c.has_videoamp AND c.is_linear
)
SELECT
    m.campaign_id,
    m.campaign_name,
    m.campaign_type,
    m.flight_start,
    m.flight_end,
    m.videoamp_planning_id,
    count(DISTINCT r.forecast_run_id)                                                        AS nielsen_runs_before_flight,
    max(fr.first_run_on)                                                                     AS nielsen_first_run_on,
    count(DISTINCT v.audience_id)                                                            AS va_audiences_with_forecast,
    min(v.first_processed)                                                                   AS va_first_processed,
    count(DISTINCT CASE WHEN CAST(v.first_processed AS varchar) < CAST(m.flight_start AS varchar) THEN v.audience_id END) AS va_audiences_processed_before_flight
FROM measured m
CROSS JOIN (SELECT min(completed_on) AS first_run_on FROM runs) fr
LEFT JOIN runs r ON r.completed_on < m.flight_start
LEFT JOIN va_fcst v
       ON contains(transform(split(coalesce(m.videoamp_audience_ids, ''), ','), s -> trim(s)), v.audience_id)
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY m.flight_end DESC
