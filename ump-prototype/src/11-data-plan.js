/* =============================================================================
   11-data-plan.js
   The anchored sample deal, its evidence store, and the seller position.
   One genuinely-shaped scenario, synthetic in detail (Fast Prototyping §Data).
   ============================================================================= */

const DEAL = {
  id: "OPP-2026-04872",
  plan: "Tide — Global Summer Refresh 2026",
  advertiser: "Procter & Gamble",
  brand: "Tide / Ariel",
  agency: "Publicis (Starcom)",
  ae: "Marcus Vieira",
  planner: "You (Sales Planner)",
  pi: "Rachel Levine (P&I)",
  industry: "Consumer Products",
  category: "Home Care / Laundry",
  dealType: "Upfront",
  channel: "Unified",
  grossBudget: 18_500_000,
  agencyCommissionPct: 0.15,
  createdAt: "2026-05-04",
};
DEAL.netBudget = Math.round(DEAL.grossBudget * (1 - DEAL.agencyCommissionPct));

/* Provenance ladder — strongest to weakest (baseline doc, Objects & vocabulary) */
const PROV = {
  stated:    { k:"stated",    label:"Stated in RFP",        short:"STATED",    cls:"b", rank:1 },
  clarified: { k:"clarified", label:"Clarified by client",  short:"CLARIFIED", cls:"t", rank:2 },
  hist:      { k:"hist",      label:"Inferred from history",short:"INF · HIST",cls:"a", rank:3 },
  cohort:    { k:"cohort",    label:"Inferred from cohort", short:"INF · COHORT",cls:"v", rank:4 },
  seller:    { k:"seller",    label:"Seller context (P&I)", short:"P&I",       cls:"n", rank:2 },
  planner:   { k:"planner",   label:"Planner correction",   short:"PLANNER",   cls:"g", rank:2 },
  gap:       { k:"gap",       label:"Unsupported by evidence",short:"GAP",     cls:"r", rank:9 },
};

