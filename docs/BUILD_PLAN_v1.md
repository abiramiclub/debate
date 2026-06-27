# Build Plan v1 — Wiki & Vicky, a Deliberation Mediator (Slack Agent)

**Hackathon:** Slack Agent Builder Challenge · Track: Agent for Good
**Deadline:** July 13, 2026, 5:00pm PDT · **Today:** June 19, 2026 (~24 days)
**Required tech used:** MCP server integration (core) + Real-Time Search API (info-injection). Two of three — combination, per the rules, is rewarded.

---

## The one-paragraph spec

A Slack agent that makes group deliberation fairer and groupthink-resistant. It does **not** debate. It **mediates**: a deterministic constitution (the Wiki) — rules distilled from computational-deliberation research (Pol.is, Habermas Machine, Community Notes) — conducts the process, and a probabilistic mediator (Vicky) performs the language work the Wiki invokes — synthesizing common ground, steelmanning the minority, detecting echo. Humans do the deliberating. The constitution owns every fairness guarantee (auditable); the mediator owns understanding and phrasing (never trusted to be fair on its own).

## Architecture in one breath

`Humans (anonymized) → Slack surface → MCP server [ DETERMINISTIC constitution conducts → invokes PROBABILISTIC mediator for language tasks → deterministic aggregation/selection → quorum ] → Slack debrief + metrics`. See `architecture_v1.mermaid`.

---

## Phase 0 — Setup (Days 1–2)

1. Join the **Slack Developer Program** (free) to unlock a developer **sandbox workspace**. The sandbox URL is required at submission, so do this first.
2. Install the **Slack CLI (v4+)**. Run `slack create agent`, pick the **Python** template. Run `slack run` (socket mode, hot reload) and confirm a hello-world agent posts in the sandbox.
3. Create the GitHub repo. Establish two top-level packages: `constitution/` (deterministic) and `mediator/` (probabilistic). Keep them importable independently — the separation is the whole thesis and the demo narrative.
4. Decide the LLM for the mediator: Claude via API (simplest, reliable) or local qwen3 over a tunnel (cheaper, on-brand, but adds latency/fragility for a recorded demo). **Recommendation: Claude API for the build, note the local-LLM option as a deployment variant.**

**Exit check:** an agent responds in your sandbox; repo scaffolded with the two-package split.

## Phase 1 — Deterministic core: the Constitution + MCP server (Days 3–6)

5. **Distill the constitution.** Write the rule set (the Wiki) as a table: *principle → system rule*. Cover exactly five mechanisms (no more for v1):
   - Independent assessment before advertising → collect each member's private read **before** any reveal (anti-anchoring).
   - Merit-proportional visibility → support surfaced in proportion to merit, not volume/recency.
   - Cross-inhibition (stop-signals) → fire a counter-signal when consensus forms too fast (anti-premature-lock-in).
   - Quorum threshold → decide at a threshold, not forced unanimity.
   - Stale-signal detection → trigger a structural refresh when the discussion signal goes flat (stale-consensus detection).
6. **Implement the state machine** (`constitution/protocol.py`): states = `COLLECT_READS → REVEAL → CROSS_INHIBITION → QUORUM_CHECK → (loop|DEBRIEF)`. Pure, deterministic transitions. No LLM calls here.
7. **Implement the aggregation rule:** **bridging-based ranking / group-informed consensus** (score statements by cross-group agreement, not within-group) — the deployed anti-majority-tyranny math from Pol.is / Remesh / Community Notes. This is the fairness guarantee.
8. **Anti-sycophancy weighting:** weight recency **down**, under-represented views **up**, in any ranking. Make the weights config so they're tunable (phase-aware: more dissent-preservation early).
9. **Audit log:** every state transition and every agent contribution appended to a JSONL file with timestamp + source. This is both governance and demo evidence.
10. **Wrap the engine as an MCP server** exposing deterministic tools: `start_session`, `store_read`, `check_quorum`, `rank_bridging`, `get_audit`. Wire the Slack agent to call them.

**Exit check:** a scripted text-only session runs end-to-end through the state machine via MCP, with a JSONL audit produced. **MCP requirement satisfied — bank it here.**

> RISK: MCP-server-to-Slack-agent wiring is the least-documented seam. Spend an hour validating the connection in Phase 1; do not discover it in week 3.

## Phase 2 — Probabilistic mediator (Days 7–11)

