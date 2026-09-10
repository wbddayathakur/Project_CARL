# Unified Media Planning — prototype, round 1

`UMP-Prototype.html` is the deliverable. One file, ~530 KB, no build step, no network
calls, no CDN. Double-click it, or attach it to an email, or drop it in a Confluence
page as an attachment. React and ReactDOM are inlined; nothing loads at runtime.

## What it covers

Five phases, two primary personas, and the sixteen agents that produce evidence for
them. Everything is anchored on one deal — Tide, Global Summer Refresh 2026,
$18.5M gross across US, EMEA, LATAM and APAC, linear and digital — against a
22-product WBD supply book with regional CPM benchmarks, sell-out positions and a
competitive read.

| Screen | What it is for |
| --- | --- |
| How the desk works | The flow diagrams: phase loop, **flow architecture**, persona swimlane, agent map, artifact lineage, learning loop, open questions |
| Your desk | The portfolio a planner opens on. The Tide row reads live state |
| Tide — Global Summer | The plan itself: Intake, Discovery, Strategize & iterate, Analyze, Approval |
| Global market | The supply book, universes, benchmarks and sell-out position Discovery ranks against |
| What it has learned | Active signals, their effect on this plan, feedback capture, the full ledger |

## The flow architecture

Source: *UMP — Flow Architecture*, 6 September 2026 (handwritten). It does not
replace the five-phase model; it refines what happens **inside** a phase and adds
the thing that decides whether a phase is allowed to end. Drawn on the
**Flow architecture** tab (`#blueprint/flow`).

### The orchestrator

The note defines it in three lines, and everything else follows from them:

- it knows the full state machine, the evaluation points inside it, and the current
  score at each point;
- it understands and scores the **intermediate** status, not just done / not-done;
- if scores are below par it **re-runs the loop, or surfaces for strategic analysis
  and input**.

There is one orchestrator per phase and they hand off to each other. The handoff
question is stated explicitly for Intake — *"what constitutes the trigger handoff to
the Discovery orchestrator: a sound, defensible intake brief is built"* — and the
same shape is applied to the other four.

In the build this is `src/25-gates.js` (`evaluateGate`) surfaced as the **handoff
gate** on every phase screen. Each gate is a weighted set of named evaluation
points; the phase score is their weighted mean; the handoff button is disabled until
every point is met. Nothing can be waived, because the point of the gate is that the
next phase can trust its inputs without re-checking them.

| Handoff | Asks | Points |
| --- | --- | --- |
| Intake → Discovery | Is a sound, defensible intake brief built? | material gaps adjudicated · contradictions resolved · graph confidence · brief approved on the current version · adjudication reasons hold |
| Discovery → Strategize | Is this a ranked list the planner would defend, product by product? | every funded region has a product · no unresolved hard breach · ranking changes survive evaluation · list accepted |
| Strategize → Analyze | Is there a saved allocation whose every deviation is argued? | solved from the accepted list · overrides argued and holding · no unallocated envelope · no hard breach · a version saved |
| Analyze → Approval | Is one version chosen, and is the choice legible? | more than one version · one committed · rubric against the bar · override arguments hold · a missed KPI explained |
| Approval → close | Does every line carry a decision and a reason? | every line decided · every decision reasoned · disapprovals actionable |

### Eval Justifications — the agent that challenges the decision

This is the box in the note's Discovery flow with two exits: **NO** loops back to the
human with feedback, **YES** goes on to customisation, pricing and avails. It is the
part of the document that changes the product most.

Before this, the prototype *demanded* a justification and never *judged* one — any
25 characters passed. Now the argument itself is scored, on four tests:

| Test | Met when |
| --- | --- |
| Substance | There is enough of an argument to read — roughly two sentences |
| Specific | It cites something checkable: a CPM, a share, a reach point, a date |
| Grounded | It is anchored in the record — the RFP, a clarification, the P&I position, the advertiser's history — rather than in taste |
| Consequence | It owns what the change costs. An argument that costs nothing reads as one that was not weighed |

Preference language on its own ("I think", "makes sense", "better") with nothing
checkable and nothing grounded is capped at 25 and always sent back — it is the
exact failure mode the box exists to catch. Scoring is deterministic and visible as
you type, so it reads as a standard rather than a verdict.

At 75 or above it passes. Between 50 and 74 it travels but is marked thin. Below 50
it is **sent back** with the specific thing it is missing. After two attempts you can
record it as weak, which lets the change through but flags its quality wherever it is
read — the change is never blocked, only its argument is on the record.

This applies to the planner's ranking changes and overrides, the commit note, and
P&I's own disapprovals, which are held to the same bar because a disapproval that
does not say what would make the line approvable is not an instruction the planner
can act on.

### Intake — agents write to a graph, not to a brief

The note's intake flow is numbered, and every arrow lands in one shared structure,
`BUILD RFP GRAPH`:

1. **Collect in parallel** — RFP requirements parser, advertiser history and
   competitive intelligence (each ranked by relevance), and seller context. All of
   them write records into the graph. None writes the brief.
   1″. **Client negotiations** arrive late and out of band, and re-derive the brief.
2. **Evidence Eval Agent** reads the graph, evaluates the *strengths and weaknesses
   of each record*, and writes an updated probability back onto it.
3. **Build intake brief** derives the brief from the graph — then *surface analysis
   with reccos (HITL)*, where the planner adjudicates, which updates evidence and
   re-derives.

Its three rules for the brief:

- **A.** An RFP is comprehensively defined by its attributes.
- **B.** Every attribute is either **copied from**, **inferred from**, or
  **operator-added by** — the provenance ladder, never blank.
- **C.** The intake brief is validated by the operator (the planner).