/* -----------------------------------------------------------------------------
   EVIDENCE STORE — records, never summaries. Every record carries where it came
   from, where in the source it appeared, when it arrived, stated vs inferred.
--------------------------------------------------------------------------------*/
const EVIDENCE = [
  { id:"E01", attr:"Advertiser", value:"Procter & Gamble", cls:"stated",
    src:"Salesforce OPP-2026-04872", loc:"Account", ts:"2026-05-04 09:12", by:"Salesforce sync" },
  { id:"E02", attr:"Brand", value:"Tide (US) / Ariel (EMEA, LATAM, APAC)", cls:"stated",
    src:"RFP PDF", loc:"p.1 §1 Brand", ts:"2026-05-04 09:12", by:"Salesforce sync" },
  { id:"E03", attr:"Gross budget", value:"$18,500,000", cls:"stated",
    src:"RFP PDF", loc:"p.2 §2.1", ts:"2026-05-04 09:12", by:"Salesforce sync" },
  { id:"E04", attr:"Flight", value:"Jun 1 – Sep 27, 2026 (17 weeks)", cls:"stated",
    src:"RFP PDF", loc:"p.2 §2.2", ts:"2026-05-04 09:12", by:"Salesforce sync" },
  { id:"E05", attr:"Primary objective", value:"Incremental reach against light-TV households ahead of the Q3 pack redesign", cls:"stated",
    src:"RFP PDF", loc:"p.1 §1.2 Objective", ts:"2026-05-04 09:12", by:"Salesforce sync" },
  { id:"E06", attr:"Primary KPI", value:"1+ reach at 3+ effective frequency, A25-54", cls:"stated",
    src:"RFP PDF", loc:"p.3 §3.1 Success measures", ts:"2026-05-04 09:12", by:"Salesforce sync" },
  { id:"E07", attr:"Target demo", value:"A25-54, skew W25-54", cls:"stated",
    src:"RFP PDF", loc:"p.3 §3.2", ts:"2026-05-04 09:12", by:"Salesforce sync" },
  { id:"E08", attr:"Markets", value:"US, EMEA (UK/DE/PL/ES), LATAM (BR/MX), APAC (AU/SG/PH)", cls:"stated",
    src:"RFP PDF", loc:"p.2 §2.3 Geography", ts:"2026-05-04 09:12", by:"Salesforce sync" },
  { id:"E09", attr:"Brand-safety exclusion", value:"No hard-news adjacency", cls:"stated",
    src:"RFP PDF", loc:"p.4 §4.2 Exclusions", ts:"2026-05-04 09:12", by:"Salesforce sync" },
  { id:"E10", attr:"Do-not-air list", value:"41 titles (attached XLSX)", cls:"stated",
    src:"RFP attachment", loc:"tide_dna_2026.xlsx", ts:"2026-05-04 09:14", by:"Salesforce sync" },
  { id:"E11", attr:"Viewability floor", value:"80% MRC-viewable, digital video", cls:"stated",
    src:"RFP PDF", loc:"p.5 §5.1 Quality", ts:"2026-05-04 09:12", by:"Salesforce sync" },
  { id:"E12", attr:"Creative", value:":30 hero, :15 cutdown, 9:16 social variant", cls:"stated",
    src:"RFP PDF", loc:"p.6 §6", ts:"2026-05-04 09:12", by:"Salesforce sync" },

  { id:"E13", attr:"Linear / digital split", value:"Client will accept up to 45% linear if reach case is made", cls:"clarified",
    src:"AE call notes — Marcus Vieira", loc:"Call 2026-05-11, min 14", ts:"2026-05-11 16:40", by:"Marcus Vieira (AE)" },
  { id:"E14", attr:"CPM ceiling", value:"$32 blended, digital", cls:"clarified",
    src:"Agency email — Starcom", loc:"Re: Tide summer parameters", ts:"2026-05-12 11:05", by:"Marcus Vieira (AE)" },
  { id:"E15", attr:"Frequency cap", value:"6 per week per user, digital", cls:"clarified",
    src:"Agency email — Starcom", loc:"Re: Tide summer parameters", ts:"2026-05-12 11:05", by:"Marcus Vieira (AE)" },

  { id:"E16", attr:"Preferred networks", value:"HGTV, Food Network, discovery+ — 68% of prior 12-month spend", cls:"hist",
    src:"Advertiser history — 12-mo lookback", loc:"Plans PL-8841, PL-9002, PL-9187", ts:"2026-05-04 09:20", by:"Context service" },
  { id:"E17", attr:"CPM paid, digital video", value:"$28.40 average, 12-mo", cls:"hist",
    src:"Advertiser history — 12-mo lookback", loc:"4 plans, 61 lines", ts:"2026-05-04 09:20", by:"Context service" },
  { id:"E18", attr:"Rejected previously", value:"Programmatic PMP above 10% of plan — rejected twice on viewability", cls:"hist",
    src:"Advertiser history", loc:"PL-9002 rev 2, PL-9187 rev 1", ts:"2026-05-04 09:20", by:"Context service" },
  { id:"E19", attr:"Sports posture", value:"Never bought live sport on WBD; declined NBA package in 2025", cls:"hist",
    src:"Advertiser history", loc:"PL-8841 rejection note", ts:"2026-05-04 09:20", by:"Context service" },
  { id:"E20", attr:"Measurement partner", value:"VideoAmp + Nielsen ONE dual currency", cls:"hist",
    src:"Advertiser history", loc:"Last 3 plans, all markets", ts:"2026-05-04 09:20", by:"Context service" },

  { id:"E21", attr:"Regional budget split", value:"US 60 / EMEA 25 / LATAM 10 / APAC 5", cls:"cohort",
    src:"Cohort — global FMCG home-care, $15–25M", loc:"6 advertisers, 14 plans", ts:"2026-05-04 09:22", by:"Context service" },
  { id:"E22", attr:"Flight weighting", value:"Front-load 60% in first 8 weeks", cls:"cohort",
    src:"Cohort — summer FMCG launches", loc:"9 comparable flights", ts:"2026-05-04 09:22", by:"Context service" },

  { id:"E23", attr:"Yield posture", value:"Protect HBO Max premium CTV floor at $34; do not clear below", cls:"seller",
    src:"P&I standing position Q3'26", loc:"Position card PI-Q3-07", ts:"2026-04-28 08:00", by:"Rachel Levine (P&I)" },
  { id:"E24", attr:"Push list", value:"discovery+ US lifestyle genre and HBO Max LATAM ad tier are under-sold for Q3", cls:"seller",
    src:"P&I standing position Q3'26", loc:"Position card PI-Q3-11", ts:"2026-04-28 08:00", by:"Rachel Levine (P&I)" },
  { id:"E25", attr:"PMP cap", value:"Curated PMP capped at 12% of any FMCG plan — yield dilution", cls:"seller",
    src:"P&I standing position Q3'26", loc:"Position card PI-Q3-03", ts:"2026-04-28 08:00", by:"Rachel Levine (P&I)" },
  { id:"E26", attr:"Sports hold", value:"TNT / TNT Sports held against upfront sport commitments; release above floor +15% only", cls:"seller",
    src:"P&I standing position Q3'26", loc:"Position card PI-Q3-09", ts:"2026-04-28 08:00", by:"Rachel Levine (P&I)" },
  { id:"E27", attr:"P&I position on this RFP", value:"No advertiser-specific position stated. Absence recorded 2026-05-05.", cls:"seller",
    src:"P&I", loc:"Requested 2026-05-04, no response", ts:"2026-05-05 17:00", by:"System", absence:true },

  { id:"E28", attr:"Competitive pressure", value:"Persil US up 34% YoY on CTV; pulled entirely out of cable news", cls:"cohort",
    src:"Competitive research (planner-triggered)", loc:"eMarketer + internal category read", ts:"2026-05-13 10:30", by:"Research (on request)" },
];

