/* =============================================================================
   41-flowarch.js — the Flow Architecture, drawn.

   A direct transcription of the handwritten flow architecture note (6 Sep
   2026) into the same SVG vocabulary as the other blueprints, so the three
   flows in it can be read beside the phase loop they refine.

   Three drawings:
     1. Intake — every agent writes into one RFP graph, none of them writes
        the brief. Numbered as the note numbers them.
     2. Products / packaging — configs and documents vectorised into one index
        that Discovery asks questions of.
     3. Discovery — the ranking loop, with `Eval Justifications` sitting on the
        path between the planner's change and the next step, routing NO back to
        the human and YES forward.

   Red is the note's own colour for the human-in-the-loop edges.
   ============================================================================= */

const HITL = "#b3261e";
const GRAPHC = "#0b57d0";

/* --------------------------------------------------- 1. intake / RFP graph */
const IntakeGraphSvg = () => (
  <svg viewBox="0 0 1180 520" style={{width:"100%", height:"auto"}}>
    <Defs/>

    <text x="14" y="26" className="flx-t">TRIGGER</text>
    <SvgBox x={12} y={34} w={132} h={44} title="Plan trigger" chars={22} tone="#8a95a0"
      body="RFP lands on the desk"/>
    <Arrow d="M78,78 L78,108"/>
    <SvgBox x={12} y={110} w={132} h={52} title="Intake" body="orchestrator" chars={22} tone={GRAPHC}/>

    {/* the four step-1 collectors */}
    <text x="228" y="26" className="flx-t">1 · COLLECT IN PARALLEL</text>
    <SvgBox x={226} y={34} w={230} h={44} chars={40} title="RFP requirements parser"
      body="Attributes copied, with their location"/>
    <SvgBox x={226} y={86} w={230} h={44} chars={40} title="Advertiser history"
      body="12-month lookback on this advertiser"/>
    <SvgBox x={226} y={138} w={230} h={44} chars={40} title="Competitive intelligence"
      body="Category pressure in the flight"/>
    <SvgBox x={226} y={190} w={230} h={44} chars={40} title="Build seller context"
      body="P&I position, posture, push list"/>

    {/* rank-by-relevance stage on the two inferential ones */}
    <SvgBox x={486} y={86} w={122} h={44} chars={20} title="Rank by" body="relevance"/>
    <SvgBox x={486} y={138} w={122} h={44} chars={20} title="Rank by" body="relevance"/>
    <Arrow d="M456,108 L482,108"/>
    <Arrow d="M456,160 L482,160"/>

    {/* client negotiations arrives late and out of band */}
    <SvgBox x={486} y={10} w={122} h={40} chars={20} title="Client" body="negotiations" dash
      titleColor={HITL} stroke={HITL}/>

    {/* the graph */}
    <SvgBox x={772} y={16} w={180} h={218} fill="#f2f7ff" stroke={GRAPHC} chars={28}
      title="RFP graph" titleColor={GRAPHC}
      body="One structure. Every agent writes records into it. Nothing here is a conclusion — records carry a value, a source, a location and a confidence."/>

    <Arrow d="M456,56 L636,56 L636,68 L768,68" color={GRAPHC}/>
    <Arrow d="M608,30 L768,30" color={HITL} chip label="1″ arrives late, re-derives the brief" lx={688} ly={30} lw={20}/>
    <Arrow d="M608,108 L690,108 L690,86 L768,86" color={GRAPHC}/>
    <Arrow d="M608,160 L700,160 L700,120 L768,120" color={GRAPHC}/>
    <Arrow d="M456,212 L710,212 L710,160 L768,160" color={GRAPHC}/>

    {/* 2 — evidence eval */}
    <text x="228" y="278" className="flx-t">2 · SCORE WHAT IS ON IT</text>
    <SvgBox x={226} y={286} w={230} h={52} chars={40} tone={GRAPHC} title="Evidence eval agent"
      body="Strengths and weaknesses of each record"/>
    <Arrow d="M78,162 L78,312 L222,312" color={GRAPHC}/>
    <SvgBox x={486} y={286} w={200} h={52} chars={34} title="Update probability"
      body="Written back onto the record"/>
    <Arrow d="M456,312 L482,312"/>
    <Arrow d="M686,312 L730,312 L730,246 L862,246 L862,238" color={GRAPHC} chip
      label="update score" lx={796} ly={246} lw={18}/>
    <Arrow d="M900,238 L900,266 L470,266 L470,282" color={GRAPHC} dash chip
      label="read evidence" lx={700} ly={266} lw={18}/>

    {/* 3 — build the brief */}
    <text x="228" y="382" className="flx-t">3 · DERIVE, DO NOT ASSEMBLE</text>
    <SvgBox x={226} y={390} w={230} h={52} chars={40} tone={GRAPHC} title="Build intake brief"
      body="Derived from the graph, never typed"/>
    <Arrow d="M78,312 L78,416 L222,416" color={GRAPHC}/>
    <Arrow d="M940,238 L940,416 L462,416" color={GRAPHC} dash chip
      label="read evidence" lx={700} ly={416} lw={18}/>

    <SvgBox x={512} y={454} w={250} h={52} chars={42} stroke={HITL} titleColor={HITL}
      title="Surface analysis with reccos — HITL"
      body="The planner adjudicates; nothing auto-accepts"/>
    <Arrow d="M341,442 L341,480 L508,480" color={HITL}/>
    <Arrow d="M762,480 L980,480 L980,238" color={HITL} chip label="update evidence" lx={880} ly={480} lw={20}/>

    <SvgBox x={12} y={390} w={132} h={52} title="Intake brief" chars={22} tone="#1e8e3e"
      body="The handoff artifact"/>
    <Arrow d="M226,416 L150,416" color="#8a95a0"/>
  </svg>
);

