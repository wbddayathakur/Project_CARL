# CARL data-readiness report (PoC)

Every number below is computed from real inputs. Nothing is simulated. Where the inputs cannot answer a question, the report says **UNVERIFIED**.

## 1. Inputs and how fresh they are

| Input | As of | Age today | What it is |
|---|---|---|---|
| Glue catalog inventory (dev + prod) | 2026-10-07 | 15 days old | 1489 tables, live Glue export |
| Prod load history | 2026-10-13 | 9 days old | Iceberg snapshot history for 291 prod tables (0 not in the inventory) |
| Jira (CARL project) | 2026-10-22 | 0 days old | 250 stories: children of the ingestion epics plus all Blocked |

QA and stage accounts are **not** in the catalog export, so readiness here is dev-versus-prod only.

## 2. What the evidence says (ranked by count)

1. 421 tables across 21 source/layer groups exist only in dev, with nothing in prod. Largest: CARL DWH (legacy gold) gold (150); Venus silver (80); FreeWheel bronze (79); usaffdwh silver (28); NEO bronze (12).
2. 56 prod tables have exactly one retained snapshot older than 14 days, so no recurring load is evidenced. By source: iDeal (Oracle) (56).
3. 29 stories are in Ready for Testing / In Testing / UAT / In Review with no matching table in the catalog (e.g. CARL-1382, CARL-1383, CARL-1384, CARL-1386, CARL-1389, CARL-1390). All were touched after the 2026-10-07 snapshot, so the tables may simply post-date the catalog export. Refresh the catalog before treating these as gaps.
4. 18 Done stories were resolved after the catalog snapshot, so they cannot be judged until the catalog is refreshed.
5. 8 stories are still open although a matching table is already in prod (7 of them Blocked: CARL-696, CARL-698, CARL-705, CARL-1469, CARL-1470, CARL-1472, CARL-2803). The ticket status is stale, or the table is live but unaccepted. Either way reporting on Jira status misstates the lake.
6. 3 stories were Done before the catalog snapshot but no matching table exists: CARL-242, CARL-280, CARL-295. 2 of them have a near-identical table name in the catalog (likely a rename), so they are naming drift rather than missing data; the rest need an owner to confirm.

## 3. Readiness by source and layer

`Stage` is derived only from the catalog. Quality is **unverified** for every row because no data-quality, schema-contract or parity results exist in any input (see section 6).

| Source | Layer | Tables | In dev | In prod | Stage | Flags | Jira-requested tables found in dev / prod |
|---|---|---:|---:|---:|---|---|---|
| CARL DWH (legacy gold) | gold | 150 | 150 | 0 | dev only | - | - |
| DDL Forecasting | bronze | 1 | 1 | 1 | in prod | - | - |
| DDL Forecasting | silver | 1 | 1 | 1 | in prod | - | - |
| FreeWheel | bronze | 79 | 79 | 0 | dev only | - | 0 / 0 of 98 |
| FreeWheel | silver | 0 | 0 | 0 | not present | - | 0 / 0 of 18 |
| International | bronze | 5 | 5 | 0 | dev only | - | - |
| International | silver | 7 | 7 | 0 | dev only | - | - |
| International | gold | 7 | 7 | 0 | dev only | - | - |
| LDR modelled (dim/fact) | silver | 17 | 17 | 7 | partly in prod | 1 stale in prod | 5 / 5 of 12 |
| LDR modelled (dim/fact) | gold | 17 | 17 | 11 | partly in prod | 2 stale in prod | 2 / 2 of 7 |
| LDR other | bronze | 12 | 12 | 7 | partly in prod | 1 stale in prod | - |
| LDR other | silver | 9 | 9 | 3 | partly in prod | - | - |
| LDR other | gold | 12 | 12 | 9 | partly in prod | 5 stale in prod | - |
| Linear Forecasting | bronze | 1 | 1 | 0 | dev only | - | - |
| Linear Forecasting | silver | 6 | 6 | 0 | dev only | - | - |
| Linear Forecasting | gold | 1 | 1 | 0 | dev only | - | - |
| Market Share (Ad Intel) | bronze | 10 | 10 | 10 | in prod | - | - |
| NEO | bronze | 12 | 12 | 0 | dev only | - | - |
| NEO | silver | 7 | 7 | 0 | dev only | - | - |
| NEO | gold | 7 | 7 | 0 | dev only | - | - |
| Nielsen Big MIT | bronze | 8 | 8 | 8 | in prod | - | - |
| Nielsen NRLD | bronze | 12 | 12 | 0 | dev only | - | - |
| Operative | bronze | 89 | 81 | 89 | in prod | 1 stale in prod | - |
| QuickSight usage | bronze | 5 | 5 | 5 | in prod | - | - |
| QuickSight usage | silver | 4 | 4 | 4 | in prod | - | - |
| QuickSight usage | gold | 1 | 1 | 1 | in prod | - | - |
| Salesforce (via Oracle) | bronze | 50 | 50 | 45 | partly in prod | 8 stale in prod | 0 / 0 of 18 |
| Venus | silver | 80 | 80 | 0 | dev only | - | - |
| Venus | gold | 1 | 1 | 0 | dev only | - | - |
| adsales_iceberg | silver | 3 | 3 | 0 | dev only | - | - |
| carl_inflight | bronze | 1 | 1 | 0 | dev only | - | - |
| global_channel_insights | bronze | 1 | 1 | 1 | in prod | 1 stale in prod | - |
| global_channel_insights | silver | 1 | 1 | 1 | in prod | 1 stale in prod | - |
| h18 | gold | 1 | 1 | 0 | dev only | - | - |
| h18_silver_new | silver | 5 | 5 | 0 | dev only | - | - |
| iDeal (Oracle) | bronze | 392 | 392 | 129 | partly in prod | 13 stale in prod; 129 with no recurring-load evidence | 21 / 11 of 22 |
| iDeal (Oracle) | silver | 192 | 191 | 149 | partly in prod | 48 stale in prod; 149 with no recurring-load evidence | - |
| impact | bronze | 3 | 3 | 0 | dev only | - | - |
| ump_linear_de | silver | 5 | 5 | 0 | dev only | - | - |
| unmapped | silver | 0 | 0 | 0 | not present | - | 0 / 0 of 1 |
| usaffdwh | silver | 28 | 28 | 0 | dev only | - | - |