/* Contradictions — both records kept, neither quietly wins. */
const CONTRADICTIONS = [
  { id:"C01", attr:"Linear / digital split", material:true,
    a:{ ev:"E13", text:"Client will accept up to 45% linear if the reach case is made", cls:"clarified", ts:"2026-05-11" },
    b:{ ev:"E29", text:"RFP body states 'digital-first, linear only where incremental'", cls:"stated", ts:"2026-05-04", loc:"RFP p.1 §1.3" },
    rec:"Treat 45% as a ceiling, not a target. The clarification is later and more specific; the RFP language is directional. Recommend planning to 32% linear and carrying headroom to 45%.",
    basis:"Later-and-more-specific rule + advertiser history (linear ran 29–38% across the last four plans)." },
  { id:"C02", attr:"CPM ceiling", material:true,
    a:{ ev:"E14", text:"$32 blended digital CPM ceiling", cls:"clarified", ts:"2026-05-12" },
    b:{ ev:"E17", text:"Advertiser paid $28.40 average digital video CPM over 12 months", cls:"hist", ts:"2026-05-04" },
    rec:"Not a true contradiction on the same attribute — a ceiling and a historical actual. Recommend recording the ceiling as the hard constraint and the $28.40 as the yield benchmark P&I will read the plan against.",
    basis:"Attribute-type reconciliation. No supersession required." },
  { id:"C03", attr:"Measurement currency", material:false,
    a:{ ev:"E20", text:"VideoAmp + Nielsen ONE dual currency", cls:"hist", ts:"2026-05-04" },
    b:{ ev:"E30", text:"RFP appendix names Nielsen ONE only", cls:"stated", ts:"2026-05-04", loc:"RFP Appendix B" },
    rec:"Immaterial to allocation. Surface at approval; do not block planning. Recommend confirming with the AE before the plan is shared.",
    basis:"Gap classification: planning is not invalidated by proceeding." },
];

