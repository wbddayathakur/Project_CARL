# FF-06 — Provide `FW_VIDTYPE_MAP` as governed reference data

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Story |
| Suggested owner | DF team |
| Size / Wave | S / 2 |
| Suggested priority | Medium |
| Depends on | FF-01 |
| Related Jira | CARL-3807 (`dim_video`), CARL-4222 |
| Labels | `financial-forecasting`, `df-team`, `reference-data`, `freewheel` |

## User story

As a **DF data engineer**, I want **`FW_VIDTYPE_MAP` available as governed reference data** so that **the video-type classification used by the forecast is documented, versioned and reproducible outside the share**.

## Context

No CARL table for `FW_VIDTYPE_MAP` was found. Its origin and rules are unknown in the thread. It classifies video assets into types, and `dim_video` in Silver does not carry the same classification (Phase 1 follows the reference and adds rating and air_date in CARL-4222).

## Scope

1. Extract the map's content, key, owner and current derivation (hand-maintained, rule-based or derived from FreeWheel attributes).
2. If derivable from `dim_video` attributes, document the rule and reproduce it. If hand-maintained, make it a governed table as in FF-11.
3. Add a check that every video in the fact has a type.
4. Record the disposition in the FF-01 mapping.

## Out of scope

Changing the classification itself; adding it to FreeWheel Silver.

## Acceptance criteria

- **Given** the map, **when** the story is done, **then** its owner, key, columns and derivation are documented.
- **Given** the fact's video assets, **when** the map is applied, **then** the share of untyped videos is reported and agreed.
- **Given** a change to the map, **when** it is published, **then** it is versioned with a review record.
- **Given** the reproduced map, **when** compared to the share's `FW_VIDTYPE_MAP`, **then** it matches or each difference is explained.

## Test plan

- Compare contents with the share side by side.
- Coverage test on the video keys in the fact for the last 30 days.
- Review sign-off by the owner.

## Dependencies and risks

- If the map is derived from enriched third-party fields, reproducing it depends on the decoupling work.

## Open questions

- Who maintains `FW_VIDTYPE_MAP` today, and how is it built?
