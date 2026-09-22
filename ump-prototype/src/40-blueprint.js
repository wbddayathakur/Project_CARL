/* =============================================================================
   40-blueprint.js — the visual flows.
   Phase loop, persona swimlane, agent map, artifact lineage, learning loop.
   Drawn as SVG so they can be lifted straight into a deck.
   ============================================================================= */

function wrapText(t, maxChars){
  const words = String(t).split(/\s+/); const out = []; let line = "";
  words.forEach(w => {
    if ((line + " " + w).trim().length > maxChars){ if(line) out.push(line); line = w; }
    else line = (line ? line + " " : "") + w;
  });
  if (line) out.push(line);
  return out;
}

const SvgBox = ({x, y, w, h, title, body, fill="#fff", stroke="var(--line)", dash, titleColor, chars=30, tone}) => {
  const lines = body ? wrapText(body, chars) : [];
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx="6" fill={fill} stroke={stroke} strokeWidth="1"
        strokeDasharray={dash ? "4 3" : null}/>
      {tone && <rect x={x} y={y} width="3" height={h} rx="1.5" fill={tone}/>}
      {title && <text x={x+10} y={y+15} className="flx" style={{fontWeight:600, fill:titleColor||"var(--ink)"}}>{title}</text>}
      {lines.map((l,i)=><text key={i} x={x+10} y={y+(title?29:15)+i*11.5} className="flx-s">{l}</text>)}
    </g>
  );
};

const AH = { "#8a95a0":"ah", "#0b57d0":"ahb", "#b3261e":"ahr" };

/* A label may sit directly on its own line: it is drawn on a white chip so the
   stroke reads as passing behind it, which keeps both loops legible. */
const Arrow = ({d, color="#8a95a0", dash, label, lx, ly, head=true, lw=40, chip}) => {
  const ls = label ? wrapText(label, lw) : [];
  const w  = Math.max(...ls.map(l=>l.length), 0) * 4.35 + 10;
  const h  = ls.length * 11.5 + 5;
  return (
    <g>
      <path d={d} fill="none" stroke={color} strokeWidth="1.3" strokeDasharray={dash?"4 3":null}
        markerEnd={head ? `url(#${AH[color] || "ah"})` : null}/>
      {chip && ls.length > 0 &&
        <rect x={lx-w/2} y={ly-h/2} width={w} height={h} rx="3" fill="#fff"/>}
      {ls.map((l,i) => chip
        ? <text key={i} x={lx} y={ly-h/2+11+i*11.5} textAnchor="middle" className="flx-s" style={{fill:color}}>{l}</text>
        : <text key={i} x={lx} y={ly+i*11.5} className="flx-s" style={{fill:color}}>{l}</text>)}
    </g>
  );
};

const Defs = () => (
  <defs>
    <marker id="ah" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L8,4 L0,8 z" fill="#8a95a0"/>
    </marker>
    <marker id="ahb" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L8,4 L0,8 z" fill="#0b57d0"/>
    </marker>
    <marker id="ahr" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L8,4 L0,8 z" fill="#b3261e"/>
    </marker>
  </defs>
);

