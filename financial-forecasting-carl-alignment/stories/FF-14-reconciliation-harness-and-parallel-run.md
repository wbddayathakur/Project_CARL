# FF-14 — Reconciliation harness and parallel run: Gerry-side share vs CARL

| Field | Value |
|---|---|
| Epic | Financial Forecasting — CARL Source Alignment |
| Type | Story |
| Suggested owner | DF team |
| Size / Wave | M / 1 |
| Suggested priority | High |
| Depends on | FF-01 |
| Related Jira | CARL-746, CARL-2887, AI-087 (decoupling) |
| Labels | `financial-forecasting`, `df-team`, `testing`, `reconciliation` |

## User story

As a **Finance forecasting owner**, I want **an automated comparison between the current share-based inputs and the CARL-based inputs** so that **we can prove the forecast still reconciles when sources are repointed, and show why numbers differ when they do not**.

## Context

The forecast reads FreeWheel through the Gerry-side share rather than CARL `freewheel_bronze`, so its numbers may not reconcile with other CARL FreeWheel reporting. FreeWheel retains only 7 days at source (per the roadmap), and the daily job rebuilds the last 7 activity dates, so late-arriving corrections need explicit proof.

## Scope

1. Define the comparison grain and measures per repointed object, from the FF-01 mapping.
2. Propose tolerances per measure (for example exact for keys and counts, a stated percentage for money and impressions) and get Finance sign-off.
3. Build repeatable queries or notebooks that compare old vs new by day, by key dimensions and by the last 7 activity dates.
4. Run in parallel for a defined window (suggest at least two full weeks) and record results.
5. For each variance, classify the cause: timing, filter, logic, source difference or defect.
6. Produce a summary table that is attached to Jira and updated per run.

## Out of scope

Changing the production pipeline to read CARL (that happens in the repoint stories after sign-off).

## Acceptance criteria

- **Given** a repointed object, **when** the harness runs, **then** it outputs row counts, key coverage and measure totals for both sides per day.
- **Given** an agreed tolerance, **when** a measure exceeds it, **then** the run is marked failed and lists the contributing keys.
- **Given** the last 7 activity dates, **when** a late correction is applied at source, **then** the harness shows whether CARL Bronze reflects it.
- **Given** the parallel-run window, **when** it ends, **then** a Finance sign-off or a documented exception list is attached.
- **Given** variances, **when** they are reviewed, **then** each has a cause class and an owner.

## Test plan

- Seed test: run the harness against identical data and confirm zero variance.
- Break test: alter one key in a copy and confirm detection.
- Review the tolerances with Finance before the parallel run starts.

## Dependencies and risks

- Needs CARL read access in dev and QA; prod comparison needs FF-09.
- If CARL Bronze history is shorter than the comparison window, the run is limited to what exists.

## Open questions

- Which tolerances will Finance accept?
- Is there a Finance-owned control total to reconcile against, beyond the share?
