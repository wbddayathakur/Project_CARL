/* =============================================================================
   20-engine.js
   Ranking model, targeting/pricing model, the optimiser, the reach model and
   the good-plan rubric. Everything here is deterministic — same inputs, same
   output — because the optimiser is not negotiated with (T7).
   ============================================================================= */

/* ------------------------------------------------------------------ formatting */
const money = (n, sym="$") => n == null ? "—" : sym + Math.round(n).toLocaleString("en-US");
const money1 = (n, sym="$") => n == null ? "—" : sym + (n/1e6).toFixed(2) + "M";
const num = (n, d=0) => n == null ? "—" : Number(n).toLocaleString("en-US", {minimumFractionDigits:d, maximumFractionDigits:d});
const pct = (n, d=1) => n == null ? "—" : (n*100).toFixed(d) + "%";
const pctn = (n, d=1) => n == null ? "—" : n.toFixed(d) + "%";
const cpmf = (n, sym="$") => n == null ? "—" : sym + Number(n).toFixed(2);
const imps = (k) => k == null ? "—"
  : k >= 1e6 ? (k/1e6).toFixed(2) + "B"
  : k >= 1000 ? (k/1000).toFixed(1) + "M"
  : Math.round(k) + "K";
const clamp = (v,a,b) => Math.max(a, Math.min(b, v));
const uid = (p="id") => p + "-" + Math.random().toString(36).slice(2,8);
const NOW = () => new Date().toISOString().slice(0,16).replace("T"," ");

/* ------------------------------------------------- the brief's planning frame */
const FRAME = {
  demo: "A25-54",
  regions: ["US","EMEA","LATAM","APAC"],
  regionSplit: { US:0.60, EMEA:0.25, LATAM:0.10, APAC:0.05 },   // G01 recommendation
  cpmCeiling: 32,               // E14, hard
  linearCeiling: 0.45,          // E13 ceiling; 0.32 recommended target
  linearTarget: 0.32,
  freqCap: 6,                   // per week, digital (E15)
  viewFloor: 0.80,              // E11, hard for digital video
  pmpCap: 0.12,                 // PI-Q3-03, hard
  hbomaxFloor: 34,              // PI-Q3-07 + learned signal S2
  sportHoldPremium: 0.15,       // PI-Q3-09
  frontLoad: 0.60,              // G02
  reachGoal1: 0.33,             // 1+ reach, share of in-market A25-54 universe
  reachGoal3: 0.20,             // 3+ reach, share of in-market A25-54 universe
};
const INMARKET_UNIVERSE = FRAME.regions.reduce((s,r)=> s + UNIVERSE[r]["A25-54"], 0); // 000s

/* ---------------------------------------------------------- ranking criteria */
const CRITERIA = [
  { k:"audience", label:"Audience fit",     w:0.25, help:"Delivered composition inside A25-54, weighted to the W25-54 skew the brief asks for." },
  { k:"kpi",      label:"KPI relevance",    w:0.25, help:"Does the unit move 1+ reach at 3+ frequency, not just impressions." },
  { k:"avails",   label:"Inventory",        w:0.15, help:"Sellable impressions in the flight against what this region's envelope needs." },
  { k:"price",    label:"Price workability",w:0.20, help:"Workable CPM against the $32 ceiling and the $28.40 the advertiser has been paying." },
  { k:"seller",   label:"Seller position",  w:0.15, help:"WBD's own posture: push, neutral, hold, or yield-dilutive." },
];
const POSTURE_SCORE = { push:92, neutral:58, hold:30, dump:18 };
const POSTURE_LABEL = { push:"Push", neutral:"Neutral", hold:"Held", dump:"Yield-dilutive" };

