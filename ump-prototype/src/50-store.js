/* =============================================================================
   50-store.js — plan state.
   Context attaches to the plan, not to the user (T2). Everything a planner does
   lands here as a recorded action with its reason, and every brief is derived
   from this, never edited.
   ============================================================================= */

/* The system's own first proposal, computed once, kept forever so the planner's
   changes can always be read beside it (Discovery §4). */
const SYSTEM_RANKED = buildRanking({}, SEED_SIGNALS);
const SYSTEM_ORDER  = SYSTEM_RANKED.map(r => r.pid);
const SYSTEM_RANK   = Object.fromEntries(SYSTEM_RANKED.map((r,i) => [r.pid, i+1]));
const DEFAULT_ON    = Object.fromEntries(SYSTEM_RANKED.map((r,i) => [r.pid, i < 12]));

const PHASES = [
  { k:"intake",     n:"Intake",              owner:"Planner", q:"What does the advertiser want, and what do we not know?" },
  { k:"discovery",  n:"Discovery",           owner:"Planner", q:"Which products are eligible, in what order, and why?" },
  { k:"strategize", n:"Strategize & iterate",owner:"Planner", q:"Given that list, what is the allocation?" },
  { k:"analyze",    n:"Analyze",             owner:"Planner", q:"Which of these versions do we put forward?" },
  { k:"approval",   n:"Approval",            owner:"P&I",     q:"Does this plan agree with our inventory and yield position?" },
];

/* Everything that had already happened to this deal before the planner sat down.
   Kept as a module constant so the worked example can reset to it. */
const BASE_TIMELINE = [
  { at:"2026-05-04 09:12", kind:"sys",  who:"Salesforce", text:"Opportunity OPP-2026-04872 synced. 12 stated records written." },
  { at:"2026-05-04 09:22", kind:"sys",  who:"Context", text:"12-month advertiser lookback complete — 4 plans, 61 lines. 5 inferences proposed." },
  { at:"2026-05-05 17:00", kind:"warn", who:"System", text:"No advertiser-specific P&I position returned. Absence recorded against G04." },
  { at:"2026-05-11 16:40", kind:"sys",  who:"Marcus Vieira (AE)", text:"Client clarification on linear tolerance recorded. Brief re-derived to v2." },
  { at:"2026-05-12 11:05", kind:"sys",  who:"Marcus Vieira (AE)", text:"CPM ceiling and frequency cap recorded. Brief re-derived to v3." },
  { at:"2026-05-13 10:30", kind:"sys",  who:"Research", text:"Competitive read returned on planner request. 6 category advertisers." },
];

function usePlanStore(){
  const [st, setSt] = useState(() => ({
    phase: "intake",
    /* intake */
    briefVersion: 3,
    gapDecisions: {},
    contraDecisions: {},
    corrections: [],
    intakeApproved: null,          // { version, at }
    researchRun: false,
    /* discovery */
    order: SYSTEM_ORDER.slice(),
    on: { ...DEFAULT_ON },
    customMap: {},
    rankJust: {},                  // pid -> reason for a move / add / remove / retarget
    strategyAccepted: null,        // { version, at }
    strategyVersion: 1,
    /* strategize */
    overrides: {},                 // pid -> spend
    justifications: {},            // pid -> reason
    lastRun: null,
    /* analyze */
    versions: [],
    committed: null,
    commitNote: null,              // why this version, read first by P&I
    /* approval */
    decisions: {},                 // pid -> { d, reason, at }
    sentToPI: false,
    /* learning */
    signals: SEED_SIGNALS.map(s => ({...s})),
    /* audit */
    timeline: BASE_TIMELINE.slice(),
  }));

  const up = useCallback((patch) => setSt(s => ({...s, ...(typeof patch === "function" ? patch(s) : patch)})), []);

  const log = useCallback((kind, text, reason) => setSt(s => ({...s,
    timeline: [...s.timeline, { at: NOW(), kind, who: kind === "pi" ? "Rachel Levine (P&I)" : "You", text, reason }]
  })), []);

  /* A planner correction is a record in the evidence store, not an edit to the
     brief. The brief re-derives over it (T3). */
  const correct = useCallback((attr, value, reason) => setSt(s => ({...s,
    briefVersion: s.briefVersion + 1,
    corrections: [...s.corrections, { id: uid("c"), attr, value, reason, at: NOW(), cls:"planner" }],
    intakeApproved: null,
    timeline: [...s.timeline, { at: NOW(), kind:"edit", who:"You",
      text:`Correction recorded on “${attr}”. Brief re-derived to v${s.briefVersion + 1}; the prior approval lapses.`, reason }],
  })), []);

  /* A learned signal, visible and reversible. */
  const learn = useCallback((sig) => setSt(s => ({...s,
    signals: [...s.signals, { id: uid("S"), when: NOW().slice(0,10), on:true, strength:"new", ...sig }],
  })), []);

  const seed = useCallback((phase) => setSt(s => ({ ...seedState({
    ...s, gapDecisions:{}, contraDecisions:{}, corrections:[], decisions:{}, versions:[], committed:null,
    overrides:{}, justifications:{}, customMap:{}, rankJust:{}, order:SYSTEM_ORDER.slice(), on:{...DEFAULT_ON},
    briefVersion:3, strategyVersion:1, researchRun:false, intakeApproved:null, strategyAccepted:null,
    lastRun:null, sentToPI:false, commitNote:null, timeline:BASE_TIMELINE.slice(),
  }, phase), phase })), []);

  return { st, up, log, correct, learn, seed, setSt };
}

