/* =============================================================================
   28-forecast.js — the forecast boundary between UMP and the Allocation Engine.

   Forecast data reaches planning in two fidelity classes. They are not high and
   low quality versions of one number. They are different answers to different
   questions, asked at different moments:

     Indicative   Does enough inventory exist for this product across this
                  flight to be worth putting in front of the planner at all?
                  Product level, no targeting, pre-computed daily, read
                  instantly. It powers the eligibility list and nothing else.

     Constrained  What will this specific line, with this specific targeting,
                  actually deliver? Line level, full waterfall, computed on
                  demand when the optimiser runs. This is what the plan rests
                  on and what the client eventually sees.

   The binding rule that connects them: a plan version cannot be committed for
   approval while any line still rests on an Indicative figure. That is T5
   applied to inventory rather than to advertiser requirements — an inferred
   value is a proposal and must be confirmed before approval. It is what lets
   Discovery be fast and approximate without making the approval package
   indefensible.

   The consequence the UX has to carry: between those two moments, the planner
   customises targeting and gets no number back. Precise availability at a
   specific customisation does not exist until the solver runs (D-8). What they
   get instead is a constraint flag and a direction of travel.
   ============================================================================= */

const FIDELITY = {
  indicative: {
    id:"indicative", label:"Indicative", short:"IND", tone:"a",
    what:"Product-level pre-screen. This RFP's targeting is not applied.",
    granularity:"Product or package",
    targeting:"None — standing pressure only",
    computed:"Daily, pre-computed. Read immediately, no run required.",
    carriedBy:"The strategy brief, as the inventory position per eligibility entry.",
    admissible:"Eligibility and ranked order in Discovery only.",
    notAdmissible:"Any plan version submitted for approval.",
  },
  constrained: {
    id:"constrained", label:"Constrained", short:"CON", tone:"g",
    what:"Line-level forecast against this RFP's actual targeting.",
    granularity:"Line item, per UMP placement ID",
    targeting:"Full waterfall — TMR, AMR, ABR, FCR",
    computed:"On demand, asynchronously, when the accepted list goes to the optimiser.",
    carriedBy:"The plan version brief.",
    admissible:"Allocation, Analyze, and anything going to approval.",
    notAdmissible:"Nothing — this is the defensible class.",
  },
};

/* The Indicative pre-screen is recomputed overnight; the read is instant but the
   figure is as-at the last nightly pass, which is why it carries a date. */
const INDICATIVE_RUN = "2026-09-22 03:15";

/* Below this, a product has too little inventory across the flight to be worth
   surfacing at all — it never reaches the eligibility list (Forecast §1). */
const INDICATIVE_FLOOR_K = 40000;

/* Maximum age of a Constrained run before P&I is advised to ask for a fresh one.
   [OPEN] The real threshold is P&I's to set, against how fast inventory moves. */
const STALE_HOURS = 24;

/* -------------------------------------------------------- UMP placement IDs */
/* UMP generates the line identifier and the Allocation Engine accepts it,
   without an Operative One deal needing to exist first (dependency DDF-1251).
   The ID carries product, flight and targeting, so two lines differing only in
   customisation are two different forecast questions. */
function umpPlacementId(p, customIds){
  const t = (customIds || []).slice().sort().join("+");
  const h = t ? t.split("").reduce((a,c)=> (a*31 + c.charCodeAt(0)) >>> 0, 7).toString(36).slice(0,3).toUpperCase() : "BSE";
  return `UMP-${p.id}-${h}`;
}

/* --------------------------------------------------------- the ten-step waterfall */
/* The Allocation Engine's own model, reused rather than duplicated. Every
   Constrained figure is explained by it, and the run date travels with the
   derivation as provenance — the same line reading 15% on one date and 10.7% on
   another is not a contradiction, it is the system behaving correctly (§9). */
