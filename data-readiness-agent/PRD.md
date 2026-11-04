# PRD: CARL Data-Readiness Agent

| | |
|---|---|
| **Status** | Draft v0.1. A proof of concept exists; this PRD defines the product it should become |
| **Date** | 2026-10-22 |
| **Program** | CALS (Converged Advertising & Linear Systems), data platform: CARL (Iceberg lakehouse) |
| **Owner** | TBD (needs a named product owner and a data-platform engineering owner) |
| **Source of the problem** | Problem statement #1, "Data readiness lags the agentic ambition" |
| **Companion artifacts** | `README.md`, `out/readiness_report.md`, the running UI (`python3 -m readiness.server`) |

Figures marked **PoC** were measured by the prototype on real inputs (Glue export 2026-10-07, prod load history 2026-10-13, Jira 2026-10-22). Anything labelled *proposed* or *TBD* is a recommendation that needs an owner's decision.

---

## 1. Summary

CALS wants agents (Metropolis 2.0, the NAL/ARG MCP server, CAPI, Agent Factory agents) to act on data in Iceberg. Today nobody can say, with evidence, whether a given source is complete or trustworthy enough for an agent to act on. Readiness is reported in percentages with no agreed definition, Jira status is the de facto record, and the lake and Jira disagree.

The Data-Readiness Agent scores every data source and medallion layer against an explicit, owner-agreed rubric using only measurable evidence. It reports status (not percentages), says "unverified" when it cannot measure something, reconciles Jira against the catalog, triages new table requests before launches, and exposes a go/caution/block verdict that other agents can query before they act.

## 2. Problem

CALS wants agents to act on data that is not yet trustworthy or complete in Iceberg.

Evidence from program documents (CARL/Iceberg leadership review, Architecture Review Board summary):

- Bronze is not a full raw copy. Tables are ingested on request, close to launch.
- Salesforce reaches Iceberg only through Oracle, once a day.
- Non-prod DMS points at prod Oracle (CARL-4112).
- Golden and eval datasets do not exist.
- There is no agreed definition of "gold".

Evidence from the PoC on real data:

| Observation | PoC value |
|---|---|
| Scored tables in the catalog | 1,243 (481 in prod) |
| Tables that exist only in dev | 421, across 21 source/layer groups (largest: legacy CARL DWH gold 150, Venus silver 80, FreeWheel bronze 79) |
| FreeWheel phase 2 bronze tables requested in Jira found in dev | 0 of 98 |
| Prod tables with evidence of a recurring load | 0 of 278 that have load history (not proof of no schedule; see Risks) |
| Blocked Jira stories whose table is already in prod | 7 of 27 |
| Table-named Jira stories that matched a catalog table | 28 of 176 |
| Golden/eval datasets found by name search of the whole catalog | 0 |
| Rubric criteria with no data source at all | 7 of 18 |
| Agent-use gate result | 0 groups CLEARED, 18 CAUTION, 21 BLOCK |

Consequences: reporting overstates or misstates readiness; agents can be pointed at data that is dev-only, stale or unverified; launch dates slip because bronze tables are discovered missing late.

## 3. Goals and non-goals

### Goals
1. **A shared definition of readiness.** An explicit, versioned rubric per layer that data owners agree to.
2. **Evidence-based status.** Every status traces to a measurable fact. If it cannot be measured it is shown as unverified, never inferred.
3. **A machine-readable verdict.** Agents can ask "may I act on this source/layer/table?" and receive BLOCK, CAUTION or CLEARED with reasons.
4. **Earlier visibility of gaps.** New table requests are triaged against the catalog and Jira before a launch, producing a bronze backlog.
5. **Honest reporting.** Delivery and executive reporting uses real status and shows how fresh the evidence is.

### Non-goals (v1)
- Fixing data quality. The agent measures and reports; it does not repair data.
- Replacing Jira, the catalog, or the Evidence Store.
- Auto-promoting tables or auto-creating ingestion pipelines.
- Generating golden/eval datasets (a stated opportunity, but blocked on production-traffic logs; see Phase 4).
- Inferring readiness from natural-language documents.

## 4. Users and needs

