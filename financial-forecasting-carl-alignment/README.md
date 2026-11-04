# Financial Forecasting — CARL Alignment Pack

Prepared 21 Oct 2026 for Daya Thakur, from the thread *"Financial Forecasting: what's in CARL Iceberg/Cube and open questions"* (16–20 Oct) and Daya's follow-up (data pull to be done by Kaustuva's team, no dependency on the CARL team, everything tracked in Jira with proper testing).

## Files

| File | What it is |
|---|---|
| [01-carl-iceberg-cube-inventory-and-gaps.md](01-carl-iceberg-cube-inventory-and-gaps.md) | What exists in CARL Iceberg and Cube today, mapped object by object to the 11 Financial Forecasting sources, plus what is missing |
| [02-existing-jira-epics-and-overlap.md](02-existing-jira-epics-and-overlap.md) | The epics and stories already in Jira that touch this work, and where a new epic is needed |
| [03-proposed-epic-and-story-map.md](03-proposed-epic-and-story-map.md) | The proposed epic, 17 stories, waves, dependencies, Definition of Done and test approach |
| [stories/](stories/) | One drafted user story per file (`FF-01` … `FF-17`), ready to paste into Jira |

## The short version

1. **The Financial Forecasting pipeline does not read from CARL Iceberg or Cube today.** DF's Iceberg tables are Snowflake-managed in DF's own S3 buckets (confirmed by Kaustuva, 20 Oct). QuickSight reads the two Gold views directly.
2. **Of the 11 source objects: 1 has a prod CARL table (Bronze), 5 have Bronze candidates in dev only, 1 is unconfirmed (API placements), and 4 have no CARL table** (including `OM_CON_DY_V`, whose inputs do exist in prod Bronze). See file 01 for the split.
3. **FreeWheel is dev-only in Glue.** `freewheel_bronze` has 0 tables in prod Glue (79 in dev on 7 Oct). Prod S3 landing exists but is not registered in the prod catalog.
4. **There is no Silver/Gold/Cube for FreeWheel revenue or Operative line-day data.** FreeWheel Silver Phase 1 is impression-grain; Operative One Silver (CARL-2888) is To Do.
5. **No existing Jira epic covers this pipeline.** CARL-1364 and CARL-1479 are the Finance *pacing/EPM-feed* workstream, not the DF capacity-forecast pipeline. A new epic is proposed.

## Nothing here has been created in Jira

All epics and stories are **drafts** in Markdown. Story IDs `FF-xx` are placeholders. No tickets were created or edited.

## Evidence base and its limits

| Source | As of |
|---|---|
| Glue catalog snapshots in `iceberg-catalog-agent/out/` (all four environments, 1,128 tables) | 24 Sep 2026 |
| Glue live pull, dev and prod only (QA and stage not included) | 7 Oct 2026 |
| Cube model registry and `CARL_Cube_Semantic_Layer_Data_Inventory.xlsx` | 7 Oct 2026 (Cube `/meta` was not reachable) |
| Jira (project CARL) and Confluence (FreeWheel Silver Phase 1 design) | read live 21 Oct 2026 |
| Kaustuva Hota's answers | email of 20 Oct 2026 |

Glue state may have moved since 7 Oct. Re-run `iceberg-catalog-agent` before using any table count as a commitment.

## Open questions that block or shape stories

| # | Question | Who | Affects |
|---|---|---|---|
| Q1 | Is prod (`DIGIREV_PROD`) set up the same way as `DIGIREV_DEV`? Kaustuva answered the schedule part of question 6 but not this part. | Kaustuva Hota | FF-15 |
| Q2 | Plan to move `VW_PORTFOLIO_FORECASTING_FORECAST` from one-time dump to a recurring prod feed | Ankit Gajiwala | FF-12 |
| Q3 | Priority of loading the missing data into CARL (the request to Rohini on 16 Oct is unanswered in the thread) | Rohini Vugumudi | FF-05, FF-07, FF-17 |
| Q4 | Which FreeWheel and Operative objects have a CARL equivalent? Kaustuva is unsure; his source was the Looker logic and Gerry. Needs FF-01 to settle. | Kaustuva Hota, Gerry | FF-01 |
| Q5 | Is "Financial Forecasting" in this thread the DF capacity forecast (`CAPACITY_FORECAST_FINANCE_ENT`), distinct from the CARL-1364 pacing dashboard? The material suggests yes; please confirm. | Daya Thakur | Epic scope |
| Q6 | Who owns the Snowflake-managed DF Iceberg tables' visibility in Glue, and is it wanted at all? | Daya, Debarghyo | FF-13 |
| Q7 | Is Financial Forecasting data in SOX scope? CARL-1479 flags the EPM feed as "Highly Sensitive / SOX". | Finance, Daya | All stories (access and evidence) |
