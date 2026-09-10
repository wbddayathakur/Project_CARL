/* =============================================================================
   35-gate.js — the Orchestrator's two surfaces.

   `Gate`     — the handoff panel. Score, evaluation points, and the button that
                stays shut until the phase is defensible.
   `JustifyG` — Justify, with `Eval Justifications` wired in. The planner writes
                an argument, the orchestrator scores it live, and a weak one is
                sent back with the specific thing it is missing rather than
                accepted and quietly passed downstream.

   Neither surface decides. The gate says what is not yet sound; the evaluator
   says what an argument lacks. A human still moves the plan (T7).
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
  const cls = g.verdict === "handoff" ? "ok" : g.verdict === "surface" ? "warn" : "bad";
  return (
    <Card title="Handoff gate"
      sub={`${g.meta.from} · ${g.meta.asks}`}
      right={<Chip c={cls === "ok" ? "g" : cls === "warn" ? "a" : "r"}>
        {g.verdict === "handoff" ? "READY" : g.verdict === "surface" ? "SURFACED" : "BELOW PAR"}</Chip>}>

      <div className="row" style={{gap:13, alignItems:"center", marginBottom:12}}>
        <GateRing score={g.score} par={g.par}/>
        <div style={{minWidth:0}}>
          <div style={{fontSize:12.5, lineHeight:1.5}}>
            {g.verdict === "handoff"
              ? <>Every evaluation point is met. The handoff to <b>{g.meta.to}</b> is open.</>
              : g.verdict === "surface"
              ? <>Above par at <b>{g.score}</b>, but {g.blockers.length} point{g.blockers.length>1?"s":""} {g.blockers.length>1?"are":"is"} unmet.
                  Surfaced for your judgement rather than run again.</>
              : <>Below par at <b>{g.score}</b> against {g.par}. The orchestrator holds the handoff and
                  loops back rather than passing this to <b>{g.meta.to}</b>.</>}
          </div>
        </div>
      </div>

      <div className="col" style={{gap:7}}>
        {g.points.map(p => (
          <div key={p.id} className="row" style={{gap:8, alignItems:"flex-start"}}>
            <Chip c={p.ok ? "g" : p.score >= 60 ? "a" : "r"}>{p.ok ? "✓" : p.score}</Chip>
            <div style={{minWidth:0, flex:1}}>
              <div style={{fontSize:12}}>{p.label}{" "}
                <span className="tiny dim">· weight {p.w}%{p.bar < 100 ? ` · bar ${p.bar}` : ""}</span></div>
              <div className="tiny muted">{p.detail}</div>
              {!p.ok && p.fix && <div className="tiny" style={{color:"var(--accent)", marginTop:2}}>→ {p.fix}</div>}
            </div>
          </div>
        ))}
      </div>

      {note && <div className="tiny muted" style={{marginTop:11}}>{note}</div>}

      {onGo && <>
        <div className="hr"/>
        <Btn c="pri" style={{width:"100%"}} disabled={!g.open} onClick={onGo}>
          {g.open ? verb : `${verb} — held at ${g.score}`}
        </Btn>
        {!g.open && <div className="tiny dim" style={{marginTop:6}}>
          The button opens when every point is met. Nothing here can be waived —
          the gate is what makes the next phase's inputs trustworthy.
        </div>}
      </>}

      {!onGo && <div className="tiny dim" style={{marginTop:10}}>
        Read-only: this phase is not the current one.
      </div>}

      <div style={{marginTop:10}}>
        <Btn c="xs gho" onClick={()=>setOpen(o=>!o)}>{open ? "Hide" : "What is this?"}</Btn>
        {open && <div className="tiny muted" style={{marginTop:8, lineHeight:1.6}}>
          The orchestrator knows the whole state machine and the evaluation points inside it, and it
          scores the intermediate status at each one. Below par it loops the phase again or surfaces
          for your input; it never advances the plan on its own and never overrules you. Its one
          power is to refuse a handoff.
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
  const [tries, setTries] = useState(0);
  const [sent, setSent] = useState(null);          // the evaluation that came back
  const ev = useMemo(() => evalJustification(t, {kind}), [t, kind]);
  const canSubmit = t.trim().length >= 20;

  const submit = () => {
    const e = evalJustification(t, {kind});
    if (e.verdict === "revise"){ setSent(e); setTries(n=>n+1); return; }
    onConfirm(t.trim(), e);
  };

  const tone = ev.verdict === "pass" ? "g" : ev.verdict === "thin" ? "a" : "r";

  return (
    <Modal title={title}
      sub="The reason is evaluated before the change is accepted. A weak argument comes back to you rather than going forward (Flow architecture — Eval Justifications)."
      onClose={onCancel}
      footer={<>
        <div className="tiny dim">
          {ev.verdict === "pass" ? "Defensible. This travels into the brief and the approval package."
            : ev.verdict === "thin" ? "This will travel, but a reader would have to ask you a question."
            : "Not yet defensible."}
        </div>
        <div style={{flex:1}}/>
        <Btn onClick={onCancel}>Cancel</Btn>
        {tries >= 2 && ev.verdict === "revise" &&
          <Btn onClick={()=>onConfirm(t.trim(), ev)} title="Recorded as a weak argument and flagged wherever it is read">
            Record as weak
          </Btn>}
        <Btn c="pri" disabled={!canSubmit} onClick={submit}>{verb}</Btn>
      </>}>

      <div className="banner b" style={{marginBottom:14}}><span className="bi">Change</span><div>{what}</div></div>

      <label className="lbl">Why</label>
      <textarea className="inp" autoFocus value={t} onChange={e=>{setT(e.target.value); setSent(null);}}
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

      {/* the NO edge: sent back with feedback */}
      {sent && <div className="banner r" style={{marginTop:13}}>
        <span className="bi">Sent back</span>
        <div>
          <b>The orchestrator did not accept this reason.</b> {sent.feedback}
          {sent.missing.length > 0 && <ul style={{margin:"7px 0 0 16px", padding:0}}>
            {sent.missing.map(m => <li key={m.id} style={{marginBottom:3}}>{m.ask}</li>)}
          </ul>}
          {tries >= 2 && <div className="tiny" style={{marginTop:7}}>
            You can record it as a weak argument instead. It goes forward flagged, and P&I sees that
            it was flagged — the change is not blocked, only its quality is on the record.
          </div>}
        </div>
      </div>}

      {hints.length > 0 && <div style={{marginTop:12}}>
        <div className="lbl">Reasons used on this deal before</div>
        <div className="row wrap" style={{gap:6}}>
          {hints.map((h,i)=><button key={i} className="chip o" style={{cursor:"pointer"}}
            onClick={()=>{setT(h); setSent(null);}}>{h.slice(0,64)}…</button>)}
        </div>
      </div>}
    </Modal>
  );
};