/* -----------------------------------------------------------------------------
   A worked example. Replays the decisions a planner would have made, so a
   showcase can open on any phase without walking the whole flow first.
   Every seeded action carries the reason it would have carried live.
--------------------------------------------------------------------------------*/
const SEED_REASONS = {
  P01: "Reach is the KPI and this is the only unit in the portfolio that buys light-TV households at scale. Efficiency ranked it 3rd; the brief is not asking for efficiency, it is asking for incremental reach before the pack change. I want it second so the solver weights it properly.",
  P06: "Viewability at 79% breaches the 80% floor the RFP states. Excluding UGC-adjacent placements clears it at 85% and costs 5% on CPM and 22% of avails — worth it, because a breach here fails at approval anyway.",
  P03: "Locking the genre to home and lifestyle is the whole contextual argument for this product on a laundry brief. It halves avails, which is fine — we were never going to buy the full run.",
};

function seedState(base, phase){
  const s = { ...base };
  const at = "2026-09-09 09:40";
  const order = ["intake","discovery","strategize","analyze","approval"].indexOf(phase);

  /* "Load up to X" seeds everything behind X and leaves X to be done. Intake is
     therefore a clean desk — its whole content is the adjudication nobody has
     made yet. */
  if (order <= 0) return s;

  /* Intake — every material gap resolved, every material contradiction adjudicated */
  GAPS.forEach(g => {
    s.gapDecisions[g.id] = { status:"accepted", value:g.rec, reason:
      g.id==="G01" ? "The cohort is close enough on spend band and category, and it matches what this advertiser did globally last year. Accepting as a proposal, not as a fact."
      : g.id==="G02" ? "Front-loading is right for a pre-launch reach build. 60/40 rather than the 58% median because the pack change lands in week 9, not week 10."
      : g.id==="G04" ? "Proceeding on the standing Q3 cards and recording that nothing advertiser-specific was returned, so the absence is on the record at approval."
      : "Accepting the recommendation; immaterial to allocation.",
      at, cls:g.wouldCarry,
      why:`Accepted as a proposal, and it stays visibly inferred. Basis: ${g.basis}` };
  });
  CONTRADICTIONS.forEach(c => {
    s.contraDecisions[c.id] = { choice:"Recommendation adopted", at, reason:
      c.id==="C01" ? "Treating 45% as a ceiling and planning to 32%. The clarification is later and more specific, and the RFP language is directional rather than a constraint."
      : c.id==="C02" ? "Not a contradiction on the same attribute — recording the ceiling as the hard constraint and the historical CPM as the benchmark P&I reads against."
      : "Immaterial to allocation. Flagging it at share rather than blocking planning on it." };
  });
  s.briefVersion = 4;
  s.researchRun = true;
  s.timeline = [...s.timeline,
    { at, kind:"ok", who:"You", text:"5 gaps resolved and 3 contradictions adjudicated. Brief re-derived to v4." },
    { at, kind:"ok", who:"You", text:"Intake brief v4 approved. Approval binds to this version, not to the plan." }];
  s.intakeApproved = { version:4, at };
  if (order <= 1) return s;

  /* Discovery — one promotion, two targeting customisations, all justified */
  s.customMap = { P06:["ugc"], P03:["genre"] };
  s.rankJust = { ...SEED_REASONS };
  const ranked = buildRanking(s.customMap, s.signals);
  const ord = ranked.map(r=>r.pid);
  const i = ord.indexOf("P01");
  ord.splice(i,1); ord.splice(1,0,"P01");
  s.order = ord;
  s.on = Object.fromEntries(ord.map((pid,ix)=>[pid, ix < 12]));
  s.on.P21 = true;                       // APAC needs at least one product or its envelope has nowhere to go
  s.rankJust.P21 = "APAC has 5% of the budget and nothing in the list, so the envelope had nowhere to go. Adding the only APAC product with an ad tier in market for this flight.";
  s.strategyVersion = 4;
  s.timeline = [...s.timeline,
    { at, kind:"edit", who:"You", text:"HBO Max premium CTV moved to position 2 (system had it at 3).", reason:SEED_REASONS.P01 },
    { at, kind:"edit", who:"You", text:"Targeting customised on Bleacher Report and discovery+.", reason:SEED_REASONS.P06 },
    { at, kind:"ok", who:"You", text:"Strategy brief v4 accepted — 13 products, in this order, with this targeting." }];
  s.strategyAccepted = { at };

  /* The optimiser has already answered the accepted list — that proposal is what
     the planner walks into Strategize to adjudicate. */
  s.lastRun = at;
  s.timeline = [...s.timeline,
    { at, kind:"sys", who:"Optimiser", text:"Solved from 13 accepted products. 13 lines, 0 held out." }];
  if (order <= 2) return s;

  /* Strategize — a justified override, then two saved versions */
  const rows = buildRanking(s.customMap, s.signals);
  const byPid = Object.fromEntries(rows.map(r=>[r.pid,r]));
  const ordered = s.order.map(pid=>({ ...byPid[pid], on: !!s.on[pid] }));
  const baseRes = optimise(ordered, {});
  const sysSpend = Object.fromEntries(baseRes.lines.map(l=>[l.pid,l.spend]));

  const mk = (over, just, name, note) => {
    const res = optimise(ordered, { overrides:over, systemSpend:sysSpend });
    const cons = checkConstraints(res, ordered);
    const rub  = scorePlan(res, ordered, over, just, cons);
    return { name, note, at, parent:null, strategyVersion:s.strategyVersion, cons, rubric:rub,
      overrides:{...over}, justifications:{...just},
      order:s.order.slice(), on:{...s.on}, customMap:JSON.parse(JSON.stringify(s.customMap)),
      lines: res.lines.map(l=>({ pid:l.pid, name:l.p.name, region:l.region, medium:l.p.medium, brand:l.p.brand,
        spend:l.spend, cpm:l.cpm, impsK:l.impsK, comp:l.comp, availUse:l.availUse,
        overridden:l.overridden, systemSpend:l.systemSpend, floorCpm:l.p.floorCpm })),
      roll: { spend:res.spend, impsK:res.impsK, reach1:res.reach1, reach3:res.reach3, avgFreq:res.avgFreq,
        blendedCpm:res.blendedCpm, digCpm:res.digCpm, linearPct:res.linearPct, hhi:res.hhi, byRegion:res.byRegion } };
  };
  const ovr = { P01: Math.round((sysSpend.P01 || 1_200_000) * 2.4) };
  const just = { P01: "The solver gave this 14% of the plan on price. HBO Max premium CTV is where the light-TV household sits and where the brand wants to be seen before the pack change, and the client has said so in the call notes twice. I know what this costs: modelled 3+ goes backwards and blended CPM goes up. I am buying context and attention, and I will defend it on that, not on efficiency." };
  s.versions = [
    Object.assign(mk({}, {}, "Balanced global", "The optimiser's own answer to the accepted list. Nothing overridden — the cleanest version to defend."), {id:"PV-A"}),
    Object.assign(mk(ovr, just, "Premium-weighted", "HBO Max premium CTV weighted up on brand judgement, at a cost in modelled reach and blended CPM."), {id:"PV-B"}),
  ];
  s.overrides = ovr; s.justifications = just;
  s.timeline = [...s.timeline,
    { at, kind:"ok", who:"You", text:"PV-A saved — immutable from here." },
    { at, kind:"edit", who:"You", text:"HBO Max premium CTV overridden upward. Re-solved from the overridden value.", reason:just.P01 },
    { at, kind:"ok", who:"You", text:"PV-B saved." }];
  if (order <= 3) return s;

  /* Analyze — one version committed */
  s.commitNote = "The two versions score within half a point of each other, so the rubric is not choosing for me. PV-B misses the 20% 3+ reach goal by 2.3 points and costs $1.30 more on blended CPM, and I am committing it anyway: the weight sits on HBO Max premium CTV, where this client has twice said in call notes they want to be seen before the pack change. I am trading measured reach for context and I will defend that trade.";
  s.committed = "PV-B"; s.sentToPI = true;
  s.timeline = [...s.timeline, { at, kind:"ok", who:"You", text:"PV-B committed and shared for P&I approval.",
    reason:s.commitNote }];

  /* Approval — P&I has decided some but not all lines */
  const v = s.versions[1];
  const dec = (pid, d, reason, weight) => { const l = v.lines.find(x=>x.pid===pid);
    if (l) s.decisions[pid] = { d, reason, weight, at, spend:l.spend }; };
  dec("P03","approve","On the Q3 push list and the genre lock makes the contextual case. Clears floor by a comfortable margin.");
  dec("P01","condition","A third of the plan on one product is more concentration than I would normally sign, and the planner has argued for it, so I will take the weight — but not at any clearance. Holds at $42 or above for the whole flight. If the agency pushes back on CPM, this line comes down rather than clearing at $38.");
  dec("P09","disapprove","41% of the flight's sellable daytime avails at $9.20 — the lowest clearance in the US linear book. The composition is the best in the plan, so I understand why the ranking likes it, but I am not committing that much daytime to one advertiser at that price in Q3. Take it to no more than 20% of avails and put the weight on HGTV prime: composition 0.73 against 0.77, and it clears at $15.40.", true);
  s.timeline = [...s.timeline,
    { at, kind:"pi", who:"Rachel Levine (P&I)", text:"3 of 13 lines decided so far." }];
  return s;
}

