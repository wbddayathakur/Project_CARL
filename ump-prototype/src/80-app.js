/* =============================================================================
   80-app.js — shell.
   ============================================================================= */
const NAV = [
  { sec:"Design" },
  { k:"blueprint", n:"How the desk works", d:"Flows, personas, agents" },
  { sec:"Planning" },
  { k:"desk", n:"Your desk", d:"Six plans, one quarter" },
  { k:"plan", n:"Tide — Global Summer", d:"The worked plan", bold:true },
  { sec:"Reference" },
  { k:"market", n:"Global market", d:"Linear + digital supply" },
  { k:"learning", n:"What it has learned", d:"Signals, ledger, feedback" },
];

/* Deep links: #desk, #market, #plan/discovery, #blueprint/personas … */
const HASH = (location.hash || "").replace(/^#/, "").split("/");
const SCREENS = ["blueprint","desk","plan","market","learning"];

const App = () => {
  const S = usePlanStore();
  const { st, up } = S;
  const [screen, setScreen] = useState(SCREENS.includes(HASH[0]) ? HASH[0] : "blueprint");
  const [jump, setJump] = useState(false);
  useEffect(() => {
    if (HASH[0] !== "plan" || !PHASES.some(p=>p.k===HASH[1])) return;
    if (HASH[2] === "worked") S.seed(HASH[1]); else up({phase:HASH[1]});
  }, []);
  const [toasts, setToasts] = useState([]);
  const toast = useCallback((t) => {
    const id = uid("t");
    setToasts(x => [...x, {id, t}]);
    setTimeout(()=>setToasts(x=>x.filter(y=>y.id!==id)), 3200);
  }, []);

  const persona = st.phase === "approval" && screen === "plan" ? "pi" : "planner";

  const phaseScreen = {
    intake: <Intake S={S}/>, discovery: <Discovery S={S}/>, strategize: <Strategize S={S}/>,
    analyze: <Analyze S={S}/>, approval: <Approval S={S}/>,
  }[st.phase];

  return (
    <ToastCtx.Provider value={toast}>
      <div className="app">
        <div className="rail">
          <div className="rail-brand">
            <div className="wb">WARNER BROS. DISCOVERY</div>
            <div className="nm">Unified Media Planning</div>
            <div className="sub">Prototype round 1 · anchored sample data</div>
          </div>
          <div className="rail-scroll">
            {NAV.map((n,i)=> n.sec
              ? <div key={i} className="rail-sec">{n.sec}</div>
              : <button key={n.k} className={"rail-item" + (screen===n.k?" on":"")}
                  onClick={()=>{ setScreen(n.k); history.replaceState(null,"","#"+n.k); }}>
                  <span className="rail-dot"/>
                  <span style={{minWidth:0}}>
                    <span style={{display:"block", fontWeight:n.bold?600:500, whiteSpace:"nowrap",
                      overflow:"hidden", textOverflow:"ellipsis"}}>{n.n}</span>
                    <span style={{display:"block", fontSize:10, opacity:.7, whiteSpace:"nowrap",
                      overflow:"hidden", textOverflow:"ellipsis"}}>{n.d}</span>
                  </span>
                </button>)}
            {screen === "plan" && (
              <div style={{marginTop:6, paddingLeft:8}}>
                {PHASES.map((p,i)=>(
                  <button key={p.k} className={"rail-item" + (st.phase===p.k?" on":"")}
                    style={{fontSize:11.5, paddingLeft:14}} onClick={()=>up({phase:p.k})}>
                    <span className="rail-dot"/>{i+1}. {p.n}
                  </button>))}
              </div>
            )}
          </div>
          <div className="rail-foot">
            <button style={{color:"#8fb4ef", display:"block", marginBottom:6}} onClick={()=>setJump(true)}>
              Load the worked example →</button>
            Not branded as AI (T8) · every value carries its provenance · nothing is deleted
          </div>
        </div>

        <div className="main">
          <div className="topbar">
            <h1>{{blueprint:"How the desk works", desk:"Your desk", plan:DEAL.plan,
                  market:"Global market reference", learning:"What the desk has learned"}[screen]}</h1>
            {screen === "plan" && <>
              <span className="crumb">{DEAL.advertiser} · {DEAL.agency} · {money1(DEAL.grossBudget)} gross · {FLIGHT.label}</span>
            </>}
            <div className="spacer"/>
            {screen === "plan" && (
              <div className="row" style={{gap:8}}>
                <Chip c={persona==="pi"?"a":"b"}>
                  {persona==="pi" ? "VIEWING AS P&I APPROVER" : "VIEWING AS PLANNER"}</Chip>
                <Chip c="o">brief v{st.briefVersion}</Chip>
                {st.versions.length>0 && <Chip c="o">{st.versions.length} version{st.versions.length>1?"s":""}</Chip>}
              </div>
            )}
            {screen !== "plan" && <span className="crumb">Anchored sample data · synthetic in detail</span>}
          </div>

          <div className="content">
            {screen === "blueprint" && <Blueprint initialTab={HASH[0]==="blueprint" ? HASH[1] : null}/>}
            {screen === "desk" && <Desk st={st} onOpen={()=>setScreen("plan")}/>}
            {screen === "market" && <Market/>}
            {screen === "learning" && <Learning S={S}/>}
            {screen === "plan" && (
              <div className="pad">
                <div style={{marginBottom:14}}>
                  <PhaseRail phase={st.phase} st={st} onGo={(k)=>up({phase:k})}/>
                  <div className="tiny dim" style={{marginTop:6}}>
                    You can traverse backwards to any phase from any point — a late clarification, a change in P&amp;I's
                    position, or a disapproval all land somewhere upstream and everything downstream re-derives.
                  </div>
                </div>
                {phaseScreen}
              </div>
            )}
          </div>
        </div>
      </div>

      {jump && <Modal title="Load the worked example" onClose={()=>setJump(false)}
        sub="Replays the decisions a planner would have made, so a showcase can open on any phase. Every seeded action carries the reason it would have carried live.">
        <div className="col" style={{gap:8}}>
          {PHASES.map((p,i)=>(
            <button key={p.k} className="card" style={{textAlign:"left"}}
              onClick={()=>{ S.seed(p.k); setScreen("plan"); setJump(false);
                toast("Loaded up to " + p.n); }}>
              <div className="card-b" style={{padding:"10px 13px"}}>
                <div className="row"><Chip c="n">{i+1}</Chip><b style={{fontSize:12.5}}>{p.n}</b>
                  <div style={{flex:1}}/><span className="tiny dim">{p.owner} owns</span></div>
                <div className="tiny muted" style={{marginTop:3}}>{[
                  "A clean desk: five gaps open, three contradictions unadjudicated, nothing approved.",
                  "Intake settled and brief v4 approved. Discovery opens on the system's own ranking, untouched.",
                  "One promotion and two targeting changes made, all justified, and the optimiser has solved the accepted list. Nothing overridden yet.",
                  "Two versions saved, one of them carrying a justified override. Nothing committed.",
                  "PV-B committed and with P&I, who has decided three of thirteen lines.",
                ][i]}</div>
              </div>
            </button>))}
        </div>
      </Modal>}

      <div className="toastwrap">
        {toasts.map(t=><div key={t.id} className="toast">{t.t}</div>)}
      </div>
    </ToastCtx.Provider>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