Excluded from scoring: 178 sandbox database; 13 no medallion layer (raw/audit/unknown); 55 test/tmp-looking table name. Rules are in `config/rubric.json`.

### Criterion detail

**CARL DWH (legacy gold) / gold**: dev only

- G1 Exists in dev: **PASS** (150 of 150 tables in dev)
- G2 Promoted to prod: **FAIL** (0 of 150 tables in prod)
- G3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- G4 Business definition documented and owned: **UNVERIFIED** (no evidence source)
- G5 Parity with legacy output verified: **UNVERIFIED** (no evidence source)
- G6 A golden / eval dataset exists for it: **UNVERIFIED** (no evidence source)

**DDL Forecasting / bronze**: in prod

- B1 Landed in dev: **PASS** (1 of 1 tables in dev)
- B2 Promoted to prod: **PASS** (1 of 1 tables in prod)
- B3 Updated in prod within the freshness window: **PASS** (1 of 1 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 1 prod tables)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**DDL Forecasting / silver**: in prod

- S1 Exists in dev: **PASS** (1 of 1 tables in dev)
- S2 Promoted to prod: **PASS** (1 of 1 tables in prod)
- S3 Updated in prod within the freshness window: **PASS** (1 of 1 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 1 prod tables)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**FreeWheel / bronze**: dev only

- B1 Landed in dev: **PASS** (79 of 79 tables in dev)
- B2 Promoted to prod: **FAIL** (0 of 79 tables in prod)
- B3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**International / bronze**: dev only

- B1 Landed in dev: **PASS** (5 of 5 tables in dev)
- B2 Promoted to prod: **FAIL** (0 of 5 tables in prod)
- B3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**International / silver**: dev only

- S1 Exists in dev: **PASS** (7 of 7 tables in dev)
- S2 Promoted to prod: **FAIL** (0 of 7 tables in prod)
- S3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**International / gold**: dev only

- G1 Exists in dev: **PASS** (7 of 7 tables in dev)
- G2 Promoted to prod: **FAIL** (0 of 7 tables in prod)
- G3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- G4 Business definition documented and owned: **UNVERIFIED** (no evidence source)
- G5 Parity with legacy output verified: **UNVERIFIED** (no evidence source)
- G6 A golden / eval dataset exists for it: **UNVERIFIED** (no evidence source)

**LDR modelled (dim/fact) / silver**: partly in prod

