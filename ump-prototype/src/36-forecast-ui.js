/* =============================================================================
   36-forecast-ui.js — the surfaces for the forecast boundary.

   `FidelityChip`  which class a figure belongs to, readable at a glance
   `StaleBadge`    the run date, its age, and the re-run when it is too old
   `WaterfallView` the ten-step derivation of one Constrained figure
   `SellThrough`   what P&I sees: this line against the real inventory position

   The waterfall is the Allocation Engine's own model, reused rather than
   duplicated, because it is the route to the evidence behind every number the
   plan rests on (T5). Displayed values are the model's values — no rounding and
   no approximation, a rule V1.1 already established.
   ============================================================================= */

const FidelityChip = ({f, runAt}) => {
  const d = FIDELITY[f || "indicative"];
  return <Chip c={d.tone} title={`${d.what}\n\nGranularity: ${d.granularity}\nTargeting: ${d.targeting}\nComputed: ${d.computed}\nAdmissible for: ${d.admissible}${runAt ? `\n\nRun ${runAt}` : ""}`}>
    {d.short}</Chip>;
};

const StaleBadge = ({runAt, onRerun}) => {
  if (!runAt) return null;
  const s = staleness(runAt);
  return (
    <span className="row tiny" style={{gap:6, alignItems:"center", display:"inline-flex"}}>
      <span className="dim">run {runAt}</span>
      <Chip c={s.stale ? "a" : ""} title={s.stale
        ? `Older than the ${s.threshold}h threshold. Inventory moves; a version committed against figures that have since changed may no longer be deliverable.`
        : "Within the freshness threshold."}>{s.label}</Chip>
      {s.stale && onRerun && <Btn c="xs" onClick={onRerun}>Request a fresh run</Btn>}
    </span>
  );
};

/* The derivation. Every Constrained figure has one, and it is the same object
   the approval package carries, so P&I and the planner read the same thing. */
const WaterfallView = ({w, compact}) => {
  if (!w) return <div className="tiny dim">No Constrained run for this line yet — it still rests on the Indicative pre-screen.</div>;
  const top = w.rows[0].value;
  return (
    <div>
      <div className="row tiny" style={{gap:9, marginBottom:8, alignItems:"center"}}>
        <Chip c="n">{w.pid}</Chip>
        <span className="dim">run {w.runAt}</span>
        <div style={{flex:1}}/>
        <span className="dim">{pct(w.reductionPct,1)} reduction, capacity to net</span>
      </div>
      <div className="col" style={{gap:0}}>
        {w.rows.map((r,i) => (
          <div key={r.k} style={{
            display:"grid", gridTemplateColumns:"1fr 90px 74px", gap:8, alignItems:"center",
            padding:"5px 0", borderTop: i ? "1px solid var(--line)" : "none",
            background: r.strong ? "var(--accent-soft)" : r.divider ? "var(--line-2)" : null }}>
            <div style={{minWidth:0}}>
              <div style={{fontSize:11.5, fontWeight: r.strong ? 600 : 400}}>{r.label}</div>
              {!compact && <div className="mini dim" style={{lineHeight:1.45}}>{r.note}</div>}
            </div>
            <div style={{textAlign:"right", fontSize:11.5, fontWeight: r.strong ? 700 : 500}}>
              {imps(r.value)}
            </div>
            <div style={{textAlign:"right"}}>
              {r.lost > 0
                ? <span className="mini" style={{color:"var(--bad)"}}>−{imps(r.lost)}</span>
                : <span className="mini dim">—</span>}
            </div>
          </div>
        ))}
      </div>
      <div className="mini dim" style={{marginTop:7, lineHeight:1.5}}>
        The run date is part of the derivation. The same line reading a 15% reduction on one date and
        10.7% on another is not a contradiction — it is the model behaving correctly, and the date is
        what makes that legible.
      </div>
    </div>
  );
};

/* What P&I sees at approval, per line. The plan under review projected onto the
   real inventory position: everything already booked and pressured, everything
   else in flight competing for the same pool, and what this line would take.
   Line level, never aggregated — P&I decides one line at a time. */