In the build, `src/26-evidence.js` scores every record on directness of source,
whether it is cited to a place you could go and check, corroboration, whether it is
contested, and age. Confidence is shown per record on the Evidence store tab and
summarised by the Evidence Eval Agent panel. Crucially it is **not static**:
adjudicating a contradiction or accepting a gap recommendation re-scores the graph,
which is the note's *update probabilities* edge. On the worked example that moves the
graph from 71% to 79% plannable, which is what lifts the intake gate over its bar.

### Products and packaging — one index, asked in words

Targeting templates, ad product configs and content inventory packages come out of
**FreeWheel and Operative**; reference pricing and product KPIs come out of
**spreadsheets and documents**. All of it is vectorised into one product RAG that
Discovery queries in natural language. The note's own examples:

1. What product meets these KPIs?
2. What customisations are available on this product?
3. I want to exclude Mature content off this product targeting.

Live in Discovery under **Ask the catalogue** (`src/27-rag.js`). Retrieval is
deterministic rather than embedded — what has to be right before anyone builds the
real index is the shape of the interaction and the provenance of the answer, so every
answer names the configs and documents it came from. Exclusions resolve to real
config expressions with their avails and price consequence, and only against
inventory that actually carries the thing being excluded: *exclude mature content
from Food Network* correctly returns nothing.

### Discovery — the loop the challenger sits in

```
rank products → surface for HITL → allow ranking changes + justification
                      ↑                          ↓
                      └──── NO ──── eval justifications ──── YES ────┐
                                                                      ↓
                                              allow customisations ───┼→ check inventory availability
                                                                      └→ compute price
                                                                          ↓
                            surface for HITL ←───────────────────────────┘
                                   ↓ additional customisations → back to customisations
                                 DONE → discovery orchestrator
```

Two loops, and the phase does not end until both are quiet. The upper one is the
argument loop: change the ranking, defend it, and either the defence holds or it
comes back. The lower one is the consequence loop: every customisation re-checks
avails and re-computes price *before* the planner commits to it, so nobody discovers
at trafficking that the targeting they promised costs a fifth of the inventory.

## Driving it

Open it and use the rail, or deep-link with the hash:

```
#blueprint            #blueprint/flow       #blueprint/personas
#blueprint/agents     #blueprint/lineage    #blueprint/learn
#blueprint/open       #desk                 #market
#learning
#plan/intake          #plan/discovery       #plan/strategize
#plan/analyze         #plan/approval
```

Append `/worked` to any `#plan/…` route — or use **Load the worked example** at the
bottom of the rail — to replay the decisions a planner would have made *up to* that
phase, leaving that phase to be done. Every seeded action carries the reason it
would have carried live, so the audit trail reads the same as a live one.

- `#plan/intake/worked` — a clean desk: 5 gaps open, 3 contradictions unadjudicated.
  Handoff gate at 14 of 100
- `#plan/discovery/worked` — brief v4 approved, ranking untouched. Gate at 26, and it
  names the three things in the way: APAC has budget and no product, Bleacher Report
  carries a viewability breach, the list is not accepted
- `#plan/strategize/worked` — list accepted, optimiser solved, nothing overridden
- `#plan/analyze/worked` — two versions saved, nothing committed
- `#plan/approval/worked` — PV-B committed, P&I 3 of 13 lines in

The gate scores are worth watching as you work a phase: they are the fastest way to
see that the orchestrator is scoring live state rather than showing a checklist.

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
src/25-gates.js       the orchestrator: state machine, evaluation points, handoff
                      scoring, and Eval Justifications
src/26-evidence.js    the RFP graph and the Evidence Eval Agent (record confidence)
src/27-rag.js         products / packaging system — the queryable product index
src/30-kit.js         UI kit, including the Excel-affinity grid (XL)
src/35-gate.js        the handoff gate panel and the challenger-aware justify modal
src/40-blueprint.js   the flow diagrams, drawn as SVG so they lift into a deck
src/41-flowarch.js    the flow architecture drawings from the 6 Sep note
src/50-store.js       plan state, phase strip, timeline, worked-example seeding
src/51-market.js      src/52-desk.js
src/60-intake.js  61-discovery.js  62-strategize.js  63-analyze.js  64-approval.js
src/70-learning.js    src/80-app.js    src/99-foot.html
tools/transpile.js    JSX → JS under JavaScriptCore
tools/shots.sh        screenshots every screen and fails on console errors
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
   the room could act on — and the reason is scored, not just required. A weak one
   comes back before the change travels.
5. A phase ends when it is defensible, not when the planner is finished. The
   orchestrator scores the handoff and can refuse it; that refusal is the only
   power any agent has over the plan.
6. The optimiser is not negotiated with. Levers are declared before the run; an
   override is re-solved *from*, not argued with.
7. Approvals bind to a version, not to "the plan". A late clarification lapses the
   prior approval.
8. Not branded as AI. The agents are named for the desk job each does.

## Caveats

All data is synthetic but internally consistent — CPMs, avails, universes and
sell-out rates are anchored to public market ranges for US, EMEA, LATAM and APAC
linear and streaming, not to WBD's actual book. The good-plan rubric on the Analyze
screen is labelled `[PROPOSED]` on the surface because its definition is an open
question, not a settled artifact. Open questions are listed with their status on the
last Blueprint tab.

Two things in the flow architecture are deliberately shallower than they would be in
production. Justification scoring is a deterministic rubric over what an argument
contains, not a language model reading it for sense — which means it can be gamed by
someone who knows the four tests, and the real version needs a model behind the same
four-test contract. And the product index is a query matcher over the catalogue
rather than a vector index over the FreeWheel and Operative configs. Both are built
so that the surface, the provenance and the refusal behaviour are right first; the
retrieval and the scoring can be replaced behind them without the screens changing.
