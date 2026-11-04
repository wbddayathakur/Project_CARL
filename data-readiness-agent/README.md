# CARL data-readiness agent: PoC

Scores each CARL data source against explicit layer criteria using **only real evidence**, so readiness reporting can use
status instead of percentages. No data in this project is simulated.

## Run

```
python3 -m readiness            # writes out/readiness_report.md, out/readiness.json, out/jira_glue_reconciliation.csv
python3 -m unittest discover -s tests
```

Standard library only, Python 3.9+.

## UI

```
python3 -m readiness.server        # then open http://127.0.0.1:8765
```

- **Overview**: headline numbers, ranked findings, tables by source, what nobody can measure.
- **Sources**: every source/layer with stage, a derived agent-use gate (BLOCK / CAUTION / CLEARED), rubric criteria, and the tables behind each row.
- **Jira vs lake**: filter stories by how Jira's status compares with the catalog.
- **Triage**: paste table names; each gets a verdict (already in prod, dev only, already requested, possible rename, new backlog item). Export to CSV.
- **Rubric**: change the freshness and recurring-load thresholds and watch everything recompute. Save writes `config/rubric.json`.
- **Ask the agent** (right panel): questions are routed to tool calls over the evidence. It is a rule-based router, not an LLM, and every answer shows its evidence trail.

### Static HTML prototype (no server)

`prototype/readiness_prototype.html` is a single self-contained file (about 1.3 MB) with a snapshot of the real data embedded. Double-click it; it works offline and can be emailed or shared.

```
python3 tools/build_prototype.py          # regenerate after the data or UI changes
python3 tests/check_prototype_parity.py   # in-browser logic == Python engine (29 checks)
python3 tests/check_prototype_ui.py       # drives every tab in a fake DOM (26 checks)
```

Triage, question answering and drill-downs run in the browser. The rubric tab offers a precomputed grid of thresholds (freshness 7/14/30/60/90 days, recurring load 1/2/3 days) instead of free values, and cannot save. Ages are computed from the real clock, so the snapshot visibly gets staler.

The server binds to 127.0.0.1 only, requires JSON on POSTs and rejects non-local Host headers.

## Inputs (all real, in `data/`)

| File | Source | As of |
|---|---|---|
| `glue_inventory_2026-10-07.csv` | Live AWS Glue export, dev + prod, from `iceberg-catalog-agent` | 2026-10-07 |
| `prod_load_history_2026-10-13.json` | Iceberg snapshot history for prod tables | 2026-10-13 |
| `jira_snapshot.json` | CARL Jira via Atlassian MCP (`tools/distill_jira.py`; JQL recorded inside the file) | 2026-10-22 |

`data/raw/` holds the raw Jira dumps (they contain names and comments) and is git-ignored.

## How it works

1. **Classify** every Glue table: source (rules in `config/rubric.json`), medallion layer, and whether it looks like a sandbox or test table (excluded, with counts shown).
2. **Score** each source/layer against the *proposed* rubric (`config/rubric.json`). Criteria with data behind them (in dev, in prod, fresh, loads recur) get exact counts. Criteria with no data source (schema contract, DQ results, parity, golden set, business definition) are reported as `UNVERIFIED`, never guessed.
3. **Reconcile Jira with the catalog**: parse the table name from each story title, match it to the catalog (exact, then suffix), and classify the mismatch, e.g. Done in Jira but not in prod, or in prod but still open. Stories resolved after the catalog snapshot are separated out. Cross-source name collisions are not counted as matches.
4. **Report** the evidence, the match rate, the evidence gaps and the limits of the run.

## Adapting it

- Change what "ready" means: edit `config/rubric.json` (criteria, freshness window, recurring-load threshold).
- Refresh: drop newer `glue_inventory_<date>.csv` / `prod_load_history_<date>.json` into `data/`, re-run `tools/distill_jira.py` input, then `python3 -m readiness`.

## Next steps toward the agent

- Replace the file inputs with live calls (Glue, Iceberg snapshots, Jira MCP) so the report is never stale.
- Add the missing evidence sources: DQ results, schema diffs, parity results, a source-table manifest.
- Expose `out/readiness.json` as an MCP tool so Metropolis / Agent Factory agents can ask "is this source fit to act on?" before they act.
- Table-request triage: feed new requests through the same matcher and rubric to build the bronze backlog.
- Golden/eval sets: needs production-traffic logs, which are not available today.