/* ------------------------------------------------ targeting customisations */
const CUSTOM_OPTIONS = [
  { id:"demoGuar", label:"Demo-guaranteed A25-54", medium:"both",
    desc:"Guarantee delivery inside the demo rather than buying to composition.",
    cpmX:1.18, availX:0.62, compTo:0.94, kpi:+4 },
  { id:"genre", label:"Genre lock — Home & Lifestyle", medium:"Digital",
    desc:"Restrict delivery to home, food and lifestyle content.",
    cpmX:1.12, availX:0.46, compTo:null, kpi:+6 },
  { id:"daypart", label:"Daypart lock — Daytime + Prime", medium:"Linear",
    desc:"Restrict units to daytime and prime; drop overnight and fringe.",
    cpmX:1.15, availX:0.54, compTo:null, kpi:+5 },
  { id:"ugc", label:"Exclude UGC-adjacent placements", medium:"Digital",
    desc:"Drop comment-adjacent and social-embedded placements. Lifts measured viewability.",
    cpmX:1.05, availX:0.78, compTo:null, kpi:+1, viewLift:0.06 },
  { id:"freq", label:"Hard frequency cap 6/wk", medium:"Digital",
    desc:"Enforce the client's stated cap at the ad server rather than in planning.",
    cpmX:1.03, availX:0.87, compTo:null, kpi:+3 },
  { id:"frontload", label:"Front-load weeks 1–8", medium:"both",
    desc:"Weight 60% of impressions into the first eight weeks.",
    cpmX:1.07, availX:0.92, compTo:null, kpi:+4 },
];

function customFor(p){ return CUSTOM_OPTIONS.filter(o => o.medium === "both" || o.medium === p.medium); }

/* Apply a set of customisation ids to a product; returns the live position. */
function applyCustom(p, ids){
  let cpm = p.openCpm, availK = p.availK, comp = p.demoComp, kpi = p.kpiFit, view = p.viewability;
  (ids||[]).forEach(id => {
    const o = CUSTOM_OPTIONS.find(x => x.id === id); if (!o) return;
    cpm *= o.cpmX; availK *= o.availX; kpi += o.kpi;
    if (o.compTo) comp = Math.max(comp, o.compTo);
    if (o.viewLift && view != null) view = Math.min(0.99, view + o.viewLift);
  });
  return { cpm: +cpm.toFixed(2), availK: Math.round(availK), comp:+comp.toFixed(3), kpi: clamp(kpi,0,100),
           view: view == null ? null : +view.toFixed(3), availEstimate: (ids||[]).length > 0 };
}

/* A hard-constraint breach the planner must see at the moment of customisation,
   not at optimisation or at approval (Discovery §5). */
function breachesFor(p, live){
  const out = [];
  if (p.medium === "Digital" && live.view != null && live.view < FRAME.viewFloor)
    out.push({ id:"H2", text:`Viewability ${pct(live.view,0)} is below the ${pct(FRAME.viewFloor,0)} floor the RFP states`,
               fix:"ugc", fixLabel:"Exclude UGC-adjacent placements" });
  if (p.id === "P01" && live.cpm < FRAME.hbomaxFloor)
    out.push({ id:"S1", text:`${cpmf(live.cpm)} is below the ${cpmf(FRAME.hbomaxFloor)} P&I floor`, fix:null });
  if (p.yieldPosture === "hold" && live.cpm < p.floorCpm * (1 + FRAME.sportHoldPremium))
    out.push({ id:"H6", text:`Held inventory: release needs ${cpmf(p.floorCpm*(1+FRAME.sportHoldPremium))} (floor +15%), offered at ${cpmf(live.cpm)}`, fix:null });
  return out;
}

/* --------------------------------------------------------------- the ranking */
/* Five criteria produce the order. Every position carries the reasoning that
   put it there, and that reasoning travels forward (Discovery §3, T5). */
const TYPICAL_LINE_SHARE = 0.30;   // a line is typically ~30% of a regional envelope

