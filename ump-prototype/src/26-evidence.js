/* =============================================================================
   26-evidence.js — the RFP graph and the Evidence Eval Agent.

   From the Flow Architecture note: intake does not assemble a brief directly.
   Every agent writes into one shared structure — `BUILD RFP GRAPH` — and reads
   back out of it. Sitting on that graph is an `Evidence Eval Agent` that
   evaluates the *strengths and weaknesses of each record* and updates its
   probability score. The brief is then built from the graph, not from the
   sources.

   The consequence worth having in the UI: two records can say the same thing
   and not be worth the same. A number read off page 2 of the RFP and a number
   inferred from four comparable advertisers are both evidence; only one of them
   is worth planning a $18.5M allocation on without asking.

   The score is deterministic and every point of it is attributable — no record
   carries a confidence it cannot explain.
   ============================================================================= */

const EV_TODAY = "2026-09-09";

/* Directness of the source. A stated number outranks an inferred one, and a
   planner correction outranks both because a human put their name on it. */
const EV_BASE = { stated:78, clarified:74, planner:80, seller:70, hist:52, cohort:42, gap:12 };

function evDays(ts){
  const a = new Date(String(ts || "").slice(0,10)), b = new Date(EV_TODAY);
  const d = Math.round((b - a) / 86400000);
  return isNaN(d) ? null : d;
}

function scoreEvidence(r, all, adj){
  const a = adj || { contra:{}, attrs:{} };
  const strengths = [], weaknesses = [];
  let s = EV_BASE[r.cls] != null ? EV_BASE[r.cls] : 50;

  /* The planner has adjudicated this attribute and put their name on the
     value. That is the strongest thing that can happen to an inference: it
     stops being a guess the system is carrying alone. */
  const owned = !!a.attrs[r.attr];

  strengths.push({ t: PROV[r.cls] ? PROV[r.cls].label : r.cls, v: EV_BASE[r.cls] || 50 });

  /* Cited to a place a reader can go and check. */
  const cited = r.loc && r.loc !== "—" && r.loc !== "";
  if (cited){ s += 9; strengths.push({ t:`Cited to ${r.loc}`, v:+9 }); }
  else weaknesses.push({ t:"No location in the source — cannot be re-checked without asking", v:-9, fix:"Ask the AE where this came from." });
  if (!cited) s -= 9;

  /* Corroboration: another record on the same attribute saying the same thing. */
  const same = (all || []).filter(x => x.id !== r.id && x.attr === r.attr);
  const agree = same.filter(x => String(x.value).trim() === String(r.value).trim());
  if (agree.length){ s += 8; strengths.push({ t:`Corroborated by ${agree.map(x=>x.id).join(", ")}`, v:+8 }); }

  /* Contested: another record on this attribute disagrees. Adjudicating the
     contradiction is what clears it — the losing record is superseded, never
     deleted, and the surviving one stops carrying the doubt. */
  const contested = CONTRADICTIONS.filter(c =>
    c.a.ev === r.id || c.b.ev === r.id || c.attr === r.attr);
  const openContest = contested.filter(c => !a.contra[c.id]);
  if (openContest.length){
    s -= 22;
    weaknesses.push({ t:`Contested by ${openContest.map(c=>c.id).join(", ")} — another record on this attribute disagrees`,
      v:-22, fix:"Adjudicate the contradiction; the losing record is superseded, not deleted." });
  } else if (contested.length){
    s += 6; strengths.push({ t:`Contradiction ${contested.map(c=>c.id).join(", ")} adjudicated`, v:+6 });
  }

  if (owned){ s += 22; strengths.push({ t:"Planner adjudicated this attribute and owns the value", v:+22 }); }

  /* Age. An inference drawn months ago is weaker than one drawn this week; a
     stated fact does not rot the same way, and neither does one a human has
     just re-affirmed. */
  const age = evDays(r.ts);
  if (age != null && age > 90 && (r.cls === "hist" || r.cls === "cohort") && !owned){
    s -= 10; weaknesses.push({ t:`Inferred ${age} days ago, before the flight was priced`, v:-10,
      fix:"Adjudicate the attribute, or re-run the inference against the current cohort." });
  } else if (age != null && age <= 30){
    s += 4; strengths.push({ t:`Arrived ${age} day${age===1?"":"s"} ago`, v:+4 });
  }

  /* An inference that does not name what it was drawn from is not an
     inference, it is an assertion. */
  if ((r.cls === "hist" || r.cls === "cohort") && !owned && !/\d/.test(String(r.src))){
    weaknesses.push({ t:"Basis is named but not counted — no deal or cohort size given", v:-6,
      fix:"Show n. An inference from four deals reads differently from one from forty." });
    s -= 6;
  }

  s = clamp(Math.round(s), 5, 99);
  return {
    id: r.id, conf: s, strengths, weaknesses,
    band: s >= 80 ? "high" : s >= 60 ? "workable" : s >= 40 ? "thin" : "weak",
    /* What the agent writes back onto the graph. */
    note: s >= 80 ? "Plan on it."
        : s >= 60 ? "Plan on it, and say in the brief that you did."
        : s >= 40 ? "Usable as a starting position, not as a commitment."
        : "Do not carry this into an allocation without asking.",
  };
}