/* ------------------------------------------------------------- 1. phase loop */
const PhaseLoopSvg = () => (
  <svg viewBox="0 0 1260 484" style={{width:"100%", height:"auto"}}>
    <Defs/>

    {/* ------------------------------------------------------------- input */}
    <text x="16" y="40" className="flx-t">INPUT</text>
    <SvgBox x={14} y={48} w={182} h={58} title="RFP + Salesforce opp" chars={28} tone="#8a95a0"
      body="Attachments, AE call notes, do-not-air list"/>
    <Arrow d="M196,77 L246,77"/>

    {/* ------------------------------------------------------------- intake */}
    <SvgBox x={250} y={44} w={350} h={62} fill="#fafbfc" tone="#57636e" chars={57}
      title="Intake — what does the advertiser want?"
      body="Evidence store built. Brief derives. Planner adjudicates gaps and contradictions, then approves a version."/>
    <text x="622" y="40" className="flx-t">PRODUCES</text>
    <SvgBox x={622} y={48} w={180} h={44} title="Intake brief" body="versioned, read-only" chars={28} dash/>
    <Arrow d="M425,106 L425,156"/>
    <text x="433" y="122" className="flx-s">approved version opens Discovery</text>

    {/* --------------------------------------------------------- the loop */}
    <rect x="236" y="128" width="378" height="254" rx="10" fill="none" stroke="#cfe6dc" strokeDasharray="5 4"/>
    <text x="244" y="146" className="flx-t" style={{fill:"#0d7a4e"}}>PLAN-BUILDING LOOP · THE PLANNER OWNS ALL THREE</text>

    <SvgBox x={250} y={158} w={350} h={58} fill="#eef8f3" tone="#0d7a4e" chars={57}
      title="Discovery — which products, in what order, why?"
      body="Eligibility list, every exclusion legible. Five criteria rank it. Planner re-orders with reasons."/>
    <SvgBox x={622} y={160} w={180} h={54} title="Strategy brief" body="one per plan version" chars={28} dash/>
    <Arrow d="M425,216 L425,238"/>

    <SvgBox x={250} y={238} w={350} h={58} fill="#eef8f3" tone="#0d7a4e" chars={57}
      title="Strategize & iterate — what is the allocation?"
      body="Levers declared before the run. Optimiser solves. Planner overrides with a reason, saves a version."/>
    <SvgBox x={622} y={240} w={180} h={54} title="Plan version brief" body="immutable once saved" chars={28} dash/>
    <Arrow d="M425,296 L425,320"/>

    <SvgBox x={250} y={320} w={350} h={56} fill="#eef8f3" tone="#0d7a4e" chars={57}
      title="Analyze — which version do we put forward?"
      body="Scored against the good-plan rubric. One version is committed."/>
    <SvgBox x={622} y={320} w={180} h={54} title="Plan version analysis" body="scored, never ranked" chars={28} dash/>

    {/* the two return paths run in the left gutter so nothing crosses an artifact */}
    <Arrow d="M250,348 H196 V190 H244" color="#0b57d0"
      label="revise · re-run" lx={196} ly={264} lw={16} chip/>
    <Arrow d="M425,376 L425,404"/>

    {/* ----------------------------------------------------------- approval */}
    <SvgBox x={250} y={404} w={350} h={54} fill="#fffdf6" tone="#9a6600" chars={57}
      title="Approval — P&I decides line by line"
      body="Against a position already stated, seeing what each line does to inventory."/>
    <SvgBox x={622} y={406} w={200} h={50} title="Approved / disapproved lines" body="every line has a decision" chars={32} dash/>

    <Arrow d="M250,430 H128 V196 H244" color="#b3261e" dash
      label="disapproved lines return to Discovery" lx={189} ly={430} lw={19} chip/>

    {/* ------------------------------------------------------- right column */}
    <SvgBox x={846} y={44} w={400} h={66} fill="#fff8f7" tone="#b3261e" chars={66}
      title="Late negotiation, or a change in P&I's position"
      body="Enters as new evidence anywhere in the flow. The brief re-derives and the prior approval lapses."/>
    <Arrow d="M844,50 C680,4 560,4 426,34" color="#b3261e" dash/>

    <SvgBox x={846} y={126} w={400} h={94} fill="#fafbfc" tone="#0b57d0" chars={66}
      title="What the planner can always do"
      body="Traverse backwards to any phase from any point. Short-circuit steps on later passes. Dive into any detail that influences the outcome, from anywhere in the iteration."/>
    <SvgBox x={846} y={236} w={400} h={94} fill="#fafbfc" tone="#5b3fb8" chars={66}
      title="What carries forward every iteration"
      body="Planner overrides and their justifications. Products rejected and why. Targeting already tested, with its price and avails consequence. P&I disapproval reasons."/>
    <SvgBox x={846} y={346} w={400} h={82} fill="#fff8f7" tone="#b3261e" chars={66}
      title="What never happens"
      body="Nobody edits a brief. Nobody adjusts the optimiser mid-solve. Nothing is deleted — evidence is superseded. No value appears without its provenance."/>
  </svg>
);

