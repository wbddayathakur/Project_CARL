# NEO Reporting: Pacing Hub design

Prototype: [`NEO_Pacing_Hub_Prototype.html`](NEO_Pacing_Hub_Prototype.html). Open it in a browser and use **Viewing as** to switch audience. Deep links work as `#<persona>/<tab>`, for example `#finance/revenue`.

Sources, read 4 Nov 2026: Jira (CARL, CN); Confluence pages *NEO PRD | Reporting: Self-Serve Campaign Insights* (7945061365), *ADD 015: NEO 2.0 Unified Reporting Data Layer* (7744716852), *Neo – Reporting Enhancements* (7951220793), *WIP – NEO PRD | M&A Integration* (7952369802), *NEO 2.0 Backend Migration: API Delivery Status* (7952499034); and the local CARL registry (`iceberg-catalog-agent/registry`).

## The requirement and how the design meets it

| Requirement | Design answer |
| --- | --- |
| Holistic, not a point solution | One **Pacing Hub** in NEO with three kinds of pacing (delivery, revenue, forecast) and one catalog of every pacing report, whichever tool renders it today. There is no NEO-only pipeline. Everything reads CARL Gold through Cube. |
| All pacing reports surfaced through NEO | Each report in the catalog appears in NEO in one of four ways: **native** (NEO React on Cube REST), **embedded** (Quick Suite inside NEO, reading the same Cube view), **linked** (deep link out until migrated), or **feed** (data that supplies other reports). The mode is a migration state, not a permanent answer. |
| Self-service for users | A governed report builder where measures and dimensions come from Cube. The report runs on demand, export and schedule reuse exactly what is on screen, and large exports run in the background. Library users can subscribe or request a report; requests go to CARL intake with the closest existing report pre-filled. |
| Connected back to CARL and upstream systems | Every number carries a trust line showing its Cube view, Gold table, freshness and a **Trace to source** link. The lineage view runs from the source system through Bronze, Silver, Gold and Cube to NEO, and includes load status and known gaps. Outbound links go to Campaign Cockpit, Salesforce and the Jira item behind each report. |

## Audiences and scope

