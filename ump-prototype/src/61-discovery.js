/* =============================================================================
   61-discovery.js — Discovery phase.
   Ranking is the substance. Every position carries the reasoning that put it
   there; every planner deviation carries a justification; both travel forward.
   ============================================================================= */

function interrogate(row, ranking){
  const above = ranking.find(r => r.rank === row.rank - 1);
  const qs = [];
  if (above){
    const gaps = CRITERIA.map(c => ({ c, d: above.parts[c.k] - row.parts[c.k] })).sort((a,b)=>b.d-a.d);
    const worst = gaps[0];
    qs.push({ q:`Why is this ranked ${row.rank} and not above ${above.p.name.split(" — ")[0]}?`,
      a: worst.d > 1
        ? `${worst.c.label} is the difference — ${row.parts[worst.c.k].toFixed(0)} against ${above.parts[worst.c.k].toFixed(0)}. ${row.why[worst.c.k]} Everything else is within a few points.`
        : `It is close. The two are within ${Math.abs(above.total-row.total).toFixed(1)} points and the order between them is not load-bearing — if you want it higher, move it and say why.` });
  }
  const weakest = CRITERIA.map(c=>({c, v:row.parts[c.k]})).sort((a,b)=>a.v-b.v)[0];
  qs.push({ q:"What would it take to move this up?",
    a:`${weakest.c.label} is its weakest criterion at ${weakest.v.toFixed(0)}. ${row.why[weakest.c.k]}${
      weakest.c.k === "avails" || weakest.c.k === "audience" ? " Targeting customisation moves this; the price and avails consequence updates as you set it." :
      weakest.c.k === "price" ? " Price is the lever, and it is a negotiation, not a setting." :
      weakest.c.k === "seller" ? " That is P&I's posture, not a planning input. It changes when they change it." : ""}` });
  const bought = HISTORY.filter(h => h.topProducts.some(t => row.p.name.includes(t.split(" ")[0])));
  qs.push({ q:"Has this advertiser bought it before?",
    a: bought.length
      ? `Yes — ${bought.length} of the last four plans: ${bought.map(b=>`${b.plan} (${b.closed}, ${cpmf(b.cpm)} blended)`).join(", ")}.`
      : `Not in the 12-month lookback. That is not a reason to exclude it, but it is a reason the argument has to be made explicitly in the plan brief.` });
  const pos = positionsFor(row.pid);
  qs.push({ q:"What does P&I say about it?",
    a: pos.length
      ? pos.map(p=>`${p.title} (${p.id}, ${p.hardness}): ${p.text} Reason given: ${p.reason}`).join(" ")
      : `Nothing specific. It falls under the general Q3 posture — ${POSTURE_LABEL[row.p.yieldPosture].toLowerCase()}. ${row.p.note}` });
  qs.push({ q:"What is the inventory and price position right now?",
    a:`${imps(row.live.availK)} sellable across the flight at ${cpmf(row.live.cpm)}${row.custom.length ? ` with ${row.custom.length} customisation${row.custom.length>1?"s":""} applied` : ""}. Floor ${cpmf(row.p.floorCpm)}, card ${cpmf(row.p.cardCpm)}, market benchmark ${cpmf((BENCH[row.p.region+"|"+row.p.medium]||{}).cpm)}. ${row.live.availEstimate ? "Avails is an estimate while targeting is customised — the firm number returns with the solve." : "Avails is firm as at derivation."}` });
  return qs;
}

