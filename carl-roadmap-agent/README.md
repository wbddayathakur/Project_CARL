# carl-roadmap-agent

Keeps `CARL_Program_Roadmap_v3.html` current from Jira, every week, in place.

One file, one path, one URL. The page people have already shared is rewritten
rather than republished, so links never go stale and nobody has to be told
where the new version is.

```
python -m carl_roadmap check     # prove credentials and fields, write nothing
python -m carl_roadmap run       # the weekly refresh
python -m carl_roadmap run --dry-run
```

## What it refreshes, and what it will not touch

Jira knows an epic's name, status, owner, ticket count and points. It does not
know which of the five CARL programmes the epic belongs to, what was committed
to Nage, or why a date moved. Those two halves are kept apart on purpose:

| Owned by Jira, refreshed weekly | Owned by you, never overwritten |
| --- | --- |
| epic name, status, assignee | programme and sub-project |
| ticket count, story points | committed start / target / forecast / actual |
| parent capability, last-updated | priority, the "why" note |
| RAG (derived from the above) | roadmap-only rows with no epic |

The human half lives in `registry/epic-map.yaml`. A refresh reads it and never
writes it. This is the whole reason the agent is safe to run unattended: a
refresh that regenerated the programme structure from Jira would flatten it
every Monday, which is how automated pages lose their audience.

`rels` (epic-to-epic dependencies) and `deps` (the outside dependencies) are
also judgement rather than data — Jira issue links do not carry "this vendor
owes us an API scope". The agent reads them back out of the page it is about to
rewrite and puts them straight back.

## How To Do and In Triage are counted

Per the agreed rule, **To Do and In Triage count as in progress**: the PM is
holding those stories to gather requirements with stakeholders, so they are
active work rather than an untouched backlog.

They are kept as their own bucket rather than merged into build work, because
the distinction is the one an exec acts on:

| Bucket | Statuses | Bar colour |
| --- | --- | --- |
| Done | Done, Closed, Resolved | green |
| In build | In Progress, UAT, QA, review, testing, Blocked | amber |
| Requirements with PM | To Do, In Triage, Pending Scope | blue |
| Excluded | Archive, Cancelled, Won't Do | not counted at all |

A programme sitting mostly blue is short of definition; mostly amber is short
of engineers. Collapsing the two would hide which. The headline
"in progress" figure is blue + amber, which is what the rule asks for.

Archived work leaves the denominator entirely, so tidying the backlog never
reads as a regression. Buckets are configured in `config.yaml`; a status that
matches nothing is counted as requirements (never as done) and reported at the
end of the run.

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env     # then paste a token from id.atlassian.com
.venv/bin/python -m carl_roadmap check
```

`bootstrap` has already been run — it seeded `registry/epic-map.yaml` from the
hand-built v3 page so none of that mapping had to be retyped. It refuses to
overwrite the file, so it is safe to leave in place.

## Scheduling

```
crontab -e
0 7 * * 1  /Users/dthakur/Documents/LocalRepo/carl-roadmap-agent/run-weekly.sh
```

Monday 07:00, before the week's reviews. If a closed laptop on Monday morning
is a risk, use `.github/workflows/weekly-roadmap.yml` instead — same agent on a
runner. One thing to settle first: the page lives in OneDrive and a GitHub
runner cannot write there, so the workflow currently runs `--dry-run` and
uploads the result as an artifact.

Exit codes matter to whatever you wire this into:

| Code | Meaning |
| --- | --- |
| 0 | refreshed, nothing needs a person |
| 1 | refreshed, but something needs attention — normally a new epic with no programme |
| 2 | Jira unreachable; the page was left at last week's numbers rather than blanked |

## Outlook

**Not connected, and not pretending to be.** There is no Outlook or Microsoft
Graph connector available to this agent, so nothing in the page comes from
mail. Wiring it up needs an Azure app registration with `Mail.Read`, which is a
tenant admin decision rather than something the agent can arrange for itself.

Until then `signals/notes.yaml` is read on each run if it exists, so status
notes that would otherwise arrive by mail can be dropped there and picked up:

```yaml
"1756":
  note: "FreeWheel vendor confirmed 7-day retention on 14 Oct — Silver scope unchanged."
  fc: "2026-12-15"
```

This is deliberately a smaller promise than "the agent reads your mail". A
weekly page that silently stopped including mail-borne updates would be worse
than one that never claimed to.

## What runs every week besides the numbers

The reconciliation checks in `reconcile.py` are the mismatches that were found
by hand at least once. Running them every Monday means nobody finds them by
hand again, and the page says what it does not know rather than quietly
presenting a wrong total.

| Code | What it catches |
| --- | --- |
| `NO-PROGRAM` | a new epic missing from every rollup until someone places it |
| `RM-ONLY` / `RM-RESOLVED` | roadmap commitments with no epic, and ones that now have one |
| `UNSIZED` | epics with tickets but no points — they make percentages rise by being opened |
| `DUPLICATE` | two epics with the same summary, so points counted twice |
| `LABEL-MISMATCH` | the AID/AIP class of error |
| `NAME-DRIFT` | the page name and the Jira summary have diverged |
| `OVERDUE` | past target with no revised date — a slip nobody has answered |
| `STALE` | In Progress but untouched for 45 days |

`NO-PROGRAM` exits 1, because an unmapped epic is invisible on every tab except
the tracker and that is the one finding that has to be cleared before the next
refresh.

## Layout

```
config.yaml               connection, buckets, RAG rules, output path
registry/epic-map.yaml    the human-owned half — programme structure and dates
signals/notes.yaml        optional manual updates (the Outlook stand-in)
carl_roadmap/
  agent.py                the weekly run
  model.py                buckets, rollups, RAG
  registry.py             human-owned fields; bootstrap from the page
  reconcile.py            the checks above
  render.py               splices data into the HTML without touching prose
  sources/jira.py         epics + children over REST
  sources/confluence.py   read-only page lookups for PRD links
out/history/              dated snapshots — week-on-week movement
tests/                    49 tests, including a full run against a copy of the real page
```

## Tests

```bash
.venv/bin/python -m pytest tests -q
```

`tests/test_end_to_end.py` runs the whole agent against a copy of the real
published page with Jira stubbed. It proves the file can be read, rewritten and
re-read; that human-owned fields survive; that a brand-new epic lands somewhere
visible rather than vanishing; and that running twice changes nothing.
