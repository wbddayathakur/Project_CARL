# FF-01 — Column-level reconciliation of the 11 source objects against CARL

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Spike |
| Suggested owner | DF team (Venkatesh D, or the person Debarghyo Sengupta assigns) |
| Size / Wave | S / 0 |
| Suggested priority | Highest. Every other story depends on it. |
| Depends on | None |
| Related Jira | CARL-746, CARL-744, CARL-1380, CARL-2887, CARL-3509 |
| Labels | `financial-forecasting`, `df-team`, `spike` |

## User story

As a **DF data engineer on the Financial Forecasting pipeline**, I want **each of the 11 source objects compared column by column to its candidate CARL table** so that **we know exactly which objects can be repointed, which need a build and which have no CARL equivalent, instead of relying on name matching**.

## Context

The 16–20 Oct thread matched objects to CARL tables by name. Kaustuva was unsure which FreeWheel and Operative objects have a CARL equivalent; his table details came from the Looker logic and Gerry. Candidates are listed in [file 01](../01-carl-iceberg-cube-inventory-and-gaps.md). Several candidates are dev only or Bronze only.

## Scope

1. For each of objects 1–11, extract the current column list, types, grain and filters from the Snowflake share view definition.
2. Compare to the candidate CARL tables: `freewheel_bronze`, `freewheel_silver`, `operative_bronze`, and the FreeWheel API Bronze (CARL-1380) for object 7.
3. Record per object: grain match, column coverage (matched, derivable, missing), type differences, filter or business logic embedded in the view, and environment availability (dev, QA, prod).
4. Assign each object one disposition: **Repoint**, **Rebuild**, **Govern as reference data**, or **Retain with reason**.
5. Record the answer to "which FreeWheel and Operative objects have a CARL equivalent" and send it to Daya, Kaustuva and Hong Zhang.
6. Open or link follow-up stories for any object whose disposition changes from the draft.

## Out of scope

Building or repointing anything. This story only produces the mapping and the dispositions.

## Acceptance criteria

- **Given** the 11 source objects, **when** the mapping is complete, **then** each has a documented disposition, a candidate CARL table (or "none") and a column coverage count.
- **Given** an object with a candidate, **when** columns differ, **then** every unmatched column is listed with a proposed handling (derive, drop, request).
- **Given** each candidate table, **when** availability is checked, **then** dev, QA and prod presence is stated with the date checked.
- **Given** object 7 (`API_PLACEMENTS_V`), **when** the mapping is complete, **then** the source feed (log Bronze or API Bronze) is stated.
- **Given** the finished mapping, **when** it is reviewed by Kaustuva and Hong Zhang, **then** disagreements are resolved or logged as open questions.

## Test plan

- Peer review of the mapping by a second DF engineer.
- Spot-check three objects by running the same sample query on both sides for one date and comparing keys and values.
- Attach the mapping document and the sample queries to the ticket.

## Dependencies and risks

- Needs read access to the share views and to CARL Glue/Athena in dev and QA.
- QA and stage were not covered in the 7 Oct Glue pull; refresh before concluding.

## Open questions

- Is the intended FreeWheel source the log Bronze (`d_*`, `v4_logs`) or API Bronze for object 7?
- Does Gerry hold the logic behind `FW_REV_VIDEOASSET_DY_SELLABLE_V` in a form that can be read?