/* --------------------------------------------------------- derived ranking */
function useRanking(st){
  return useMemo(() => {
    const rows = buildRanking(st.customMap, st.signals);
    const byPid = Object.fromEntries(rows.map(r => [r.pid, r]));
    const ordered = st.order.map(pid => byPid[pid]).filter(Boolean);
    return ordered.map((r,i) => ({
      ...r,
      rank: i + 1,
      sysRank: SYSTEM_RANK[r.pid],
      moved: (i + 1) !== SYSTEM_RANK[r.pid],
      delta: SYSTEM_RANK[r.pid] - (i + 1),
      on: st.on[r.pid] !== false && st.on[r.pid] !== undefined ? true : !!st.on[r.pid],
      just: st.rankJust[r.pid] || null,
    }));
  }, [st.customMap, st.signals, st.order, st.on, st.rankJust]);
}

/* -------------------------------------------------------------- timeline UI */
const Timeline = ({items, max}) => {
  const list = max ? items.slice(-max).reverse() : items.slice().reverse();
  return (
    <div className="tl">
      {list.map((e,i)=>(
        <div key={i} className={"tl-i " + (e.kind==="ok"?"ok":e.kind==="no"||e.kind==="warn"?"no":e.kind==="edit"?"ai":"")}>
          <div className="row" style={{gap:7, alignItems:"baseline"}}>
            <span className="mono dim" style={{fontSize:10}}>{e.at}</span>
            <span className="tiny" style={{fontWeight:600}}>{e.who}</span>
          </div>
          <div className="tiny" style={{marginTop:1}}>{e.text}</div>
          {e.reason && <div className="tiny muted" style={{marginTop:3, paddingLeft:8, borderLeft:"2px solid var(--line)"}}>“{e.reason}”</div>}
        </div>
      ))}
    </div>
  );
};

