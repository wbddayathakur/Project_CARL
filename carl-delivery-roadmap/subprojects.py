"""Curated sub-project structure for the CARL Delivery Roadmap.

Jira owns: epic name, status, owner, ticket count, story points (read from
carl-roadmap-agent/out/carl-roadmap.json, then overlaid with the live epic pull).
This file owns: which sub-project an epic belongs to, the milestone ladder,
what leadership should be told, and every item that has no Jira epic.

Date rules
  * Epic dates come from the roadmap registry (Q4 Planning workbook) unless an
    item overrides them here.
  * `ext` items are product / dependency milestones from Confluence (planning
    minutes, weekly status). They are shown but never move the CARL delivery date.
  * `approx=True` means the source only says a month ("Nov 2026").

Source tags (kept short so they fit in a table cell)
  PLAN   CARL_2026Q4_QuarterlyPlanning,Status&Roadmap.xlsx
  JIRA   live Jira (CARL), 21 Oct 2026
  WK19   Confluence "CARL Weekly Data load Status - Iceberg", 19 Oct
  MIN7   Confluence "Q4 2026 / Q1 2027 Planning Session Minutes", 7 Oct
  LDR30  Confluence "CARL / Iceberg Leadership Review", 30 Sep
  PT30   Confluence "CARL - Product Tracking and Readiness", 30 Sep
  FWS    Confluence "FreeWheel Silver - Phase 1 Design", 21 Oct
  NEO8   Confluence "NEO 2.0 Backend Migration: API Delivery Status", 8 Oct
  PACK16 CARL Weekly Program Status 16 Oct (as summarised in the Slack thread;
         the .docx itself was not available to this build)
  EML19  19 Oct email on UC1 fast-track (as summarised in the Slack thread)
"""

TODAY = "2026-10-21"

GROUPS = [
    ("BD", "Business deliverables", "Dashboards and data products a business owner is waiting for", "#0e7490"),
    ("MG", "Legacy BI migration", "Retire MicroStrategy, DataStage and Looker/Power BI workloads", "#b91c1c"),
    ("PR", "Internal products CARL feeds", "UMP, Venus/iDeal, NEO, Forecasting, AIP/NAL and regional support", "#7c3aed"),
    ("SR", "Data sources (Bronze → Silver → Gold)", "Source-by-source readiness: Nielsen, FreeWheel, Operative One, GAM, 3P", "#c2410c"),
    ("PL", "Platform & governance", "Cube semantic layer, data trust, access, operations", "#475569"),
]


def E(key, **ov):
    """An epic that exists in Jira. Everything not overridden comes from the Jira snapshot."""
    return dict(kind="epic", key=str(key), **ov)


def S(key, n, st, bucket, o="", note="", **kw):
    """A story/bug with a Jira key that is not an epic."""
    return dict(kind="story", key=key, n=n, st=st, bucket=bucket, o=o, note=note, **kw)


def R(n, bucket="req", st="No epic raised", o="", note="", src="", **kw):
    """Roadmap-only item: committed or implied work with no Jira epic."""
    return dict(kind="rm", key=None, n=n, st=st, bucket=bucket, o=o, note=note, src=src, **kw)


def X(n, bucket, st, t=None, o="", note="", src="", approx=False, a=None, s=None):
    """External product / dependency milestone. Shown, but does not drive the CARL date."""
    return dict(kind="ext", key=None, n=n, st=st, bucket=bucket, o=o, note=note, src=src,
                t=t, a=a, s=s, approx=approx)


