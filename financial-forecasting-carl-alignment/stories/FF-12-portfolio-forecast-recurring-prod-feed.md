# FF-12 — Decide and design a recurring prod feed for `VW_PORTFOLIO_FORECASTING_FORECAST`

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Spike |
| Suggested owner | Ankit Gajiwala (decision); DF engineer (design) |
| Size / Wave | S / 0 |
| Suggested priority | Medium; becomes High if Portfolio Forecasting is in the Finance forecast |
| Depends on | None |
| Related Jira | None found |
| Labels | `financial-forecasting`, `portfolio-forecasting`, `decision` |

## User story

As a **Finance forecasting owner**, I want **a decision on whether the ML portfolio forecast gets a recurring prod feed, and a design if yes** so that **the pipeline does not depend on a one-time dump**.

## Context

`VW_PORTFOLIO_FORECASTING_FORECAST` (the ML forecast) was loaded once into `cmp_test` and has no recurring prod feed. Kaustuva is unsure of the plan and pointed the question to Ankit; he can speak only to the finance forecast part. This is the only source object with no recurring delivery of any kind.

## Scope

1. Get Ankit's decision: recurring prod feed yes or no, owner, target date.
2. If yes, document the target: delivery path, cadence, destination, schema, owner, SLA.
3. If no, record the reason and what consumers should do instead.
4. Record the answer in the epic and update the FF-01 mapping.

## Out of scope

Building the feed (open a separate story once the design is approved), and any change to the ML model.

## Acceptance criteria

- **Given** Ankit's reply, **when** it is recorded, **then** the ticket states yes or no, owner and date.
- **Given** a "yes", **when** the design is written, **then** it names source, destination, cadence, schema, owner and failure handling.
- **Given** a "no", **when** the outcome is recorded, **then** the dependency on the dump is flagged as an accepted risk with an owner.
- **Given** the outcome, **when** the epic is next reviewed, **then** the object's disposition in FF-01 is updated.

## Test plan

- Review of the design by the DF lead and the model owner.
- For a "yes", a follow-up build story carries its own tests; this spike only needs the review sign-off.

## Dependencies and risks

- Depends on Ankit's availability. Without an answer the forecast keeps reading stale data.

## Open questions

- Is Portfolio Forecasting inside the Finance forecast, or a separate consumer of the same dump?
