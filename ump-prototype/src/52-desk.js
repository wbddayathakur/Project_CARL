/* =============================================================================
   52-desk.js — the desk a planner opens on.
   ============================================================================= */
const Desk = ({onOpen, st}) => {
  const [q, setQ] = useState("");

  /* The Tide row reads live state, so the desk never contradicts the plan. */
  const live = {
    stage: {intake:"Intake", discovery:"Discovery", strategize:"Strategize",
            analyze:"Analyze", approval:"Approval"}[st.phase],
    meta: st.committed ? `${st.committed} committed · with P&I`
        : st.versions.length ? `${st.versions.length} version${st.versions.length>1?"s":""} saved · none committed`
        : st.strategyAccepted ? `Strategy brief v${st.strategyVersion} accepted · no version saved`
        : st.intakeApproved ? `Brief v${st.intakeApproved.version} approved · ranking untouched`
        : `Brief v${st.briefVersion} · ${GAPS.filter(g=>g.material && !st.gapDecisions[g.id]).length} material gaps open`,
  };
  const book = PORTFOLIO.map(p => p.id === DEAL.id ? {...p, ...live} : p);
  const rows = book.filter(p =>
    !q || (p.name + p.adv + p.agy + p.id).toLowerCase().includes(q.toLowerCase()));
  const active = book.filter(p=>p.flag!=="closed").length;
  const total  = book.reduce((s,p)=>s+p.budget,0);
  const waitingPI = book.filter(p=>p.stage==="Approval");
  const tideGaps  = GAPS.filter(g=>g.material && !st.gapDecisions[g.id]).length;

  const stageChip = s => ({Intake:"", Discovery:"b", Strategize:"b", Analyze:"v",
                           Approval:"a", Planning:"", Closed:"g"}[s] || "");

  const cols = [
    { key:"name", label:"Plan", w:280, get:r=>r.name, cell:r=>(
      <div><div style={{fontWeight:r.id===DEAL.id?600:400}}>{r.name}</div>
        <div className="mini dim">{r.meta}</div></div>) },
    { key:"adv", label:"Advertiser", w:130, get:r=>r.adv },
    { key:"agy", label:"Agency", w:96, get:r=>r.agy },
    { key:"ch", label:"Channel", w:78, get:r=>r.ch,
      cell:r=><Chip c={r.ch==="Digital"?"b":r.ch==="Linear"?"a":"v"}>{r.ch}</Chip> },
    { key:"dt", label:"Deal type", w:80, get:r=>r.dt },
    { key:"stage", label:"Stage", w:92, get:r=>r.stage,
      cell:r=><Chip c={stageChip(r.stage)}>{r.stage}</Chip> },
    { key:"budget", label:"Gross budget", w:104, align:"r", get:r=>money1(r.budget), raw:r=>r.budget },
    { key:"start", label:"Flight start", w:92, get:r=>r.start },
    { key:"owner", label:"Planner", w:104, get:r=>r.owner },
    { key:"go", label:"", w:64, align:"c", get:()=>"", cell:r=>
      <Btn c="xs pri" onClick={()=>r.id===DEAL.id ? onOpen() : null}
        title={r.id===DEAL.id ? "Open this plan" : "Sample data — only the Tide plan is built out in this round"}>
        {r.id===DEAL.id ? "Open" : "—"}</Btn> },
  ];

  return (
    <div className="pad">
      <div className="row" style={{marginBottom:14, alignItems:"flex-start"}}>
        <div>
          <h2 style={{fontSize:17}}>Your desk</h2>
          <div className="muted" style={{marginTop:4}}>Six plans, one quarter. Context travels with the plan, so any
            planner can pick any of these up (T2).</div>
        </div>
        <div style={{flex:1}}/>
        <input className="inp" style={{width:250}} placeholder="Search advertiser, agency or plan…"
          value={q} onChange={e=>setQ(e.target.value)}/>
      </div>

      <div className="statgrid" style={{marginBottom:14}}>
        <Stat label="Deals in quarter" value={PORTFOLIO.length} delta="Q3 2026"/>
        <Stat label="Total gross" value={money1(total)} delta={`${active} active · ${PORTFOLIO.length-active} closed`}/>
        <Stat label="Waiting on P&I" value={waitingPI.length} tone="bad"
          delta={waitingPI.map(p=>p.name.split(" — ")[0]).join(", ") || "nothing with the seller"}/>
        <Stat label="Material gaps open" value={tideGaps + 3}
          delta={tideGaps ? `Tide ${tideGaps}, Toyota 3` : "Toyota intake"}/>
        <Stat label="Your plans" value={PORTFOLIO.filter(p=>p.owner==="You").length} delta="Tide, Dove"/>
      </div>

      <XL name="plans_q3_2026" cols={cols} rows={rows} height={330}
        rowTone={r=>r.flag==="closed"?"dis":""}
        sub={`Total $${(total/1e6).toFixed(1)}M · ${active} active · ${PORTFOLIO.length-active} closed`}/>

      <div className="g2" style={{marginTop:14}}>
        <Card title="Tide — Global Summer Refresh 2026" sub="The worked example in this round"
          right={<Btn c="pri sm" onClick={onOpen}>Open plan</Btn>}>
          <div className="g2">
            <dl className="kv">
              <dt>Opportunity</dt><dd className="mono">{DEAL.id}</dd>
              <dt>Advertiser</dt><dd>{DEAL.advertiser} — {DEAL.brand}</dd>
              <dt>Agency</dt><dd>{DEAL.agency}</dd>
              <dt>Account exec</dt><dd>{DEAL.ae}</dd>
            </dl>
            <dl className="kv">
              <dt>Gross</dt><dd>{money(DEAL.grossBudget)}</dd>
              <dt>Commission</dt><dd>−{money(DEAL.grossBudget*DEAL.agencyCommissionPct)} (15%)</dd>
              <dt>Net working</dt><dd><b>{money(DEAL.netBudget)}</b></dd>
              <dt>Flight</dt><dd>{FLIGHT.label}</dd>
            </dl>
          </div>
          <div className="hr"/>
          <div className="row wrap" style={{gap:6}}>
            <Chip c="v">Unified</Chip><Chip>Upfront</Chip><Chip>Q3</Chip><Chip>Global</Chip>
            <Chip c="b">4 regions</Chip><Chip c="a">Linear + Digital</Chip>
          </div>
          <div className="tiny muted" style={{marginTop:10}}>
            Scope note: OQ-4 is answered digital-only for v0. This plan deliberately carries linear as well, so the
            unified case is visible and the linear lines are marked throughout.
          </div>
        </Card>
        <Card title="What changed since you last looked" sub="Everything is attached to the plan, not to you">
          <Timeline items={st.timeline} max={6}/>
        </Card>
      </div>
    </div>
  );
};
