# Unified Media Planning — prototype, round 1

`UMP-Prototype.html` is the deliverable. One file, ~530 KB, no build step, no network
calls, no CDN. Double-click it, or attach it to an email, or drop it in a Confluence
page as an attachment. React and ReactDOM are inlined; nothing loads at runtime.

## What it covers

Five phases, two primary personas, and the twelve agents that produce evidence for
them. Everything is anchored on one deal — Tide, Global Summer Refresh 2026,
$18.5M gross across US, EMEA, LATAM and APAC, linear and digital — against a
22-product WBD supply book with regional CPM benchmarks, sell-out positions and a
competitive read.

| Screen | What it is for |
| --- | --- |
| How the desk works | The flow diagrams: phase loop, persona swimlane, agent map, artifact lineage, learning loop, open questions |
| Your desk | The portfolio a planner opens on. The Tide row reads live state |
| Tide — Global Summer | The plan itself: Intake, Discovery, Strategize & iterate, Analyze, Approval |
| Global market | The supply book, universes, benchmarks and sell-out position Discovery ranks against |
| What it has learned | Active signals, their effect on this plan, feedback capture, the full ledger |

## Driving it

Open it and use the rail, or deep-link with the hash:

```
#blueprint            #blueprint/personas   #blueprint/agents
#blueprint/lineage    #blueprint/learn      #blueprint/open
#desk                 #market               #learning
#plan/intake          #plan/discovery       #plan/strategize
#plan/analyze         #plan/approval
```

Append `/worked` to any `#plan/…` route — or use **Load the worked example** at the
bottom of the rail — to replay the decisions a planner would have made *up to* that
phase, leaving that phase to be done. Every seeded action carries the reason it
would have carried live, so the audit trail reads the same as a live one.

- `#plan/intake/worked` — a clean desk: 5 gaps open, 3 contradictions unadjudicated
- `#plan/discovery/worked` — brief v4 approved, ranking untouched
- `#plan/strategize/worked` — list accepted, optimiser solved, nothing overridden
- `#plan/analyze/worked` — two versions saved, nothing committed
- `#plan/approval/worked` — PV-B committed, P&I 3 of 13 lines in

## Building

Only needed if you change `src/`. macOS only, and it needs nothing installed:

```sh
./build.sh
```

JSX is transpiled by the vendored Babel running under the JavaScriptCore shell that
ships with macOS (`tools/transpile.js`), then every source file is concatenated into
the single HTML output. No node, no npm.

## Source layout

```
src/00-head.html      shell + all CSS
src/10-data-market.js WBD supply book, universes, CPM benchmarks, sell-out, competitive
src/11-data-plan.js   the deal, evidence store, provenance classes, gaps, contradictions,
                      P&I position cards, history, portfolio, agent roster
src/20-engine.js      ranking model, optimiser, reach curves, constraint checks, rubric
src/30-kit.js         UI kit, including the Excel-affinity grid (XL)
src/40-blueprint.js   the flow diagrams, drawn as SVG so they lift into a deck
src/50-store.js       plan state, phase strip, timeline, worked-example seeding
src/51-market.js      src/52-desk.js
src/60-intake.js  61-discovery.js  62-strategize.js  63-analyze.js  64-approval.js
src/70-learning.js    src/80-app.js    src/99-foot.html
```

## The rules the surfaces obey

Stated as tenets on the Persona swimlane tab, and worth knowing before reading any
screen:

1. No brief is ever edited. Briefs are read-only views derived from the evidence
   store; a planner who disagrees states what is wrong and why, that becomes a
   record, and the brief re-derives to a new version.
2. Nothing is deleted. Evidence is superseded.
3. No value appears without its provenance and a route to the record behind it.
4. Justify, then override. Every deviation carries a reason that a reader outside
   the room could act on.
5. The optimiser is not negotiated with. Levers are declared before the run; an
   override is re-solved *from*, not argued with.
6. Approvals bind to a version, not to "the plan". A late clarification lapses the
   prior approval.
7. Not branded as AI. The agents are named for the desk job each does.

## Caveats

All data is synthetic but internally consistent — CPMs, avails, universes and
sell-out rates are anchored to public market ranges for US, EMEA, LATAM and APAC
linear and streaming, not to WBD's actual book. The good-plan rubric on the Analyze
screen is labelled `[PROPOSED]` on the surface because its definition is an open
question, not a settled artifact. Open questions are listed with their status on the
last Blueprint tab.
