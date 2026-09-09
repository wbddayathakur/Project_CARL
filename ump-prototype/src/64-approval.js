/* =============================================================================
   64-approval.js — Approval, owned by P&I.
   The behaviour change: not reacting to a plan that arrives, but reviewing it
   against a position already stated, line by line, seeing what each line does
   to inventory before approving.
   ============================================================================= */
const Approval = ({S}) => {
  const { st, up, log } = S;
  const toast = useToast();
  const [ask, setAsk] = useState(null);
  const [tab, setTab] = useState("lines");
  const ver = st.versions.find(v=>v.id===st.committed);

  if (!ver) return (
    <div className="pad" style={{padding:0}}>
      <Card title="Nothing has been shared yet">
        <div className="muted">Approval opens on a committed plan version. Commit one in Analyze.</div>
        <Btn c="pri sm" style={{marginTop:11}} onClick={()=>up({phase:"analyze"})}>Go to Analyze</Btn>
      </Card>
    </div>
  );

  const decided = ver.lines.filter(l=>st.decisions[l.pid]);
  const approved = ver.lines.filter(l=>st.decisions[l.pid]?.d==="approve");
  const disapproved = ver.lines.filter(l=>st.decisions[l.pid]?.d==="disapprove");
  const conditional = ver.lines.filter(l=>st.decisions[l.pid]?.d==="condition");
  const allDecided = decided.length === ver.lines.length;
  const apSpend = approved.reduce((s,l)=>s+l.spend,0);
  const dpSpend = disapproved.reduce((s,l)=>s+l.spend,0);

  const decide = (line, d, reason, weight) => {
    up(s => ({ decisions: {...s.decisions, [line.pid]: { d, reason, weight, at: NOW(), spend: line.spend }} }));
    log("pi", `${line.name} — ${d === "approve" ? "approved" : d === "condition" ? "approved with a condition" : "disapproved"}${weight ? `, asking for more weight` : ""}.`, reason);
    setAsk(null);
    toast(`${line.name.split(" — ")[0]} ${d==="disapprove"?"disapproved":"approved"}`);
  };

  const sendBack = () => {
    /* Disapproval reasons become soft constraints on the next pass, and approved
       lines become hard constraints for the optimiser (Discovery §7, T7). */
    disapproved.forEach(l=>{
      const d = st.decisions[l.pid];
      S.learn({ from:`${ver.id} · P&I disapproval`, text:`${l.name} disapproved`, reason:d.reason,
        effect: d.weight ? `Discovery: ${l.name} moves up the ranking — P&I asked for more inventory on it`
                         : `Discovery: ${l.name} enters flagged, with P&I's reason attached`, strength:"strong" });
    });
    up({ phase:"discovery", strategyAccepted:null, overrides:{}, justifications:{} });
    log("no", `${disapproved.length} disapproved line${disapproved.length===1?"":"s"} returned to Discovery. ${approved.length} approved line${approved.length===1?"":"s"} locked as hard constraints for the re-solve.`);
    toast("Returned to Discovery with P&I's reasons attached");
  };

  return (
    <div className="split">
      <div className="col" style={{gap:14}}>
        <div className="banner a">
          <span className="bi">You are P&amp;I</span>
          <div>Rachel Levine, reviewing <b>{ver.id} · {ver.name}</b> for {DEAL.plan}. Every line below is shown against
            the position you already stated for Q3, with what it does to sellout and yield. Every line needs a decision.</div>
        </div>

        <div className="tabs">
          {[["lines","Lines", ver.lines.length],["position","Your stated position"],["inventory","Inventory effect"],["package","The whole package"]].map(([k,l,n])=>
            <button key={k} className={tab===k?"on":""} onClick={()=>setTab(k)}>{l}{n!=null && <span className="ct">{n}</span>}</button>)}
        </div>

        {tab==="lines" && ver.lines.map(l=>{
          const d = st.decisions[l.pid];
          const line = { ...l, p: PRODUCTS.find(p=>p.id===l.pid), region:l.region, availUse:l.availUse, cpm:l.cpm };
          const inv = inventoryImpact(line);
          const pos = positionsFor(l.pid);
          const just = ver.justifications[l.pid];
          return (
            <div key={l.pid} className={"linebox " + (d?.d==="approve"?"ap":d?.d==="disapprove"?"dp":d?.d==="condition"?"cn":"")}>
              <div className="lb-h">
                <span className="dot" style={{background:BRAND_COLOR[l.brand]}}/>
                <b style={{fontSize:12.5}}>{l.name}</b>
                <Chip>{l.region}</Chip>
                <Chip c={l.medium==="Digital"?"b":"a"}>{l.medium}</Chip>
                {l.overridden && <Chip c="v">planner override</Chip>}
                <div style={{flex:1}}/>
                <b>{money(l.spend)}</b>
                <span className="dim tiny">{pct(l.spend/ver.roll.spend,1)} of plan</span>
                {d && <Chip c={d.d==="approve"?"g":d.d==="disapprove"?"r":"a"}>
                  {d.d==="approve"?"APPROVED":d.d==="disapprove"?"DISAPPROVED":"CONDITIONAL"}</Chip>}
              </div>
              <div className="lb-b">
                <div className="g3" style={{gap:12, marginBottom:10}}>
                  <div>
                    <div className="lbl">The line</div>
                    <dl className="kv tiny" style={{gridTemplateColumns:"88px 1fr"}}>
                      <dt>CPM</dt><dd><b>{cpmf(l.cpm)}</b> <span className="dim">floor {cpmf(l.floorCpm)}</span></dd>
                      <dt>vs floor</dt><dd style={{color: inv.vsFloor<0.05?"var(--bad)":inv.vsFloor>0.25?"var(--good)":null}}>
                        {inv.vsFloor>0?"+":""}{pctn(inv.vsFloor*100,0)} — {inv.yield}</dd>
                      <dt>Impressions</dt><dd>{imps(l.impsK)}</dd>
                      <dt>In demo</dt><dd>{pct(l.comp,0)}</dd>
                    </dl>
                  </div>
                  <div>
                    <div className="lbl">What it does to inventory</div>
                    <div className="tiny" style={{marginBottom:5}}>
                      Takes <b>{pct(l.availUse,0)}</b> of sellable avails for the flight.</div>
                    <div className="row tiny" style={{gap:7}}>
                      <span className="dim">{l.region} {l.medium} sellout</span>
                      <b>{pctn(inv.selloutBefore,0)}</b><span className="dim">→</span>
                      <b style={{color: inv.selloutAfter>85?"var(--warn)":"var(--good)"}}>{pctn(inv.selloutAfter,0)}</b>
                    </div>
                    <Bar v={inv.selloutAfter/100} c={inv.selloutAfter>85?"a":"g"}/>
                  </div>
                  <div>
                    <div className="lbl">Against your position</div>
                    {pos.length ? pos.map(p=>(
                      <div key={p.id} className="tiny" style={{marginBottom:5}}>
                        <Chip c={p.hardness==="hard"?"r":"n"}>{p.id}</Chip> <b>{p.title}</b>
                        <div className="mini muted">{p.text}</div>
                      </div>
                    )) : <div className="tiny dim">No position card touches this line. It falls under the general Q3
                      posture — {POSTURE_LABEL[(PRODUCTS.find(p=>p.id===l.pid)||{}).yieldPosture]?.toLowerCase()}.</div>}
                  </div>
                </div>

                {l.overridden && (
                  <div className="banner b" style={{marginBottom:10}}>
                    <span className="bi">Planner override</span>
                    <div>The optimiser allocated {money(l.systemSpend)}; the planner moved it to {money(l.spend)}.
                      <div style={{marginTop:4, fontStyle:"italic"}}>“{just}”</div></div>
                  </div>
                )}

                {d ? (
                  <div className={"banner " + (d.d==="approve"?"g":d.d==="disapprove"?"r":"a")}>
                    <span className="bi">{d.d==="approve"?"Approved":d.d==="disapprove"?"Disapproved":"Conditional"}</span>
                    <div>“{d.reason}”{d.weight && <> <b>You asked for more inventory weight on this product</b> — in
                      Discovery that becomes a move up the ranking, because ranking is how a weight instruction is
                      expressed.</>}<div className="mini dim" style={{marginTop:3}}>{d.at}</div></div>
                  </div>
                ) : (
                  <div className="row" style={{gap:7}}>
                    <Btn c="ok sm" onClick={()=>setAsk({line:l, d:"approve"})}>Approve</Btn>
                    <Btn c="sm" onClick={()=>setAsk({line:l, d:"condition"})}>Approve with a condition</Btn>
                    <Btn c="dgr sm" onClick={()=>setAsk({line:l, d:"disapprove"})}>Disapprove</Btn>
                    <div style={{flex:1}}/>
                    <span className="tiny dim">Every decision carries a reason. It goes back to the planner as an instruction, not a verdict.</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {tab==="position" && (
          <div className="col" style={{gap:12}}>
            <div className="banner b"><span className="bi">Why this is here</span>
              <div>Today a plan arrives and P&amp;I reacts to it. These are the four positions you stated for Q3 before
                this plan existed. The point of the review is to read the plan against them, not to form a view from scratch.</div></div>
            {PI_POSITION.map(p=>{
              const touched = ver.lines.filter(l=>p.appliesTo.includes(l.pid));
              const spend = touched.reduce((s,l)=>s+l.spend,0);
              return (
                <Card key={p.id} title={p.title} sub={p.id + " · stated 2026-04-28"}
                  right={<Chip c={p.hardness==="hard"?"r":"n"}>{p.hardness}</Chip>}>
                  <div style={{fontSize:12.5, marginBottom:6}}>{p.text}</div>
                  <div className="tiny muted" style={{marginBottom:10}}>Reason you gave: {p.reason}</div>
                  {touched.length ? (
                    <div className="banner g"><span className="bi">In this plan</span>
                      <div>{touched.length} line{touched.length>1?"s":""} — {money(spend)}, {pct(spend/ver.roll.spend,1)} of the plan.
                        {touched.map(l=>` ${l.name.split(" — ")[0]} at ${cpmf(l.cpm)} (floor ${cpmf(l.floorCpm)}).`)}</div></div>
                  ) : <div className="banner a"><span className="bi">Not in this plan</span>
                      <div>No line in {ver.id} touches this position. If it should have, that is a Discovery instruction, not a line decision.</div></div>}
                </Card>
              );
            })}
            <Card title="What you did not state" sub="Recorded absence, from Intake">
              <div className="banner a"><span className="bi">G04</span>
                <div>No advertiser-specific position was returned for this RFP. Requested 2026-05-04, no response by
                  2026-05-05. The plan was built on the four standing Q3 cards, and the absence is on the record — which
                  is the point: nobody can later say the plan ignored a position that was never written down.</div></div>
            </Card>
          </div>
        )}

        {tab==="inventory" && (
          <Card title="What the whole plan does to inventory" tight
            sub="Sellout before and after, and yield against floor, for every line.">
            <XL name="inventory_effect" height={380} rows={ver.lines.map(l=>{
              const inv = inventoryImpact({...l, p:PRODUCTS.find(p=>p.id===l.pid)});
              return {...l, ...inv};
            })} cols={[
              { key:"name", label:"Line", w:260, get:l=>l.name },
              { key:"region", label:"Region", w:58, get:l=>l.region },
              { key:"medium", label:"Medium", w:62, get:l=>l.medium },
              { key:"spend", label:"Net spend", w:98, align:"r", get:l=>money(l.spend), raw:l=>Math.round(l.spend) },
              { key:"cpm", label:"CPM", w:62, align:"r", get:l=>cpmf(l.cpm), raw:l=>l.cpm },
              { key:"floorCpm", label:"Floor", w:60, align:"r", get:l=>cpmf(l.floorCpm), raw:l=>l.floorCpm },
              { key:"vsFloor", label:"vs floor", w:70, align:"r", get:l=>pctn(l.vsFloor*100,0), raw:l=>(l.vsFloor*100).toFixed(1),
                cell:l=><span style={{color:l.vsFloor<0.05?"var(--bad)":l.vsFloor>0.25?"var(--good)":null}}>
                  {l.vsFloor>0?"+":""}{(l.vsFloor*100).toFixed(0)}%</span> },
              { key:"yield", label:"Yield read", w:92, get:l=>l.yield,
                cell:l=><Chip c={l.yield==="accretive"?"g":l.yield==="at position"?"":l.yield==="thin"?"a":"r"}>{l.yield}</Chip> },
              { key:"availUse", label:"% of avails", w:84, align:"r", get:l=>pct(l.availUse,0), raw:l=>l.availUse },
              { key:"selloutBefore", label:"Sellout now", w:88, align:"r", get:l=>pctn(l.selloutBefore,0) },
              { key:"selloutAfter", label:"Sellout after", w:92, align:"r", get:l=>pctn(l.selloutAfter,0),
                cell:l=><b style={{color:l.selloutAfter>85?"var(--warn)":null}}>{pctn(l.selloutAfter,0)}</b> },
            ]}/>
          </Card>
        )}

        {tab==="package" && (
          <div className="brief">
            <h2>Approval package · {ver.id}</h2>
            <div className="tiny dim" style={{marginTop:3}}>One plan version and everything upstream of it. Bound to
              this version — approval never binds to “the plan” (T9).</div>

            <h4>What the advertiser asked for</h4>
            {deriveBrief(st).requirements.filter(l=>!l.gap).slice(0,7).map((l,i)=>(
              <div className="bl" key={i}><div className="bk">{l.k}</div>
                <div className="bv">{l.v}</div><ProvChip cls={l.cls} small/></div>))}

            <h4>Which products were chosen, and why they were ranked that way</h4>
            {ver.lines.map(l=>{
              const r = SYSTEM_RANKED.find(x=>x.pid===l.pid);
              return <div className="bl" key={l.pid}><div className="bk">{money(l.spend)}</div>
                <div className="bv">{l.name}<span className="why">{r?.why.audience} {r?.why.seller}</span></div></div>;
            })}

            <h4>What the optimiser recommended, and what the planner changed</h4>
            {Object.keys(ver.overrides).length === 0
              ? <div className="tiny muted" style={{padding:"6px 8px"}}>Nothing was overridden. This is the optimiser's
                  own answer to the accepted list.</div>
              : Object.entries(ver.overrides).map(([pid,val])=>{
                  const l = ver.lines.find(x=>x.pid===pid);
                  return <div className="bl" key={pid}><div className="bk">{l?.name}</div>
                    <div className="bv"><span className="strike dim">{money(l?.systemSpend)}</span> → <b>{money(val)}</b>
                      <span className="why">“{ver.justifications[pid]}”</span></div></div>;
                })}

            <h4>The rubric read</h4>
            {RUBRIC.map(r=>(
              <div className="bl" key={r.k}><div className="bk">{r.label}</div>
                <div className="bv"><b>{ver.rubric.parts[r.k].toFixed(0)}</b><span className="why">{r.help}</span></div></div>))}
          </div>
        )}
      </div>

      {/* ------------------------------------------------------------- side */}
      <div className="col sticky" style={{gap:14}}>
        <Card title="Decisions" sub="The phase is done when every line has one.">
          <div className="statgrid" style={{gridTemplateColumns:"1fr 1fr", marginBottom:11}}>
            <Stat label="Approved" value={approved.length} delta={money1(apSpend)} tone="good"/>
            <Stat label="Disapproved" value={disapproved.length} delta={money1(dpSpend)} tone={disapproved.length?"bad":null}/>
            <Stat label="Conditional" value={conditional.length}/>
            <Stat label="Undecided" value={ver.lines.length - decided.length}/>
          </div>
          <Bar v={decided.length/ver.lines.length} c={allDecided?"g":""}/>
          <div className="tiny dim" style={{marginTop:5}}>{decided.length} of {ver.lines.length} lines decided</div>
          <div className="hr"/>
          {allDecided ? (
            disapproved.length + conditional.length > 0 ? (
              <>
                <Btn c="pri" style={{width:"100%", justifyContent:"center"}} onClick={sendBack}>
                  Return {disapproved.length + conditional.length} line{disapproved.length+conditional.length>1?"s":""} to Discovery
                </Btn>
                <div className="tiny dim" style={{marginTop:7}}>
                  The {approved.length} approved line{approved.length===1?"":"s"} stay as they are and become hard
                  constraints for the re-solve. Your reasons travel with the disapprovals, and where you asked for more
                  weight the planner moves that product up the ranking.
                </div>
              </>
            ) : (
              <div className="banner g"><span className="bi">Fully approved</span>
                <div>Every line in {ver.id} is approved. Approval binds to this version — a late clarification would
                  produce a new brief version and this approval would lapse.</div></div>
            )
          ) : (
            <div className="tiny dim">Decide the remaining {ver.lines.length - decided.length} line
              {ver.lines.length-decided.length===1?"":"s"} to close the phase.</div>
          )}
        </Card>

        <Assist title="What I would look at">
          {(() => {
            const thin = ver.lines.map(l=>({l, inv:inventoryImpact({...l, p:PRODUCTS.find(p=>p.id===l.pid)})}))
              .filter(x=>x.inv.vsFloor < 0.10).sort((a,b)=>a.inv.vsFloor-b.inv.vsFloor)[0];
            const heavy = ver.lines.slice().sort((a,b)=>b.availUse-a.availUse)[0];
            if (thin) return <>
              <b>{thin.l.name.split(" — ")[0]}</b> clears at {cpmf(thin.l.cpm)} against a {cpmf(thin.l.floorCpm)} floor —
              {" "}{pctn(thin.inv.vsFloor*100,0)}. That is the thinnest line in the plan on yield, and it is the one
              worth a condition rather than a straight approval.
            </>;
            return <>
              Every line clears its floor. The one to watch is <b>{heavy.name.split(" — ")[0]}</b> at
              {" "}{pct(heavy.availUse,0)} of sellable avails — approving it commits that supply for the whole flight,
              and {heavy.region} {heavy.medium} is already at {pctn((SUPPLY.find(s=>s.region===heavy.region&&s.medium===heavy.medium)||{}).selloutPct,0)} sold.
            </>;
          })()}
        </Assist>

        <Card title="Plan at a glance" tight>
          <div style={{padding:"12px 14px"}}>
            <dl className="kv tiny" style={{gridTemplateColumns:"110px 1fr"}}>
              <dt>Version</dt><dd>{ver.id} · {ver.name}</dd>
              <dt>Net</dt><dd>{money(ver.roll.spend)}</dd>
              <dt>Lines</dt><dd>{ver.lines.length}</dd>
              <dt>Blended CPM</dt><dd>{cpmf(ver.roll.blendedCpm)}</dd>
              <dt>Linear share</dt><dd>{pct(ver.roll.linearPct,1)}</dd>
              <dt>3+ reach</dt><dd>{pct(ver.roll.reach3,1)} vs {pct(FRAME.reachGoal3,1)} goal</dd>
              <dt>Overrides</dt><dd>{Object.keys(ver.overrides).length}, each justified</dd>
              <dt>Rubric</dt><dd>{ver.rubric.total.toFixed(0)}</dd>
            </dl>
          </div>
        </Card>
      </div>

      {ask && <PiDecision line={ask.line} d={ask.d} onCancel={()=>setAsk(null)} onConfirm={decide}/>}
    </div>
  );
};

const PiDecision = ({line, d, onCancel, onConfirm}) => {
  const [r, setR] = useState("");
  const [weight, setWeight] = useState(false);
  const ok = d === "approve" ? r.trim().length >= 10 : r.trim().length >= 30;
  const title = { approve:"Approve this line", condition:"Approve with a condition", disapprove:"Disapprove this line" }[d];
  const inv = inventoryImpact({...line, p:PRODUCTS.find(p=>p.id===line.pid)});
  return (
    <Modal title={title} sub={line.name} onClose={onCancel}
      footer={<><div className="tiny dim">{d==="disapprove"
        ? "Disapproval returns to Discovery, where product selection and ranking happen. Your reason travels with it and becomes a soft constraint on the next pass."
        : "Approved lines become hard constraints for any re-solve."}</div>
        <div style={{flex:1}}/><Btn onClick={onCancel}>Cancel</Btn>
        <Btn c={d==="disapprove"?"dgr":"pri"} disabled={!ok} onClick={()=>onConfirm(line, d, r.trim(), weight)}>
          {d==="disapprove"?"Disapprove":"Approve"}</Btn></>}>
      <div className="statgrid" style={{marginBottom:14}}>
        <Stat label="Net spend" value={money(line.spend)}/>
        <Stat label="CPM vs floor" value={(inv.vsFloor>0?"+":"") + pctn(inv.vsFloor*100,0)} tone={inv.vsFloor<0.05?"bad":"good"}/>
        <Stat label="Avails taken" value={pct(line.availUse,0)}/>
        <Stat label="Sellout after" value={pctn(inv.selloutAfter,0)}/>
      </div>
      <label className="lbl">{d==="disapprove" ? "Why, and what should change" : "Reason"}</label>
      <textarea className="inp" autoFocus value={r} onChange={e=>setR(e.target.value)}
        placeholder={d==="disapprove"
          ? "Be specific about which products should have been in the plan and at what weight — that is what the planner acts on."
          : d==="condition" ? "What has to be true for this to stand." : "One line is enough."}/>
      {d !== "approve" && (
        <div className="row" style={{marginTop:12, gap:9}}>
          <Switch on={weight} onChange={setWeight}/>
          <div className="tiny">
            <b>I want more inventory weight on this product.</b>
            <div className="muted">In Discovery that becomes a move up the ranking — ranking is the mechanism by which
              a weight instruction is expressed, and there is no direct weight control.</div>
          </div>
        </div>
      )}
    </Modal>
  );
};
