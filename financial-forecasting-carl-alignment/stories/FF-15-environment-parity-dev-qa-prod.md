# FF-15 — Document and verify DEV/QA/PROD parity for the Finance forecast pipeline

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Analysis |
| Suggested owner | Kaustuva Hota's team |
| Size / Wave | S / 0 |
| Suggested priority | High |
| Depends on | None |
| Related Jira | — |
| Labels | `financial-forecasting`, `df-team`, `environments` |

## User story

As a **Finance forecasting product owner**, I want **the DEV, QA and PROD setups of the pipeline documented and compared** so that **we know whether prod is configured like `DIGIREV_DEV` before any source is repointed**.

## Context

Question 6 of the thread asked for the refresh schedule **and** whether prod is set up the same way as `DIGIREV_DEV`. Kaustuva's reply covered the schedule (daily 08:00 ET) and the job logic, but not prod parity. Known for dev and QA: `EXT_VOL_DF_ICEBERG_<ENV>_SILVER/GOLD` point to `s3://digital-forecasting-{silver|gold}-us-east-1-{dev|qa}/snowflake/iceberg/df_{silver|gold}`, with `CATALOG='SNOWFLAKE'` (Snowflake-managed). Prod bucket names were not given.

## Scope

1. Compare, per environment: Snowflake database and schema names, external volumes, S3 buckets, catalog type, Databricks job definition and schedule, stored procedure versions, share sources, QuickSight datasets.
2. Record which environment each QuickSight dashboard reads from.
3. List every difference and classify it: intended, drift, or unknown.
4. Open follow-up stories for drift that affects repointing.

## Out of scope

Fixing differences (unless trivial), and any CARL Glue work (see FF-09).

## Acceptance criteria

- **Given** the three environments, **when** the comparison is done, **then** a table shows each configuration item and its value per environment.
- **Given** any difference, **when** it is recorded, **then** it is classified intended, drift or unknown, with an owner.
- **Given** the prod Databricks job, **when** it is inspected, **then** its schedule, `load_mode` and `days_back` are stated and compared to dev.
- **Given** the final document, **when** Kaustuva signs it off, **then** the sign-off is attached to the ticket.

## Test plan

- Configuration is read from Terraform and from the live systems, and the two are compared.
- A second engineer re-checks any item marked "unknown".
- Evidence (screenshots or command output) is attached.

## Dependencies and risks

- Prod access for the reviewer.
- Terraform and live state may differ; treat live state as authoritative.

## Open questions

- Is there a prod S3 bucket pair equivalent to the dev and QA ones?
- Do prod and dev share the same Snowflake share (`SHARE_PROD_ADS_ENGAGEMENT`)?