/* Gaps — with a recommendation, never a bare question. */
const GAPS = [
  { id:"G01", attr:"Regional budget split", material:true, status:"open",
    why:"The RFP names four regions but allocates budget to none of them. The optimiser cannot solve a global plan without a regional envelope.",
    rec:"US 60% / EMEA 25% / LATAM 10% / APAC 5%",
    basis:"Cohort of 6 global FMCG home-care advertisers at $15–25M, 14 plans over 18 months. Median split 58/26/11/5; the advertiser's own 2025 global plan ran 62/24/9/5.",
    cohortSet:["Unilever — Persil Global 2025","Henkel — Global Home 2025","Reckitt — Finish Global 2026","P&G — Ariel EMEA 2025","Colgate — Global Care 2025","SC Johnson — Global 2025"],
    wouldCarry:"cohort" },
  { id:"G02", attr:"Flight weighting", material:true, status:"open",
    why:"Pack redesign lands week 9. Even weighting across 17 weeks would under-deliver the pre-launch reach build the objective asks for.",
    rec:"Front-load 60% of impressions into weeks 1–8, 40% into weeks 9–17",
    basis:"9 comparable summer FMCG launch flights. Median front-load 58%. Advertiser's own 2025 summer flight ran 63% front-loaded.",
    cohortSet:["9 summer FMCG launch flights, 2024–2026"],
    wouldCarry:"cohort" },
  { id:"G03", attr:"Creative rotation by market", material:false, status:"open",
    why:"Creative is specified centrally but no per-market rotation or language variant is stated. Affects trafficking, not allocation.",
    rec:"Assume single global rotation with local-language audio in DE, PL, ES, BR, MX",
    basis:"Advertiser's last two global plans; no cohort needed.",
    cohortSet:[], wouldCarry:"hist" },
  { id:"G04", attr:"P&I position for this advertiser", material:true, status:"absence",
    why:"No advertiser-specific seller position was returned. Standing Q3 position cards apply, but nothing specific to Tide.",
    rec:"Proceed on the four standing Q3'26 position cards and record the absence. Flag at approval so P&I cannot say the plan ignored a position they never stated.",
    basis:"Intake §2 — 'where P&I has stated nothing, the absence is recorded rather than left blank'.",
    cohortSet:[], wouldCarry:"seller" },
  { id:"G05", attr:"Attention / outcome guarantee", material:false, status:"open",
    why:"The KPI is reach at frequency. No attention or outcome guarantee is requested, but the category is moving that way.",
    rec:"Do not add. Offer an attention read-out as a value-add at share, not as a plan constraint.",
    basis:"Competitive read — 2 of 6 cohort advertisers now buy on attention. Advertiser has not asked.",
    cohortSet:["Persil","Arm & Hammer"], wouldCarry:"cohort" },
];

/* P&I standing position — the position the plan will be read against, line by line. */
const PI_POSITION = [
  { id:"PI-Q3-07", title:"Protect HBO Max premium CTV floor", posture:"floor",
    text:"No clearance below $34 CPM on HBO Max premium CTV for the Q3 window. This is the yield anchor for the whole US digital portfolio.",
    reason:"Q3 sellout tracking at 78%, +6 pts YoY. Clearing below floor resets the anchor for the scatter market.",
    appliesTo:["P01"], hardness:"soft" },
  { id:"PI-Q3-11", title:"Push under-sold supply", posture:"push",
    text:"discovery+ US lifestyle genre and HBO Max LATAM ad tier are behind pace for Q3. Plans that carry them meaningfully clear faster.",
    reason:"discovery+ lifestyle at 61% sellout vs 74% plan; HBO Max LATAM at 44% vs 60% plan.",
    appliesTo:["P03","P19"], hardness:"soft" },
  { id:"PI-Q3-03", title:"Cap curated PMP on FMCG", posture:"cap",
    text:"Curated PMP must not exceed 12% of any FMCG plan.",
    reason:"Yield dilution. FMCG PMP clears at 38% of direct CPM and cannibalises direct demand.",
    appliesTo:["P08"], hardness:"hard" },
  { id:"PI-Q3-09", title:"Hold sport inventory", posture:"hold",
    text:"TNT and TNT Sports inventory is held against upfront sport commitments. Release to scatter only above floor +15%.",
    reason:"Upfront sport commitments are 91% covered; the remaining units are the yield upside for the quarter.",
    appliesTo:["P07","P13"], hardness:"hard" },
];