/* -------------------------------------------------------- phase progress bar */
const PhaseRail = ({phase, onGo, st}) => {
  const idx = PHASES.findIndex(p => p.k === phase);
  const doneMap = {
    intake: !!st.intakeApproved,
    discovery: !!st.strategyAccepted,
    strategize: st.versions.length > 0,
    analyze: !!st.committed,
    approval: Object.keys(st.decisions).length > 0,
  };
  return (
    <div className="phaserail">
      {PHASES.map((p,i)=>(
        <button key={p.k} className={"phasestep " + (p.k===phase ? "cur" : doneMap[p.k] ? "done" : "")}
          onClick={()=>onGo(p.k)} title={p.q}>
          <div className="pl">{doneMap[p.k] && p.k!==phase ? "✓ " : ""}Phase {i+1} · {p.owner}</div>
          <div className="pn">{p.n}</div>
          <div className="po">{{
            intake: st.intakeApproved ? `Brief v${st.intakeApproved.version} approved` : `Brief v${st.briefVersion} · ${GAPS.filter(g=>g.material && !st.gapDecisions[g.id]).length} material gaps open`,
            discovery: st.strategyAccepted ? `Strategy brief v${st.strategyVersion} accepted` : `${Object.values(st.on).filter(Boolean).length} products in the list`,
            strategize: st.versions.length ? `${st.versions.length} version${st.versions.length>1?"s":""} saved`
                        : st.lastRun ? "solved · nothing saved yet" : "not run",
            analyze: st.committed ? `${st.committed} committed` : "nothing committed",
            approval: st.sentToPI ? `${Object.keys(st.decisions).length} of ${(st.versions.find(v=>v.id===st.committed)||{lines:[]}).lines.length} lines decided` : "not shared",
          }[p.k]}</div>
        </button>
      ))}
    </div>
  );
};