Scope is enforced in the Cube `access_policy` (row filters on `agency_id`, `advertiser_id`, the AE's book of business, and an internal-only flag on revenue views). The UI only reflects that scope. This follows PRD principle 5: "governance expressed at the platform layer", which means the UI, the API and exports can't drift apart.

| Persona | Delivery pacing | Revenue / forecast pacing | Report library | Builder |
| --- | --- | --- | --- | --- |
| Agency / advertiser buyer | Own agency–advertiser campaigns | **Never** | No | Delivery measures only |
| Account executive | Book of business | Own accounts | Yes | Delivery + revenue |
| Sales leadership / Finance | No | All teams; forecast for Finance | Yes | Revenue + forecast |
| NEO Ops / support | All NEO campaigns, once an advertiser or agency is picked | No | Yes | Delivery |

The PRD marks AE access as post-MVP. Internal personas also need NEO sign-in through the shared Cognito/Okta login (`cals-identity-service`), which `cals-neo` already uses.

## Screens

1. **Pacing home.** A tile per pacing type the user can see, a "needs attention" list sorted worst first, and alerts (pacing shortfall, stalled data, reports going live), as in M&A PRD use case 4.
2. **Delivery pacing.** A campaign list with health bands and filters for NEO vs direct IO buys and flight status. Campaign detail shows delivered vs contracted, flight elapsed, the required daily rate, a chart of cumulative delivery against plan and the line needed to finish, and the benchmark windows table (original benchmark kept unchanged next to the rolling one).
3. **Revenue pacing (internal).** Booked vs budget (and forecast, for Finance) by team, drilling to VP, AE and account, with the existing revenue pacing reports opened in place.
4. **All pacing reports.** The catalog: status, how it appears in NEO, where it lives today, owner, Jira item, and trace, subscribe and request actions.
5. **Build a report.** Dimensions grouped as Time, Delivery, Inventory, Geography, Content, Creative and Sales. Reach is shown but disabled because it can't be added up across rows. The report runs on demand, and the page states the schedule semantics.
6. **Lineage & trust.** Each data path from source to NEO, freshness, latest loads and data-quality checks, known gaps, and the reports built on that path.

## Pacing report inventory (from Jira, 4 Nov 2026)

| Report | Today | Status | In NEO as | Jira |
| --- | --- | --- | --- | --- |
| NEO Campaign & Deal Delivery Pacing | NEO 1.0 | In build (ADD 015 Phase 1) | Native | CN-64, CN-86 |
| NEO Delivery Health Benchmarks | — | Planned (PRD Stage 1) | Native | — |
| Linear & Digital Converged Pacing | Quick Suite | Live | Embedded → native | CARL-5 (+ 2769/2770/2771 open) |
| Ad Sales National Incentive Revenue Pacing (SIP) | Quick Suite | Live; bug in UAT | Embedded → native | CARL-4110, 3696, 3933 |
| Finance Forecasting Pacing | Excel | In build; blocked on Finance file | Embedded | CARL-1364, 1366, 3952, 4239 |
| CNN Domestic Ad Sales Finance Pacing | Power BI | Discovery | Linked | CARL-4095 |
| 2026 Linear Pending (Revamp Pacing) | MicroStrategy | In testing | Linked | CARL-4311 |
| 2026 Sports Rev (Revamp Pacing) | MicroStrategy | Ready for UAT | Linked | CARL-4314 |
| 2026 Ent & News Rev (Revamp Pacing) | MicroStrategy | Ready for UAT | Linked | CARL-4313 |
| Salesforce ABS Pacing feed | Oracle `wkg_wrr` | Bronze done; duplicate bug | Feed | CARL-3659, 3915 |
| Operative One line-day pacing | — | To do | Native | CARL-4252 |
| Venus digital pacing | 3P FreeWheel feed | Blocked on FreeWheel decoupling | Linked | — |

## Data paths

- **Delivery:** FreeWheel `NEO_INTRADAY_AD_STREAM_V` (gneast), NEO Postgres via DMS, Ad-Juster, ClearLine → `neo_bronze` → `neo_silver` → `neo_gold.rpt_deal_daily_metrics` (plus package, discrepancy) → Cube NEO views → NEO. Freshness is about 1 hour.
- **Revenue:** iDeal/Gabriel, stwprd, DWH, Salesforce ABS, WRR → `linear_digital_revenue_*` → `gold.fact_pacing_revenue_budget_month` → Cube `finance_view_pacing_revenue_budget` → Quick today, NEO later. Daily at 10:00 ET, with a 30-hour freshness SLA.
- **Forecast:** Finance weekly CSV → S3 → Total Ad Revenue Pacing model → Finance pacing Gold (CARL-3952) → Cube or dataset, still undecided (CARL-4239).

## Design rules

1. **One name per pacing measure.** NEO uses "Pacing %" for delivered ÷ contracted impressions; Finance uses it for booked ÷ budget. In Cube and in the UI these become **Delivery Pacing %**, **Revenue Pacing %** and **Forecast vs Budget %**, never just "Pacing".
2. **Health is a band, not a variance figure.** The band compares the achieved daily rate with the rate required for the rest of the flight. Proposed thresholds: On track ≥ 95%, At risk 85–95%, Behind < 85%. "Not started", "No benchmark", "Data stale" and "Amended – benchmark recomputing" are separate states and are never shown as Behind.
3. **Honest absence.** Zero delivery, no data yet, suppressed, unmapped and not entitled each display differently. Figures are labelled Preliminary until the settling window closes, then Final.
4. **What you see is what you export.** Export and schedule inherit the open report. Daily covers the previous day, Weekly the prior Monday–Sunday, Monthly the previous calendar month; flight-to-date is available on every cadence.
5. **AI writes words, never numbers.** Alerts and narratives are generated from Cube metrics and cite them.

## Phasing

| Phase | Scope | Gated by |
| --- | --- | --- |
| 1 (to 15 Dec) | Delivery pacing for NEO campaigns (native); the Pacing Hub and catalog, with deep links to every existing pacing report; trust lines and freshness | ADD 015 Cube models; prod Glue for FreeWheel tables |
| 2 (Q1 2027) | AE lens and alerts v1; Converged and SIP pacing embedded via the Cube view; benchmark windows and health bands | CARL-2760 (Cube model for revenue pacing); internal sign-in in NEO; reporting-service scheduling (no EventBridge or `ecs:RunTask` wiring yet) |
| 3 | Revenue pacing native in NEO; Finance forecast pacing; MSTR revamp pacing moved to Cube; direct IO and non-NEO buys paced alongside NEO buys | CARL-3952 and the live Finance file; Operative One Silver; FreeWheel Silver and decoupling |

## Decisions needed

1. **Native vs embedded.** ADD 015 puts embedded QuickSight out of scope and serves NEO only through Cube REST. The Reporting PRD (principle 4) names Quick Suite as the single BI front end. Recommendation: build NEO native for buyer-facing delivery pacing and the hub, and embed Quick for internal revenue dashboards during the transition. Both read the same Cube view, so the numbers match.
2. **Does internal revenue pacing belong in NEO at all?** NEO is buyer-facing today. Putting Finance and Sales pacing there makes NEO the front door for internal users too. That needs a product owner's decision and a Cube policy that keeps revenue views internal.
3. **Revenue pacing Cube view status.** The registry lists `finance_view_pacing_revenue_budget` as certified, but CARL-2760 (build that Cube model) is still To Do. Reconcile this before Phase 2 depends on it.
4. **Health band thresholds and settling windows** (FreeWheel vs VideoAmp) for Preliminary → Final.
5. **Which pacing report is authoritative** when Converged Pacing, SIP Pacing and the MSTR revamp reports overlap on the same revenue.
