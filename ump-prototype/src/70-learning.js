/* =============================================================================
   70-learning.js — what the desk has learned, and from what.
   Signals are visible and reversible. A planner can see exactly what the system
   learned and switch any of it off.
   ============================================================================= */
const Learning = ({S}) => {
  const { st, up } = S;
  const toast = useToast();
  const [tab, setTab] = useState("signals");
  const [fb, setFb] = useState({ type:"Report", who:"", text:"" });
  const [captured, setCaptured] = useState([]);

  const ranking = useRanking(st);
  const withSignals = ranking;
  const without = useMemo(() => {
    const rows = buildRanking(st.customMap, st.signals.map(s=>({...s, on:false})));
    return Object.fromEntries(rows.map((r,i)=>[r.pid, i+1]));
  }, [st.customMap, st.signals]);

  const changed = withSignals.filter(r => without[r.pid] !== r.rank);

  return (
    <div className="pad">
      <div style={{marginBottom:14}}>
        <h2 style={{fontSize:17}}>What the desk has learned</h2>
        <div className="muted" style={{maxWidth:800, marginTop:4}}>
          Every override, rejection and disapproval arrives with a reason, because a change without one is not
          accepted. Those reasons are the training data. Nothing here is hidden and nothing here is permanent — turn a
          signal off and the ranking recomputes in front of you.
        </div>
      </div>

      <div className="tabs" style={{marginBottom:14}}>
        {[["signals","Active signals", st.signals.filter(s=>s.on).length],
          ["effect","Effect on this plan", changed.length],
          ["capture","Capture feedback"],
          ["ledger","This plan's ledger", st.timeline.length]].map(([k,l,n])=>
          <button key={k} className={tab===k?"on":""} onClick={()=>setTab(k)}>{l}{n!=null && <span className="ct">{n}</span>}</button>)}
      </div>

      {tab==="signals" && (
        <div className="col" style={{gap:11}}>
          {st.signals.map(s=>(
            <Card key={s.id}>
              <div className="row" style={{alignItems:"flex-start", gap:12}}>
                <Switch on={s.on} onChange={(v)=>{ up(x=>({signals:x.signals.map(y=>y.id===s.id?{...y,on:v}:y)}));
                  toast(v ? "Signal on — the ranking recomputes" : "Signal off — the ranking recomputes"); }}/>
                <div className="grow">
                  <div className="row" style={{gap:8, marginBottom:3}}>
                    <b style={{fontSize:12.5}}>{s.text}</b>
                    <Chip c={s.strength==="strong"?"g":s.strength==="new"?"v":""}>{s.strength}</Chip>
                    <span className="mono dim">{s.id}</span>
                  </div>
                  <div className="tiny muted" style={{marginBottom:5}}>Learned from <b>{s.from}</b> on {s.when}.</div>
                  <div className="tiny" style={{paddingLeft:9, borderLeft:"2px solid var(--line)", marginBottom:6}}>
                    Reason given at the time: “{s.reason}”</div>
                  <div className="banner b" style={{padding:"6px 10px"}}>
                    <span className="bi">Effect</span><div className="tiny">{s.effect}</div></div>
                </div>
              </div>
            </Card>
          ))}
          <div className="banner a"><span className="bi">Guardrail</span>
            <div>A signal only ever changes a <b>proposal</b>. It never changes a hard constraint, never removes a
              product from eligibility, and never suppresses a reason from the record. The strongest thing it can do is
              move something down the order and say why.</div></div>
        </div>
      )}

      {tab==="effect" && (
        <Card title="What the active signals are doing to this plan's ranking right now"
          sub="The order with every signal on, beside the order with every signal off.">
          {changed.length === 0
            ? <div className="tiny muted">No active signal is changing the order for this brief.</div>
            : <table className="tb">
                <thead><tr><th>Product</th><th className="r">Without signals</th><th className="r">With signals</th>
                  <th className="r">Move</th><th>Which signal, and why</th></tr></thead>
                <tbody>{changed.map(r=>{
                  const sig = st.signals.filter(s=>s.on && r.appliedSignals.includes(s.id));
                  return <tr key={r.pid}>
                    <td>{r.p.name}</td>
                    <td className="r dim">{without[r.pid]}</td>
                    <td className="r"><b>{r.rank}</b></td>
                    <td className="r" style={{color: r.rank < without[r.pid] ? "var(--good)" : "var(--bad)"}}>
                      {r.rank < without[r.pid] ? "↑" : "↓"}{Math.abs(without[r.pid]-r.rank)}</td>
                    <td className="tiny muted">{sig.length ? sig.map(s=>`${s.id}: ${s.effect}`).join(" ")
                      : "Moved as a consequence of other products moving, not by a signal of its own."}</td>
                  </tr>;
                })}</tbody>
              </table>}
          <div className="hr"/>
          <div className="tiny muted">
            This is the whole claim behind “gets better with use”, made checkable. If a planner cannot see the
            difference a signal makes, the signal should not exist.
          </div>
        </Card>
      )}

      {tab==="capture" && (
        <div className="split">
          <Card title="Capture feedback from this showcase"
            sub="Four types, different weights. Observation is recollection; report is what the user actually said.">
            <div className="row" style={{gap:8, marginBottom:12}}>
              {["Observation","Report","Interpretation","Learning"].map(t=>
                <button key={t} className={"pill" + (fb.type===t?" on":"")} onClick={()=>setFb({...fb, type:t})}>{t}</button>)}
            </div>
            <label className="lbl">Who</label>
            <input className="inp" value={fb.who} onChange={e=>setFb({...fb, who:e.target.value})}
              placeholder="Practitioner name or role" style={{marginBottom:12}}/>
            <label className="lbl">{ {Observation:"What happened",Report:"What they actually said",
              Interpretation:"What we concluded — name the report it came from",
              Learning:"What carries forward as a settled decision"}[fb.type] }</label>
            <textarea className="inp" value={fb.text} onChange={e=>setFb({...fb, text:e.target.value})}/>
            <div className="row" style={{marginTop:12}}>
              <div className="tiny dim grow">{ {Observation:"Low weight — nothing downstream leans on it as evidence.",
                Report:"High weight.", Interpretation:"High weight. Must name its report.",
                Learning:"High weight — this is what updates the cumulative PRD."}[fb.type] }</div>
              <Btn c="pri sm" disabled={!fb.text.trim()} onClick={()=>{
                setCaptured([{...fb, at:NOW()}, ...captured]); setFb({...fb, text:"", who:""});
                toast("Captured to the round record"); }}>Capture</Btn>
            </div>
            {captured.length > 0 && <>
              <div className="hr"/>
              <div className="lbl">Captured this session</div>
              {captured.map((c,i)=>(
                <div key={i} className="evrow">
                  <div className="et">{c.at.slice(11)}<div><Chip c={c.type==="Observation"?"":"g"}>{c.type}</Chip></div></div>
                  <div className="tiny"><b>{c.who || "—"}</b><div className="muted">{c.text}</div></div>
                </div>))}
              <Btn c="sm" style={{marginTop:10}} onClick={()=>{
                download("round_feedback.csv",
                  "type,who,at,text\n" + captured.map(c=>`"${c.type}","${c.who}","${c.at}","${c.text.replace(/"/g,'""')}"`).join("\n"));
                toast("Exported"); }}>Export the round record</Btn>
            </>}
          </Card>
          <div className="col" style={{gap:14}}>
            <Card title="The round this prototype belongs to" sub="Fast Prototyping operating model">
              <table className="tb">
                <tbody>
                  <tr><td style={{width:70}}><b>Objective</b></td><td className="tiny">Can a planner adjudicate a justified proposal instead of assembling a plan — across intake, ranking, allocation and approval?</td></tr>
                  <tr><td><b>Personas</b></td><td className="tiny">Planner (primary), P&amp;I approver (primary)</td></tr>
                  <tr><td><b>Data</b></td><td className="tiny">One anchored scenario — P&amp;G / Tide global summer — with synthetic detail over real WBD portfolio shape</td></tr>
                  <tr><td><b>Output</b></td><td className="tiny">Standalone single-file HTML/React prototype</td></tr>
                  <tr><td><b>Ends with</b></td><td className="tiny">Something clickable and a set of learnings written down — not a status update</td></tr>
                </tbody>
              </table>
            </Card>
            <Card title="Questions worth asking in the showcase">
              <ol className="tiny" style={{margin:0, paddingLeft:18, lineHeight:1.9}}>
                <li>Show me a product you would have expected in the list and cannot find. Did the exclusion register answer you?</li>
                <li>You moved that product up. Would the reason you typed survive P&amp;I asking about it in three weeks?</li>
                <li>Where did you want to change the optimiser rather than the inputs?</li>
                <li>Does the brief read as something you would send to the AE without a call attached?</li>
                <li>Which number on this screen would you not trust in a client meeting, and what would make you trust it?</li>
                <li>What did you go looking for in a spreadsheet anyway?</li>
              </ol>
            </Card>
          </div>
        </div>
      )}

      {tab==="ledger" && (
        <div className="g2">
          <Card title="Everything that happened on this plan" sub="Context attaches to the plan, not to you (T2). A new planner inherits all of it.">
            <Timeline items={st.timeline}/>
          </Card>
          <div className="col" style={{gap:14}}>
            <Card title="Reasons recorded on this plan" sub="These are what the next iteration starts from.">
              {[...Object.entries(st.rankJust).map(([pid,r])=>({what:(PRODUCTS.find(p=>p.id===pid)||{}).name, r, k:"Discovery"})),
                ...Object.entries(st.justifications).map(([pid,r])=>({what:(PRODUCTS.find(p=>p.id===pid)||{}).name, r, k:"Override"})),
                ...Object.entries(st.decisions).map(([pid,d])=>({what:(PRODUCTS.find(p=>p.id===pid)||{}).name, r:d.reason, k:"P&I " + d.d}))]
                .filter(x=>x.r).map((x,i)=>(
                <div key={i} className="evrow">
                  <div className="et">{x.k}</div>
                  <div className="tiny"><b>{x.what}</b><div className="muted">“{x.r}”</div></div>
                </div>))}
              {!Object.keys(st.rankJust).length && !Object.keys(st.justifications).length && !Object.keys(st.decisions).length
                && <div className="tiny muted">Nothing yet. Change something in Discovery or override an allocation and it lands here.</div>}
            </Card>
            <Card title="What carries into the next iteration" sub="OQ-5, answered: all of it.">
              <div className="col tiny" style={{gap:7}}>
                <div><b>Planner overrides and their justifications.</b> <span className="muted">Re-solved from, not discarded.</span></div>
                <div><b>Products rejected and why.</b> <span className="muted">Re-enter flagged, not removed.</span></div>
                <div><b>Targeting already tested,</b> <span className="muted">with its price and avails consequence, so the same experiment is not run twice.</span></div>
                <div><b>P&amp;I disapproval reasons.</b> <span className="muted">Become soft constraints with their origin attached.</span></div>
                <div><b>Approved lines.</b> <span className="muted">Become hard constraints for the re-solve.</span></div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
