/* =============================================================================
   27-rag.js — the Products / Packaging system.

   From the Flow Architecture note: the product catalogue is not a table the
   planner browses. Targeting templates, ad product configs and content
   inventory packages come out of FreeWheel and Operative; reference pricing
   and product KPIs live in spreadsheets and documents. All of it is vectorised
   into one product RAG, and Discovery asks it questions in the planner's own
   words:

     1. What product meets these KPIs
     2. What customisations are available on this product
     3. I want to exclude Mature content off this product targeting

   The retrieval here is deterministic rather than embedded — the point of the
   surface is the shape of the interaction and the provenance of the answer,
   which is what has to be right before anyone builds the real index. Every
   answer names the configs and documents it was drawn from, so a planner can
   go and check a number rather than trusting it.
   ============================================================================= */

/* The corpus, and where each part of it actually comes from. */
const RAG_SOURCES = [
  { id:"FW-TT",  name:"Targeting templates",        sys:"FreeWheel", kind:"config", n:214,
    desc:"Every targeting dimension sellable against a product, and which combinations are legal." },
  { id:"OP-APC", name:"Ad product configs",         sys:"Operative", kind:"config", n:186,
    desc:"Product definitions, formats, pod rules, guarantee types." },
  { id:"FW-CIP", name:"Content inventory packages", sys:"FreeWheel", kind:"config", n:97,
    desc:"Which titles and dayparts sit inside each package, and the exclusion lists." },
  { id:"DOC-RP", name:"Reference pricing",          sys:"Spreadsheet", kind:"doc", n:1,
    desc:"Rate card, floors, and the regional CPM benchmarks. Owned by P&I, refreshed quarterly." },
  { id:"DOC-KPI",name:"Product KPIs",               sys:"Doc", kind:"doc", n:1,
    desc:"Measured delivery by product: viewability, VCR, attention, in-demo composition." },
];

/* The exclusion vocabulary FreeWheel actually carries, so "exclude mature
   content" resolves to a real config rather than a free-text wish. */
/* An exclusion only means something on inventory that carries the thing being
   excluded. Saying "supported on all 22 products" would be a lie the planner
   would catch the first time they checked. */
const RAG_EXCLUSIONS = [
  { k:"mature",  label:"Mature / TV-MA content", cfg:"FW-CIP · rating_exclude=[TV-MA,R]",
    availX:0.78, cpmX:1.06, note:"Removes Adult Swim entirely and roughly a fifth of HBO Max originals inventory.",
    applies: p => /HBO Max|Adult Swim|TNT/.test(p.brand) },
  { k:"ugc",     label:"UGC-adjacent placements", cfg:"FW-CIP · ugc_adjacent=false",
    availX:0.78, cpmX:1.05, note:"The lever that clears the 80% viewability floor on Bleacher Report.",
    applies: p => p.medium === "Digital" },
  { k:"news",    label:"Hard-news adjacency", cfg:"FW-TT · vertical_exclude=[news]",
    availX:0.94, cpmX:1.02, note:"Already applied at eligibility for this brief — CNN products are out.",
    applies: p => /CNN/.test(p.brand) },
  { k:"sport",   label:"Live sport", cfg:"FW-CIP · package_exclude=[live_sport]",
    availX:0.71, cpmX:0.94, note:"Takes out the held Bleacher Report and TNT sport packages.",
    applies: p => /Bleacher|TNT Sports|Eurosport|TNT/.test(p.brand) },
];

function ragMoney(n){ return "$" + Number(n).toFixed(2); }

