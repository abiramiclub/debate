"""STEP 2 acceptance: the Slack app's EngineClient drives a full 5-person
deliberation to debrief ENTIRELY over MCP — same outcome as demo/run_ab.py."""

import asyncio

from slack_app.agent import run_session_over_mcp
from slack_app.run_scripted import load_fixture


def test_slack_client_reaches_debrief_over_mcp():
    fixture = load_fixture()
    out = asyncio.run(run_session_over_mcp(fixture, session_id="test-slack"))

    assert out["delib"]["reached_quorum"] is True
    winner = out["debrief"]["winner"]
    # The bridged compromise, distinct from either camp's opening line.
    assert winner == "Build the sourced wiki first; add a thin conversational layer on top."
    assert winner not in (fixture["rounds"][1]["candidates"][0],
                          fixture["rounds"][1]["candidates"][1])

    actions = [e["action"] for e in out["debrief"]["audit"]]
    for beat in ("store_read", "cross_inhibition", "steelman_minority",
                 "inject_evidence", "check_quorum", "debrief"):
        assert beat in actions, beat

    # Both gates fire and are audit-sourced (rendered as Wiki strikes in Slack).
    assert "neutrality_rejected" in actions
    assert "prediction_blocked" in actions

    # The AI seat (Willow) is revealed at debrief.
    ai = [p["handle"] for p in out["debrief"]["participants"] if p["actor_type"] == "agent"]
    assert ai == ["Willow"]