/* ------------------------------------------ 2. products / packaging system */
const PackagingSvg = () => (
  <svg viewBox="0 0 1180 320" style={{width:"100%", height:"auto"}}>
    <Defs/>

    <text x="14" y="26" className="flx-t">FREEWHEEL / OPERATIVE CONFIG</text>
    <SvgBox x={12} y={34} w={196} h={40} chars={34} title="Targeting templates" body="214 configs"/>
    <SvgBox x={12} y={80} w={196} h={40} chars={34} title="Ad product configs" body="186 configs"/>
    <SvgBox x={12} y={126} w={196} h={40} chars={34} title="Content inventory packages" body="97 packages"/>

    <text x="14" y="196" className="flx-t">SPREADSHEETS, DOCS</text>
    <SvgBox x={12} y={204} w={196} h={40} chars={34} title="Reference pricing" body="Rate card, floors, benchmarks"/>
    <SvgBox x={12} y={250} w={196} h={40} chars={34} title="Product KPIs" body="Measured delivery by product"/>

    <Arrow d="M208,54 L280,54 L280,150 L324,150" color={GRAPHC}/>
    <Arrow d="M208,100 L280,100 L280,150 L324,150" color={GRAPHC} head={false}/>
    <Arrow d="M208,146 L280,146 L280,150 L324,150" color={GRAPHC} head={false}/>
    <Arrow d="M208,224 L280,224 L280,150 L324,150" color={GRAPHC} head={false}/>
    <Arrow d="M208,270 L280,270 L280,150 L324,150" color={GRAPHC} head={false}/>

    <SvgBox x={328} y={106} w={168} h={90} fill="#f2f7ff" stroke={GRAPHC} chars={24}
      title="Vectorised product RAG" titleColor={GRAPHC}
      body="One index over the configs themselves, not a copy of them"/>

    <Arrow d="M496,150 L560,150" color={GRAPHC}/>
    <SvgBox x={564} y={112} w={150} h={76} chars={24} tone={GRAPHC} title="LLM queries"
      body="Asked in the planner's own words, in Discovery"/>

    <text x="762" y="26" className="flx-t">WHAT A PLANNER ACTUALLY ASKS</text>
    <SvgBox x={760} y={34} w={400} h={40} chars={72} title="1. What product meets these KPIs?"/>
    <SvgBox x={760} y={80} w={400} h={40} chars={72} title="2. What customisations are available on this product?"/>
    <SvgBox x={760} y={126} w={400} h={56} chars={68} title="3. Exclude mature content off this product targeting"
      body="Resolves to a real config, with its avails and price consequence"/>
    <Arrow d="M714,150 L756,150"/>

    <SvgBox x={760} y={198} w={400} h={56} chars={70} fill="#fafbfc" stroke="var(--line)" dash
      title="Every answer names where it came from"
      body="A planner can go and check a number rather than trusting it — which is the difference between a search box and a source."/>
  </svg>
);