const WATERFALL_STEPS = [
  { k:"capacity",  label:"Total digital inventory capacity",
    note:"Raw FreeWheel impressions for the site and period, before any constraint. Sourced from the VW_CAPACITY nightly pipeline." },
  { k:"pressure",  label:"Initial pressure cap",
    note:"Less inventory not open to this sale — programmatic PMP reserved auction, non-AD direct, and PNG." },
  { k:"higherOv",  label:"HIGHER_OV_COMPETITION",
    note:"Impressions lost to prior days and to higher-OV placements." },
  { k:"sameOv",    label:"SAME_OV_COMPETITION",
    note:"Lost to placements at the same override value but higher combined priority index (CPI = OSI + LSI + TI)." },
  { k:"afterComp", label:"After competition", divider:true,
    note:"What remains once both competition steps have been applied." },
  { k:"tmr",       label:"After_TMR — target match rate",
    note:"The share of remaining inventory matching the line's content targeting. Gold MR pipeline, with brand and portfolio fallbacks." },
  { k:"amr",       label:"After_AMR — audience match rate",
    note:"The share matching the audience segments, over the AND/OR combination tree against 14-day trailing tracked audience data." },
  { k:"abr",       label:"After_ABR — ad-break ratio",
    note:"A structural 1/N limit on how many slots in one break a single line may take. Derived from 7–14 day trailing slot data. Non-relaxing." },
  { k:"fcr",       label:"After_FCR — frequency cap ratio",
    note:"Reduces for the per-user exposure ceiling on the line." },
  { k:"net",       label:"Net constrained avails", divider:true, strong:true,
    note:"The net available impressions returned to the requester." },
];

/* Deterministic per product and targeting set, so the same line always derives
   the same way — a forecast the planner cannot reproduce is not evidence. */