SUBPROJECTS = [
    # ------------------------------------------------------------------ BD
    dict(
        id="uc1", g="BD", name="UC1 · Total Ad Revenue (North Star)",
        outcome="One trusted Linear + Digital Ad Sales revenue view for Ad Sales and Finance.",
        owner="Arlene Rose · Mike Hodge", rag="A",
        why="Fast-track Gold dataset reached the business on 16 Oct, but the governed Silver → Gold pipeline that replaces it has no committed date and the Jira Gold epic still reads To Do.",
        phase="Fast-track Gold released; governed Silver/Gold in build; Phase 2 not started",
        ladder=[("Bronze", "done"), ("Silver", "build"), ("Gold", "build"), ("Cube", "todo"), ("Dashboard", "todo"), ("UAT", "todo"), ("Prod", "todo")],
        blocker="Additional dimensions/grains still being aligned; Operative One data 'provided but not working' for Jason (root cause open since 30 Sep).",
        ask="Set a date for the governed Silver → Gold replacement and confirm V1 scope (101 fields).",
        docs=[("CARL - Product Tracking and Readiness", "7926775861")],
        items=[
            E(56, note="Linear + Digital revenue Bronze."),
            E(597, a="2026-07-07", note="WRR digital dataset Bronze."),
            E(1480, note="Digital sports revenue OTB + PipeFeed; still in triage."),
            E(312, note="Linear + Digital revenue Silver."),
            E(313, note="Linear + Digital revenue Gold."),
            E(3638, note="Silver North Star Phase 1. Jira snapshot now shows 8 of 56 SP done (older notes said 0 of 32)."),
            E(3639, note="Gold North Star Phase 1. Jira still To Do; business received a fast-track Gold on 16 Oct (EML19) — reconcile."),
            E(4086, note="Phase 2 Silver. Created 5 Oct after export; unowned."),
            E(4087, note="Phase 2 Gold. Created 5 Oct after export; unowned."),
            R("Fast-track converged Gold dataset released to Jason / Adam", bucket="done", st="Done", a="2026-10-16",
              src="EML19", note="Interim logic. All agreed fast-track work delivered 16 Oct; not yet reflected in CARL-3639."),
            R("Additional dimensions and grains (business-requested)", bucket="build", st="In progress", s="2026-10-19",
              src="EML19", note="Started 19 Oct. No end date."),
            R("Business validation of converged dataset (Jason / Adam)", bucket="build", st="In progress",
              src="LDR30", note="Both Ad Sales and Finance pacing asks are in UAT (30 Sep review)."),
            R("UC1 certified dashboard on Cube / Quick", bucket="req", st="No epic / no date",
              src="PT30", note="'Cube planned; QuickSight via Cube.' Nothing in Jira or the plan carries a date."),
        ],
    ),
    dict(
        id="fin", g="BD", name="Finance Forecasting & Pacing",
        outcome="Weekly booked vs budget vs forecast pacing that Finance can run without help.",
        owner="Arlene Rose · Saman Saran", rag="A",
        why="Both epics slipped 30 Sep → 22 Oct (tomorrow) and the feed depends on a live Finance file that is not yet arriving; the 22 Oct date should be treated as unconfirmed.",
        phase="Forecast feed + pacing dashboard in progress; blocked on live Finance file",
        ladder=[("Ingestion", "done"), ("Feed (S3)", "build"), ("Silver", "build"), ("Gold", "todo"), ("Dashboard", "build"), ("Finance UAT", "todo"), ("Prod", "todo")],
        blocker="Live Finance forecast file availability.",
        ask="Reset the date from the day Finance delivers the first live file.",
        docs=[],
        items=[
            E(628, note="Digital forecasting data ingestion."),
            E(1479, note="Standard weekly CSV template. Slipped 9/30 → 10/22. Date to be re-set from live-file availability (PACK16)."),
            E(1364, note="Booked vs forecast pacing dashboard. Slipped 9/30 → 10/22."),
            X("Forecasting report for Finance follows once the feed is complete", "req", "Planned", src="LDR30",
              note="Julian Herman (Finance) has left; Jen Blue is the contact."),
        ],
    ),
    dict(
        id="sf", g="BD", name="Salesforce Opportunity Pipeline Dashboard",
        outcome="Opportunity pipeline analytics from Salesforce / Metropolis, replacing laptop pulls from Looker.",
        owner="Mike Hodge · Surendarvarma Sritharan", rag="A",
        why="Phase 1 Bronze is done but it arrives once a day via Oracle, the pipeline model (CARL-4050) is past its 15 Oct forecast, and the dashboard (due 9 Nov) cannot start sensibly until the model lands.",
        phase="Bronze Ph1 done · Ph2 API ingest in progress · pipeline model in build · dashboard in discovery",
        ladder=[("Bronze Ph1", "done"), ("Bronze Ph2", "build"), ("Silver/Gold model", "build"), ("Cube", "todo"), ("Dashboard", "build"), ("UAT", "todo"), ("Prod", "todo")],
        blocker="Salesforce reaches Iceberg only via Oracle once a day; no owner for a direct Salesforce → Iceberg flow. 20–28 further reports wait on this model.",
        ask="Decide on a direct Salesforce → Iceberg flow and confirm the Ph2 target.",
        docs=[("CARL / Iceberg Leadership Review — 30 Sep 2026", "7931002936")],
        items=[
            E(490, note="Metropolis transition gap mitigation."),
            E(2778, st="Done", note="Phase 1 via Oracle (not direct Salesforce). Slipped 8/30 → 9/30; Jira now shows Done, completion date not recorded."),
            E(4153, note="Phase 2 API extraction (supersedes roadmap row SF2). No target date set."),
            E(4050, note="UC1 converged pipeline data model. Forecast 10/15 has passed."),
            E(3490, note="Dashboard rebuild end-to-end. Discovery in progress."),
            X("Metropolis realtime events from UMP and Venus/COMS", "req", "Must-have", t="2026-11-30", approx=True, src="MIN7",
              note="Product-side dependency, not CARL scope."),
            X("Salesforce 2.0 intent-based workflow roadmap", "req", "Open", src="MIN7", o="Nathan Hernandez-Adams · Adam Waszczak",
              note="Replaces Appian workflows; Metropolis Phase 2 (headless) is a critical priority."),
        ],
    ),
    dict(
        id="adsd", g="BD", name="Ad Sales Dashboards (published)",
        outcome="Executive and operational Ad Sales dashboards live on Quick Suite.",
        owner="Ping Feng · Arlene Rose", rag="A",
        why="Incentive Revenue Pacing, Bobby V, Direct Response and Converged Pacing are live. Holes / Shares is the only item left, at 21 of 24 SP, and is long past its 31 Mar date.",
        phase="4 of 5 live; Holes outstanding; post-release RLS validation open",
        ladder=[("Converged Pacing", "done"), ("Direct Response", "done"), ("Bobby V exec", "done"), ("Incentive 2.0", "done"), ("Holes / Shares", "build")],
        blocker="Holes target of 31 Mar is long past; RLS/login-ID case-sensitivity and VP screenshot sign-off still open on Incentive.",
        ask="Re-baseline Holes or fold it into the semantic-layer deployment.",
        docs=[("CARL Weekly Data load Status - Iceberg", "7646478631")],
        items=[
            E(5, note="Converged Pacing dashboard."),
            E(197, note="Direct Response dashboard."),
            E(497, a="2026-06-22", note="Bobby V executive dashboard. Roadmap shows Done 6/22."),
            E(6, note="Converged Holes + Sports Holes and Shares. 21 of 24 SP done; original target was 31 Mar."),
            R("Ad Sales National Incentive Revenue Pacing Dashboard", bucket="done", st="Released", a="2026-09-30",
              src="WK19", o="Arlene Rose",
              note="Production release complete (WK19). Follow-ups: RLS / login-ID case sensitivity, VP screenshot sign-off."),
        ],
    ),
    dict(
        id="bp", g="BD", name="Blueprint (Content Supply Chain)",
        outcome="Blueprint program-planning data modelled Bronze → Gold and available for reporting.",
        owner="Ronald Ramsey", rag="A",
        why="Bronze is done; pipeline epic is past its 9 Oct target and Silver/Gold design was paused on a DDL/DML vs Terraform decision (30 Sep).",
        phase="Bronze done · pipeline in build · Silver/Gold design decision pending",
        ladder=[("Bronze", "done"), ("Pipeline", "build"), ("Silver", "todo"), ("Gold", "todo"), ("Semantic", "todo")],
        blocker="DDL/DML vs Terraform decision for Silver/Gold.",
        ask="Confirm whether Silver/Gold is still required and by when.",
        docs=[("Blueprint Data Pipeline", "7873036596"), ("Blueprint Data Pipeline — One-Pager", "7912194052")],
        items=[
            E(2898, a="2026-09-30", note="Blueprint Aurora DB Bronze."),
            E(3497, note="Blueprint pipeline / full model. Past 10/9 target; Confluence pipeline pages updated 20 Oct."),
        ],
    ),
    dict(
        id="res", g="BD", name="Research & NextGen (Market Share)",
        outcome="Market-share research data foundation and the NextGen Ad Sales Research dashboard on Quick.",
        owner="Daya Thakur · Virginia Giacomini", rag="A",
        why="Dashboard work starts from a Bronze layer (NRLD / Ad Intel / Big MIT) that is itself due 31 Oct, and NextGen migration has 48 of 63 SP not started.",
        phase="Discovery and data-model enhancement; Bronze inputs due 31 Oct",
        ladder=[("Nielsen Bronze", "build"), ("Silver / model", "build"), ("Cube", "todo"), ("NextGen on Quick", "build"), ("Market Share on Quick", "build"), ("Prod", "todo")],
        blocker="Silver conformance for Big MIT and Ad Intel not yet decided; Guideline / SMI has no epic.",
        ask="Confirm Silver conformance need and name the Greenfield pilot (NextGen vs Market Research).",
        docs=[("PRD – Market Research Data Foundation & NextGen Ad Sales Research Dashboard", "7931527171"),
              ("NextGen Research Dashboard - Power BI", "7952531701"),
              ("Research Market Share Data Discovery", "7955710014")],
        items=[
            E(11, note="NextGen Power BI → Quick. Planning sheet shows 'backlog, not started' while the epic is P0."),
            E(3775, note="Market Share insight data model + Looker → Quick."),
            E(3932, note="Research measurement data support. Single epic in Jira (duplicate was in the mapping file)."),
            E(549, note="Guaranteed Reach data readiness."),
            R("Guideline / SMI source", bucket="req", st="No epic raised", src="PT30",
              note="Named as a Research source; no Jira epic or Confluence page found."),
        ],
    ),
    dict(
        id="cnn", g="BD", name="CNN (RFP chatbot, Permutive)",
        outcome="Unstructured RFP data queryable by an AI chatbot; CNNi audience data discovered.",
        owner="Colin Diemer · Ping Feng", rag="G",
        why="POC-scoping stage with an end-Nov date; no data pattern decided for unstructured data.",
        phase="POC scoping",
        ladder=[("Scope", "build"), ("POC", "todo"), ("Evaluate", "todo")],
        blocker="Platform decision on an unstructured-data pattern.",
        ask="Declare the unstructured pattern so a platform decision can be taken.",
        docs=[],
        items=[
            E(3749, note="CNN RFP query insight chatbot."),
            E(631, note="CNNI Permutive data ingestion discovery. Unsized."),
        ],
    ),

    # ------------------------------------------------------------------ MG
    dict(
        id="mstr", g="MG", name="MicroStrategy → Quick (Lumos Phase 1)",
        outcome="Every in-scope MicroStrategy report rebuilt on Quick, signed off by the business and switched off.",
        owner="Aishwarya Jairam (Anuj Singh: Affiliate)", rag="R",
        why="Finance Batch 1 (98% of SP in UAT) and SOX both passed their dates; International (717 SP, 0% done), Hive and TD-API have no date at all, so the programme end cannot be stated honestly.",
        phase="Finance in business UAT · Ad Sales 2.1/2.2/2.3 in QA/UAT · Affiliate in build · International/Hive/TD-API awaiting re-projection",
        ladder=[("Lumos infra", "done"), ("Finance B1", "risk"), ("SOX / Accounting", "risk"), ("Ad Sales 2.1–2.3", "build"), ("Affiliate 3.x", "build"), ("International", "todo"), ("Hive · TD-API", "todo"), ("MSTR switch-off", "todo")],
        blocker="Finance UAT discrepancies and Quick export limits; International not reprojected; Lumos MicroStrategy API access (interim workaround).",
        ask="Re-project International, Hive and TD-API and publish one end date for MicroStrategy retirement.",
        docs=[("Lumos Dataset Pipeline: Ingest to Iceberg to Cube to QuickSight", "7795442056"),
              ("CARL Weekly Data load Status - Iceberg", "7646478631")],
        items=[
            E(427, note="MicroStrategy migration discovery."),
            E(1693, a="2026-08-03", note="Lumos workflow config / accelerator. Target 7/31, delivered 8/3."),
            E(2727, note="Finance Batch 1. 98% of SP in UAT; reconciliation largely complete; discrepancy triage and export workarounds open (WK19: AT RISK). Target 9/30 missed — reset needed."),
            E(4134, s="2026-08-28", t="2026-10-16", note="SOX and Accounting batch. Date from Planning sheet ('Accounting, SOX MS Reporting'); passed 16 Oct."),
            E(3571, note="Ad Sales Batch 2.1 (includes SOX per Planning sheet). In testing. Date 31 Oct held in PACK16."),
            E(3789, note="Ad Sales Batch 2.2. QA/UAT. 31 Oct held in PACK16."),
            E(3790, note="Ad Sales Batch 2.3. Next wave: 26 planned reports (WK19). 78 SP with no assignee."),
            E(3786, s="2026-09-30", t="2026-11-01", note="Affiliate Batch 3.1. Planning sheet shows target '1931-11-01' (typo); read as 1 Nov 2026 — confirm."),
            E(3787, s="2026-09-30", t="2026-11-01", note="Affiliate Batch 3.2. Same date caveat as 3.1."),
            E(4154, note="Affiliate Batch 3.3 (created 12 Oct). Not in Planning sheet; no date."),
            E(4155, note="Affiliate Batch 3.4 (created 12 Oct). No date."),
            E(4156, note="Affiliate Batch 3.5 (created 12 Oct). No date."),
            E(4157, note="Affiliate Batch 3.6 (created 12 Oct). No date."),
            E(4158, note="Affiliate infrastructure work (created 12 Oct). No date."),
            E(2971, n="MicroStrategy Reports P1: Full List (International scope)", note="Workbook: 717 SP / 400 tickets, 0% done. Planning sheet: 'Pending reprojection'."),
            E(3963, note="MicroStrategy International epic under Lumos; unassigned and unstarted."),
            R("HIVE MS Reporting", bucket="req", st="No epic · pending reprojection", src="PLAN", o="Aishwarya Jairam",
              note="Planning sheet: 'Pending Reprojection'."),
            R("TD – API integration (MicroStrategy)", bucket="req", st="No epic · pending reprojection", src="PLAN", o="Daya Thakur",
              note="Planning sheet: 'Pending Reprojection'."),
            R("MicroStrategy switch-off (US scope)", bucket="req", st="No date", src="PLAN",
              note="Q1 objective: 100% of in-scope US MSTR reports signed off and switched off. No date set."),
        ],
    ),
    dict(
        id="ds", g="MG", name="IBM DataStage → AWS Glue (Lumos Phase 2)",
        outcome="Oracle / DataStage pipelines migrated to Iceberg and DataStage retired by year end.",
        owner="Avinaag Bonam · Nagasaiteja Srirangam", rag="R",
        why="BTS_DLA MVP pipeline is the blocker (WK19: BLOCKED). POC and design are done; Implementation is dated 31 Dec and leadership wants DataStage retired by year end.",
        phase="POC and design done; implementation blocked on BTS_DLA MVP pipeline",
        ladder=[("POC", "done"), ("Design (ADD)", "done"), ("Migration plan", "risk"), ("BTS_DLA MVP", "block"), ("Implementation", "build"), ("Retire DataStage", "todo")],
        blocker="BTS_DLA MVP pipeline setup and source-to-target mapping; revised migration plan not yet published.",
        ask="Publish the revised migration plan and confirm 31 Dec still holds.",
        docs=[("ADD Links - Summary and Tracking", "7994867768")],
        items=[
            E(3562, s="2026-09-15", t="2026-12-31", note="Implementation: full Oracle → Iceberg migration. POC (to 9/11) and design (to 9/15) done per PLAN."),
            X("DataStage retirement targeted by end of year", "build", "Leadership ask", t="2026-12-31", src="LDR30",
              note="Replaced by AWS Glue (30 Sep leadership review)."),
        ],
    ),
    dict(
        id="bi", g="MG", name="Looker → Quick (Time Buy, Ad Product, Finance Ad Product)",
        outcome="Remaining Looker reports rebuilt on Quick.",
        owner="Daya Thakur", rag="G",
        why="All three are in triage with future dates (Dec–Jan); nothing late yet.",
        phase="Intake / triage",
        ladder=[("Intake", "build"), ("Discovery", "todo"), ("Build", "todo"), ("Prod", "todo")],
        blocker="Ad Product depends on GAM, which has no Iceberg pipeline.",
        ask="Confirm the GAM dependency for Ad Product.",
        docs=[],
        items=[
            E(3955, note="Time Buy: two Looker reports. Supersedes roadmap row 3932-TB. Dates from PLAN: 12/1 → 12/15.", s="2026-12-01", t="2026-12-15"),
            E(3954, note="Ad Product Looker reports. P2."),
            E(3748, note="Finance Ad Product Dashboard Modernization. No dates."),
        ],
    ),

    # ------------------------------------------------------------------ PR
    dict(
        id="ump", g="PR", name="UMP (Unified Media Planning)",
        outcome="UMP runs on governed CARL data: iDeal foundation, real-time and CDC ingestion.",
        owner="Surendarvarma Sritharan · Avinaag Bonam", rag="A",
        why="Weekly status says AT RISK: source-access and ingestion gaps limit full Bronze promotion for DCI / STW production tables. CDC (15 Aug) and real-time ingestion (15 Sep) are both overdue and real-time is escalated to the Oracle DB admin.",
        phase="Dev largely done; business UAT preparation; production promotion at risk",
        ladder=[("iDeal Bronze", "build"), ("CDC", "risk"), ("Real-time", "block"), ("Silver", "build"), ("Business UAT", "todo"), ("UMP prod", "todo")],
        blocker="Source access for DCI/STW tables; Oracle DB admin escalation for real-time; new table asks keep arriving close to launches.",
        ask="Re-baseline UAT readiness; route all new table asks through intake.",
        docs=[("UMP Digital MVP: UX/UI PRD, Prototype and Storyboard", "7960887676"),
              ("CARL Weekly Data load Status - Iceberg", "7646478631")],
        items=[
            E(3960, note="[Cross Project Support] UMP. Amber in Jira RAG; 1 ticket."),
            E(351, note="CMP iDeal Data Foundation Readiness: 105 tickets, 15 blocked (Jira). Business UAT / validation prep (WK19)."),
            E(2772, note="One-time iDeal dump for UMP."),
            R("iDeal CDC solution", bucket="build", st="Pending scope · overdue", src="PLAN", t="2026-08-15",
              o="Debarghyo Sengupta · Avinaag · Kedar", note="Past 8/15 target. Needed for incremental loads."),
            R("Real-time transactional ingestion", bucket="block", st="Pending scope · escalated", src="PLAN", t="2026-09-15",
              o="Debarghyo Sengupta", note="Past 9/15 target. Escalated to Oracle DB admin (MIN7)."),
            S("CARL-698", "DCI_RATECARD_HEADER available in Bronze", "Blocked", "block", o="Chitturi Kalyan",
              note="Plus bug CARL-1883 (missing ratecard fields), also blocked."),
            X("UMP US Digital MVP", "build", "At risk", t="2026-11-30", approx=True, src="MIN7",
              note="Product milestone (end Nov). Digital agentic planning not started."),
        ],
    ),
    dict(
        id="venus", g="PR", name="Venus / iDeal Modernization (incl. COMS)",
        outcome="iDeal replaced by Venus; CARL provides the iDeal data for pricing, stewardship and North Star.",
        owner="Kedareswara Petluri · Christina McCoy · Surendarvarma Sritharan", rag="R",
        why="The Venus ingest epic is Blocked (1 of 9 tables blocked, 8 in UAT), DealBldr is 11 weeks past its 1 Aug target, and iDeal canonical Silver has no epic or date. COMS has no declared data footprint.",
        phase="DCI and MSA Bronze done · DealBldr in progress · Venus ingest blocked",
        ladder=[("DCI Bronze", "done"), ("MSA Bronze", "done"), ("DealBldr Bronze", "build"), ("Venus tables", "block"), ("iDeal Silver", "todo"), ("Gold / Cube", "todo")],
        blocker="Schema and source-access blockers on Venus ingest (CARL-4043). iDeal Oracle replacement timeline owned by Venus.",
        ask="Raise an iDeal canonical Silver epic with a date; declare COMS data needs via intake.",
        docs=[("CARL - Product Tracking and Readiness", "7926775861")],
        items=[
            E(1160, note="iDeal Modernization cross-board tracking."),
            E(1478, a="2026-08-28", note="MSA schema Bronze."),
            E(2773, a="2026-08-28", note="DCI schema Bronze."),
            E(1477, note="DealBldr schema Bronze. Target 8/1 passed."),
            E(4035, note="iDeal tables to linear_digital_revenue_bronze for Venus. 8 of 9 table stories Ready for UAT, 1 blocked (CARL-4043). 31 Oct held in PACK16."),
            E(4137, note="[Cross Project Support] Venus."),
            R("iDeal canonical Silver", bucket="req", st="Pending scope · no date", src="PLAN", o="Arlene Rose",
              note="Roadmap-only row IDS. Silver for iDeal is not started."),
            R("iDeal cross-project support epic", bucket="req", st="No epic raised", src="PLAN",
              note="Page previously linked CARL-3959, which does not exist. Raise or drop."),
            X("COMS go-live", "req", "Planned", t="2026-11-30", approx=True, src="MIN7",
              note="DEP-01/02: Venus needs product catalog and Salesforce integrations before COMS go-live."),
            X("US OMS milestones: 15 Nov (agent-first UX) · 15 Dec", "req", "Planned", t="2026-11-15", src="MIN7",
              note="ADU go-live Q1 2027. Final requirements for COMS / Stewardship / P&P / RTI due 20 Oct."),
        ],
    ),
    dict(
        id="neo", g="PR", name="NEO / NEO 2.0",
        outcome="NEO reporting and analytics served from Iceberg and Cube.",
        owner="Virginia Giacomini", rag="G",
        why="Data-layer epic is progressing to a 15 Dec target; dependency risk sits with FreeWheel Silver and Clearline, not with NEO data work.",
        phase="Data layer in progress; Cube REST API with pre-aggregations",
        ladder=[("FW Bronze", "done"), ("NEO Bronze", "done"), ("NEO Silver", "build"), ("NEO Gold", "build"), ("Cube API", "build"), ("Prod Glue", "todo")],
        blocker="Prod Glue registration for FreeWheel tables; Clearline not started.",
        ask="Confirm prod Glue registration, refresh SLO and alerting owner.",
        docs=[("NEO 2.0 Backend Migration: API Delivery Status & Strategy", "7952499034"), ("WIP - NEO PRD | M&A Integration", "7952369802")],
        items=[
            E(3694, note="[Cross Project Support] Neo Data Layer Support. 17 tickets; +3 SP done this week."),
            R("Clearline data Bronze (Neo)", bucket="req", st="Pending scope · triage", src="PLAN", o="Avinaag Bonam",
              note="Roadmap-only row CLR. P0 for Neo; no date."),
            X("NEO 2.0 backend: 190 endpoints live on dev, ~55% complete", "build", "In progress", src="NEO8",
              note="~135–165 endpoints remain (NEO engineering, not CARL scope)."),
            X("NEO Content Marketplace roadmap", "req", "Planned", t="2026-12-31", approx=True, src="MIN7"),
            X("NEO agentic core campaign creation", "req", "Planned", t="2027-02-15", approx=True, src="MIN7", note="Mid-Feb 2027."),
        ],
    ),
    dict(
        id="fcst", g="PR", name="Forecasting (Digital · DDL · Linear)",
        outcome="Digital, DDL and Linear forecasting run on governed Iceberg / Cube data.",
        owner="Avinaag Bonam · Hong Zhang", rag="A",
        why="Digital Forecasting go-live is 31 Oct but the Snowflake → Glue catalog-federation dependency is AT RISK (manual sync is the fallback) and still depends on a third party's enriched FreeWheel data with no decoupling date.",
        phase="Ingest done; federation at risk; DDL and Linear separated into their own epics",
        ladder=[("Digital ingest", "done"), ("Catalog federation", "risk"), ("DDL epic", "todo"), ("Linear epic", "todo"), ("Silver/Gold", "todo"), ("Prod", "todo")],
        blocker="Catalog federation Snowflake → Glue; FreeWheel decoupling; NRLD duplicate rows (Linear).",
        ask="Confirm federation feasibility and owners for manual sync; confirm Silver/Gold grain (Selling Title × Target × Network × quarter-hour).",
        docs=[("PRD029: Traditional Linear Forecasting", "6907035825")],
        items=[
            E(4001, note="[Cross Project Support] DDL-forecasting. 5 tickets."),
            E(4097, note="[Cross Project Support] Linear-forecasting. Created 7 Oct; separates Linear from DDL."),
            E(580, n="Configure Catalog Federation — Snowflake to Glue", st="Done", note="Jira shows Done; WK19 still reports AT RISK with manual-sync fallback — reconcile."),
            X("Digital Forecasting go-live (incl. allocation)", "build", "Committed", t="2026-10-31", src="MIN7", o="Rohini Vugumudi", note="AI-076."),
            X("Linear Forecasting production release", "req", "Committed", t="2026-11-28", src="MIN7", o="Parimal Bajpai", note="AI-077."),
        ],
    ),
    dict(
        id="aip", g="PR", name="AIP & NAL",
        outcome="AIP gets modelled Operative One / FreeWheel data; NAL gets an audience data path.",
        owner="Ethan Garrison · Diana Saafi", rag="A",
        why="Epic exists with a 15 Dec target but has no tickets; it depends on Operative One Silver and FreeWheel Silver, neither of which has started; NAL plan depends on the ID-spine decision.",
        phase="Scoping; no work items raised",
        ladder=[("Scope", "build"), ("Op1 / FW Silver", "todo"), ("Gold", "todo"), ("Prod", "todo")],
        blocker="Op1 and FreeWheel Silver; BOLT code not checked in; NAL: Hightouch ID spine vs PSky IMS.",
        ask="Declare Gold model grain and BOLT dependency date.",
        docs=[],
        items=[E(3958, note="[Cross Project Support] AIP & NAL. 0 tickets.")],
    ),
    dict(
        id="reg", g="PR", name="International & Affiliate support",
        outcome="CARL covers International scope and Affiliate data needs.",
        owner="Avinaag Bonam · Anuj Singh", rag="A",
        why="International scope is confirmed as all of International with 2 resources staffed (onboarding is the constraint); Affiliate has no declared target source tables or retirement date.",
        phase="Discovery and scoping",
        ladder=[("Scope", "build"), ("Sources named", "todo"), ("Build", "todo"), ("Prod", "todo")],
        blocker="Onboarding capacity; Affiliate target sources undeclared.",
        ask="Declare Affiliate target source tables and retirement date.",
        docs=[],
        items=[
            E(3961, note="[Cross Project Support] International. MicroStrategy International is tracked under MicroStrategy."),
            E(634, note="[Cross Project Support] US Affiliate Support. Tracked under Global Affiliates programme."),
            X("INTL HBO Max Mexico forecast", "build", "Analysis, impact and resourcing", t="2026-11-15", approx=True, src="MIN7",
              note="DEP-17 (UMP INTL). Mid-Nov."),
        ],
    ),

    # ------------------------------------------------------------------ SR
    dict(
        id="niel", g="SR", name="Nielsen (NRLD · Ad Intel · Big MIT · Stewardship)",
        outcome="All Nielsen feeds in Bronze with the NRLD data-quality defect fixed.",
        owner="Sean Malek · Colin Diemer", rag="A",
        why="Three Bronze enhancements are due 31 Oct; NRLD is red in Jira (duplicate rows and back-dated inserts bug, framework migration blocked) and Stewardship has no scope or date.",
        phase="Bronze enhancements in progress; Silver not started for any Nielsen source",
        ladder=[("NRLD Bronze", "risk"), ("Ad Intel Bronze", "build"), ("Big MIT Bronze", "build"), ("Stewardship", "todo"), ("Silver", "todo"), ("Gold", "todo")],
        blocker="NRLD back-dated inserts + duplicate rows; NRLD Snowflake framework migration blocked; Stewardship scope.",
        ask="Confirm Silver conformance need for Big MIT and Ad Intel; scope Stewardship.",
        docs=[("9.17 Nielsen Sync and KT about NRLD Notes", "7881818263"), ("Nielsen AMRLD/NRLD", "7113474159")],
        items=[
            E(3779, note="Nielsen NRLD. Consumers: UMP, Linear Forecast, NextGen. Jira RAG red."),
            S("CARL-3781", "[bug] NRLD daily ingestion misses back-dated inserts + duplicate rows", "In Review", "build", o="Sean Malek"),
            S("CARL-2952", "Complete NRLD Snowflake framework migration", "Blocked", "block", o="Sean Malek"),
            E(3499, note="Nielsen Ad Intel (marketshare). PLAN marks every stage complete but Jira epic is 8 of 16 SP — reconcile. Story CARL-468 in testing."),
            E(3500, note="Nielsen Big MIT (8 tables in big_mit_bronze). Same PLAN vs Jira gap. Story CARL-578 in testing."),
            E(3501, note="Nielsen Stewardship. Scope pending."),
        ],
    ),
    dict(
        id="fw", g="SR", name="FreeWheel (Bronze · API · Silver · decoupling)",
        outcome="FreeWheel data in Silver so Neo, Forecasting, UMP and Venus no longer depend on a third party's enriched feed.",
        owner="Hong Zhang · Sean Malek", rag="R",
        why="Leadership asked for exact decoupling dates on 30 Sep; none exist. Silver is in progress (Phase 1: one ad-stream fact + 18 dimensions) but five initiatives wait on it and the prod Glue catalog is not registered.",
        phase="Bronze done · API Bronze and Phase 2 in testing · Silver in build · decoupling undated",
        ladder=[("Bronze (64 tables)", "done"), ("API Bronze", "build"), ("Phase 2 Bronze", "build"), ("Silver Ph1", "build"), ("Prod Glue", "todo"), ("Decoupling", "block")],
        blocker="No decoupling date; FW retains 7 days; contextual data inaccessible; prod Glue catalog unregistered.",
        ask="Commit decoupling dates per dependent system (Digital Forecasting, NEO live view, Venus digital pacing).",
        docs=[("FreeWheel Silver - Phase 1 Design", "7870742561")],
        items=[
            E(3704, note="Unified Ads discovery (FreeWheel + Operative One)."),
            E(746, a="2026-07-01", note="FreeWheel log Bronze (64 tables)."),
            E(1380, note="FreeWheel API Bronze. In testing; priority lowered P1 → P2 pending product requirement."),
            E(1756, note="Phase 2 Bronze: data never before in WBD. Priority lowered P1 → P2."),
            E(2887, note="FreeWheel Silver. WK19: API validation, dimensional model review, silver fact pipeline acceptance 'next week'."),
            R("Decoupling from third-party enriched FreeWheel data", bucket="block", st="No date", src="LDR30", o="Hong Zhang · Ping Feng",
              note="Open ~6 months. Hong full-time on Silver replacement. Exact dates were due 2 Oct; progress 'behind pace' (AI-087, due 31 Oct)."),
            R("FreeWheel production Glue catalog registration", bucket="req", st="Open gap", src="PT30",
              note="Prod S3 landing exists; Glue catalog not registered in prod."),
        ],
    ),
    dict(
        id="op1", g="SR", name="Operative One",
        outcome="A conformed Silver / Gold layer on top of the 81 Operative One Bronze tables.",
        owner="Diana Saafi · Mike Hodge", rag="A",
        why="Bronze live since 1 Jul but no consumer has asked for the conformed layer, so Silver has no date. WBD Opt1 Direct Response still runs on a Snowflake view.",
        phase="Bronze done; Silver not started",
        ladder=[("Bronze (81 + 7 tables)", "done"), ("Silver", "todo"), ("Gold", "todo"), ("Cube", "todo")],
        blocker="No requester for Silver; Direct Response still on Snowflake.",
        ask="Ad Products and AIP to state Silver/Gold requirement and grain; agree Direct Response cutover.",
        docs=[],
        items=[
            E(744, a="2026-07-01", note="Operative One Bronze (81 tables in operative_bronze + 7 in operative1_bronze)."),
            E(2888, note="Operative One Silver. Shared Silver is unowned across 5 consuming initiatives (PT30)."),
        ],
    ),
    dict(
        id="gam", g="SR", name="GAM / DFP",
        outcome="Decide whether GAM data is needed and, if so, build the pipeline.",
        owner="Debarghyo Sengupta · Virginia Giacomini", rag="R",
        why="Verified: no Glue database, no S3 data, no pipeline. Four initiatives assume GAM exists. Only a discovery story is in progress.",
        phase="Discovery; requirement not confirmed",
        ladder=[("Discovery", "build"), ("Need confirmed", "todo"), ("Bronze", "todo"), ("Silver", "todo")],
        blocker="Nobody has confirmed GAM is required; it is a net-new pipeline.",
        ask="Confirm whether GAM is genuinely required for UMP / AIP / Forecasting / Ad Products, and by when.",
        docs=[],
        items=[
            E(749, note="Ingest GAM data (Bronze). Pending scope."),
            S("CARL-750", "GAM data discovery", "In Progress", "build", o="Debarghyo Sengupta"),
        ],
    ),
    dict(
        id="p3", g="SR", name="Measurement & 3P (STAQ · VideoAmp · LoopMe/iSpot · CAPI · Comscore)",
        outcome="Third-party measurement and audience sources discovered and, where needed, landed in Bronze.",
        owner="Debarghyo Sengupta · Ping Feng", rag="A",
        why="Every item is waiting on intake discovery, requirements and a PRD; none has a date. Comscore has no Jira epic or Confluence page.",
        phase="Intake / discovery",
        ladder=[("STAQ", "build"), ("VideoAmp", "todo"), ("LoopMe · iSpot", "todo"), ("CAPI", "todo"), ("Comscore", "todo")],
        blocker="Access, feeds and requirements outstanding from each vendor.",
        ask="Prioritise which measurement source is genuinely needed first.",
        docs=[],
        items=[
            E(3750, note="STAQ Bronze. Spike CARL-4165 in progress (Ping Feng). P0 for UC1."),
            E(3503, note="M&A: VideoAmp."),
            E(3504, note="M&A: LoopMe, iSpot."),
            E(3505, note="M&A: CAPI (triage-only)."),
            E(4138, note="[Cross Project Support] CAPI. First estimate-bearing home for CAPI (created 12 Oct)."),
            R("Comscore", bucket="req", st="Not found", src="Jira + Confluence search",
              note="No Jira epic or Confluence page returned for 'Comscore'. Needs an intake request before it can carry a date."),
        ],
    ),

    # ------------------------------------------------------------------ PL
    dict(
        id="cube", g="PL", name="Semantic layer (Cube)",
        outcome="Business metrics and published dashboards served through a certified Cube layer.",
        owner="Colin Diemer · Aishwarya Jairam", rag="A",
        why="Infrastructure is 74% done and due 31 Oct, but deployment of the published dashboards onto Cube (due 1 Nov) already missed its deadline and is waiting on SOP alignment and a feed.",
        phase="Infra Phase 2 (SOP / authoring) due 31 Oct; dashboard deployment slipped",
        ladder=[("Cube infra", "done"), ("Phase 2 SOP", "build"), ("Holes / DR on Cube", "build"), ("All published reports", "todo")],
        blocker="SOP alignment; pending feed.",
        ask="Agree the semantic-layer authoring SOP.",
        docs=[("NextGen Semantic layer - [CARL-88]", "7952761094")],
        items=[
            E(424, note="Cube + SageMaker integration."),
            E(547, note="Unified Semantic Layer infra. Phase 1 due 6/30 done; Phase 2 SOP due 10/31."),
            E(3783, note="Semantic model deployment for published dashboards. Missed deadline; SOP alignment pending feed."),
        ],
    ),
    dict(
        id="trust", g="PL", name="Data trust (DQ · Observability · Catalog)",
        outcome="Data quality rules, observability and a discoverable catalog across CARL datasets.",
        owner="Debarghyo Sengupta · Armando Garcia Gama · Ping Feng", rag="A",
        why="DQ and Observability both target 30 Nov at about 60–80% SP done; the Catalog epic is in triage and the three trust PRDs were only published 14–15 Oct.",
        phase="DQ MVP and observability in progress; catalog in triage",
        ladder=[("DQ MVP", "build"), ("Observability", "build"), ("Catalog", "todo"), ("Data contracts", "build")],
        blocker="Catalog federation approach; capacity (2-week holiday carve-out).",
        ask="Name an owner for catalog discoverability.",
        docs=[("CARL Platform Trust & Data Governance: 3-PRD Suite", "7969243171"),
              ("CARL Data Catalog and Discoverability PRD", "7863238871"),
              ("QA Promotion Checklist for Source to Bronze, Silver, and Gold", "7986315360")],
        items=[
            E(540, note="Data Quality MVP."),
            E(384, note="Data observability. Jira now shows In Triage though PLAN reports 83% complete — reconcile."),
            E(538, note="Data discoverability: Data Catalog for Iceberg. PRD at v55."),
        ],
    ),
    dict(
        id="gov", g="PL", name="Governance, access & operations",
        outcome="Governed repos and AWS access, production support, intake and playbook.",
        owner="Avinaag Bonam · Virginia Giacomini · Nathan Hernandez-Adams", rag="G",
        why="Foundation work is complete; governance and access are ever-green to 15 Dec. The playbook (0 of 110 SP) is the only sizeable unstarted item.",
        phase="Foundation done; run-state work continuing",
        ladder=[("Infra + CI/CD", "done"), ("Intake form", "done"), ("Access control", "build"), ("Playbook", "todo")],
        blocker="Capacity: December holidays.",
        ask="Decide the Greenfield delivery-plan pilot (NextGen vs Market Research).",
        docs=[("Greenfield Project Delivery Plan (Draft v0.1)", "7951876793")],
        items=[
            E(2), E(25), E(28), E(127), E(355), E(529), E(802), E(803),
            E(3553, note="Governance and access controls for repos and AWS environments."),
            E(345, note="Data compliance and SOX control."),
            E(4175, note="Platform gaps and governance implementation (created 14 Oct)."),
            E(462, ev=True, note="Production support (ever-green)."),
            E(660, ev=True, note="Tech debt (ever-green)."),
            E(546, ev=True, note="QuickSight usage and adoption (ever-green)."),
            E(767, note="Playbook: 0 of 110 SP."),
            E(656, note="SharePoint (unstructured data testing). Blocked."),
        ],
    ),
]