- S1 Exists in dev: **PASS** (17 of 17 tables in dev)
- S2 Promoted to prod: **PARTIAL** (7 of 17 tables in prod)
- S3 Updated in prod within the freshness window: **PARTIAL** (6 of 7 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 7 prod tables)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**LDR modelled (dim/fact) / gold**: partly in prod

- G1 Exists in dev: **PASS** (17 of 17 tables in dev)
- G2 Promoted to prod: **PARTIAL** (11 of 17 tables in prod)
- G3 Updated in prod within the freshness window: **PARTIAL** (9 of 11 prod tables updated within 14d of the catalog snapshot)
- G4 Business definition documented and owned: **UNVERIFIED** (no evidence source)
- G5 Parity with legacy output verified: **UNVERIFIED** (no evidence source)
- G6 A golden / eval dataset exists for it: **UNVERIFIED** (no evidence source)

**LDR other / bronze**: partly in prod

- B1 Landed in dev: **PASS** (12 of 12 tables in dev)
- B2 Promoted to prod: **PARTIAL** (7 of 12 tables in prod)
- B3 Updated in prod within the freshness window: **PARTIAL** (6 of 7 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 7 prod tables)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**LDR other / silver**: partly in prod

- S1 Exists in dev: **PASS** (9 of 9 tables in dev)
- S2 Promoted to prod: **PARTIAL** (3 of 9 tables in prod)
- S3 Updated in prod within the freshness window: **PASS** (3 of 3 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 3 prod tables)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**LDR other / gold**: partly in prod

- G1 Exists in dev: **PASS** (12 of 12 tables in dev)
- G2 Promoted to prod: **PARTIAL** (9 of 12 tables in prod)
- G3 Updated in prod within the freshness window: **PARTIAL** (4 of 9 prod tables updated within 14d of the catalog snapshot)
- G4 Business definition documented and owned: **UNVERIFIED** (no evidence source)
- G5 Parity with legacy output verified: **UNVERIFIED** (no evidence source)
- G6 A golden / eval dataset exists for it: **UNVERIFIED** (no evidence source)

**Linear Forecasting / bronze**: dev only

- B1 Landed in dev: **PASS** (1 of 1 tables in dev)
- B2 Promoted to prod: **FAIL** (0 of 1 tables in prod)
- B3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**Linear Forecasting / silver**: dev only

- S1 Exists in dev: **PASS** (6 of 6 tables in dev)
- S2 Promoted to prod: **FAIL** (0 of 6 tables in prod)
- S3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**Linear Forecasting / gold**: dev only

- G1 Exists in dev: **PASS** (1 of 1 tables in dev)
- G2 Promoted to prod: **FAIL** (0 of 1 tables in prod)
- G3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- G4 Business definition documented and owned: **UNVERIFIED** (no evidence source)
- G5 Parity with legacy output verified: **UNVERIFIED** (no evidence source)
- G6 A golden / eval dataset exists for it: **UNVERIFIED** (no evidence source)

**Market Share (Ad Intel) / bronze**: in prod

- B1 Landed in dev: **PASS** (10 of 10 tables in dev)
- B2 Promoted to prod: **PASS** (10 of 10 tables in prod)
- B3 Updated in prod within the freshness window: **PASS** (10 of 10 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 10 prod tables)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**NEO / bronze**: dev only

- B1 Landed in dev: **PASS** (12 of 12 tables in dev)
- B2 Promoted to prod: **FAIL** (0 of 12 tables in prod)
- B3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**NEO / silver**: dev only

- S1 Exists in dev: **PASS** (7 of 7 tables in dev)
- S2 Promoted to prod: **FAIL** (0 of 7 tables in prod)
- S3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**NEO / gold**: dev only

- G1 Exists in dev: **PASS** (7 of 7 tables in dev)
- G2 Promoted to prod: **FAIL** (0 of 7 tables in prod)
- G3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- G4 Business definition documented and owned: **UNVERIFIED** (no evidence source)
- G5 Parity with legacy output verified: **UNVERIFIED** (no evidence source)
- G6 A golden / eval dataset exists for it: **UNVERIFIED** (no evidence source)

**Nielsen Big MIT / bronze**: in prod

- B1 Landed in dev: **PASS** (8 of 8 tables in dev)
- B2 Promoted to prod: **PASS** (8 of 8 tables in prod)
- B3 Updated in prod within the freshness window: **PASS** (8 of 8 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 8 prod tables)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**Nielsen NRLD / bronze**: dev only

