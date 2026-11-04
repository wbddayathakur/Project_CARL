/* =============================================================================
   35-gate.js — the Orchestrator's two surfaces.

   `Gate`     — the handoff panel. Score, evaluation points, and a button that
                shuts only when something the next phase needs is absent.
   `JustifyG` — Justify, with `Eval Justifications` wired in. The planner writes
                an argument and the orchestrator scores it live, naming what a
                stronger one would say.

   Both surfaces separate absent from weak, and treat them differently. Absent
   holds: a gap nobody adjudicated, an override with no reason, a line still on
   an Indicative forecast — the next phase would have to guess. Weak does not
   hold: it is scored, it travels into the rubric and the approval package, and
   P&I reads it at the only gate in the design that can stop a plan (OQ-17).

   The system never blocks a weak argument. It proposes a better one and records
   the departure (OQ-22). A gate the desk could not get past under deadline is a
   gate that gets worked around, which is worse than not having one.
   ============================================================================= */

const GATE_TONE = (score, par) =>
  score >= par ? "var(--good)" : score >= par - 20 ? "#d99400" : "var(--bad)";

const GateRing = ({score, par}) => {
  const R = 26, C = 2 * Math.PI * R;
  return (
    <svg width="66" height="66" viewBox="0 0 66 66" style={{flexShrink:0}}>
      <circle cx="33" cy="33" r={R} fill="none" stroke="var(--line)" strokeWidth="6"/>
      <circle cx="33" cy="33" r={R} fill="none" stroke={GATE_TONE(score,par)} strokeWidth="6" strokeLinecap="round"
        strokeDasharray={`${C*score/100} ${C}`} transform="rotate(-90 33 33)"/>
      <text x="33" y="34" textAnchor="middle" style={{fontSize:16, fontWeight:600, fill:"var(--ink)"}}>{score}</text>
      <text x="33" y="45" textAnchor="middle" style={{fontSize:7.5, fill:"#8a95a0", letterSpacing:".06em"}}>OF 100</text>
    </svg>
  );
};