# Curated source x layer matrix. `keys` ties a row to epics so the next date is computed.
SOURCES = [
    dict(src="iDeal — DCI / MSA / DealBldr", b=("build", "DCI + MSA done; DealBldr in progress; Venus tables 8 of 9 in UAT"), s=("build", "In progress"), g=("todo", "Planned"),
         use="UMP, Venus, Lumos, North Star", sub="venus", keys=["1477", "4035", "351"]),
    dict(src="Operative One", b=("done", "81 + 7 tables"), s=("todo", "Not started"), g=("todo", "—"),
         use="AIP, Ad Products, UC1", sub="op1", keys=["2888"]),
    dict(src="FreeWheel (logs, 64 tables)", b=("done", "Done 1 Jul"), s=("build", "Phase 1 in build"), g=("todo", "Planned"),
         use="NEO, UMP, Forecasting, AIP, Venus", sub="fw", keys=["2887"]),
    dict(src="FreeWheel API (+ Phase 2)", b=("build", "In testing"), s=("todo", "—"), g=("todo", "—"),
         use="NEO, UMP, AIP", sub="fw", keys=["1380", "1756"]),
    dict(src="Salesforce / Metropolis", b=("build", "Ph1 done (Oracle, daily); Ph2 API in progress"), s=("build", "In build (UC1 model)"), g=("todo", "Planned"),
         use="UMP, Lumos, M&A, Pipeline dashboard", sub="sf", keys=["4153", "4050", "3490"]),
    dict(src="WRR / LDR2", b=("done", "Done"), s=("done", "Done"), g=("done", "Done"),
         use="Forecasting, pacing dashboards", sub="uc1", keys=["597"]),
    dict(src="Linear + Digital revenue (gabprd, stwprd, DWH)", b=("done", "176 tables"), s=("build", "156 tables; North Star in build"), g=("build", "24 tables; fast-track released"),
         use="UC1, Ad Sales dashboards", sub="uc1", keys=["312", "313", "3638", "3639"]),
    dict(src="Nielsen NRLD", b=("risk", "Enhancement in progress; duplicate-row bug"), s=("todo", "Pending"), g=("todo", "Planned"),
         use="UMP, Linear Forecasting, NextGen", sub="niel", keys=["3779"]),
    dict(src="Nielsen Ad Intel (market share)", b=("build", "10 tables; enhancement in progress"), s=("todo", "Decision pending"), g=("todo", "—"),
         use="Research, Market Share", sub="niel", keys=["3499"]),
    dict(src="Nielsen Big MIT", b=("build", "8 tables; enhancement in progress"), s=("todo", "Decision pending"), g=("todo", "—"),
         use="Research, Market Share", sub="niel", keys=["3500"]),
    dict(src="Nielsen Stewardship", b=("todo", "In triage"), s=("todo", "—"), g=("todo", "—"),
         use="UMP, Linear Forecast, Analytics", sub="niel", keys=["3501"]),
    dict(src="Guideline / SMI", b=("todo", "No epic"), s=("todo", "—"), g=("todo", "—"),
         use="Research", sub="res", keys=[]),
    dict(src="Digital Forecasting (DAAP_RPT)", b=("done", "Done"), s=("todo", "Blocked downstream"), g=("todo", "—"),
         use="UMP, Forecasting", sub="fcst", keys=["628", "4001"]),
    dict(src="GAM / DFP", b=("todo", "No pipeline"), s=("todo", "—"), g=("todo", "—"),
         use="UMP, AIP, Forecasting, Ad Products (assumed)", sub="gam", keys=["749"]),
    dict(src="Blueprint (Aurora)", b=("done", "Done"), s=("risk", "Design paused"), g=("todo", "Paused"),
         use="Program planning", sub="bp", keys=["3497"]),
    dict(src="STAQ", b=("todo", "Triage; spike in progress"), s=("todo", "—"), g=("todo", "—"),
         use="UC1", sub="p3", keys=["3750"]),
    dict(src="Clearline", b=("todo", "Triage"), s=("todo", "—"), g=("todo", "—"),
         use="NEO", sub="neo", keys=[]),
    dict(src="VideoAmp", b=("todo", "To do"), s=("todo", "—"), g=("todo", "—"),
         use="M&A, Forecasting", sub="p3", keys=["3503"]),
    dict(src="LoopMe · iSpot", b=("todo", "To do"), s=("todo", "—"), g=("todo", "—"),
         use="M&A dashboard", sub="p3", keys=["3504"]),
    dict(src="CAPI", b=("todo", "To do"), s=("todo", "—"), g=("todo", "—"),
         use="M&A dashboard", sub="p3", keys=["3505", "4138"]),
    dict(src="Comscore", b=("todo", "Not found in Jira or Confluence"), s=("todo", "—"), g=("todo", "—"),
         use="Unknown", sub="p3", keys=[]),
    dict(src="Kerv · Cairo · CEP (contextual)", b=("todo", "Not documented"), s=("todo", "—"), g=("todo", "—"),
         use="UMP contextual, Contextual Packager", sub=None, keys=[]),
    dict(src="CNN RFP docs / Permutive", b=("todo", "Not medallion"), s=("todo", "—"), g=("todo", "—"),
         use="CNN chatbot", sub="cnn", keys=["3749", "631"]),
]