function scoreProduct(p, live, signals){
  const regionEnvelope = DEAL.netBudget * (FRAME.regionSplit[p.region] || 0);
  const needK = regionEnvelope * TYPICAL_LINE_SHARE / Math.max(live.cpm, 0.01);
  const coverage = clamp(live.availK / Math.max(needK, 1), 0, 2);
  const bench = (BENCH[p.region + "|" + p.medium] || {cpm:live.cpm}).cpm;

  const audience = clamp((live.comp - 0.40) / 0.55 * 100, 0, 100);
  const kpi      = clamp(live.kpi, 0, 100);
  const avails   = clamp(coverage * 62, 0, 100);
  let   price    = clamp(62 + (bench - live.cpm) / bench * 55, 0, 100);
  if (p.medium === "Digital" && live.cpm > FRAME.cpmCeiling) price = clamp(price - 9, 0, 100);
  let   seller   = POSTURE_SCORE[p.yieldPosture] ?? 50;

  /* learned signals reweight, visibly */
  const applied = [];
  (signals||[]).forEach(s => {
    if (!s.on) return;
    if (s.id === "S1" && p.id === "P08") { seller = Math.min(seller, 14); applied.push(s.id); }
    if (s.id === "S3" && /sport/i.test(p.format + p.placement + p.brandSafe)) { seller = Math.min(seller, 22); applied.push(s.id); }
  });

  const parts = { audience, kpi, avails, price, seller };
  const total = CRITERIA.reduce((s,c) => s + parts[c.k] * c.w, 0);

  const why = {
    audience: `${pct(live.comp,0)} of delivery lands in ${FRAME.demo}${live.comp >= 0.70 ? " — top quartile of the eligible set" : live.comp < 0.55 ? " — below the 0.55 the brief's skew needs" : ""}.`,
    kpi: `${p.medium === "Digital" && p.vcr ? `${pct(p.vcr,1)} completion, ${pct(p.viewability,0)} viewable, attention index ${p.attention}` : `attention index ${p.attention}${p.grp ? `, ${p.grp} GRPs available` : ""}`}. Incremental-reach ceiling ${imps(p.reachK)}.`,
    avails: `${imps(live.availK)} sellable in flight against ${imps(needK)} a typical ${p.region} line would need at ${cpmf(live.cpm)} — ${coverage >= 1 ? "covers a full line" : `covers ${pct(coverage,0)} of one`}.${live.availEstimate ? " Estimate only: targeting is customised, firm avails return with the solve." : ""}`,
    price: `${cpmf(live.cpm)} against a ${cpmf(bench)} market benchmark for ${p.region} ${p.medium.toLowerCase()} (${(BENCH[p.region+"|"+p.medium]||{}).note||""}). Floor ${cpmf(p.floorCpm)}, card ${cpmf(p.cardCpm)}. Blended ceiling ${cpmf(FRAME.cpmCeiling)}.`,
    seller: `${POSTURE_LABEL[p.yieldPosture]}. ${p.note}`,
  };
  return { parts, total:+total.toFixed(1), why, live, needK, coverage, appliedSignals: applied };
}

function buildRanking(customMap, signals){
  /* Discovery ranks on the Indicative pre-screen. A product with no Indicative
     inventory across the flight is not eligible in fact, only in principle, and
     never reaches the list at all (Forecast §1). */
  const rows = PRODUCTS.filter(p => indicativeFor(p).eligible).map(p => {
    const ids = customMap[p.id] || [];
    const live = applyCustom(p, ids);
    const s = scoreProduct(p, live, signals);
    return { pid:p.id, p, custom:ids, breaches: breachesFor(p, live),
             /* Direction of travel, not a figure — see 28-forecast.js. */
             availSignal: customisationSignal(p, ids, live), ...s };
  });
  rows.sort((a,b) => b.total - a.total);
  rows.forEach((r,i) => { r.sysRank = i + 1; });
  return rows;
}

/* ------------------------------------------------------------ constraint set */
function constraintSet(){
  return [
    { id:"H1", kind:"hard", label:`Blended digital CPM ≤ ${cpmf(FRAME.cpmCeiling)}`, from:"E14 · clarified by client" },
    { id:"H2", kind:"hard", label:`Digital video viewability ≥ ${pct(FRAME.viewFloor,0)}`, from:"E11 · stated in RFP" },
    { id:"H3", kind:"hard", label:`Curated PMP ≤ ${pct(FRAME.pmpCap,0)} of plan`, from:"PI-Q3-03 · P&I position" },
    { id:"H4", kind:"hard", label:`Linear ≤ ${pct(FRAME.linearCeiling,0)} of plan`, from:"E13 · clarified ceiling" },
    { id:"H5", kind:"hard", label:"No hard-news adjacency", from:"E09 · stated in RFP" },
    { id:"S1", kind:"soft", label:`HBO Max premium CTV ≥ ${cpmf(FRAME.hbomaxFloor)} floor`, from:"PI-Q3-07 · P&I, hardened by learned signal S2" },
    { id:"S2", kind:"soft", label:"Carry discovery+ US and HBO Max LATAM meaningfully", from:"PI-Q3-11 · P&I push list" },
    { id:"S3", kind:"soft", label:`Linear at ${pct(FRAME.linearTarget,0)} target, headroom to ${pct(FRAME.linearCeiling,0)}`, from:"C01 adjudication" },
    { id:"S4", kind:"soft", label:`Front-load ${pct(FRAME.frontLoad,0)} into weeks 1–8`, from:"G02 · cohort recommendation" },
    { id:"S5", kind:"soft", label:"Sport ranked last unless the client reopens it", from:"Learned signal S3 · PL-8841 rejection" },
  ];
}

