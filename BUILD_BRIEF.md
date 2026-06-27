# BUILD BRIEF — Slack phase (eligibility + surface)

**Project:** Honeybee Deliberation Mediator · **Repo:** abiramiclub/debate · **Branch:** claude/jolly-ptolemy-ffxwwa
**Where we are:** Phase A (harness) + Phase B (full offline story) DONE and passing (23 tests; `demo/run_ab.py` runs end-to-end: consent → private reads → reveal → cross-inhibition → steelman → deadlock/echo → evidence injection → bridged quorum → Block Kit debrief).

This phase = the eligibility gate. Neither required technology is wired yet (RTS stubbed, MCP unbuilt — see `docs/REQUIRED_TECH_TODO.md`). A finished engine that uses no required tech is ineligible. This phase puts the engine in Slack and wires MCP + RTS for real.

## READ FIRST
1. `docs/REQUIRED_TECH_TODO.md` — the two tracked must-dos.
2. `constitution/protocol.py`, `constitution/evidence.py` — the engine + the evidence seam you'll make real.
3. `demo/run_ab.py`, `demo/debrief_blockkit.json` — the story + the debrief you'll render in Slack. Report current state before coding.

## LOCKED DECISIONS — do not re-litigate
1. Start fresh from the generic Slack agent template (`slack create agent`, Bolt Python). Do NOT retrofit the existing OpenClaw bots. The template is the surface; strip it of HR/IT/Sales domain content.
2. Reuse existing backends for models: qwen (local) + Claude (cloud) via OpenClaw, behind the existing 4-method mediator interface. New = Slack surface + MCP wrapper.
3. MCP architecture: the Slack agent is the MCP host/client; the constitution engine is the MCP server. The agent connects via Slack's MCP-client capability and calls the engine's tools. This is your strongest "wouldn't be possible without it" required-tech story.
4. Mediator: real Claude/qwen behind the interface for the live agent; the scripted mediator (`mediator/scripted.py`) replays the captured run for the recorded demo (reproducible, not fake); FakeMediator stays for tests.
5. RTS: called from the backend at the deadlock (it's a Web API method — confirm it's token-callable in the seam slice). Implement `evidence.RTSAdapterStub.fetch()`.
6. Visible mediator (posts to channel).
7. Honesty (carry into the writeup): harness numbers = validated on real data; demo numbers = illustrative engineered scenario. Keep them separate.

## STEP 0 — THE SEAM SLICE (do this FIRST, then stop)
Before building ANY UI, prove the three risky seams with trivial round-trips:
* MCP — Slack agent reaches the engine (wrapped as an MCP server) and gets back one tool result. This is the least-documented seam — retire the risk first.
* RTS — one real RTS call returns a result with a workspace token. Confirm whether it works from the backend (outside the event runtime).
* Real mediator — one real Claude/qwen call through the 4-method interface returns sane candidates + a steelman.

>> CHECKPOINT: stop after the slice and report. If any seam fails, we replan before investing in UI. <<

## THEN — the Slack surface + required-tech wiring
* Sandbox app: register in the developer sandbox; grant access to `slackhack@salesforce.com` and `testing@devpost.com` (required at submission).
* MCP server: wrap the engine's operations as MCP tools — `start_session`, `store_read`, `rank_bridging`, `check_quorum`, `inject_evidence`, `get_audit`. The constitution logic is frozen; wrap it, don't rewrite it.
* Private reads: modal so reads are hidden before reveal (preserves the anti-anchoring guarantee).
* Channel posts: mediator synthesis, minority steelman, injected fact (neutral handle).
* RTS real: implement `RTSAdapterStub.fetch()` — build a query from the deadlock context, issue the RTS call, vet the top result through a position-neutrality check, return `Evidence(text, source)`.
* Debrief: render the existing `debrief_blockkit.json` into the channel.

## GUARDRAILS — do NOT
* Do not rebuild the engine — wrap it. The constitution + Phase B logic are frozen.
* Do not skip the seam slice and build UI first.
* Do not build the full Karpaty wiki or any parked feature.
* Do not present demo metrics as the validated result.
* At least one required tech must be solid; aim for both (combining MCP + RTS is explicitly rewarded).

## DEFINITION OF DONE (this phase)
A live session runs in the Slack sandbox through the MCP-wrapped engine — consent, private reads, reveal, steelman, RTS evidence injection at the deadlock, bridged quorum, Block Kit debrief — captured cleanly on video. Sandbox URL ready with judge access. Then the submission package: architecture diagram (`architecture_v2.mermaid`, done), text writeup using the locked positioning, ~3-min video (first 60 seconds carry it — judges spend ~5–7 min/project), Agent for Good track, submit before Jul 13, 5pm PDT.

## EXPECTED OUTPUTS
```
slack_app/            Bolt Python agent (the surface)
mcp_server/           engine wrapped as MCP tools
constitution/evidence.py   RTSAdapter implemented (real call)
(demo recording + submission text — produced by you, not Claude Code)
```