| User | Need | How the agent serves them |
|---|---|---|
| Program / delivery manager | Report real status, not percentages | Source/layer status with counts and evidence age |
| Data engineer (CARL) | Know what is missing, stale or mis-ticketed | Reconciliation of Jira vs catalog; dev-only and stale lists |
| Agent builder (Metropolis 2.0, NAL/ARG, CAPI, Agent Factory) | Know whether data is safe to act on | Verdict API with reasons; evidence trail |
| Data owner / governance | Agree and enforce what "ready" means | Editable rubric; visible unmeasured criteria |
| Launch lead | Avoid late discovery of missing bronze tables | Table-request triage before launch |

## 5. Product scope

### 5.1 Capabilities

**C1. Readiness scoring.** Classify every catalog table by source, layer and noise (test/tmp/sandbox), then evaluate each source/layer against the rubric. Output exact counts per criterion with statuses PASS, PARTIAL, FAIL, n/a, UNVERIFIED.

**C2. Agent-use gate.** Derive a verdict per source/layer: BLOCK (not in prod), CAUTION (in prod but with stale tables, partial promotion or unverified criteria), CLEARED (all criteria have passing evidence). CLEARED must be impossible while any criterion is unverified.

**C3. Jira-to-lake reconciliation.** Parse the table name from each story, match it to the catalog, and classify the disagreement (Done but not in prod; in prod but still open; testing but no table; Done after the catalog snapshot, and so on). Report the match rate, and never count a cross-source name collision as a match.

**C4. Table-request triage.** For a requested table: already in prod, dev only (needs promotion), already requested in Jira, possible rename, or new bronze item. Suggest the source group from related existing tables. Export as a backlog.

**C5. Question answering with an evidence trail.** Answer readiness questions by calling tools over the evidence; show which tools ran.

**C6. Freshness transparency.** Show the age of every input and separate findings that depend on stale inputs rather than presenting them as gaps.

**C7. Editable rubric.** Thresholds and criteria are configuration, versioned and visible, and recompute all results.

### 5.2 Interfaces
- **Web UI** (exists): Overview, Sources, Jira vs lake, Triage, Rubric, and a question panel.
- **Report / JSON / CSV** (exists): `readiness_report.md`, `readiness.json`, `jira_glue_reconciliation.csv`.
- **MCP tool** (not built): expose C1 to C5 so other agents can query before acting. Registered through the MCP gateway.

## 6. Requirements

Priority: **P0** required for v1, **P1** needed soon after, **P2** later. Status reflects the PoC.

### Functional

| ID | Requirement | Priority | PoC status |
|---|---|---|---|
| F1 | Classify tables by source, layer and noise via configuration | P0 | Done |
| F2 | Score each source/layer against the rubric with exact counts, no composite percentage | P0 | Done |
| F3 | Report UNVERIFIED for criteria with no evidence source; never infer pass or fail | P0 | Done |
| F4 | Agent-use verdict per source/layer, with reasons; CLEARED only if all criteria pass | P0 | Done |
| F5 | Reconcile Jira stories with the catalog and report match rate, no-match breakdown and ambiguous matches | P0 | Done |
| F6 | Separate findings caused by stale inputs (Done after snapshot) from real gaps | P0 | Done |
| F7 | Table-request triage with verdict, evidence and CSV export | P0 | Done |
| F8 | Question answering that cites tool calls and falls back honestly | P1 | Done (rule-based) |
| F9 | Live ingestion of Glue (all accounts), Iceberg snapshot history and Jira, replacing file inputs | P0 | Not built |
| F10 | Cover QA and stage accounts in addition to dev and prod | P0 | Not built |
| F11 | Expose verdict and triage as MCP tools through the gateway, with authentication | P0 | Not built |
| F12 | Record each verdict and the evidence behind it in the Evidence Store for audit | P1 | Not built |
| F13 | Per-table verdict (today it is per source/layer) | P1 | Partial (table drill-down only) |
| F14 | History: compare readiness over time and show trend | P1 | Not built |
| F15 | Ingest results of DQ checks, schema diffs, join verification and parity runs to turn UNVERIFIED into PASS/FAIL | P1 | Not built (depends on those systems producing results) |
| F16 | Optional LLM layer for free-form questions, restricted to calling the same tools | P2 | Not built |
| F17 | Alerting: notify owners when a Blocked story's table is live, or a prod table goes stale | P2 | Not built |