const RankRow = ({row, ranking, onMove, onToggle, onOpen}) => {
  const p = row.p;
  return (
    <div className={"rk" + (row.on ? "" : " off") + (row.moved ? " moved" : "")}>
      <div className="rk-n">
        <div className="arrows"><button onClick={()=>onMove(row,-1)} title="Move up — requires a reason">▲</button></div>
        <b>{row.rank}</b>
        <div className="arrows"><button onClick={()=>onMove(row,1)} title="Move down — requires a reason">▼</button></div>
      </div>
      <div className="rk-m">
        <div className="row" style={{gap:7}}>
          <span className="dot" style={{background:BRAND_COLOR[p.brand]||"#8a95a0"}}/>
          <b style={{fontSize:12.5}}>{p.name}</b>
          <Chip c={p.medium==="Digital"?"b":"a"}>{p.medium}</Chip>
          <Chip>{p.region}</Chip>
          {row.custom.length>0 && <Chip c="v">{row.custom.length} customisation{row.custom.length>1?"s":""}</Chip>}
          {row.breaches.length>0 && <Chip c="r" title={row.breaches[0].text}>BREACH</Chip>}
          {row.moved && <Chip c="v">moved {row.delta>0?"↑":"↓"}{Math.abs(row.delta)} from system rank {row.sysRank}</Chip>}
          <div style={{flex:1}}/>
          <Switch on={row.on} onChange={()=>onToggle(row)}/>
        </div>
        <div className="tiny muted" style={{marginTop:4, lineHeight:1.5}}>
          {row.why.kpi}
        </div>
        <div className="row wrap tiny" style={{gap:12, marginTop:6}}>
          <span><span className="dim">CPM</span> <b>{cpmf(row.live.cpm)}</b></span>
          <span><span className="dim">Avails</span> <b>{imps(row.live.availK)}</b>{row.live.availEstimate && <span className="dim" title="Estimate while targeting is customised"> est</span>}</span>
          <span><span className="dim">In-demo</span> <b>{pct(row.live.comp,0)}</b></span>
          <span><span className="dim">P&amp;I</span> <b>{POSTURE_LABEL[p.yieldPosture]}</b></span>
          <div style={{flex:1}}/>
          <Btn c="xs" onClick={()=>onOpen(row,"why")}>Read the reasoning</Btn>
          <Btn c="xs" onClick={()=>onOpen(row,"ask")}>Interrogate</Btn>
          <Btn c="xs" onClick={()=>onOpen(row,"target")}>Customise targeting</Btn>
        </div>
        {row.just && <div className="tiny" style={{marginTop:6, paddingLeft:8, borderLeft:"2px solid var(--violet)", color:"var(--ink-2)"}}>
          Your reason: “{row.just}”</div>}
        {row.breaches.map((b,i)=>(
          <div key={i} className="banner r" style={{marginTop:6, padding:"6px 9px"}}>
            <span className="bi">Breach</span><div className="tiny">{b.text}{b.fix && ` — “${b.fixLabel}” clears it.`}</div></div>))}
      </div>
      <div className="rk-s">
        <div className="row" style={{justifyContent:"space-between", marginBottom:5}}>
          <span className="sec-title">Why here</span><b style={{fontSize:13}}>{row.total.toFixed(1)}</b>
        </div>
        <div className="crit">
          {CRITERIA.map(c=>(
            <Fragment key={c.k}>
              <span className="cn" title={c.help}>{c.label}</span>
              <div className="bar" style={{height:4}}><i style={{width:row.parts[c.k]+"%",
                background: row.parts[c.k]>70?"var(--good)":row.parts[c.k]>45?"var(--accent)":"#d99400"}}/></div>
              <span className="cv">{row.parts[c.k].toFixed(0)}</span>
            </Fragment>
          ))}
        </div>
        {row.appliedSignals.length>0 && <div className="mini" style={{marginTop:6, color:"var(--violet)"}}>
          Learned signal {row.appliedSignals.join(", ")} applied</div>}
      </div>
    </div>
  );
};

