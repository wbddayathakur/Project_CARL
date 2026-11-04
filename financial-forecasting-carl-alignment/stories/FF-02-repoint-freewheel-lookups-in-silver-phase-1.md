# FF-02 — Repoint FreeWheel lookups already in Silver Phase 1

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Story |
| Suggested owner | DF team |
| Size / Wave | M / 1 |
| Suggested priority | High |
| Depends on | FF-01; FF-09 for prod |
| Related Jira | CARL-2887, CARL-3803, CARL-3804, CARL-3805, CARL-3807, CARL-3808, CARL-1380 |
| Labels | `financial-forecasting`, `df-team`, `freewheel`, `repoint` |

## User story

As a **DF data engineer**, I want **the FreeWheel lookups that CARL Silver already provides to be read from CARL instead of the share** so that **those inputs are governed and reconcile with other CARL FreeWheel reporting**.

## Context

FreeWheel Silver Phase 1 provides `dim_video`, `dim_video_series`, `dim_placement`, `dim_site` and `dim_site_section`, plus 14 other dimensions. They are in dev and mostly Ready for Testing (CARL-3803 to CARL-3808); they are not in prod Glue. Candidate matches: object 5 `VIDEO_ASSET_MASTER_V` (partly), object 7 `API_PLACEMENTS_V` (log-based only; API source unconfirmed), objects 2 and 4 (site attributes only; the group mapping is Bronze only, see FF-03).

## Scope

1. Take the objects and columns that FF-01 marks **Repoint** and are served by Silver Phase 1.
2. Change the pipeline reads for those objects in dev, then QA.
3. Handle gaps: columns Silver lacks (for example `d_video` rating and air_date, pending CARL-4222).
4. Keep the old share read behind a switch until FF-14 signs off.
5. Document each repointed object and the columns that changed.

## Out of scope

Site-group, video-group and listings lookups (FF-03); the sellable fact (FF-04, FF-05); prod cutover (needs FF-09 and FF-15).

## Acceptance criteria

- **Given** a repointed lookup, **when** the pipeline runs in dev and QA, **then** it reads from `freewheel_silver` and produces the same keys as before.
- **Given** a column that Silver lacks, **when** it is needed downstream, **then** the gap is listed and either handled or raised against CARL-2887.
- **Given** the switch, **when** it is flipped back, **then** the pipeline reads the share with no code change.
- **Given** FF-14, **when** its harness runs, **then** the repointed lookups pass the agreed tolerances.
- **Given** the ticket, **when** it closes, **then** test evidence and a mapping update are attached.

## Test plan

- Structure, volume and value tests from the [standard approach](../03-proposed-epic-and-story-map.md).
- Key-coverage test: every key used by the fact exists in the repointed lookup.
- Regression: `CAPACITY_HISTORY_FINANCE` unchanged within tolerance after the repoint.

## Dependencies and risks

- Silver is dev only until FF-09; prod stays on the share until then.
- Silver Phase 1 follows the `user_ad_stream_base` reference and covers one network (191701); confirm that covers the forecast.
- Table definitions may still change while stories are Ready for Testing.

## Open questions

- Does the forecast need the other two networks that the reference covers?
