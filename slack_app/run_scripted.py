"""STEP 2 acceptance — a scripted, no-Slack client run that reaches debrief
ENTIRELY over MCP (mirrors tests/test_mcp_roundtrip.py, but through the Slack
app's own EngineClient seam).

Run:  python -m slack_app.run_scripted
"""

import asyncio
import json
import os

from slack_app.agent import run_session_over_mcp

FIXTURE = os.path.join(os.path.dirname(__file__), "..", "demo", "fixture_5p_twocamp.json")


def load_fixture() -> dict:
    with open(FIXTURE) as f:
        return json.load(f)


async def main() -> int:
    fixture = load_fixture()
    out = await run_session_over_mcp(fixture, session_id="scripted")
    delib, debrief = out["delib"], out["debrief"]

    print("handles:", out["started"]["handles"])
    print("reached_quorum:", delib["reached_quorum"])
    print("winner:", debrief["winner"])
    actions = [e["action"] for e in debrief["audit"]]  # includes the debrief event
    for beat in ("store_read", "rank_bridging", "cross_inhibition",
                 "steelman_minority", "inject_evidence", "check_quorum", "debrief"):
        print(f"  audit has {beat:<18}: {beat in actions}")
    ai = [p["handle"] for p in debrief["participants"] if p["actor_type"] == "agent"]
    print("AI seat revealed:", ai)

    assert delib["reached_quorum"] and debrief["winner"]
    print("\nSLACK MCP SEAM: PASS — full deliberation reached debrief over MCP.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
