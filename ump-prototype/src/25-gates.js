/* =============================================================================
   25-gates.js — the Orchestrator.

   From the Flow Architecture note (6 Sep 2026):
     · knows the full state machine, the evaluation points, and the current
       score at each point
     · understands and scores the intermediate status
     · if scores are below par, re-runs the loop or surfaces for strategic
       analysis and input

   Two things live here. The phase gate, which scores whether a handoff is
   allowed to open at all, and the justification evaluator, which is the
   `Eval Justifications` box in the Discovery flow — the one whose NO edge
   loops back to the human instead of forward to the next step.

   Both are deterministic and both show their working. Neither one decides
   anything: the gate says what is not yet defensible, the evaluator says what
   an argument is missing. A human still moves the plan (T7, T8).
   ============================================================================= */

const GATE_PAR = 80;            // below par, the handoff does not open

/* -----------------------------------------------------------------------------
   EVAL JUSTIFICATIONS

   Scores what an argument *contains*, never what it concludes. A planner can
   argue anything they like; they cannot argue it in a way a reader outside the
   room could not act on.

   The four tests are the ones a P&I approver actually applies when a line
   arrives with a reason attached: is there enough of it, does it cite something
   checkable, is it anchored in the evidence rather than in taste, and does it
   own what it costs.
-------------------------------------------------------------------------------*/

const JUST_ANCHORS = [
  "rfp","brief","client","stated","clarifi","position","p&i","pi ","history","cohort",
  "kpi","reach","frequency","floor","ceiling","cap","constraint","avail","sellout","sell-out",
  "yield","composition","demo","viewab","cpm","benchmark","cards","push list","do-not-air",
  "call notes","evidence","last year","q3","q4","flight","pack change","launch","competitive",
];

const JUST_CONSEQUENCE = [
  "cost","costs","trade","instead","rather than","at the expense","gives up","give up",
  "worth it","hit","sacrific","in exchange","pay for","comes out of","loses","lose",
  "goes backwards","accept","tolerat","downside","risk","expensive","efficiency",
  "even though","despite","knowing",
];

const JUST_PREFERENCE = [
  "i think","i prefer","i feel","feels","seems","looks better","better","best","makes sense",
  "should be","want to","i like","obviously","clearly","just ","fine","good idea","trust me",
];

function evalJustification(text, opts){
  const o = Object.assign({ kind:"change" }, opts || {});
  const t = String(text || "").trim();
  const low = t.toLowerCase();
  const words = t.split(/\s+/).filter(Boolean).length;

  const hasAny = list => list.some(k => low.includes(k));

  const tests = [
    { id:"substance", label:"Enough of an argument to read",
      ok: t.length >= 55 && words >= 11,
      ask:"Two sentences at least. What the system got wrong, and what you know that it does not." },
    { id:"specific", label:"Cites something checkable",
      ok: /\d/.test(t) || /[$%]/.test(t),
      ask:"Name the number you are arguing about — the CPM, the share, the reach point, the date." },
    { id:"grounded", label:"Anchored in the evidence, not in taste",
      ok: hasAny(JUST_ANCHORS),
      ask:"Point at the record: the RFP, a clarification, the P&I position, the advertiser's history, the KPI." },
    { id:"consequence", label:"Owns what the change costs",
      ok: hasAny(JUST_CONSEQUENCE),
      ask:"Say what this gives up. An argument that costs nothing reads as one that was not weighed." },
  ];

  const passed = tests.filter(x => x.ok);
  let score = Math.round(passed.length / tests.length * 100);

  /* Preference language on its own is the failure mode this box exists to
     catch: it reads like a reason and carries none. */
  const prefOnly = hasAny(JUST_PREFERENCE) && !tests[1].ok && !tests[2].ok;
  if (prefOnly) score = Math.min(score, 25);

  return {
    score,
    tests,
    missing: tests.filter(x => !x.ok),
    prefOnly,
    verdict: score >= 75 ? "pass" : score >= 50 ? "thin" : "revise",
    /* The feedback edge in the flow: what the orchestrator sends back. */
    feedback: prefOnly
      ? "This reads as a preference rather than an argument. Nothing in it can be checked or contested, so P&I has nothing to approve against."
      : score >= 75 ? "This is defensible on its own. It goes forward as written."
      : score >= 50 ? "This will travel, but a reader outside the room would have to ask you a question to act on it."
      : "Not yet defensible. Sent back rather than forward.",
  };
}

