# FF-08 — Repoint `OPERATIVE_SALES_ORDER_CUSTOM_FIELD_V` to `operative_bronze`

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Story |
| Suggested owner | DF team |
| Size / Wave | M / 1 |
| Suggested priority | High. This is the only object with a prod CARL table today. |
| Depends on | FF-01; CARL-3509 outcome |
| Related Jira | CARL-744, CARL-3509, CARL-2888 |
| Labels | `financial-forecasting`, `df-team`, `operative`, `repoint` |

## User story

As a **DF data engineer**, I want **the Operative sales-order custom-field lookup read from `operative_bronze`** so that **this input comes from a governed prod table and is typed and mapped explicitly**.

## Context

`operative_bronze.sales_order_custom_field` and `sales_order_line_item_custom_field` exist in all four environments, refreshed every 30 minutes between 06:00 and 22:00 ET. CARL-3509 documents that every business column is a `string`, 15 columns across 9 tables have malformed names, and only `discount_profiles` has a `source` column. Existing CARL field-mapping work shows custom-field values selected by `custom_field_id` (for example deal type from IDs 41 and 214).

## Scope

1. Map the view's output columns to the two Bronze tables using FF-01.
2. Reproduce the view's filters and the `custom_field_id` logic, with explicit `TRY_CAST` for numeric and date fields.
3. Handle the missing `source` column: drop the `WHERE source = 'WBD'` filter only after CARL-3509 confirms the feed is WBD-only; otherwise record the risk.
4. Run in dev and QA, then prod behind a switch until FF-14 signs off.
5. Document the casting rules and any custom-field IDs in scope.

## Out of scope

Fixing the Bronze naming or typing (CARL-3509), and Operative Silver (CARL-2888).

## Acceptance criteria

- **Given** the view's key set, **when** the repointed lookup runs, **then** every key and custom-field value matches the share view for the comparison window.
- **Given** numeric and date custom fields, **when** values cannot be cast, **then** they are counted and surfaced, not dropped silently.
- **Given** the `source` question, **when** the story closes, **then** the decision and its evidence are recorded.
- **Given** dev, QA and prod, **when** the read is run, **then** results and shape are the same or differences are explained.
- **Given** FF-14, **when** it runs, **then** this lookup passes the agreed tolerances.

## Test plan

- Structure, volume and value tests.
- Negative test: insert a malformed numeric string in a test copy and confirm it is reported.
- Compare custom-field value distributions by `custom_field_id` on both sides.

## Dependencies and risks

- If CARL-3509 renames columns later, this read breaks. Pin a column-name contract, or read through a view that survives the rename.
- Bronze strings can hide wrong comparisons (`'80' >= '9'`); casting must be explicit.

## Open questions

- Which `custom_field_id` values does the view use today?
- Is the Operative feed contractually WBD-only?
