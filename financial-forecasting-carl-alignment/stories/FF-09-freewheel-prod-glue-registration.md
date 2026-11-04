# FF-09 — Register FreeWheel Bronze (and Silver) in the prod Glue catalog

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment (linked dependency) |
| Type | Dependency story (CARL-owned) |
| Suggested owner | CARL platform team (Hong Zhang / platform lead to confirm) |
| Size / Wave | M / 1 |
| Suggested priority | High. Blocks any prod read of FreeWheel through CARL. |
| Depends on | Decision on archived CARL-3852 |
| Related Jira | CARL-3852 (Archive), CARL-746, CARL-2887; roadmap item "FreeWheel production Glue catalog registration" |
| Labels | `financial-forecasting`, `carl-dependency`, `freewheel`, `glue` |

## User story

As a **consumer of CARL FreeWheel data**, I want **`freewheel_bronze` and `freewheel_silver` registered in the prod Glue catalog** so that **prod pipelines can read FreeWheel from CARL**.

## Context

Glue shows `freewheel_bronze` with 79 tables in dev and **0 in prod** (7 Oct). The roadmap states that prod S3 landing exists but the prod Glue catalog is not registered; five initiatives wait on this. CARL-3852 ("Bring freewheel_bronze and freewheel_silver under carl-infra Glue database and Lake Formation management") is the closest existing story, and it is **Archived**.

## Scope

1. Confirm why CARL-3852 was archived and whether to re-open it or create a new story linked to it.
2. Register the prod databases and tables, under carl-infra and Lake Formation management.
3. Grant read access to the DF team's role, following least privilege.
4. Confirm the same table set and schema as dev.
5. Update the Glue inventory and the Cube/Iceberg catalog.

## Out of scope

FreeWheel Silver build progress (CARL-2887); consumer repointing (FF-02, FF-03).

## Acceptance criteria

- **Given** prod Glue, **when** the story is done, **then** `freewheel_bronze` lists the same tables as dev, and Silver tables are listed once released.
- **Given** the DF team role, **when** it runs a read query in prod, **then** it succeeds, and a role without grant is denied.
- **Given** the infra code, **when** it is applied, **then** the databases and permissions are under carl-infra and Lake Formation.
- **Given** the next catalog run, **when** it completes, **then** prod shows non-zero FreeWheel tables.

## Test plan

- Compare dev and prod table lists and schemas.
- Positive and negative access tests, with output attached.
- Sample row-count check between prod S3 landing and the registered table.

## Dependencies and risks

- Decision needed on CARL-3852's archive reason; there may be a design change.
- This is CARL work, outside Daya's "no dependency on CARL" statement. Treat as a **tracked external dependency**, not DF scope.

## Open questions

- Who in CARL owns this, and what is the date?
- Is prod Glue registration planned as part of the Silver prod release?
