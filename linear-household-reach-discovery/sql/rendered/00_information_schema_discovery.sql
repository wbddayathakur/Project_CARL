-- Standalone (does not use _base.sql). Column-level check of every candidate table,
-- plus any reach / universe / forecast / join-key looking column in the in-scope databases.
-- In Dev this fails while any schema holds an Iceberg table without a metadata location; use verify_columns.py then.
SELECT
    CASE WHEN (table_schema, table_name) IN (
            ('impact_bronze', 'campaign'),
            ('impact_bronze', 'videoamp_request'),
            ('impact_bronze', 'videoamp_measurement_report'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_deal_header'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_order_line'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_order_line_sell'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_order_line_sell_weeks'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_order_line_impressions'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_deal_revision'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_deal_demo_target'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_idl_hh_demo_map'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_pricing_rating'),
            ('linear_digital_revenue_bronze', 'ideal_dci_dci_net'),
            ('linear_digital_revenue_bronze', 'ideal_dci_calendar_week'),
            ('linear_digital_revenue_gold', 'dim_daypart'),
            ('linear_digital_revenue_gold', 'dim_selling_title'),
            ('big_mit_bronze', 'universe_estimate'),
            ('linear_forecasting_bronze', 'dim_forecast_run'),
            ('linear_forecasting_gold', 'fct_forecast_current'),
            ('ddl_forecasting_silver', 'ddl_forecasts_daily_tracking_videoamp'),
            ('carl_ke_poc_gold_dev', 'fact_impressions_certified'),
            ('carl_dwhprd_gold_dev', 'deal_revenue_snapshot_dim')
         ) THEN 'candidate table' ELSE 'pattern match' END AS why,
    table_schema,
    table_name,
    ordinal_position,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema IN (
        'impact_bronze', 'linear_digital_revenue_bronze', 'linear_digital_revenue_silver',
        'linear_digital_revenue_gold', 'linear_forecasting_bronze', 'linear_forecasting_silver',
        'linear_forecasting_gold', 'ddl_forecasting_bronze', 'ddl_forecasting_silver',
        'carl_dwhprd_gold_dev', 'carl_ke_poc_gold_dev', 'big_mit_bronze')
  AND (
        (table_schema, table_name) IN (
            ('impact_bronze', 'campaign'), ('impact_bronze', 'videoamp_request'),
            ('impact_bronze', 'videoamp_measurement_report'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_deal_header'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_order_line'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_order_line_sell'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_order_line_sell_weeks'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_order_line_impressions'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_deal_revision'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_deal_demo_target'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_idl_hh_demo_map'),
            ('linear_digital_revenue_bronze', 'ideal_dealbldr_dci_pricing_rating'),
            ('linear_digital_revenue_bronze', 'ideal_dci_dci_net'),
            ('linear_digital_revenue_bronze', 'ideal_dci_calendar_week'),
            ('linear_digital_revenue_gold', 'dim_daypart'),
            ('linear_digital_revenue_gold', 'dim_selling_title'),
            ('big_mit_bronze', 'universe_estimate'),
            ('linear_forecasting_bronze', 'dim_forecast_run'),
            ('linear_forecasting_gold', 'fct_forecast_current'),
            ('ddl_forecasting_silver', 'ddl_forecasts_daily_tracking_videoamp'),
            ('carl_ke_poc_gold_dev', 'fact_impressions_certified'),
            ('carl_dwhprd_gold_dev', 'deal_revenue_snapshot_dim'))
        OR regexp_like(lower(column_name), 'reach|universe|^ue_|request|campaign|deal_?id|forecast_run|version|grp|daypart')
      )
ORDER BY why, table_schema, table_name, ordinal_position
