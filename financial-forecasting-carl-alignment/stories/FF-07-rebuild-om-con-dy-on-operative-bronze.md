# FF-07 — Rebuild `OM_CON_DY_V` logic on `operative_bronze`

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Story |
| Suggested owner | DF team, with Mike Hodge (Op1 Silver) consulted |
| Size / Wave | L / 2 |
| Suggested priority | High |
| Depends on | FF-01; CARL-3509 outcome; CARL-2888 (soft) |
| Related Jira | CARL-744, CARL-2888, CARL-2889–2891, CARL-3509 |
| Labels | `financial-forecasting`, `df-team`, `operative`, `rebuild` |

## User story

As a **DF data engineer**, I want **the `OM_CON_DY_V` logic rebuilt on `operative_bronze`** so that **the forecast no longer depends on the share view and the line-day logic is documented and testable**.

## Context

`OM_CON_DY_V` is not a CARL table. It is logic in the Looker ETL for the Op1 contracted snapshot: expand each order line into days, apply currency and a custom pacing view. Inputs exist in prod `operative_bronze`: `sales_order_line_items`, `sales_order`, `currency_exchange_rate`, `sales_line_item_booked_delivered` and related tables. CARL-3509 found that the DF consumer already ran into `om_con_dy_v` specifics: the `source` column filter (`WHERE source = 'WBD'`) cannot be reproduced because `source` is absent, all columns are strings, and 15 column names are malformed. Operative Silver (CARL-2888) is To Do with three unassigned children.

## Scope

1. Document the view's output grain (order line by day), columns, filters, currency conversion and pacing rules.
2. Rebuild in DF's environment from `operative_bronze`, with explicit typing and the casting rules from FF-08.
3. Handle the malformed column names with quoted or aliased reads, until CARL-3509 delivers a fix.
4. Run in dev and QA; compare with the share view through FF-14.
5. If CARL-2888 later provides Silver, record how this logic moves or is replaced.

## Out of scope

Building CARL Operative One Silver. Fixing Bronze (CARL-3509).

## Acceptance criteria

- **Given** a line and day, **when** the rebuild runs, **then** day-level amount and quantity match the share view within the agreed tolerance.
- **Given** a line spanning several days, **when** expanded, **then** daily values add up to the line total.
- **Given** a non-USD currency, **when** converted, **then** the rate and date used match the view's rule.
- **Given** malformed column names, **when** the SQL runs, **then** every affected column is read correctly and listed.
- **Given** the `source` filter, **when** the story closes, **then** the handling is documented and agreed with CARL-3509.

## Test plan

- Row-count and sum reconciliation by day, by account and by currency.
- Boundary tests: lines starting or ending on a month boundary, zero-day lines, lines with changes.
- Re-run test: results are stable when run twice on the same input.
- Peer review of the SQL.

## Dependencies and risks

- CARL-3509 may rename or retype columns, which would break this SQL; coordinate the change.
- Rebuilding in DF creates a second copy of line-day logic next to the one Op1 Silver will need. Record it to prevent drift.
- Operative refreshes every 30 minutes between 06:00 and 22:00 ET; confirm the 08:00 ET job reads a consistent snapshot.

## Open questions

- Which pacing view does the logic use, and where does it live?
- Is the feed WBD-only by contract?