11. **Generative synthesis** (`mediator/synthesize.py`): given the collected reads, produce N candidate common-ground statements (Habermas-style; start with N=8). 
12. **Agreement prediction:** for each candidate, estimate each participant's agreement from their submitted read (Habermas reward-model role). Feed these into the deterministic bridging-ranker from Phase 1 — **the mediator proposes, the constitution selects.**
13. **Minority steelman:** generate the strongest version of the least-supported credible view on demand (cross-inhibition payload).
14. **Semantic echo detection:** classify whether a thread is intensifying without new information entering (the failure mode from arXiv 2506.11825). Output a boolean + reason; the constitution decides what to do with it.

**Exit check:** given a fixed set of reads, the pipeline returns a constitution-selected common-ground statement + a minority steelman, with the selection traceable to the deterministic ranker.

## Phase 3 — Slack integration depth (Days 12–15)

15. **Anonymization:** assign neutral handles (Birch, Maple, Cedar…); keep the handle↔user map server-side and access-controlled. Humans and any seeded agents post under neutral handles only.
16. **Private-read flow:** collect independent reads + confidence (1–5) via DM or modal **before** reveal.
17. **Block Kit rendering:** rounds, surfaced common-ground statement, cross-inhibition prompt, quorum status.
18. **Consent gate:** session opens with the consensual-blind notice ("anonymous participants may include AI; you won't know which; contributions are logged; debrief follows") and an explicit opt-in.

**Exit check:** a small live session (you + 2–3 friends) completes in the sandbox under anonymized handles.

## Phase 4 — Real-Time Search injection + the demo foil (Days 16–18)

19. **RTS info-injection:** at a defined point, pull a vetted, **sourced** fact via the Real-Time Search API and inject it through an anonymous handle. Log the source in the audit. (Second required technology satisfied.)
20. **Information-uptake metric:** compare each participant's pre/post position + confidence against the injected evidence.
21. **The foil:** seed all-AI debate agents that reproduce the arXiv echo-chamber result, then switch the mediator on and show de-polarization. This is the control condition *and* the three-minute story.

**Exit check:** the foil run visibly echo-chambers; the mediated run visibly does not; metrics quantify the difference.

## Phase 5 — Metrics, debrief, hardening (Days 19–22)

22. **Debrief view (Block Kit):** information-uptake score, echo index, which participants were agents, the audit trail. This is the "for good" payload and the UX score.
23. **N-agnostic test:** run with 3, 6, and 10 participants; confirm quorum logic scales (threshold property — a decision is a threshold, not a headcount).
24. **Edge cases:** no quorum reached; single dominant speaker; everyone agrees immediately (is it real or performative?); a participant drops mid-session.

**Exit check:** clean runs at three group sizes; debrief renders correctly; no crashes on the edge cases above.

## Phase 6 — Demo, diagram, writeup, submit (Days 23–24 + buffer)

25. Record the **controlled** 3-minute demo (foil → mediated → debrief). Do **not** gamble on a live unknown-N session on camera.
26. Finalize the **architecture diagram** (`architecture_v1.mermaid`) for the required diagram artifact.
27. Writeup using the prepared framing: "Slack is where teams decide; this makes them decide *well*," the prob/det split (Wiki vs. Vicky), the deliberation-science lineage (Pol.is / Habermas / Community Notes), and the Habermas/Science credibility shield. Frame fairness strictly as *process*, never outcome; elections as motivating example, not headline.
28. Submit: text description, demo video, architecture diagram, sandbox URL.

---

## Scope discipline (read before adding anything)

- **In for v1:** 5 governing mechanisms, bridging-based ranking, anti-sycophancy weighting, anonymization, RTS injection, the foil, debrief metrics, audit log.
- **Out of v1 (named, parked):** a "facilitator refresh," a "group fork," the full rule-set wiki (curate only the 5 rows you need; the full wiki is a post-hackathon asset), QLoRA/fine-tuning anything, Marketplace submission (that's the Organizations track; you're Agent for Good).
- **Decision still open:** mediator **visible** (posts synthesis into channel) vs **ambient** (works through private nudges, near-invisible). Visible = stronger demo; ambient = purer facilitator principle. Resolve before Phase 3.

## Top risks (flagged early, per working style)

1. **MCP↔Slack seam** — validate in Phase 1, not week 3.
2. **Demo fragility** — controlled recording mitigates; build a seeded, replayable session.
3. **Mediator latency** — if using local qwen3, synthesis of 8 candidates may be slow on camera; pre-warm or use Claude API for the recording.
4. **Scope creep via the wiki** — the wiki is seductive and infinite; freeze it at 5 rows for v1.
5. **"Whose fairness" optics** — keep all framing on procedural fairness; never let the agent hold a topic position; audit log is your defense.