/* --------------------------------------------------------- 2. persona lanes */
const LANES = [
  { name:"Planner", role:"Primary", tone:"#0b57d0", h:118, cells:[
    "Owns the phase. Reads the derived brief, adjudicates every contradiction, accepts or rejects each inference with a reason. The only approver.",
    "Reads the reasoning behind every rank — a first-class surface, not a tooltip. Re-orders, adds, removes and re-targets. Each change carries a justification.",
    "Declares every lever before the run: order, targeting, soft constraints. Overrides allocations with a reason. Saves a version they would defend.",
    "Judges versions against the rubric and against the advertiser's stated requirements. Commits one. Every change it provokes is made back in Discovery.",
    "Receives the line decisions. Leaves approved lines alone, reworks the disapproved ones, re-ranks where P&I wanted more weight, re-runs.",
  ]},
  { name:"P&I approver", role:"Primary", tone:"#9a6600", h:98, cells:[
    "Voice of the seller. Standing position cards enter the evidence store as soft constraints, each with its reason. Where nothing is stated, the absence is recorded.",
    "No action. Their position is already ranked in, and the planner can see which constraint each ranking decision served.",
    "No action. Their position enters the solve as constraints, not as a conversation with the solver.",
    "No action.",
    "Decides every line against the position they already stated, seeing what each line does to sellout and yield before approving. Disapproval carries reasons.",
  ]},
  { name:"Account Executive", role:"Peripheral", tone:"#8a95a0", h:74, cells:[
    "Voice of the customer. Submits the opportunity; clarifications enter as evidence with their provenance.",
    "Late client negotiation lands here as new evidence and re-opens the phase.",
    "—", "—",
    "Carries the committed version to the client. Client pushback returns as new evidence.",
  ]},
  { name:"Ad Ops leadership", role:"Reader", tone:"#8a95a0", h:62, cells:[
    "Reads the intake brief. One artifact, no per-role variant.", "—", "—",
    "Reads the plan brief and the analysis.", "Reads outcomes and key performance metrics.",
  ]},
  { name:"System agents", role:"Runs the desk", tone:"#0d7a4e", h:106, cells:[
    "Intake · Advertiser Context · Cohort · Seller Position · Competitive. They write records, never conclusions, and every inference names its evidence.",
    "Eligibility · Ranking · Avails & Pricing. Every exclusion gets a reason; every rank gets its rationale; price and avails re-check the moment targeting moves.",
    "Optimiser. Deterministic, not conversational. Solves only from the accepted list and nothing is adjusted while it runs.",
    "Analysis. Scores each version in isolation against the rubric — it does not rank versions against each other, because that would be choosing for the planner.",
    "Approval package · Learning. Presents position and consequence; never decides. Disapproval reasons become tomorrow's soft constraints.",
  ]},
];
const PHASE_COLS = [
  { n:"Intake", q:"What does the advertiser want, and what do we not know?" },
  { n:"Discovery", q:"Which products are eligible, in what order, and why?" },
  { n:"Strategize & iterate", q:"Given that list, what is the allocation?" },
  { n:"Analyze", q:"Which of these versions do we put forward?" },
  { n:"Approval", q:"Does this plan agree with our inventory and yield position?" },
];
const ARTIFACTS = ["Intake brief","Strategy brief","Plan version brief","Plan version analysis","Approval package"];