/* Justifications already on the plan, scored in bulk — used by the gates. */
function scoreJustifications(map){
  const out = Object.entries(map || {})
    .filter(([, v]) => String(v || "").trim().length > 0)
    .map(([k, v]) => ({ key:k, ...evalJustification(v) }));
  return {
    all: out,
    weak: out.filter(x => x.verdict === "revise"),
    thin: out.filter(x => x.verdict === "thin"),
    mean: out.length ? Math.round(out.reduce((s,x)=>s+x.score,0) / out.length) : 100,
  };
}

/* -----------------------------------------------------------------------------
   THE PHASE GATE

   One evaluation set per handoff. Each point carries its weight, its current
   score, and — when it is not met — the specific thing that would meet it.
   The note's rule: "what constitutes the trigger handoff to the Discovery
   orchestrator — a sound, defensible intake brief is built."
-------------------------------------------------------------------------------*/

const GATE_META = {
  intake:     { to:"Discovery",  from:"Intake orchestrator",     asks:"Is a sound, defensible intake brief built?" },
  discovery:  { to:"Strategize", from:"Discovery orchestrator",  asks:"Is this ranked list one the planner would defend, product by product?" },
  strategize: { to:"Analyze",    from:"Strategize orchestrator",  asks:"Is there a saved allocation whose every deviation is argued?" },
  analyze:    { to:"Approval",   from:"Analyze orchestrator",    asks:"Is one version chosen, and is the choice legible?" },
  approval:   { to:"the client proposal",      from:"Approval orchestrator",   asks:"Does every line carry a decision and a reason?" },
};