- B1 Landed in dev: **PASS** (12 of 12 tables in dev)
- B2 Promoted to prod: **FAIL** (0 of 12 tables in prod)
- B3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**Operative / bronze**: in prod

- B1 Landed in dev: **PARTIAL** (81 of 89 tables in dev)
- B2 Promoted to prod: **PASS** (89 of 89 tables in prod)
- B3 Updated in prod within the freshness window: **PARTIAL** (88 of 89 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 89 prod tables)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**QuickSight usage / bronze**: in prod

- B1 Landed in dev: **PASS** (5 of 5 tables in dev)
- B2 Promoted to prod: **PASS** (5 of 5 tables in prod)
- B3 Updated in prod within the freshness window: **PASS** (5 of 5 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 5 prod tables)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**QuickSight usage / silver**: in prod

- S1 Exists in dev: **PASS** (4 of 4 tables in dev)
- S2 Promoted to prod: **PASS** (4 of 4 tables in prod)
- S3 Updated in prod within the freshness window: **PASS** (4 of 4 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 4 prod tables)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**QuickSight usage / gold**: in prod

- G1 Exists in dev: **PASS** (1 of 1 tables in dev)
- G2 Promoted to prod: **PASS** (1 of 1 tables in prod)
- G3 Updated in prod within the freshness window: **PASS** (1 of 1 prod tables updated within 14d of the catalog snapshot)
- G4 Business definition documented and owned: **UNVERIFIED** (no evidence source)
- G5 Parity with legacy output verified: **UNVERIFIED** (no evidence source)
- G6 A golden / eval dataset exists for it: **UNVERIFIED** (no evidence source)

**Salesforce (via Oracle) / bronze**: partly in prod

- B1 Landed in dev: **PASS** (50 of 50 tables in dev)
- B2 Promoted to prod: **PARTIAL** (45 of 50 tables in prod)
- B3 Updated in prod within the freshness window: **PARTIAL** (37 of 45 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 45 prod tables)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**Venus / silver**: dev only

- S1 Exists in dev: **PASS** (80 of 80 tables in dev)
- S2 Promoted to prod: **FAIL** (0 of 80 tables in prod)
- S3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**Venus / gold**: dev only

- G1 Exists in dev: **PASS** (1 of 1 tables in dev)
- G2 Promoted to prod: **FAIL** (0 of 1 tables in prod)
- G3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- G4 Business definition documented and owned: **UNVERIFIED** (no evidence source)
- G5 Parity with legacy output verified: **UNVERIFIED** (no evidence source)
- G6 A golden / eval dataset exists for it: **UNVERIFIED** (no evidence source)

**adsales_iceberg / silver**: dev only

- S1 Exists in dev: **PASS** (3 of 3 tables in dev)
- S2 Promoted to prod: **FAIL** (0 of 3 tables in prod)
- S3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**carl_inflight / bronze**: dev only

- B1 Landed in dev: **PASS** (1 of 1 tables in dev)
- B2 Promoted to prod: **FAIL** (0 of 1 tables in prod)
- B3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**global_channel_insights / bronze**: in prod

- B1 Landed in dev: **PASS** (1 of 1 tables in dev)
- B2 Promoted to prod: **PASS** (1 of 1 tables in prod)
- B3 Updated in prod within the freshness window: **FAIL** (0 of 1 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 1 prod tables)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**global_channel_insights / silver**: in prod

