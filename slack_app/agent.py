"""Agent-side orchestration.

The Slack app is the MCP client; the mediator (Vicky / ClaudeMediator) and the RTS
evidence fetch run AGENT-SIDE, and their outputs are passed as *data* into the
deterministic engine via the MCP `deliberate` tool. The engine selects, gates, and
reaches quorum. No LLM call decides a state transition.

Two paths:
  * `run_session_over_mcp(fixture)` — replays the fixture's pre-produced mediator
    script (the reproducible recorded-demo path). Fully offline; this is what the
    STEP 2 acceptance run and the Slack demo use.
  * `build_live_round0(reads)` — generates round-0 candidates + agreement live via
    ClaudeMediator (needs ANTHROPIC_API_KEY / OpenClaw). The live per-round arc is
    a follow-up; the recorded demo replays the captured script for reproducibility.
"""

from .mcp_client import engine_client


def participants_payload(fixture: dict) -> list[dict]:
    return [{"user_id": p["user_id"], "actor_type": p["actor_type"], "handle": p["handle"]}
            for p in fixture["participants"]]


async def run_session_over_mcp(fixture: dict, session_id: str = "slack-demo") -> dict:
    """Drive an entire deliberation to debrief ENTIRELY over MCP. Returns the
    started handles, the per-round deliberation result, the audit, and the debrief.
    This is the seam the Slack UI renders on top of."""
    async with engine_client() as engine:
        started = await engine.start_session(session_id, participants_payload(fixture))
        handles = started["handles"]

        # Private reads collected before any reveal (anti-anchoring).
        for handle, read in zip(handles, fixture["reads"]):
            await engine.submit_read(session_id, handle, read["text"], read["confidence"])

        # The agent's language work (candidates+agreement per round, steelman) and
        # the sourced evidence are passed in; the frozen loop runs server-side.
        delib = await engine.deliberate(
            session_id, fixture["rounds"], fixture["steelman_text"], fixture["evidence"])

        audit = await engine.get_audit(session_id)
        debrief = await engine.debrief(session_id)
        return {"started": started, "delib": delib, "audit": audit, "debrief": debrief}


DEFAULT_MODEL = "claude-sonnet-5"  # opus burns API budget for no demo gain


def _reads_to_objs(reads: list[dict]):
    from mediator.base import Read
    return [Read(handle=r.get("handle", f"P{i}"), text=r["text"], confidence=int(r["confidence"]))
            for i, r in enumerate(reads)]


def _make_mediator(client=None, model: str = DEFAULT_MODEL):
    from mediator.claude import ClaudeMediator
    return ClaudeMediator(client=client, model=model)


def _evidence_dict(evidence) -> dict | None:
    if evidence is None:
        return None
    if isinstance(evidence, dict):
        return evidence
    return {"text": evidence.text, "source": evidence.source,
            "handle": evidence.handle, "label": evidence.label}


def _round(cand_reads: list[dict], agree_reads: list[dict], mediator, n: int) -> dict:
    """One mediator_script round: candidates synthesized from `cand_reads`, and
    agreement predicted for `agree_reads` (always the REAL participants, so the
    matrix row count matches the session — the injected evidence informs the
    candidates without becoming a voting row)."""
    candidates = mediator.synthesize_candidates(_reads_to_objs(cand_reads), n)
    agreement = mediator.predict_agreement(_reads_to_objs(agree_reads), candidates)
    return {"candidates": candidates, "agreement": agreement}


def build_live_round0(reads: list[dict], mediator=None, client=None,
                      model: str = DEFAULT_MODEL, n: int = 8) -> dict:
    """Live round-0 candidates + agreement from real reads via ClaudeMediator."""
    mediator = mediator or _make_mediator(client, model)
    return _round(reads, reads, mediator, n)


def build_live_script(reads: list[dict], mediator, n_rounds: int = 4,
                      evidence=None, n: int = 8) -> list[dict]:
    """Assemble a live mediator_script. Round 0 (repeated to let echo build) is the
    camps' positions; the final round's candidates are re-synthesized with the
    injected evidence in view (the compromise), while agreement stays over the
    real participants. The engine then runs the frozen loop, gating and selecting."""
    g0 = _round(reads, reads, mediator, n)
    ev = _evidence_dict(evidence)
    if not ev:
        return [g0] * n_rounds
    reads_e = list(reads) + [{"handle": ev.get("handle", "Linden"),
                              "text": ev["text"], "confidence": 3}]
    g_post = _round(reads_e, reads, mediator, n)  # evidence-informed candidates
    return [g0] * max(1, n_rounds - 1) + [g_post]


async def run_live_session_over_mcp(question: str, reads: list[dict],
                                    participants: list[dict] | None = None,
                                    mediator=None, client=None, model: str = DEFAULT_MODEL,
                                    evidence=None, rts_adapter=None,
                                    session_id: str = "slack-live") -> dict:
    """Drive a LIVE deliberation over MCP: real reads -> live Vicky candidates +
    agreement -> Wiki's deterministic selection/gates/quorum -> debrief. The
    mediator (and optional RTS evidence fetch) run agent-side; their outputs are
    passed as data into `deliberate`. No LLM call decides a transition.

    Self-contained: opens its own MCP connection and collects the given reads."""
    mediator = mediator or _make_mediator(client, model)
    parts = participants or [
        {"user_id": r.get("handle", f"P{i}"), "actor_type": "human",
         "handle": r.get("handle", f"P{i}")} for i, r in enumerate(reads)]

    async with engine_client() as engine:
        started = await engine.start_session(session_id, parts)
        handles = started["handles"]
        for handle, r in zip(handles, reads):
            await engine.submit_read(session_id, handle, r["text"], int(r["confidence"]))

        # Evidence: live RTS at the deadlock, or provided (fixture/offline).
        if evidence is None and rts_adapter is not None:
            evidence = rts_adapter.fetch({"query": question, "reads": _reads_to_objs(reads)})
        ev = _evidence_dict(evidence)

        script = build_live_script(reads, mediator, evidence=ev)
        # Opinion groups for the steelman come from the engine's deterministic ranker.
        labels = (await engine.rank_bridging(script[0]["agreement"]))["groups"]
        steelman = mediator.steelman_minority(_reads_to_objs(reads), labels)

        delib = await engine.deliberate(session_id, script, steelman, ev)
        debrief = await engine.debrief(session_id)
        return {"started": started, "delib": delib, "debrief": debrief, "steelman": steelman}