const SwimlaneSvg = () => {
  const LW = 128, CW = 216, HH = 46, AH = 40;
  const W = LW + CW*5, laneY = [];
  let y = HH;
  LANES.forEach(l => { laneY.push(y); y += l.h; });
  const H = y + AH;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{width:"100%", height:"auto"}}>
      <Defs/>
      <rect x="0" y="0" width={W} height={H} rx="8" fill="#fff" stroke="var(--line)"/>
      {/* header */}
      <rect x="0" y="0" width={W} height={HH} fill="#f2f4f7"/>
      {PHASE_COLS.map((p,i)=>(
        <g key={i}>
          <text x={LW + i*CW + 11} y={18} className="flx" style={{fontWeight:600}}>{p.n}</text>
          {wrapText(p.q, 34).slice(0,2).map((l,j)=><text key={j} x={LW+i*CW+11} y={30+j*10} className="flx-s">{l}</text>)}
          <line x1={LW+i*CW} y1="0" x2={LW+i*CW} y2={H} stroke="var(--line)"/>
        </g>
      ))}
      {/* lanes */}
      {LANES.map((l,li)=>(
        <g key={li}>
          <rect x="0" y={laneY[li]} width={LW} height={l.h} fill="#fafbfc"/>
          <rect x="0" y={laneY[li]} width="3" height={l.h} fill={l.tone}/>
          <text x="12" y={laneY[li]+19} className="flx" style={{fontWeight:600}}>{wrapText(l.name,15)[0]}</text>
          {wrapText(l.name,15)[1] && <text x="12" y={laneY[li]+31} className="flx" style={{fontWeight:600}}>{wrapText(l.name,15)[1]}</text>}
          <text x="12" y={laneY[li]+(wrapText(l.name,15)[1]?45:33)} className="flx-s">{l.role}</text>
          <line x1="0" y1={laneY[li]} x2={W} y2={laneY[li]} stroke="var(--line)"/>
          {l.cells.map((c,ci)=>(
            <g key={ci}>
              {c === "—"
                ? <text x={LW+ci*CW+11} y={laneY[li]+20} className="flx-s">—</text>
                : wrapText(c, 33).map((t,ti)=>(
                    <text key={ti} x={LW+ci*CW+11} y={laneY[li]+17+ti*11.5} className="flx" style={{fontSize:10}}>{t}</text>))}
            </g>
          ))}
        </g>
      ))}
      {/* artifact band */}
      <line x1="0" y1={H-AH} x2={W} y2={H-AH} stroke="var(--line)"/>
      <rect x="0" y={H-AH} width={W} height={AH} fill="#f6f7f9"/>
      <text x="12" y={H-AH+16} className="flx-t">PRODUCES</text>
      <text x="12" y={H-AH+30} className="flx-s">versioned, read-only</text>
      {ARTIFACTS.map((a,i)=>(
        <g key={i}>
          <rect x={LW+i*CW+10} y={H-AH+9} width={CW-24} height={22} rx="4" fill="#fff" stroke="var(--line)" strokeDasharray="4 3"/>
          <text x={LW+i*CW+20} y={H-AH+24} className="flx" style={{fontSize:10.5}}>{a}</text>
          {i<4 && <path d={`M${LW+(i+1)*CW-12},${H-AH+20} L${LW+(i+1)*CW+8},${H-AH+20}`} stroke="#8a95a0" strokeWidth="1.2" markerEnd="url(#ah)"/>}
        </g>
      ))}
    </svg>
  );
};

/* ------------------------------------------------------ 3. artifact lineage */
const LineageSvg = () => (
  <svg viewBox="0 0 1260 300" style={{width:"100%", height:"auto"}}>
    <Defs/>
    <rect x="8" y="34" width="300" height="242" rx="8" fill="#fafbfc" stroke="var(--line)"/>
    <text x="20" y="52" className="flx-t">EVIDENCE STORE — RECORDS, NOT SUMMARIES</text>
    {[
      ["Salesforce opportunity + RFP","Stated","#0b57d0"],
      ["Client clarifications via AE","Clarified","#0a6b6b"],
      ["Advertiser 12-month history","Inferred · history","#9a6600"],
      ["Cohort of similar advertisers","Inferred · cohort","#5b3fb8"],
      ["P&I position cards","Seller context","#0f1519"],
      ["Competitive research","[OPEN] no class yet","#b3261e"],
      ["Planner corrections","Planner","#0d7a4e"],
    ].map(([t,c,col],i)=>(
      <g key={i}>
        <rect x={20} y={62+i*29} width={276} height={23} rx="4" fill="#fff" stroke="var(--line)"/>
        <rect x={20} y={62+i*29} width="3" height={23} rx="1.5" fill={col}/>
        <text x={30} y={77+i*29} className="flx" style={{fontSize:10.5}}>{t}</text>
        <text x={290} y={77+i*29} className="flx-s" textAnchor="end" style={{fill:col}}>{c}</text>
      </g>
    ))}
    <Arrow d="M308,150 L348,150" color="#0b57d0"/>
    <text x="312" y="143" className="flx-s">derives</text>

    <SvgBox x={350} y={64} w={194} h={172} fill="#fff" title="Intake brief" chars={32}
      body="Read-only. Nobody writes it. Every value carries its provenance and a route to the record behind it. Hard and soft constraints separated. Gaps named, never blanked. Re-derives on its own when evidence changes — nobody asks for a refresh."/>
    <text x={360} y={228} className="flx-s" style={{fill:"#0b57d0"}}>v1 · v2 · v3 — all readable</text>

    <Arrow d="M544,150 L584,150" color="#0b57d0"/>
    <SvgBox x={586} y={64} w={194} h={172} fill="#fff" title="Strategy brief" chars={32}
      body="+ product, pricing and inventory. Ranked eligibility list, the reason for every position, exclusions with their reason, and the system's original list beside the planner's changes."/>
    <text x={596} y={228} className="flx-s" style={{fill:"#0b57d0"}}>one per plan version</text>

    <Arrow d="M780,150 L820,150" color="#0b57d0"/>
    <SvgBox x={822} y={64} w={194} h={172} fill="#fff" title="Plan version brief" chars={32}
      body="+ optimiser output and planner overrides. Immutable once saved. Binds exactly one strategy brief version. Can be forked into a new line of exploration."/>
    <text x={832} y={228} className="flx-s" style={{fill:"#0b57d0"}}>PV-A · PV-B · PV-C</text>

    <Arrow d="M1016,150 L1056,150" color="#0b57d0"/>
    <SvgBox x={1058} y={64} w={194} h={172} fill="#fffdf6" title="Approval package" chars={32}
      body="One version and everything upstream of it. Bound to that version — approval never binds to 'the plan' (T9)."/>
    <text x={1068} y={228} className="flx-s" style={{fill:"#0b57d0"}}>binds to a version, not a plan</text>

    <text x="8" y="292" className="flx-s">Correction path: a planner who disagrees with a value does not edit the brief. They state what is wrong and why; that statement becomes a record; the brief re-derives to a new version (T3).</text>
  </svg>
);