const Gate = ({gate, verb, onGo, note}) => {
  const [open, setOpen] = useState(false);
  const g = gate;
  const tone = g.verdict === "clean" ? "g" : g.verdict === "open-with-notes" ? "a" : "r";
  const nB = g.blockers.length, nA = g.advisory.length;

  /* Binding points first, then advisory — the order makes the distinction
     legible without having to read the labels. */
  const groups = [
    ["What the next phase cannot work without", g.points.filter(p => p.kind === "binding")],
    ["What travels forward and will be read", g.points.filter(p => p.kind === "advisory")],
  ];

  return (
    <Card title="Handoff gate"
      sub={`${g.meta.from} · ${g.meta.asks}`}
      right={<Chip c={tone}>
        {g.verdict === "clean" ? "CLEAN" : g.verdict === "open-with-notes" ? "OPEN · NOTES" : "INCOMPLETE"}</Chip>}>

      <div className="row" style={{gap:13, alignItems:"center", marginBottom:12}}>
        <GateRing score={g.score} par={g.par}/>
        <div style={{minWidth:0}}>
          <div style={{fontSize:12.5, lineHeight:1.5}}>
            {g.verdict === "clean"
              ? <>Nothing missing and nothing thin. The handoff to <b>{g.meta.to}</b> is open.</>
              : g.verdict === "open-with-notes"
              ? <>The handoff to <b>{g.meta.to}</b> is open. {nA} thing{nA>1?"s":""} {nA>1?"are":"is"} thinner
                  than it could be — {nA>1?"they travel":"it travels"} forward and P&amp;I will read {nA>1?"them":"it"}.</>
              : <>{nB} thing{nB>1?"s":""} {nB>1?"are":"is"} <b>missing</b>, not weak. {nB>1?"They":"It"} cannot be
                  inferred or argued around, so <b>{g.meta.to}</b> has nothing to work from until {nB>1?"they are":"it is"} there.</>}
          </div>
        </div>
      </div>

      {groups.map(([heading, pts]) => pts.length === 0 ? null : (
        <div key={heading} style={{marginBottom:11}}>
          <div className="lbl">{heading}</div>
          <div className="col" style={{gap:7}}>
            {pts.map(p => (
              <div key={p.id} className="row" style={{gap:8, alignItems:"flex-start"}}>
                <Chip c={p.ok ? "g" : p.kind === "binding" ? "r" : "a"}>{p.ok ? "✓" : p.score}</Chip>
                <div style={{minWidth:0, flex:1}}>
                  <div style={{fontSize:12}}>{p.label}{" "}
                    <span className="tiny dim">· weight {p.w}%{p.kind === "advisory" ? ` · bar ${p.bar} · advisory` : ""}</span></div>
                  <div className="tiny muted">{p.detail}</div>
                  {!p.ok && p.fix && <div className="tiny" style={{color:"var(--accent)", marginTop:2}}>→ {p.fix}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {note && <div className="tiny muted" style={{marginTop:11}}>{note}</div>}

      {onGo && <>
        <div className="hr"/>
        <Btn c="pri" style={{width:"100%"}} disabled={!g.open} onClick={onGo}>
          {g.open ? verb : `${verb} — ${nB} thing${nB>1?"s":""} missing`}
        </Btn>
        <div className="tiny dim" style={{marginTop:6}}>
          {g.open
            ? <>Advisory points never hold the handoff. A weak argument goes forward carrying its
                weakness, because a gate the desk could not get past under deadline would simply be
                worked around.</>
            : <>Only the points above the line hold the handoff, and only because something is absent
                rather than weak. Nothing here is a judgement about whether you are right.</>}
        </div>
      </>}

      {!onGo && <div className="tiny dim" style={{marginTop:10}}>
        Read-only: this phase is not the current one.
      </div>}

      <div style={{marginTop:10}}>
        <Btn c="xs gho" onClick={()=>setOpen(o=>!o)}>{open ? "Hide" : "What is this?"}</Btn>
        {open && <div className="tiny muted" style={{marginTop:8, lineHeight:1.6}}>
          The orchestrator knows the whole state machine and scores the intermediate status at every
          evaluation point inside it. It distinguishes two things and treats them differently.
          Something <b>missing</b> stops the handoff, because the next phase would have to guess.
          Something <b>weak</b> does not: it is scored, it travels into the rubric and the approval
          package, and P&amp;I reads it at the only gate that can actually stop a plan. The system
          never blocks a weak argument — it proposes a better one and records the departure.
        </div>}
      </div>
    </Card>
  );
};

/* ------------------------------------------------------- justify + challenge */
/* `Eval Justifications` from the Discovery flow: NO loops back to the human
   with feedback, YES lets the change through. */
const JustifyG = ({title, what, onCancel, onConfirm, verb="Record change", hints=[], kind="change"}) => {
  const [t, setT] = useState("");
  const ev = useMemo(() => evalJustification(t, {kind}), [t, kind]);

  /* Absence blocks; weakness does not. A change with no reason at all cannot be
     read by P&I, so it is not accepted. A weakly argued one goes forward
     carrying its score — the system proposes a better argument and records the
     departure, it does not refuse the change (OQ-22). */
  const canSubmit = t.trim().length >= 20;
  const tone = ev.verdict === "pass" ? "g" : ev.verdict === "thin" ? "a" : "r";

  return (
    <Modal title={title}
      sub="The reason is scored as you write it, and the score travels with the change. A thin argument is not refused — it arrives at P&I visibly thin."
      onClose={onCancel}
      footer={<>
        <div className="tiny dim">
          {!canSubmit ? "A change with no reason cannot be read by P&I at all."
            : ev.verdict === "pass" ? "Defensible on its own. Travels into the brief and the approval package."
            : ev.verdict === "thin" ? "Goes forward, and a reader would have to ask you one question."
            : "Goes forward flagged. P&I sees the score alongside the change."}
        </div>
        <div style={{flex:1}}/>
        <Btn onClick={onCancel}>Cancel</Btn>
        <Btn c="pri" disabled={!canSubmit} onClick={()=>onConfirm(t.trim(), ev)}>
          {ev.verdict === "revise" && canSubmit ? `${verb} — flagged thin` : verb}
        </Btn>
      </>}>

      <div className="banner b" style={{marginBottom:14}}><span className="bi">Change</span><div>{what}</div></div>

      <label className="lbl">Why</label>
      <textarea className="inp" autoFocus value={t} onChange={e=>setT(e.target.value)}
        placeholder="State what the system got wrong, what you know that it does not, and what your change costs. This is what P&I will read." />

      {/* live evaluation — the four tests, scored as you type */}
      <div className="row" style={{gap:10, alignItems:"center", marginTop:12}}>
        <Chip c={tone}>ARGUMENT {ev.score}</Chip>
        <div className={"bar " + tone} style={{flex:1}}><i style={{width:ev.score+"%"}}/></div>
      </div>

      <div className="col" style={{gap:5, marginTop:9}}>
        {ev.tests.map(x => (
          <div key={x.id} className="row" style={{gap:7, alignItems:"flex-start"}}>
            <span style={{color: x.ok?"var(--good)":"#8a95a0", fontSize:12, lineHeight:1.5, flexShrink:0}}>
              {x.ok ? "✓" : "○"}</span>
            <div style={{minWidth:0}}>
              <span style={{fontSize:11.5, color: x.ok?"var(--ink)":"var(--ink-2)"}}>{x.label}</span>
              {!x.ok && t.trim().length > 0 &&
                <div className="tiny dim" style={{marginTop:1}}>{x.ask}</div>}
            </div>
          </div>
        ))}
      </div>

      {/* What a better argument would say. A proposal, not a refusal. */}
      {ev.verdict === "revise" && t.trim().length >= 20 && <div className="banner a" style={{marginTop:13}}>
        <span className="bi">Thin</span>
        <div>
          {ev.feedback}
          {ev.missing.length > 0 && <ul style={{margin:"7px 0 0 16px", padding:0}}>
            {ev.missing.map(m => <li key={m.id} style={{marginBottom:3}}>{m.ask}</li>)}
          </ul>}
          <div className="tiny" style={{marginTop:7}}>
            Record it as it stands if that is the argument. It is not blocked — it arrives at P&amp;I
            scored {ev.score}, and the score is part of what they decide on.
          </div>
        </div>
      </div>}

      {hints.length > 0 && <div style={{marginTop:12}}>
        <div className="lbl">Reasons used on this deal before</div>
        <div className="row wrap" style={{gap:6}}>
          {hints.map((h,i)=><button key={i} className="chip o" style={{cursor:"pointer"}}
            onClick={()=>setT(h)}>{h.slice(0,64)}…</button>)}
        </div>
      </div>}
    </Modal>
  );
};