/* --------------------------------------------------- 3. the discovery loop */
const EvalLoopSvg = () => (
  <svg viewBox="0 0 1180 470" style={{width:"100%", height:"auto"}}>
    <Defs/>

    <SvgBox x={12} y={20} w={128} h={44} title="I/P trigger" chars={21} tone="#8a95a0"
      body="Handoff accepted"/>
    <Arrow d="M76,64 L76,96"/>
    <SvgBox x={12} y={98} w={128} h={54} title="Discovery" body="orchestrator" chars={21} tone={GRAPHC}/>

    <SvgBox x={186} y={20} w={210} h={58} chars={36} title="Brief parser + evidence store validation"
      body="Is the upstream artifact sound?"/>
    <SvgBox x={438} y={20} w={196} h={58} chars={32} title="Prep queries"
      body="What would suit this brief, asked of the product RAG"/>
    <Arrow d="M140,42 L182,42" color={GRAPHC}/>
    <Arrow d="M396,49 L434,49"/>

    <SvgBox x={676} y={20} w={178} h={58} chars={30} fill="#fafbfc" title="Products / packaging"
      body="The vectorised index"/>
    <Arrow d="M634,49 L672,49"/>

    <SvgBox x={438} y={114} w={196} h={52} chars={32} stroke={GRAPHC} titleColor={GRAPHC}
      title="Rank products" body="Five criteria, each scored"/>
    <Arrow d="M291,78 L291,140 L434,140" color={GRAPHC}/>
    <Arrow d="M765,78 L765,140 L638,140"/>

    {/* the human loop */}
    <SvgBox x={186} y={114} w={196} h={52} chars={32} stroke={HITL} titleColor={HITL}
      title="Surface for HITL" body="The planner reads the order and its reasons"/>
    <Arrow d="M434,140 L386,140" color={HITL}/>

    <SvgBox x={186} y={206} w={196} h={66} chars={32} stroke={HITL} titleColor={HITL}
      title="Allow ranking changes" body="Move, add, remove — each one carrying a justification"/>
    <Arrow d="M284,166 L284,202" color={HITL}/>

    <SvgBox x={472} y={206} w={180} h={66} chars={30} tone={HITL}
      title="Eval justifications"
      body="Scores the argument, not the change"/>
    <Arrow d="M382,239 L468,239"/>

    <Arrow d="M562,206 L562,178 L340,178 L340,170" color={HITL} chip
      label="THIN — named, scored, travels anyway" lx={451} ly={178} lw={44}/>

    <SvgBox x={472} y={318} w={180} h={52} chars={30} title="Allow customisations"
      body="Targeting templates on the product"/>
    <Arrow d="M562,272 L562,314" chip label="YES" lx={578} ly={296} lw={6}/>

    <SvgBox x={730} y={296} w={168} h={46} chars={28} title="Check inventory availability"/>
    <SvgBox x={730} y={352} w={168} h={46} chars={28} title="Compute price"/>
    <Arrow d="M652,336 L700,336 L700,319 L726,319"/>
    <Arrow d="M652,348 L700,348 L700,375 L726,375"/>

    <SvgBox x={472} y={402} w={180} h={52} chars={30} stroke={HITL} titleColor={HITL}
      title="Surface for HITL" body="Avails and price, before committing to the change"/>
    <Arrow d="M898,319 L950,319 L950,428 L656,428" color="#8a95a0"/>
    <Arrow d="M898,375 L930,375 L930,414 L656,414" color="#8a95a0"/>
    <Arrow d="M472,428 L430,428 L430,344 L468,344" color={HITL} chip
      label="additional customisations" lx={430} ly={392} lw={16}/>

    <Arrow d="M186,239 L76,239 L76,152" color={GRAPHC} chip label="DONE" lx={110} ly={200} lw={6}/>

    <text x="12" y="300" className="flx-t">THE POINT OF THE LOOP</text>
    <SvgBox x={12} y={310} w={160} h={144} chars={26} fill="#fafbfc" dash
      body="The planner can change anything. What they cannot do is change it without an argument that survives being read by someone who was not in the room. A weak one comes back here rather than travelling downstream inside the plan."/>
  </svg>
);

