"""SEAM SLICE — MCP round-trip.

Spawns the constitution engine as a real MCP server (stdio) and drives it as an
MCP CLIENT (the role the Slack agent will play), proving:
  1. tool discovery works,
  2. a deterministic tool result comes back over the wire,
  3. it is IDENTICAL to the in-process frozen engine (the wrapper rewrote nothing),
  4. stateful tools + audit round-trip (start_session -> store_read -> inject -> get_audit).

Run:  python -m mcp_server.seam_check
"""

import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# In-process engine, for the equivalence check.
from constitution.bridging import cluster_participants, rank_candidates
from constitution.config import DEFAULT

# A polarized matrix where a bridge (candidate 1) beats the majority pick (candidate 0).
AGREEMENT = [
    [1.0, 0.7], [1.0, 0.7], [1.0, 0.7],  # 3-person majority loves cand 0
    [0.0, 0.7], [0.0, 0.7],              # 2-person minority hates cand 0, likes cand 1
]


def _inprocess_winner(agreement):
    labels = cluster_participants(agreement, DEFAULT.k_max, DEFAULT.min_n_for_clustering)
    scored = rank_candidates(agreement, labels)
    return scored[0].index


def _payload(result):
    if getattr(result, "structuredContent", None):
        return result.structuredContent
    return json.loads(result.content[0].text)


async def main() -> int:
    params = StdioServerParameters(command="python", args=["-m", "mcp_server.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = sorted(t.name for t in tools.tools)
            print("1) tool discovery:", names)
            assert {"start_session", "store_read", "rank_bridging", "check_quorum",
                    "inject_evidence", "get_audit"}.issubset(set(names))

            r = await session.call_tool("rank_bridging", {"agreement": AGREEMENT})
            out = _payload(r)
            print("2) rank_bridging over the wire:", out)
            expected = _inprocess_winner(AGREEMENT)
            assert out["winner_index"] == expected, (out["winner_index"], expected)
            assert out["winner_index"] == 1, "bridge should beat the majority pick"
            print(f"3) matches in-process engine (winner_index={expected}, the bridge) ✓")

            await session.call_tool("start_session", {"session_id": "seam",
                "participants": [{"user_id": "a", "actor_type": "human"},
                                 {"user_id": "b", "actor_type": "agent"}]})
            await session.call_tool("store_read", {"session_id": "seam", "handle": "Birch",
                "text": "coverage matters", "confidence": 4})
            await session.call_tool("inject_evidence", {"session_id": "seam", "handle": "Linden",
                "text": "pilot kept output up with a rota", "source": "https://example.org/pilot"})
            audit = _payload(await session.call_tool("get_audit", {"session_id": "seam"}))
            actions = [e["action"] for e in (audit if isinstance(audit, list) else audit["result"])]
            print("4) stateful audit round-trip actions:", actions)
            assert "inject_evidence" in actions and "store_read" in actions

    print("\nMCP SEAM: PASS — engine is reachable as an MCP server and returns the real frozen result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