const SellThrough = ({line}) => {
  const p = line.p || PRODUCTS.find(x => x.id === line.pid);
  if (!p) return null;
  const res  = reservedFor(p);
  const comp = competingUmpDemand(p);
  const askK = line.impsK;

  const pctOf = k => k / res.capacityK;
  const now       = res.reservedK / res.capacityK;
  const projected = (res.reservedK + askK) / res.capacityK;
  const withComp  = (res.reservedK + askK + comp.askK) / res.capacityK;

  const toneVar = projected > 0.95 ? "var(--bad)" : projected > 0.85 ? "var(--warn)" : "var(--good)";

  return (
    <div>
      {/* One stacked bar: reserved, this plan, competing demand, headroom. */}
      <div className="row" style={{height:13, borderRadius:3, overflow:"hidden", background:"var(--line)", marginBottom:7}}>
        <div style={{width:`${pctOf(res.bookedK)*100}%`, background:"#5b6770"}} title={`Booked (signed IO) ${imps(res.bookedK)}`}/>
        <div style={{width:`${pctOf(res.pressuredK)*100}%`, background:"#8a95a0"}} title={`COMS-pressured ${imps(res.pressuredK)}`}/>
        <div style={{width:`${pctOf(askK)*100}%`, background:"var(--accent)"}} title={`This plan's ask ${imps(askK)}`}/>
        <div style={{width:`${pctOf(comp.askK)*100}%`, background:"var(--violet)", opacity:0.55}} title={`Competing UMP plans ${imps(comp.askK)}`}/>
      </div>
      <div className="row wrap mini" style={{gap:11, marginBottom:9}}>
        <span><i className="key" style={{background:"#5b6770"}}/>Booked {imps(res.bookedK)}</span>
        <span><i className="key" style={{background:"#8a95a0"}}/>COMS-pressured {imps(res.pressuredK)}</span>
        <span><i className="key" style={{background:"var(--accent)"}}/>This plan {imps(askK)}</span>
        {comp.askK > 0 && <span><i className="key" style={{background:"var(--violet)", opacity:0.55}}/>Competing UMP {imps(comp.askK)}</span>}
      </div>

      <dl className="kv tiny" style={{gridTemplateColumns:"132px 1fr"}}>
        <dt>Total capacity</dt>
        <dd>{imps(res.capacityK)} <span className="dim">across the flight, before exclusions</span></dd>
        <dt>Already reserved</dt>
        <dd><b>{imps(res.reservedK)}</b> <span className="dim">= {pctn(now*100,1)} sold. Booked plus COMS-pressured,
          combined — the Allocation Engine excludes both before it returns anything, and never breaks them out
          to a planner.</span></dd>
        <dt>This plan's ask</dt>
        <dd><b>{imps(askK)}</b> <span className="dim">{pct(line.availUse,0)} of the net available this line was
          forecast against</span></dd>
        <dt>Projected sell-through</dt>
        <dd><b style={{color:toneVar}}>{pctn(projected*100,1)}</b>
          <span className="dim"> if you approve this line</span></dd>
        <dt>Competing UMP plans</dt>
        <dd>{comp.plans.length
          ? <>{comp.plans.map(x => `${x.advertiser} ${imps(x.askK)}`).join(", ")} — <b>{pctn(withComp*100,1)}</b> if
              all of it lands. <span className="dim">Not current functionality: the Allocation Engine does not
              identify competing UMP demand today. Carried here as the stated requirement.</span></>
          : <span className="dim">No other in-flight UMP plan is targeting this product.</span>}</dd>
      </dl>

      {projected > 0.90 && (
        <div className="banner a" style={{marginTop:9}}>
          <span className="bi">Tight</span>
          <div className="tiny">Approving this line takes the product to {pctn(projected*100,1)} sold. There is
            {" "}{imps(res.capacityK - res.reservedK - askK)} of headroom left for everything else in the quarter.</div>
        </div>
      )}
    </div>
  );
};