/* ------------------------------------------------------------ 4. learn loop */
const LearnLoopSvg = () => (
  <svg viewBox="0 0 1180 216" style={{width:"100%", height:"auto"}}>
    <Defs/>
    {[
      ["Planner acts","Re-orders a rank, overrides an allocation, rejects a recommendation, edits targeting.","#0b57d0"],
      ["Reason is required","T6. A change without a stated reason is not accepted, so the signal always arrives with its explanation.","#0b57d0"],
      ["Recorded as evidence","Not a log line. A record in the evidence store, superseding nothing, visible in the brief's timeline.","#0d7a4e"],
      ["Applied to the next derivation","Same deal: the next iteration starts from it. Similar deals: it reweights a criterion or pre-flags a product.","#5b3fb8"],
      ["Visible and reversible","The planner can see exactly what the system learned, and switch any signal off.","#9a6600"],
    ].map(([t,b,c],i)=>(
      <g key={i}>
        <SvgBox x={8+i*236} y={30} w={214} h={100} title={t} body={b} chars={31} tone={c} fill="#fff"/>
        {i<4 && <path d={`M${222+i*236},80 L${240+i*236},80`} stroke="#8a95a0" strokeWidth="1.3" markerEnd="url(#ah)"/>}
      </g>
    ))}
    <path d="M1120,130 C1120,176 600,190 118,176 C60,170 60,148 60,134" fill="none" stroke="#5b3fb8" strokeWidth="1.3"
      strokeDasharray="4 3" markerEnd="url(#ah)"/>
    <text x="470" y="196" className="flx-s" style={{fill:"#5b3fb8"}}>the next plan opens with a better first proposal — which is the whole behaviour change: operator to analyst</text>
    <text x="8" y="20" className="flx-t">HOW THE DESK GETS BETTER WITH USE</text>
  </svg>
);

/* ------------------------------------------------------------------ screen */
const BP_TABS = [["phases","Phase flow"],["flow","Flow architecture"],["personas","Persona swimlane"],
  ["agents","Agent map"],["lineage","Artifact lineage"],["learn","Learning loop"],["open","Open questions"]];