function evaluateGate(phase, st, ctx){
  const c = ctx || {};
  const pt = [];
  /* Binding points hold the handoff. They test for the *absence* of something
     the next phase cannot work without — an unadjudicated gap, an override with
     no reason at all, a line still resting on an Indicative forecast. */
  const add = (id, label, w, ok, detail, fix) =>
    pt.push({ id, label, w, bar:100, kind:"binding", ok:!!ok, score: ok?100:0, detail, fix });

  /* Advisory points never hold the handoff. They measure *quality* — how good an
     argument is, how strong the evidence is — and quality is not the system's to
     veto (OQ-22: the system never blocks a weak strategy, it proposes a better
     one and records the departure). The score travels into the rubric and into
     the approval package, where P&I reads it and it carries consequence. */
  const addA = (id, label, w, score, detail, fix, bar) => {
    const b = bar == null ? 70 : bar;
    pt.push({ id, label, w, bar:b, kind:"advisory", ok: score >= b, score: Math.round(score), detail, fix });
  };

  if (phase === "intake"){
    const material = GAPS.filter(g => g.material);
    const openGaps = material.filter(g => !st.gapDecisions[g.id]);
    const matContra  = CONTRADICTIONS.filter(x => x.material);
    const openContra = matContra.filter(x => !st.contraDecisions[x.id]);
    const jm = scoreJustifications(Object.fromEntries(
      Object.entries(st.gapDecisions).map(([k,v]) => [k, v && v.reason])));

    add("G1", "Every material requirement received or inferred, and accepted", 26,
      openGaps.length === 0,
      `${material.length - openGaps.length} of ${material.length} material gaps adjudicated.`,
      openGaps.length ? `Resolve ${openGaps.map(g=>g.id).join(", ")}.` : null);

    add("G2", "No contradiction left standing on a material attribute", 22,
      openContra.length === 0,
      `${matContra.length - openContra.length} of ${matContra.length} material contradictions adjudicated.`,
      openContra.length ? `Adjudicate ${openContra.map(x=>x.id).join(", ")}.` : null);

    /* Scored by the Evidence Eval Agent on the RFP graph, not asserted here. */
    const eg = c.evGraph || evalEvidenceGraph(EVIDENCE, st);
    addA("G3", "The graph is strong enough to plan an allocation on", 14,
      eg.plannable,
      `${eg.plannable}% of ${eg.scored.length} records clear the 60 confidence bar; mean ${eg.mean}.${
        eg.weak.length ? ` ${eg.weak.length} below it (weakest ${eg.weak[0].id} at ${eg.weak[0].conf}).` : ""}`,
      eg.weak.length ? `Strengthen ${eg.weak.slice(0,3).map(w=>w.id).join(", ")} — the evidence tab says how.` : null, 75);

    add("G4", "The brief is approved on the version now current", 24,
      st.intakeApproved && st.intakeApproved.version === st.briefVersion,
      st.intakeApproved
        ? (st.intakeApproved.version === st.briefVersion
            ? `Approved on v${st.intakeApproved.version}.`
            : `Approved on v${st.intakeApproved.version} but the brief has re-derived to v${st.briefVersion} — the approval lapsed (T9).`)
        : `Brief v${st.briefVersion} is not approved.`,
      st.intakeApproved ? "Re-approve the current version." : "Approve the brief once the gaps are closed.");

    addA("G5", "Adjudications carry reasons a reader could act on", 14,
      jm.all.length ? jm.mean : 0,
      jm.all.length
        ? `${jm.all.length} recorded, mean argument score ${jm.mean}.${jm.weak.length ? ` ${jm.weak.length} would read thin to P&I.` : ""}`
        : "No adjudication reasons recorded yet.",
      jm.weak.length ? "Strengthen the reasons flagged on the gaps tab — or carry them as they are and P&I will read them." : null, 70);
  }

  if (phase === "discovery"){
    const ranking = c.ranking || [];
    const on = ranking.filter(r => r.on);
    const emptyRegions = FRAME.regions.filter(rg =>
      (FRAME.regionSplit[rg] || 0) > 0 && !on.some(r => r.p.region === rg));
    const breached = on.filter(r => (r.breaches || []).some(b => b.id === "H2" || b.id === "H6"));
    const jm = scoreJustifications(st.rankJust);

    addA("D1", "Every region carrying budget has a product in the list", 22,
      emptyRegions.length === 0 ? 100 : 0,
      emptyRegions.length
        ? `${emptyRegions.join(", ")} has an envelope and nothing to spend it on — the solver will report it unallocated rather than move the money.`
        : "All four regional envelopes have somewhere to go.",
      emptyRegions.length ? `Add a product in ${emptyRegions.join(", ")}, or proceed and let the solve report it.` : null, 100);

    add("D2", "No product in the list carries an unresolved hard breach", 24,
      breached.length === 0,
      breached.length
        ? `${breached.map(r=>r.p.name.split(" — ")[0]).join(", ")} would be held out of the solve rather than shorten the list quietly.`
        : "Every product in the list clears its hard constraints.",
      breached.length ? "Re-target to clear the breach, or take the product out." : null);

    /* Presence of a reason binds; the strength of it does not. */
    const changed = Object.keys(st.rankJust || {});
    const unreasoned = changed.filter(k => !String(st.rankJust[k] || "").trim());
    add("D3", "Every change to the system's order carries a reason", 14,
      unreasoned.length === 0,
      unreasoned.length ? `${unreasoned.length} change${unreasoned.length>1?"s":""} with no reason recorded.`
        : changed.length ? `${changed.length} change${changed.length>1?"s":""}, each with a reason.`
        : "No changes to the system's order.",
      "A change with no reason cannot be read by P&I at all.");

    addA("D3q", "Those reasons hold up to being read cold", 18,
      jm.all.length ? jm.mean : 100,
      jm.all.length
        ? `Mean argument score ${jm.mean} across ${jm.all.length} change${jm.all.length>1?"s":""}.${jm.weak.length ? ` ${jm.weak.length} would read thin.` : ""}`
        : "No changes to the system's order — nothing to defend.",
      jm.weak.length ? `${jm.weak.map(w=>w.key).join(", ")} would benefit from a rewrite. This does not hold the handoff.` : null, 70);

    add("D4", "The ranked list and its targeting are accepted", 24,
      !!st.strategyAccepted,
      st.strategyAccepted ? `Strategy brief v${st.strategyVersion} accepted.` : "The list has not been accepted yet.",
      "Accept the list to open the solve. Acceptance is explicit, not implied by running the solve (D-5).");
  }

  if (phase === "strategize"){
    const res  = c.res || { unallocated:[], dropped:[] };
    const cons = c.cons || [];
    const jm = scoreJustifications(st.justifications);
    const ovr = Object.keys(st.overrides || {});
    const unjust = ovr.filter(k => !(st.justifications || {})[k]);
    const hardFail = cons.filter(x => x.kind === "hard" && !x.ok);

    add("S1", "The optimiser has solved from the accepted list", 18,
      !!st.lastRun || (c.res && c.res.lines && c.res.lines.length),
      st.lastRun ? `Last solved ${st.lastRun}.` : "Not run yet.", "Run the solve.");

    /* Discovery §9: a version cannot be saved while an override is unjustified.
       That is absence, and it binds. Strength is the advisory point below. */
    add("S2", "Every override carries a reason", 20,
      unjust.length === 0,
      ovr.length === 0 ? "No overrides — the optimiser's own answer stands."
        : unjust.length ? `${unjust.length} override${unjust.length>1?"s":""} carrying no reason at all.`
        : `${ovr.length} override${ovr.length>1?"s":""}, each with a reason.`,
      unjust.length ? "Attach a reason to every override." : null);

    addA("S2q", "Those reasons would survive P&I reading them", 16,
      jm.all.length ? jm.mean : 100,
      jm.all.length ? `Mean argument score ${jm.mean}.${jm.weak.length?` ${jm.weak.length} would read thin.`:""}`
        : "No overrides to defend.",
      jm.weak.length ? "Worth a rewrite before P&I sees it. This does not hold the handoff." : null, 70);

    addA("S3", "No regional envelope left unallocated", 16,
      (res.unallocated || []).length === 0 ? 100 : 0,
      (res.unallocated || []).length
        ? `${res.unallocated.map(u=>`${u.region} ${money1(u.amount)}`).join(", ")} has nowhere to go.`
        : "Every envelope is spent where it was budgeted.",
      (res.unallocated || []).length ? "Go back to Discovery and add a product in that region, or carry it forward as a known shortfall." : null, 100);

    add("S4", "No hard constraint breached in the solve", 16,
      hardFail.length === 0,
      hardFail.length ? `${hardFail.map(x=>x.id).join(", ")} breached.` : "All hard constraints clear.",
      hardFail.length ? "A hard constraint is a limit, not a preference — it binds before the solve (OQ-14)." : null);

    add("S5", "At least one version saved", 14,
      (st.versions || []).length > 0,
      `${(st.versions||[]).length} saved.`, "Save a version you would defend.");
  }

  if (phase === "analyze"){
    const vs = st.versions || [];
    const cur = vs.find(v => v.id === st.committed);
    const best = cur || vs[vs.length - 1];
    const jm = best ? scoreJustifications(best.justifications) : { mean:100, weak:[], all:[] };
    const missKpi = best && best.roll.reach3 < FRAME.reachGoal3;

    addA("A1", "More than one version to choose between", 10,
      vs.length >= 2 ? 100 : 0, `${vs.length} version${vs.length===1?"":"s"} saved.`,
      vs.length < 2 ? "A single version is a recommendation, not a choice. Not a blocker." : null, 100);

    add("A2", "One version is committed", 26,
      !!st.committed, st.committed ? `${st.committed} committed.` : "Nothing committed.",
      "Commit the version you would put in front of the client.");

    /* The binding forecast rule: Indicative is a pre-screen, not a number a plan
       may rest on at approval. T5 applied to inventory rather than requirements. */
    const fc = c.forecast || (best ? versionFidelity(best) : null);
    add("A6", "Every line rests on a Constrained forecast, not an Indicative one", 24,
      !best ? false : fc && fc.indicativeLines.length === 0,
      !best ? "No version to check."
        : fc.indicativeLines.length
          ? `${fc.indicativeLines.length} of ${fc.total} line${fc.total===1?"":"s"} still on the daily Indicative pre-screen: ${fc.indicativeLines.slice(0,3).join(", ")}${fc.indicativeLines.length>3?"…":""}.`
          : `All ${fc.total} lines on Constrained avails, run ${fc.runAt}.`,
      "Re-run the solve to replace the pre-screen figures. Indicative is not admissible at approval.");

    addA("A3", "Every rubric dimension clears the threshold this RFP set", 16,
      best ? best.rubric.clear / best.rubric.of * 100 : 0,
      best
        ? `${best.rubric.clear} of ${best.rubric.of} dimensions clear.${best.rubric.below.length
            ? ` Short: ${best.rubric.below.map(b=>`${b.label} ${b.score} against ${b.bar}`).join(", ")}.`
            : ""}`
        : "No version to score.",
      best && best.rubric.below.length
        ? "A version can go forward short on a dimension. P&I reads which one, and by how much."
        : null, 100);

    addA("A4", "Every override in it carries an argument that held", 14,
      jm.all.length ? jm.mean : 100,
      jm.all.length ? `${jm.all.length} override${jm.all.length>1?"s":""}, mean score ${jm.mean}.` : "No overrides to defend.",
      jm.weak.length ? "Strengthen the argument before P&I reads it." : null, 70);

    /* Only assessable once a version is committed — the explanation lives in the
       commit note, which is the thing P&I reads first. */
    const noteEv = st.commitNote ? evalJustification(st.commitNote) : null;
    addA("A5", "A missed KPI is explained, not left to be found", 10,
      !st.committed ? 0 : !missKpi ? 100 : (noteEv ? noteEv.score : 0),
      !st.committed
        ? (missKpi && best ? `3+ reach is ${pct(best.roll.reach3,1)} against a ${pct(FRAME.reachGoal3,0)} goal — the commit note should carry why.`
                           : "Assessed at commit.")
        : !missKpi ? "The stated KPI is met."
        : noteEv ? `Commit note scored ${noteEv.score}.` : "No commit note recorded.",
      !st.committed ? "Say why this version still goes forward when you commit it." : null, 70);
  }

  if (phase === "approval"){
    const v = (st.versions || []).find(x => x.id === st.committed);
    const lines = v ? v.lines : [];
    const dec = st.decisions || {};
    const decided = lines.filter(l => dec[l.pid]);
    const noReason = decided.filter(l => !(dec[l.pid].reason || "").trim());
    const jm = scoreJustifications(Object.fromEntries(
      decided.map(l => [l.pid, dec[l.pid].reason])));

    /* The only real gate in the design (OQ-17). Every line must be decided —
       not every line approved. */
    add("P1", "Every line has a decision", 44,
      lines.length > 0 && decided.length === lines.length,
      `${decided.length} of ${lines.length} decided.`,
      decided.length < lines.length ? `${lines.length - decided.length} line${lines.length-decided.length===1?"":"s"} still open.` : null);

    add("P2", "Every decision carries a reason", 24,
      noReason.length === 0,
      noReason.length ? `${noReason.length} decision${noReason.length>1?"s":""} with no reason recorded.` : "Each decision states its grounds.",
      "A disapproval without a workable reason is not a decision, it is a rejection.");

    addA("P3", "Disapprovals are actionable, not verdicts", 32,
      jm.all.length ? jm.mean : 0,
      jm.all.length ? `Mean reason score ${jm.mean} across ${jm.all.length} decision${jm.all.length>1?"s":""}.` : "No reasons yet.",
      jm.weak.length ? "Say what would make the line approvable, and where the inventory should sit instead." : null, 70);
  }

  const wsum = pt.reduce((s,x) => s + x.w, 0) || 1;
  const score = Math.round(pt.reduce((s,x) => s + x.score * x.w, 0) / wsum);

  /* Only binding points hold the handoff. Advisory shortfalls are surfaced,
     travel into the rubric and the approval package, and are never a veto. */
  const binding  = pt.filter(x => x.kind === "binding");
  const blockers = binding.filter(x => !x.ok);
  const advisory = pt.filter(x => x.kind === "advisory" && !x.ok);

  return {
    phase, score, par: GATE_PAR,
    open: blockers.length === 0,
    points: pt, blockers, advisory, meta: GATE_META[phase] || {},
    /* What the orchestrator does, in its own words. It has three answers and
       none of them is "no". */
    verdict: blockers.length   ? "incomplete"     // something is missing, not weak
           : advisory.length   ? "open-with-notes" // passable, with things P&I will read
           : "clean",
  };
}
