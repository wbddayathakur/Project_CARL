/* =============================================================================
   10-data-market.js
   Global market reference data for Warner Bros. Discovery — linear + digital.
   Figures are anchored-sample: directionally realistic, synthetic in detail.
   Sources modelled on: WBD Networks rate cards, Nielsen/Barb/Kantar universe
   estimates, eMarketer category spend, IAB viewability/VCR benchmarks.
   ============================================================================= */

const FLIGHT = { start: "2026-06-01", end: "2026-09-27", weeks: 17, label: "Jun 1 – Sep 27, 2026" };

const REGIONS = [
  { id: "US",    name: "United States",        cur: "USD", sym: "$", fx: 1.00, markets: ["US"] },
  { id: "EMEA",  name: "Europe, ME & Africa",  cur: "EUR", sym: "€", fx: 1.08, markets: ["UK","DE","PL","IT","ES","NL"] },
  { id: "LATAM", name: "Latin America",        cur: "USD", sym: "$", fx: 1.00, markets: ["BR","MX","AR","CO","CL"] },
  { id: "APAC",  name: "Asia Pacific",         cur: "USD", sym: "$", fx: 1.00, markets: ["IN","AU","SG","PH","ID"] },
];

/* Population universes (000s) for the demo cells we plan against. */
const UNIVERSE = {
  US:    { "A25-54": 128400, "W25-54": 65100, "P18-49": 132900, "HH": 124600 },
  EMEA:  { "A25-54":  96200, "W25-54": 48900, "P18-49": 101400, "HH":  92800 },
  LATAM: { "A25-54": 112500, "W25-54": 57800, "P18-49": 124300, "HH":  78400 },
  APAC:  { "A25-54": 168000, "W25-54": 81200, "P18-49": 191600, "HH": 121000 },
};

/* Category-level market context. Used by the Competitive Context agent. */
const MARKET_CONTEXT = [
  { region:"US", medium:"Linear", cat:"Home Care / Laundry", spendQ:  412, yoy:-11.4, cpmIdx: 98, note:"Category still over-indexes on daytime and early fringe; prime CPP up 4% on reduced supply." },
  { region:"US", medium:"Digital", cat:"Home Care / Laundry", spendQ:  688, yoy:+18.2, cpmIdx:106, note:"CTV absorbing linear shift; premium AVOD CPMs firm, mid-tail softening." },
  { region:"EMEA", medium:"Linear", cat:"Home Care / Laundry", spendQ: 196, yoy: -6.8, cpmIdx: 94, note:"UK/DE linear stable; PL and IT deflationary on supply glut." },
  { region:"EMEA", medium:"Digital", cat:"Home Care / Laundry", spendQ: 271, yoy:+14.1, cpmIdx:101, note:"Streaming ad tiers scaling fast; live sport inventory is the scarce unit." },
  { region:"LATAM", medium:"Linear", cat:"Home Care / Laundry", spendQ: 158, yoy: -2.1, cpmIdx: 71, note:"Pay-TV decline slower than US; still efficient reach for mass FMCG." },
  { region:"LATAM", medium:"Digital", cat:"Home Care / Laundry", spendQ: 143, yoy:+22.6, cpmIdx: 68, note:"Cheapest incremental reach in the portfolio; measurement quality is the constraint." },
  { region:"APAC", medium:"Linear", cat:"Home Care / Laundry", spendQ: 121, yoy: -3.9, cpmIdx: 46, note:"India drives volume; addressability limited." },
  { region:"APAC", medium:"Digital", cat:"Home Care / Laundry", spendQ: 209, yoy:+27.3, cpmIdx: 52, note:"Very low CPM, very high frequency risk without caps." },
];

/* What the competitive set is doing. Triggered research, per Intake §2. */
const COMPETITIVE = [
  { brand:"Persil (Henkel)",  region:"US",   spend: 24.6, mix:"58 digital / 42 linear", note:"Heavied up on retail media + CTV in Q2; pulled out of cable news entirely." },
  { brand:"Gain (P&G)",       region:"US",   spend: 11.2, mix:"40 digital / 60 linear", note:"Sister brand — daytime lifestyle heavy. Overlap risk on Food Network / HGTV." },
  { brand:"Arm & Hammer",     region:"US",   spend:  8.4, mix:"71 digital / 29 linear", note:"Almost fully programmatic; low premium-CTV presence." },
  { brand:"Ariel (P&G)",      region:"EMEA", spend: 19.8, mix:"52 digital / 48 linear", note:"Same parent, adjacent territory. Eurosport live sport used for summer reach." },
  { brand:"Omo (Unilever)",   region:"LATAM",spend: 14.1, mix:"35 digital / 65 linear", note:"Owns LATAM linear novela adjacency; digital under-invested." },
  { brand:"Surf Excel (HUL)", region:"APAC", spend: 16.9, mix:"44 digital / 56 linear", note:"Dominant in IN linear; WBD share of category near zero." },
];