/* -----------------------------------------------------------------------------
   Query resolution. Intent is matched on the words a planner would actually
   use; each intent returns rows plus the sources it drew on.
-------------------------------------------------------------------------------*/
function ragQuery(q, ctx){
  const s = String(q || "").toLowerCase().trim();
  const c = ctx || {};
  if (!s) return null;

  const has = (...w) => w.some(x => s.includes(x));
  const region = FRAME.regions.find(r => s.includes(r.toLowerCase()));
  const named  = PRODUCTS.find(p =>
    s.includes(p.brand.toLowerCase()) || s.includes(p.name.toLowerCase().split(" — ")[0]));
  const budget = (s.match(/\$?\s?(\d+(?:\.\d+)?)\s?(?:cpm|dollars?)?/) || [])[1];

  /* 3 — exclusions */
  const exc = RAG_EXCLUSIONS.find(e => s.includes(e.k)) ||
              (has("exclude","without","off","remove","block") ? RAG_EXCLUSIONS[0] : null);
  if (exc && has("exclude","without","off","remove","block","mature","ugc")){
    const scope = PRODUCTS.filter(p => (!region || p.region === region) && exc.applies(p));
    const pool = named ? (exc.applies(named) ? [named] : []) : scope;
    if (!pool.length) return {
      intent:"exclusion",
      headline:`${exc.label} — nothing in scope carries it`,
      body:<>The exclusion is a real config (<span className="mono">{exc.cfg}</span>) but none of the products
        {named ? <> on {named.name}</> : region ? <> in {region}</> : null} carry this content in the first place.
        Applying it would cost avails and change nothing.</>,
      rows:[], sources:["FW-CIP"],
      caveat:"An exclusion with no effect is worth knowing about — it is a line of negotiation you can give away free.",
    };
    return {
      intent:"exclusion",
      headline:`${exc.label} — applies to ${pool.length} product${pool.length===1?"":"s"}, at a cost`,
      body:<>The exclusion resolves to <span className="mono">{exc.cfg}</span>, which is a real targeting
        dimension rather than a note on the insertion order. {exc.note}</>,
      rows: pool.slice(0,6).map(p => ({
        k:p.id, a:p.name, b:`avails ${imps(Math.round(p.availK*exc.availX))} (was ${imps(p.availK)})`,
        c:`${ragMoney(p.openCpm*exc.cpmX)} (was ${ragMoney(p.openCpm)})`,
        d:`${Math.round((1-exc.availX)*100)}% of inventory removed` })),
      sources:["FW-CIP","FW-TT","DOC-RP"],
      caveat:"Applying it here sets it on the product for this plan only. It does not change the package.",
    };
  }

  /* 2 — customisations available on a product */
  if (has("customis","customiz","options","levers","can i","available on")){
    const p = named || (c.top && c.top.p);
    const opts = CUSTOM_OPTIONS.filter(o =>
      o.medium === "both" || !p || o.medium.toLowerCase() === p.medium.toLowerCase());
    return {
      intent:"customisation",
      headline: p ? `${opts.length} customisations available on ${p.name}` : `${opts.length} customisations in the catalogue`,
      body:<>Each one is a template that already exists in the ad server, so the avails and price consequence is
        known before you commit to it — not estimated afterwards.</>,
      rows: opts.map(o => ({
        k:o.id, a:o.label, b:o.desc,
        c: o.cpmX !== 1 ? `CPM ×${o.cpmX.toFixed(2)}` : "no price change",
        d: o.availX !== 1 ? `avails ×${o.availX.toFixed(2)}` : "no avails change" })),
      sources:["FW-TT","OP-APC","DOC-RP"],
      caveat:"Setting one re-scores the product and can move it in the ranking. That is the point of setting it in Discovery rather than at trafficking.",
    };
  }

  /* price */
  if (has("cpm","price","cheap","under","below","budget","expensive") && budget){
    const cap = parseFloat(budget);
    const pool = PRODUCTS.filter(p => (!region || p.region === region) && p.openCpm <= cap)
      .sort((a,b)=>b.kpiFit-a.kpiFit);
    return {
      intent:"price",
      headline:`${pool.length} products clear ${ragMoney(cap)}${region?` in ${region}`:""}`,
      body:<>Open CPM, not card. The floor is what P&amp;I will not go below and is a different number —
        both are shown, because a product that clears your ceiling but sits on its floor has no negotiating room.</>,
      rows: pool.slice(0,8).map(p => ({
        k:p.id, a:p.name, b:`${p.region} · ${p.medium}`,
        c:`open ${ragMoney(p.openCpm)} · floor ${ragMoney(p.floorCpm)}`,
        d:`KPI fit ${p.kpiFit}` })),
      sources:["DOC-RP","OP-APC"],
      caveat:"Reference pricing is refreshed quarterly. A number older than the quarter is a starting position, not a rate.",
    };
  }

  /* 1 — which product meets these KPIs (the default, and the most common ask) */
  const wantsReach = has("reach","3+","frequency","incremental","light");
  const pool = PRODUCTS
    .filter(p => !region || p.region === region)
    .map(p => ({ p, fit: p.kpiFit + (wantsReach ? p.reachK/1000 : 0) }))
    .sort((a,b)=>b.fit-a.fit);
  return {
    intent:"kpi",
    headline: region
      ? `Best fit against the brief's KPIs in ${region}`
      : "Best fit against the brief's KPIs, across all four regions",
    body:<>Matched on the KPIs in the intake brief — {pct(FRAME.reachGoal3,0)} 3+ reach against {FRAME.demo},
      digital blended CPM under {cpmf(FRAME.cpmCeiling)}, viewability at or above {pct(FRAME.viewFloor,0)}.
      This is the same measured delivery the ranking scores on, so the two cannot disagree.</>,
    rows: pool.slice(0,7).map(({p}) => ({
      k:p.id, a:p.name, b:`${p.region} · ${p.medium} · ${p.format}`,
      c:`KPI fit ${p.kpiFit} · reach ${imps(p.reachK)}`,
      d:`${pct(p.demoComp,0)} in demo${p.viewability?` · ${pct(p.viewability,0)} viewable`:""}` })),
    sources:["DOC-KPI","OP-APC","FW-CIP"],
    caveat:"KPI fit is measured delivery from the last four quarters, not a promise. It is one of five ranking criteria, not the ranking.",
  };
}