const Discovery = ({S}) => {
  const { st, up, log } = S;
  const toast = useToast();
  const ranking = useRanking(st);
  const [tab, setTab] = useState("list");
  const [drawer, setDrawer] = useState(null);      // {row, mode}
  const [ask, setAsk] = useState(null);            // pending justification
  const selected = ranking.filter(r=>r.on);
  const gate = useMemo(() => evaluateGate("discovery", st, {ranking}), [st, ranking]);

  const hints = Object.values(st.rankJust).filter(Boolean);

  const move = (row, dir) => {
    const i = st.order.indexOf(row.pid), j = i + dir;
    if (j < 0 || j >= st.order.length) return;
    setAsk({ kind:"move", row, dir,
      title: dir < 0 ? "Move up" : "Move down",
      what: <>Moving <b>{row.p.name}</b> from position {row.rank} to {row.rank + dir}.
        The system put it at {row.sysRank} on {CRITERIA.map(c=>c.label.toLowerCase()).join(", ")}.
        Ranking is how a weight instruction is expressed — there is no direct weight control.</> });
  };
  const toggle = (row) => setAsk({ kind:"toggle", row,
    title: row.on ? "Remove from the list" : "Add to the list",
    what: row.on
      ? <>Taking <b>{row.p.name}</b> out of the list handed to the optimiser. It stays in the strategy brief as a
          considered-and-excluded entry with your reason, so it remains findable.</>
      : <>Adding <b>{row.p.name}</b> back into the list. The system ranked it {row.sysRank} of {ranking.length}.</> });

  const confirm = (reason) => {
    const a = ask;
    if (a.kind === "move"){
      const order = st.order.slice();
      const i = order.indexOf(a.row.pid);
      order.splice(i + a.dir, 0, order.splice(i,1)[0]);
      up(s => ({ order, rankJust: {...s.rankJust, [a.row.pid]: reason}, strategyAccepted:null,
        strategyVersion: s.strategyVersion + 1 }));
      log("edit", `${a.row.p.name} moved to position ${a.row.rank + a.dir} (system had it at ${a.row.sysRank}).`, reason);
    }
    if (a.kind === "toggle"){
      up(s => ({ on: {...s.on, [a.row.pid]: !a.row.on}, rankJust: {...s.rankJust, [a.row.pid]: reason},
        strategyAccepted:null, strategyVersion: s.strategyVersion + 1 }));
      log(a.row.on ? "no" : "ok", `${a.row.p.name} ${a.row.on ? "removed from" : "added to"} the accepted list.`, reason);
    }
    if (a.kind === "custom"){
      up(s => ({ customMap: {...s.customMap, [a.row.pid]: a.ids}, rankJust: {...s.rankJust, [a.row.pid]: reason},
        strategyAccepted:null, strategyVersion: s.strategyVersion + 1 }));
      log("edit", `Targeting customised on ${a.row.p.name}: ${a.ids.map(i=>CUSTOM_OPTIONS.find(o=>o.id===i).label).join(", ") || "cleared"}. Price and avails re-checked at the moment of change.`, reason);
    }
    if (a.kind === "readd"){
      log("ok", `${a.x.name} added back to the eligibility list against the exclusion “${a.x.reason}”.`, reason);
      toast("Recorded — this exclusion is now on the record as overridden");
    }
    setAsk(null); setDrawer(null);
    toast("Recorded. Your reason travels into the strategy brief and the approval package.");
  };

  const gridCols = [
    { key:"rank", label:"Rank", w:50, align:"c", get:r=>r.rank, cell:r=><b>{r.rank}</b> },
    { key:"sys", label:"System", w:56, align:"c", get:r=>r.sysRank,
      cell:r=> r.moved ? <span style={{color:"var(--violet)"}}>{r.sysRank} {r.delta>0?"↑":"↓"}</span> : <span className="dim">{r.sysRank}</span> },
    { key:"on", label:"In list", w:56, align:"c", get:r=>r.on?"yes":"no",
      cell:r=><Chip c={r.on?"g":""}>{r.on?"in":"out"}</Chip> },
    { key:"name", label:"Product / package", w:270, get:r=>r.p.name },
    { key:"region", label:"Region", w:60, get:r=>r.p.region },
    { key:"medium", label:"Medium", w:62, get:r=>r.p.medium },
    { key:"cpm", label:"CPM", w:66, align:"r", get:r=>cpmf(r.live.cpm), raw:r=>r.live.cpm },
    { key:"avail", label:"Avails", w:74, align:"r", get:r=>imps(r.live.availK), raw:r=>r.live.availK*1000 },
    { key:"comp", label:"In-demo", w:66, align:"r", get:r=>pct(r.live.comp,0), raw:r=>r.live.comp },
    ...CRITERIA.map(c=>({ key:c.k, label:c.label, w:88, align:"r", help:c.help,
      get:r=>r.parts[c.k].toFixed(0), raw:r=>r.parts[c.k].toFixed(1) })),
    { key:"total", label:"Score", w:60, align:"r", get:r=>r.total.toFixed(1), cell:r=><b>{r.total.toFixed(1)}</b> },
    { key:"custom", label:"Customisations", w:200, get:r=>r.custom.map(i=>CUSTOM_OPTIONS.find(o=>o.id===i).label).join("; ") },
    { key:"just", label:"Your reason", w:320, get:r=>r.just||"" },
  ];

  return (
    <div className="split">
      <div className="col" style={{gap:14}}>
        <div className="tabs">
          {[["list","Ranked list", selected.length],["grid","Grid"],["ask","Ask the catalogue"],["excluded","Excluded", EXCLUDED.length],["brief","Strategy brief"]].map(([k,l,n])=>
            <button key={k} className={tab===k?"on":""} onClick={()=>setTab(k)}>{l}{n!=null && <span className="ct">{n}</span>}</button>)}
        </div>

        {tab==="list" && <>
          <div className="banner b">
            <span className="bi">How to read this</span>
            <div>Five criteria produce the order, and each one is scored on the right of every row with the reasoning
              behind it. The list is <b>eligibility, not allocation</b> — the optimiser may use only the top few.
              Ranking expresses preference; it does not pre-commit spend.</div>
          </div>
          {ranking.map(r => <RankRow key={r.pid} row={r} ranking={ranking} onMove={move} onToggle={toggle}
            onOpen={(row,mode)=>setDrawer({row,mode})}/>)}
        </>}

        {tab==="grid" && (
          <Card title="Ranked eligibility list" tight
            sub="The same list, as a sheet. Every criterion score is a column, so you can sort the argument the way you would in Excel.">
            <XL name="eligibility_ranked" cols={gridCols} rows={ranking} height={560}
              rowTone={r=>r.on?"":"dis"}
              onRowClick={r=>setDrawer({row:r, mode:"why"})}
              sub="Click any row to open its reasoning"/>
          </Card>
        )}

        {tab==="ask" && (
          <div className="col" style={{gap:12}}>
            <div className="banner b"><span className="bi">Why this exists</span>
              <div>The catalogue is 22 products with a few hundred targeting templates behind them, and the question a
                planner actually has is never “show me the list”. It is “what meets this KPI”, “what can I change on
                this”, “what does excluding that cost me”. Asking is faster than knowing where to look, and the answer
                carries the config it came from so you can check it.</div></div>
            <ProductRAG ctx={{top: selected[0]}}/>
          </div>
        )}

        {tab==="excluded" && (
          <div className="col" style={{gap:12}}>
            <div className="banner a"><span className="bi">Rule</span>
              <div>Every exclusion is as legible as every inclusion. A product you expected to see and do not must be
                findable, with the reason it was excluded.</div></div>
            {EXCLUDED.map(x=>(
              <Card key={x.id} title={x.name} sub={`${x.brand} · ${x.region} · ${x.medium}`}
                right={<Chip c={x.overridable?"a":"r"}>{x.overridable ? "overridable" : "cannot be overridden"}</Chip>}>
                <div className="row" style={{alignItems:"flex-start", gap:12}}>
                  <div className="grow">
                    <div style={{fontWeight:600, fontSize:12.5, marginBottom:3}}>{x.reason}</div>
                    <div className="tiny muted">{x.detail}</div>
                  </div>
                  {x.overridable && <Btn c="sm" onClick={()=>setAsk({kind:"readd", x, title:"Override the exclusion",
                    what:<>Adding <b>{x.name}</b> back against the exclusion “{x.reason}”. The exclusion and your
                      override both stay on the record.</>})}>Add back</Btn>}
                </div>
              </Card>
            ))}
            <Card title="Also applied to the whole list" sub="List-level inclusions and exclusions from the intake brief">
              <div className="row wrap" style={{gap:8}}>
                <Chip c="r">Do-not-air list · 41 titles</Chip>
                <Chip c="r">No hard-news adjacency</Chip>
                <Chip c="a">Sport flagged, ranked last — learned signal S3</Chip>
                <Chip c="b">Home &amp; lifestyle content package · available</Chip>
                <Chip c="b">Summer live-event package · available</Chip>
              </div>
            </Card>
          </div>
        )}

        {tab==="brief" && (
          <div className="brief">
            <div className="row" style={{alignItems:"flex-start"}}>
              <div><h2>Strategy brief</h2>
                <div className="tiny dim" style={{marginTop:3}}>{DEAL.plan} · version {st.strategyVersion} ·
                  derived from intake brief v{st.intakeApproved?.version ?? st.briefVersion} + product, pricing and inventory data</div></div>
              <div style={{flex:1}}/>
              <div className="readonly"><Chip c="o">READ-ONLY</Chip> derived, like every brief</div>
            </div>

            <h4>Ranked eligibility list — {selected.length} products handed to the optimiser</h4>
            {selected.map(r=>(
              <div className="bl" key={r.pid}>
                <div className="bk"><b>{r.rank}.</b> {r.p.region} · {r.p.medium}</div>
                <div className="bv">{r.p.name}
                  <span className="why">{r.why.audience} {r.why.kpi}</span>
                  <span className="why">Relevance to the KPI: incremental 1+ reach ceiling {imps(r.p.reachK)} at {cpmf(r.live.cpm)}.</span>
                  {r.custom.length>0 && <span className="why">Customised: {r.custom.map(i=>CUSTOM_OPTIONS.find(o=>o.id===i).label).join(", ")} — price now {cpmf(r.live.cpm)} ({pctn((r.live.cpm/r.p.openCpm-1)*100,0)} vs opening), avails now {imps(r.live.availK)} ({pctn((r.live.availK/r.p.availK-1)*100,0)}).</span>}
                  {r.just && <span className="why" style={{color:"var(--violet)"}}>Planner: “{r.just}”</span>}
                </div>
                <div className="col" style={{alignItems:"flex-end", gap:3}}>
                  <b>{r.total.toFixed(1)}</b>
                  {r.moved && <Chip c="v">system had {r.sysRank}</Chip>}
                </div>
              </div>
            ))}

            <h4>Considered and excluded</h4>
            {ranking.filter(r=>!r.on).map(r=>(
              <div className="bl" key={r.pid}>
                <div className="bk">{r.p.region} · {r.p.medium}</div>
                <div className="bv"><span className="strike">{r.p.name}</span>
                  <span className="why">{r.just ? `Removed by the planner: “${r.just}”` : `Scored ${r.total.toFixed(1)}, below the cut. ${r.why.seller}`}</span></div>
                <Chip>out</Chip>
              </div>
            ))}
            {EXCLUDED.map(x=>(
              <div className="bl" key={x.id}>
                <div className="bk">{x.region} · {x.medium}</div>
                <div className="bv"><span className="strike">{x.name}</span><span className="why">{x.reason} — {x.detail}</span></div>
                <Chip c="r">ineligible</Chip>
              </div>
            ))}

            <h4>The system's list, beside yours</h4>
            <table className="tb">
              <thead><tr><th className="r" style={{width:60}}>System</th><th>System order</th>
                <th className="r" style={{width:60}}>Yours</th><th>Your order</th></tr></thead>
              <tbody>{SYSTEM_RANKED.slice(0,14).map((sr,i)=>{
                const mine = ranking[i];
                return <tr key={i}><td className="r dim">{i+1}</td><td className="tiny">{sr.p.name}</td>
                  <td className="r dim">{i+1}</td>
                  <td className="tiny" style={mine && mine.pid!==sr.pid ? {color:"var(--violet)", fontWeight:600} : null}>
                    {mine ? mine.p.name : "—"}</td></tr>;
              })}</tbody>
            </table>

            <h4>Constraints this ranking served</h4>
            {constraintSet().map(c=>(
              <div className="bl" key={c.id}>
                <div className="bk"><Chip c={c.kind==="hard"?"r":"n"}>{c.kind}</Chip></div>
                <div className="bv">{c.label}<span className="why">{c.from}</span></div>
              </div>
            ))}

            <div className="banner a" style={{marginTop:18}}><span className="bi">[OPEN]</span>
              <div>The planner re-orders and adds or removes directly, yet this brief is a derived read-only view. The
                reconciliation implemented here: a planner action is a record, and the brief re-derives over it — the
                planner is correcting the system, not editing the brief. This needs confirming as the intended model
                before UX is specified.</div></div>
          </div>
        )}
      </div>

      {/* ------------------------------------------------------------- side */}
      <div className="col sticky" style={{gap:14}}>
        <Card title="Phase exit" sub="Done when the planner accepts the ranked list and its targeting.">
          <div className="statgrid" style={{gridTemplateColumns:"1fr 1fr", marginBottom:11}}>
            <Stat label="In the list" value={selected.length} delta={`of ${ranking.length} eligible`}/>
            <Stat label="Your changes" value={ranking.filter(r=>r.just).length} delta="each with a reason"/>
          </div>
          {st.strategyAccepted ? (
            <div className="banner g"><span className="bi">Accepted</span>
              <div>Strategy brief v{st.strategyVersion}, {st.strategyAccepted.at}. This ordered list is the optimiser's input.</div></div>
          ) : (
            <>
              <Btn c="pri" style={{width:"100%", justifyContent:"center"}}
                disabled={selected.length < 3}
                onClick={()=>{ up({strategyAccepted:{at:NOW()}, phase:"strategize"});
                  log("ok", `Strategy brief v${st.strategyVersion} accepted — ${selected.length} products, in this order, with this targeting.`);
                  toast("Accepted. The optimiser solves from this list and nothing outside it."); }}>
                Accept the ranked list and its targeting
              </Btn>
              <div className="tiny dim" style={{marginTop:7}}>
                Accepting is what the gate below scores. It does not open the next phase on its own.
              </div>
            </>
          )}
        </Card>

        <Gate gate={gate} verb="Hand off to Strategize"
          onGo={()=>{ up({phase:"strategize"});
            log("sys", `Discovery orchestrator handed off to Strategize at gate score ${gate.score}.`);
            toast("Handoff accepted — Strategize orchestrator has the list"); }}
          note="[OPEN] Whether acceptance is an explicit act — as above — or is implied by clearing the gate is undecided. The two produce different audit trails on re-entry."/>

        <Card title="Constraints in force" tight>
          <div style={{padding:"10px 13px"}}>
            {constraintSet().map(c=>(
              <div key={c.id} className="row" style={{alignItems:"flex-start", gap:8, marginBottom:8}}>
                <Chip c={c.kind==="hard"?"r":"n"}>{c.kind==="hard"?"H":"S"}</Chip>
                <div><div className="tiny">{c.label}</div><div className="mini dim">{c.from}</div></div>
              </div>
            ))}
          </div>
        </Card>

        <Assist title="On this list">
          {(() => {
            const breach = ranking.find(r => r.on && r.breaches.length);
            const hbo = ranking.find(r=>r.pid==="P01");
            if (breach) return <>
              <b>{breach.p.name.split(" — ")[0]}</b> is in the list carrying a hard breach: {breach.breaches[0].text.toLowerCase()}.
              The optimiser will hold it out of the solve rather than quietly shorten the list. “{breach.breaches[0].fixLabel}”
              clears it and costs {pctn((CUSTOM_OPTIONS.find(o=>o.id===breach.breaches[0].fix)?.cpmX-1)*100,0)} on CPM and
              {" "}{pctn((1-CUSTOM_OPTIONS.find(o=>o.id===breach.breaches[0].fix)?.availX)*100,0)} of avails.
            </>;
            if (hbo && hbo.rank > 4) return <>
              <b>HBO Max premium CTV</b> sits at {hbo.rank} because price workability scores {hbo.parts.price.toFixed(0)} —
              {cpmf(hbo.live.cpm)} against a {cpmf(BENCH["US|Digital"].cpm)} US benchmark. Its KPI relevance is the highest
              in the portfolio at {hbo.parts.kpi.toFixed(0)}. If you believe the reach case beats the efficiency case,
              move it up and say so — that reason is what P&amp;I reads at approval.
            </>;
            return <>The list is in an order you can defend. Before you accept it, check that every region you have
              budget for has at least one product in the list — the optimiser cannot spend an envelope with nothing in it.</>;
          })()}
        </Assist>

        <Card title="Regional coverage" sub="An envelope with no product in the list has nowhere to go.">
          {FRAME.regions.map(r=>{
            const n = selected.filter(x=>x.p.region===r).length;
            return <div key={r} className="row" style={{marginBottom:7}}>
              <span className="tiny" style={{width:56}}>{r}</span>
              <span className="tiny dim" style={{width:92}}>{money1(DEAL.netBudget*FRAME.regionSplit[r])}</span>
              <div className="grow"><Bar v={clamp(n/3,0,1)} c={n===0?"r":n<2?"a":"g"}/></div>
              <span className="tiny" style={{width:60, textAlign:"right", color:n===0?"var(--bad)":"var(--ink-2)"}}>
                {n} product{n===1?"":"s"}</span>
            </div>;
          })}
        </Card>
      </div>

      {/* ----------------------------------------------------------- drawer */}
      {drawer && <ProductDrawer row={drawer.row} mode={drawer.mode} ranking={ranking}
        onClose={()=>setDrawer(null)}
        onCustom={(ids)=>setAsk({kind:"custom", row:drawer.row, ids,
          title:"Record the targeting change",
          what:<>Customising <b>{drawer.row.p.name}</b>. The customisation, its inventory consequence and its pricing
            consequence are recorded together, so the trade-off is visible downstream rather than only its result.</>})}/>}

      {ask && <JustifyG title={ask.title} what={ask.what} hints={hints}
        onCancel={()=>setAsk(null)} onConfirm={confirm}/>}
    </div>
  );
};