/* Market CPM benchmarks — what a comparable unit clears at, by region and
   medium, A25-54. Price workability is judged against these, not against one
   global number, because a LATAM CPM and a US CPM are not the same question. */
const BENCH = {
  "US|Digital":    { cpm:30.0, note:"US premium AVOD/CTV video, direct" },
  "US|Linear":     { cpm:14.0, note:"US cable entertainment prime/daytime blend" },
  "EMEA|Digital":  { cpm:22.0, note:"UK/DE/ES streaming ad tier, direct" },
  "EMEA|Linear":   { cpm:11.0, note:"6-market pay-TV network prime" },
  "LATAM|Digital": { cpm:11.0, note:"BR/MX streaming ad tier" },
  "LATAM|Linear":  {  cpm:5.5, note:"BR/MX/AR pay-TV prime" },
  "APAC|Digital":  {  cpm:8.5, note:"AU/SG/PH streaming ad tier" },
  "APAC|Linear":   {  cpm:3.0, note:"IN/AU/PH network prime" },
};

/* Portfolio-level supply position for the flight. Feeds P&I inventory view. */
const SUPPLY = [
  { region:"US",    medium:"Digital", selloutPct: 78, trend:"+6 pts vs LY", scarce:["HBO Max premium CTV","Live sport midroll"] },
  { region:"US",    medium:"Linear",  selloutPct: 64, trend:"−9 pts vs LY", scarce:["TNT prime sport"] },
  { region:"EMEA",  medium:"Digital", selloutPct: 71, trend:"+11 pts vs LY", scarce:["Eurosport live"] },
  { region:"EMEA",  medium:"Linear",  selloutPct: 52, trend:"−4 pts vs LY", scarce:[] },
  { region:"LATAM", medium:"Digital", selloutPct: 44, trend:"+3 pts vs LY", scarce:[] },
  { region:"LATAM", medium:"Linear",  selloutPct: 58, trend:"flat", scarce:[] },
  { region:"APAC",  medium:"Digital", selloutPct: 39, trend:"+8 pts vs LY", scarce:[] },
  { region:"APAC",  medium:"Linear",  selloutPct: 47, trend:"−2 pts vs LY", scarce:[] },
];

