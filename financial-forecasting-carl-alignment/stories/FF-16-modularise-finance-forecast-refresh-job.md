# FF-16 — Modularise `DF_Run_Finance_Forecast_Capacity`

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment (optional, parked) |
| Type | Story |
| Suggested owner | Kaustuva Hota's team |
| Size / Wave | M / Parked |
| Suggested priority | Low for alignment; DF backlog item |
| Depends on | FF-14 |
| Related Jira | None found |
| Labels | `financial-forecasting`, `df-team`, `tech-debt` |

## User story

As a **DF data engineer**, I want **the Finance forecast job split into modular, independently testable steps** so that **source changes and reruns do not require rebuilding the entire forecast table**.

## Context

Kaustuva stated a plan to make the process more modular and manageable, but it is not set up yet. Today `DF_Run_Finance_Forecast_Capacity` (Databricks, daily 08:00 ET) runs two procedures in order:
- `SP_LOAD_CAPACITY_HISTORY_FINANCE` loads `CAPACITY_HISTORY_FINANCE`: INCREMENTAL, `days_back=7`, one transaction that deletes the last 7 activity dates and inserts rebuilt rows. FULL mode truncates, needs a `START_DATE` and is not part of the daily job.
- `SP_LOAD_CAP_FIN_FORECAST` truncates and rebuilds `CAPACITY_FORECAST_FINANCE` every day (actuals plus 365-day forecast), regardless of the job's `load_mode`. Every row carries the same `LAST_PROCESS_UTC`.

The job is defined in `foresite_digital/finance_forecast_capacity.tf` with notebook `data_engineering/finance_forecast_capacity.ipynb`.

## Scope

1. Write down the target design: steps, inputs, outputs, rerun and backfill behaviour.
2. Separate source reads, transformation and forecast build so each step can run and be tested alone.
3. Add a rerun path for a date range that does not truncate the full forecast.
4. Keep outputs identical to the current job, proven through FF-14.

## Out of scope

Changing the forecast model. Moving off Databricks.

## Acceptance criteria

- **Given** the new design, **when** a single step is rerun, **then** only its outputs change.
- **Given** a backfill range, **when** run, **then** the target table is changed only for that range.
- **Given** the same inputs, **when** old and new jobs run, **then** outputs match within tolerance.
- **Given** a failure in one step, **when** it occurs, **then** the run fails visibly with the step named.

## Test plan

- Output comparison against the current job for two weeks.
- Failure injection per step.
- Peer review of the job definition.

## Dependencies and risks

- Rewrites change a production Finance process; run in parallel before cutover.
- Not required for CARL alignment; keep out of the critical path.

## Open questions

- Does Kaustuva's team already have a design?