### Non-functional

| ID | Requirement |
|---|---|
| N1 | **No fabricated data.** Every figure traces to an input; test suite asserts invariants (every table scored or excluded; unverifiable criteria never pass or fail) |
| N2 | **Explainability.** Every verdict lists the criteria and counts behind it |
| N3 | **Freshness.** Inputs refreshed at least daily; staleness shown in the UI and in every API response |
| N4 | **Security.** Read-only access to Glue and Jira; local UI binds to loopback; hosted version needs SSO and per-environment authorisation; raw Jira dumps (names, comments) are not stored in the repo |
| N5 | **Performance.** Full recompute for the current catalog (about 1,500 tables, a few hundred stories) well under a second; verdict API under 500 ms |
| N6 | **Configurability.** Rubric, source mapping and exclusion rules live in versioned config, not code |
| N7 | **Portability.** Core engine has no third-party dependencies |

## 7. The rubric (proposed, needs owner sign-off)

There is no agreed definition of readiness today, so the rubric is the single most important input to this product. The proposal below is what the PoC implements. Owners should edit it before it is treated as a standard.

| ID | Layer | Criterion | Evidence available today |
|---|---|---|---|
| B1 | Bronze | Landed in dev | Glue |
| B2 | Bronze | Promoted to prod | Glue |
| B3 | Bronze | Updated in prod within the freshness window (default 14 days) | Glue |
| B4 | Bronze | Loads recur (default at least 2 commit days in 30) | Iceberg snapshot history |
| B5 | Bronze | Schema contract enforced (nullability, decimals) | None |
| B6 | Bronze | Complete against the source system's table list | None |
| S1 to S4 | Silver | Exists, promoted, fresh, recurring | Glue / history |
| S5 | Silver | Join integrity verified | None |
| S6 | Silver | DQ rule results logged | None (a `dq_check_result` table exists in dev only) |
| G1 to G3 | Gold | Exists, promoted, fresh | Glue |
| G4 | Gold | Business definition documented and owned | None |
| G5 | Gold | Parity with legacy output verified | None |
| G6 | Gold | A golden/eval dataset exists | None (name search found 0) |

Verdict logic (proposed): BLOCK if the layer is absent or dev-only; CAUTION if in prod but any criterion is partial, failing or unverified; CLEARED only if every criterion passes.

## 8. Success metrics

Baselines are PoC measurements. **Targets are TBD** and should be set with the program owners; none are asserted here.

| Metric | Baseline (PoC) | Target |
|---|---|---|
| Share of rubric criteria with an evidence source | 11 of 18 | TBD |
| Source/layer groups with a verdict backed by at least one quality criterion | 0 | TBD |
| Jira stories that disagree with the lake (open but live, Done but missing) | 11 flagged (8 open-but-live, 3 Done-but-missing) | TBD, trending down |
| Table-named stories that can be matched to a catalog table | 28 of 176 | TBD |
| Age of the oldest input at report time | 15 days (catalog) | TBD (proposed at most 1 day) |
| Launches where a missing bronze table was found only late | Not measured today | Baseline first, then TBD |
| Agents that check the verdict before acting | 0 | TBD |

## 9. Architecture

**Today (PoC):** file inputs (Glue CSV, load-history JSON, Jira snapshot) → classification → rubric scoring → Jira matcher → engine → web UI, JSON and CSV outputs. Standard library only.

**Target:**
- **Collectors**: Glue (all accounts), Iceberg snapshot metadata (Athena/Glue), Jira via the Atlassian MCP, scheduled on MWAA or equivalent.
- **Evidence layer**: normalised facts with timestamps, stored in the Evidence Store.
- **Scoring engine**: the existing deterministic engine, driven by versioned rubric config.
- **Interfaces**: MCP server (verdict, triage, reconcile, explain) behind the MCP gateway; web UI for people; scheduled report to delivery reporting.
- **Optional LLM layer**: only calls the tools above and cites them. It does not hold facts of its own.