/* -----------------------------------------------------------------------------
   PRODUCT & PACKAGE CATALOGUE
   availK   — impressions (000s) genuinely available to this advertiser over the
              17-week flight, after holdbacks
   floorCpm — P&I yield floor, in region currency
   cardCpm  — rate card
   openCpm  — opening negotiated CPM the pricing service returns for this brief
   demoComp — % of delivered impressions inside the A25-54 target
   reachK   — 1+ reach ceiling (000s) if the product were bought to saturation
   kpiFit   — fit against the brief's stated KPI (incremental reach @ 3+ freq)
--------------------------------------------------------------------------------*/
const PRODUCTS = [
  /* ---------------------------------------------------------------- US digital */
  { id:"P01", name:"HBO Max — Premium CTV Video :30", brand:"HBO Max", region:"US", medium:"Digital",
    format:"CTV in-stream", placement:"Originals & Movies, pod position 1",
    availK:412000, floorCpm:34, cardCpm:48, openCpm:42.0, demoComp:0.71, reachK:41800, kpiFit:94,
    viewability:0.97, vcr:0.965, attention:78, brandSafe:"Full episodic, no UGC",
    yieldPosture:"push", note:"Highest-attention unit in the portfolio. Scarce in Q3." },
  { id:"P02", name:"HBO Max — Pause Ad Sponsorship", brand:"HBO Max", region:"US", medium:"Digital",
    format:"Pause / display", placement:"Session pause, category exclusive",
    availK:96000, floorCpm:22, cardCpm:32, openCpm:27.5, demoComp:0.69, reachK:14200, kpiFit:61,
    viewability:0.99, vcr:null, attention:52, brandSafe:"Full episodic",
    yieldPosture:"push", note:"Sells category exclusivity; underbought by FMCG." },
  { id:"P03", name:"discovery+ — CTV Pre-roll :30", brand:"discovery+", region:"US", medium:"Digital",
    format:"CTV in-stream", placement:"Lifestyle & Home genre pod",
    availK:388000, floorCpm:26, cardCpm:38, openCpm:33.0, demoComp:0.74, reachK:29600, kpiFit:91,
    viewability:0.96, vcr:0.951, attention:69, brandSafe:"Full episodic",
    yieldPosture:"push", note:"Home & lifestyle genre is the closest contextual match to the brief." },
  { id:"P04", name:"Food Network Digital — Recipe Contextual Video", brand:"Food Network", region:"US", medium:"Digital",
    format:"Outstream video", placement:"Recipe & how-to pages",
    availK:214000, floorCpm:19, cardCpm:34, openCpm:29.5, demoComp:0.66, reachK:18900, kpiFit:74,
    viewability:0.82, vcr:0.712, attention:44, brandSafe:"O&O editorial",
    yieldPosture:"neutral", note:"Strong contextual story; viewability below the brief's 80% floor by 0 pts." },
  { id:"P05", name:"CNN Digital — Homepage Video Takeover", brand:"CNN", region:"US", medium:"Digital",
    format:"Homepage video", placement:"CNN.com HP, 24h roadblock",
    availK:64000, floorCpm:21, cardCpm:30, openCpm:26.0, demoComp:0.58, reachK:11400, kpiFit:38,
    viewability:0.88, vcr:0.664, attention:41, brandSafe:"News adjacency",
    yieldPosture:"push", note:"Blocked by the advertiser's standing news exclusion." },
  { id:"P06", name:"Bleacher Report — Social & Short-form Video", brand:"Bleacher Report", region:"US", medium:"Digital",
    format:"Social video", placement:"B/R owned handles + app",
    availK:302000, floorCpm:11, cardCpm:22, openCpm:18.5, demoComp:0.52, reachK:24300, kpiFit:57,
    viewability:0.79, vcr:0.588, attention:33, brandSafe:"UGC-adjacent comments",
    yieldPosture:"push", note:"Cheap reach, but skews M18-34 against a W25-54 brief." },
  { id:"P07", name:"TNT Sports Digital — Live Stream Midroll", brand:"TNT Sports", region:"US", medium:"Digital",
    format:"Live in-stream", placement:"NBA / NHL simulcast pods",
    availK:118000, floorCpm:32, cardCpm:52, openCpm:44.0, demoComp:0.61, reachK:16700, kpiFit:66,
    viewability:0.98, vcr:0.978, attention:81, brandSafe:"Live sport",
    yieldPosture:"hold", note:"P&I holding for upfront sports commitments; release only above floor +15%." },
  { id:"P08", name:"WBD Audience Network — Curated PMP", brand:"WBD Ad Network", region:"US", medium:"Digital",
    format:"Programmatic PMP", placement:"Cross-portfolio run of network",
    availK:940000, floorCpm:8, cardCpm:16, openCpm:13.0, demoComp:0.49, reachK:38200, kpiFit:48,
    viewability:0.74, vcr:0.523, attention:22, brandSafe:"Mixed",
    yieldPosture:"dump", note:"Yield-dilutive. P&I position is to cap FMCG PMP at 12% of any plan." },

  /* ----------------------------------------------------------------- US linear */
  { id:"P09", name:"Food Network — Daytime :30", brand:"Food Network", region:"US", medium:"Linear",
    format:"Linear spot :30", placement:"M-F 10a-4p",
    availK:268000, floorCpm:6.5, cardCpm:12, openCpm:9.2, demoComp:0.77, reachK:22100, kpiFit:83,
    viewability:null, vcr:null, attention:47, brandSafe:"Full episodic", grp:112, cpp:2840,
    yieldPosture:"push", note:"Best W25-54 composition in the linear portfolio at the lowest CPM." },
  { id:"P10", name:"HGTV — Prime :30", brand:"HGTV", region:"US", medium:"Linear",
    format:"Linear spot :30", placement:"Su-Sa 8p-11p",
    availK:184000, floorCpm:11, cardCpm:19, openCpm:15.4, demoComp:0.73, reachK:19600, kpiFit:79,
    viewability:null, vcr:null, attention:58, brandSafe:"Full episodic", grp:96, cpp:4120,
    yieldPosture:"push", note:"Home-improvement adjacency; historically the advertiser's top linear network." },
  { id:"P11", name:"TLC — Prime :30", brand:"TLC", region:"US", medium:"Linear",
    format:"Linear spot :30", placement:"Su-Sa 8p-11p",
    availK:152000, floorCpm:8.5, cardCpm:15, openCpm:11.8, demoComp:0.68, reachK:15300, kpiFit:64,
    viewability:null, vcr:null, attention:51, brandSafe:"Full episodic", grp:74, cpp:3380,
    yieldPosture:"neutral", note:"Efficient, but heavy duplication with HGTV in the same household base." },
  { id:"P12", name:"Discovery Channel — Prime Access :30", brand:"Discovery Channel", region:"US", medium:"Linear",
    format:"Linear spot :30", placement:"Su-Sa 7p-8p",
    availK:141000, floorCpm:9, cardCpm:16, openCpm:12.6, demoComp:0.54, reachK:14800, kpiFit:44,
    viewability:null, vcr:null, attention:49, brandSafe:"Full episodic", grp:68, cpp:3910,
    yieldPosture:"neutral", note:"M-skewing. Weak against a W25-54 brief." },
  { id:"P13", name:"TNT — Prime Sport :30", brand:"TNT", region:"US", medium:"Linear",
    format:"Linear spot :30", placement:"NBA / NHL windows",
    availK:98000, floorCpm:24, cardCpm:39, openCpm:31.5, demoComp:0.57, reachK:21400, kpiFit:59,
    viewability:null, vcr:null, attention:74, brandSafe:"Live sport", grp:141, cpp:8250,
    yieldPosture:"hold", note:"Reserved against upfront sport commitments." },

  /* ------------------------------------------------------------------- EMEA */
  { id:"P14", name:"HBO Max EMEA — CTV Video :30", brand:"HBO Max", region:"EMEA", medium:"Digital",
    format:"CTV in-stream", placement:"UK/DE/PL/ES ad tier",
    availK:246000, floorCpm:21, cardCpm:34, openCpm:28.5, demoComp:0.67, reachK:23400, kpiFit:86,
    viewability:0.96, vcr:0.958, attention:73, brandSafe:"Full episodic",
    yieldPosture:"push", note:"Ad tier scaling; incremental to any linear buy in-market." },
  { id:"P15", name:"discovery+ UK — Sponsorship Package", brand:"discovery+", region:"EMEA", medium:"Digital",
    format:"Sponsorship", placement:"Home & Food strand, 8-week",
    availK:58000, floorCpm:16, cardCpm:28, openCpm:22.0, demoComp:0.72, reachK:7100, kpiFit:70,
    viewability:0.94, vcr:0.902, attention:64, brandSafe:"O&O strand",
    yieldPosture:"push", note:"Fixed-cost strand; only sellable as a whole 8 weeks." },
  { id:"P16", name:"Eurosport — Live Event Midroll", brand:"Eurosport", region:"EMEA", medium:"Digital",
    format:"Live in-stream", placement:"Cycling / Tennis summer window",
    availK:132000, floorCpm:18, cardCpm:31, openCpm:24.5, demoComp:0.55, reachK:17800, kpiFit:62,
    viewability:0.97, vcr:0.971, attention:79, brandSafe:"Live sport",
    yieldPosture:"push", note:"Tour de France window falls squarely inside the flight." },
  { id:"P17", name:"Eurosport — Linear Live Sport :30", brand:"Eurosport", region:"EMEA", medium:"Linear",
    format:"Linear spot :30", placement:"Summer live windows",
    availK:174000, floorCpm:11, cardCpm:20, openCpm:16.0, demoComp:0.51, reachK:19200, kpiFit:53,
    viewability:null, vcr:null, attention:66, brandSafe:"Live sport", grp:88, cpp:3050,
    yieldPosture:"neutral", note:"Duplicates the Eurosport digital audience at roughly 34%." },
  { id:"P18", name:"Discovery EMEA Networks — Prime :30", brand:"Discovery EMEA", region:"EMEA", medium:"Linear",
    format:"Linear spot :30", placement:"6-market network prime",
    availK:298000, floorCpm:5.5, cardCpm:11, openCpm:8.4, demoComp:0.63, reachK:26700, kpiFit:68,
    viewability:null, vcr:null, attention:44, brandSafe:"Full episodic", grp:104, cpp:1980,
    yieldPosture:"push", note:"Cheapest quality reach in EMEA; PL and IT supply is long." },

  /* ------------------------------------------------------------------ LATAM */
  { id:"P19", name:"HBO Max LATAM — CTV Video :30", brand:"HBO Max", region:"LATAM", medium:"Digital",
    format:"CTV in-stream", placement:"BR/MX ad tier",
    availK:308000, floorCpm:8, cardCpm:16, openCpm:12.4, demoComp:0.64, reachK:24800, kpiFit:78,
    viewability:0.95, vcr:0.944, attention:70, brandSafe:"Full episodic",
    yieldPosture:"push", note:"Ad tier launched Q4'25; low sellout, real upside." },
  { id:"P20", name:"Discovery LATAM — Pay-TV Prime :30", brand:"Discovery LATAM", region:"LATAM", medium:"Linear",
    format:"Linear spot :30", placement:"BR/MX/AR network prime",
    availK:412000, floorCpm:3.8, cardCpm:8, openCpm:6.1, demoComp:0.6, reachK:31200, kpiFit:66,
    viewability:null, vcr:null, attention:41, brandSafe:"Full episodic", grp:126, cpp:1240,
    yieldPosture:"push", note:"Mass reach at the lowest CPM in the portfolio." },

  /* ------------------------------------------------------------------- APAC */
  { id:"P21", name:"HBO Max APAC — CTV Video :30", brand:"HBO Max", region:"APAC", medium:"Digital",
    format:"CTV in-stream", placement:"AU/SG/PH ad tier",
    availK:164000, floorCpm:6, cardCpm:14, openCpm:9.8, demoComp:0.58, reachK:14100, kpiFit:59,
    viewability:0.94, vcr:0.937, attention:66, brandSafe:"Full episodic",
    yieldPosture:"neutral", note:"IN not included — no ad tier in market for the flight." },
  { id:"P22", name:"Discovery APAC — Network Prime :30", brand:"Discovery APAC", region:"APAC", medium:"Linear",
    format:"Linear spot :30", placement:"IN/AU/PH network prime",
    availK:520000, floorCpm:2.1, cardCpm:5, openCpm:3.4, demoComp:0.46, reachK:38600, kpiFit:41,
    viewability:null, vcr:null, attention:33, brandSafe:"Full episodic", grp:98, cpp:640,
    yieldPosture:"neutral", note:"Volume without composition. Frequency risk without a cap." },
];

