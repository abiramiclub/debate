# BUILD BRIEF — Dataset Harness + Demo (no Slack yet)

**Project:** Honeybee Deliberation Mediator · **Repo:** abiramiclub/debate
**This session's job:** de-risk *novelty* and *"does it actually work"* before any Slack/MCP work.
**Two outputs only, in order:** (A) a measurement harness on real human deliberation data, then (B) a controlled demo that visibly exercises the enforced rules. Nothing else.

---

## READ FIRST (before writing any code)
Read, in this order, and confirm current state back to me:
1. `DELIBERATION_CONSTITUTION.md` (canonical rule set)
2. `constitution/` (protocol.py, bridging.py, weighting.py, audit.py, config.py)
3. `mediator/` (base.py interface, fake.py)
4. `demo/run_session.py` and the existing tests
Report: which of the rules below are already implemented vs. missing. Do **not** assume — verify in the code.

---

## LOCKED DECISIONS — do not re-litigate
1. **Test bed = the Habermas Machine open dataset** (DeepMind: `github.com/google-deepmind/habermas_machine`). Verify exact data availability, schema, and **license** before using. If redistribution is unclear, load locally and **gitignore the raw data** — do not commit it.
2. **Enforced constitution = Buckets A + B only.** Bucket C is parked (do not build the conviction module or performative-quorum detection this session).
3. **Mediator is VISIBLE** — it posts synthesis into the channel (Habermas-style). Resolve the data model in favor of visible. No ambient/private-nudge path.
4. **Canonical names:** `constitution/` (deterministic) and `mediator/` (probabilistic). The labels "Vicky" and "Karpaty Wiki" are retired from **all new code and all user-facing output** (debrief, logs surfaced to users, writeup). Do **not** do a wholesale rename of existing internal identifiers — not worth the churn pre-demo; just use canonical names going forward.
5. **Debrief = Slack Block Kit JSON**, built and validated **offline** now (renders in Block Kit Builder); wired to a live Slack app in a later session.
6. **Predictive layer = bridging/endorsement prediction ONLY.** Predicting the *outcome/winner* is a banned red line (it violates "fairness = process, never outcome").

---

## ENFORCED RULES THIS SESSION (the A+B set)

**Bucket A — hard-enforced, provable in the audit log:**
- Consent gate before session opens
- Independent reads collected **before** reveal (anti-anchoring) — structural
- Anonymization (handles; identity map server-side; reveal only at debrief)
- Bridging-based selection of the quorum statement (cross-group support, not vote count/recency)
- Recency down-weighting / dissent preservation
- Quorum threshold (bridging-adjusted, N-agnostic)
- Immutable JSONL audit
- Cross-inhibition trigger (deterministic fast-consensus velocity check)

**Bucket B — deterministic gate on a probabilistic output:**
- Minority-steelman requirement **fires deterministically** whenever a minority cluster exists (text is generated; the *trigger* is a rule)
- Echo detection → flag → consequence (evidence injection)
- Position-neutrality gate (mediator output rejected/regenerated if it takes a topic side) — **verify if built**; if not, a minimal deterministic version is in-scope **only if** it slots cleanly into the demo fixture, else park it and showcase steelman + echo instead.

---

## PHASE A — Habermas dataset harness (offline, no Slack, no live LLM required)
Goal: produce real numbers on whether bridging selection beats naive baselines on **real human** data.

1. Acquire + license-check the dataset; build an **adapter** mapping its format → the engine's internal types (positions, candidate statements, per-participant endorsement).
2. Run the constitution's **bridging selection** against baselines on each dataset session:
   - baseline 1: most-endorsed-overall (majority)
   - baseline 2: last-speaker statement
   - baseline 3: random
3. **Metrics:** cross-group endorsement breadth of the selected statement (the bridging score) and minority-survival. Keep the endorsement predictor **swappable and offline-runnable** (FakeMediator-style is fine; if a model is needed, gate it behind the interface).
4. Emit `RESULTS.md` (+ a CSV): one row per session, plus aggregate. Reproducible with **one command**.

**Exit check:** harness runs offline on N sessions and prints a comparison table. Report honestly where bridging beats baselines on cross-group breadth **and where it doesn't** — a mixed result is still a valid finding and must not be hidden.

### >> CHECKPOINT: stop after Phase A and show me the numbers before starting Phase B. <<
If bridging does not beat baselines, that reshapes the demo and the pitch — I need to see it first.

---

## PHASE B — Demo fixture + controlled A/B + Block Kit debrief
Goal: make the enforced rules *visible*. The demo is a **fixed-input A/B**, not puppeted agents.

1. **Build ONE demo fixture:** a scripted input deliberation engineered so **every** Bucket A/B rule above is forced to fire — an anchoring gap, a minority cluster needing steelman, a fast-consensus velocity that **trips cross-inhibition** (this closes the known "cross-inhibition never fires in default demo" gap), and an evidence gap for injection.
2. **Two pipelines on the SAME fixed input:**
   - *naive*: no constitution — reveal-all immediately + summarize (this is "what Slack does today")
   - *constitution*: full protocol, **visible** mediator
3. **Block Kit debrief JSON:** echo index before/after, minority-survival, bridging-support score, info-uptake after injected evidence, AI-handle reveal, link to audit trail. Validate against the Block Kit schema so it renders in Block Kit Builder.
4. Every showcased rule must leave a **traceable audit-log line**; produce a short `DEMO_SCRIPT.md` mapping each on-screen moment → the rule → its log line.

**Exit check:** the two pipelines produce visibly divergent outcomes on identical input; the debrief JSON validates/renders; every enforced rule fires and is traceable.

---

## GUARDRAILS — do NOT
- Do **not** build the Slack app, the MCP server wrapper, or wire live Slack. Later session.
- Do **not** add Bucket C (conviction, performative-quorum detection).
- Do **not** add new rules or tune new parameters — **freeze the constitution**.
- Do **not** require a live LLM for the harness; keep model calls swappable + offline-runnable.
- Do **not** commit raw dataset if the license is unclear.
- Do **not** wholesale-rename existing internal identifiers.

## DEFINITION OF DONE
Real numbers from real human data (Phase A) **plus** a controlled A/B that visibly exercises every enforced rule with a validated Block Kit debrief (Phase B) — all runnable offline with documented commands. This is the de-risk package. Slack/MCP come after, only once this works.

## EXPECTED OUTPUT FILES
```
harness/            loader + adapter, baselines, metrics, runner
RESULTS.md          the numbers + one-command reproduce steps
demo/fixture_*.json the engineered input
demo/run_ab.py      naive vs constitution on the fixed input
demo/debrief_blockkit.json   + a tiny schema validator
DEMO_SCRIPT.md      on-screen moment → rule → audit-log line
```
