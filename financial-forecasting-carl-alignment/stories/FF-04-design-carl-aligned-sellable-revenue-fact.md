# FF-04 — Design the CARL-aligned equivalent of `FW_REV_VIDEOASSET_DY_SELLABLE_V`

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Design spike |
| Suggested owner | DF team, with Hong Zhang consulted |
| Size / Wave | M / 2 |
| Suggested priority | High. This is the main fact. |
| Depends on | FF-01, FF-03 |
| Related Jira | CARL-2887, CARL-3809, CARL-1380, AI-087 |
| Labels | `financial-forecasting`, `design`, `freewheel`, `revenue` |

## User story

As a **Finance forecasting owner**, I want **a documented design for a CARL-aligned revenue-by-video-asset-by-day "sellable" table** so that **we can choose between rebuilding it in CARL and keeping the Gerry-side source, based on facts**.

## Context

`FW_REV_VIDEOASSET_DY_SELLABLE_V` is the main fact. It is Gerry-side curated and was marked informational only in the earlier DF one-time dump. CARL has no equivalent: FreeWheel Silver Phase 1 `fact_ad_stream_impression` is impression grain built from `v4_logs` and does not carry revenue, video-asset-by-day grain or the sellable logic. FreeWheel decoupling from the third-party enriched data has no date (AI-087, behind pace).

## Scope

1. Document the view's grain, columns, filters and sellable rule, and every upstream it uses, using the share definition and the Looker logic.
2. Identify which parts can be derived from CARL (Silver Phase 1, Bronze, `operative_bronze`) and which depend on enriched third-party fields.
3. Propose the target: table name, layer, grain, keys, load method, history and refresh timing, aligned with the FreeWheel Silver processing rules.
4. Compare options: (a) build in CARL Silver/Gold, (b) keep the share and add reconciliation only, (c) hybrid.
5. State the effort, dependencies and risks. Get a decision from Daya, Debarghyo and Rohini, who was asked to prioritise.

## Out of scope

Building the table (FF-05) and the decoupling programme.

## Acceptance criteria

- **Given** the view, **when** the design is written, **then** grain, keys, columns, filters and the sellable rule are documented and reviewed by Gerry or the view owner.
- **Given** each column, **when** mapped, **then** it is marked derivable from CARL, not derivable, or needs the enriched feed.
- **Given** the options, **when** the design is presented, **then** each has effort, dependencies and risk, and a recommendation.
- **Given** the decision, **when** it is made, **then** it is on the ticket, and FF-05 is confirmed, reshaped or closed.

## Test plan

- Review with the view owner.
- Prove the grain by counting distinct keys per day on the share view for a sample week and comparing with the proposed key.
- Reproduce one day's totals from CARL inputs where possible, and record the variance.

## Dependencies and risks

- The enriched third-party data may not be reproducible from CARL Bronze.
- Source retention is 7 days, so history before CARL Bronze began may not be re-creatable.

## Open questions

- Is the sellable rule documented anywhere, or only in the view definition?
- Does Rohini's priority for loading the missing data cover this object?
