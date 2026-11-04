# FF-13 — Decide and (if wanted) implement Glue visibility for DF Snowflake-managed Iceberg

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Decision, then story |
| Suggested owner | Debarghyo Sengupta (decision); DF engineer (implementation) |
| Size / Wave | M / 3 |
| Suggested priority | Low to Medium |
| Depends on | CARL-580 status confirmed |
| Related Jira | CARL-580 |
| Labels | `financial-forecasting`, `catalog`, `federation`, `decision` |

## User story

As a **data platform owner**, I want **a decision on whether the DF Snowflake-managed Iceberg tables should be visible in the CARL Glue catalog** so that **discovery, lineage and access are consistent with the rest of CARL, or the exclusion is a documented choice**.

## Context

The DF tables (for example `DIGIREV_DEV.DF_SILVER.CAPACITY_HISTORY_FINANCE`) are Snowflake-managed (`CATALOG='SNOWFLAKE'`, not Glue) through external volumes pointing at `s3://digital-forecasting-{silver|gold}-us-east-1-{dev|qa}/snowflake/iceberg/df_{silver|gold}`. They are not in CARL Glue. CARL-580 (Configure Catalog Federation — Snowflake to Glue) is **Done in Jira**, but the weekly status of 19 Oct still lists federation AT RISK with a manual-sync fallback.

## Options

| Option | Effect |
|---|---|
| A. Leave outside CARL, document | No work; DF tables stay invisible to CARL discovery |
| B. Federate via the CARL-580 mechanism | Visibility in Glue; depends on whether federation is live |
| C. Manual sync | Works now; manual upkeep |

## Scope

1. Confirm whether CARL-580's federation is live or the fallback is in use.
2. Decide the option with Daya and Debarghyo, with the reason recorded.
3. If B or C, implement for the DF Silver and Gold tables in dev and QA, with correct permissions.
4. Update the catalog so DF tables show with owner and source.

## Out of scope

Moving DF tables to CARL-managed storage. Changing QuickSight sources.

## Acceptance criteria

- **Given** CARL-580, **when** checked, **then** the live federation status is on the ticket.
- **Given** the three options, **when** the decision is made, **then** the chosen option and reason are recorded.
- **Given** option B or C, **when** implemented, **then** the DF tables show in Glue in dev and QA with the same schema as Snowflake.
- **Given** the catalog run, **when** it completes, **then** the DF tables appear with an owner and are marked not CARL-produced.

## Test plan

- Schema comparison between Snowflake and Glue for each table.
- Read test through Athena if option B or C.
- Permission test: an unauthorised role is denied.

## Dependencies and risks

- Federation status is inconsistent between Jira and the weekly status.
- Tables could appear certified when they are not; label them clearly.

## Open questions

- Does anyone besides the DF team need to read these tables?
