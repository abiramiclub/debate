"""MCP client seam — the Slack app's ONLY path to the engine.

The Slack app is the MCP host/client; `mcp_server/server.py` is the server. The
app drives the whole deliberation exclusively through MCP tools and never imports
`constitution/` directly. This is the required-tech integration — do not bypass it.

Usage:
    async with engine_client() as engine:
        started = await engine.start_session("s1", participants)
        ...
"""

import json
import sys
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _payload(result):
    """Unwrap a FastMCP CallToolResult into plain JSON data."""
    sc = getattr(result, "structuredContent", None)
    if sc is not None:
        # FastMCP wraps non-dict returns (e.g. lists) under "result".
        return sc.get("result", sc) if isinstance(sc, dict) else sc
    return json.loads(result.content[0].text)


class EngineClient:
    """Thin async facade over the engine's MCP tools."""

    def __init__(self, session: ClientSession):
        self._session = session

    async def call(self, name: str, **args):
        return _payload(await self._session.call_tool(name, args))

    async def list_tools(self) -> list[str]:
        tools = await self._session.list_tools()
        return sorted(t.name for t in tools.tools)

    # --- stateful lifecycle ---
    async def start_session(self, session_id: str, participants: list[dict]) -> dict:
        return await self.call("start_session", session_id=session_id, participants=participants)

    async def submit_read(self, session_id: str, handle: str, text: str, confidence: int) -> dict:
        return await self.call("submit_read", session_id=session_id, handle=handle,
                               text=text, confidence=confidence)

    async def deliberate(self, session_id: str, mediator_script: list[dict],
                         steelman_text: str, evidence: dict | None = None,
                         max_rounds: int = 6) -> dict:
        args = {"session_id": session_id, "mediator_script": mediator_script,
                "steelman_text": steelman_text, "max_rounds": max_rounds}
        if evidence is not None:
            args["evidence"] = evidence
        return await self.call("deliberate", **args)

    async def get_audit(self, session_id: str) -> list[dict]:
        out = await self.call("get_audit", session_id=session_id)
        return out if isinstance(out, list) else out.get("result", [])

    async def debrief(self, session_id: str) -> dict:
        return await self.call("debrief", session_id=session_id)

    # --- stateless primitives ---
    async def rank_bridging(self, agreement: list[list[float]]) -> dict:
        return await self.call("rank_bridging", agreement=agreement)

    async def check_quorum(self, support: float, ci_rounds_elapsed: int,
                           cross_inhibition_fired: bool) -> dict:
        return await self.call("check_quorum", support=support,
                               ci_rounds_elapsed=ci_rounds_elapsed,
                               cross_inhibition_fired=cross_inhibition_fired)

    async def inject_evidence(self, session_id: str, handle: str, text: str, source: str) -> dict:
        return await self.call("inject_evidence", session_id=session_id, handle=handle,
                               text=text, source=source)


@asynccontextmanager
async def engine_client(server_args: list[str] | None = None):
    """Spawn the engine MCP server over stdio and yield a connected EngineClient."""
    params = StdioServerParameters(
        command=sys.executable, args=server_args or ["-m", "mcp_server.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield EngineClient(session)