/* Products the eligibility pass throws out, with the reason (Discovery §2:
   'every exclusion is as legible as every inclusion'). */
const EXCLUDED = [
  { id:"X01", name:"CNN Linear — Early Fringe News :30", brand:"CNN", region:"US", medium:"Linear",
    reason:"Advertiser standing news exclusion", detail:"P&G global brand-safety policy excludes hard-news adjacency. Stated in RFP §4.2 and confirmed on the last four plans.", overridable:false },
  { id:"X02", name:"Adult Swim — Late Night :30", brand:"Adult Swim", region:"US", medium:"Linear",
    reason:"Do-not-air list", detail:"Advertiser do-not-air list, uploaded with the RFP. 6 titles on the network are listed; network-level exclusion applied.", overridable:true },
  { id:"X03", name:"HBO Max — Sports Tier Sponsorship", brand:"HBO Max", region:"US", medium:"Digital",
    reason:"No avails in flight", detail:"Fully committed to two upfront holds through Sep 30. Zero sellable impressions in the flight window.", overridable:false },
  { id:"X04", name:"Motor Trend — Prime :30", brand:"Motor Trend", region:"US", medium:"Linear",
    reason:"Below audience-fit threshold", detail:"A25-54 composition 0.31 against a W25-54 brief; ranked below the eligibility cut of 0.45.", overridable:true },
  { id:"X05", name:"Discovery India — Prime :30", brand:"Discovery APAC", region:"APAC", medium:"Linear",
    reason:"Price above ceiling after clearance risk", detail:"Workable CPM is inside the ceiling, but 41% historical pre-emption in the window pushes effective CPM to $5.90 against a $4.50 APAC ceiling.", overridable:true },
  { id:"X06", name:"TBS — Prime :30", brand:"TBS", region:"US", medium:"Linear",
    reason:"Superseded by TNT package", detail:"Sold only as part of the TNT/TBS sports bundle for this flight; represented by P13.", overridable:false },
];

const BRAND_COLOR = {
  "HBO Max":"#7b3fe4","discovery+":"#0b57d0","Food Network":"#d1451b","HGTV":"#0d7a4e","TLC":"#c2185b",
  "Discovery Channel":"#1a6fb5","TNT":"#e8641a","TNT Sports":"#e8641a","CNN":"#b3261e","Bleacher Report":"#0f1519",
  "WBD Ad Network":"#8a95a0","Eurosport":"#0a6b6b","Discovery EMEA":"#1a6fb5","Discovery LATAM":"#1a6fb5",
  "Discovery APAC":"#1a6fb5","Adult Swim":"#5b3fb8","Motor Trend":"#9a6600","TBS":"#0842a0",
};
