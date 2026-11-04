/* =============================================================================
   60-intake.js — Intake phase.
   The brief is a read-only derived view. A planner who disagrees corrects the
   system; the brief re-derives to a new version (T3). Nothing here is a form.
   ============================================================================= */

function deriveBrief(st){
  const gv = (id) => st.gapDecisions[id];
  const corr = (attr) => st.corrections.filter(c => c.attr === attr).slice(-1)[0];
  const line = (k, v, cls, why, ev) => {
    const c = corr(k);
    if (c) return { k, v: c.value, cls:"planner", why:`Corrected by the planner. “${c.reason}”`, ev:"planner correction " + c.at };
    return { k, v, cls, why, ev };
  };

  const requirements = [
    line("Advertiser", "Procter & Gamble — Tide (US) / Ariel (international)", "stated", null, "E01, E02"),
    line("Objective", "Incremental reach against light-TV households ahead of the Q3 pack redesign", "stated", null, "E05"),
    line("Primary KPI", "1+ reach at 3+ effective frequency, A25-54", "stated", null, "E06"),
    line("Gross budget", money(DEAL.grossBudget) + " · net working " + money(DEAL.netBudget), "stated", "15% agency commission applied at intake.", "E03"),
    line("Flight", FLIGHT.label + " · " + FLIGHT.weeks + " weeks", "stated", null, "E04"),
    line("Markets", "US, EMEA (UK/DE/PL/ES), LATAM (BR/MX), APAC (AU/SG/PH)", "stated", null, "E08"),
    line("Target demo", "A25-54, skew W25-54", "stated", null, "E07"),
    gv("G01")
      ? line("Regional budget split", gv("G01").value, gv("G01").cls, gv("G01").why, "G01 · " + gv("G01").at)
      : { k:"Regional budget split", gap:"G01" },
    gv("G02")
      ? line("Flight weighting", gv("G02").value, gv("G02").cls, gv("G02").why, "G02 · " + gv("G02").at)
      : { k:"Flight weighting", gap:"G02" },
    line("Creative", ":30 hero, :15 cutdown, 9:16 social variant", "stated", null, "E12"),
    gv("G03")
      ? line("Creative rotation", gv("G03").value, gv("G03").cls, gv("G03").why, "G03")
      : { k:"Creative rotation", gap:"G03" },
    line("Measurement", "VideoAmp + Nielsen ONE dual currency", "hist", "Last three plans, all markets. RFP appendix names Nielsen ONE only — see contradiction C03.", "E20, C03"),
  ];

  const hard = [
    line("Brand safety", "No hard-news adjacency", "stated", "P&G global policy. Confirmed on the last four plans.", "E09"),
    line("Do-not-air", "41 titles (attached list)", "stated", null, "E10"),
    line("Viewability floor", "80% MRC-viewable on digital video", "stated", null, "E11"),
    line("CPM ceiling", cpmf(FRAME.cpmCeiling) + " blended, digital", "clarified", null, "E14"),
    line("Frequency cap", FRAME.freqCap + " per week per user, digital", "clarified", null, "E15"),
  ];

  const soft = [
    { k:"Linear share", v:"Target " + pct(FRAME.linearTarget,0) + ", ceiling " + pct(FRAME.linearCeiling,0), cls:"clarified",
      why:"Adjudicated from contradiction C01 — the clarification is a ceiling, the RFP language is directional.", ev:"C01, E13", origin:"Client, via AE" },
    { k:"HBO Max CTV floor", v:"≥ " + cpmf(FRAME.hbomaxFloor) + " CPM", cls:"seller",
      why:"Q3 sellout at 78%, +6 pts YoY. Clearing below the floor resets the anchor for the scatter market.", ev:"PI-Q3-07", origin:"P&I standing position" },
    { k:"Push list", v:"discovery+ US lifestyle, HBO Max LATAM ad tier", cls:"seller",
      why:"Both behind Q3 pace — 61% vs 74% plan and 44% vs 60% plan.", ev:"PI-Q3-11", origin:"P&I standing position" },
    { k:"PMP cap", v:"≤ " + pct(FRAME.pmpCap,0) + " of plan", cls:"seller",
      why:"Yield dilution — FMCG PMP clears at 38% of direct CPM. Hard, not soft.", ev:"PI-Q3-03", origin:"P&I standing position" },
    { k:"Sport", v:"Held; and excluded by advertiser preference", cls:"hist",
      why:"P&I holds sport above floor +15%. Separately the advertiser declined the 2025 NBA package — 'no sport for this brand'.", ev:"PI-Q3-09, E19", origin:"P&I + advertiser history" },
  ];

  return { requirements, hard, soft };
}

