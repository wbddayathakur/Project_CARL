# FF-03 — Decide and repoint FreeWheel lookups that are Bronze-only

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Story (decision, then implementation) |
| Suggested owner | DF team, with Hong Zhang consulted |
| Size / Wave | M / 1–2 |
| Suggested priority | High |
| Depends on | FF-01 |
| Related Jira | CARL-2887, CARL-746, CARL-4222 |
| Labels | `financial-forecasting`, `df-team`, `freewheel`, `decision` |

## User story

As a **DF data engineer**, I want **a decision on how to read the FreeWheel site-group, video-group and listings tables that only exist in Bronze** so that **those lookups can be repointed without waiting on work CARL has not planned**.

## Context

The FreeWheel Silver Table Catalog states that 55 of the 77 Bronze tables are not read in Phase 1. Needed ones in that set:

| Source object | Bronze table | Silver |
|---|---|---|
| 2 `VIDEO_AD_SITE_GROUP_V` | `d_site_group`, `d_site_to_site_group` | none |
| 3 `SITE_GROUP_TO_SITE_GROUP_V` | `d_site_group_to_site_group` | none |
| 4 `SITE_SECTION_TO_SITE_GROUP_V` | `d_site_section_to_site_group` | none |
| 5 `VIDEO_ASSET_MASTER_V` (group part) | `d_video_group`, `d_video_to_video_group`, `d_video_group_to_video_group`, `d_video_series_to_video_group` | none |
| 6 `LISTINGS_V` | `d_listings` | none (fact keeps only `listing_id`) |

All are dev only. Bronze tables are raw; Silver rules (full-replace dimensions, `row_hash_silver`) do not apply to them.

## Options

| Option | For | Against |
|---|---|---|
| A. Read Bronze directly | No dependency on CARL | Raw typing and duplicates; no Silver rules; bypasses the shared Silver |
| B. Ask CARL to add them in a Phase 1.1 | One shared definition | Not planned; Silver epic already has no date for prod and five initiatives waiting |
| C. DF team builds the small dimension tables and shares them back | Fits Daya's "DF does the pull" model | Risk of a private Silver, which the roadmap flags as a problem |

## Scope

1. Take the decision with Debarghyo, Kaustuva and Hong Zhang, and record it on the ticket.
2. Implement the chosen option for objects 2, 3, 4, 5 (group part) and 6 in dev and QA.
3. If B is chosen, open a story under CARL-2887 and link it.
4. Keep the share read behind a switch until FF-14 signs off.

## Out of scope

The sellable fact (FF-04, FF-05) and prod cutover (FF-09).

## Acceptance criteria

- **Given** the three options, **when** the decision is made, **then** the chosen option, rationale and owner are on the ticket.
- **Given** the chosen option, **when** the pipeline runs in dev and QA, **then** each of the five lookups returns the same keys as the share view.
- **Given** duplicates in Bronze, **when** the lookup is read, **then** the latest version per key is selected and the rule is documented.
- **Given** FF-14, **when** it runs, **then** these lookups pass the agreed tolerances.

## Test plan

- Structure, volume and key-coverage tests.
- Uniqueness test per lookup key.
- Hierarchy test: site-group-to-site-group and video-group chains have no cycles and no orphans.

## Dependencies and risks

- FreeWheel Silver is the declared shared definition; option C creates a private copy.
- Dev-only until FF-09.

## Open questions

- Does the forecast need the full group hierarchy, or only the top-level group?