- S1 Exists in dev: **PASS** (1 of 1 tables in dev)
- S2 Promoted to prod: **PASS** (1 of 1 tables in prod)
- S3 Updated in prod within the freshness window: **FAIL** (0 of 1 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **UNVERIFIED** (no load history for any of the 1 prod tables)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**h18 / gold**: dev only

- G1 Exists in dev: **PASS** (1 of 1 tables in dev)
- G2 Promoted to prod: **FAIL** (0 of 1 tables in prod)
- G3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- G4 Business definition documented and owned: **UNVERIFIED** (no evidence source)
- G5 Parity with legacy output verified: **UNVERIFIED** (no evidence source)
- G6 A golden / eval dataset exists for it: **UNVERIFIED** (no evidence source)

**h18_silver_new / silver**: dev only

- S1 Exists in dev: **PASS** (5 of 5 tables in dev)
- S2 Promoted to prod: **FAIL** (0 of 5 tables in prod)
- S3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**iDeal (Oracle) / bronze**: partly in prod

- B1 Landed in dev: **PASS** (392 of 392 tables in dev)
- B2 Promoted to prod: **PARTIAL** (129 of 392 tables in prod)
- B3 Updated in prod within the freshness window: **PARTIAL** (116 of 129 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **UNVERIFIED** (0 recurring, 127 with a single retained snapshot, history covers 129 of 129 prod tables)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**iDeal (Oracle) / silver**: partly in prod

- S1 Exists in dev: **PARTIAL** (191 of 192 tables in dev)
- S2 Promoted to prod: **PARTIAL** (149 of 192 tables in prod)
- S3 Updated in prod within the freshness window: **PARTIAL** (101 of 149 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **UNVERIFIED** (0 recurring, 149 with a single retained snapshot, history covers 149 of 149 prod tables)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**impact / bronze**: dev only

- B1 Landed in dev: **PASS** (3 of 3 tables in dev)
- B2 Promoted to prod: **FAIL** (0 of 3 tables in prod)
- B3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- B4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- B5 Schema contract enforced (nullability, decimals preserved): **UNVERIFIED** (no evidence source)
- B6 Complete against the source system's table list: **UNVERIFIED** (no evidence source)

**ump_linear_de / silver**: dev only

- S1 Exists in dev: **PASS** (5 of 5 tables in dev)
- S2 Promoted to prod: **FAIL** (0 of 5 tables in prod)
- S3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

**usaffdwh / silver**: dev only

- S1 Exists in dev: **PASS** (28 of 28 tables in dev)
- S2 Promoted to prod: **FAIL** (0 of 28 tables in prod)
- S3 Updated in prod within the freshness window: **n/a** (0 of 0 prod tables updated within 14d of the catalog snapshot)
- S4 Loads recur in prod (not a one-time load): **n/a** (nothing in prod)
- S5 Join integrity verified (match rate, orphan rate): **UNVERIFIED** (no evidence source)
- S6 Data-quality rule results are logged: **UNVERIFIED** (no evidence source)

## 4. Jira versus the catalog

Of 250 stories, 176 name a table and a layer that this PoC could parse; 74 are design, discovery or access tasks with no table name. Of the 176 parsed, **28 matched a catalog table** and 148 did not. The matcher is a naming heuristic, so treat a no-match as a lead to check, not a verdict. Breakdown of the stories with no catalog match: 98 open with no table yet (not started), 29 in testing/UAT with no table in the catalog, 18 Done after the catalog snapshot, 3 Done before the snapshot with no table.

| Reconciliation | Stories |
|---|---:|
| Done in Jira and the table is in prod (consistent) | 10 |
| Done in Jira, but the table is only in dev (promotion gap) | 0 |
| Done in Jira before the catalog snapshot, but no matching table (gap or naming mismatch) | 3 |
| Done in Jira after the catalog snapshot (cannot judge: refresh the catalog) | 18 |
| Table is in prod but the story is still open (stale ticket or unfinished validation) | 8 |
| Table is in dev; story open (consistent) | 10 |
| Story is in testing/UAT but no matching table in the catalog (gap, or created after the snapshot) | 29 |
| Story open and no table yet (consistent: not started) | 98 |

7 stories matched more than one table (suffix match); they are flagged `ambiguous` in the CSV.

### Done in Jira before the catalog snapshot, but no matching table (gap or naming mismatch)

- CARL-242 (Done) SILVER.FACT_PACING_REVENUE_BUDGET_MO transformation/business logic -> no exact match (closest names, hint only: linear_digital_revenue_silver.fact_pacing_revenue_budget_month, linear_digital_revenue_silver.fact_pacing_revenue_budget_month_20260504)
- CARL-280 (Done) GOLD.FACT_PACING_REVENUE_BUDGET_MO  transformation/business logic -> no exact match (closest names, hint only: linear_digital_revenue_gold.fact_pacing_revenue_budget_month, linear_digital_revenue_gold.fact_pacing_revenue_budget_month_v2)
- CARL-295 (Done) [Q2] Phase 2 GOLD.DIM_MONTH -> no exact match

### Table is in prod but the story is still open (stale ticket or unfinished validation)

- CARL-284 (To Do) [Q2] Phase 2 GOLD.DIM_AGENCY transformation/business logic -> linear_digital_revenue_gold.dim_agency
- CARL-696 (Blocked) Get DCI_RATECARD_DEMOVPVH table available in bronze -> linear_digital_revenue_bronze.ideal_dci_dci_ratecard_demovpvh, linear_digital_revenue_bronze.ideal_dci_ratecard_demovpvh
- CARL-698 (Blocked) Get DCI_RATECARD_HEADER table available in bronze -> linear_digital_revenue_bronze.ideal_dci_dci_ratecard_header, linear_digital_revenue_bronze.ideal_dci_ratecard_header
- CARL-705 (Blocked) Get DCI_DEAL_SUMMARY_DATA table available in bronze -> linear_digital_revenue_bronze.ideal_dealbldr_dci_deal_summary_data
- CARL-1469 (Blocked) Ingest STW_IMPRESSION to bronze (Prod) -> linear_digital_revenue_bronze.ideal_posting_stw_impression
- CARL-1470 (Blocked) Ingest STW_UNIT_IMPRESSION to bronze (Prod) -> linear_digital_revenue_bronze.ideal_posting_stw_unit_impression
- CARL-1472 (Blocked) Ingest DE_UNITS to bronze (Prod) -> linear_digital_revenue_bronze.ideal_dealbldr_dci_de_units, linear_digital_revenue_bronze.ideal_msa_de_units
- CARL-2803 (Blocked) Get DCI_ORDER_HEADER table available in bronze -> linear_digital_revenue_bronze.ideal_dealbldr_dci_order_header

## 5. Blocked work, mapped to the lake

27 CARL stories are Blocked. For the 8 that name a table:

- CARL-691 Get DCI_INV_SCHEDULE_ENTITY table available in bronze: Table is in dev; story open (consistent)
- CARL-705 Get DCI_DEAL_SUMMARY_DATA table available in bronze: Table is in prod but the story is still open (stale ticket or unfinished validation)
- CARL-698 Get DCI_RATECARD_HEADER table available in bronze: Table is in prod but the story is still open (stale ticket or unfinished validation)
- CARL-1470 Ingest STW_UNIT_IMPRESSION to bronze (Prod): Table is in prod but the story is still open (stale ticket or unfinished validation)
- CARL-1472 Ingest DE_UNITS to bronze (Prod): Table is in prod but the story is still open (stale ticket or unfinished validation)
- CARL-2803 Get DCI_ORDER_HEADER table available in bronze: Table is in prod but the story is still open (stale ticket or unfinished validation)
- CARL-1469 Ingest STW_IMPRESSION to bronze (Prod): Table is in prod but the story is still open (stale ticket or unfinished validation)
- CARL-696 Get DCI_RATECARD_DEMOVPVH table available in bronze: Table is in prod but the story is still open (stale ticket or unfinished validation)

## 6. Evidence gaps: criteria nobody can currently measure

These rubric criteria have no data source. They are the real blockers to scoring readiness without guesswork.

- B5 (bronze) Schema contract enforced (nullability, decimals preserved). Needs: Source-vs-bronze schema diff results (cf. CARL-3556).
- B6 (bronze) Complete against the source system's table list. Needs: A manifest of expected source tables and row counts.
- S5 (silver) Join integrity verified (match rate, orphan rate). Needs: Join-verification results (cf. CARL-4177).
- S6 (silver) Data-quality rule results are logged. Needs: Rows in a DQ results table (a dq_metrics database exists in dev only).
- G4 (gold) Business definition documented and owned. Needs: A data-product registry entry with owner and grain.
- G5 (gold) Parity with legacy output verified. Needs: Parity-harness results (cf. CARL-4128).
- G6 (gold) A golden / eval dataset exists for it. Needs: A golden-dataset location and naming convention.

- Golden / eval datasets: a name search across all 1489 catalog tables for golden / eval / ground-truth / benchmark found **0**.
- DQ results store: `dq_metrics.dq_check_result` (dev=Y, prod=N).
- Environment isolation (non-prod DMS pointing at prod Oracle, CARL-4112): evidenced only by Jira/ARB notes. No input shows DMS endpoints, so it cannot be scored here.
- Layer definitions: the rubric in `config/rubric.json` is a proposal. Until owners agree it, the stage labels are this PoC's reading, not a company standard.

## 7. Limits of this run

- Glue `UpdateTime` is when metadata or data last changed, not when data was last read or reconciled.
- Load history comes from retained Iceberg snapshots. If snapshots were expired, 'single snapshot' can understate real load frequency.
- The `Done` judgement in section 4 uses a catalog that is older than Jira; stories resolved after the snapshot are separated out rather than counted as gaps.
- Table-name matching is heuristic (exact, then suffix). The match rate above is reported as is.