const Blueprint = ({initialTab}) => {
  const [tab, setTab] = useState(
    BP_TABS.some(([k]) => k === initialTab) ? initialTab : "phases");
  const [agent, setAgent] = useState(null);
  return (
    <div className="pad">
      <div className="row" style={{marginBottom:14, alignItems:"flex-start"}}>
        <div>
          <h2 style={{fontSize:17}}>How the desk works</h2>
          <div className="muted" style={{maxWidth:760, marginTop:4}}>
            The workflow, the people, the artifacts and the agents. Everything the prototype does downstream is an
            instance of one of these five phases. Derived from the Digital Media Planning baseline (tenets T1–T9),
            the Intake requirements and the Discovery / Strategize / Analyze requirements.
          </div>
        </div>
      </div>

      <div className="tabs" style={{marginBottom:14}}>
        {BP_TABS.map(([k,l])=>
          <button key={k} className={tab===k?"on":""} onClick={()=>setTab(k)}>{l}</button>)}
      </div>

      {tab==="flow" && <FlowArchTab/>}

      {tab==="phases" && <>
        <Card title="Planning phases" sub="Read the loop in the middle: Discovery → Strategize → Analyze runs as many times as it takes.">
          <PhaseLoopSvg/>
        </Card>
        <div className="g3" style={{marginTop:14}}>
          {PHASE_COLS.map((p,i)=>(
            <Card key={i} title={p.n} sub={["Planner","Planner","Planner","Planner","P&I"][i] + " owns"}>
              <div className="tiny muted" style={{marginBottom:8}}>{p.q}</div>
              <div className="kv tiny">
                <dt>Produces</dt><dd>{ARTIFACTS[i]}</dd>
                <dt>Done when</dt><dd>{[
                  "We know enough that planning won't be invalidated by what's missing.",
                  "The planner accepts the ranked list and its targeting.",
                  "The planner saves a version they'd defend.",
                  "One version is chosen.",
                  "Every line has a decision.",
                ][i]}</dd>
              </div>
            </Card>
          ))}
        </div>
      </>}

      {tab==="personas" && <>
        <Card title="Who does what, phase by phase" sub="Two primary personas. The other two are read and voice, not design targets in v0.">
          <SwimlaneSvg/>
        </Card>
        <div className="g2" style={{marginTop:14}}>
          <Card title="The behaviour change this is all for">
            <div className="col" style={{gap:12}}>
              <div>
                <div className="row" style={{gap:8, marginBottom:4}}><Chip c="b">PLANNER</Chip><span className="tiny dim">primary</span></div>
                <div style={{fontSize:12.5}}>
                  From an <b>operator</b> assembling a plan out of tribal knowledge and a series of manual steps,
                  to an <b>analyst</b> adjudicating a justified proposal. Every screen in this prototype should be
                  readable as a step toward that.
                </div>
              </div>
              <div className="hr"/>
              <div>
                <div className="row" style={{gap:8, marginBottom:4}}><Chip c="a">P&amp;I APPROVER</Chip><span className="tiny dim">primary</span></div>
                <div style={{fontSize:12.5}}>
                  From <b>reacting</b> to a plan that arrives, to <b>reviewing it against a position they already
                  stated</b> — line by line, seeing what each line does to inventory before they approve.
                </div>
              </div>
            </div>
          </Card>
          <Card title="Tenets the surfaces have to obey">
            <table className="tb">
              <tbody>
                {[["T1","Desk mirror, not personal mirror"],["T2","Context attaches to the plan, not the user"],
                  ["T3","Briefs are read-only derived views"],["T4","Evidence is superseded, never deleted"],
                  ["T5","No information without rationale and evidence"],["T6","Justify, then override"],
                  ["T7","The optimiser is not negotiated with"],["T8","Not branded as AI"],
                  ["T9","Approvals bind to a version, not to 'the plan'"]].map(([k,v])=>
                  <tr key={k}><td style={{width:34}}><Chip>{k}</Chip></td><td>{v}</td></tr>)}
              </tbody>
            </table>
          </Card>
        </div>
      </>}

      {tab==="agents" && <>
        <div className="banner b" style={{marginBottom:14}}>
          <span className="bi">Note</span>
          <div>{AGENTS.length} agents, named for the desk job each does rather than for the technique. None of them
            decides anything — each produces evidence, a proposal or a consequence, and a human adjudicates. The
            orchestrator is the only one that can hold the plan at all, and only when something the next phase needs
            is missing — never because it judged the work weak. Click one to read its contract.</div>
        </div>
        {["Intake","Discovery","Strategize","Analyze","Approval","All"].map(ph => {
          const list = AGENTS.filter(a => a.phase === ph);
          if (!list.length) return null;
          return (
            <div key={ph} style={{marginBottom:14}}>
              <div className="sec-title" style={{marginBottom:7}}>{ph === "All" ? "Runs in every phase" : ph}</div>
              <div className="g3">
                {list.map(a=>(
                  <button key={a.id} className="card" style={{textAlign:"left"}} onClick={()=>setAgent(a)}>
                    <div className="card-b">
                      <div className="row" style={{marginBottom:6}}>
                        <span className="chip n">{a.id}</span>
                        <b style={{fontSize:13}}>{a.name}</b>
                      </div>
                      <div className="tiny muted" style={{lineHeight:1.5}}>{a.role}</div>
                      <div className="tiny" style={{marginTop:8, color:"var(--bad)"}}>Guardrail · {a.guard}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
        {agent && <Modal title={agent.name + " agent"} sub={agent.id + " · " + agent.phase} onClose={()=>setAgent(null)}>
          <div className="col" style={{gap:14}}>
            <div><div className="lbl">What it does</div><div>{agent.role}</div></div>
            <div className="g2">
              <div><div className="lbl">Reads</div><ul style={{margin:0, paddingLeft:16}}>{agent.inputs.map((i,x)=><li key={x}>{i}</li>)}</ul></div>
              <div><div className="lbl">Writes</div><ul style={{margin:0, paddingLeft:16}}>{agent.outputs.map((i,x)=><li key={x}>{i}</li>)}</ul></div>
            </div>
            <div className="banner r"><span className="bi">Guardrail</span><div>{agent.guard}</div></div>
            <div className="banner b"><span className="bi">Learns from</span><div>{agent.learns}</div></div>
          </div>
        </Modal>}
      </>}

      {tab==="lineage" && <>
        <Card title="Evidence in, briefs out" sub="Nobody writes a brief. Every brief is a view over the evidence store, and it re-derives when the store changes.">
          <LineageSvg/>
        </Card>
        <div className="g2" style={{marginTop:14}}>
          <Card title="The provenance ladder" sub="Strongest to weakest. The two inferred classes are proposals, not facts.">
            <table className="tb">
              <tbody>
                {["stated","clarified","hist","cohort"].map(k=>(
                  <tr key={k}><td style={{width:130}}><ProvChip cls={k}/></td>
                    <td className="tiny">{{
                      stated:"Literally present in the RFP or the Salesforce opportunity. Hard constraint unless traded explicitly.",
                      clarified:"Said by the client after the RFP, through the AE. Later and more specific usually wins a contradiction.",
                      hist:"Derived from this advertiser's own 12-month buying record. Names the deals behind it. Stays visibly inferred even after the planner accepts it.",
                      cohort:"Derived from similar advertisers because this one has no record. Weakest class. [OQ-6] the similarity rule itself is undefined.",
                    }[k]}</td></tr>
                ))}
                <tr><td><Chip c="r">GAP</Chip></td>
                  <td className="tiny">A detail the plan requires that the evidence cannot supply. Surfaced with a recommendation, never as a blank, a zero, a default or a bare question.</td></tr>
              </tbody>
            </table>
          </Card>
          <Card title="Versioning rules">
            <div className="col tiny" style={{gap:9}}>
              {[
                ["Immutable","A saved plan version never changes. A new allocation produces a further version, it does not replace the saved one (T4)."],
                ["Bound","Each plan version binds exactly one strategy brief version and one plan brief."],
                ["Forkable","[NEW] A version can branch a new line of exploration without a Discovery round trip — which means versions have parents, not a flat list."],
                ["Lapsing approval","A late clarification produces a new brief version and the prior approval lapses. A brief is never final, only approved-as-of-a-version."],
                ["Blocked commit","A version cannot be committed while an override is unjustified or an inferred value is unconfirmed (T5, T6)."],
              ].map(([t,d])=><div key={t}><b>{t}.</b> <span className="muted">{d}</span></div>)}
            </div>
          </Card>
        </div>
      </>}

      {tab==="learn" && <>
        <Card title="How the desk gets better with use">
          <LearnLoopSvg/>
        </Card>
        <div className="g2" style={{marginTop:14}}>
          <Card title="Feedback types the squad captures" sub="From the Fast Prototyping operating model — weight differs by type.">
            <table className="tb">
              <thead><tr><th>Type</th><th>Definition</th><th>Weight</th></tr></thead>
              <tbody>
                <tr><td>Observation</td><td className="tiny">What happened, from memory, dependent on who was watching.</td><td><Chip>Low</Chip></td></tr>
                <tr><td>Report</td><td className="tiny">What the user actually said.</td><td><Chip c="g">High</Chip></td></tr>
                <tr><td>Interpretation</td><td className="tiny">What we concluded. Must name the report it came from.</td><td><Chip c="g">High</Chip></td></tr>
                <tr><td>Learning</td><td className="tiny">What carries forward as a settled decision, and updates the cumulative PRD.</td><td><Chip c="g">High</Chip></td></tr>
              </tbody>
            </table>
          </Card>
          <Card title="What the system itself learns in-product">
            <div className="col tiny" style={{gap:9}}>
              {[["Ranking criteria weights","A planner who consistently demotes a product type against a stated reason reweights that criterion for this advertiser, then for the cohort."],
                ["Eligibility flags","A product rejected with a reason enters the next list flagged rather than removed, so the exclusion stays legible."],
                ["Recommendation phrasing","A rejected recommendation is never re-offered unchanged."],
                ["Hardening soft constraints","A P&I disapproval reason that recurs becomes a soft constraint on the next plan, with its origin attached."],
                ["Gap patterns","Gaps a planner always fills the same way get offered as a single accept rather than four fields."]].map(([t,d])=>
                <div key={t}><b>{t}.</b> <span className="muted">{d}</span></div>)}
            </div>
          </Card>
        </div>
      </>}

      {tab==="open" && (
        <Card title="Open questions carried into this prototype" sub="Each is load-bearing. Where the prototype had to choose, it says so on the surface.">
          <table className="tb">
            <thead><tr><th style={{width:60}}>ID</th><th>Question</th><th style={{width:300}}>What this prototype does</th><th style={{width:90}}>Status</th></tr></thead>
            <tbody>
              {[
                ["OQ-1","May the planner give the optimiser soft guidance before it runs?","Levers are declared before the run only: order, targeting, soft constraints with reasons. Nothing is adjustable mid-solve.","OPEN"],
                ["OQ-2","What is the definition of a good plan?","A six-line rubric is proposed and labelled [PROPOSED] on the Analyze screen. Scores each version in isolation.","OPEN"],
                ["OQ-3","Does the product present as AI-assisted?","No assistant persona and no narrator. Help surfaces at the point of need, shaped by the task.","OPEN"],
                ["OQ-4","Digital only, or linear and digital?","Answered digital-only, but this prototype carries both so the unified case can be seen. Linear lines are marked.","ANSWERED"],
                ["OQ-5","What carries forward between iterations?","Overrides and justifications, rejections and reasons, targeting already tested with its price and avails consequence.","ANSWERED"],
                ["OQ-6","What makes an advertiser similar enough for cohort inference?","The cohort set is shown on every cohort recommendation so the planner can judge the match themselves.","OPEN"],
                ["OQ-7","What are the criteria for the intake sufficiency gate?","Every material gap must be received or inferred, and both accepted, before intake can be approved.","ANSWERED"],
                ["OQ-8","Supersede silently, or surface the contradiction?","Surfaced, with a recommendation and its basis. The planner adjudicates.","ANSWERED"],
                ["OQ-9","Is a planner revision treated like a P&I-compelled rework?","Same path, same levers. The difference is that the rework carries P&I's reasons with it.","ANSWERED"],
                ["OQ-10","Who owns intake?","The planner, as the only approver. AE and P&I are voices in the evidence, not approval steps.","ANSWERED"],
                ["OQ-11","Does the Ad Ops reader persona pull Learning back into scope?","No. Post-flight is out of scope; Ad Ops is a reader of the same artifacts.","ANSWERED"],
              ].map(([id,q,d,s])=>(
                <tr key={id}><td><Chip c={s==="OPEN"?"a":"g"}>{id}</Chip></td><td>{q}</td>
                  <td className="tiny muted">{d}</td><td><span className={"chip " + (s==="OPEN"?"a":"g")}>{s}</span></td></tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
};