/* ------------------------------------------------------------------ screen */
const FlowArchTab = () => (
  <>
    <div className="banner b" style={{marginBottom:14}}>
      <span className="bi">Source</span>
      <div>Drawn from the <b>UMP Flow Architecture</b> note, 6 September 2026. It refines the five-phase loop rather
        than replacing it: same phases, same owners, but it says how the agents inside a phase are wired to each
        other, and it introduces the thing that decides whether a phase is allowed to end.</div>
    </div>

    <Card title="The orchestrator"
      sub="The note defines it in three lines. Everything else on this tab is a consequence of them.">
      <div className="g3">
        {[
          ["Knows the state machine",
           "Not just the current phase — every evaluation point inside every phase, and what each one is worth."],
          ["Scores the intermediate status",
           "A phase is not done or not-done. It has a score, and the score is made of named points a human can argue with."],
          ["Separates missing from weak",
           "Something absent holds the handoff, because the next phase would have to guess. Something weak does not — it is scored and carried forward. It never advances the plan and never overrules the planner."],
        ].map(([t,b],i)=>(
          <div key={i} style={{borderLeft:"2px solid var(--accent)", paddingLeft:11}}>
            <div style={{fontSize:12.5, fontWeight:600}}>{t}</div>
            <div className="tiny muted" style={{marginTop:3, lineHeight:1.55}}>{b}</div>
          </div>
        ))}
      </div>
      <div className="hr"/>
      <div className="tiny muted" style={{lineHeight:1.6}}>
        The one power it has is to refuse a handoff when something is <b>absent</b> — never when something is merely
        weak. That is a smaller claim than “an AI that plans”, and a much more useful one: the next phase never has
        to guess at an input, and nobody's judgement is second-guessed by a scoring function. Quality is still
        measured, but it travels forward to P&amp;I, who holds the only gate that can stop a plan. A gate the desk
        could not get past under deadline would simply be worked around, which is worse than not having one.
        Live on every phase screen as the <b>handoff gate</b>.
      </div>
    </Card>

    <Card title="1 · Intake — agents write to a graph, not to a brief" style={{marginTop:14}}
      sub="Numbered as the note numbers them. 1 collects, 2 scores what was collected, 3 derives the brief from the result.">
      <IntakeGraphSvg/>
      <div className="hr"/>
      <div className="g2">
        <div>
          <div className="lbl">What this changes</div>
          <div className="tiny muted" style={{lineHeight:1.6}}>
            No agent writes the brief. They write records, the eval agent scores them, and the brief is derived from
            the graph in one step at the end. That is why correcting something re-derives the brief instead of editing
            it — and why a late clarification can arrive at step 1″ and ripple through without anyone re-typing
            anything.
          </div>
        </div>
        <div>
          <div className="lbl">The note's three rules for the brief</div>
          <div className="col tiny" style={{gap:6}}>
            <div><b>A.</b> <span className="muted">An RFP is comprehensively defined by its attributes.</span></div>
            <div><b>B.</b> <span className="muted">Every attribute is either copied from, inferred from, or operator-added by — the provenance ladder, and it is never blank.</span></div>
            <div><b>C.</b> <span className="muted">The intake brief is validated by the operator, meaning the planner. Not by the system, and not by the AE.</span></div>
          </div>
        </div>
      </div>
    </Card>

    <Card title="2 · Products and packaging — one index, asked in words" style={{marginTop:14}}
      sub="Live in Discovery under 'Ask the catalogue'.">
      <PackagingSvg/>
    </Card>

    <Card title="3 · Discovery — the loop that Eval Justifications sits in" style={{marginTop:14}}
      sub="This is the flow that gives the challenger its shape: NO goes back to the human, YES goes on to customisation, pricing and avails.">
      <EvalLoopSvg/>
      <div className="hr"/>
      <div className="tiny muted" style={{lineHeight:1.6}}>
        Read the two red loops. The upper one is the argument loop: change the ranking, defend it, and either the
        defence holds or it comes back. The lower one is the consequence loop: every customisation re-checks avails and
        re-computes price before the planner commits to it, so nobody discovers at trafficking that the targeting they
        promised costs a fifth of the inventory. Only when both are quiet does <b>DONE</b> return to the orchestrator.
      </div>
    </Card>
  </>
);