/* --------------------------------------------------------------- the surface */
const RAG_EXAMPLES = [
  "What product meets these KPIs?",
  "What customisations are available on HBO Max?",
  "I want to exclude Mature content off this product targeting",
  "What clears $30 CPM in EMEA?",
];

const ProductRAG = ({ctx}) => {
  const [q, setQ] = useState("");
  const [asked, setAsked] = useState(null);
  const res = useMemo(() => (asked ? ragQuery(asked, ctx) : null), [asked, ctx]);
  const go = (text) => { setQ(text); setAsked(text); };

  return (
    <Card title="Product knowledge"
      sub="Targeting templates, product configs and inventory packages out of FreeWheel and Operative; pricing and KPIs out of the spreadsheets. Asked in your words."
      right={<Chip c="n">{RAG_SOURCES.reduce((s,x)=>s+x.n,0)} configs indexed</Chip>}>

      <div className="row" style={{gap:8}}>
        <input className="inp" style={{flex:1}} value={q} placeholder="Ask about products, KPIs, customisations, exclusions, price…"
          onChange={e=>setQ(e.target.value)} onKeyDown={e=>{ if (e.key==="Enter") go(q); }}/>
        <Btn c="pri" onClick={()=>go(q)} disabled={!q.trim()}>Ask</Btn>
      </div>

      <div className="row wrap" style={{gap:6, marginTop:9}}>
        {RAG_EXAMPLES.map((x,i)=>
          <button key={i} className="chip o" style={{cursor:"pointer"}} onClick={()=>go(x)}>{x}</button>)}
      </div>

      {res && <>
        <div className="hr"/>
        <div style={{fontSize:13, fontWeight:600, marginBottom:4}}>{res.headline}</div>
        <div className="tiny muted" style={{lineHeight:1.6, marginBottom:11}}>{res.body}</div>

        <div className="col" style={{gap:0}}>
          {res.rows.length === 0 && <div className="tiny dim">No rows — see the note above.</div>}
          {res.rows.map((r,i)=>(
            <div key={r.k} className="row" style={{gap:10, padding:"7px 0",
              borderTop: i ? "1px solid var(--line)" : "none", alignItems:"baseline"}}>
              <span className="mono tiny" style={{width:34, flexShrink:0}}>{r.k}</span>
              <div style={{flex:"1 1 200px", minWidth:0}}>
                <div style={{fontSize:12}}>{r.a}</div>
                <div className="mini dim">{r.b}</div>
              </div>
              <div style={{flex:"0 1 190px", minWidth:0, textAlign:"right"}}>
                <div className="tiny">{r.c}</div>
                <div className="mini dim">{r.d}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="hr"/>
        <div className="lbl">Drawn from</div>
        <div className="col" style={{gap:5}}>
          {res.sources.map(id => { const s = RAG_SOURCES.find(x=>x.id===id); if (!s) return null;
            return (
              <div key={id} className="row" style={{gap:8, alignItems:"baseline"}}>
                <Chip c={s.kind==="config"?"b":"a"}>{s.sys}</Chip>
                <div style={{minWidth:0}}>
                  <span className="tiny">{s.name}</span>{" "}
                  <span className="mini dim">· {s.n > 1 ? `${s.n} configs` : "1 document"} · {s.desc}</span>
                </div>
              </div>
            ); })}
        </div>
        <div className="tiny dim" style={{marginTop:9}}>{res.caveat}</div>
      </>}

      {!res && <div className="tiny dim" style={{marginTop:11, lineHeight:1.6}}>
        [OPEN] The real index is vectorised over the configs themselves, so a product that changes in Operative
        changes here without anyone re-typing it. What is not settled is refresh — a planner reading a stale
        avails number is worse than one who knows to go and look.
      </div>}
    </Card>
  );
};
