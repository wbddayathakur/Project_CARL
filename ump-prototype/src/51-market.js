/* =============================================================================
   51-market.js — global market reference.
   The data a planner currently pulls from four systems and three spreadsheets,
   on one surface, in a grid they already know how to read.
   ============================================================================= */
const Market = () => {
  const [region, setRegion] = useState("ALL");
  const [medium, setMedium] = useState("ALL");
  const [view, setView] = useState("grid");

  const rows = useMemo(() => PRODUCTS.filter(p =>
    (region === "ALL" || p.region === region) && (medium === "ALL" || p.medium === medium)
  ), [region, medium]);

  const cols = [
    { key:"id", label:"ID", w:44, get:r=>r.id, cell:r=><span className="mono">{r.id}</span> },
    { key:"brand", label:"Brand", w:130, get:r=>r.brand,
      cell:r=><span className="row" style={{gap:6}}><span className="dot" style={{background:BRAND_COLOR[r.brand]||"#8a95a0"}}/>{r.brand}</span> },
    { key:"name", label:"Product / package", w:290, get:r=>r.name },
    { key:"region", label:"Region", w:62, get:r=>r.region },
    { key:"medium", label:"Medium", w:66, get:r=>r.medium,
      cell:r=><Chip c={r.medium==="Digital"?"b":"a"}>{r.medium}</Chip> },
    { key:"format", label:"Format", w:118, get:r=>r.format },
    { key:"placement", label:"Placement", w:210, get:r=>r.placement },
    { key:"availK", label:"Avails (imps)", w:92, align:"r", get:r=>imps(r.availK), raw:r=>r.availK*1000, help:"Sellable to this advertiser across the 17-week flight, after holdbacks" },
    { key:"floorCpm", label:"Floor CPM", w:74, align:"r", get:r=>cpmf(r.floorCpm), raw:r=>r.floorCpm },
    { key:"cardCpm", label:"Card CPM", w:74, align:"r", get:r=>cpmf(r.cardCpm), raw:r=>r.cardCpm },
    { key:"openCpm", label:"Open CPM", w:76, align:"r", get:r=>cpmf(r.openCpm), raw:r=>r.openCpm,
      cell:r=><b>{cpmf(r.openCpm)}</b> },
    { key:"bench", label:"vs benchmark", w:92, align:"r",
      get:r=>{ const b=(BENCH[r.region+"|"+r.medium]||{}).cpm; return b?pctn((r.openCpm/b-1)*100,0):"—"; },
      raw:r=>{ const b=(BENCH[r.region+"|"+r.medium]||{}).cpm; return b?((r.openCpm/b-1)*100).toFixed(1):""; },
      cell:r=>{ const b=(BENCH[r.region+"|"+r.medium]||{}).cpm; if(!b) return "—";
        const d=(r.openCpm/b-1)*100;
        return <span style={{color: d>12?"var(--bad)": d<-8?"var(--good)":"var(--ink-2)"}}>{d>0?"+":""}{d.toFixed(0)}%</span>; } },
    { key:"demoComp", label:"A25-54 comp", w:88, align:"r", get:r=>pct(r.demoComp,0), raw:r=>r.demoComp },
    { key:"reachK", label:"1+ reach ceiling", w:104, align:"r", get:r=>imps(r.reachK), raw:r=>r.reachK*1000 },
    { key:"view", label:"Viewability", w:82, align:"r", get:r=>r.viewability==null?"n/a":pct(r.viewability,0), raw:r=>r.viewability??"" },
    { key:"vcr", label:"VCR", w:60, align:"r", get:r=>r.vcr==null?"n/a":pct(r.vcr,1), raw:r=>r.vcr??"" },
    { key:"grp", label:"GRPs", w:56, align:"r", get:r=>r.grp==null?"n/a":num(r.grp), raw:r=>r.grp??"" },
    { key:"cpp", label:"CPP", w:66, align:"r", get:r=>r.cpp==null?"n/a":money(r.cpp), raw:r=>r.cpp??"" },
    { key:"attention", label:"Attention idx", w:88, align:"r", get:r=>r.attention,
      cell:r=><div className="row" style={{gap:6, justifyContent:"flex-end"}}><span>{r.attention}</span>
        <div className="bar" style={{width:34}}><i style={{width:r.attention+"%"}}/></div></div> },
    { key:"posture", label:"P&I posture", w:104, get:r=>POSTURE_LABEL[r.yieldPosture],
      cell:r=><Chip c={{push:"g",neutral:"",hold:"a",dump:"r"}[r.yieldPosture]}>{POSTURE_LABEL[r.yieldPosture]}</Chip> },
    { key:"kpiFit", label:"KPI fit", w:60, align:"r", get:r=>r.kpiFit },
    { key:"note", label:"Desk note", w:340, get:r=>r.note },
  ];

  const totalAvail = rows.reduce((s,r)=>s+r.availK,0);
  const wCpm = rows.length ? rows.reduce((s,r)=>s+r.openCpm*r.availK,0)/totalAvail : 0;

  const spendByRegion = REGIONS.map(r => ({
    l: r.id, c: {US:"#0b57d0",EMEA:"#0d7a4e",LATAM:"#e8641a",APAC:"#5b3fb8"}[r.id],
    v: MARKET_CONTEXT.filter(m=>m.region===r.id).reduce((s,m)=>s+m.spendQ,0),
  }));

  return (
    <div className="pad">
      <div className="row" style={{marginBottom:14, alignItems:"flex-start"}}>
        <div>
          <h2 style={{fontSize:17}}>Global market</h2>
          <div className="muted" style={{maxWidth:780, marginTop:4}}>
            WBD linear and digital supply across four regions, with the market benchmarks, category spend and
            competitive read the planner would otherwise assemble by hand. Everything on this page is what Discovery
            ranks against.
          </div>
        </div>
        <div style={{flex:1}}/>
        <Seg value={view} onChange={setView} opts={[{v:"grid",l:"Supply grid"},{v:"context",l:"Market context"}]}/>
      </div>

      <div className="statgrid" style={{marginBottom:14}}>
        <Stat label="Products in view" value={rows.length} delta={`${PRODUCTS.length} in the portfolio`}/>
        <Stat label="Sellable impressions" value={imps(totalAvail)} delta={FLIGHT.label}/>
        <Stat label="Avails-weighted CPM" value={cpmf(wCpm)} delta="opening negotiated, blended"/>
        <Stat label="In-market universe" value={imps(INMARKET_UNIVERSE) + " people"} delta="A25-54, four regions"/>
        <Stat label="Category spend, quarter" value={"$" + num(MARKET_CONTEXT.reduce((s,m)=>s+m.spendQ,0)) + "M"} delta="Home care / laundry, all regions"/>
      </div>

      {view === "grid" ? <>
        <div className="row wrap" style={{marginBottom:10, gap:8}}>
          <span className="sec-title">Region</span>
          {["ALL",...REGIONS.map(r=>r.id)].map(r=>
            <button key={r} className={"pill" + (region===r?" on":"")} onClick={()=>setRegion(r)}>{r === "ALL" ? "All" : r}</button>)}
          <div style={{width:10}}/>
          <span className="sec-title">Medium</span>
          {["ALL","Linear","Digital"].map(m=>
            <button key={m} className={"pill" + (medium===m?" on":"")} onClick={()=>setMedium(m)}>{m === "ALL" ? "All" : m}</button>)}
        </div>
        <XL name="WBD_global_supply" cols={cols} rows={rows} height={520}
          sub="Linear rows carry GRPs and CPP; digital rows carry viewability and VCR. Blank means the metric does not apply to that medium."/>
        <div className="g3" style={{marginTop:14}}>
          <Card title="Population universes" sub="000s of people, the denominators every reach number uses">
            <table className="tb">
              <thead><tr><th>Region</th><th className="r">A25-54</th><th className="r">W25-54</th><th className="r">P18-49</th><th className="r">TV HH</th></tr></thead>
              <tbody>{REGIONS.map(r=>(
                <tr key={r.id}><td><b>{r.id}</b> <span className="dim tiny">{r.markets.join(" ")}</span></td>
                  {["A25-54","W25-54","P18-49","HH"].map(k=><td key={k} className="r">{num(UNIVERSE[r.id][k])}</td>)}</tr>))}
                <tr><td><b>Total</b></td>
                  {["A25-54","W25-54","P18-49","HH"].map(k=><td key={k} className="r"><b>{num(REGIONS.reduce((s,r)=>s+UNIVERSE[r.id][k],0))}</b></td>)}</tr>
              </tbody>
            </table>
          </Card>
          <Card title="Market CPM benchmarks" sub="What a comparable unit clears at — price workability is judged against these">
            <table className="tb">
              <thead><tr><th>Region · medium</th><th className="r">Benchmark</th><th>Definition</th></tr></thead>
              <tbody>{Object.entries(BENCH).map(([k,v])=>(
                <tr key={k}><td>{k.replace("|"," · ")}</td><td className="r"><b>{cpmf(v.cpm)}</b></td><td className="tiny muted">{v.note}</td></tr>))}
              </tbody>
            </table>
          </Card>
          <Card title="Supply position for the flight" sub="Sellout against plan — this is what P&I reads at approval">
            <div className="col" style={{gap:9}}>
              {SUPPLY.map((s,i)=>(
                <div key={i}>
                  <div className="row tiny" style={{justifyContent:"space-between"}}>
                    <span>{s.region} · {s.medium}</span>
                    <span className="dim">{pctn(s.selloutPct,0)} sold · {s.trend}</span>
                  </div>
                  <Bar v={s.selloutPct/100} c={s.selloutPct>72?"a":""}/>
                  {s.scarce.length>0 && <div className="mini dim" style={{marginTop:2}}>Scarce: {s.scarce.join(", ")}</div>}
                </div>
              ))}
            </div>
          </Card>
        </div>
      </> : <>
        <div className="split">
          <div className="col" style={{gap:14}}>
            <Card title="Category spend and direction" sub="Home care / laundry, current quarter, $M">
              <XL name="category_spend" height={280} cols={[
                { key:"region", label:"Region", w:70, get:r=>r.region },
                { key:"medium", label:"Medium", w:70, get:r=>r.medium },
                { key:"spendQ", label:"Spend $M", w:80, align:"r", get:r=>"$"+num(r.spendQ)+"M", raw:r=>r.spendQ },
                { key:"yoy", label:"YoY", w:64, align:"r", get:r=>(r.yoy>0?"+":"")+r.yoy.toFixed(1)+"%", raw:r=>r.yoy,
                  cell:r=><span style={{color:r.yoy>0?"var(--good)":"var(--bad)"}}>{r.yoy>0?"+":""}{r.yoy.toFixed(1)}%</span> },
                { key:"cpmIdx", label:"CPM index", w:80, align:"r", get:r=>r.cpmIdx },
                { key:"note", label:"Read", w:520, get:r=>r.note },
              ]} rows={MARKET_CONTEXT}/>
            </Card>
            <Card title="Competitive context" sub="Planner-triggered research. [OPEN] this source has no provenance class on the ladder yet — nothing is derived from it.">
              <XL name="competitive" height={240} cols={[
                { key:"brand", label:"Advertiser", w:150, get:r=>r.brand },
                { key:"region", label:"Region", w:70, get:r=>r.region },
                { key:"spend", label:"Spend $M", w:80, align:"r", get:r=>"$"+r.spend.toFixed(1)+"M", raw:r=>r.spend },
                { key:"mix", label:"Digital / linear mix", w:150, get:r=>r.mix },
                { key:"note", label:"What they are doing", w:520, get:r=>r.note },
              ]} rows={COMPETITIVE}/>
            </Card>
          </div>
          <div className="col sticky" style={{gap:14}}>
            <Card title="Category spend by region">
              <div className="row" style={{gap:16}}>
                <Donut parts={spendByRegion} center={<>
                  <b style={{fontSize:15}}>${num(spendByRegion.reduce((s,r)=>s+r.v,0))}M</b>
                  <span className="mini dim">quarter</span></>}/>
                <div className="grow"><HBars rows={spendByRegion} fmt={v=>"$"+v+"M"}/></div>
              </div>
            </Card>
            <Card title="Digital share of category, by region">
              <HBars rows={REGIONS.map(r=>{
                const d = MARKET_CONTEXT.find(m=>m.region===r.id&&m.medium==="Digital")?.spendQ||0;
                const l = MARKET_CONTEXT.find(m=>m.region===r.id&&m.medium==="Linear")?.spendQ||0;
                return { l:r.id, v: d/(d+l)*100 };
              })} fmt={v=>v.toFixed(0)+"%"} max={100}/>
              <div className="tiny muted" style={{marginTop:10}}>
                LATAM and APAC are still linear-majority categories. A digital-only plan in those regions buys
                efficiency and gives up reach — which is exactly the trade the Discovery ranking has to make legible.
              </div>
            </Card>
            <Assist title="What this means for the open brief">
              Persil has pulled out of US cable news entirely and put the money into CTV, and the category's US digital
              spend is up 18% year on year. That is the market the advertiser's own news exclusion is sitting inside —
              worth saying out loud in the plan brief rather than presenting the exclusion as a constraint we merely obeyed.
            </Assist>
          </div>
        </div>
      </>}
    </div>
  );
};
