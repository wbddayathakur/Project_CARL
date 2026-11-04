# FF-11 — Govern the three DF-owned reference maps

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Story |
| Suggested owner | Kaustuva Hota's team |
| Size / Wave | S / 2 |
| Suggested priority | Medium |
| Depends on | FF-01 |
| Related Jira | CARL-4222 (possible overlap on `d_reseller`) |
| Labels | `financial-forecasting`, `df-team`, `reference-data` |

## User story

As a **Finance forecasting owner**, I want **`RESELLER_TYPE_MAP`, `SITE_SECTION_NETWORK_LDCI_MAP` and `BRAND_GROUP_STANDARD_NAME_MAPPING` governed as reference data** so that **changes are reviewed, versioned and visible instead of silently altering the forecast**.

## Context

These three tables live in `DF_SILVER` and are DF-owned; they are not in CARL. The thread lists them as not in CARL and gives no governance plan. CARL-4222 folds `d_reseller` into FreeWheel `dim_network`, which may overlap `RESELLER_TYPE_MAP`.

## Scope

1. Name an owner and a steward for each map.
2. Record, per map: purpose, key, columns, row count, update frequency and last change.
3. Put each map under change control: source-controlled definition or load script, a change log and a review step.
4. Add a check that flags unmapped values in the pipeline (for example a site section with no network).
5. Check overlap with `dim_network` and CARL-4222 and record the outcome.

## Out of scope

Moving the maps into CARL Glue. FF-13 decides catalog visibility.

## Acceptance criteria

- **Given** each map, **when** the story is done, **then** it has a named owner, steward and documented update process.
- **Given** a change to a map, **when** it is deployed, **then** it has a review record and a change-log entry.
- **Given** a value in source with no map row, **when** the pipeline runs, **then** it is reported and counted.
- **Given** the CARL-4222 overlap check, **when** it is complete, **then** the outcome is on the ticket.

## Test plan

- Unmapped-value test with a seeded unmapped key.
- Compare map contents between dev, QA and prod.
- Review of the change process by the DF lead.

## Dependencies and risks

- Ownership may be unclear; if no one accepts ownership, escalate to Debarghyo.

## Open questions

- Who owns each map today?