/* 12-month advertiser lookback — records, so every inference can name its deals. */
const HISTORY = [
  { plan:"PL-9187", name:"Tide — Spring Clean 2026", closed:"2026-03-14", gross:6_200_000, linearPct:31,
    topProducts:["HGTV Prime","discovery+ CTV","Food Network Daytime"], cpm:27.9, outcome:"Delivered 104% of reach goal", rejected:"PMP at 14% — cut to 8% at agency request" },
  { plan:"PL-9002", name:"Tide — Holiday 2025", closed:"2025-11-02", gross:8_900_000, linearPct:38,
    topProducts:["HGTV Prime","TLC Prime","HBO Max CTV"], cpm:29.6, outcome:"Delivered 97%", rejected:"PMP at 12% — cut to 6% on viewability" },
  { plan:"PL-8841", name:"Ariel — EMEA Summer 2025", closed:"2025-05-20", gross:5_400_000, linearPct:34,
    topProducts:["Discovery EMEA Prime","HBO Max EMEA CTV","discovery+ UK"], cpm:24.1, outcome:"Delivered 101%", rejected:"NBA package declined — 'no sport for this brand'" },
  { plan:"PL-8620", name:"Tide — Back to School 2025", closed:"2025-08-08", gross:4_100_000, linearPct:29,
    topProducts:["Food Network Daytime","discovery+ CTV","HGTV Prime"], cpm:28.0, outcome:"Delivered 99%", rejected:"—" },
];

/* Desk / portfolio — other plans, so the prototype opens on a real desk. */
const PORTFOLIO = [
  { id:"OPP-2026-04872", name:"Tide — Global Summer Refresh 2026", adv:"Procter & Gamble", agy:"Publicis", ch:"Unified", dt:"Upfront", stage:"Intake", budget:18_500_000, start:"2026-06-01", meta:"Brief v3 · 3 material gaps open", owner:"You", flag:"active" },
  { id:"OPP-2026-04710", name:"Samsung — Galaxy Fold Launch", adv:"Samsung", agy:"Starcom", ch:"Digital", dt:"Scatter", stage:"Approval", budget: 7_200_000, start:"2026-06-15", meta:"PV-B with P&I · 3 lines disapproved", owner:"K. Lagwankar", flag:"blocked" },
  { id:"OPP-2026-04655", name:"Toyota — Summer Sales Event", adv:"Toyota", agy:"Dentsu", ch:"Linear", dt:"Scatter", stage:"Intake", budget: 4_800_000, start:"2026-07-01", meta:"Brief v1 · 3 material gaps", owner:"C. Cruz", flag:"active" },
  { id:"OPP-2026-04502", name:"Unilever — Dove Global Care", adv:"Unilever", agy:"Mindshare", ch:"Unified", dt:"Upfront", stage:"Analyze", budget:11_400_000, start:"2026-06-01", meta:"4 versions saved · none committed", owner:"You", flag:"active" },
  { id:"OPP-2026-04388", name:"Delta — Summer Destinations", adv:"Delta Air Lines", agy:"Omnicom", ch:"Digital", dt:"Scatter", stage:"Closed", budget: 3_100_000, start:"2026-05-01", meta:"PV-C approved · in flight", owner:"B. Mughal", flag:"closed" },
  { id:"OPP-2026-04201", name:"Nestlé — Coffee Portfolio EMEA", adv:"Nestlé", agy:"Zenith", ch:"Unified", dt:"Upfront", stage:"Planning", budget: 9_650_000, start:"2026-07-06", meta:"Awaiting intake approval", owner:"R. Iyer", flag:"active" },
];