/* The whole graph, scored against what the planner has adjudicated so far.
   This is the `Update probabilities / score` edge in the note: the agent
   re-scores the graph every time a human resolves something on it. */
function evalEvidenceGraph(records, st){
  const all = records || EVIDENCE;
  const s = st || {};
  const adj = {
    contra: s.contraDecisions || {},
    attrs: Object.fromEntries(Object.keys(s.gapDecisions || {})
      .map(gid => [(GAPS.find(g => g.id === gid) || {}).attr, true])
      .filter(([k]) => k)
      .concat(Object.keys(s.contraDecisions || {})
        .map(cid => [(CONTRADICTIONS.find(c => c.id === cid) || {}).attr, true])
        .filter(([k]) => k))),
  };
  const scored = all.map(r => scoreEvidence(r, all, adj));
  const by = Object.fromEntries(scored.map(x => [x.id, x]));
  const mean = scored.length ? Math.round(scored.reduce((s,x)=>s+x.conf,0)/scored.length) : 0;
  return {
    scored, by, mean,
    weak: scored.filter(x => x.conf < 60).sort((a,b)=>a.conf-b.conf),
    high: scored.filter(x => x.conf >= 80).length,
    /* Share of the graph the brief can be planned on without a question. */
    plannable: scored.length ? Math.round(scored.filter(x=>x.conf>=60).length / scored.length * 100) : 0,
  };
}

/* --------------------------------------------------------------- the surface */
const ConfBar = ({v}) => (
  <div className="row" style={{gap:7, alignItems:"center"}}>
    <div className={"bar " + (v>=80?"g":v>=60?"":"a")} style={{width:52, flexShrink:0}}>
      <i style={{width:v+"%"}}/></div>
    <span className="mono tiny" style={{width:20}}>{v}</span>
  </div>
);

/* The Evidence Eval Agent's own panel: not a list of records, a list of the
   ones that would not survive a question. */
const EvidenceEval = ({graph, onFix}) => (
  <Card title="Evidence eval agent"
    sub="Scores the strengths and weaknesses of each record on the RFP graph, and writes the probability back onto it."
    right={<Chip c={graph.plannable>=80?"g":graph.plannable>=60?"a":"r"}>{graph.plannable}% PLANNABLE</Chip>}>

    <div className="statgrid" style={{gridTemplateColumns:"1fr 1fr 1fr", marginBottom:13}}>
      <Stat label="Records on the graph" value={graph.scored.length}/>
      <Stat label="Mean confidence" value={graph.mean}/>
      <Stat label="Below the 60 bar" value={graph.weak.length} tone={graph.weak.length?"bad":"good"}/>
    </div>

    {graph.weak.length === 0
      ? <div className="banner g"><span className="bi">Sound</span>
          <div>Every record on the graph clears the 60 bar. The brief can be planned on without a question back to the AE.</div></div>
      : <>
          <div className="lbl">Weakest records, and what would strengthen them</div>
          <div className="col" style={{gap:10}}>
            {graph.weak.slice(0,5).map(x => {
              const rec = EVIDENCE.find(r => r.id === x.id) || {};
              return (
                <div key={x.id} style={{borderLeft:"2px solid var(--line)", paddingLeft:10}}>
                  <div className="row" style={{gap:8, alignItems:"center"}}>
                    <span className="mono tiny">{x.id}</span>
                    <ProvChip cls={rec.cls} small/>
                    <div className="grow tiny">{rec.attr}</div>
                    <ConfBar v={x.conf}/>
                  </div>
                  <div className="mini muted" style={{marginTop:3}}>{x.note}</div>
                  {x.weaknesses.map((w,i)=>(
                    <div key={i} className="mini" style={{marginTop:3}}>
                      <span style={{color:"var(--bad)"}}>−{Math.abs(w.v)}</span>{" "}
                      <span className="muted">{w.t}</span>
                      {w.fix && <div className="mini" style={{color:"var(--accent)", marginLeft:0}}>→ {w.fix}</div>}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </>}

    <div className="tiny dim" style={{marginTop:12, lineHeight:1.6}}>
      Confidence is not a model output — every point of it is attributable to the directness of the source,
      whether it is cited to a place you could go and check, whether anything corroborates or contests it,
      and how old it is. A record can be argued with on any one of those.
    </div>
  </Card>
);
