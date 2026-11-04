# FF-05 — Build the sellable revenue video-asset-day table in CARL Silver/Gold

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Story (contingent on the FF-04 decision) |
| Suggested owner | To be decided (DF team or CARL FreeWheel Silver team) |
| Size / Wave | L / 3 |
| Suggested priority | Gated on Rohini Vugumudi's priority |
| Depends on | FF-04, FF-09, priority decision |
| Related Jira | CARL-2887, CARL-3809, AI-087 |
| Labels | `financial-forecasting`, `freewheel`, `silver`, `gold` |

## User story

As a **Finance forecasting owner**, I want **the sellable revenue table by video asset by day built in CARL** so that **the main forecast input is governed and reconciles with other CARL FreeWheel reporting**.

## Context

Only proceeds if FF-04 recommends a CARL build. The FF-04 design defines table name, layer, grain, keys and load method. FreeWheel Silver has no date for prod, and Phase 1 excludes this grain.

## Scope

1. Implement the table as designed in FF-04, following the FreeWheel Silver processing rules (merge key, late-arrival window, `row_hash_silver`).
2. Run in dev and QA; register in prod after FF-09.
3. Add data-quality checks: key uniqueness, nulls in required columns, day coverage.
4. Reconcile to the share view through FF-14.
5. Update Cube/Iceberg catalogs and the mapping in FF-01.

## Out of scope

Decoupling from the third-party feed. Dashboard changes.

## Acceptance criteria

- **Given** the design, **when** the table is built, **then** its columns and grain match the signed-off FF-04 spec.
- **Given** the last 7 activity dates, **when** a late correction arrives, **then** the table reflects it according to the documented rule.
- **Given** FF-14, **when** it runs, **then** the table passes the agreed tolerances for at least the agreed window.
- **Given** dev, QA and prod, **when** the table is queried, **then** it exists with the same shape (prod after FF-09).
- **Given** the table, **when** the catalog runs, **then** it appears with an owner and a refresh promise.

## Test plan

- Uniqueness, null and day-coverage checks in the pipeline.
- Reconciliation per day and by key dimensions.
- Failure test: stop an upstream and confirm the run fails visibly.

## Dependencies and risks

- Priority is not yet confirmed.
- Enriched third-party fields may not be derivable.
- History available in CARL Bronze may be shorter than the forecast needs.

## Open questions

- Which team owns the table once built?
