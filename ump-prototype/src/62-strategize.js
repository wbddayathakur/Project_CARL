/* =============================================================================
   62-strategize.js — Strategize & iterate.
   Everything the planner wants to influence is declared before the run. Nothing
   is adjusted while the solver runs. An override is re-solved from, not argued
   with (T7).
   ============================================================================= */
const Strategize = ({S}) => {
  const { st, up, log } = S;
  const toast = useToast();
  const ranking = useRanking(st);
  const [running, setRunning] = useState(false);
  const [ran, setRan] = useState(false);
  const [ovr, setOvr] = useState(null);          // { line, value }
  const [tab, setTab] = useState("alloc");
  const [saveOpen, setSaveOpen] = useState(false);

  const locked = useMemo(() => {
    const m = {};
    Object.entries(st.decisions).forEach(([pid,d]) => { if (d.d === "approve") m[pid] = d.spend; });
    return m;
  }, [st.decisions]);

  /* the system's own answer, kept so overrides can always be read beside it */
  const base = useMemo(() => optimise(ranking, { locked }), [ranking, locked]);
  const systemSpend = useMemo(() => Object.fromEntries(base.lines.map(l=>[l.pid, l.spend])), [base]);
  const res  = useMemo(() => optimise(ranking, { overrides: st.overrides, locked, systemSpend }),
                       [ranking, st.overrides, locked, systemSpend]);
  const cons = useMemo(() => checkConstraints(res, ranking), [res, ranking]);
  const rub  = useMemo(() => scorePlan(res, ranking, st.overrides, st.justifications, cons), [res, ranking, st, cons]);

  const unjustified = Object.keys(st.overrides).filter(k => (st.justifications[k]||"").trim().length < 25);
  const gate = useMemo(() => evaluateGate("strategize", st, {res, cons, ranking}), [st, res, cons, ranking]);

  const run = () => {
    setRunning(true);
    setTimeout(() => { setRunning(false); setRan(true);
      up({ lastRun: NOW() });
      log("sys", `Optimiser solved from ${ranking.filter(r=>r.on).length} accepted products. ${res.lines.length} lines, ${res.dropped.length} held out, ${res.unallocated.length} envelope issue${res.unallocated.length===1?"":"s"}.`);
      toast("Solved — " + res.lines.length + " lines");
    }, 900);
  };

  const applyOverride = (line, value, reason) => {
    up(s => ({ overrides: {...s.overrides, [line.pid]: value},
               justifications: {...s.justifications, [line.pid]: reason} }));
    log("edit", `${line.p.name} overridden from ${money(line.systemSpend)} to ${money(value)}. Re-solved from the overridden value; the rest of the ${line.region} envelope redistributes.`, reason);
    setOvr(null);
    toast("Override recorded and re-solved");
  };

  const saveVersion = (name, note) => {
    const id = "PV-" + String.fromCharCode(65 + st.versions.length);
    up(s => ({ versions: [...s.versions, {
      id, name, note, at: NOW(), parent: null,
      strategyVersion: s.strategyVersion,
      lines: res.lines.map(l=>({ pid:l.pid, name:l.p.name, region:l.region, medium:l.p.medium, brand:l.p.brand,
        spend:l.spend, cpm:l.cpm, impsK:l.impsK, comp:l.comp, availUse:l.availUse,
        overridden:l.overridden, systemSpend:l.systemSpend, floorCpm:l.p.floorCpm,
        /* the forecast class the line rests on, and its derivation */
        fidelity:l.fidelity, umpPid:l.umpPid, forecastRunAt:l.forecastRunAt,
        indicativeK:l.indicativeK, constrainedK:l.constrainedK, waterfall:l.waterfall, custom:l.custom })),
      roll: { spend:res.spend, impsK:res.impsK, reach1:res.reach1, reach3:res.reach3, avgFreq:res.avgFreq,
              blendedCpm:res.blendedCpm, digCpm:res.digCpm, linearPct:res.linearPct, hhi:res.hhi, byRegion:res.byRegion },
      rubric: rub, cons,
      overrides: {...s.overrides}, justifications: {...s.justifications},
      order: s.order.slice(), on: {...s.on}, customMap: JSON.parse(JSON.stringify(s.customMap)),
    }], phase:"analyze" }));
    log("ok", `Plan version ${id} saved — immutable from here. Binds strategy brief v${st.strategyVersion}.`, note);
    setSaveOpen(false);
    toast(id + " saved");
  };

  const cols = [
    { key:"rank", label:"#", w:36, align:"c", get:l=>l.rank },
    { key:"name", label:"Product / package", w:270, get:l=>l.p.name, cell:l=>(
      <span className="row" style={{gap:6}}><span className="dot" style={{background:BRAND_COLOR[l.p.brand]}}/>{l.p.name}</span>) },
    { key:"region", label:"Region", w:60, get:l=>l.region },
    { key:"medium", label:"Medium", w:62, get:l=>l.p.medium,
      cell:l=><Chip c={l.p.medium==="Digital"?"b":"a"}>{l.p.medium}</Chip> },
    { key:"cpm", label:"CPM", w:64, align:"r", get:l=>cpmf(l.cpm), raw:l=>l.cpm },
    { key:"spend", label:"Net spend", w:104, align:"r", get:l=>money(l.spend), raw:l=>Math.round(l.spend),
      editable:true, cell:l=>(
      <button style={{width:"100%", textAlign:"right"}} onClick={(e)=>{e.stopPropagation(); setOvr({line:l, value:Math.round(l.spend)});}}
        title="Override this allocation — a reason is required">
        <b>{money(l.spend)}</b>{l.overridden && <span style={{color:"var(--violet)"}}> ✎</span>}
        {l.locked && <span style={{color:"var(--good)"}}> 🔒</span>}
      </button>) },
    { key:"share", label:"Share", w:58, align:"r", get:l=>pct(l.spend/res.spend,1), raw:l=>(l.spend/res.spend) },
    { key:"sys", label:"System said", w:104, align:"r", get:l=>money(l.systemSpend), raw:l=>Math.round(l.systemSpend||0),
      cell:l=> l.overridden
        ? <span><span className="strike dim">{money(l.systemSpend)}</span>{" "}
            <span style={{color: l.spend>l.systemSpend?"var(--good)":"var(--bad)"}}>
              {l.spend>l.systemSpend?"+":""}{money(l.spend-l.systemSpend)}</span></span>
        : <span className="dim">—</span> },
    { key:"imps", label:"Impressions", w:96, align:"r", get:l=>imps(l.impsK), raw:l=>Math.round(l.impsK*1000) },
    { key:"comp", label:"In-demo", w:66, align:"r", get:l=>pct(l.comp,0), raw:l=>l.comp },
    { key:"avail", label:"% of avails", w:82, align:"r", get:l=>pct(l.availUse,0), raw:l=>l.availUse,
      cell:l=><span style={{color:l.availUse>0.75?"var(--warn)":"var(--ink)"}}>{pct(l.availUse,0)}</span> },
    { key:"floor", label:"vs floor", w:70, align:"r", get:l=>pctn((l.cpm/l.p.floorCpm-1)*100,0), raw:l=>((l.cpm/l.p.floorCpm-1)*100).toFixed(1),
      cell:l=>{ const d=(l.cpm/l.p.floorCpm-1)*100; return <span style={{color:d<5?"var(--bad)":d>25?"var(--good)":"var(--ink-2)"}}>{d>0?"+":""}{d.toFixed(0)}%</span>; } },
    { key:"just", label:"Justification", w:330, get:l=>st.justifications[l.pid]||"" },
  ];
  const totals = {
    name: `${res.lines.length} lines`,
    spend: money(res.spend), share: pct(res.spend/DEAL.netBudget,1),
    imps: imps(res.impsK), cpm: cpmf(res.blendedCpm),
    comp: pct(res.targetImpsK/Math.max(res.impsK,1),0),
  };

  if (!ran && !st.lastRun && !st.versions.length) return (
    <div className="split">
      <div className="col" style={{gap:14}}>
        <Card title="Declare the levers, then run" sub="Everything the planner wants to influence is declared as an input before the run. Nothing is adjusted while the solver runs.">
          <div className="g2">
            <div>
              <div className="lbl">Accepted list · in this order</div>
              <div className="col" style={{gap:4}}>
                {ranking.filter(r=>r.on).map(r=>(
                  <div key={r.pid} className="row tiny" style={{gap:8}}>
                    <b style={{width:16}}>{r.rank}</b>
                    <span className="dot" style={{background:BRAND_COLOR[r.p.brand]}}/>
                    <span className="grow" style={{whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis"}}>{r.p.name}</span>
                    {r.custom.length>0 && <Chip c="v">{r.custom.length}c</Chip>}
                    {r.moved && <Chip c="v">moved</Chip>}
                    <span className="dim">{cpmf(r.live.cpm)}</span>
                  </div>))}
              </div>
            </div>
            <div>
              <div className="lbl">Constraints entering the solve</div>
              <div className="col" style={{gap:6}}>
                {constraintSet().map(c=>(
                  <div key={c.id} className="row tiny" style={{alignItems:"flex-start", gap:7}}>
                    <Chip c={c.kind==="hard"?"r":"n"}>{c.kind==="hard"?"H":"S"}</Chip>
                    <div><div>{c.label}</div><div className="mini dim">{c.from}</div></div>
                  </div>))}
              </div>
            </div>
          </div>
          <div className="hr"/>
          <div className="row">
            <div className="tiny muted grow">
              The optimiser operates only with the selected products and their customisations. Nothing outside the
              accepted list enters the solve. If you are unhappy with the result you change the Discovery levers and
              re-run — you do not adjust the optimiser.
            </div>
            <Btn c="pri" onClick={run} disabled={running}>
              {running ? <><span className="spin"/> Solving…</> : "Run the optimiser"}</Btn>
          </div>
        </Card>
        <Card title="What it will solve for">
          <div className="statgrid">
            <Stat label="Net working budget" value={money1(DEAL.netBudget)} delta={`${money1(DEAL.grossBudget)} gross − 15%`}/>
            <Stat label="Products in the list" value={ranking.filter(r=>r.on).length} delta={`${ranking.length} eligible`}/>
            <Stat label="Flight" value={FLIGHT.weeks + " weeks"} delta={FLIGHT.label}/>
            <Stat label="Reach goal" value={pct(FRAME.reachGoal3,1) + " at 3+"} delta={`of ${imps(INMARKET_UNIVERSE)} A25-54`}/>
          </div>
        </Card>
      </div>
      <div className="col sticky" style={{gap:14}}>
        <Assist title="Before you run">
          {FRAME.regions.filter(r=>!ranking.some(x=>x.on && x.p.region===r)).length > 0 ? <>
            <b>{FRAME.regions.filter(r=>!ranking.some(x=>x.on && x.p.region===r)).join(", ")}</b> has budget in the
            regional split but no product in the accepted list. The solver will report the envelope as unallocated
            rather than quietly spending it somewhere else.
          </> : <>Every region with budget has at least one product. The solve will fill the top of the order first
            and fall down it — the ranking is preference, not a spend commitment, so expect the tail to get little
            or nothing.</>}
        </Assist>
        <Card title="Levers you have" sub="Discovery exposes the planner's whole means of influence.">
          <div className="col tiny" style={{gap:8}}>
            <div><b>Which products are in the list.</b> <span className="muted">Add, remove, override an exclusion.</span></div>
            <div><b>In what order.</b> <span className="muted">Ranking is how a weight instruction is expressed. There is no direct weight control.</span></div>
            <div><b>With what targeting.</b> <span className="muted">Each customisation moves price and avails, and the consequence is recorded with it.</span></div>
            <div><b>Soft constraints, with a reason.</b> <span className="muted">Expected to originate from P&I, so disapproval-driven changes arrive with their justification attached.</span></div>
          </div>
        </Card>
      </div>
    </div>
  );

  return (
    <div className="split">
      <div className="col" style={{gap:14}}>
        <div className="statgrid">
          <Stat label="Allocated" value={money1(res.spend)} delta={`${pct(res.spend/DEAL.netBudget,1)} of net working`}
            tone={res.spend < DEAL.netBudget*0.98 ? "bad" : null}/>
          <Stat label="Impressions" value={imps(res.impsK)} delta={`${pct(res.targetImpsK/res.impsK,0)} in demo`}/>
          <Stat label="1+ reach" value={pct(res.reach1,1)} delta={`goal ${pct(FRAME.reachGoal1,0)} · ${imps(res.reachedK)} people`}
            tone={res.reach1>=FRAME.reachGoal1?"good":"bad"}/>
          <Stat label="3+ reach" value={pct(res.reach3,1)} delta={`goal ${pct(FRAME.reachGoal3,1)} — the stated KPI`}
            tone={res.reach3>=FRAME.reachGoal3?"good":"bad"}/>
          <Stat label="Avg frequency" value={res.avgFreq.toFixed(1)} delta={`cap ${FRAME.freqCap}/week`}/>
          <Stat label="Blended CPM" value={cpmf(res.blendedCpm)} delta={`digital ${cpmf(res.digCpm)} · ceiling ${cpmf(FRAME.cpmCeiling)}`}/>
        </div>

        <div className="tabs">
          {[["alloc","Allocation"],["cons","Constraint report", cons.filter(c=>!c.ok).length],
            ["shape","Plan shape"],["brief","Plan version brief"]].map(([k,l,n])=>
            <button key={k} className={tab===k?"on":""} onClick={()=>setTab(k)}>{l}
              {n>0 && <span className="ct" style={{background:"var(--bad-soft)", color:"var(--bad)"}}>{n}</span>}</button>)}
        </div>

        {tab==="alloc" && <>
          {res.unallocated.length>0 && res.unallocated.map((u,i)=>(
            <div key={i} className="banner a"><span className="bi">{money(u.amount)} unallocated</span><div>{u.why}</div></div>))}
          {res.dropped.length>0 && res.dropped.map((d,i)=>(
            <div key={i} className="banner r"><span className="bi">Held out of the solve</span>
              <div><b>{d.name}</b> — {d.reason}. {d.fix && <>Applying “{d.fix}” in Discovery clears it.</>}</div></div>))}
          <Card title="Allocation" tight
            sub="Click any Net spend cell to override it. An override is re-solved from, not argued with — the rest of that region's envelope redistributes around it."
            right={<div className="row" style={{gap:6}}>
              {Object.keys(st.overrides).length>0 && <Btn c="sm" onClick={()=>{ up({overrides:{}, justifications:{}});
                log("edit","All overrides cleared. Back to the system allocation."); toast("Overrides cleared"); }}>Clear overrides</Btn>}
              <Btn c="sm" onClick={run}>Re-run</Btn>
            </div>}>
            <XL name="allocation" cols={cols} rows={res.lines} total={totals} height={420}/>
          </Card>
          {Object.keys(st.overrides).length>0 && (
            <Card title="Overrides on this allocation" sub="Each one carries forward into the plan version brief and into the approval package.">
              {Object.entries(st.overrides).map(([pid,v])=>{
                const l = res.lines.find(x=>x.pid===pid);
                const j = st.justifications[pid] || "";
                return (
                  <div key={pid} className="bl">
                    <div className="bk">{l ? l.p.name : pid}</div>
                    <div className="bv">
                      <span className="strike dim">{money(l?.systemSpend)}</span> → <b>{money(v)}</b>
                      <span className="why" style={{color: j.length>=25 ? "var(--ink-2)" : "var(--bad)"}}>
                        {j.length>=25 ? `“${j}”` : "No justification. This version cannot be committed until there is one (T5, T6)."}</span>
                    </div>
                    <Btn c="xs" onClick={()=>setOvr({line:l, value:Math.round(v)})}>Revise</Btn>
                  </div>
                );
              })}
            </Card>
          )}
        </>}

        {tab==="cons" && (
          <Card title="Constraint report" sub="Hard constraints cannot be traded. Soft constraints can be, at a stated cost.">
            <div className="col" style={{gap:9}}>
              {cons.map(c=>(
                <div key={c.id} className="row" style={{alignItems:"flex-start", gap:10}}>
                  <Chip c={c.ok ? "g" : c.kind==="hard" ? "r" : "a"}>{c.ok ? "PASS" : c.kind==="hard" ? "BREACH" : "MISS"}</Chip>
                  <div className="grow"><div style={{fontSize:12.5, fontWeight:500}}>{c.label}</div>
                    <div className="tiny muted">{c.detail}</div></div>
                  <Chip>{c.kind}</Chip>
                </div>
              ))}
            </div>
            <div className="hr"/>
            <div className="g2">
              <div>
                <div className="lbl">Where the money went by region</div>
                {FRAME.regions.map(r=>{
                  const target = DEAL.netBudget*FRAME.regionSplit[r], got = res.byRegion[r]||0;
                  return <div key={r} className="row" style={{marginBottom:6}}>
                    <span className="tiny" style={{width:52}}>{r}</span>
                    <div className="grow"><Bar v={got/target} c={got/target<0.9?"a":"g"}/></div>
                    <span className="tiny dim" style={{width:150, textAlign:"right"}}>
                      {money1(got)} of {money1(target)} ({pct(got/target,0)})</span>
                  </div>;
                })}
              </div>
              <div>
                <div className="lbl">Concentration</div>
                <div className="tiny muted">HHI {res.hhi.toFixed(3)} across {res.lines.length} lines.
                  {res.hhi > 0.20 ? " Concentrated — a single line dominates, which is a delivery risk if it under-clears."
                    : " Reasonably spread; no single line dominates delivery."}</div>
                <div style={{marginTop:10}}>
                  <HBars rows={res.lines.slice(0,6).map(l=>({l:l.p.name.split(" — ")[0], v:l.spend/res.spend*100,
                    c:BRAND_COLOR[l.p.brand]}))} fmt={v=>v.toFixed(1)+"%"}/>
                </div>
              </div>
            </div>
          </Card>
        )}

        {tab==="shape" && (
          <div className="g2">
            <Card title="Linear and digital">
              <div className="row" style={{gap:16}}>
                <Donut size={110} parts={[
                  {l:"Digital", v:res.digSpend, c:"#0b57d0"},
                  {l:"Linear", v:res.linSpend, c:"#e8641a"}]}
                  center={<><b style={{fontSize:15}}>{pct(res.linearPct,0)}</b><span className="mini dim">linear</span></>}/>
                <div className="grow">
                  <HBars rows={[{l:"Digital", v:res.digSpend, c:"#0b57d0"},{l:"Linear", v:res.linSpend, c:"#e8641a"}]} fmt={money1}/>
                  <div className="tiny muted" style={{marginTop:10}}>
                    Target {pct(FRAME.linearTarget,0)}, ceiling {pct(FRAME.linearCeiling,0)} — adjudicated from
                    contradiction C01. {res.linearPct > FRAME.linearTarget + 0.03
                      ? "Above target and inside the ceiling; the reach case for it needs to be in the brief."
                      : "Inside target."}
                  </div>
                </div>
              </div>
            </Card>
            <Card title="Regional split">
              <div className="row" style={{gap:16}}>
                <Donut size={110} parts={FRAME.regions.map(r=>({l:r, v:res.byRegion[r]||0,
                  c:{US:"#0b57d0",EMEA:"#0d7a4e",LATAM:"#e8641a",APAC:"#5b3fb8"}[r]}))}
                  center={<><b style={{fontSize:15}}>{money1(res.spend)}</b><span className="mini dim">allocated</span></>}/>
                <div className="grow"><HBars rows={FRAME.regions.map(r=>({l:r, v:res.byRegion[r]||0,
                  c:{US:"#0b57d0",EMEA:"#0d7a4e",LATAM:"#e8641a",APAC:"#5b3fb8"}[r]}))} fmt={money1}/></div>
              </div>
            </Card>
            <Card title="Flighting" sub={`Front-loaded ${pct(FRAME.frontLoad,0)} into weeks 1–8, per the G02 recommendation`}>
              <FlightStrip frontLoad={FRAME.frontLoad}/>
              <div className="row tiny dim" style={{justifyContent:"space-between", marginTop:5}}>
                <span>W1 · Jun 1</span><span>W9 · pack redesign</span><span>W17 · Sep 27</span>
              </div>
              <div className="tiny muted" style={{marginTop:9}}>
                The objective is a reach build ahead of the pack redesign in week 9. Even weighting would under-deliver
                it, which is why G02 exists.
              </div>
            </Card>
            <Card title="Reach curve" sub="Model, not a guarantee: per-product saturation, then incremental reach with a duplication penalty for same-brand and same-medium overlap.">
              <HBars rows={res.curve.slice(0,8).map(l=>({l:l.p.name.split(" — ")[0], v:l.incReachK/1000,
                c:BRAND_COLOR[l.p.brand]}))} fmt={v=>v.toFixed(1)+"M"}/>
              <div className="tiny muted" style={{marginTop:10}}>
                {imps(res.reachedK)} people reached at least once, {pct(res.reach1,1)} of the {imps(INMARKET_UNIVERSE)}
                {" "}in-market A25-54 universe, at an average of {res.avgFreq.toFixed(1)} exposures.
              </div>
            </Card>
          </div>
        )}

        {tab==="brief" && (
          <div className="brief">
            <div className="row" style={{alignItems:"flex-start"}}>
              <div><h2>Plan version brief</h2>
                <div className="tiny dim" style={{marginTop:3}}>Derived from strategy brief v{st.strategyVersion} + optimiser output + planner overrides · not yet saved</div></div>
              <div style={{flex:1}}/>
              <div className="readonly"><Chip c="o">READ-ONLY</Chip></div>
            </div>
            <h4>What we propose</h4>
            <div className="tiny muted" style={{marginBottom:8}}>
              {money(res.spend)} net across {res.lines.length} lines in {FRAME.regions.filter(r=>res.byRegion[r]>0).length} regions,
              delivering {imps(res.impsK)} impressions and {pct(res.reach1,1)} 1+ reach at {res.avgFreq.toFixed(1)} average
              frequency, against a KPI of {pct(FRAME.reachGoal3,1)} at 3+.
            </div>
            {res.lines.map(l=>(
              <div className="bl" key={l.pid}>
                <div className="bk">{money(l.spend)} · {pct(l.spend/res.spend,1)}</div>
                <div className="bv">{l.p.name}
                  <span className="why">{imps(l.impsK)} impressions at {cpmf(l.cpm)}, {pct(l.comp,0)} in demo,
                    {" "}{pct(l.availUse,0)} of sellable avails. Ranked {l.rank} in the accepted list.</span>
                  {l.overridden && <span className="why" style={{color:"var(--violet)"}}>
                    Overridden from {money(l.systemSpend)}. “{st.justifications[l.pid]}”</span>}
                  {l.locked && <span className="why" style={{color:"var(--good)"}}>Locked — P&I has already approved this line, so the optimiser treats it as a hard constraint.</span>}
                </div>
                <Chip c={l.p.medium==="Digital"?"b":"a"}>{l.p.medium}</Chip>
              </div>
            ))}
            <h4>And why</h4>
            {[["The objective", `Incremental reach against light-TV households. This version reaches ${imps(res.reachedK)} people, ${pct(res.reach1,1)} of the in-market universe, with ${pct(res.reach3,1)} at the 3+ frequency the KPI names.`],
              ["The price position", `Blended ${cpmf(res.blendedCpm)}; digital ${cpmf(res.digCpm)} against the ${cpmf(FRAME.cpmCeiling)} ceiling and the ${cpmf(28.40)} this advertiser has been paying.`],
              ["The seller position", `${pct((res.lines.filter(l=>["P03","P19"].includes(l.pid)).reduce((s,l)=>s+l.spend,0))/res.spend,1)} of the plan sits on P&I's Q3 push list. Every floor and cap in the position cards is respected.`],
              ["The linear case", `${pct(res.linearPct,1)} linear, inside the ${pct(FRAME.linearCeiling,0)} ceiling the client stated. It is there for reach the digital portfolio cannot buy at this budget, not for efficiency.`],
            ].map(([k,v])=><div className="bl" key={k}><div className="bk">{k}</div><div className="bv">{v}</div></div>)}
          </div>
        )}
      </div>

      {/* ------------------------------------------------------------- side */}
      <div className="col sticky" style={{gap:14}}>
        <Card title="Save a version">
          <div className="row" style={{gap:12, marginBottom:11}}>
            <div className="scorebadge" style={{borderColor: rub.below.length===0?"var(--good)":rub.below.length<=1?"var(--warn)":"var(--bad)"}}>
              <b>{rub.clear}<span style={{fontSize:11, fontWeight:400}}>/{rub.of}</span></b><span>CLEAR</span>
            </div>
            <div className="grow tiny muted">Dimensions clearing the threshold this RFP set. Scored separately, not
              added up — the trade-off between them is the thing worth seeing. [OQ-2] the content is not settled.</div>
          </div>
          {RUBRIC.map(r=>{
            const v = rub.parts[r.k], clear = v >= r.bar;
            return (
              <div key={r.k} className="row" style={{marginBottom:6}}>
                <span className="tiny" style={{width:118}} title={`${r.help}\n\nNeeds ${r.bar} for this RFP.`}>{r.label}</span>
                <div className="grow"><Bar v={v/100} c={clear?"g":"a"}/></div>
                <span className="tiny" style={{width:26, textAlign:"right", color: clear?"var(--ink-3)":"var(--warn)"}}>{v.toFixed(0)}</span>
              </div>
            );
          })}
          <div className="hr"/>
          {unjustified.length > 0 && <div className="banner r" style={{marginBottom:9}}>
            <span className="bi">Blocked</span><div>{unjustified.length} override without a justification. A version
              cannot be saved for commitment while an override is unjustified (T5, T6).</div></div>}
          <Btn c="pri" style={{width:"100%", justifyContent:"center"}} disabled={unjustified.length>0}
            onClick={()=>setSaveOpen(true)}>Save this as a plan version</Btn>
          <div className="tiny dim" style={{marginTop:7}}>
            Immutable once saved. A further allocation produces another version rather than replacing this one.
          </div>
        </Card>

        <Gate gate={gate} verb="Hand off to Analyze"
          onGo={()=>{ up({phase:"analyze"});
            log("sys", `Strategize orchestrator handed off to Analyze at gate score ${gate.score}.`);
            toast("Handoff accepted — " + st.versions.length + " version(s) to compare"); }}/>

        <Assist title="Reading this solve">
          {res.unallocated.length > 0 ? <>
            {money(res.unallocated[0].amount)} of the {res.unallocated[0].region} envelope has nowhere to go.
            {" "}{res.unallocated[0].why} That is a Discovery problem, not an optimiser problem — the solver will not
            move it to another region on its own, because the regional split is a recorded decision (G01).
          </> : res.reach3 < FRAME.reachGoal3 ? <>
            3+ reach lands at {pct(res.reach3,1)} against a {pct(FRAME.reachGoal3,1)} goal. Average frequency is
            {" "}{res.avgFreq.toFixed(1)}, so the gap is reach breadth rather than weight — more distinct products, not
            more money on the ones already in.
          </> : <>
            The solve clears the KPI at {pct(res.reach3,1)} against {pct(FRAME.reachGoal3,1)}. The argument to check
            before you save: {res.lines[0].p.name.split(" — ")[0]} carries {pct(res.lines[0].spend/res.spend,0)} of the
            plan on its own, and it is at {pct(res.lines[0].availUse,0)} of sellable avails.
          </>}
        </Assist>

        <Card title="Versions saved" tight>
          <div style={{padding:"10px 13px"}}>
            {st.versions.length === 0 ? <div className="tiny dim">None yet.</div> :
              st.versions.map(v=>(
                <div key={v.id} className="row" style={{marginBottom:7}}>
                  <Chip c="n">{v.id}</Chip>
                  <div className="grow tiny">{v.name}<div className="mini dim">{v.at}</div></div>
                  <b className="tiny" title={v.rubric.below.length
                    ? "Short on: " + v.rubric.below.map(b=>`${b.label} ${b.score}/${b.bar}`).join("; ")
                    : "Every dimension clears."}>{v.rubric.clear}<span className="dim">/{v.rubric.of}</span></b>
                </div>))}
          </div>
        </Card>
      </div>

      {ovr && <OverrideModal line={ovr.line} value={ovr.value} res={res}
        onCancel={()=>setOvr(null)} onConfirm={applyOverride}/>}

      {saveOpen && <SaveVersion n={st.versions.length} res={res} rub={rub}
        onCancel={()=>setSaveOpen(false)} onConfirm={saveVersion}/>}
    </div>
  );
};

const OverrideModal = ({line, value, res, onCancel, onConfirm}) => {
  const [v, setV] = useState(value);
  const [r, setR] = useState("");
  const [sent, setSent] = useState(null);
  const [tries, setTries] = useState(0);
  const ok = r.trim().length >= 20 && v > 0;
  const impsK = v / line.cpm;
  const availUse = impsK / line.availK;

  /* Overriding the optimiser is the largest single deviation a planner can
     make, so the argument for it is held to the same bar as everything else. */
  const ev = evalJustification(r);
  const tone = ev.verdict === "pass" ? "g" : ev.verdict === "thin" ? "a" : "r";
  const submit = () => {
    if (ev.verdict === "revise" && tries < 2){ setSent(ev); setTries(n=>n+1); return; }
    onConfirm(line, v, r.trim());
  };

  return (
    <Modal title="Override this allocation" sub="Justify, then override (T6). The reason is evaluated before the override is accepted; the optimiser re-solves from the overridden value and does not negotiate."
      onClose={onCancel}
      footer={<><div className="tiny dim">{ev.verdict === "pass"
        ? "The rest of the " + line.region + " envelope will redistribute around this."
        : ev.verdict === "thin" ? "This will travel, but P&I would have to ask you a question to act on it."
        : "Not yet defensible."}</div><div style={{flex:1}}/>
        <Btn onClick={onCancel}>Cancel</Btn>
        <Btn c="pri" disabled={!ok} onClick={submit}>Override and re-solve</Btn></>}>
      <div className="row" style={{gap:10, marginBottom:14}}>
        <span className="dot" style={{background:BRAND_COLOR[line.p.brand]}}/>
        <b>{line.p.name}</b><Chip>{line.region}</Chip><Chip c={line.p.medium==="Digital"?"b":"a"}>{line.p.medium}</Chip>
      </div>
      <div className="g2" style={{marginBottom:14}}>
        <div>
          <label className="lbl">Net spend</label>
          <input className="inp" type="number" value={v} step={10000} onChange={e=>setV(Number(e.target.value))}/>
          <div className="tiny dim" style={{marginTop:5}}>System allocated {money(line.systemSpend)} ({pct(line.systemSpend/res.spend,1)} of plan)</div>
        </div>
        <div>
          <div className="lbl">What that buys</div>
          <dl className="kv" style={{gridTemplateColumns:"104px 1fr"}}>
            <dt>Impressions</dt><dd>{imps(impsK)}</dd>
            <dt>At CPM</dt><dd>{cpmf(line.cpm)}</dd>
            <dt>% of avails</dt><dd style={availUse>0.85?{color:"var(--bad)"}:null}>{pct(availUse,0)}{availUse>0.85 && " — not deliverable"}</dd>
            <dt>Share of plan</dt><dd>{pct(v/res.spend,1)}</dd>
          </dl>
        </div>
      </div>
      <label className="lbl">Why</label>
      <textarea className="inp" autoFocus value={r} onChange={e=>{setR(e.target.value); setSent(null);}}
        placeholder="What does the optimiser not know? Name the number you are moving and what the move costs. This travels into the plan brief and P&I reads it at approval."/>

      <div className="row" style={{gap:10, alignItems:"center", marginTop:11}}>
        <Chip c={tone}>ARGUMENT {ev.score}</Chip>
        <div className={"bar " + tone} style={{flex:1}}><i style={{width:ev.score+"%"}}/></div>
      </div>
      <div className="col" style={{gap:4, marginTop:8}}>
        {ev.tests.map(x => (
          <div key={x.id} className="row" style={{gap:7, alignItems:"flex-start"}}>
            <span style={{color:x.ok?"var(--good)":"#8a95a0", fontSize:12, lineHeight:1.5, flexShrink:0}}>
              {x.ok?"✓":"○"}</span>
            <div style={{minWidth:0}}>
              <span style={{fontSize:11.5, color:x.ok?"var(--ink)":"var(--ink-2)"}}>{x.label}</span>
              {!x.ok && r.trim().length > 0 && <div className="tiny dim" style={{marginTop:1}}>{x.ask}</div>}
            </div>
          </div>
        ))}
      </div>

      {sent && <div className="banner r" style={{marginTop:12}}>
        <span className="bi">Sent back</span>
        <div><b>The orchestrator did not accept this reason.</b> {sent.feedback}
          <ul style={{margin:"7px 0 0 16px", padding:0}}>
            {sent.missing.map(m => <li key={m.id} style={{marginBottom:3}}>{m.ask}</li>)}
          </ul>
          {tries >= 2 && <div className="tiny" style={{marginTop:7}}>
            Submitting again records it as a weak argument. The override goes through and the weakness is on the
            record wherever it is read.</div>}
        </div>
      </div>}
    </Modal>
  );
};

const SaveVersion = ({n, res, rub, onCancel, onConfirm}) => {
  const [name, setName] = useState(["Balanced global", "Digital-led", "Reach-max", "Yield-led"][n] || "Version " + (n+1));
  const [note, setNote] = useState("");
  return (
    <Modal title={"Save plan version PV-" + String.fromCharCode(65+n)}
      sub="Immutable once saved. Binds one strategy brief version and one plan brief."
      onClose={onCancel}
      footer={<><div className="tiny dim">A further allocation produces another version rather than replacing this one (T4).</div>
        <div style={{flex:1}}/><Btn onClick={onCancel}>Cancel</Btn>
        <Btn c="pri" disabled={!name.trim()} onClick={()=>onConfirm(name.trim(), note.trim())}>Save version</Btn></>}>
      <div className="statgrid" style={{marginBottom:14}}>
        <Stat label="Net allocated" value={money1(res.spend)}/>
        <Stat label="3+ reach" value={pct(res.reach3,1)}/>
        <Stat label="Blended CPM" value={cpmf(res.blendedCpm)}/>
        <Stat label="Rubric" value={rub.total.toFixed(0)}/>
      </div>
      <label className="lbl">Name this version</label>
      <input className="inp" value={name} onChange={e=>setName(e.target.value)} style={{marginBottom:12}}/>
      <label className="lbl">What is this version arguing? (optional)</label>
      <textarea className="inp" value={note} onChange={e=>setNote(e.target.value)}
        placeholder="One line the next reader needs — what is this version for, and what did you trade to get it?"/>
    </Modal>
  );
};