/* -----------------------------------------------------------------------------
   AGENT ROSTER — the personas the system runs as.
   Deliberately not branded as AI in the UI copy (T8); named for the desk job
   each one does, and each one shows its reasoning.
--------------------------------------------------------------------------------*/
const AGENTS = [
  /* Added from the Flow Architecture note (6 Sep 2026). The orchestrator is
     first because everything else runs inside the state machine it holds. */
  { id:"A0", name:"Orchestrator", phase:"All", role:"Holds the state machine, knows every evaluation point inside it, and scores the intermediate status at each one. It separates what is missing from what is merely weak, and only the first of those holds a handoff.",
    inputs:["Phase state","Every evaluation point and its weight","Justification scores"], outputs:["Gate score","What is absent, and its remedy","What is weak, scored and carried forward"],
    guard:"It can hold a handoff only for absence — something the next phase would have to guess at. It has no power over quality: a weak argument goes forward carrying its score, to be read by P&I at the only gate that can stop a plan (OQ-17, OQ-22).", learns:"Which binding points planners routinely find ways around — a point worked around every time is a badly written point." },
  { id:"A0b", name:"Justification Eval", phase:"All", role:"Scores the argument behind a change, never the change itself, and names what a stronger argument would say.",
    inputs:["The planner's or approver's written reason","What is being changed"], outputs:["Argument score","What the argument is missing","Pass, thin, or flagged thin"],
    guard:"Judges form, not conclusion, and refuses nothing. It has no view on whether the change is right, and no power to stop a weak one — the score travels with the change into the approval package instead.", learns:"Reasons that passed and were later vindicated or overturned at approval." },
  { id:"A0c", name:"Evidence Eval", phase:"Intake", role:"Scores the strengths and weaknesses of every record on the RFP graph and writes the probability back onto it. Re-scores the graph whenever a human resolves something on it.",
    inputs:["Every record on the RFP graph","Adjudications and corrections"], outputs:["Per-record confidence","What would strengthen the weak ones"],
    guard:"Every point of a confidence score is attributable to source directness, citation, corroboration, contest and age. Nothing is a model output that cannot be argued with.", learns:"Which weak records turned out to matter, and which strong ones were wrong." },
  { id:"A0d", name:"Product Knowledge", phase:"Discovery", role:"Answers questions about products, customisations, exclusions and price in the planner's own words, over one index built from the FreeWheel and Operative configs and the pricing documents.",
    inputs:["Targeting templates, ad product configs, inventory packages (FreeWheel, Operative)","Reference pricing, product KPIs (spreadsheets, docs)"], outputs:["Answers with the configs they came from"],
    guard:"Every answer names its sources so a number can be checked rather than trusted. It retrieves; it does not recommend.", learns:"The questions planners ask that it answers badly." },

  { id:"A1", name:"Intake", phase:"Intake", role:"Reads the RFP and the Salesforce opportunity, writes evidence records, never conclusions.",
    inputs:["Salesforce opportunity","RFP PDF + attachments","AE call notes"], outputs:["Evidence records (stated)"],
    guard:"Cannot infer. Anything not literally in the source is left to the Context agent.", learns:"Field-extraction corrections by the planner." },
  { id:"A2", name:"Advertiser Context", phase:"Intake", role:"12-month lookback over prior plans. Produces proposals marked inferred-from-history, each naming its deals.",
    inputs:["Prior plans, lines, clearances","Rejections and their reasons"], outputs:["Inferred records (history)","Named comparables"],
    guard:"Every inference must name the deals behind it or it is not emitted.", learns:"Which historical signals the planner accepts vs rejects." },
  { id:"A3", name:"Cohort", phase:"Intake", role:"Finds similar advertisers when history is thin, and fills gaps with a recommendation and its comparable set.",
    inputs:["Category, spend band, geography","Cohort plan corpus"], outputs:["Inferred records (cohort)","Gap recommendations"],
    guard:"Similarity logic is stated on the record. OQ-6 is open — matching rule is [PROPOSED].", learns:"Accepted vs rejected cohort matches tighten the similarity rule." },
  { id:"A4", name:"Seller Position", phase:"All", role:"Carries P&I's stated position into the plan as soft constraints, each with its reason. Records absence where nothing was stated.",
    inputs:["P&I position cards","Sellout and yield pacing"], outputs:["Soft constraints","Recorded absences"],
    guard:"Never invents a position. Absence is a record, not a blank.", learns:"P&I approval and disapproval reasons refine the position model." },
  { id:"A5", name:"Competitive", phase:"Intake", role:"Planner-triggered external research on category spend and competitor activity.",
    inputs:["Category spend feeds","Competitive activity reads"], outputs:["Context records"],
    guard:"[OPEN] No provenance class on the ladder yet — cannot be derived from without breaking the evidence rule.", learns:"Which research the planner actually opens." },
  { id:"A6", name:"Eligibility", phase:"Discovery", role:"Selects every product that could legitimately serve the brief, and writes the reason for every exclusion.",
    inputs:["Intake brief","Product catalogue, avails, pricing"], outputs:["Eligibility list","Exclusion register"],
    guard:"An exclusion without a legible reason is a defect.", learns:"Products the planner adds back, and why." },
  { id:"A7", name:"Ranking", phase:"Discovery", role:"Orders the eligible set on five criteria and writes the reasoning that put each product where it sits.",
    inputs:["Eligibility list","KPI, constraints, seller position"], outputs:["Ranked strategy brief"],
    guard:"No position asserted without rationale (T5). Ranking is preference, not spend.", learns:"Planner re-orders and their justifications reweight the criteria." },
  { id:"A8", name:"Avails & Pricing", phase:"Discovery", role:"Re-prices and re-checks inventory the moment targeting changes, and raises the breach at that moment, not at approval.",
    inputs:["Targeting customisations","Rate card, floors, avails"], outputs:["Live price and avails position","Constraint breaches"],
    guard:"Price is exact; avails is an estimate until the solve. Says which is which.", learns:"Which customisations planners actually try." },
  { id:"A9", name:"Optimiser", phase:"Strategize", role:"Solves the allocation from the accepted ranked list. Deterministic. Not conversational, not negotiated with (T7).",
    inputs:["Ranked list + customisations","Hard and soft constraints","Justified overrides"], outputs:["Allocation","Constraint report"],
    guard:"Nothing is adjusted while the solver runs. Nothing outside the accepted list enters the solve.", learns:"Nothing directly — it learns only through better inputs." },
  { id:"A10", name:"Analysis", phase:"Analyze", role:"Reads each saved version against the good-plan rubric and against the advertiser's stated requirements.",
    inputs:["Plan version brief","Good-plan rubric [OQ-2 open]"], outputs:["Plan Version Analysis brief"],
    guard:"Scores each version in isolation. Does not rank versions against each other — that would be choosing for the planner.", learns:"Which rubric lines the planner and P&I argue with." },
  { id:"A11", name:"Approval", phase:"Approval", role:"Assembles the approval package and shows P&I each line against the position they already stated, with its inventory consequence.",
    inputs:["Committed version","P&I position cards","Supply position"], outputs:["Line decisions with reasons"],
    guard:"Cannot decide. Presents the position and the consequence; the human decides every line.", learns:"Disapproval reasons become tomorrow's soft constraints." },
  { id:"A12", name:"Learning", phase:"All", role:"Keeps every override, justification, rejection and disapproval, and applies them to the next derivation on this deal and the next similar one.",
    inputs:["Every recorded action + its reason"], outputs:["Applied signals","Criterion reweighting"],
    guard:"Signals are visible and reversible. A planner can see what the system learned and turn it off.", learns:"That is the whole job." },
];

