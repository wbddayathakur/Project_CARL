# iceberg-catalog-agent

Publishes what is available in the CARL Iceberg lakehouse and the Cube semantic
layer, every week, to one Confluence page whose URL never changes — so that URL
can sit inside the Intake demand form and be the first thing a requester reads.

## Why it is shaped this way

The input this replaces is a 1,464-line Glue catalog dump: 1,128 tables across
36 databases and four accounts, dev through prod, sorted by database name. That
document is correct and it is the right artefact for an engineer auditing the
estate. It is the wrong artefact to put behind an intake form, for one reason:
a requester cannot tell `ideal_dci_ratecard_demovpvh` in dev from a certified
Gold fact, so they conclude nothing exists and file a new request. Publishing
more of it makes that worse, not better.

So the agent keeps two tiers and never mixes them.

**The curated tier** is `registry/products.yaml`, hand-maintained, a few dozen
entries. Each one names the business question it answers, its grain, its owner
and a freshness promise. This is what a requester reads.

**The physical tier** is whatever Glue returned this morning. Collected, never
hand-edited, and tiered by how safe it is to cite — from `certified` down
through `production`, `pipeline`, `undocumented`, `sandbox` and `stale`.

Every run resolves the first against the second. A product claiming a table
that has vanished, gone stale, or never reached prod is downgraded in the
published page rather than continuing to advertise a promise it is not keeping.
The registry will drift — the design assumes it does, and the weekly run is
what surfaces it.

## What one run produces

| Output | What it is for |
| --- | --- |
| `out/iceberg-catalog.md` | The human-readable catalog. Products first, adoption second, the full listing last |
| `out/iceberg-catalog-tabular.md` | The same estate as pure tables — no prose sections. See below |
| `out/iceberg-catalog-inventory.csv` | The inventory table as CSV, for sorting and pivoting in Excel |
| `out/iceberg-catalog.confluence.xhtml` | The catalog in Confluence storage format |
| `out/iceberg-catalog.json` | Machine-readable. Also the payload the API serves, so the page and the API can never disagree |
| `out/history/adoption-<date>.json` | A dated copy of the metrics, so week-on-week movement is reconstructable without a time-series store |

## The tabular layout

The prose-and-sections layout of the original snapshot puts the logical model
in three places at once: definitions in paragraphs, attributes in per-database
sections, and stale counts in a tail table with a different shape. Nothing can
be sorted or pivoted without reading the whole document.

`render/tabular.py` flattens all of it into twelve tables:

| § | Table | Rows |
| --- | --- | --- |
| 1 | Run — counts and settings for this collection | 13 |
| 2 | Column definitions — the prose from the original, as rows | 9 |
| 3 | Tier values and what each one permits | 6 |
| 4 | Accounts | 4 |
| 5 | Databases — layer, domain, per-environment counts, coverage | one per database |
| 6 | **Table inventory** — every attribute as a column | one per table name |
| 7 | Lineage — one row per table-to-consumer edge | one per read edge |
| 8 | Producer jobs — what each job writes, and where | one per job |
| 9 | Source systems | one per source |
| 10 | Refresh cadences | one per distinct schedule |
| 11 | Not refreshed in the window | one per database |
| 12 | Run notes | as raised |

Section 6 is the one to sort. Sections 7 to 10 are pivots of it and carry
nothing it does not already hold; they exist because the inventory is over a
thousand rows wide and those four questions are the ones actually asked of it.

To write it over an existing snapshot — the normal case, since the point is to
replace the sectioned document:

```bash
.venv/bin/python -m iceberg_catalog \
  --source snapshot --snapshot path/to/snapshot.md \
  --tabular-out path/to/snapshot.md
```

A `.bak` of whatever was there is kept. `sources/snapshot.py` reads both
layouts — detected per table from the shape of its header row, not from a
document-level flag — so replacing a sectioned file with a flat one does not
break the fallback path. `tests/test_tabular.py` asserts the two parse to
identical catalogs, field by field.

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
# Live, across the four accounts, writing to out/
.venv/bin/python -m iceberg_catalog

# Live, and update the Confluence page
.venv/bin/python -m iceberg_catalog --publish

# No AWS: re-render from a markdown snapshot someone handed you
.venv/bin/python -m iceberg_catalog --source snapshot --snapshot path/to/snapshot.md