/* --------------------------------------------------------- product drawer */
const ProductDrawer = ({row, mode, ranking, onClose, onCustom}) => {
  const [m, setM] = useState(mode);
  const [ids, setIds] = useState(row.custom);
  const p = row.p;
  const preview = applyCustom(p, ids);
  const previewBreach = breachesFor(p, preview);
  const qs = useMemo(()=>interrogate(row, ranking), [row, ranking]);

  return (
    <Drawer title={p.name} sub={`${p.brand} · ${p.region} · ${p.medium} · rank ${row.rank} of ${ranking.length}`} onClose={onClose}
      foot={m==="target" ? <>
        <div className="tiny dim">Pricing is exact. Avails is an estimate until the solve.</div>
        <div style={{flex:1}}/>
        <Btn onClick={()=>setIds(row.custom)}>Reset</Btn>
        <Btn c="pri" disabled={JSON.stringify(ids)===JSON.stringify(row.custom)}
          onClick={()=>onCustom(ids)}>Apply, with a reason</Btn>
      </> : null}>
      <div className="tabs" style={{marginBottom:14}}>
        {[["why","Reasoning"],["ask","Interrogate"],["target","Targeting"],["mkt","Market position"]].map(([k,l])=>
          <button key={k} className={m===k?"on":""} onClick={()=>setM(k)}>{l}</button>)}
      </div>

      {m==="why" && <div className="col" style={{gap:12}}>
        <div className="row" style={{gap:12}}>
          <div className="scorebadge"><b>{row.total.toFixed(0)}</b><span>SCORE</span></div>
          <div className="grow tiny muted">Rank {row.rank}{row.moved ? ` — you moved it from ${row.sysRank}` : ", the position the system produced"}.
            The five criteria below are what put it there, and this reasoning travels into the plan brief and the
            approval package.</div>
        </div>
        {CRITERIA.map(c=>(
          <div key={c.k} className="card"><div className="card-b">
            <div className="row" style={{marginBottom:5}}>
              <b style={{fontSize:12}}>{c.label}</b>
              <Chip>weight {pct(c.w,0)}</Chip>
              <div style={{flex:1}}/>
              <b>{row.parts[c.k].toFixed(0)}</b>
            </div>
            <Bar v={row.parts[c.k]/100} c={row.parts[c.k]>70?"g":row.parts[c.k]>45?"":"a"}/>
            <div className="tiny muted" style={{marginTop:7, lineHeight:1.55}}>{row.why[c.k]}</div>
            <div className="mini dim" style={{marginTop:5}}>{c.help}</div>
          </div></div>
        ))}
      </div>}

      {m==="ask" && <div className="col" style={{gap:11}}>
        <div className="tiny muted">Pressure-test the choice and the ranking. These are the questions the desk gets
          asked at review, answered from the same evidence the ranking used.</div>
        {qs.map((x,i)=>(
          <div key={i} className="card"><div className="card-b">
            <div style={{fontWeight:600, fontSize:12.5, marginBottom:5}}>{x.q}</div>
            <div className="tiny muted" style={{lineHeight:1.6}}>{x.a}</div>
          </div></div>
        ))}
      </div>}

      {m==="target" && <div className="col" style={{gap:12}}>
        <div className="banner b"><span className="bi">Live</span>
          <div>As targeting changes, inventory and price change with it. Any breach of the brief's constraints is raised
            here, at the moment of customisation — not at optimisation and not at approval.</div></div>
        <div className="statgrid" style={{gridTemplateColumns:"1fr 1fr 1fr"}}>
          <Stat label="CPM" value={cpmf(preview.cpm)}
            delta={preview.cpm===p.openCpm ? "unchanged" : `${pctn((preview.cpm/p.openCpm-1)*100,1)} vs ${cpmf(p.openCpm)}`}
            tone={preview.cpm>FRAME.cpmCeiling?"bad":null}/>
          <Stat label="Avails" value={imps(preview.availK)}
            delta={preview.availK===p.availK ? "firm" : `${pctn((preview.availK/p.availK-1)*100,0)} · estimate`}/>
          <Stat label="In-demo" value={pct(preview.comp,0)}
            delta={preview.comp===p.demoComp ? "unchanged" : `from ${pct(p.demoComp,0)}`} tone={preview.comp>p.demoComp?"good":null}/>
        </div>
        {previewBreach.map((b,i)=><div key={i} className="banner r"><span className="bi">Breach</span><div>{b.text}</div></div>)}
        {ids.length>0 && preview.cpm*1 > 0 && (
          <div className="banner a"><span className="bi">Trade-off</span>
            <div>This buys {pctn((preview.comp/p.demoComp-1)*100,0)} more in-demo delivery and costs
              {" "}{pctn((preview.cpm/p.openCpm-1)*100,0)} on CPM and {pctn((1-preview.availK/p.availK)*100,0)} of the
              sellable inventory. At this price the {p.region} envelope buys {imps(DEAL.netBudget*FRAME.regionSplit[p.region]*0.3/preview.cpm)} on a typical line.</div></div>
        )}
        <div className="col" style={{gap:8}}>
          {customFor(p).map(o=>{
            const on = ids.includes(o.id);
            return (
              <button key={o.id} className="card" style={{textAlign:"left", borderColor: on?"var(--accent)":"var(--line)"}}
                onClick={()=>setIds(on ? ids.filter(x=>x!==o.id) : [...ids, o.id])}>
                <div className="card-b" style={{padding:"10px 12px"}}>
                  <div className="row">
                    <span className={"sw" + (on?" on":"")}><i/></span>
                    <b style={{fontSize:12.5}}>{o.label}</b>
                    <div style={{flex:1}}/>
                    <span className="tiny dim">{pctn((o.cpmX-1)*100,0)} CPM · {pctn((o.availX-1)*100,0)} avails</span>
                  </div>
                  <div className="tiny muted" style={{marginTop:4, paddingLeft:39}}>{o.desc}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>}

      {m==="mkt" && <div className="col" style={{gap:12}}>
        <dl className="kv">
          <dt>Format</dt><dd>{p.format}</dd>
          <dt>Placement</dt><dd>{p.placement}</dd>
          <dt>Brand safety</dt><dd>{p.brandSafe}</dd>
          <dt>Floor CPM</dt><dd>{cpmf(p.floorCpm)}</dd>
          <dt>Card CPM</dt><dd>{cpmf(p.cardCpm)}</dd>
          <dt>Opening CPM</dt><dd><b>{cpmf(p.openCpm)}</b></dd>
          <dt>Market benchmark</dt><dd>{cpmf((BENCH[p.region+"|"+p.medium]||{}).cpm)} — {(BENCH[p.region+"|"+p.medium]||{}).note}</dd>
          <dt>Sellable avails</dt><dd>{imps(p.availK)} across {FLIGHT.weeks} weeks</dd>
          <dt>1+ reach ceiling</dt><dd>{imps(p.reachK)} people</dd>
          {p.viewability!=null && <><dt>Viewability</dt><dd>{pct(p.viewability,0)} MRC</dd></>}
          {p.vcr!=null && <><dt>Completion</dt><dd>{pct(p.vcr,1)}</dd></>}
          {p.grp!=null && <><dt>GRPs available</dt><dd>{p.grp}</dd></>}
          {p.cpp!=null && <><dt>Cost per point</dt><dd>{money(p.cpp)}</dd></>}
          <dt>Attention index</dt><dd>{p.attention}</dd>
          <dt>P&amp;I posture</dt><dd>{POSTURE_LABEL[p.yieldPosture]}</dd>
        </dl>
        <div className="banner b"><span className="bi">Desk note</span><div>{p.note}</div></div>
        {positionsFor(p.id).map(x=>(
          <div key={x.id} className="banner a"><span className="bi">{x.id}</span>
            <div><b>{x.title}</b> — {x.text}<div className="tiny" style={{marginTop:3}}>Reason: {x.reason}</div></div></div>
        ))}
      </div>}
    </Drawer>
  );
};