# Places where two sources disagree. Each one is a question for the owner, not a verdict.
CONFLICTS = [
    ("UC1", "CARL-3639 (Gold North Star) is To Do in Jira, but the business received a fast-track Gold dataset on 16 Oct (EML19).", "Arlene Rose · Mike Hodge", "Update Jira or split the interim release into its own item."),
    ("UC1", "Weekly pack of 16 Oct said the combined Ad Sales revenue table was heading to 22 Oct; the 19 Oct email says it was released 16 Oct.", "Arlene Rose", "Treat the 16 Oct pack as stale for UC1."),
    ("Forecasting", "CARL-580 Catalog Federation is Done in Jira, but the 19 Oct weekly status still lists it AT RISK with a manual-sync fallback.", "Virginia Giacomini", "Confirm whether federation is live or the fallback is in use."),
    ("Nielsen", "Planning sheet marks every stage 'Complete' for Ad Intel and Big MIT; the Jira epics are 8 of 16 SP and In Progress.", "Colin Diemer", "Confirm what 'Complete' meant (Dev vs Prod)."),
    ("MicroStrategy", "Planning sheet shows Affiliate target as 1931-11-01 and Catalog Federation as 1931-09-01 — date typos.", "Anuj Singh · Virginia Giacomini", "Read as Nov 2026 / unknown; confirm."),
    ("MicroStrategy", "Planning sheet ties SOX to CARL-3571 while Jira has a separate epic CARL-4134 (created 12 Oct) with no dates.", "Aishwarya Jairam", "Confirm which epic owns SOX and its date."),
    ("Observability", "CARL-384 now reads In Triage in Jira while the plan reports 83% complete.", "Debarghyo Sengupta", "Confirm status."),
    ("Venus", "Roadmap links CARL-3959 (iDeal cross-project support), which does not exist in Jira.", "Surendarvarma Sritharan", "Raise the epic or drop the row."),
    ("Dates", "The 16 Oct weekly pack dates (Ad Sales 31 Oct, Venus 31 Oct, Finance 'reset') came via the Slack summary; the pack itself was not available.", "Venkatesh D (PMO)", "Reconfirm against the .docx."),
]

DECISIONS = [
    ("MicroStrategy", "Re-project International (717 SP, 0%), Hive and TD-API, then publish one MicroStrategy retirement date.", "Aishwarya Jairam · Daya Thakur"),
    ("FreeWheel", "Commit decoupling dates per dependent system; leadership asked for these on 30 Sep.", "Hong Zhang · Ping Feng"),
    ("GAM / DFP", "Is GAM genuinely required (it is a net-new pipeline), and by when?", "Product"),
    ("Salesforce", "Build a direct Salesforce → Iceberg flow, or stay on daily Oracle copy?", "Engineering"),
    ("UC1", "Confirm V1 scope and date the governed Silver → Gold replacement.", "Arlene Rose · Rohini Vugumudi"),
    ("Shared Silver", "One shared FreeWheel and Operative One Silver definition, rather than five private ones.", "Consuming teams"),
    ("Comscore", "Raise an intake request so Comscore can carry a date.", "Product"),
    ("Greenfield pilot", "Choose NextGen or Market Research Dashboard as the first Greenfield pilot.", "Program"),
]