# Check the Confluence body renders and the credentials work, without writing
.venv/bin/python -m iceberg_catalog --publish --dry-run
```

`--source auto` (the default) tries live Glue and falls back if no account can
be reached. It prefers the previous run's `out/iceberg-catalog.json` over a
markdown snapshot, because the published markdown has stale and sandbox tables
stripped out of it and re-parsing that would shrink every adoption denominator.
A fallback run says so in a banner at the top of the page.

## The read-only API

```bash
.venv/bin/python -m iceberg_catalog serve        # http://127.0.0.1:8787
```

| Endpoint | |
| --- | --- |
| `/health` | generation time, source, counts |
| `/catalog` | everything |
| `/products` | `?domain= &status= &available=true` |
| `/products/<product_id>` | one product, with its live tables resolved |
| `/tables` | `?q= &domain= &layer= &tier= &env= &limit=` |
| `/adoption` | the metrics |
| `/search?q=` | ranked products and tables, plus a one-sentence verdict |

`/search` is the endpoint that matters. It is meant to be called by the intake
form while someone is still typing, so the form can answer before the request
is filed:

```bash
curl -s --get --data-urlencode "q=pacing against budget" localhost:8787/search
```

```
1 existing product may already answer this: Pacing, Revenue & Budget by Month.
Ask to use one before requesting a new build.
```

```bash
curl -s --get --data-urlencode "q=CPM and yield by vertical" localhost:8787/search
```

```
Nothing is available yet, but these are already designed: Ad Product Yield.
Attach your demand to one rather than opening a duplicate.
```

Catching that second case is worth more than the whole catalog. It is a
duplicate build about to be scoped against work that is already specified.

## Configuration

Everything lives in `config.yaml`. Four things need real values before the
first live run:

1. **AWS access per environment.** `profile` on a laptop, `role_arn` in CI. The
   run needs `glue:GetDatabases` and `glue:GetTables` and nothing else — it
   never reads table data, so no row leaves the account.
2. **`intake.form_url`.** The catalog's product links point here with the
   product already named in the query string:
   `?product_id=LDR-PACING-001&product_name=...&mode=reuse`.
3. **`confluence.page_id`.** Create the page once by hand and paste its ID. The
   agent then owns the body and updates that same page every week, which is
   what keeps the URL stable.
4. **`CONFLUENCE_USER` and `CONFLUENCE_TOKEN`** in the environment, never in
   the file. Under cron there is no shell profile, so put them in `.env` next
   to `run-weekly.sh` — it is gitignored.

## Scheduling

```bash
crontab -e
0 7 * * 1  /Users/dthakur/Documents/LocalRepo/iceberg-catalog-agent/run-weekly.sh
```

Monday 07:00, so the page is current before the week's requests arrive.

`.github/workflows/weekly-catalog.yml` does the same in CI and is the better
option: a laptop that is closed on Monday morning silently stops publishing,
and nobody notices until someone files a duplicate against a two-month-old
page.

## Maintaining the registry

Adding an entry to `registry/products.yaml` is the act that promotes a table
from "exists in Glue" to "you may build on this". The four statuses are
promises rather than labels:

| Status | Means |
| --- | --- |
| `certified` | An owner is accountable, the grain is fixed, breaking changes get announced |
| `beta` | Real and refreshing, but the contract is not frozen |
| `proposed` | Designed, not built. Listed so intake can attach demand instead of duplicating it |
| `deprecated` | Still there; do not build anything new on it |

`answers` must be a question a business person would actually ask. If you
cannot write one, the product is not ready to be listed.

Listing `proposed` products is not padding. The four Ad Products entries were
specified in full against the Week 35 workbook before any table exists, and
without them the same request gets raised again by someone who had no way of
knowing the design was already done.

## Tests

```bash
.venv/bin/python tests/test_roundtrip.py
.venv/bin/python tests/test_tabular.py
```

`test_roundtrip.py` asserts the fidelity difference the fallback logic depends
on: the published markdown is allowed to be lossy, the run JSON is not.

`test_tabular.py` asserts that the flat layout carries everything the sectioned
one did — same tables, same timestamps, same consumer edges, same stale counts.
That is what makes overwriting a snapshot in place safe.

## Module map

| Module | Responsibility |
| --- | --- |
| `config.py` | Load and validate `config.yaml` |
| `model.py` | `Table` and `DataProduct` — the two tiers |
| `sources/glue.py` | Live collection across the four accounts |
| `sources/snapshot.py` | Parse a markdown snapshot back into a catalog, sectioned or flat |
| `sources/previous.py` | Restore the previous run's JSON — the preferred fallback |
| `registry.py` | Load `products.yaml`, resolve it against the live catalog |
| `classify.py` | Layer, domain and shareability tier |
| `adoption.py` | The six metrics and the headline findings |
| `render/markdown.py` | The human-readable catalog |
| `render/tabular.py` | The twelve-table layout, plus the CSV inventory |
| `render/confluence.py` | Confluence storage format |
| `publish/confluence.py` | Update the page in place |
| `serve.py` | Read-only JSON API, including `/search` |
| `agent.py` | Orchestration |

## Known limits

- **Consumers and producers come from the `carl-data-engineering` manifests,
  not from query logs.** The inventory only sees reads it can find in that one
  repo, which is why 30 of 1,128 tables show a consumer. That number measures
  the inventory's coverage at least as much as it measures real usage, and the
  published page says so rather than presenting it as a usage statistic. Athena
  query-log analysis would settle it and is the obvious next source.
- **The Cube model is read from `registry/cube_model.yaml`, not from Cube.**
  Point `registry.cube_model` at a generated export of the REST `/meta`
  endpoint once the agent's network can reach it.
- **Freshness is Glue `UpdateTime`, which is a publish, not a read.** It moves
  when a commit writes a new metadata file. It says nothing about whether the
  data inside is correct.
- **`reuse_rate` needs the intake log.** It is the only metric that cannot be
  derived from the catalog, and it is the one that measures whether any of this
  is working. Without `intake.log_path` it is reported as unknown rather than
  guessed.