/* ------------------------------------------------------------- the optimiser */
/* Rank-preference waterfall inside each regional envelope, capped by avails,
   floors, and the hard constraint set. Preference decays with rank; it does not
   pre-commit spend (Discovery §3). */
function optimise(ranked, opts){
  const o = Object.assign({ lambda:0.42, overrides:{}, locked:{}, buyCap:0.80 }, opts || {});
  const lines = [];
  const dropped = [];
  const unallocated = [];

  /* A product carrying an unresolved hard breach cannot enter the solve.
     The solver reports it rather than quietly shortening the list. */
  const selected = ranked.filter(r => {
    if (r.on === false) return false;
    const hard = (r.breaches || []).filter(b => b.id === "H2" || b.id === "H6");
    if (hard.length){
      dropped.push({ pid:r.pid, name:r.p.name, reason: hard.map(h=>h.text).join("; "),
                     fix: hard.find(h=>h.fix)?.fixLabel || null });
      return false;
    }
    return true;
  });

  /* Sending the accepted list to the optimiser is what triggers the Constrained
     run. Until this moment every avails figure on the deal is the Indicative
     pre-screen; from here each line has its own waterfall derivation, its own
     UMP placement ID, and a run date that travels with it as provenance.
     The solve allocates against Constrained avails, not against the pre-screen. */
  const runAt = NOW();
  const fc = {};
  selected.forEach(r => { fc[r.pid] = constrainedFor(r.p, r.custom, runAt); });
  const conK = r => (fc[r.pid] ? fc[r.pid].availK : r.live.availK);

  FRAME.regions.forEach(region => {
    const envelope = DEAL.netBudget * FRAME.regionSplit[region];
    const all = selected.filter(r => r.p.region === region);
    if (!all.length){
      unallocated.push({ region, amount: envelope,
        why: `No ${region} product is in the accepted list. The envelope has nowhere to go — add a ${region} product in Discovery or re-cut the regional split.` });
      return;
    }

    /* Fixed values enter the solve as constraints, not as suggestions: a justified
       planner override, or a line P&I has already approved (T7). */
    const fixed = all.filter(r => o.locked[r.pid] != null || o.overrides[r.pid] != null);
    const pool  = all.filter(r => o.locked[r.pid] == null && o.overrides[r.pid] == null);
    let fixedSpend = 0;
    fixed.forEach(r => {
      const spend = o.locked[r.pid] != null ? o.locked[r.pid] : o.overrides[r.pid];
      fixedSpend += spend;
      if (spend < 1) return;
      const impsK = spend / r.live.cpm;
      lines.push({ pid:r.pid, p:r.p, region, rank: all.indexOf(r)+1, cpm:r.live.cpm, spend, impsK,
        custom:r.custom, comp:r.live.comp, availK: conK(r), view:r.live.view,
        availUse: impsK / conK(r),
        ...forecastOn(fc[r.pid], r.p),
        overridden: o.overrides[r.pid] != null, locked: o.locked[r.pid] != null,
        systemSpend: (o.systemSpend || {})[r.pid] });
    });
    if (!pool.length){
      const left = envelope - fixedSpend;
      if (Math.abs(left) > 5000) unallocated.push({ region, amount:left,
        why: left > 0 ? `Every ${region} line is fixed by an override or a P&I approval, and they do not add up to the envelope.`
                      : `Fixed ${region} lines exceed the envelope by ${money(-left)}.` });
      return;
    }

    /* preference weight by position in the accepted order */
    const weights = pool.map((r,i) => Math.exp(-o.lambda * i) * (0.55 + r.total / 220));

    /* first pass: proportional, then clip to avails, redistribute the remainder */
    let remaining = Math.max(0, envelope - fixedSpend);
    const alloc = pool.map(()=>0);
    for (let pass = 0; pass < 4 && remaining > 1000; pass++){
      const active = pool.map((r,i) => alloc[i] < conK(r) * r.live.cpm * o.buyCap);
      const aw = weights.map((w,i)=> active[i] ? w : 0);
      const asum = aw.reduce((a,b)=>a+b,0);
      if (asum <= 0) break;
      let spent = 0;
      pool.forEach((r,i) => {
        if (!active[i]) return;
        const cap = conK(r) * r.live.cpm * o.buyCap - alloc[i];   // never buy past 80% of constrained avails
        const want = remaining * (aw[i]/asum);
        const take = Math.max(0, Math.min(cap, want));
        alloc[i] += take; spent += take;
      });
      remaining -= spent;
      if (spent < 1000) break;
    }
    if (remaining > 5000) unallocated.push({ region, amount: remaining,
      why: `Every accepted ${region} product hit its avails ceiling at ${pct(o.buyCap,0)} of constrained inventory. More budget needs more products, not more weight.` });

    pool.forEach((r,i) => {
      const spend = alloc[i];
      if (spend < 1) return;
      const impsK = spend / r.live.cpm;
      lines.push({
        pid: r.pid, p: r.p, region, rank: all.indexOf(r) + 1, cpm: r.live.cpm, spend, impsK,
        custom: r.custom, comp: r.live.comp, availK: conK(r), view: r.live.view,
        availUse: impsK / conK(r),
        ...forecastOn(fc[r.pid], r.p),
        overridden: false, locked: false,
        systemSpend: (o.systemSpend || {})[r.pid] != null ? o.systemSpend[r.pid] : spend,
      });
    });
  });

  lines.sort((a,b) => b.spend - a.spend);
  return { lines, dropped, unallocated, ...rollup(lines) };
}