/* Seed learning signals — what previous rounds on this advertiser already taught. */
const SEED_SIGNALS = [
  { id:"S1", when:"2026-03-14", from:"PL-9187 · planner override", text:"Programmatic PMP demoted below direct video on Tide plans", reason:"Agency cut PMP twice on viewability; carrying it high wastes a ranking slot.", effect:"Ranking: price-workability weight reduced for PMP-type products on this advertiser", strength:"strong", on:true },
  { id:"S2", when:"2026-03-14", from:"PL-9187 · P&I disapproval", text:"HBO Max premium CTV never proposed below the stated floor", reason:"Disapproved once at $31 CPM against a $34 floor; the rework cost four days.", effect:"Optimiser: treats the floor as hard on this advertiser unless P&I restates", strength:"strong", on:true },
  { id:"S3", when:"2025-05-20", from:"PL-8841 · client rejection", text:"Live sport excluded from Tide/Ariel eligibility by default", reason:"'No sport for this brand' — stated at rejection, repeated at the 2026 kickoff.", effect:"Eligibility: sport products enter the list flagged, ranked last, not removed", strength:"medium", on:true },
  { id:"S4", when:"2026-05-12", from:"Cohort acceptance rate", text:"Cohort splits for global FMCG accepted 11 of 14 times without edit", reason:"Recommendation quality on regional split is high; surface it as a single accept, not four fields.", effect:"Intake: regional split offered as one recommendation", strength:"medium", on:true },
];
