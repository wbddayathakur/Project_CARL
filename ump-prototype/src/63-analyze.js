/* =============================================================================
   63-analyze.js — Analyze.
   A judgement step. The plan is read here; every change it provokes is made back
   in Discovery. Versions are scored in isolation, never ranked against each
   other — ranking versions comes close to choosing for the planner.
   ============================================================================= */
const Analyze = ({S}) => {
  const { st, up, log } = S;
  const toast = useToast();
  const [sel, setSel] = useState(null);
  const [cmp, setCmp] = useState([]);
  const [commit, setCommit] = useState(null);
  const v = st.versions;
  const cur = sel ? v.find(x=>x.id===sel) : v[v.length-1];
  const gate = useMemo(() => evaluateGate("analyze", st, {}), [st]);

  useEffect(()=>{ if (v.length && !sel) setSel(v[v.length-1].id); }, [v.length]);
  if (!v.length) return (
    <div className="pad" style={{padding:0}}>
      <Card title="Nothing to analyze yet">
        <div className="muted">Analyze reads saved plan versions. Run the optimiser and save one first.</div>
        <Btn c="pri sm" style={{marginTop:11}} onClick={()=>up({phase:"strategize"})}>Go to Strategize &amp; iterate</Btn>
      </Card>
    </div>
  );

  const toggleCmp = (id) => setCmp(c => c.includes(id) ? c.filter(x=>x!==id) : [...c, id].slice(-3));
  const cmpList = cmp.length >= 2 ? v.filter(x=>cmp.includes(x.id)) : [];

  const rows = [
    ["Net allocated", x=>money(x.roll.spend), x=>x.roll.spend],
    ["Impressions", x=>imps(x.roll.impsK), x=>x.roll.impsK],
    ["1+ reach", x=>pct(x.roll.reach1,1), x=>x.roll.reach1],
    ["3+ reach — the stated KPI", x=>pct(x.roll.reach3,1), x=>x.roll.reach3],
    ["Average frequency", x=>x.roll.avgFreq.toFixed(2), x=>x.roll.avgFreq],
    ["Blended CPM", x=>cpmf(x.roll.blendedCpm), x=>-x.roll.blendedCpm],
    ["Digital CPM", x=>cpmf(x.roll.digCpm), x=>-x.roll.digCpm],
    ["Linear share", x=>pct(x.roll.linearPct,1), x=>x.roll.linearPct],
    ["Concentration (HHI)", x=>x.roll.hhi.toFixed(3), x=>-x.roll.hhi],
    ["Lines", x=>x.lines.length, x=>x.lines.length],
    ["Overrides", x=>Object.keys(x.overrides).length, x=>-Object.keys(x.overrides).length],
    ["Rubric", x=>x.rubric.total.toFixed(1), x=>x.rubric.total],
  ];

  return (
    <div className="split">
      <div className="col" style={{gap:14}}>
        <div className="row wrap" style={{gap:10}}>
          {v.map(x=>(
            <button key={x.id} className="card" style={{textAlign:"left", flex:"1 1 240px", minWidth:240,
              borderColor: x.id===sel ? "var(--accent)" : x.id===st.committed ? "var(--good)" : "var(--line)"}}
              onClick={()=>setSel(x.id)}>
              <div className="card-b" style={{padding:"12px 14px"}}>
                <div className="row" style={{marginBottom:7}}>
                  <Chip c="n">{x.id}</Chip>
                  <b style={{fontSize:12.5}}>{x.name}</b>
                  <div style={{flex:1}}/>
                  {x.id===st.committed && <Chip c="g">COMMITTED</Chip>}
                </div>
                <div className="row" style={{gap:12}}>
                  <div className="scorebadge" style={{width:48, height:48,
                    borderColor: x.rubric.total>=80?"var(--good)":x.rubric.total>=65?"var(--warn)":"var(--bad)"}}>
                    <b style={{fontSize:17}}>{x.rubric.total.toFixed(0)}</b><span style={{fontSize:7.5}}>RUBRIC</span></div>
                  <div className="grow tiny">
                    <div className="row" style={{justifyContent:"space-between"}}><span className="dim">3+ reach</span><b>{pct(x.roll.reach3,1)}</b></div>
                    <div className="row" style={{justifyContent:"space-between"}}><span className="dim">Blended CPM</span><b>{cpmf(x.roll.blendedCpm)}</b></div>
                    <div className="row" style={{justifyContent:"space-between"}}><span className="dim">Linear</span><b>{pct(x.roll.linearPct,0)}</b></div>
                    <div className="row" style={{justifyContent:"space-between"}}><span className="dim">Overrides</span><b>{Object.keys(x.overrides).length}</b></div>
                  </div>
                </div>
                {x.note && <div className="tiny muted" style={{marginTop:8, fontStyle:"italic"}}>“{x.note}”</div>}
                <div className="row" style={{marginTop:9}}>
                  <span className="mini dim">{x.at} · strategy brief v{x.strategyVersion}</span>
                  <div style={{flex:1}}/>
                  <span className="mini" style={{color: cmp.includes(x.id) ? "var(--accent)" : "var(--ink-3)"}}
                    onClick={(e)=>{e.stopPropagation(); toggleCmp(x.id);}}>
                    {cmp.includes(x.id) ? "✓ comparing" : "compare"}</span>
                </div>
              </div>
            </button>
          ))}
          {v.length < 4 && (
            <button className="card" style={{flex:"0 0 168px", borderStyle:"dashed"}} onClick={()=>up({phase:"discovery"})}>
              <div className="card-b" style={{padding:"12px 14px"}}>
                <b style={{fontSize:12.5}}>Create another</b>
                <div className="tiny muted" style={{marginTop:4}}>Returns to Discovery to re-order or re-target, then
                  produces a further version.</div>
              </div>
            </button>
          )}
        </div>

        {cmpList.length >= 2 && (
          <Card title="Comparison" sub="Deltas only. No version is ranked against another — that would be choosing for you."
            right={<Btn c="sm gho" onClick={()=>setCmp([])}>Clear</Btn>}>
            <table className="tb">
              <thead><tr><th style={{width:230}}>Measure</th>
                {cmpList.map(x=><th key={x.id} className="r">{x.id} · {x.name}</th>)}</tr></thead>
              <tbody>{rows.map(([label, fmt, val])=>{
                const vals = cmpList.map(val), best = Math.max(...vals);
                return <tr key={label}><td>{label}</td>
                  {cmpList.map((x,i)=><td key={x.id} className="r"
                    style={vals[i]===best && vals.some(z=>z!==best) ? {fontWeight:600, color:"var(--good)"} : null}>{fmt(x)}</td>)}
                </tr>;
              })}</tbody>
            </table>
            <div className="hr"/>
            <div className="lbl">Line-level differences</div>
            <table className="tb">
              <thead><tr><th>Line</th>{cmpList.map(x=><th key={x.id} className="r">{x.id}</th>)}</tr></thead>
              <tbody>{Array.from(new Set(cmpList.flatMap(x=>x.lines.map(l=>l.pid)))).map(pid=>{
                const name = cmpList.flatMap(x=>x.lines).find(l=>l.pid===pid).name;
                return <tr key={pid}><td className="tiny">{name}</td>
                  {cmpList.map(x=>{ const l = x.lines.find(y=>y.pid===pid);
                    return <td key={x.id} className="r tiny">{l ? money(l.spend) : <span className="dim">not in</span>}</td>; })}
                </tr>;
              })}</tbody>
            </table>
          </Card>
        )}

        {cur && <>
          <Card title={`${cur.id} · ${cur.name}`} sub={`Plan Version Analysis brief · derived ${cur.at}`}
            right={<div className="row" style={{gap:6}}>
              <Btn c="sm" onClick={()=>{ up({phase:"discovery"}); toast("Back to Discovery — the levers are all there"); }}>Update product</Btn>
              <Btn c="sm" onClick={()=>{
                const id = "PV-" + String.fromCharCode(65 + st.versions.length);
                up(s=>({ versions:[...s.versions, {...cur, id, name: cur.name + " (fork)", parent: cur.id, at: NOW()}] }));
                log("edit", `${cur.id} forked to ${id} — a new line of exploration without returning through Discovery.`);
                toast("Forked to " + id); }}>Fork</Btn>
              {st.committed === cur.id
                ? <Chip c="g">COMMITTED</Chip>
                : <Btn c="pri sm" onClick={()=>setCommit(cur)}>Commit and share with P&amp;I</Btn>}
            </div>}>
            <div className="statgrid" style={{marginBottom:14}}>
              <Stat label="Net allocated" value={money1(cur.roll.spend)} delta={pct(cur.roll.spend/DEAL.netBudget,1) + " of budget"}/>
              <Stat label="3+ reach" value={pct(cur.roll.reach3,1)} delta={`goal ${pct(FRAME.reachGoal3,1)}`}
                tone={cur.roll.reach3>=FRAME.reachGoal3?"good":"bad"}/>
              <Stat label="1+ reach" value={pct(cur.roll.reach1,1)} delta={`goal ${pct(FRAME.reachGoal1,0)}`}
                tone={cur.roll.reach1>=FRAME.reachGoal1?"good":"bad"}/>
              <Stat label="Blended CPM" value={cpmf(cur.roll.blendedCpm)} delta={`digital ${cpmf(cur.roll.digCpm)}`}/>
              <Stat label="Frequency" value={cur.roll.avgFreq.toFixed(1)} delta="average across the flight"/>
            </div>

            <div className="g2">
              <div>
                <div className="lbl">Rated against the good-plan rubric</div>
                <div className="banner a" style={{marginBottom:10, padding:"7px 10px"}}>
                  <span className="bi">[OQ-2]</span><div className="tiny">The definition of a good plan is not a settled
                    WBD artifact. This rubric is proposed, and the shape — not the content — is what the prototype is testing.</div></div>
                {RUBRIC.map(r=>(
                  <div key={r.k} style={{marginBottom:9}}>
                    <div className="row tiny" style={{justifyContent:"space-between"}}>
                      <span title={r.help}>{r.label} <span className="dim">· weight {pct(r.w,0)}</span></span>
                      <b>{cur.rubric.parts[r.k].toFixed(0)}</b>
                    </div>
                    <Bar v={cur.rubric.parts[r.k]/100} c={cur.rubric.parts[r.k]>75?"g":cur.rubric.parts[r.k]>50?"":"a"}/>
                  </div>
                ))}
              </div>
              <div>
                <div className="lbl">Requirement coverage</div>
                <div className="col" style={{gap:6}}>
                  {cur.rubric.coverageItems.map((c,i)=>(
                    <div key={i} className="row" style={{alignItems:"flex-start", gap:8}}>
                      <span className="chip" style={{background:c.ok?"var(--good-soft)":"var(--bad-soft)",
                        color:c.ok?"var(--good)":"var(--bad)"}}>{c.ok?"✓":"✕"}</span>
                      <div><div className="tiny">{c.t}</div>{c.d && <div className="mini dim">{c.d}</div>}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>

          <Card title="Decisions overridden" tight
            sub="The optimiser's original allocation beside the planner's changes, so both remain readable — and the quality of the argument for each.">
            {Object.keys(cur.overrides).length === 0
              ? <div style={{padding:14}} className="tiny muted">No overrides on this version. The allocation is the
                  optimiser's own answer to the accepted list.</div>
              : <div style={{padding:"4px 14px 14px"}}>
                  {Object.entries(cur.overrides).map(([pid,val])=>{
                    const l = cur.lines.find(x=>x.pid===pid);
                    const j = cur.justifications[pid]||"";
                    const q = j.length >= 90 ? "specific" : j.length >= 45 ? "adequate" : "thin";
                    return (
                      <div key={pid} className="bl">
                        <div className="bk">{l?.name}</div>
                        <div className="bv">
                          <span className="strike dim">{money(l?.systemSpend)}</span> → <b>{money(val)}</b>
                          {" "}<span className="dim">({l && l.systemSpend ? pctn((val/l.systemSpend-1)*100,0) : "—"})</span>
                          <span className="why">“{j}”</span>
                        </div>
                        <Chip c={q==="specific"?"g":q==="adequate"?"":"a"}>{q}</Chip>
                      </div>
                    );
                  })}
                  <div className="tiny muted" style={{marginTop:8}}>
                    Quality of argument scored {cur.rubric.parts.argument.toFixed(0)} — {cur.rubric.withReason} of
                    {" "}{cur.rubric.devs} overrides carry a reason a reader outside the room could act on.
                  </div>
                </div>}
          </Card>

          <Card title="Allocation" tight>
            <XL name={cur.id + "_allocation"} height={300} rows={cur.lines} cols={[
              { key:"name", label:"Product / package", w:270, get:l=>l.name },
              { key:"region", label:"Region", w:60, get:l=>l.region },
              { key:"medium", label:"Medium", w:62, get:l=>l.medium },
              { key:"spend", label:"Net spend", w:100, align:"r", get:l=>money(l.spend), raw:l=>Math.round(l.spend) },
              { key:"share", label:"Share", w:58, align:"r", get:l=>pct(l.spend/cur.roll.spend,1) },
              { key:"cpm", label:"CPM", w:64, align:"r", get:l=>cpmf(l.cpm), raw:l=>l.cpm },
              { key:"imps", label:"Impressions", w:96, align:"r", get:l=>imps(l.impsK), raw:l=>Math.round(l.impsK*1000) },
              { key:"avail", label:"% avails", w:74, align:"r", get:l=>pct(l.availUse,0), raw:l=>l.availUse },
              { key:"ovr", label:"Overridden", w:88, align:"c", get:l=>l.overridden?"yes":"",
                cell:l=>l.overridden?<Chip c="v">yes</Chip>:"" },
              { key:"just", label:"Justification", w:340, get:l=>cur.justifications[l.pid]||"" },
            ]} total={{ name:`${cur.lines.length} lines`, spend: money(cur.roll.spend), share:"100.0%",
              cpm: cpmf(cur.roll.blendedCpm), imps: imps(cur.roll.impsK) }}/>
          </Card>
        </>}
      </div>

      <div className="col sticky" style={{gap:14}}>
        <Card title="What Analyze is for">
          <div className="tiny muted" style={{lineHeight:1.6}}>
            One question: which of these versions do we put forward. It is a judgement step — the plan is read here, but
            every change it provokes is made back in Discovery, because that is where product selection and ranking
            live. Committing binds approval to <b>this version</b>, not to “the plan”.
          </div>
          <div className="hr"/>
          <div className="lbl">Options open to you</div>
          <div className="col tiny" style={{gap:7}}>
            <div><b>Save another version.</b> <span className="muted">Immutable, sits beside this one.</span></div>
            <div><b>Compare.</b> <span className="muted">Allocation, price, reach and coverage deltas.</span></div>
            <div><b>Fork.</b> <span className="muted">[NEW] Branch from a saved version without the Discovery round trip — which means versions have parents, not a flat list.</span></div>
            <div><b>Update product.</b> <span className="muted">Back to Discovery, re-order and re-target, re-run.</span></div>
            <div><b>Commit and share.</b> <span className="muted">P&I gets the allocation and everything upstream of it.</span></div>
          </div>
        </Card>

        <Gate gate={gate} verb="Hand off to Approval"
          onGo={()=>{ up({phase:"approval"});
            log("sys", `Analyze orchestrator handed off to Approval at gate score ${gate.score}.`);
            toast("Handoff accepted — P&I has " + st.committed); }}/>

        <Assist title="On this version">
          {cur && v.length > 1 && (() => {
            const other = v.filter(x => x.id !== cur.id)
              .sort((a,b) => Math.abs(a.rubric.total-cur.rubric.total) - Math.abs(b.rubric.total-cur.rubric.total))[0];
            const gap = Math.abs(cur.rubric.total - other.rubric.total);
            if (gap > 3) return null;
            const d3 = (cur.roll.reach3 - other.roll.reach3) * 100;
            const dc = cur.roll.blendedCpm - other.roll.blendedCpm;
            return <div style={{marginBottom:8}}>
              {cur.id} and {other.id} score within {gap.toFixed(1)} of each other, so the rubric is not choosing for you.
              What separates them is shape: {cur.id} is {d3 >= 0 ? "+" : ""}{d3.toFixed(1)} points of modelled 3+ reach
              and {dc >= 0 ? "+" : "−"}{cpmf(Math.abs(dc))} of blended CPM against {other.id}. Commit the one whose
              argument you can make out loud, and the other one stays saved as the alternative you rejected.
            </div>;
          })()}
          {cur && (cur.roll.reach3 < FRAME.reachGoal3 ? <>
            {cur.id} misses the stated KPI by {pctn((FRAME.reachGoal3-cur.roll.reach3)*100,1)} points. Before you commit
            it, it is worth saving a second version that trades some of the {pct(cur.roll.linearPct,0)} linear share for
            distinct digital products — the gap is breadth, not weight.
          </> : Object.keys(cur.overrides).length === 0 ? <>
            {cur.id} is the optimiser's own answer with nothing overridden, which makes it the cleanest version to
            defend and the least interesting to argue with. If you believe something about this advertiser the ranking
            does not know, this is the moment it should show up.
          </> : <>
            {cur.id} carries {Object.keys(cur.overrides).length} override{Object.keys(cur.overrides).length>1?"s":""}.
            P&amp;I will read each one against a position they already stated, so the justification is doing as much
            work as the number.
          </>)}
        </Assist>
      </div>

      {commit && <JustifyG title={"Commit " + commit.id}
        what={<>Approval binds to <b>{commit.id}</b>, not to the plan. P&amp;I receives the allocation, the intake
          brief, the product ranking and customisations, the optimiser's original recommendation, and every one of your
          changes with its explanation.</>}
        verb="Commit and share"
        onCancel={()=>setCommit(null)}
        onConfirm={(r)=>{ up({committed:commit.id, sentToPI:true, commitNote:r, phase:"approval"});
          log("ok", `${commit.id} committed and shared for P&I approval.`, r);
          setCommit(null); toast(commit.id + " shared with P&I"); }}/>}
    </div>
  );
};