/* ----------------------------------------------------------- the reach model */
/* Per-product saturation curve, then sequential incremental reach with a
   duplication penalty for same-brand and same-medium overlap. A model, and
   labelled as one wherever it is shown. */
function rollup(lines){
  const spend = lines.reduce((s,l)=>s+l.spend,0);
  const impsK = lines.reduce((s,l)=>s+l.impsK,0);
  const targetImpsK = lines.reduce((s,l)=>s+l.impsK*l.comp,0);
  const digital = lines.filter(l=>l.p.medium==="Digital");
  const linear  = lines.filter(l=>l.p.medium==="Linear");
  const digSpend = digital.reduce((s,l)=>s+l.spend,0);
  const linSpend = linear.reduce((s,l)=>s+l.spend,0);
  const digImpsK = digital.reduce((s,l)=>s+l.impsK,0);

  const curve = lines.map(l => {
    const ceil = l.p.reachK;
    const r = ceil * (1 - Math.exp(-l.impsK / (ceil * 2.2)));
    return { ...l, reachK: r };
  }).sort((a,b)=> b.reachK - a.reachK);

  const seenBrand = new Set(), seenMedReg = new Set();
  let reachedK = 0;
  const universe = INMARKET_UNIVERSE;
  curve.forEach(l => {
    let dup = 0;
    if (seenBrand.has(l.p.brand)) dup = 0.34;
    else if (seenMedReg.has(l.p.medium + l.region)) dup = 0.14;
    seenBrand.add(l.p.brand); seenMedReg.add(l.p.medium + l.region);
    const inc = l.reachK * (1 - reachedK / universe) * (1 - dup);
    l.incReachK = inc;
    reachedK += inc;
  });

  const reach1 = reachedK / universe;
  const avgFreq = reachedK > 0 ? (targetImpsK / reachedK) : 0;
  const share3 = avgFreq <= 1 ? 0 : 1 - Math.exp(-0.32 * (avgFreq - 1));
  const reach3 = reach1 * share3;
  const blendedCpm = impsK > 0 ? spend / impsK : 0;
  const digCpm = digImpsK > 0 ? digSpend / digImpsK : 0;
  const cpReachPt = reach1 > 0 ? spend / (reach1 * 100) : 0;

  /* concentration (HHI over spend) */
  const hhi = spend > 0 ? lines.reduce((s,l)=> s + Math.pow(l.spend/spend, 2), 0) : 1;
  const byRegion = {}; FRAME.regions.forEach(r => { byRegion[r] = lines.filter(l=>l.region===r).reduce((s,l)=>s+l.spend,0); });

  return { byRegion,
    spend, impsK, targetImpsK, digSpend, linSpend, digImpsK,
    linearPct: spend>0 ? linSpend/spend : 0,
    pmpPct: spend>0 ? (lines.filter(l=>l.pid==="P08").reduce((s,l)=>s+l.spend,0))/spend : 0,
    reachedK, reach1, reach3, avgFreq, blendedCpm, digCpm, cpReachPt, hhi,
    curve,
  };
}

