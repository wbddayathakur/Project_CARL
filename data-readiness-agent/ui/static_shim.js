// Static data layer for the self-contained prototype. Replaces the HTTP API with the same
// operations over an embedded snapshot of REAL data. No DOM access; no network.
(function (root) {
  "use strict";
  var D = __DATA__;
  var LAYERS = ["bronze", "silver", "gold"];
  var TESTING = ["Ready for Testing", "In Testing", "Ready For UAT", "In Review"];
  var STOP = ["carl", "gold", "silver", "bronze", "legacy", "oracle", "modelled", "other", "usage", "insights", "global", "channel", "dim", "fact", "ldr", "via", "the", "unmapped"];
  var SHORT_OK = ["neo", "dwh", "nrld", "mit"];
  var SUGGESTED = ["Give me an overview", "Which sources are safe for an agent to use?", "What is blocked?", "Is FreeWheel ready?",
    "Where does Jira disagree with the lake?", "What can't you measure?", "How fresh is the data?", "Look up DCI_RATECARD_HEADER"];

  var cur = { f: D["default"].fresh, r: D["default"].rec };
  var V = function () { return D.variants[cur.f + "_" + cur.r]; };
  var inList = function (a, x) { return a.indexOf(x) >= 0; };
  var esc = function (s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); };
  var todayISO = function () { var d = new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); };
  var daysBetween = function (a, b) { return Math.round((Date.parse(b) - Date.parse(a)) / 86400000); };
  var classInfo = function (id) { for (var i = 0; i < D.jira.classes.length; i++) if (D.jira.classes[i].id === id) return D.jira.classes[i]; return { id: id, short: id, label: id }; };
  var tool = function (name, args, result) { return { tool: name, args: args, result: result }; };
  var count = function (arr, fn) { var o = {}; arr.forEach(function (x) { var k = fn(x); o[k] = (o[k] || 0) + 1; }); return o; };
  var sortedPairs = function (o) { return Object.keys(o).map(function (k) { return [k, o[k]]; }).sort(function (a, b) { return b[1] - a[1]; }); };

  // ---------------- state ----------------
  function state() {
    var v = V(), t = todayISO();
    return {
      today: t, rubric_status: D.rubric_status, rubric_note: D.rubric_note,
      thresholds: { fresh_window_days: cur.f, recurring_min_commit_days_30d: cur.r,
        baseline: { fresh_window_days: D["default"].fresh, recurring_min_commit_days_30d: D["default"].rec } },
      inputs: D.inputs.map(function (i) { return { name: i.name, as_of: i.as_of, detail: i.detail, age_days: daysBetween(i.as_of, t) }; }),
      jira_site: D.site, totals: v.totals, findings: v.findings, rows: v.rows, excluded: D.excluded,
      criteria: D.criteria, gaps: D.gaps, golden_name_matches: D.golden, dq_metrics_tables: D.dq,
      jira: D.jira, sources: D.sources
    };
  }

  // ---------------- drill-downs ----------------
  function tables(q) {
    var ql = (q.q || "").toLowerCase().trim(), out = [];
    D.tables.forEach(function (t) {
      if (q.source && t.source !== q.source) return;
      if (q.layer && t.layer !== q.layer) return;
      if (ql && t.name.toLowerCase().indexOf(ql) < 0) return;
      if (q.prod === "yes" && !t.in_prod) return;
      if (q.prod === "no" && t.in_prod) return;
      var fresh = !!(t.in_prod && t.prod_updated && daysBetween(t.prod_updated, D.glue_as_of) <= cur.f);
      var has = t.versions !== null && t.versions !== undefined;
      out.push({ fqn: t.fqn, name: t.name, source: t.source, layer: t.layer, in_dev: t.in_dev, in_prod: t.in_prod,
        dev_updated: t.dev_updated, prod_updated: t.prod_updated, fresh: fresh,
        versions: has ? t.versions : null, commit_days_30d: has ? t.commit_days : null,
        recurring: has ? (t.commit_days || 0) >= cur.r : null, stories: t.stories });
    });
    out.sort(function (a, b) { return (a.in_prod === b.in_prod ? 0 : a.in_prod ? -1 : 1) || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0); });
    return { total: out.length, rows: out.slice(0, 300), truncated: out.length > 300 };
  }

  function recon(q) {
    var ql = (q.q || "").toLowerCase().trim(), rows = D.recon.filter(function (r) {
      if (q.classification && r.classification !== q.classification) return false;
      if (q.source && r.source !== q.source) return false;
      if (ql && r.summary.toLowerCase().indexOf(ql) < 0 && r.key.toLowerCase().indexOf(ql) < 0 &&
        !r.tables.some(function (t) { return t.indexOf(ql) >= 0; })) return false;
      return true;
    });
    return { total: rows.length, rows: rows.slice(0, 400), truncated: rows.length > 400 };
  }

  // ---------------- triage (port of Engine.triage_one) ----------------
  function ratio(a, b) {   // Ratcliff/Obershelp, same measure as Python difflib.SequenceMatcher.ratio
    function block(alo, ahi, blo, bhi) {
      var bi = alo, bj = blo, bk = 0;
      for (var i = alo; i < ahi; i++) for (var j = blo; j < bhi; j++) {
        var k = 0; while (i + k < ahi && j + k < bhi && a.charAt(i + k) === b.charAt(j + k)) k++;
        if (k > bk) { bi = i; bj = j; bk = k; }
      }
      return [bi, bj, bk];
    }
    function matches(alo, ahi, blo, bhi) {
      if (alo >= ahi || blo >= bhi) return 0;
      var m = block(alo, ahi, blo, bhi); if (!m[2]) return 0;
      return m[2] + matches(alo, m[0], blo, m[1]) + matches(m[0] + m[2], ahi, m[1] + m[2], bhi);
    }
    return a.length + b.length === 0 ? 1 : 2 * matches(0, a.length, 0, b.length) / (a.length + b.length);
  }
  function closeMatches(word, names, n, cutoff) {
    var scored = [];
    names.forEach(function (nm) {
      var up = 2 * Math.min(word.length, nm.length) / (word.length + nm.length);
      if (up < cutoff) return;
      var r = ratio(word, nm); if (r >= cutoff) scored.push([r, nm]);
    });
    scored.sort(function (x, y) { return y[0] - x[0] || (x[1] < y[1] ? 1 : -1); });
    return scored.slice(0, n).map(function (x) { return x[1]; });
  }

  function triageOne(raw) {
    var name = (raw || "").trim(), res = { input: name };
    if (!name || name.length > 200) return Object.assign(res, { code: "invalid", title: "Invalid or empty name", next: "Enter a table name such as DCI_RATECARD_HEADER or DEALBLDR.DCI_RATECLASS." });
    var s = name.toLowerCase().replace(/^(bronze|silver|gold)\./, ""), schema = null, cands;
    if (s.indexOf(".") >= 0) { var p = s.split("."); schema = p[0]; cands = [schema + "_" + p.slice(1).join("."), p.slice(1).join(".")]; } else cands = [s];
    cands = cands.map(function (c) { return c.replace(/[^a-z0-9_]/g, "_"); });

    var pool = D.tables, hits = [], used = cands[0];
    for (var i = 0; i < cands.length; i++) {
      var c = cands[i];
      hits = pool.filter(function (t) { return t.name === c || (t.name.length > c.length && t.name.slice(-(c.length + 1)) === "_" + c); });
      if (hits.length) { used = c; break; }
    }
    var hitRows = hits.slice().sort(function (a, b) { return (a.in_prod === b.in_prod ? 0 : a.in_prod ? -1 : 1) || (a.layer < b.layer ? -1 : a.layer > b.layer ? 1 : 0) || (a.name < b.name ? -1 : 1); })
      .slice(0, 8).map(function (t) { return { fqn: t.fqn, layer: t.layer, source: t.source, in_dev: t.in_dev, in_prod: t.in_prod, prod_updated: t.prod_updated }; });

    var pats = cands.map(function (c) { return new RegExp("(^|[^a-z0-9_])" + esc(c) + "($|[^a-z0-9_])"); }), storyHits = [];
    D.stories.forEach(function (st) {
      var low = st.summary.toLowerCase(), texts = [low.replace(/\./g, "_"), low.replace(/\./g, " ")];
      if (pats.some(function (p) { return texts.some(function (t) { return p.test(t); }); }))
        storyHits.push({ key: st.key, status: st.status, summary: st.summary.trim(), resolved: st.resolved || null });
    });
    storyHits.sort(function (a, b) { return +a.key.split("-")[1] - +b.key.split("-")[1]; });

    var related = [];
    if (schema) {
      var cnt = count(pool.filter(function (t) { return t.name.indexOf(schema + "_") === 0 || t.name.indexOf("_" + schema + "_") >= 0; }), function (t) { return t.source; });
      related = sortedPairs(cnt).slice(0, 3).map(function (x) { return { source: x[0], tables: x[1] }; });
    }
    var close = [];
    if (!hits.length) {
      var byName = {}; pool.forEach(function (t) { byName[t.name] = t.fqn; });
      close = closeMatches(used, Object.keys(byName), 3, 0.85).map(function (n) { return byName[n]; }).sort();
    }

    var prodB = hits.filter(function (h) { return h.in_prod && h.layer === "bronze"; }), prodAny = hits.filter(function (h) { return h.in_prod; });
    var devAny = hits.filter(function (h) { return h.in_dev; });
    var openStory = null; for (var k = 0; k < storyHits.length; k++) if (storyHits[k].status !== "Done" && storyHits[k].status !== "Archive") { openStory = storyHits[k]; break; }
    var code, title, nxt;
    if (prodB.length || prodAny.length) {
      var hh = (prodB.length ? prodB : prodAny)[0];
      code = "in_prod"; title = "Already in prod (" + hh.layer + "): no new ingestion needed";
      nxt = "Check recurrence and freshness below before relying on it.";
      if (openStory) nxt += " Jira " + openStory.key + " is still '" + openStory.status + "': likely a stale ticket or unfinished acceptance.";
    } else if (devAny.length) {
      code = "dev_only"; title = "Exists in dev only: needs promotion, not a new ingestion"; nxt = "Put promotion to prod on the backlog.";
    } else if (storyHits.length) {
      var st0 = storyHits[0];
      if (st0.status === "Done") {
        var after = !!(st0.resolved && st0.resolved > D.glue_as_of);
        code = "done_no_table"; title = "Jira " + st0.key + " is Done but the catalog has no such table";
        nxt = after ? "It was resolved after the catalog snapshot, so refresh the catalog first." : "Resolved before the snapshot, so this is a real gap or a rename: confirm with the story owner.";
      } else {
        code = "requested_no_table"; title = "Requested in Jira (" + st0.key + ", " + st0.status + ") but not in the catalog";
        nxt = inList(TESTING, st0.status) ? "Status says testing/UAT, so check whether the catalog export is stale before treating this as a gap." : "Already on the backlog: no duplicate request needed.";
      }
      if (close.length) nxt += " Near-identical table names exist: this may be a rename.";
    } else if (close.length) {
      code = "possible_rename"; title = "Not found, but near-identical table names exist";
      nxt = "Likely a rename or variant of an existing table. Confirm before creating a new backlog item.";
    } else {
      code = "new_request"; title = "Not in the catalog and no Jira story: new bronze backlog item"; nxt = "Create a bronze ingestion story.";
      nxt += related.length ? " Related tables already live under " + related[0].source + " (" + related[0].tables + " tables), so reuse that pipeline and DAG."
        : " No related tables found, so the source group is unknown: an owner must assign one.";
    }
    return Object.assign(res, { code: code, title: title, next: nxt, candidate: used, tables: hitRows, stories: storyHits.slice(0, 6),
      close_names: close, related_sources: related, data_age_days: daysBetween(D.glue_as_of, todayISO()) });
  }

  // ---------------- agent (port of agent.py; same intents, same wording) ----------------
  function sourcesIn(q) {
    var names = {}, ql = q.toLowerCase(), found = [];
    V().rows.forEach(function (r) { if (r.source !== "unmapped") names[r.source] = 1; });
    Object.keys(names).sort().forEach(function (n) {
      var nl = n.toLowerCase(), words = (nl.match(/[a-z0-9]+/g) || []).filter(function (w) { return !inList(STOP, w) && (w.length >= 4 || inList(SHORT_OK, w)); });
      if (ql.indexOf(nl) >= 0 || words.some(function (w) { return new RegExp("\\b" + esc(w) + "\\b").test(ql); })) found.push(n);
    });
    return found.slice(0, 3);
  }
  var layerIn = function (q) { for (var i = 0; i < 3; i++) if (new RegExp("\\b" + LAYERS[i] + "\\b").test(q.toLowerCase())) return LAYERS[i]; return null; };
  var totals = function () { return V().totals; };

  function aOverview() {
    var st = state(), t = st.totals, j = st.jira, pop = st.rows.filter(function (r) { return r.counts.tables; });
    var g = count(pop, function (r) { return r.gate.verdict; }), old = st.inputs.filter(function (i) { return i.age_days > 7; });
    var b = [
      "Agent-use gate across " + pop.length + " populated source/layer groups: " + (g.BLOCK || 0) + " BLOCK, " + (g.CAUTION || 0) + " CAUTION, " + (g.CLEARED || 0) + " CLEARED. Nothing is CLEARED because no data-quality, schema or parity evidence exists.",
      "No prod table shows a recurring load in the retained history (" + t.prod_recurring + " of " + t.prod_with_history + " with history). This is 'not evidenced', not proof of no schedule.",
      j.blocked_with_prod_table + " of " + j.blocked_total + " Blocked Jira stories already have their table in prod.",
      "Only " + j.matched + " of " + j.reconciled + " table-named stories matched a catalog table; the rest are not started, post-date the catalog, or are naming drift."];
    if (old.length) b.push("Staleness: " + old.map(function (i) { return i.name + " is " + i.age_days + " days old"; }).join(", ") + ".");
    return { headline: t.in_prod + " of " + t.tables + " scored tables are in prod. " + t.dev_only + " sit only in dev.", bullets: b,
      tools: [tool("get_state", {}, st.rows.length + " source/layer rows, " + st.findings.length + " findings")],
      followups: ["Which sources are safe for an agent to use?", "What is blocked?", "What can't you measure?"] };
  }
  function aGate() {
    var rows = V().rows.filter(function (r) { return r.counts.tables; }), by = count(rows, function (r) { return r.gate.verdict; });
    var caution = rows.filter(function (r) { return r.gate.verdict === "CAUTION"; });
    return { headline: "No source is cleared for unsupervised agent use. " + (by.CAUTION || 0) + " groups are usable with caution, " + (by.BLOCK || 0) + " are blocked.",
      table: { cols: ["Source", "Layer", "In prod", "Verdict", "Why"], rows: caution.map(function (r) { return [r.source, r.layer, r.counts.in_prod + "/" + r.counts.tables, r.gate.verdict, r.gate.reason]; }) },
      bullets: ["CAUTION means the tables are in prod, so an agent can read them, but quality is unverified. The agent should cite the data as unverified and avoid irreversible actions on it."],
      tools: [tool("gate_by_source_layer", {}, rows.length + " groups evaluated")], followups: ["Is iDeal ready?", "What can't you measure?"],
      caveat: "The gate is derived from the proposed rubric, not an approved standard." };
  }
  function aSource(srcs, layer) {
    var rows = V().rows.filter(function (r) { return inList(srcs, r.source) && (!layer || r.layer === layer); });
    var tools = [tool("readiness_by_source", { sources: srcs, layer: layer }, rows.length + " rows")];
    if (!rows.length) return { headline: "No rows for " + srcs.join(", ") + (layer ? " / " + layer : "") + ".", tools: tools };
    var recs = D.recon.filter(function (r) { return inList(srcs, r.source) && (!layer || r.layer === layer); });
    tools.push(tool("jira_for_source", { sources: srcs }, recs.length + " table stories"));
    var b = rows.map(function (r) {
      var c = r.counts;
      return c.tables ? r.source + " " + r.layer + ": " + c.in_dev + " in dev, " + c.in_prod + " in prod of " + c.tables + ". Verdict " + r.gate.verdict + ": " + r.gate.reason
        : r.source + " " + r.layer + ": no tables in the catalog.";
    });
    if (recs.length) b.push("Jira: " + sortedPairs(count(recs, function (r) { return r.classification; })).map(function (x) { return x[1] + " " + classInfo(x[0]).short; }).join(", ") + ".");
    var blocked = recs.filter(function (r) { return r.status === "Blocked"; });
    if (blocked.length) b.push("Blocked: " + blocked.map(function (r) { return r.key; }).join(", ") + ".");
    var allBlock = rows.every(function (r) { return r.gate.verdict === "BLOCK"; });
    return { headline: srcs.join(", ") + ": " + (allBlock ? "Not ready for an agent to act on." : "Partly usable, with caution."), bullets: b, tools: tools,
      followups: ["What is blocked for " + srcs[0] + "?", "What can't you measure?"],
      caveat: "Catalog is " + state().inputs[0].age_days + " days old. Quality criteria are unverified for every layer." };
  }
  function aBlocked() {
    var byKey = {}; D.recon.forEach(function (r) { byKey[r.key] = r; });
    var named = 0, rows = D.blocked.map(function (bk) {
      var r = byKey[bk.key]; if (r) named++;
      return [bk.key, bk.summary.trim().slice(0, 80), r ? classInfo(r.classification).short : "no table named"];
    });
    rows.sort(function (a, b) { return ((a[2] === "no table named") - (b[2] === "no table named")) || (a[0] < b[0] ? -1 : 1); });
    var j = D.jira;
    return { headline: j.blocked_total + " stories are Blocked. " + j.blocked_with_prod_table + " of them already have a table in prod.",
      bullets: [named + " of the blocked stories name a table; for the other " + (rows.length - named) + " the lake cannot say anything.",
        "A Blocked story whose table is already in prod is either a stale ticket or live-but-unaccepted data. Ask the owner which."],
      table: { cols: ["Story", "Summary", "Lake says"], rows: rows },
      tools: [tool("list_blocked", {}, rows.length + " stories"), tool("jira_vs_catalog", {}, named + " matched to table names")],
      followups: ["Where does Jira disagree with the lake?"] };
  }
  function aJira() {
    var j = D.jira;
    return { headline: j.matched + " of " + j.reconciled + " table-named stories match a catalog table.",
      table: { cols: ["Reconciliation", "Stories"], rows: j.classes.map(function (c) { return [c.label, c.count]; }) },
      bullets: ["Open the 'Jira vs lake' tab to filter these and see the tables behind each."],
      tools: [tool("jira_vs_catalog", {}, j.reconciled + " reconciled, " + j.unparsed + " without a table name")], followups: ["What is blocked?"],
      caveat: "Matching is a naming heuristic; a no-match is a lead, not a verdict." };
  }
  function aGaps() {
    var g = D.golden;
    return { headline: D.gaps.length + " rubric criteria cannot be measured from any data we hold.",
      table: { cols: ["Criterion", "Layer", "What is needed"], rows: D.gaps.map(function (x) { return [x.id + " " + x.title, x.layer, x.needs]; }) },
      bullets: ["Golden / eval datasets: a name search over " + totals().tables + " tables found " + g.length + "."]
        .concat(D.dq.map(function (d) { return "DQ results store: " + d[0] + " (dev=" + (d[1] ? "Y" : "N") + ", prod=" + (d[2] ? "Y" : "N") + ")."; }))
        .concat(["Environment isolation (non-prod DMS pointing at prod Oracle, CARL-4112) is only in Jira/ARB notes: not scorable here."]),
      tools: [tool("evidence_gaps", {}, D.gaps.length + " criteria without evidence"), tool("name_search", { pattern: "golden|eval|ground_truth|benchmark" }, g.length + " hits")],
      followups: ["Which sources are safe for an agent to use?"] };
  }
  function aFresh() {
    var st = state(), t = st.totals;
    return { headline: t.stale_in_prod + " of " + t.in_prod + " prod tables were not updated within " + cur.f + " days of the catalog snapshot.",
      table: { cols: ["Input", "As of", "Age (days)", "Detail"], rows: st.inputs.map(function (i) { return [i.name, i.as_of, i.age_days, i.detail]; }) },
      bullets: ["The catalog is the oldest input, so findings that depend on it (Done-but-no-table, testing-but-no-table) may be overtaken by events.", "Change the freshness window in the Rubric tab to see how this moves."],
      tools: [tool("input_freshness", {}, "3 inputs"), tool("count_stale_prod", { window_days: cur.f }, t.stale_in_prod + " stale")], followups: ["What can't you measure?"] };
  }
  function aRecur() {
    var t = totals(), rows = V().rows.filter(function (r) { return r.counts.prod_with_history; });
    return { headline: t.prod_recurring + " of " + t.prod_with_history + " prod tables with history show a recurring load.",
      table: { cols: ["Source", "Layer", "With history", "Recurring", "Single snapshot"], rows: rows.map(function (r) { return [r.source, r.layer, r.counts.prod_with_history, r.counts.prod_recurring, r.counts.prod_single_snapshot]; }) },
      bullets: ["'Recurring' means commits on at least the configured number of distinct days in the last 30. A single retained snapshot may just mean snapshots were expired, so treat this as not evidenced rather than proof of no schedule."],
      tools: [tool("load_cadence", { min_days: cur.r }, rows.length + " groups with history")], followups: ["How fresh is the data?"] };
  }
  function aDevOnly() {
    var rows = V().rows.filter(function (r) { return r.counts.tables && r.counts.in_prod === 0; }).sort(function (a, b) { return b.counts.tables - a.counts.tables; });
    return { headline: rows.reduce(function (s, r) { return s + r.counts.tables; }, 0) + " tables across " + rows.length + " source/layer groups exist only in dev.",
      table: { cols: ["Source", "Layer", "Tables in dev only"], rows: rows.map(function (r) { return [r.source, r.layer, r.counts.tables]; }) },
      tools: [tool("dev_only_groups", {}, rows.length + " groups")], followups: ["Which sources are safe for an agent to use?"] };
  }
  function aLookup(names) {
    var res = names.slice(0, 3).map(triageOne), b = [];
    res.forEach(function (r) {
      b.push(r.input + ": " + r.title + ". " + r.next);
      (r.tables || []).slice(0, 3).forEach(function (h) { b.push("   " + h.fqn + ": dev=" + (h.in_dev ? "Y" : "N") + ", prod=" + (h.in_prod ? "Y" : "N")); });
      (r.stories || []).slice(0, 2).forEach(function (s) { b.push("   " + s.key + " (" + s.status + "): " + s.summary.slice(0, 70)); });
    });
    return { headline: "Looked up " + res.length + " table name" + (res.length !== 1 ? "s" : "") + ".", bullets: b,
      tools: res.map(function (r) { return tool("triage_table", { name: r.input }, r.code || ""); }), followups: ["Open the Triage tab to check many table names at once"] };
  }

  function ask(question) {
    var q = (question || "").trim().slice(0, 500);
    if (!q) return { headline: "Ask me something about readiness.", suggestions: SUGGESTED, tools: [] };
    var ql = q.toLowerCase();
    var toks = (q.match(/[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)?/g) || []).filter(function (t) { return (t.indexOf("_") >= 0 || t.indexOf(".") >= 0) && !/^(e\.g|i\.e)/i.test(t); });
    if (toks.length) return aLookup(toks);
    var srcs = sourcesIn(q);
    if (srcs.length && !/\b(all|every|overall)\b/.test(ql)) return aSource(srcs, layerIn(q));
    if (/\bblock(ed|ers?)?\b/.test(ql)) return aBlocked();
    if (/\b(overview|summary|summari[sz]e|big picture|where are we|what'?s going on)\b/.test(ql)) return aOverview();
    if (/\b(jira|tickets?|stor(y|ies)|disagree|mismatch(es)?)\b/.test(ql)) return aJira();
    if (/\b(gaps?|unverified|evidence|golden|eval|dq|quality|measure|missing|can'?t|cannot)\b/.test(ql)) return aGaps();
    if (/\b(fresh|freshness|stale|old|up to date|age|ages|recent|snapshot)\b/.test(ql)) return aFresh();
    if (/\b(recur\w*|cadence|schedul\w*|one.time|reload\w*)\b/.test(ql)) return aRecur();
    if (/\b(dev.only|only in dev|promot\w*|not in prod)\b/.test(ql)) return aDevOnly();
    if (/\b(safe|trust\w*|agents?|use|act|clear\w*|gate|ready|reliable)\b/.test(ql)) return aGate();
    var o = aOverview(); o.headline = "I'm not sure what you meant, so here is the overview. " + o.headline; o.suggestions = SUGGESTED; return o;
  }

  // ---------------- router ----------------
  function parseQuery(path) {
    var i = path.indexOf("?"), out = { _p: i < 0 ? path : path.slice(0, i) };
    if (i >= 0) path.slice(i + 1).split("&").forEach(function (kv) { var p = kv.split("="); if (p[0]) out[decodeURIComponent(p[0])] = decodeURIComponent((p[1] || "").replace(/\+/g, " ")); });
    return out;
  }
  function snap(opts, v) { var best = opts[0]; opts.forEach(function (o) { if (Math.abs(o - v) < Math.abs(best - v)) best = o; }); return best; }

  root.STATIC_MODE = true;
  root.STATIC_OPTIONS = D.options;
  root.__STATIC_TEST = { triageOne: triageOne, ask: ask, state: state, tables: tables, recon: recon, setThresholds: function (f, r) { cur = { f: f, r: r }; } };
  root.STATIC_API = function (path, body) {
    return new Promise(function (resolve, reject) {
      try {
        var q = parseQuery(path);
        switch (q._p) {
          case "/api/state": return resolve(state());
          case "/api/tables": return resolve(tables(q));
          case "/api/recon": return resolve(recon(q));
          case "/api/suggestions": return resolve({ suggestions: SUGGESTED });
          case "/api/ask": return resolve(ask(String((body || {}).question || "")));
          case "/api/triage": return resolve({ results: ((body || {}).names || []).map(String).filter(function (n) { return n.trim(); }).slice(0, 100).map(triageOne) });
          case "/api/rubric": {
            var before = V().totals;
            cur = { f: snap(D.options.fresh, +body.fresh_window_days), r: snap(D.options.rec, +body.recurring_min_commit_days_30d) };
            return resolve({ delta: { before: before, after: V().totals }, state: state() });
          }
          case "/api/reload": return resolve({ state: state() });
          default: return reject(new Error("Not available in the static prototype: " + q._p));
        }
      } catch (e) { reject(e); }
    });
  };
})(typeof window !== "undefined" ? window : this);
