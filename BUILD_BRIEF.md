# BUILD BRIEF — Phase B: the deliberation demo (offline, full story)

**Project:** Honeybee Deliberation Mediator · **Repo:** abiramiclub/debate · **Branch:** claude/jolly-ptolemy-ffxwwa
**Where we are:** Phase A done (harness on the Habermas dataset; commit `771996e`). The engine and the bridging selection are validated on 6,605 real sessions.
**What was wrong with the last plan:** the harness compressed the whole system down to a single voting decision. The deliberation process (the spine) and the evidence-grounding (a required-tech route) fell out of what we build and show. This phase brings both back.

This session builds the full story, offline: a real multi-round deliberation running through the actual state machine, with a minimal evidence-injection step, ending in a Block Kit debrief. No Slack/MCP wiring yet — that's the next phase.

## READ FIRST (verify, don't assume)
1. `docs/HONEYBEE_CONSTITUTION.md` — canonical rule doc (note: this is the real name; an earlier brief said `DELIBERATION_CONSTITUTION.md`).
2. `constitution/protocol.py` — the state machine you will now drive end-to-end.
3. `constitution/bridging.py`, `weighting.py`, `audit.py`, `config.py`.
4. `mediator/base.py`, `mediator/fake.py`. Report current state back before coding.

## LOCKED DECISIONS — do not re-litigate
1. The demo IS a live, multi-round deliberation through `protocol.py` — consent → reads-before-reveal → reveal → cross-inhibition → quorum. NOT a one-shot selection. The process is the point and the differentiator.
2. Scenario = 5 participants, two clearly opposed camps. Phase A showed the bridging effect only appears with real camps at 5+. A smaller or mostly-agreeing group makes the demo fall flat.
3. Visible mediator (posts synthesis into the channel).
4. Two pipelines on the SAME fixture: naive (reveal-all immediately + majority/summarize) vs constitution (full protocol). Same input, divergent outcome.
5. Minimal evidence injection at the deadlock point: one sourced fact, injected via a neutral handle, source logged, and each participant's position measured before vs after (information uptake). This is the Real-Time Search (RTS) route to a required hackathon technology.
6. Wiki stays THIN: one shared briefing at session start + the logged injected fact(s). Do NOT build the runtime-citable evidence store.
7. Block Kit debrief mirrors the harness metrics for THIS one session — least-satisfied-group support, minority survival, average — plus the uptake delta, the AI-handle reveal, and an audit-trail link.
8. Canonical names: `constitution/` + `mediator/`. Retire "Vicky" / "Karpaty Wiki" from all user-facing output — including the audit log `actor_handle="Vicky"` in `protocol.py`, which must become `"mediator"`.
9. Honesty rule (carry into all output): the bridging claim is proven on real data (Phase A). The uptake claim is demonstrated in the scenario only (the Habermas data has no evidence dimension). Never present uptake as data-validated.

## DEMO-CRITICAL RULE FIXES (do these first — B1)
These are the gaps that currently make the rules invisible. Fix only these:
* Cross-inhibition must actually fire in the demo fixture (today it never trips in the default demo). Engineer the fixture so round-0 support crosses `V_ci`.
* Minority steelman must fire whenever a minority cluster exists, not only as the cross-inhibition payload. Make the trigger "minority cluster present," per the constitution.
* Echo/deadlock → evidence-injection consequence. Wire the injection as the consequence of the deadlock/echo signal (today detect→flag exists but the consequence is unbuilt).
* Rename `actor_handle="Vicky"` → `"mediator"` in `protocol.py`.
* (Optional, only if trivial) call `recency_weights()` where the constitution says recency should down-weight; if non-trivial, leave it and note it.

## PHASE B STEPS
B1 — Demo-critical rule fixes (above).
Exit check: on the fixture, cross-inhibition fires, steelman fires on the minority cluster, the deadlock triggers injection, no "Vicky" in user-facing strings.

B2 — The 5-person two-camp fixture + the spine
* Build ONE fixture: 5 participants, two opposed camps, individual reads engineered so the full sequence is exercised — reads-before-reveal, reveal, cross-inhibition firing, a deadlock, then (post-injection) a bridging statement reaching quorum that differs from either camp's opening line.
* Run it through BOTH pipelines (naive vs constitution). Exit check: the two pipelines produce visibly different outcomes on identical input; every constitution step is traceable in the audit log.

>> CHECKPOINT: stop after B2 and show me the run + audit trace before B3/B4. <<

B3 — Evidence injection + uptake metric
* Add a swappable `EvidenceSource` interface: a labeled fixture source for this offline demo + an RTS adapter stub for the real call. Verify whether RTS can be called outside a Slack app; if it requires the Slack runtime, keep the stub and record "real RTS wiring" as a tracked must-do for the Slack phase (it is one of the two required-tech routes — do not let it silently disappear).
* At the deadlock, inject one sourced fact via a neutral handle, log the source in the audit.
* Measure each participant's position/confidence before vs after → an uptake number. Exit check: injection fires at deadlock, source is logged, uptake is computed and non-trivial in the scenario.

B4 — Block Kit debrief
* Emit `demo/debrief_blockkit.json`: least-satisfied-group support, minority survival, average (same three the harness reports), uptake delta, AI-handle reveal, audit-trail link. Validate against the Block Kit schema (renders in Block Kit Builder).
* `DEMO_SCRIPT.md`: each on-screen moment → the rule → its audit-log line. Frame the story as bridging-in-a-room-with-an-audit-trail-and-mid-debate-evidence, NOT a voting rule (avoid looking like a Pol.is clone). Exit check: debrief JSON validates/renders; the script maps every showcased moment to a real audit line.

## GUARDRAILS — do NOT
* Do not build the full Karpaty wiki / runtime-citable evidence store (thin only).
* Do not build the Slack app or MCP wrapper this session — but log RTS-real-wiring and MCP as the required-tech must-dos for the next (Slack) phase.
* Do not add new rules or parameters beyond the B1 fixes; otherwise freeze the constitution.
* Do not hardcode the evidence fact; it goes through the `EvidenceSource` interface.
* Do not present uptake as data-validated, or conflate it with the bridging result.

## DEFINITION OF DONE
A full multi-round deliberation runs end-to-end on the 5-person two-camp fixture; both pipelines diverge; cross-inhibition, steelman, evidence-injection, and bridging-quorum all fire and are audit-traceable; uptake is measured pre/post; the Block Kit debrief validates — all offline, one command. The on-camera Slack demo and real RTS/MCP wiring come next; this makes the full story runnable and inspectable first.

## EXPECTED OUTPUT FILES
```
demo/fixture_5p_twocamp.json     the engineered two-camp input
demo/run_ab.py                   naive vs constitution, full deliberation
constitution/evidence.py         EvidenceSource interface + fixture impl + RTS adapter stub
demo/debrief_blockkit.json       + a tiny schema validator
DEMO_SCRIPT.md                   on-screen moment -> rule -> audit-log line
```
