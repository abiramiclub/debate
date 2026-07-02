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


def build_live_round0(reads: list[dict], n: int = 8, client=None, model: str = "claude-opus-4-8") -> dict:
    """Live path: produce round-0 candidates + agreement from real reads via
    ClaudeMediator. Needs credentials. Returned in the mediator_script shape:
    {"candidates": [...], "agreement": [[...]]}."""
    from mediator.base import Read
    from mediator.claude import ClaudeMediator

    med = ClaudeMediator(client=client, model=model)
    rs = [Read(handle=r.get("handle", f"P{i}"), text=r["text"], confidence=r["confidence"])
          for i, r in enumerate(reads)]
    candidates = med.synthesize_candidates(rs, n)
    agreement = med.predict_agreement(rs, candidates)
    return {"candidates": candidates, "agreement": agreement}