const BLine = ({l, onCorrect, onGap}) => {
  if (l.gap){
    const g = GAPS.find(x=>x.id===l.gap);
    return (
      <div className="bl gap">
        <div className="bk">{l.k}</div>
        <div className="bv">
          <span style={{color:"var(--bad)"}}>Not supported by the evidence store</span>
          <span className="why">{g.why}</span>
        </div>
        <Btn c="sm dgr" onClick={()=>onGap(g)}>{g.material ? "Material gap — resolve" : "Resolve"}</Btn>
      </div>
    );
  }
  return (
    <div className="bl">
      <div className="bk">{l.k}</div>
      <div className="bv">
        {l.v}
        {l.why && <span className="why">{l.why}</span>}
        {l.origin && <span className="why">Origin: {l.origin}</span>}
      </div>
      <div className="row" style={{gap:6}}>
        <ProvChip cls={l.cls} small/>
        {l.ev && <span className="mono dim" title="Route to the evidence behind this value">{l.ev}</span>}
        <Btn c="xs gho" title="You cannot edit a brief. State what is wrong; the brief re-derives."
          onClick={()=>onCorrect(l)}>Correct</Btn>
      </div>
    </div>
  );
};

const Intake = ({S}) => {
  const { st, up, log, correct } = S;
  const toast = useToast();
  const [tab, setTab] = useState("brief");
  const [gap, setGap] = useState(null);
  const [contra, setContra] = useState(null);
  const [fix, setFix] = useState(null);
  const brief = useMemo(()=>deriveBrief(st), [st]);

  const materialGaps = GAPS.filter(g => g.material);
  const openGaps = materialGaps.filter(g => !st.gapDecisions[g.id]);
  const materialContras = CONTRADICTIONS.filter(c => c.material);
  const openContras = materialContras.filter(c => !st.contraDecisions[c.id]);
  const gateOk = openGaps.length === 0 && openContras.length === 0;
  const evRows = useMemo(() => [
    ...EVIDENCE,
    ...st.corrections.map(c=>({ id:c.id, attr:c.attr, value:c.value, cls:"planner",
      src:"Planner correction", loc:"—", ts:c.at, by:"You" })),
  ], [st.corrections]);
  const evGraph = useMemo(() => evalEvidenceGraph(evRows, st), [evRows, st.gapDecisions, st.contraDecisions]);
  const gate = useMemo(() => evaluateGate("intake", st, {evGraph}), [st, evGraph]);

  const decideGap = (g, kind, value, reason) => {
    up(s => ({ gapDecisions: { ...s.gapDecisions,
      [g.id]: { status:kind, value, reason, at:NOW(), cls: kind==="edited" ? "planner" : g.wouldCarry,
                why: kind==="accepted"
                  ? `Accepted as a proposal, and it stays visibly inferred. Basis: ${g.basis} “${reason}”`
                  : `Planner-supplied. “${reason}”` } },
      briefVersion: s.briefVersion + 1, intakeApproved: null }));
    log(kind === "rejected" ? "no" : "ok",
      `Gap ${g.id} (${g.attr}) ${kind}. Brief re-derived to v${st.briefVersion+1}.`, reason);
    setGap(null);
    toast(`${g.id} ${kind} — brief re-derived to v${st.briefVersion+1}`);
  };

  const decideContra = (c, choice, reason) => {
    up(s => ({ contraDecisions: { ...s.contraDecisions, [c.id]: { choice, reason, at:NOW() } },
      briefVersion: s.briefVersion + 1, intakeApproved: null }));
    log("ok", `Contradiction ${c.id} adjudicated — ${choice}.`, reason);
    setContra(null);
    toast(`${c.id} adjudicated`);
  };

  return (
    <div className="split">
      <div className="col" style={{gap:14}}>
        <div className="tabs">
          {[["brief","Intake brief"],["evidence","Evidence store"],
            ["gaps","Gaps", materialGaps.filter(g=>!st.gapDecisions[g.id]).length],
            ["contra","Contradictions", openContras.length],
            ["history","History & cohort"],["timeline","Change timeline"]].map(([k,l,n])=>
            <button key={k} className={tab===k?"on":""} onClick={()=>setTab(k)}>
              {l}{n>0 && <span className="ct" style={{background:"var(--bad-soft)", color:"var(--bad)"}}>{n}</span>}</button>)}
        </div>

        {tab==="brief" && (
          <div className="brief">
            <div className="row" style={{alignItems:"flex-start"}}>
              <div>
                <h2>Intake brief</h2>
                <div className="tiny dim" style={{marginTop:3}}>
                  {DEAL.plan} · derived {NOW()} · version {st.briefVersion}
                </div>
              </div>
              <div style={{flex:1}}/>
              <div className="col" style={{alignItems:"flex-end", gap:5}}>
                <div className="readonly"><Chip c="o">READ-ONLY</Chip> nobody writes this — it derives from the evidence store</div>
                {st.intakeApproved
                  ? <Chip c="g">APPROVED · v{st.intakeApproved.version}</Chip>
                  : <Chip c="a">NOT APPROVED</Chip>}
              </div>
            </div>

            <h4>What the advertiser wants</h4>
            {brief.requirements.map((l,i)=><BLine key={i} l={l} onGap={setGap}
              onCorrect={()=>setFix(l)}/>)}

            <h4>Hard constraints — cannot be traded</h4>
            {brief.hard.map((l,i)=><BLine key={i} l={l} onGap={setGap} onCorrect={()=>setFix(l)}/>)}

            <h4>Soft constraints — can be traded, at a stated cost</h4>
            {brief.soft.map((l,i)=><BLine key={i} l={l} onGap={setGap} onCorrect={()=>setFix(l)}/>)}

            <h4>Buying history — 12-month lookback</h4>
            <table className="tb">
              <thead><tr><th>Plan</th><th>Closed</th><th className="r">Gross</th><th className="r">Linear</th><th className="r">CPM</th><th>Top products</th><th>Rejected, and why</th></tr></thead>
              <tbody>{HISTORY.map(h=>(
                <tr key={h.plan}><td><span className="mono">{h.plan}</span><div className="mini dim">{h.name}</div></td>
                  <td className="tiny">{h.closed}</td><td className="r">{money1(h.gross)}</td>
                  <td className="r">{h.linearPct}%</td><td className="r">{cpmf(h.cpm)}</td>
                  <td className="tiny">{h.topProducts.join(", ")}</td>
                  <td className="tiny muted">{h.rejected}</td></tr>))}
              </tbody>
            </table>

            <h4>Seller context — P&amp;I is the voice of the seller</h4>
            {PI_POSITION.map(p=>(
              <div className="bl" key={p.id}>
                <div className="bk">{p.title}</div>
                <div className="bv">{p.text}<span className="why">Reason given: {p.reason}</span></div>
                <div className="row" style={{gap:6}}>
                  <Chip c={p.hardness==="hard"?"r":"n"}>{p.hardness}</Chip>
                  <span className="mono dim">{p.id}</span>
                </div>
              </div>
            ))}
            <div className="bl contra">
              <div className="bk">Position on this RFP</div>
              <div className="bv">No advertiser-specific position was returned.
                <span className="why">Requested 2026-05-04, no response by 2026-05-05. The absence is recorded rather than left blank, so at approval nobody can say the plan ignored a position that was never stated.</span></div>
              <Chip c="a">ABSENCE RECORDED</Chip>
            </div>

            <h4>Competitive context</h4>
            {st.researchRun ? (
              <>
                {COMPETITIVE.map((c,i)=>(
                  <div className="bl" key={i}>
                    <div className="bk">{c.brand}</div>
                    <div className="bv">{c.note}<span className="why">{c.region} · ${c.spend.toFixed(1)}M · {c.mix}</span></div>
                    <Chip c="o">NO CLASS [OPEN]</Chip>
                  </div>
                ))}
                <div className="tiny muted" style={{marginTop:8, paddingLeft:8}}>
                  [OPEN] Competitive context has no provenance class on the ladder yet, so nothing in the plan may be
                  derived from it without breaking the evidence rule. It is shown, and it is not used.
                </div>
              </>
            ) : (
              <div className="banner b">
                <span className="bi">Not run</span>
                <div>Competitive research is triggered by the planner, not gathered automatically.
                  <Btn c="sm" style={{marginLeft:10}} onClick={()=>{ up({researchRun:true});
                    log("sys","Competitive research triggered. 6 category advertisers returned."); toast("Research returned — 6 advertisers"); }}>
                    Run category research</Btn></div>
              </div>
            )}

            <h4>Definition of a good plan for this RFP</h4>
            <div className="banner a"><span className="bi">[OPEN] OQ-2</span>
              <div>The shape is settled, the content is not. For this brief the proposed set is: cover every stated
                requirement, land 3+ reach at or above {pct(FRAME.reachGoal3,1)} of the in-market universe, hold digital
                blended CPM under {cpmf(FRAME.cpmCeiling)}, respect every P&amp;I floor and cap, and carry a reason for
                every deviation. The Analyze phase scores against exactly this.</div></div>
          </div>
        )}

        {tab==="evidence" && (
          <div className="col" style={{gap:12}}>
          <div className="banner b"><span className="bi">Graph</span>
            <div>This is the <b>RFP graph</b>. Every intake agent writes records into it and reads back out of it —
              none of them writes the brief. The brief is derived from the graph once, at the end, which is why
              correcting a record re-derives the brief rather than editing it.</div></div>

          <EvidenceEval graph={evGraph}/>

          <Card title="Evidence store" tight
            sub="Records, not summaries. Superseded, never edited or deleted — the brief can be rebuilt from this at any version.">
            <XL name="evidence_store" height={500} rows={[
              ...EVIDENCE,
              ...st.corrections.map(c=>({ id:c.id, attr:c.attr, value:c.value, cls:"planner",
                src:"Planner correction", loc:"—", ts:c.at, by:"You" })),
              ...Object.entries(st.gapDecisions).map(([gid,d])=>({ id:gid, attr:(GAPS.find(g=>g.id===gid)||{}).attr,
                value:d.value, cls:d.cls, src:"Gap recommendation " + d.status, loc:"—", ts:d.at, by:"You" })),
            ]} cols={[
              { key:"id", label:"Record", w:60, get:r=>r.id, cell:r=><span className="mono">{r.id}</span> },
              { key:"attr", label:"Attribute", w:170, get:r=>r.attr },
              { key:"value", label:"Value", w:400, get:r=>r.value },
              { key:"cls", label:"Provenance", w:130, get:r=>PROV[r.cls]?.label || r.cls,
                cell:r=><ProvChip cls={r.cls} small/> },
              { key:"conf", label:"Confidence", w:96,
                get:r=>(evGraph.by[r.id] ? evGraph.by[r.id].conf : scoreEvidence(r, EVIDENCE).conf),
                raw:r=>(evGraph.by[r.id] ? evGraph.by[r.id].conf : scoreEvidence(r, EVIDENCE).conf),
                cell:r=>{ const x = evGraph.by[r.id] || scoreEvidence(r, EVIDENCE);
                  return <span title={[...x.strengths.map(s=>`+ ${s.t}`), ...x.weaknesses.map(w=>`− ${w.t}`)].join("\n")}>
                    <ConfBar v={x.conf}/></span>; } },
              { key:"src", label:"Source", w:200, get:r=>r.src },
              { key:"loc", label:"Where in the source", w:190, get:r=>r.loc },
              { key:"ts", label:"Arrived", w:118, get:r=>r.ts },
              { key:"by", label:"By", w:130, get:r=>r.by },
            ]}/>
          </Card>
          </div>
        )}

        {tab==="gaps" && (
          <div className="col" style={{gap:12}}>
            <div className="banner b"><span className="bi">Rule</span>
              <div>A material gap is surfaced together with a recommendation wherever one can be justified — never as a
                bare question. Acceptance does not promote it: an accepted inference stays visibly inferred.</div></div>
            {GAPS.map(g=>{
              const d = st.gapDecisions[g.id];
              return (
                <Card key={g.id} title={g.attr}
                  sub={g.why}
                  right={<div className="row" style={{gap:6}}>
                    <Chip c={g.material?"r":""}>{g.material ? "MATERIAL" : "immaterial"}</Chip>
                    {g.status==="absence" && <Chip c="a">ABSENCE</Chip>}
                    {d && <Chip c={d.status==="rejected"?"r":"g"}>{d.status.toUpperCase()}</Chip>}
                  </div>}>
                  <div className="banner b" style={{marginBottom:11}}>
                    <span className="bi">Recommendation</span>
                    <div><b>{g.rec}</b>
                      <div style={{marginTop:5}} className="tiny">Basis: {g.basis}</div>
                      {g.cohortSet.length>0 && <div className="tiny dim" style={{marginTop:4}}>
                        Comparable set: {g.cohortSet.join(" · ")}</div>}
                      <div className="tiny" style={{marginTop:5}}>Would carry: <ProvChip cls={g.wouldCarry} small/></div>
                    </div>
                  </div>
                  {d ? (
                    <div className="banner g"><span className="bi">{d.status}</span>
                      <div><b>{d.value}</b><div className="tiny" style={{marginTop:3}}>“{d.reason}” — {d.at}</div>
                        {d.status==="rejected" && <div className="tiny" style={{marginTop:4}}>
                          This recommendation will not be re-offered unchanged.</div>}</div></div>
                  ) : (
                    <div className="row" style={{gap:7}}>
                      <Btn c="pri sm" onClick={()=>setGap({g, kind:"accepted"})}>Accept as proposed</Btn>
                      <Btn c="sm" onClick={()=>setGap({g, kind:"edited"})}>Accept with an edit</Btn>
                      <Btn c="sm dgr" onClick={()=>setGap({g, kind:"rejected"})}>Reject</Btn>
                      <div style={{flex:1}}/>
                      <span className="tiny dim">Each of these is recorded with a reason.</span>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        )}

        {tab==="contra" && (
          <div className="col" style={{gap:12}}>
            <div className="banner a"><span className="bi">Rule</span>
              <div>Where two sources say different things about the same attribute, both records are kept and the pair is
                surfaced with a recommendation. Neither quietly wins.</div></div>
            {CONTRADICTIONS.map(c=>{
              const d = st.contraDecisions[c.id];
              return (
                <Card key={c.id} title={c.attr} sub={c.id}
                  right={<div className="row" style={{gap:6}}>
                    <Chip c={c.material?"r":""}>{c.material?"MATERIAL":"immaterial"}</Chip>
                    {d && <Chip c="g">ADJUDICATED</Chip>}</div>}>
                  <div className="g2" style={{marginBottom:11}}>
                    {[c.a, c.b].map((r,i)=>(
                      <div key={i} className="card" style={{background:"var(--panel-2)"}}>
                        <div className="card-b">
                          <div className="row" style={{marginBottom:6}}>
                            <ProvChip cls={r.cls} small/><span className="mono dim">{r.ev}</span>
                            <div style={{flex:1}}/><span className="tiny dim">{r.ts}</span>
                          </div>
                          <div style={{fontSize:12.5}}>{r.text}</div>
                          {r.loc && <div className="mini dim" style={{marginTop:4}}>{r.loc}</div>}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="banner b"><span className="bi">Recommendation</span>
                    <div>{c.rec}<div className="tiny" style={{marginTop:4}}>Basis: {c.basis}</div></div></div>
                  <div className="row" style={{gap:7, marginTop:11}}>
                    {d ? <div className="banner g" style={{flex:1}}><span className="bi">{d.choice}</span>
                          <div className="tiny">“{d.reason}” — {d.at}</div></div>
                      : <>
                        <Btn c="pri sm" onClick={()=>setContra({c, choice:"Recommendation adopted"})}>Adopt the recommendation</Btn>
                        <Btn c="sm" onClick={()=>setContra({c, choice:"Later record wins"})}>Later record wins</Btn>
                        <Btn c="sm" onClick={()=>setContra({c, choice:"Original record wins"})}>Original record wins</Btn>
                      </>}
                  </div>
                </Card>
              );
            })}
          </div>
        )}

        {tab==="history" && (
          <div className="col" style={{gap:14}}>
            <Card title="Advertiser history — how this advertiser actually buys" tight
              sub="Held as records so every inference can name the deals behind it.">
              <XL name="advertiser_history" height={200} rows={HISTORY} cols={[
                { key:"plan", label:"Plan", w:80, get:r=>r.plan },
                { key:"name", label:"Name", w:230, get:r=>r.name },
                { key:"closed", label:"Closed", w:88, get:r=>r.closed },
                { key:"gross", label:"Gross", w:88, align:"r", get:r=>money1(r.gross), raw:r=>r.gross },
                { key:"linearPct", label:"Linear %", w:74, align:"r", get:r=>r.linearPct+"%", raw:r=>r.linearPct },
                { key:"cpm", label:"CPM paid", w:80, align:"r", get:r=>cpmf(r.cpm), raw:r=>r.cpm },
                { key:"topProducts", label:"Top products", w:290, get:r=>r.topProducts.join(", ") },
                { key:"outcome", label:"Outcome", w:180, get:r=>r.outcome },
                { key:"rejected", label:"Rejected, and why", w:290, get:r=>r.rejected },
              ]}/>
            </Card>
            <div className="g2">
              <Card title="What history proposes" sub="Proposals, not facts. They stay marked as inferred even after you accept them.">
                {EVIDENCE.filter(e=>e.cls==="hist").map(e=>(
                  <div className="bl" key={e.id}><div className="bk">{e.attr}</div>
                    <div className="bv">{e.value}<span className="why">{e.src} · {e.loc}</span></div>
                    <ProvChip cls="hist" small/></div>))}
              </Card>
              <Card title="What the cohort proposes" sub="Used where this advertiser's own record cannot answer.">
                {EVIDENCE.filter(e=>e.cls==="cohort").map(e=>(
                  <div className="bl" key={e.id}><div className="bk">{e.attr}</div>
                    <div className="bv">{e.value}<span className="why">{e.src} · {e.loc}</span></div>
                    <ProvChip cls="cohort" small/></div>))}
                <div className="banner a" style={{marginTop:10}}><span className="bi">[OQ-6]</span>
                  <div>What makes an advertiser similar enough is undefined. Until it is settled, the comparable set is
                    printed on every cohort recommendation so a planner can judge the match themselves.</div></div>
              </Card>
            </div>
          </div>
        )}

        {tab==="timeline" && (
          <Card title="Timeline of information updates" sub="Every correction, clarification, supersession and adjudication in order, with who changed what and why.">
            <Timeline items={st.timeline}/>
          </Card>
        )}
      </div>

      {/* ------------------------------------------------------------- side */}
      <div className="col sticky" style={{gap:14}}>
        <Card title="Approve the brief" sub="The planner is the only approver. The AE and P&I are voices in the evidence, not approval steps.">
          {st.intakeApproved ? (
            <div className="banner g"><span className="bi">Approved</span>
              <div>Brief v{st.intakeApproved.version}, {st.intakeApproved.at}. Discovery opens on this version with
                accepted inferences carried through, still marked inferred.</div></div>
          ) : (
            <>
              <Btn c="pri" style={{width:"100%", justifyContent:"center"}} disabled={!gateOk}
                onClick={()=>{ up({intakeApproved:{version:st.briefVersion, at:NOW()}});
                  log("ok", `Intake brief v${st.briefVersion} approved. Approval binds to this version, not to the plan.`);
                  toast("Brief v" + st.briefVersion + " approved"); }}>
                Approve intake brief v{st.briefVersion}
              </Btn>
              {!gateOk && <div className="tiny dim" style={{marginTop:7}}>
                {openGaps.length>0 && `${openGaps.length} material gap${openGaps.length>1?"s":""} still open. `}
                {openContras.length>0 && `${openContras.length} material contradiction${openContras.length>1?"s":""} unadjudicated.`}
              </div>}
            </>
          )}
          <div className="tiny dim" style={{marginTop:8}}>
            Approving is one of the five things the gate below scores. Approval alone does not open Discovery.
          </div>
        </Card>

        <Gate gate={gate} verb="Hand off to Discovery"
          onGo={()=>{ up({phase:"discovery"});
            log("sys", `Intake orchestrator handed off to the Discovery orchestrator at gate score ${gate.score}. A sound, defensible intake brief is built.`);
            toast("Handoff accepted — Discovery orchestrator has the brief"); }}
          note="The gate asks whether planning would be invalidated by what is missing — not whether everything is present."/>

        <Assist title="Worth looking at first">
          {openGaps.length > 0 ? <>
            <b>{openGaps[0].attr}</b> is the one that blocks the solve. {openGaps[0].why} The recommendation is drawn
            from {openGaps[0].cohortSet.length ? `${openGaps[0].cohortSet.length} comparable advertisers` : "this advertiser's own record"},
            and it would enter as <ProvChip cls={openGaps[0].wouldCarry} small/> — a proposal, not a fact.
          </> : openContras.length > 0 ? <>
            Everything material is filled. <b>{openContras[0].attr}</b> still has two records saying different things,
            and the plan cannot be approved with that unadjudicated.
          </> : <>
            The gate is clear. Worth noting before you approve: P&amp;I stated nothing specific to this advertiser, and
            that absence is on the record — so if the plan is later challenged on yield, the challenge has to come from
            the four standing position cards, not from a position nobody wrote down.
          </>}
        </Assist>

        <Card title="Provenance in this brief" tight>
          <div style={{padding:"12px 14px"}}>
            {["stated","clarified","hist","cohort","seller","planner"].map(k=>{
              const n = EVIDENCE.filter(e=>e.cls===k).length + (k==="planner" ? st.corrections.length : 0);
              if (!n) return null;
              return <div key={k} className="row" style={{marginBottom:7}}>
                <div style={{width:132}}><ProvChip cls={k} small/></div>
                <div className="grow"><Bar v={n/14}/></div>
                <span className="tiny dim" style={{width:22, textAlign:"right"}}>{n}</span>
              </div>;
            })}
            <div className="tiny muted" style={{marginTop:8}}>
              Nine of these values are inferred rather than stated. They are proposals until you accept them, and they
              stay marked as inferred afterwards.
            </div>
          </div>
        </Card>
      </div>

      {gap && <JustifyG
        title={{accepted:"Accept the recommendation", edited:"Accept with an edit", rejected:"Reject the recommendation"}[gap.kind]}
        what={<><b>{gap.g.attr}</b> — {gap.kind==="rejected" ? "rejecting " : "recording "}
          “{gap.g.rec}”. {gap.kind==="edited" && "Enter your value in the reason, and it will be recorded as a planner value rather than an inference."}
          {gap.kind==="accepted" && " It will stay visibly inferred after acceptance."}</>}
        verb={{accepted:"Accept",edited:"Accept with edit",rejected:"Reject"}[gap.kind]}
        onCancel={()=>setGap(null)}
        onConfirm={(r)=>decideGap(gap.g, gap.kind, gap.kind==="edited" ? r : gap.g.rec, r)}/>}

      {contra && <JustifyG title="Adjudicate the contradiction"
        what={<><b>{contra.c.attr}</b> — recording “{contra.choice}”. Both records stay in the store; neither is deleted.</>}
        verb="Adjudicate" onCancel={()=>setContra(null)}
        onConfirm={(r)=>decideContra(contra.c, contra.choice, r)}/>}

      {fix && <JustifyG title="Correct the system"
        what={<>You are not editing the brief — briefs are read-only. State what is wrong about <b>{fix.k}</b> and what
          it should be. Your statement enters the evidence store as a record, and the brief re-derives to a new version.
          The prior approval lapses.</>}
        verb="Record correction" onCancel={()=>setFix(null)}
        onConfirm={(r)=>{ correct(fix.k, r, r); setFix(null); toast("Correction recorded — brief re-derived"); }}/>}
    </div>
  );
};
