# FF-10 — Plan and implement governed reference data for the Looker Excel snapshot maps (`EXCEL_SHEETS_V`)

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Story |
| Suggested owner | Gerry (owns the maps) with a DF engineer |
| Size / Wave | M / 2 |
| Suggested priority | Medium to High: uncontrolled spreadsheet inputs in a Finance forecast |
| Depends on | FF-01 |
| Related Jira | None found |
| Labels | `financial-forecasting`, `reference-data`, `governance` |

## User story

As a **Finance forecasting owner**, I want **the Looker Excel snapshot maps behind `EXCEL_SHEETS_V` turned into governed reference data** so that **spreadsheet edits no longer change the forecast without review**.

## Context

Gerry owns the Looker Excel snapshot maps and, per Kaustuva, can help only with the plan to make them governed reference data. No governed source exists in CARL. Which Excel sheets feed the forecast, and how often they change, is not documented in the thread.

## Scope

1. List every sheet and column that `EXCEL_SHEETS_V` exposes and which pipeline step reads each.
2. Record owner, change frequency and last change per sheet.
3. Agree the target form: a governed table with a load process, version history and review step, or retirement of sheets that are no longer needed.
4. Implement the target for sheets that are kept, in dev and QA.
5. Add an unmapped-value check and a change log.

## Out of scope

Replatforming Looker; the other three DF-owned maps (FF-11).

## Acceptance criteria

- **Given** `EXCEL_SHEETS_V`, **when** the inventory is done, **then** every sheet in use has an owner and change frequency.
- **Given** a kept sheet, **when** it is loaded, **then** it lands in a governed table with version history.
- **Given** a change to a sheet, **when** it is published, **then** a review record exists before it reaches the pipeline.
- **Given** an unused sheet, **when** the review is complete, **then** it is retired or marked unused.
- **Given** the pipeline run, **when** a value has no map row, **then** it is reported.

## Test plan

- Compare table contents with the original sheets for the current snapshot.
- Change test: make a controlled edit and confirm the review and version trail.
- Unmapped-value test.

## Dependencies and risks

- Depends on Gerry's time and willingness to own the plan.
- Sheets edited by hand carry operational risk until the process is enforced.

## Open questions

- Which sheets are actually used by the forecast?
- Who approves changes: Finance, Ad Sales Ops or DF?
