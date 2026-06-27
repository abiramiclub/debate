"""Full-deliberation MCP round-trip.

A local MCP client drives an entire 5-person two-camp deliberation through the
MCP tools (start_session -> submit_read ×5 -> deliberate -> get_audit) and asserts
it reaches the SAME bridged quorum that demo/run_ab.py produces in-process — but
over MCP, with session state persisted server-side across the stateless calls.
"""

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from demo.run_ab import load_fixture, run_constitution


def _payload(result):
    if getattr(result, "structuredContent", None) is not None:
        sc = result.structuredContent
        # FastMCP wraps non-dict returns (e.g. lists) under "result".
        return sc.get("result", sc) if isinstance(sc, dict) else sc
    return json.loads(result.content[0].text)


async def _drive_over_mcp(fixture: dict) -> dict:
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            started = _payload(await session.call_tool("start_session", {
                "session_id": "rt",
                "participants": [{"user_id": p["user_id"], "actor_type": p["actor_type"]}
                                 for p in fixture["participants"]]}))
            handles = started["handles"]

            for handle, r in zip(handles, fixture["reads"]):
                await session.call_tool("submit_read", {
                    "session_id": "rt", "handle": handle,
                    "text": r["text"], "confidence": r["confidence"]})

            delib = _payload(await session.call_tool("deliberate", {
                "session_id": "rt",
                "mediator_script": fixture["rounds"],
                "steelman_text": fixture["steelman_text"],
                "evidence": fixture["evidence"]}))

            audit = _payload(await session.call_tool("get_audit", {"session_id": "rt"}))
            audit = audit if isinstance(audit, list) else audit.get("result", [])
            return {"delib": delib, "audit": audit}


def _expected_winner(fixture):
    import os, tempfile
    path = os.path.join(tempfile.mkdtemp(), "audit.jsonl")
    _, _, debrief = run_constitution(fixture, path)
    return debrief["winner"]


def test_full_deliberation_over_mcp_reaches_same_bridged_quorum():
    fixture = load_fixture()
    out = asyncio.run(_drive_over_mcp(fixture))
    delib = out["delib"]

    assert delib["reached_quorum"] is True
    # Same outcome as the in-process demo — but produced entirely over MCP.
    assert delib["winner"] == _expected_winner(fixture)
    # The bridged winner is the compromise, not either camp's opening line.
    assert delib["winner"] not in (fixture["rounds"][1]["candidates"][0],
                                   fixture["rounds"][1]["candidates"][1])

    # The full arc fired and is auditable over MCP.
    actions = [e["action"] for e in out["audit"]]
    assert "store_read" in actions
    assert "cross_inhibition" in actions
    assert "steelman_minority" in actions
    assert "inject_evidence" in actions
    decisions = [r["decision"] for r in delib["rounds"]]
    assert "EVIDENCE_INJECTED" in decisions
    assert decisions[-1] == "QUORUM_MET"