function seeded(str){
  let h = 2166136261;
  for (let i=0;i<str.length;i++){ h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
  return () => { h = Math.imul(h ^ (h>>>15), 2246822507); return ((h>>>0) % 1000) / 1000; };
}

/* Run the waterfall for one line. `p` is the product, `customIds` the targeting
   customisations the planner applied. Returns every step so the derivation can
   be read, not just the answer. */
function runWaterfall(p, customIds, runAt){
  const pid = umpPlacementId(p, customIds);
  const rnd = seeded(pid);
  const ids = customIds || [];

  /* Indicative sits at product level with no targeting, so it is the closest
     thing to raw capacity this model has. The waterfall starts above it. */
  const capacity = Math.round(p.availK / 0.42);
  const rows = [];
  let v = capacity;
  const step = (k, ratio) => {
    const before = v; v = Math.round(v * ratio);
    rows.push({ ...WATERFALL_STEPS.find(s=>s.k===k), value:v, lost:before - v, ratio });
    return v;
  };

  rows.push({ ...WATERFALL_STEPS[0], value:capacity, lost:0, ratio:1 });
  step("pressure",  0.88 - rnd()*0.06);
  step("higherOv",  0.94 - rnd()*0.07);
  step("sameOv",    0.96 - rnd()*0.05);
  rows.push({ ...WATERFALL_STEPS[4], value:v, lost:0, ratio:1 });

  /* Targeting customisations bite here, which is exactly why a customised
     figure cannot be known before this runs. */
  const cs = ids.map(id => CUSTOM_OPTIONS.find(o=>o.id===id)).filter(Boolean);
  const tmrX = cs.filter(o=>["genre","daypart","ugc"].includes(o.id)).reduce((a,o)=>a*o.availX, 0.86 - rnd()*0.08);
  const amrX = cs.filter(o=>["demoGuar"].includes(o.id)).reduce((a,o)=>a*o.availX, 0.79 - rnd()*0.10);
  const fcrX = cs.filter(o=>["freq"].includes(o.id)).reduce((a,o)=>a*o.availX, 0.93 - rnd()*0.05);

  step("tmr", clamp(tmrX, 0.05, 1));
  step("amr", clamp(amrX, 0.05, 1));
  step("abr", 0.91 - rnd()*0.06);
  step("fcr", clamp(fcrX, 0.05, 1));
  rows.push({ ...WATERFALL_STEPS[9], value:v, lost:0, ratio:1 });

  return { pid, runAt: runAt || NOW(), capacityK: capacity, netK: v, rows,
           reductionPct: 1 - v / capacity };
}

/* ------------------------------------------------------- the two read paths */
/* Indicative: no run, no targeting, read straight off the nightly pass. */
function indicativeFor(p){
  return { fidelity:"indicative", pid:null, availK:p.availK, runAt:INDICATIVE_RUN,
           eligible: p.availK >= INDICATIVE_FLOOR_K };
}

/* Constrained: the answer only the solver pass can give. */
function constrainedFor(p, customIds, runAt){
  const w = runWaterfall(p, customIds, runAt);
  return { fidelity:"constrained", pid:w.pid, availK:w.netK, runAt:w.runAt, waterfall:w };
}

/* What the planner gets at the moment of customisation: not a figure. A flag,
   a direction, and the Indicative still visible as the reference point (§7).
   Recording the direction alongside the pricing consequence is what makes the
   trade-off readable downstream rather than only its result. */
function customisationSignal(p, customIds, live){
  const ids = customIds || [];
  if (!ids.length) return null;
  const x = ids.reduce((a,id) => {
    const o = CUSTOM_OPTIONS.find(c=>c.id===id); return o ? a * o.availX : a;
  }, 1);
  const dir = x < 0.97 ? "down" : x > 1.03 ? "up" : "flat";
  const severity = x < 0.55 ? "sharp" : x < 0.8 ? "material" : "slight";
  return {
    direction: dir, severity,
    /* Deliberately not a number. The honest answer is that nobody knows yet. */
    text: dir === "flat"
      ? "No material change to available inventory."
      : `Available inventory moves ${dir} ${severity === "sharp" ? "sharply" : severity === "material" ? "materially" : "slightly"} against the pre-screen.`,
    reference: p.availK,
    priced: live ? live.cpm : null,
    why: "The size of the move is not knowable until the optimiser runs this line through the waterfall against your targeting.",
  };
}

/* The fidelity fields a solved line carries. They travel into the saved plan
   version, which is how the Analyze gate can tell whether anything still rests
   on the pre-screen, and how P&I can read the run date at approval. */
function forecastOn(c, p){
  if (!c) return { fidelity:"indicative", umpPid:null, forecastRunAt:null,
                   indicativeK: p.availK, constrainedK:null, waterfall:null };
  return {
    fidelity: "constrained",
    umpPid: c.pid,
    forecastRunAt: c.runAt,
    indicativeK: p.availK,
    constrainedK: c.availK,
    waterfall: c.waterfall,
  };
}

/* --------------------------------------------------- reserved and available */
/* The Allocation Engine excludes reserved inventory before it returns anything,
   and never breaks it out. Planners consequently never see a pressure figure.
   P&I sees the combined reserved total at approval, and only there (§8).

   Reserved is booked (signed IO, from COMS) plus COMS-pressured (deals past
   advertiser approval at 80%+ sell-through). Plans still inside UMP contribute
   nothing — they have not reached COMS. */
function reservedFor(p){
  const rnd = seeded("res-" + p.id);
  const capacity = Math.round(p.availK / 0.42);
  const booked    = Math.round(capacity * (0.34 + rnd()*0.26));
  const pressured = Math.round(capacity * (0.08 + rnd()*0.12));
  return { capacityK:capacity, bookedK:booked, pressuredK:pressured,
           reservedK: booked + pressured,
           sellThrough: (booked + pressured) / capacity };
}

/* Competing in-flight UMP demand against the same product. P&I asked for this
   so they can see the whole picture before deciding, rather than this plan's
   draw in isolation.
   NOTE: not current functionality — the Allocation Engine does not identify
   competing UMP plan demand today. Carried here as the stated requirement. */
function competingUmpDemand(p){
  const rnd = seeded("comp-" + p.id);
  const n = Math.floor(rnd() * 3);            // 0–2 other plans
  if (!n) return { plans:[], askK:0, modelled:true };
  const plans = Array.from({length:n}, (_,i) => ({
    ref: `UMP-${String(2100 + Math.floor(rnd()*880)).slice(0,4)}`,
    advertiser: ["Nestlé Purina","Samsung Mobile","Capital One","Toyota NA","Booking.com"][Math.floor(rnd()*5)],
    askK: Math.round(p.availK * (0.03 + rnd()*0.09)),
  }));
  return { plans, askK: plans.reduce((s,x)=>s+x.askK,0), modelled:true };
}

/* ------------------------------------------------------- staleness and lineage */
function hoursSince(ts){
  if (!ts) return Infinity;
  const t = Date.parse(String(ts).replace(" ", "T") + ":00");
  return isNaN(t) ? 0 : Math.max(0, (Date.now() - t) / 36e5);
}

function staleness(runAt){
  const h = hoursSince(runAt);
  return { hours:h, stale: h > STALE_HOURS, threshold:STALE_HOURS,
           label: h < 1 ? "just now" : h < 24 ? `${Math.round(h)}h ago` : `${Math.round(h/24)}d ago` };
}

/* Which class every line in a saved version rests on. The Analyze gate's one
   binding forecast point reads this. */
function versionFidelity(v){
  const lines = (v && v.lines) || [];
  const ind = lines.filter(l => (l.fidelity || "indicative") !== "constrained");
  const runs = lines.map(l => l.forecastRunAt).filter(Boolean).sort();
  return {
    total: lines.length,
    indicativeLines: ind.map(l => l.pid || (l.p && l.p.id) || "line"),
    constrainedLines: lines.length - ind.length,
    runAt: runs[0] || null,
    stale: runs.length ? staleness(runs[0]).stale : false,
  };
}
