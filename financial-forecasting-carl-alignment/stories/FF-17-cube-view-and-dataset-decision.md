# FF-17 — Decide Cube semantic view and QuickSight dataset path for the Finance capacity forecast

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Decision |
| Suggested owner | Daya Thakur and Rohini Vugumudi |
| Size / Wave | S / 3 |
| Suggested priority | Gated on the priority Rohini is to share |
| Depends on | FF-14; priority input |
| Related Jira | CARL-1364 |
| Labels | `financial-forecasting`, `cube`, `quicksight`, `decision` |

## User story

As a **product owner for Finance reporting**, I want **a decision on whether the capacity forecast gets a Cube view and a different QuickSight dataset path** so that **the reporting either uses the semantic layer or is knowingly outside it**.

## Context

QuickSight dashboards are backed directly by two DF Gold views: `CAPACITY_FORECAST_FINANCE_ENT` and `VW_STREAMING_SPORTS_CAPACITY_ACTUALS_FINANCE`. There is no Cube model, and Athena is not used. The existing CARL finance Cube views cover booked revenue and pacing, not capacity. CARL-1364 aims at one set of definitions across Finance sources.

## Options

| Option | Effect |
|---|---|
| A. Keep direct Snowflake Gold views | No change; no semantic layer |
| B. Add Cube views over the DF Gold tables | Shared definitions; needs DF tables reachable by Cube |
| C. Move the datasets to Athena over Glue-visible tables | Only after FF-13 chooses visibility |

## Scope

1. List the measures and dimensions used by the dashboards.
2. Check overlap with the CARL-1364 definitions (booked revenue, pipeline, forecast) and record conflicts.
3. Decide the option with Daya and Rohini and record the reason.
4. If B or C, open an implementation story with its own acceptance criteria and tests.

## Out of scope

Building the Cube view or dataset.

## Acceptance criteria

- **Given** the two Gold views, **when** reviewed, **then** their measures and dimensions are listed.
- **Given** CARL-1364, **when** compared, **then** differing definitions are listed with an owner for each.
- **Given** the three options, **when** decided, **then** the choice and reason are on the ticket.
- **Given** option B or C, **when** chosen, **then** a follow-up story exists, linked to this epic.

## Test plan

- Review of the definition comparison with Finance.
- Decision recorded in a meeting note attached to the ticket.

## Dependencies and risks

- Priority is not confirmed.
- Choosing B or C without FF-13 may be impossible.

## Open questions

- Is a semantic layer a requirement from Finance, or a CARL preference?