/* --------------------------------------------------------- constraint report */
function checkConstraints(res, ranked){
  const out = [];
  const push = (id,label,ok,detail,kind) => out.push({id,label,ok,detail,kind});
  push("H1", `Blended digital CPM ≤ ${cpmf(FRAME.cpmCeiling)}`, res.digCpm <= FRAME.cpmCeiling,
    `Solved at ${cpmf(res.digCpm)}.`, "hard");
  const badView = res.lines.filter(l => l.p.medium==="Digital" && l.view != null && l.view < FRAME.viewFloor);
  push("H2", `Digital video viewability ≥ ${pct(FRAME.viewFloor,0)}`, badView.length === 0,
    badView.length ? `${badView.length} line(s) below floor: ${badView.map(l=>l.p.name.split(" — ")[0]).join(", ")}.`
      : (res.dropped||[]).length ? `All lines in the solve clear the floor. ${res.dropped.length} product held out of the solve — see below.`
      : "All digital video lines clear the floor.", "hard");
  push("H3", `Curated PMP ≤ ${pct(FRAME.pmpCap,0)}`, res.pmpPct <= FRAME.pmpCap + 1e-6,
    `PMP at ${pct(res.pmpPct,1)} of plan.`, "hard");
  push("H4", `Linear ≤ ${pct(FRAME.linearCeiling,0)}`, res.linearPct <= FRAME.linearCeiling + 1e-6,
    `Linear at ${pct(res.linearPct,1)} of plan (target ${pct(FRAME.linearTarget,0)}).`, "hard");
  const hbo = res.lines.find(l => l.pid === "P01");
  push("S1", `HBO Max premium CTV ≥ ${cpmf(FRAME.hbomaxFloor)}`, !hbo || hbo.cpm >= FRAME.hbomaxFloor,
    hbo ? `Carried at ${cpmf(hbo.cpm)}.` : "Not in the plan.", "soft");
  const pushSpend = res.lines.filter(l=>["P03","P19"].includes(l.pid)).reduce((s,l)=>s+l.spend,0);
  push("S2", "P&I push list carried meaningfully", pushSpend / Math.max(res.spend,1) >= 0.10,
    `discovery+ US and HBO Max LATAM at ${pct(pushSpend/Math.max(res.spend,1),1)} of plan.`, "soft");
  const over = res.lines.filter(l => l.availUse > 0.85);
  push("S6", "No line above 85% of its sellable avails", over.length === 0,
    over.length ? `${over.length} line(s) at risk: ${over.map(l=>`${l.p.name.split(" — ")[0]} ${pct(l.availUse,0)}`).join(", ")}.` : "Every line sits inside a deliverable share of avails.", "soft");
  return out;
}

/* ------------------------------------------------------- the good-plan rubric */
/* [PROPOSED] — OQ-2 is open. The shape is settled, the content is not.
   Scored in isolation, never ranked against other versions (Analyze §9). */
/* The definition of a good plan has two layers (OQ-2).

   The standing layer is WBD's, agreed once rather than per deal: these are the
   dimensions a plan is judged on at all. The per-RFP layer is the weights and
   thresholds below, instantiated for this brief.

   The dimensions are scored separately and deliberately not collapsed into one
   number, so the trade-off between them stays visible. A version that buys
   objective delivery by abandoning yield alignment should look different from
   one that is merely average everywhere, and a single total hides exactly that.

   [OPEN] The dimensions here are candidates. Whether they are the right ones,
   how each is measured, and who sets the per-RFP weights are all with the
   business. */
const RUBRIC = [
  { k:"coverage", label:"Requirement coverage", w:0.20, bar:80, help:"Stated requirements this version satisfies." },
  { k:"objective",label:"KPI service",          w:0.22, bar:85, help:"1+ and 3+ reach against the goal the brief set." },
  { k:"price",    label:"Efficiency",           w:0.15, bar:70, help:"Blended CPM against the ceiling and the advertiser's paid benchmark." },
  { k:"yield",    label:"Seller alignment",     w:0.16, bar:75, help:"Agreement with P&I's stated position, floors and caps." },
  { k:"argument", label:"Argument quality",     w:0.15, bar:70, help:"Every deviation from the system proposal carries a reason that would survive a question." },
  { k:"realism",  label:"Deliverability",       w:0.12, bar:75, help:"Deliverability against constrained avails and concentration risk." },
];