## 10. Dependencies

- Read access to Glue and Iceberg metadata in dev, QA, stage and prod (QA and stage accounts are absent from the current export).
- Jira access via the Atlassian MCP.
- MCP gateway and Evidence Store (Agent Factory work).
- Result feeds from the DQ framework (cf. CARL-4177 join verification, CARL-3556 schema checks), the parity harness (cf. CARL-4128), and the DQ results table, to retire UNVERIFIED criteria.
- A source-table manifest per source system, to make bronze completeness measurable (B6).
- A data-product registry with owners and grain, for gold definitions (G4).

## 11. Rollout

No calendar dates are proposed; sequencing only.

| Phase | Scope | Exit criteria |
|---|---|---|
| **0. PoC** (done) | File inputs, scoring, reconciliation, triage, UI | Reviewed with data owners |
| **1. Agree the rubric** | Owners edit and approve the rubric; map epics to sources; decide the freshness window | Signed-off rubric version 1 |
| **2. Live and complete** | F9, F10: live collectors, all four accounts, scheduled refresh | Inputs less than 1 day old; QA/stage covered |
| **3. Agents consume it** | F11, F12: MCP tools, audit trail; first agent (for example Metropolis 2.0) checks the verdict before acting | One agent gated by verdict in a real flow |
| **4. Close evidence gaps** | F15 plus golden/eval generation | Criteria B5, B6, S5, S6, G5 measurable; production-traffic logs available |

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Rubric disagreement stalls the product | Ship the proposal as editable config; show the criteria and counts so debate is about definitions, not hidden logic |
| Stale evidence leads to wrong conclusions | Show input age everywhere; separate "after snapshot" findings; live collectors in Phase 2 |
| Table-name matching is heuristic (28 of 176 matched) | Report the match rate; never count cross-source collisions; add a story-to-table field or link convention in Jira so matching becomes exact |
| "No recurring load" may be a snapshot-retention artefact | Label as "not evidenced", not "fail"; add scheduler/DAG run history as a better source |
| Glue `UpdateTime` is not a data-freshness guarantee | State the limit in the report; add row-count and max-timestamp checks when available |
| False sense of safety from a green verdict | CLEARED requires every criterion to pass; today none can |
| Verdict used as a hard gate before it is trusted | Start advisory (CAUTION/BLOCK shown to the agent), move to enforcing only after owner sign-off |
| Raw Jira data contains people and comments | Keep raw dumps out of version control; store only the distilled fields |

## 13. Open questions

1. Who owns the rubric, and who can approve a change?
2. Is the freshness window of 14 days right per source, or should each source have its own cadence?
3. Should an agent be blocked or only warned when the verdict is CAUTION?
4. Where should the evidence and verdicts live: the Evidence Store, the catalog, or both?
5. Can Jira carry an explicit target-table field so reconciliation stops relying on title parsing?
6. What is the authoritative list of tables each source system should land in bronze (needed for completeness)?
7. How should non-prod DMS pointing at prod Oracle (CARL-4112) be evidenced: DMS endpoint inventory, or a check in the collector?
8. What counts as a golden/eval set for CALS agents, and where would production-traffic logs come from?

## 14. Appendix: how the PoC computes its findings

- **Scoping:** a table is scored if it has a medallion layer, is not in a sandbox database (`*test*`, `*_poc*`, `*_uat*` and similar) and does not look like a test/tmp table. Counts of excluded tables are shown (PoC: 178 sandbox-database tables, 55 test/tmp-looking, 13 without a layer).
- **Stage:** `not present`, `dev only`, `partly in prod`, `in prod`, derived only from Glue.
- **Recurring load:** commits on at least N distinct days in the last 30, from retained Iceberg snapshots.
- **Reconciliation:** parse a table name from the story title, infer layer from the title or parent epic, match exact then by suffix at an underscore boundary within the same source group. Classes: done and in prod; done but dev-only; done with no table; done after snapshot; live but open; in dev and open; testing with no table; open with no table.
- **Verification:** 33 automated tests, including invariants against the real data and local-server security checks.