function scorePlan(res, ranked, overrides, justifications, constraints){
  const coverageItems = [
    { t:"Flight and markets as stated", ok:true },
    { t:`Demo ${FRAME.demo} with W25-54 skew`, ok: res.targetImpsK / Math.max(res.impsK,1) >= 0.62,
      d:`${pct(res.targetImpsK/Math.max(res.impsK,1),0)} of delivery in demo.` },
    { t:"No hard-news adjacency", ok:true, d:"CNN products excluded at eligibility." },
    { t:"Do-not-air list applied", ok:true, d:"41 titles; Adult Swim excluded at network level." },
    { t:`Viewability ≥ ${pct(FRAME.viewFloor,0)}`, ok: constraints.find(c=>c.id==="H2")?.ok, },
    { t:`Frequency cap ${FRAME.freqCap}/wk`, ok: res.avgFreq <= 14, d:`Modelled average frequency ${res.avgFreq.toFixed(1)} across the flight.` },
    { t:"Creative variants deliverable", ok:true },
    { t:"Dual measurement currency", ok:false, d:"VideoAmp not yet confirmed for LATAM lines — C03 open." },
  ];
  const coverage = coverageItems.filter(i=>i.ok).length / coverageItems.length * 100;

  const o1 = clamp(res.reach1 / FRAME.reachGoal1, 0, 1.15) * 100;
  const o3 = clamp(res.reach3 / FRAME.reachGoal3, 0, 1.15) * 100;
  const objective = clamp(o1 * 0.4 + o3 * 0.6, 0, 100);

  const price = clamp(60 + (FRAME.cpmCeiling - res.digCpm) / FRAME.cpmCeiling * 130, 0, 100);

  const hardFails = constraints.filter(c=>c.kind==="hard" && !c.ok).length;
  const softFails = constraints.filter(c=>c.kind==="soft" && !c.ok).length;
  const yieldScore = clamp(100 - hardFails * 34 - softFails * 12, 0, 100);

  const devs = Object.keys(overrides || {});
  const withReason = devs.filter(k => (justifications[k]||"").trim().length >= 25);
  const argument = devs.length === 0 ? 84
    : clamp((withReason.length / devs.length) * 100 - (devs.length > 6 ? 8 : 0), 0, 100);

  const overAvails = res.lines.filter(l=>l.availUse > 0.85).length;
  const realism = clamp(100 - overAvails * 18 - Math.max(0, (res.hhi - 0.16)) * 260, 0, 100);

  const parts = { coverage, objective, price, yield:yieldScore, argument, realism };

  /* The profile, not a verdict. Which dimensions clear the threshold this RFP
     set, and which do not — that is the readable answer. `total` is retained
     only as a weak sort key for the version list; nothing decides on it. */
  const below = RUBRIC.filter(r => parts[r.k] < r.bar)
    .map(r => ({ ...r, score: +parts[r.k].toFixed(1), short: +(r.bar - parts[r.k]).toFixed(1) }))
    .sort((a,b) => b.short - a.short);
  const total = RUBRIC.reduce((s,r) => s + parts[r.k] * r.w, 0);

  return { parts, below, clear: RUBRIC.length - below.length, of: RUBRIC.length,
           total:+total.toFixed(1), coverageItems, devs: devs.length, withReason: withReason.length };
}

/* ------------------------------------------------------------ P&I line review */
function inventoryImpact(line){
  const supply = SUPPLY.find(s => s.region === line.region && s.medium === line.p.medium) || {selloutPct:50};
  const share = line.availUse;
  const after = clamp(supply.selloutPct + share * (100 - supply.selloutPct) * 0.55, 0, 100);
  const vsFloor = (line.cpm - line.p.floorCpm) / line.p.floorCpm;
  return {
    selloutBefore: supply.selloutPct, selloutAfter: +after.toFixed(1),
    availUse: share, vsFloor,
    yield: vsFloor >= 0.25 ? "accretive" : vsFloor >= 0.05 ? "at position" : vsFloor >= 0 ? "thin" : "below floor",
  };
}

/* Which stated P&I position each line touches — so P&I reads the plan against
   a position they already stated, rather than reacting to it cold. */
function positionsFor(pid){ return PI_POSITION.filter(p => p.appliesTo.includes(pid)); }
